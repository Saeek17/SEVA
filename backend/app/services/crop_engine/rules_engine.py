import logging
from typing import List, Dict, Any
from app.schemas.crop_config import CropConfig, GrowthStage
from app.schemas.rules import (
    AdviceItem,
    AdviceAction,
    UrgencyLevel,
    EnvironmentalSnapshot
)

logger = logging.getLogger(__name__)

class RulesEngine:
    """
    Deterministic Agronomic Rules Engine.
    Evaluates environmental facts against expert-sourced crop thresholds.
    NEVER relies on an LLM to decide agricultural advice.
    Produces structured AdviceItem objects with explicit urgency, reason codes,
    data confidence, and university/KVK source citations.
    """
    @classmethod
    def evaluate(
        cls,
        crop: CropConfig,
        stage: GrowthStage,
        das: int,
        env: EnvironmentalSnapshot
    ) -> List[AdviceItem]:
        items: List[AdviceItem] = []
        sources = env.sources_used.copy()

        # ----------------------------------------------------------------------
        # 1. WEATHER HAZARD RULES (Urgency: HIGH)
        # ----------------------------------------------------------------------
        # A. Heat Stress Warning
        heat_threshold = min(stage.temperature.heat_stress_c, crop.general_thresholds.heat_stress_warning_c)
        if env.forecast_max_temp_c >= heat_threshold:
            items.append(AdviceItem(
                action=AdviceAction.HEAT_ALERT,
                urgency=UrgencyLevel.HIGH,
                reason_code="EXTREME_HEAT_STRESS",
                params={
                    "temp_c": env.forecast_max_temp_c,
                    "threshold_c": heat_threshold,
                    "stage_name": stage.name_en,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.temperature.source]
            ))

        # B. Heavy Rain / Waterlogging Hazard
        rain_threshold = crop.general_thresholds.excess_rain_24h_mm
        if env.forecast_rain_24h_mm >= rain_threshold or env.forecast_rain_48h_mm >= 50.0:
            items.append(AdviceItem(
                action=AdviceAction.RAIN_ALERT,
                urgency=UrgencyLevel.HIGH,
                reason_code="EXCESS_RAIN_WATERLOGGING",
                params={
                    "rain_mm": env.forecast_rain_24h_mm,
                    "rain_48h_mm": env.forecast_rain_48h_mm,
                    "threshold_mm": rain_threshold,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [crop.general_thresholds.excess_rain_source]
            ))

        # C. Frost / Cold Injury Risk
        frost_threshold = max(stage.temperature.frost_stress_c, crop.general_thresholds.frost_stress_warning_c)
        if env.forecast_min_temp_c <= frost_threshold:
            items.append(AdviceItem(
                action=AdviceAction.FROST_ALERT,
                urgency=UrgencyLevel.HIGH,
                reason_code="COLD_FROST_INJURY_RISK",
                params={
                    "min_temp_c": env.forecast_min_temp_c,
                    "threshold_c": frost_threshold,
                    "stage_name": stage.name_en,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [crop.general_thresholds.frost_stress_source]
            ))

        # D. Prolonged Dry Spell / Drought
        if env.consecutive_dry_days >= 12 and env.forecast_rain_48h_mm < 3.0 and env.soil_moisture_0_7cm_pct < stage.moisture.depletion_trigger_pct:
            items.append(AdviceItem(
                action=AdviceAction.DROUGHT_ALERT,
                urgency=UrgencyLevel.HIGH,
                reason_code="PROLONGED_DRY_SPELL_DROUGHT",
                params={
                    "dry_days": env.consecutive_dry_days,
                    "soil_moisture_pct": env.soil_moisture_0_7cm_pct,
                    "crop_name": crop.common_name_en,
                    "stage_name": stage.name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + ["NASA POWER 30-Day Agromet Archive", stage.moisture.source]
            ))

        # ----------------------------------------------------------------------
        # 2. IRRIGATION RULES (Urgency: HIGH to LOW)
        # ----------------------------------------------------------------------
        is_maturity = (das >= (crop.typical_duration_days - 15)) or (stage.stage_id == "maturity_harvesting")

        if is_maturity:
            # Strictly withhold irrigation before harvest
            items.append(AdviceItem(
                action=AdviceAction.SKIP_IRRIGATION,
                urgency=UrgencyLevel.MEDIUM,
                reason_code="MATURITY_WITHHOLD_IRRIGATION",
                params={
                    "das": das,
                    "stage_name": stage.name_en,
                    "crop_name": crop.common_name_en,
                    "reason": "Water withholding required for grain drydown and lodging prevention"
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.moisture.source]
            ))
        elif env.forecast_rain_48h_mm >= 15.0 or env.soil_moisture_0_7cm_pct >= stage.moisture.waterlogging_threshold_pct:
            # Skip irrigation because significant rain is imminent or soil is already saturated
            items.append(AdviceItem(
                action=AdviceAction.SKIP_IRRIGATION,
                urgency=UrgencyLevel.MEDIUM,
                reason_code="ANTICIPATED_RAIN_OR_SATURATED",
                params={
                    "rain_mm": env.forecast_rain_48h_mm,
                    "soil_moisture_pct": env.soil_moisture_0_7cm_pct,
                    "crop_name": crop.common_name_en,
                    "stage_name": stage.name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.moisture.source]
            ))
        elif env.soil_moisture_0_7cm_pct < stage.moisture.depletion_trigger_pct and env.forecast_rain_48h_mm < 5.0:
            # Irrigation needed
            if stage.critical_for_irrigation:
                items.append(AdviceItem(
                    action=AdviceAction.IRRIGATE,
                    urgency=UrgencyLevel.HIGH,
                    reason_code="CRITICAL_STAGE_MOISTURE_DEFICIT",
                    params={
                        "soil_moisture_pct": env.soil_moisture_0_7cm_pct,
                        "trigger_pct": stage.moisture.depletion_trigger_pct,
                        "stage_name": stage.name_en,
                        "crop_name": crop.common_name_en,
                        "rain_prob_pct": env.rain_probability_pct,
                        "critical_reason": stage.critical_reason or "Critical yield-determining growth stage"
                    },
                    data_confidence=env.data_confidence,
                    sources_used=sources + [stage.moisture.source]
                ))
            else:
                items.append(AdviceItem(
                    action=AdviceAction.IRRIGATE,
                    urgency=UrgencyLevel.MEDIUM,
                    reason_code="SOIL_MOISTURE_DEPLETION",
                    params={
                        "soil_moisture_pct": env.soil_moisture_0_7cm_pct,
                        "trigger_pct": stage.moisture.depletion_trigger_pct,
                        "stage_name": stage.name_en,
                        "crop_name": crop.common_name_en,
                        "rain_prob_pct": env.rain_probability_pct
                    },
                    data_confidence=env.data_confidence,
                    sources_used=sources + [stage.moisture.source]
                ))
        else:
            # Moisture is currently adequate
            items.append(AdviceItem(
                action=AdviceAction.SKIP_IRRIGATION,
                urgency=UrgencyLevel.LOW,
                reason_code="ADEQUATE_SOIL_MOISTURE",
                params={
                    "soil_moisture_pct": env.soil_moisture_0_7cm_pct,
                    "stage_name": stage.name_en,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.moisture.source]
            ))

        # ----------------------------------------------------------------------
        # 3. SPRAYING SAFETY RULES (Urgency: MEDIUM to LOW)
        # ----------------------------------------------------------------------
        # Do not spray at maturity stage
        if is_maturity:
            items.append(AdviceItem(
                action=AdviceAction.AVOID_SPRAY,
                urgency=UrgencyLevel.MEDIUM,
                reason_code="PRE_HARVEST_INTERVAL_PROHIBITION",
                params={
                    "das": das,
                    "stage_name": stage.name_en,
                    "crop_name": crop.common_name_en,
                    "reason": "Chemical spraying prohibited near harvest to avoid toxic residues"
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.spraying.source]
            ))
        elif env.wind_speed_kmh > stage.spraying.max_wind_kmh:
            items.append(AdviceItem(
                action=AdviceAction.AVOID_SPRAY,
                urgency=UrgencyLevel.MEDIUM,
                reason_code="HIGH_WIND_DRIFT_HAZARD",
                params={
                    "wind_kmh": env.wind_speed_kmh,
                    "max_safe_wind_kmh": stage.spraying.max_wind_kmh,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.spraying.source]
            ))
        elif env.rain_probability_pct > stage.spraying.max_rain_probability_pct or env.forecast_rain_24h_mm >= 5.0:
            items.append(AdviceItem(
                action=AdviceAction.AVOID_SPRAY,
                urgency=UrgencyLevel.MEDIUM,
                reason_code="RAIN_WASHOFF_RISK",
                params={
                    "rain_prob_pct": env.rain_probability_pct,
                    "forecast_rain_24h_mm": env.forecast_rain_24h_mm,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.spraying.source]
            ))
        elif env.forecast_max_temp_c > stage.spraying.max_temp_c:
            items.append(AdviceItem(
                action=AdviceAction.AVOID_SPRAY,
                urgency=UrgencyLevel.LOW,
                reason_code="HIGH_TEMP_EVAPORATION_SCORCH",
                params={
                    "max_temp_c": env.forecast_max_temp_c,
                    "safe_temp_c": stage.spraying.max_temp_c,
                    "crop_name": crop.common_name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.spraying.source]
            ))
        else:
            items.append(AdviceItem(
                action=AdviceAction.SAFE_SPRAY,
                urgency=UrgencyLevel.LOW,
                reason_code="FAVORABLE_SPRAY_WINDOW",
                params={
                    "wind_kmh": env.wind_speed_kmh,
                    "max_temp_c": env.forecast_max_temp_c,
                    "rain_prob_pct": env.rain_probability_pct,
                    "crop_name": crop.common_name_en,
                    "stage_name": stage.name_en
                },
                data_confidence=env.data_confidence,
                sources_used=sources + [stage.spraying.source]
            ))

        # ----------------------------------------------------------------------
        # 4. HARVEST TIMING RULES (Urgency: HIGH)
        # ----------------------------------------------------------------------
        if is_maturity and env.forecast_rain_7d_mm < 10.0:
            items.append(AdviceItem(
                action=AdviceAction.HARVEST_READY,
                urgency=UrgencyLevel.HIGH,
                reason_code="OPTIMAL_DRY_HARVEST_WINDOW",
                params={
                    "das": das,
                    "crop_name": crop.common_name_en,
                    "forecast_rain_7d_mm": env.forecast_rain_7d_mm
                },
                data_confidence=env.data_confidence,
                sources_used=sources + ["SAU Package of Practices - Harvest Timing"]
            ))

        # ----------------------------------------------------------------------
        # SORTING: Prioritize HIGH urgency first, then MEDIUM, then LOW
        # ----------------------------------------------------------------------
        urgency_order = {
            UrgencyLevel.HIGH: 0,
            UrgencyLevel.MEDIUM: 1,
            UrgencyLevel.LOW: 2
        }
        items.sort(key=lambda x: urgency_order.get(x.urgency, 99))

        return items
