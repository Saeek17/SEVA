import pytest
from app.schemas.rules import AdviceItem, AdviceAction, UrgencyLevel
from app.services.advice_generator.validator import OutputValidator

@pytest.fixture
def irrigation_only_item():
    return [
        AdviceItem(
            action=AdviceAction.IRRIGATE,
            urgency=UrgencyLevel.HIGH,
            reason_code="CRITICAL_STAGE_MOISTURE_DEFICIT",
            params={"soil_moisture_pct": 25.0, "trigger_pct": 35.0, "das": 21},
            sources_used=["MPKV PoP"]
        )
    ]

@pytest.fixture
def spray_avoid_item():
    return [
        AdviceItem(
            action=AdviceAction.AVOID_SPRAY,
            urgency=UrgencyLevel.MEDIUM,
            reason_code="HIGH_WIND_DRIFT_HAZARD",
            params={"wind_kmh": 22.0, "das": 45},
            sources_used=["VNMKV PoP"]
        )
    ]

def test_valid_irrigation_message_passes(irrigation_only_item):
    text = "किसान साथी: गेहूं की ताज जड़ अवस्था है। मिट्टी में नमी 25% कम है। आज 48 घंटे में बारिश नहीं है, तुरंत हल्की सिंचाई करें।"
    is_valid, reason = OutputValidator.validate(text, irrigation_only_item, das=21)
    assert is_valid is True
    assert reason == "VALIDATION_PASSED"

def test_unapproved_spray_action_rejected(irrigation_only_item):
    # LLM hallucinates pesticide recommendation when only irrigation was approved!
    hallucinated_text = "किसान साथी: गेहूं को हल्की सिंचाई करें और साथ ही इल्ली नियंत्रण के लिए कीटनाशक का छिड़काव करें।"
    is_valid, reason = OutputValidator.validate(hallucinated_text, irrigation_only_item, das=21)
    assert is_valid is False
    assert "UNAPPROVED_ACTION" in reason

def test_unapproved_irrigation_action_rejected(spray_avoid_item):
    # Advice was only avoid spray, but LLM adds irrigation advice!
    hallucinated_text = "किसान साथी: आज तेज हवा 22 किमी/घंटे है। इसलिए फवारणी करू नका आणि शेताला पाणी द्या।"
    is_valid, reason = OutputValidator.validate(hallucinated_text, spray_avoid_item, das=45)
    assert is_valid is False
    assert "UNAPPROVED_ACTION" in reason

def test_hallucinated_number_rejected(irrigation_only_item):
    # Params have 25.0 and das=21. LLM introduces "500 ml" or "80 kg"
    drift_text = "किसान साथी: गेहूं को हल्की सिंचाई करें और प्रति एकड़ 500 मिली टॉनिक दें।"
    is_valid, reason = OutputValidator.validate(drift_text, irrigation_only_item, das=21)
    assert is_valid is False
    assert "NUMERICAL_DRIFT" in reason
    assert "500" in reason

def test_length_overflow_rejected(irrigation_only_item):
    # Message longer than 320 chars must fail
    long_text = "किसान साथी: " + "गेहूं में हल्की सिंचाई करें। " * 25
    assert len(long_text) > 320
    is_valid, reason = OutputValidator.validate(long_text, irrigation_only_item, das=21)
    assert is_valid is False
    assert "LENGTH_OVERFLOW" in reason
