import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config import settings
from app.schemas.rules import AdviceItem, AdviceAction

logger = logging.getLogger(__name__)

class TemplateFallback:
    """
    Deterministic DLT-certified fallback message generator.
    Activated whenever:
    1. LLM API is unavailable, rate-limited, or network fails.
    2. LLM generated text fails anti-hallucination validation checks.
    """
    _templates_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def _load_templates(cls) -> Dict[str, Any]:
        if cls._templates_cache is not None:
            return cls._templates_cache

        template_file = settings.DATA_PATH / "language" / "dlt_templates.json"
        if not template_file.exists():
            logger.warning(f"DLT templates file not found at {template_file}. Using built-in fallback.")
            return {}

        try:
            with open(template_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._templates_cache = data.get("templates", {})
                return cls._templates_cache
        except Exception as e:
            logger.error(f"Error loading DLT templates: {e}")
            return {}

    @classmethod
    def render(
        cls,
        primary_item: AdviceItem,
        crop_name: str,
        stage_name: str,
        language: str = "hi"
    ) -> str:
        templates = cls._load_templates()
        action_key = primary_item.action.value
        lang = language if language in ("hi", "mr", "en") else "hi"

        action_template = templates.get(action_key, {}).get(lang)
        if not action_template:
            # Universal hard fallback if template file is missing
            if lang == "mr":
                return f"किसान साथी: आपल्या {crop_name} पिकासाठी ({stage_name}) सल्ला. कृषी नियमांनुसार काळजी घ्या."
            elif lang == "en":
                return f"KisanSaathi: Advisory for your {crop_name} ({stage_name}). Follow recommended practices."
            else:
                return f"किसान साथी: आपकी {crop_name} फसल ({stage_name}) के लिए सलाह। अनुशंसित कृषि कार्यों का पालन करें।"

        # Extract variable parameters with sensible defaults
        params = primary_item.params or {}
        context = {
            "crop": crop_name,
            "stage": stage_name,
            "rain_prob": int(params.get("rain_prob_pct", 10)),
            "rain_mm": round(params.get("rain_mm", params.get("rain_48h_mm", 0.0)), 1),
            "moisture": round(params.get("soil_moisture_pct", 30.0), 1),
            "temp_c": round(params.get("temp_c", params.get("max_temp_c", 35.0)), 1),
            "wind_kmh": round(params.get("wind_kmh", 10.0), 1),
            "dry_days": params.get("dry_days", 14),
            "das": params.get("das", "")
        }

        try:
            rendered = action_template.format(**context)
            return rendered
        except KeyError as ke:
            logger.warning(f"Missing format key {ke} for template {action_key}. Returning unformatted.")
            return action_template
