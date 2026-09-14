from __future__ import annotations

import pytest
from backend.models.schemas import (
    DefenderItem,
    EcosystemState,
    EnvironmentData,
    PestItem,
    PlantHealth,
    SamplingStation,
    StationObservationRecord,
    VisionAnalysisResult,
)
from backend.services.aesa_engine import AESAEngine


def test_pdr_calculation():
    engine = AESAEngine()
    # 2 aphids (weight 1.0) vs 2 ladybirds (weight 1.0) -> PDR = 2 / (2 + 0.001) ~ 1.0
    vis = VisionAnalysisResult(
        pests=[PestItem(name="aphid", count=2, confidence=0.9)],
        defenders=[DefenderItem(name="ladybird", count=2, confidence=0.9)],
    )
    pdr, pests_w, defs_w = engine.calculate_pdr(vis)
    assert pdr <= 1.01
    assert pests_w == 2.0
    assert defs_w == 2.0


def test_abiotic_risk_calculation():
    engine = AESAEngine()
    # Optimal environment
    env_opt = EnvironmentData(
        temperature_c=24.0,
        humidity_percent=60.0,
        soil_moisture_percent=55.0,
        available=True,
    )
    risk_opt = engine.calculate_abiotic_risk(env_opt)
    assert risk_opt.risk_level == "LOW"

    # Extreme heat & drought
    env_stress = EnvironmentData(
        temperature_c=39.0,
        humidity_percent=25.0,
        soil_moisture_percent=15.0,
        available=True,
    )
    risk_stress = engine.calculate_abiotic_risk(env_stress)
    assert risk_stress.risk_level == "HIGH"


def test_evaluate_station_balanced_vs_imbalanced():
    engine = AESAEngine()
    env = EnvironmentData(
        temperature_c=25.0,
        humidity_percent=60.0,
        soil_moisture_percent=50.0,
        available=True,
    )

    # Station with low pest, high predator -> BALANCED
    vis_balanced = VisionAnalysisResult(
        pests=[PestItem(name="aphid", count=2, confidence=0.9)],
        defenders=[DefenderItem(name="ladybird", count=4, confidence=0.9)],
    )
    eval_b = engine.evaluate_station(1, vis_balanced, env)
    assert eval_b.ecosystem_state == EcosystemState.BALANCED
    assert eval_b.pdr <= 2.0

    # Station with high pest, zero predator -> IMBALANCED
    vis_imbalanced = VisionAnalysisResult(
        pests=[PestItem(name="aphid", count=40, confidence=0.9)],
        defenders=[],
    )
    eval_i = engine.evaluate_station(2, vis_imbalanced, env)
    assert eval_i.ecosystem_state == EcosystemState.IMBALANCED
    assert eval_i.pdr > 5.0


def test_generate_field_assessment():
    engine = AESAEngine()
    env = EnvironmentData(temperature_c=25.0, humidity_percent=60.0, soil_moisture_percent=50.0, available=True)
    vis_b = VisionAnalysisResult(pests=[], defenders=[DefenderItem(name="spider", count=2, confidence=0.9)])
    eval_b = engine.evaluate_station(1, vis_b, env)

    obs1 = StationObservationRecord(
        station=SamplingStation(id=1, x=1.0, y=1.0),
        timestamp="1000",
        environment=env,
        vision=vis_b,
        analysis=eval_b,
    )

    field_card = engine.generate_field_assessment("MISSION-1", [obs1])
    assert field_card.total_stations_scouted == 1
    assert field_card.balanced_stations_count == 1
    assert field_card.overall_field_state == EcosystemState.BALANCED
