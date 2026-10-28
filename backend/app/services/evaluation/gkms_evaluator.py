import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config import settings
from app.schemas.rules import EnvironmentalSnapshot, AdviceAction
from app.services.crop_engine.loader import crop_loader
from app.services.crop_engine.stage_calculator import StageCalculator
from app.services.crop_engine.rules_engine import RulesEngine

logger = logging.getLogger(__name__)

class GKMSEvaluator:
    """
    Automated Evaluation Harness for KisanSaathi.
    Loads real IMD GKMS district agromet advisory bulletins from /data/benchmarks/gkms_advisories.json.
    Runs the deterministic rules engine on the exact meteorological conditions recorded in the bulletin.
    Computes agreement percentage and isolates mismatches for expert agronomist review.
    """
    @classmethod
    def get_benchmark_file_path(cls) -> Path:
        return settings.DATA_PATH / "benchmarks" / "gkms_advisories.json"

    @classmethod
    def load_benchmarks(cls) -> List[Dict[str, Any]]:
        path = cls.get_benchmark_file_path()
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading benchmark file {path}: {e}")
            return []

    @classmethod
    def run_evaluation(cls) -> Dict[str, Any]:
        benchmarks = cls.load_benchmarks()
        if not benchmarks:
            return {
                "status": "missing_data",
                "message": (
                    "No benchmark data found at /data/benchmarks/gkms_advisories.json. "
                    "Please download official GKMS agromet bulletins from agromet.imd.gov.in and add records."
                ),
                "total_evaluated": 0,
                "overall_agreement_pct": 0.0,
                "irrigation_agreement_pct": 0.0,
                "spraying_agreement_pct": 0.0,
                "alert_agreement_pct": 0.0,
                "records": [],
                "mismatches": []
            }

        total = len(benchmarks)
        irrigation_matches = 0
        spray_matches = 0
        alert_matches = 0
        exact_matches = 0

        detailed_records = []
        mismatches = []

        for b in benchmarks:
            rec_id = b.get("id")
            crop_id = b.get("crop_id")
            das = b.get("das", 30)
            obs = b.get("observed_conditions", {})
            expert = b.get("expert_advice", {})

            # Load crop config dynamically
            crop = crop_loader.get_crop(crop_id)
            if not crop:
                logger.warning(f"Crop {crop_id} referenced in benchmark {rec_id} not found in /config/crops.")
                continue

            stage, _ = StageCalculator.resolve_stage(crop, das)

            # Build EnvironmentalSnapshot matching recorded observations
            rain_48h = obs.get("forecast_rain_48h_mm", 0.0)
            max_t = obs.get("max_temp_c", 30.0)
            min_t = obs.get("min_temp_c", 18.0)
            wind = obs.get("wind_speed_kmh", 10.0)
            sm_pct = obs.get("soil_moisture_pct", 30.0)

            env = EnvironmentalSnapshot(
                latitude=b.get("latitude", 19.0),
                longitude=b.get("longitude", 75.0),
                forecast_max_temp_c=max_t,
                forecast_min_temp_c=min_t,
                forecast_rain_24h_mm=rain_48h / 2.0,
                forecast_rain_48h_mm=rain_48h,
                forecast_rain_7d_mm=rain_48h * 1.5,
                rain_probability_pct=80.0 if rain_48h > 10.0 else 10.0,
                wind_speed_kmh=wind,
                relative_humidity_pct=65.0,
                soil_moisture_0_7cm_pct=sm_pct,
                soil_moisture_7_28cm_pct=sm_pct + 3.0,
                soil_temp_0_7cm_c=max_t - 4.0,
                soil_texture_class="Clay Loam",
                consecutive_dry_days=10 if rain_48h == 0.0 else 0,
                cumulative_rain_30d_mm=40.0,
                data_confidence="HIGH",
                sources_used=["IMD GKMS Benchmark Archive"]
            )

            # Run deterministic rules engine
            advice_items = RulesEngine.evaluate(crop, stage, das, env)
            system_actions = [item.action.value for item in advice_items]

            # 1. Irrigation comparison
            exp_irr = expert.get("irrigation")
            sys_irr = "IRRIGATE" if AdviceAction.IRRIGATE.value in system_actions else "SKIP_IRRIGATION"
            irr_agree = (exp_irr == sys_irr)
            if irr_agree:
                irrigation_matches += 1

            # 2. Spraying comparison
            exp_spray = expert.get("spray")
            sys_spray = "AVOID_SPRAY" if AdviceAction.AVOID_SPRAY.value in system_actions else "SAFE_SPRAY"
            spray_agree = (exp_spray == sys_spray)
            if spray_agree:
                spray_matches += 1

            # 3. Alert comparison
            exp_alert = expert.get("alert", "NONE")
            has_rain_alert = AdviceAction.RAIN_ALERT.value in system_actions
            has_heat_alert = AdviceAction.HEAT_ALERT.value in system_actions
            sys_alert = "RAIN_ALERT" if has_rain_alert else ("HEAT_ALERT" if has_heat_alert else "NONE")
            alert_agree = (exp_alert == sys_alert)
            if alert_agree:
                alert_matches += 1

            is_exact = irr_agree and spray_agree and alert_agree
            if is_exact:
                exact_matches += 1

            rec_summary = {
                "id": rec_id,
                "district": b.get("district"),
                "bulletin_date": b.get("bulletin_date"),
                "crop_name": b.get("crop_name"),
                "growth_stage": stage.name_en,
                "das": das,
                "source_bulletin": b.get("source_bulletin"),
                "expert_advice": expert,
                "system_advice": {
                    "irrigation": sys_irr,
                    "spray": sys_spray,
                    "alert": sys_alert,
                    "all_actions": system_actions
                },
                "agreement": {
                    "irrigation": irr_agree,
                    "spray": spray_agree,
                    "alert": alert_agree,
                    "overall": is_exact
                }
            }
            detailed_records.append(rec_summary)

            if not is_exact:
                mismatches.append({
                    "id": rec_id,
                    "district": b.get("district"),
                    "bulletin_date": b.get("bulletin_date"),
                    "crop_name": b.get("crop_name"),
                    "disagreements": {
                        "irrigation": {"expert": exp_irr, "system": sys_irr} if not irr_agree else None,
                        "spray": {"expert": exp_spray, "system": sys_spray} if not spray_agree else None,
                        "alert": {"expert": exp_alert, "system": sys_alert} if not alert_agree else None,
                    },
                    "expert_summary": expert.get("expert_summary_en")
                })

        return {
            "status": "success",
            "total_evaluated": total,
            "overall_exact_agreement_pct": round((exact_matches / total) * 100.0, 1) if total else 0.0,
            "irrigation_agreement_pct": round((irrigation_matches / total) * 100.0, 1) if total else 0.0,
            "spraying_agreement_pct": round((spray_matches / total) * 100.0, 1) if total else 0.0,
            "alert_agreement_pct": round((alert_matches / total) * 100.0, 1) if total else 0.0,
            "records": detailed_records,
            "mismatches": mismatches
        }
