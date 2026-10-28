from datetime import date
from typing import Tuple, Optional
from app.schemas.crop_config import CropConfig, GrowthStage

class StageCalculator:
    """
    Calculates active growth stage based on Days After Sowing (DAS)
    using the dynamic stage boundaries defined in the CropConfig.
    """
    @classmethod
    def calculate_das(cls, sowing_date: date, target_date: Optional[date] = None) -> int:
        ref_date = target_date or date.today()
        das = (ref_date - sowing_date).days
        return max(1, das)

    @classmethod
    def resolve_stage(cls, crop_config: CropConfig, das: int) -> Tuple[GrowthStage, bool]:
        """
        Match DAS to the appropriate growth stage defined in crop config.
        Returns: Tuple[GrowthStage, is_beyond_typical_duration]
        """
        if not crop_config.stages:
            raise ValueError(f"Crop {crop_config.crop_id} has no defined growth stages.")

        # Find stage whose range contains das
        for stage in crop_config.stages:
            if stage.das_start <= das <= stage.das_end:
                return stage, False

        # If das is before stage 1
        if das < crop_config.stages[0].das_start:
            return crop_config.stages[0], False

        # If das is past the last stage (post maturity)
        last_stage = crop_config.stages[-1]
        return last_stage, True
