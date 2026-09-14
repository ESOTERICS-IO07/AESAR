from __future__ import annotations

import logging
from typing import List, Optional

from backend.config.settings import settings
from backend.models.schemas import (
    AbioticRiskBreakdown,
    AESAStationAnalysis,
    EcosystemState,
    EnvironmentData,
    FieldAssessment,
    StationObservationRecord,
    VisionAnalysisResult,
)

logger = logging.getLogger("aesar.aesa")


class AESAEngine:
    """
    Agro-EcoSystem Analysis (AESA) Engine for AESAR.
    Combines visual observation (pests, beneficial defenders, foliar health)
    with physical environmental observations (temperature, humidity, soil moisture).
    
    Deterministic, fully testable, and configuration-driven.
    Gemini/Vision observes; backend AESAEngine computes.
    """

    def __init__(self) -> None:
        self.pest_weights = settings.aesa_pdr_pest_weights
        self.defender_weights = settings.aesa_pdr_defender_weights
        self.epsilon = settings.aesa_pdr_epsilon
        self.thresholds = settings.aesa_abiotic_thresholds

    def calculate_pdr(self, vision: VisionAnalysisResult) -> tuple[float, float, float]:
        """
        Calculate Pest-to-Defender Ratio:
          weighted_pests / (weighted_defenders + epsilon)
        Returns (pdr, total_weighted_pests, total_weighted_defenders)
        """
        weighted_pests = 0.0
        for item in vision.pests:
            weight = self.pest_weights.get(item.name.lower(), 1.0)
            weighted_pests += item.count * weight

        weighted_defenders = 0.0
        for item in vision.defenders:
            weight = self.defender_weights.get(item.name.lower(), 1.0)
            weighted_defenders += item.count * weight

        pdr = weighted_pests / (weighted_defenders + self.epsilon)
        return round(pdr, 2), round(weighted_pests, 1), round(weighted_defenders, 1)

    def calculate_abiotic_risk(self, env: Optional[EnvironmentData]) -> AbioticRiskBreakdown:
        """
        Calculates environmental stress risk index from temperature, humidity, and soil moisture.
        Returns component scores and overall risk level.
        """
        if env is None or not env.available:
            return AbioticRiskBreakdown(
                temperature_risk=0.0,
                humidity_risk=0.0,
                soil_moisture_risk=0.0,
                overall_score=0.0,
                risk_level="UNKNOWN",
                primary_stressors=["Sensor data unavailable"],
            )

        temp_t = self.thresholds.get("temperature_c", {})
        hum_t = self.thresholds.get("humidity_percent", {})
        sm_t = self.thresholds.get("soil_moisture_percent", {})

        stressors: List[str] = []

        # Temperature risk (0.0 to 1.0)
        t_risk = 0.0
        if env.temperature_c is not None:
            t = env.temperature_c
            t_opt_min = temp_t.get("optimal_min", 18.0)
            t_opt_max = temp_t.get("optimal_max", 28.0)
            t_crit_low = temp_t.get("critical_low", 15.0)
            t_crit_high = temp_t.get("critical_high", 35.0)

            if t < t_crit_low:
                t_risk = 0.8
                stressors.append(f"Cold stress ({t}°C)")
            elif t > t_crit_high:
                t_risk = 0.9
                stressors.append(f"Heat stress ({t}°C)")
            elif t < t_opt_min:
                t_risk = 0.3
                stressors.append(f"Sub-optimal low temp ({t}°C)")
            elif t > t_opt_max:
                t_risk = 0.4
                stressors.append(f"Elevated temp ({t}°C)")

        # Humidity risk (0.0 to 1.0)
        h_risk = 0.0
        if env.humidity_percent is not None:
            h = env.humidity_percent
            h_opt_min = hum_t.get("optimal_min", 50.0)
            h_opt_max = hum_t.get("optimal_max", 70.0)
            h_crit_low = hum_t.get("critical_low", 35.0)
            h_crit_high = hum_t.get("critical_high", 85.0)

            if h < h_crit_low:
                h_risk = 0.8
                stressors.append(f"Desiccating air ({h}%)")
            elif h > h_crit_high:
                h_risk = 0.7
                stressors.append(f"High disease risk humidity ({h}%)")
            elif h < h_opt_min:
                h_risk = 0.3
            elif h > h_opt_max:
                h_risk = 0.4

        # Soil Moisture risk (0.0 to 1.0)
        sm_risk = 0.0
        if env.soil_moisture_percent is not None:
            sm = env.soil_moisture_percent
            sm_opt_min = sm_t.get("optimal_min", 40.0)
            sm_opt_max = sm_t.get("optimal_max", 70.0)
            sm_crit_low = sm_t.get("critical_low", 25.0)
            sm_crit_high = sm_t.get("critical_high", 85.0)

            if sm < sm_crit_low:
                sm_risk = 0.9
                stressors.append(f"Severe drought stress ({sm}%)")
            elif sm > sm_crit_high:
                sm_risk = 0.8
                stressors.append(f"Root waterlogging ({sm}%)")
            elif sm < sm_opt_min:
                sm_risk = 0.4
                stressors.append(f"Low soil moisture ({sm}%)")
            elif sm > sm_opt_max:
                sm_risk = 0.3

        # Weighted composite score
        composite = round(0.4 * sm_risk + 0.35 * t_risk + 0.25 * h_risk, 2)
        if composite < 0.35:
            level = "LOW"
        elif composite < 0.65:
            level = "MODERATE"
        else:
            level = "HIGH"

        if not stressors:
            stressors = ["Optimal agro-climatic conditions"]

        return AbioticRiskBreakdown(
            temperature_risk=round(t_risk, 2),
            humidity_risk=round(h_risk, 2),
            soil_moisture_risk=round(sm_risk, 2),
            overall_score=composite,
            risk_level=level,
            primary_stressors=stressors,
        )

    def evaluate_station(
        self,
        station_id: int,
        vision: Optional[VisionAnalysisResult],
        env: Optional[EnvironmentData],
    ) -> AESAStationAnalysis:
        """
        Synthesizes visual and environmental observations for a single scouting station.
        Determines deterministic ecosystem state and Non-Pesticidal Management recommendation.
        """
        # If vision observation is completely unavailable
        if vision is None or vision.overall_confidence < 0.2:
            abiotic = self.calculate_abiotic_risk(env)
            return AESAStationAnalysis(
                station_id=station_id,
                pdr=0.0,
                weighted_pests=0.0,
                weighted_defenders=0.0,
                abiotic_risk=abiotic,
                ecosystem_state=EcosystemState.UNKNOWN,
                recommendation="Visual observation unavailable. Inspect sampling station manually.",
                confidence=0.0,
                data_quality="POOR",
            )

        pdr, w_pests, w_defenders = self.calculate_pdr(vision)
        abiotic = self.calculate_abiotic_risk(env)

        # Ecosystem State Decision Matrix:
        # PDR <= 2.0 -> balanced biological control
        # 2.0 < PDR <= 5.0 -> moderate strain
        # PDR > 5.0 -> imbalanced pest breakout
        # Severe abiotic stress can exacerbate moderate to imbalanced
        if pdr <= 2.0:
            if abiotic.risk_level == "HIGH":
                state = EcosystemState.MODERATE
                rec = (
                    "Predator population is healthy (PDR: {:.1f}), but abiotic stress ({}) is high. "
                    "Irrigate or adjust micro-climate to prevent pest escalation."
                ).format(pdr, ", ".join(abiotic.primary_stressors[:2]))
            else:
                state = EcosystemState.BALANCED
                rec = (
                    "Agro-ecosystem is in biological equilibrium (PDR: {:.1f}). Natural predators "
                    "(ladybirds/spiders) are effectively suppressing pests. Zero chemical intervention required."
                ).format(pdr)
        elif 2.0 < pdr <= 5.0:
            state = EcosystemState.MODERATE
            rec = (
                "Pest counts exceed defender threshold (PDR: {:.1f}). Implement cultural & mechanical controls: "
                "install yellow sticky cards and release additional biocontrol agents. Re-scout in 48 hours."
            ).format(pdr)
        else:
            state = EcosystemState.IMBALANCED
            rec = (
                "Critical pest breakout detected (PDR: {:.1f}). Beneficial defenders are overwhelmed. "
                "Apply botanical Neem seed kernel extract (NSKE 5%) or targeted organic bio-pesticide. "
                "Avoid broad-spectrum chemicals to preserve remaining beneficial predators."
            ).format(pdr)

        # Confidence & data quality calculation
        env_conf = 0.9 if (env and env.available) else 0.5
        overall_conf = round(0.7 * vision.overall_confidence + 0.3 * env_conf, 2)
        quality = "EXCELLENT" if overall_conf >= 0.85 else ("GOOD" if overall_conf >= 0.65 else "FAIR")

        return AESAStationAnalysis(
            station_id=station_id,
            pdr=pdr,
            weighted_pests=w_pests,
            weighted_defenders=w_defenders,
            abiotic_risk=abiotic,
            ecosystem_state=state,
            recommendation=rec,
            confidence=overall_conf,
            data_quality=quality,
        )

    def generate_field_assessment(
        self,
        mission_id: str,
        observations: List[StationObservationRecord],
    ) -> FieldAssessment:
        """
        Synthesizes observations across all mission sampling stations into an AESA Field Card.
        """
        total = len(observations)
        if total == 0:
            return FieldAssessment(
                mission_id=mission_id,
                total_stations_scouted=0,
                balanced_stations_count=0,
                moderate_stations_count=0,
                imbalanced_stations_count=0,
                unknown_stations_count=0,
                average_pdr=0.0,
                average_temperature_c=None,
                average_humidity_percent=None,
                average_soil_moisture_percent=None,
                overall_field_state=EcosystemState.UNKNOWN,
                field_recommendation="No station observations recorded in this mission.",
                hotspot_stations=[],
            )

        balanced_cnt = 0
        moderate_cnt = 0
        imbalanced_cnt = 0
        unknown_cnt = 0
        pdr_sum = 0.0
        pdr_valid_count = 0
        temp_sum = 0.0
        temp_cnt = 0
        hum_sum = 0.0
        hum_cnt = 0
        sm_sum = 0.0
        sm_cnt = 0
        hotspots: List[int] = []

        for obs in observations:
            st_state = obs.analysis.ecosystem_state if obs.analysis else EcosystemState.UNKNOWN
            if st_state == EcosystemState.BALANCED:
                balanced_cnt += 1
            elif st_state == EcosystemState.MODERATE:
                moderate_cnt += 1
            elif st_state == EcosystemState.IMBALANCED:
                imbalanced_cnt += 1
                hotspots.append(obs.station.id)
            else:
                unknown_cnt += 1

            if obs.analysis and obs.analysis.confidence > 0.3:
                pdr_sum += obs.analysis.pdr
                pdr_valid_count += 1

            if obs.environment and obs.environment.available:
                if obs.environment.temperature_c is not None:
                    temp_sum += obs.environment.temperature_c
                    temp_cnt += 1
                if obs.environment.humidity_percent is not None:
                    hum_sum += obs.environment.humidity_percent
                    hum_cnt += 1
                if obs.environment.soil_moisture_percent is not None:
                    sm_sum += obs.environment.soil_moisture_percent
                    sm_cnt += 1

        avg_pdr = round(pdr_sum / max(1, pdr_valid_count), 2)
        avg_temp = round(temp_sum / temp_cnt, 1) if temp_cnt > 0 else None
        avg_hum = round(hum_sum / hum_cnt, 1) if hum_cnt > 0 else None
        avg_sm = round(sm_sum / sm_cnt, 1) if sm_cnt > 0 else None

        # Overall Field State
        if imbalanced_cnt > 0 and (imbalanced_cnt / total) >= 0.25:
            field_state = EcosystemState.IMBALANCED
            rec = (
                f"Field exhibits localized pest outbreak in {imbalanced_cnt}/{total} stations (Hotspots: {hotspots}). "
                "Targeted botanical interventions (Neem oil/NSKE 5%) recommended strictly within hotspot zones. "
                "Conserve beneficial predator reservoirs across balanced stations."
            )
        elif (moderate_cnt + imbalanced_cnt) > 0 and ((moderate_cnt + imbalanced_cnt) / total) >= 0.4:
            field_state = EcosystemState.MODERATE
            rec = (
                f"Field ecosystem is under moderate pressure with {moderate_cnt} transitional stations. "
                "Enhance biological controls: deploy yellow sticky traps and increase scouting frequency. "
                "No broad-spectrum chemical sprays."
            )
        elif balanced_cnt > 0 and (balanced_cnt / total) >= 0.5:
            field_state = EcosystemState.BALANCED
            rec = (
                f"Whole-field agro-ecosystem is healthy and resilient ({balanced_cnt}/{total} balanced stations). "
                "Natural predator-to-prey biological balance is sustaining crop vitality. Continue regular scouting."
            )
        else:
            field_state = EcosystemState.UNKNOWN
            rec = "Mixed or insufficient scouting observations. Additional sampling recommended."

        return FieldAssessment(
            mission_id=mission_id,
            total_stations_scouted=total,
            balanced_stations_count=balanced_cnt,
            moderate_stations_count=moderate_cnt,
            imbalanced_stations_count=imbalanced_cnt,
            unknown_stations_count=unknown_cnt,
            average_pdr=avg_pdr,
            average_temperature_c=avg_temp,
            average_humidity_percent=avg_hum,
            average_soil_moisture_percent=avg_sm,
            overall_field_state=field_state,
            field_recommendation=rec,
            hotspot_stations=hotspots,
        )
