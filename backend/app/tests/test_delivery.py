import pytest
from datetime import datetime, date
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.farmer import Farmer
from app.models.advisory import AdvisoryRun, AdviceItemModel
from app.security import encrypt_phone, hash_phone
from app.services.delivery.tts_service import GoogleTTSService
from app.services.delivery.twilio_provider import TwilioDeliveryProvider
from app.services.scheduler.deduplicator import AlertDeduplicator

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup if needed

@pytest.mark.asyncio
async def test_tts_synthesis_creates_valid_audio():
    audio_url = await GoogleTTSService.synthesize("किसान साथी: नमस्कार। अपनी फसल की देखभाल करें।", "hi")
    assert audio_url.startswith("/api/v1/delivery/audio/")
    filename = audio_url.split("/")[-1]
    
    # Check that file exists on disk
    file_path = Path("app/static/audio") / filename
    if not file_path.exists():
        file_path = Path("backend/app/static/audio") / filename
    assert file_path.exists()
    assert file_path.stat().st_size > 1000

@pytest.mark.asyncio
async def test_twilio_mock_dispatch():
    provider = TwilioDeliveryProvider()
    sms_res = await provider.send_sms("+919876543210", "Test KisanSaathi message", "adv-123")
    assert sms_res["status"] in ("SENT", "DELIVERED")
    assert sms_res["sid"].startswith("SM_")

    voice_res = await provider.make_voice_call("+919876543210", "/audio/test.wav", "adv-123")
    assert voice_res["status"] in ("QUEUED", "DELIVERED")
    assert voice_res["sid"].startswith("CA_")

def test_stop_opt_out_webhook(setup_db):
    db: Session = SessionLocal()
    phone = "+919988776655"
    p_hash = hash_phone(phone)

    # Clean existing
    db.query(Farmer).filter(Farmer.phone_hash == p_hash).delete()
    db.commit()

    # Create active farmer
    farmer = Farmer(
        full_name="Ramesh Patil",
        phone_encrypted=encrypt_phone(phone),
        phone_hash=p_hash,
        language="mr",
        latitude=19.1,
        longitude=74.7,
        crop_id="wheat_maharashtra",
        sowing_date=date(2023, 11, 1),
        is_active=True
    )
    db.add(farmer)
    db.commit()

    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/delivery/webhooks/sms",
            data={
                "From": phone,
                "Body": "STOP",
                "MessageSid": "SM_incoming_123"
            }
        )
        assert resp.status_code == 200
        assert "unsubscribed" in resp.text.lower()

    # Verify database state
    db.refresh(farmer)
    assert farmer.is_active is False
    db.close()

def test_alert_deduplication(setup_db):
    db: Session = SessionLocal()
    farmer_id = "test-dedup-farmer-1"

    # Create run and high urgency alert
    run = AdvisoryRun(
        farmer_id=farmer_id,
        crop_id="wheat_maharashtra",
        growth_stage="Flowering",
        das=50,
        generated_message="Test alert",
        language="hi",
        fallback_used="NONE",
        created_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()

    item = AdviceItemModel(
        advisory_run_id=run.id,
        action="HEAT_ALERT",
        urgency="HIGH",
        reason_code="EXTREME_HEAT_STRESS"
    )
    db.add(item)
    db.commit()

    # Now verify deduplication detects it
    is_dupe = AlertDeduplicator.is_duplicate_alert(db, farmer_id, "EXTREME_HEAT_STRESS")
    assert is_dupe is True

    # Different reason code should not be dupe
    is_other_dupe = AlertDeduplicator.is_duplicate_alert(db, farmer_id, "EXCESS_RAIN_WATERLOGGING")
    assert is_other_dupe is False

    db.close()
