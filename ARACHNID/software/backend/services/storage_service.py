from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from threading import RLock
from typing import Any, Dict, Generator, List, Optional

from backend.config.settings import settings
from backend.models.schemas import (
    FieldAssessment,
    SamplingStation,
    StationObservationRecord,
)

logger = logging.getLogger("aesar.storage")


class StorageService:
    """
    Local SQLite and file-backed persistence layer for AESAR missions and observations.
    Thread-safe, requires no external database server, and keeps image storage configurable.
    """

    def __init__(self, db_path: Optional[str] = None, images_dir: Optional[str] = None) -> None:
        self.db_path = db_path or settings.storage_database_path
        self.images_dir = images_dir or settings.storage_image_dir
        self._lock = RLock()

        # Ensure directories exist
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()

            # Missions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    status TEXT NOT NULL,
                    number_of_stations INTEGER NOT NULL,
                    completed_stations INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Station observations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS station_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT NOT NULL,
                    station_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    soil_moisture REAL,
                    image_path TEXT,
                    pest_detections TEXT,
                    defender_detections TEXT,
                    plant_health TEXT,
                    pdr REAL,
                    abiotic_risk REAL,
                    ecosystem_state TEXT,
                    recommendation TEXT,
                    confidence REAL,
                    data_quality TEXT,
                    raw_json TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions (mission_id)
                )
            """)

            # Field assessment cards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_assessments (
                    mission_id TEXT PRIMARY KEY,
                    assessment_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mission_id) REFERENCES missions (mission_id)
                )
            """)
            logger.info(f"AESAR SQLite storage initialized at {self.db_path}")

    def save_image(self, mission_id: str, station_id: int, image_bytes: bytes) -> str:
        """Saves JPEG frame to local disk and returns relative/stored file path."""
        filename = f"{mission_id}_st_{station_id}_{int(time.time())}.jpg"
        filepath = os.path.join(self.images_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            return filepath
        except Exception as e:
            logger.error(f"Failed to write station image: {e}")
            return ""

    def create_mission(self, mission_id: str, total_stations: int) -> None:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO missions (mission_id, start_time, status, number_of_stations, completed_stations)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mission_id, time.time(), "INITIALIZING", total_stations, 0),
            )

    def update_mission_status(
        self,
        mission_id: str,
        status: str,
        completed_stations: Optional[int] = None,
        end_time: Optional[float] = None,
    ) -> None:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            if completed_stations is not None and end_time is not None:
                cursor.execute(
                    """
                    UPDATE missions
                    SET status = ?, completed_stations = ?, end_time = ?
                    WHERE mission_id = ?
                    """,
                    (status, completed_stations, end_time, mission_id),
                )
            elif completed_stations is not None:
                cursor.execute(
                    """
                    UPDATE missions
                    SET status = ?, completed_stations = ?
                    WHERE mission_id = ?
                    """,
                    (status, completed_stations, mission_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE missions
                    SET status = ?
                    WHERE mission_id = ?
                    """,
                    (status, mission_id),
                )

    def save_station_observation(
        self,
        mission_id: str,
        obs: StationObservationRecord,
        image_bytes: Optional[bytes] = None,
    ) -> StationObservationRecord:
        """Persists a complete scouting observation and saves captured image if provided."""
        image_path = obs.image_path
        if image_bytes and not image_path:
            image_path = self.save_image(mission_id, obs.station.id if obs.station else (obs.station_id or 1), image_bytes)
            obs.image_path = image_path

        pests_json = json.dumps([p.model_dump() for p in (obs.vision.pests if obs.vision else obs.pest_detections)])
        defenders_json = json.dumps([d.model_dump() for d in (obs.vision.defenders if obs.vision else obs.defender_detections)])
        plant_health = (
            obs.vision.plant_health.value
            if (obs.vision and hasattr(obs.vision.plant_health, "value"))
            else str(obs.plant_health)
        )

        temp = obs.environment.temperature_c if obs.environment else obs.temperature
        hum = obs.environment.humidity_percent if obs.environment else obs.humidity
        sm = obs.environment.soil_moisture_percent if obs.environment else obs.soil_moisture

        pdr = obs.analysis.pdr if obs.analysis else obs.pdr
        abiotic_risk = (
            obs.analysis.abiotic_risk.overall_score
            if (obs.analysis and obs.analysis.abiotic_risk)
            else obs.abiotic_risk
        )
        state = (
            obs.analysis.ecosystem_state.value
            if (obs.analysis and hasattr(obs.analysis.ecosystem_state, "value"))
            else str(obs.ecosystem_state)
        )
        rec = obs.analysis.recommendation if obs.analysis else obs.recommendation
        conf = obs.analysis.confidence if obs.analysis else obs.confidence
        qual = obs.analysis.data_quality if obs.analysis else obs.data_quality

        raw_json = obs.model_dump_json()
        station_id = obs.station.id if obs.station else (obs.station_id or 1)
        st_x = obs.station.x if obs.station else (obs.x or 0.0)
        st_y = obs.station.y if obs.station else (obs.y or 0.0)
        ts_val = float(obs.timestamp) if isinstance(obs.timestamp, (int, float)) else time.time()

        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO station_observations (
                    mission_id, station_id, timestamp, x, y,
                    temperature, humidity, soil_moisture, image_path,
                    pest_detections, defender_detections, plant_health,
                    pdr, abiotic_risk, ecosystem_state, recommendation,
                    confidence, data_quality, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    station_id,
                    ts_val,
                    st_x,
                    st_y,
                    temp,
                    hum,
                    sm,
                    image_path,
                    pests_json,
                    defenders_json,
                    plant_health,
                    pdr,
                    abiotic_risk,
                    state,
                    rec,
                    conf,
                    qual,
                    raw_json,
                ),
            )

        return obs

    def save_field_assessment(self, assessment: FieldAssessment) -> None:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO field_assessments (mission_id, assessment_json)
                VALUES (?, ?)
                """,
                (assessment.mission_id, assessment.model_dump_json()),
            )

    def get_missions(self) -> List[Dict[str, Any]]:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM missions ORDER BY start_time DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_station_observations(self, mission_id: str) -> List[StationObservationRecord]:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_json FROM station_observations WHERE mission_id = ? ORDER BY station_id ASC",
                (mission_id,),
            )
            rows = cursor.fetchall()
            results: List[StationObservationRecord] = []
            for row in rows:
                try:
                    results.append(StationObservationRecord.model_validate_json(row["raw_json"]))
                except Exception as e:
                    logger.error(f"Failed to parse stored station observation: {e}")
            return results

    def get_field_assessment(self, mission_id: str) -> Optional[FieldAssessment]:
        with self._lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT assessment_json FROM field_assessments WHERE mission_id = ?",
                (mission_id,),
            )
            row = cursor.fetchone()
            if row:
                try:
                    return FieldAssessment.model_validate_json(row["assessment_json"])
                except Exception as e:
                    logger.error(f"Failed to parse field assessment: {e}")
            return None
