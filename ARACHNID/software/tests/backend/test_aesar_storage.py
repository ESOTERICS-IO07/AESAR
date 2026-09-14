from __future__ import annotations

import os
import tempfile
import pytest
from backend.models.schemas import (
    AESAStationAnalysis,
    EcosystemState,
    EnvironmentData,
    FieldAssessment,
    SamplingStation,
    StationObservationRecord,
)
from backend.services.storage_service import StorageService


def test_storage_service_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_aesar.db")
        img_dir = os.path.join(tmpdir, "images")

        storage = StorageService(db_path=db_path, images_dir=img_dir)

        # 1. Create mission
        storage.create_mission("TEST-M1", total_stations=5)
        missions = storage.get_missions()
        assert len(missions) == 1
        assert missions[0]["mission_id"] == "TEST-M1"
        assert missions[0]["status"] == "INITIALIZING"

        # 2. Save observation
        station = SamplingStation(id=1, x=1.2, y=2.4)
        obs = StationObservationRecord(
            station=station,
            timestamp=12345.67,
            environment=EnvironmentData(temperature_c=25.0, humidity_percent=60.0, available=True),
            analysis=AESAStationAnalysis(station_id=1, pdr=1.2, ecosystem_state=EcosystemState.BALANCED),
        )
        fake_img = b"\xff\xd8\xff\xe0" + b"\x00" * 30
        saved_obs = storage.save_station_observation("TEST-M1", obs, image_bytes=fake_img)
        assert saved_obs.image_path is not None
        assert os.path.isfile(saved_obs.image_path)

        # Retrieve observations
        retrieved_obs = storage.get_station_observations("TEST-M1")
        assert len(retrieved_obs) == 1
        assert retrieved_obs[0].station.id == 1

        # 3. Save and retrieve Field Assessment
        card = FieldAssessment(
            mission_id="TEST-M1",
            total_stations_scouted=1,
            overall_field_state=EcosystemState.BALANCED,
        )
        storage.save_field_assessment(card)
        retrieved_card = storage.get_field_assessment("TEST-M1")
        assert retrieved_card is not None
        assert retrieved_card.overall_field_state == EcosystemState.BALANCED
