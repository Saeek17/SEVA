import logging
from typing import List, Tuple
from app.schemas.crop_config import CropConfig, GrowthStage
from app.schemas.rules import AdviceItem
from app.services.advice_generator.llm_client import GeminiAdviceClient
from app.services.advice_generator.validator import OutputValidator
from app.services.advice_generator.template_fallback import TemplateFallback

logger = logging.getLogger(__name__)

class AdviceGenerator:
    """
    End-to-end Advice Generation Orchestrator.
    Workflow:
    1. Prompts LLM (Gemini or Mock) for plain-language message.
    2. Executes strict anti-hallucination guardrail validation.
    3. If valid -> returns generated message.
    4. If invalid (or LLM failure) -> seamlessly falls back to pre-certified DLT template.
    """
    def __init__(self):
        self.llm_client = GeminiAdviceClient()

    async def generate_advisory(
        self,
        crop: CropConfig,
        stage: GrowthStage,
        das: int,
        advice_items: List[AdviceItem],
        language: str = "hi"
    ) -> Tuple[str, bool, str, str]:
        """
        Returns:
            Tuple of:
            - final_message (str): Verified message for SMS/Voice.
            - validation_passed (bool): Whether LLM output was accepted.
            - validation_notes (str): Reason code from validator.
            - fallback_used (str): 'NONE' or 'DLT_TEMPLATE'.
        """
        if not advice_items:
            empty_msg = TemplateFallback.render(
                None, crop.common_name_hi if language == "hi" else crop.common_name_en, stage.name_en, language
            )
            return empty_msg, True, "NO_ACTION_REQUIRED", "NONE"

        primary_item = advice_items[0]
        crop_name = getattr(crop, f"common_name_{language}", crop.common_name_en)
        stage_name = getattr(stage, f"name_{language}", stage.name_en)

        try:
            # Step 1: Generate candidate message with LLM
            candidate_text = await self.llm_client.generate_message(
                crop_id=crop.crop_id,
                crop_name=crop_name,
                stage_id=stage.stage_id,
                stage_name=stage_name,
                das=das,
                advice_items=advice_items,
                language=language
            )

            # Step 2: Validate against hallucination & numbers
            is_valid, reason = OutputValidator.validate(candidate_text, advice_items, das)

            if is_valid:
                logger.info("Advisory text passed anti-hallucination validation.")
                return candidate_text, True, reason, "NONE"
            else:
                logger.warning(f"Advisory text rejected by validator: {reason}. Falling back to DLT template.")
                fallback_msg = TemplateFallback.render(primary_item, crop_name, stage_name, language)
                return fallback_msg, False, reason, "DLT_TEMPLATE"

        except Exception as e:
            logger.error(f"Unexpected error in advice generator: {e}. Activating DLT fallback.")
            fallback_msg = TemplateFallback.render(primary_item, crop_name, stage_name, language)
            return fallback_msg, False, f"SYSTEM_EXCEPTION: {str(e)}", "DLT_TEMPLATE"
