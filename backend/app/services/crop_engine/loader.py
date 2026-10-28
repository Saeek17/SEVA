import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from app.config import settings
from app.schemas.crop_config import CropConfig

logger = logging.getLogger(__name__)

class CropConfigLoader:
    """
    Dynamic Crop Configuration Loader.
    Scans the /config/crops directory for YAML/JSON configurations.
    Zero hardcoded crop names or thresholds in application code.
    Fails loudly with strict Pydantic validation on malformed or incomplete files.
    """
    _cache: Dict[str, CropConfig] = {}

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or settings.CROPS_CONFIG_PATH

    def load_all_crops(self, force_reload: bool = False) -> Dict[str, CropConfig]:
        if self._cache and not force_reload:
            return self._cache

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Crop configuration directory does not exist: {self.config_dir}")

        loaded: Dict[str, CropConfig] = {}
        errors: List[str] = []

        # Scan for yaml and yml files
        config_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        if not config_files:
            logger.warning(f"No crop configuration YAML files found in {self.config_dir}")

        for file_path in sorted(config_files):
            try:
                crop = self.load_crop_file(file_path)
                loaded[crop.crop_id] = crop
                logger.info(f"Loaded crop config: {crop.crop_id} ({crop.common_name_en}) from {file_path.name}")
            except Exception as e:
                err_msg = f"Failed to load crop config '{file_path.name}': {e}"
                logger.error(err_msg)
                errors.append(err_msg)

        if errors:
            raise ValueError(f"Crop configuration validation errors encountered:\n" + "\n".join(errors))

        self._cache = loaded
        return loaded

    def load_crop_file(self, file_path: Path) -> CropConfig:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        if not isinstance(raw_data, dict):
            raise ValueError(f"File {file_path.name} does not contain a valid YAML dictionary mapping.")

        # Validate with Pydantic
        crop_config = CropConfig(**raw_data)
        return crop_config

    def get_crop(self, crop_id: str) -> Optional[CropConfig]:
        crops = self.load_all_crops()
        return crops.get(crop_id)

    def list_available_crops(self) -> List[Dict[str, Any]]:
        """Return dynamic metadata list for farmer registration form dropdown and simulation."""
        crops = self.load_all_crops()
        result = []
        for crop in crops.values():
            result.append({
                "crop_id": crop.crop_id,
                "common_name_en": crop.common_name_en,
                "common_name_hi": crop.common_name_hi,
                "common_name_mr": crop.common_name_mr,
                "scientific_name": crop.scientific_name,
                "typical_duration_days": crop.typical_duration_days,
                "region": crop.region,
                "stage_count": len(crop.stages)
            })
        return result

# Global singleton instance
crop_loader = CropConfigLoader()
