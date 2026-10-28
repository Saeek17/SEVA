import re
import unicodedata
from typing import List, Tuple, Set, Any
from app.schemas.rules import AdviceItem, AdviceAction

# Devanagari digit translation table to ASCII
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

class OutputValidator:
    """
    Strict Anti-Hallucination Guardrail Validator.
    Verifies that:
    1. Generated text does not exceed 320 characters (SMS segment limit).
    2. No agricultural action is suggested unless explicitly present in structured advice.
    3. No hallucinated numbers/dosages are introduced that differ from params.
    """
    MAX_SMS_LENGTH = 320

    # Keywords for action presence detection across Hindi, Marathi, English
    IRRIGATION_AFFIRMATIVE_KEYWORDS = [
        "सिंचाई करें", "पानी दें", "हल्की सिंचाई", "पानी लगाएं", "पलेवा",
        "पाणी द्या", "हलके पाणी", "सिंचन करा", "पाणी देणे",
        "irrigate", "apply irrigation", "water the crop", "provide irrigation"
    ]

    SPRAY_AFFIRMATIVE_KEYWORDS = [
        "छिड़काव करें", "दवा छिड़कें", "स्प्रे करें", "कीटनाशक",
        "फवारणी करावी", "फवारणी करा", "औषध फवारा", "कीटकनाशक",
        "apply spray", "safe to spray", "spray pesticide", "spray fungicide"
    ]

    HARVEST_AFFIRMATIVE_KEYWORDS = [
        "कटाई करें", "कटाई की योजना", "फसल काटें",
        "कापणी करा", "कापणीचे नियोजन",
        "harvest crop", "plan harvest", "harvest the field"
    ]

    @classmethod
    def validate(
        cls,
        generated_text: str,
        structured_items: List[AdviceItem],
        das: int
    ) -> Tuple[bool, str]:
        if not generated_text or not generated_text.strip():
            return False, "EMPTY_MESSAGE: LLM generated empty text"

        text = generated_text.strip()

        # 1. Length constraint (Max 320 chars)
        if len(text) > cls.MAX_SMS_LENGTH:
            return False, f"LENGTH_OVERFLOW: Message length {len(text)} exceeds {cls.MAX_SMS_LENGTH} characters"

        # Approved actions set
        approved_actions: Set[AdviceAction] = {item.action for item in structured_items}
        text_lower = text.lower()

        # 2. Action Whitelist Verification
        # Check Irrigation
        if AdviceAction.IRRIGATE not in approved_actions:
            for kw in cls.IRRIGATION_AFFIRMATIVE_KEYWORDS:
                if kw in text_lower:
                    return False, f"UNAPPROVED_ACTION: Irrigation advised in text ('{kw}') but not in structured advice"

        # Check Spraying (Safe Spray)
        if AdviceAction.SAFE_SPRAY not in approved_actions:
            # If safe spray is NOT approved, text must NOT tell farmer to spray
            for kw in cls.SPRAY_AFFIRMATIVE_KEYWORDS:
                if kw in text_lower and "न करें" not in text_lower and "करू नका" not in text_lower and "do not" not in text_lower and "postpone" not in text_lower:
                    return False, f"UNAPPROVED_ACTION: Spraying advised in text ('{kw}') but not in structured advice"

        # Check Harvesting
        if AdviceAction.HARVEST_READY not in approved_actions:
            for kw in cls.HARVEST_AFFIRMATIVE_KEYWORDS:
                if kw in text_lower:
                    return False, f"UNAPPROVED_ACTION: Harvest advised in text ('{kw}') but not in structured advice"

        # 3. Numeric Fidelity Verification
        # Normalize devanagari numerals to standard digits (०-९ -> 0-9)
        normalized_text = text.translate(DEVANAGARI_DIGITS)

        # Collect all approved numbers from params and context
        approved_numbers: Set[float] = {
            float(das),
            24.0, 48.0, 72.0, # Standard forecast hour buckets
            1.0, 2.0, 3.0, 4.0, 5.0, 7.0 # Common day counts
        }

        for item in structured_items:
            params = item.params or {}
            for k, val in params.items():
                if isinstance(val, (int, float)):
                    approved_numbers.add(round(float(val), 1))
                    approved_numbers.add(float(int(val))) # integer version

        # Extract all numbers from generated text
        found_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", normalized_text)
        for num_str in found_numbers:
            val = float(num_str)
            # Allow matching within a small float tolerance (0.1) or integer equality
            matched = any(abs(val - app_num) < 0.2 for app_num in approved_numbers)
            if not matched:
                return False, f"NUMERICAL_DRIFT: Hallucinated number '{num_str}' not found in structured advice params"

        return True, "VALIDATION_PASSED"
