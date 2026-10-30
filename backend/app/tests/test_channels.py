import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.farmer import Farmer
from app.models.advisory import AdvisoryRun
from app.models.delivery import DeliveryLog
from app.models.push import PushSubscription
from app.security import encrypt_phone, hash_phone
from app.services.delivery.twilio_provider import TwilioDeliveryProvider, absolute_url
from app.services.scheduler.task_scheduler import scheduler_service

TEST_PHONES = ["+919000000101", "+919000000102", "+919000000104"]
PUSH_TEST_ENDPOINT = "https://push.example.com/a"

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # These tests share the dev database: remove only the rows they created.
    db = SessionLocal()
    for phone in TEST_PHONES:
        for farmer in db.query(Farmer).filter(Farmer.phone_hash == hash_phone(phone)).all():
            db.delete(farmer)
    db.query(PushSubscription).filter(PushSubscription.endpoint.in_([PUSH_TEST_ENDPOINT, PUSH_BODY["endpoint"]])).delete(synchronize_session=False)
    db.commit()
    db.close()

def make_farmer(db, phone: str, **overrides) -> Farmer:
    db.query(Farmer).filter(Farmer.phone_hash == hash_phone(phone)).delete()
    db.commit()
    farmer = Farmer(
        full_name="Test Farmer", phone_encrypted=encrypt_phone(phone), phone_hash=hash_phone(phone),
        language="mr", latitude=18.4, longitude=76.5, crop_id="wheat_maharashtra",
        sowing_date=date.today() - timedelta(days=45), is_active=True, **overrides
    )
    db.add(farmer)
    db.commit()
    return farmer

def logs_for(db, farmer_id: str):
    return (
        db.query(DeliveryLog).join(AdvisoryRun, DeliveryLog.advisory_run_id == AdvisoryRun.id)
        .filter(AdvisoryRun.farmer_id == farmer_id).all()
    )

def test_absolute_url(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://api.example.com/")
    assert absolute_url("/api/v1/delivery/audio/a.mp3") == "https://api.example.com/api/v1/delivery/audio/a.mp3"
    assert absolute_url("https://cdn.example.com/a.mp3") == "https://cdn.example.com/a.mp3"
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "")
    assert absolute_url("/api/v1/x.mp3") == "/api/v1/x.mp3"

async def test_whatsapp_skipped_without_sender_and_mocked_with_sender(monkeypatch):
    provider = TwilioDeliveryProvider()
    monkeypatch.setattr(provider, "whatsapp_from", "")
    assert (await provider.send_whatsapp("+919876543210", "hi", "adv"))["status"] == "SKIPPED"

    monkeypatch.setattr(provider, "whatsapp_from", "+14155238886")
    monkeypatch.setattr(settings, "DRY_RUN", True)
    res = await provider.send_whatsapp("+919876543210", "hi", "adv")
    assert res["status"] == "DELIVERED" and res["sid"].startswith("WA_")

async def test_whatsapp_is_preferred_over_sms(monkeypatch):
    db = SessionLocal()
    farmer = make_farmer(db, "+919000000101")
    monkeypatch.setattr(scheduler_service.delivery, "whatsapp_from", "+14155238886")
    monkeypatch.setattr(settings, "DRY_RUN", True)
    await scheduler_service.process_farmer_advisory(farmer, db, is_urgent_only=False)
    channels = sorted(l.channel for l in logs_for(db, farmer.id))
    assert "WHATSAPP" in channels and "SMS" not in channels
    db.close()

async def test_sms_fallback_when_whatsapp_fails(monkeypatch):
    db = SessionLocal()
    farmer = make_farmer(db, "+919000000102")

    async def failing(*args, **kwargs):
        return {"provider": "TWILIO", "status": "FAILED", "sid": None, "error": "boom"}

    monkeypatch.setattr(scheduler_service.delivery, "send_whatsapp", failing)
    await scheduler_service.process_farmer_advisory(farmer, db, is_urgent_only=False)
    channels = sorted(l.channel for l in logs_for(db, farmer.id))
    assert "WHATSAPP" in channels and "SMS" in channels
    db.close()

def test_missed_call_rejects_and_triggers_callback(monkeypatch):
    called = []

    async def fake_callback(phone, db):
        called.append(phone)
        return True

    monkeypatch.setattr(scheduler_service, "call_back_farmer", fake_callback)
    with TestClient(app) as client:
        resp = client.post("/api/v1/delivery/webhooks/ivr", data={"From": "+919000000103"})
    assert resp.status_code == 200
    assert "<Reject" in resp.text
    assert called == ["+919000000103"]

async def test_callback_is_voice_only_and_rate_limited():
    db = SessionLocal()
    farmer = make_farmer(db, "+919000000104")
    assert await scheduler_service.call_back_farmer("+919000000104", db) is True
    assert await scheduler_service.call_back_farmer("+919000000104", db) is True  # within 10 min: skipped

    logs = logs_for(db, farmer.id)
    assert [l.channel for l in logs] == ["VOICE"]
    assert await scheduler_service.call_back_farmer("+919000000199", db) is False  # unregistered
    db.close()

PUSH_BODY = {
    "endpoint": "https://push.example.com/send/test-endpoint-1",
    "keys": {"p256dh": "BPk", "auth": "auth123"},
    "language": "mr", "latitude": 18.4, "longitude": 76.5,
    "crop_id": "wheat_maharashtra", "das": 45,
}

def test_push_api_flow(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    with TestClient(app) as client:
        assert client.get("/api/v1/push/public-key").json() == {"enabled": True, "public_key": "pub"}
        assert client.post("/api/v1/push/subscribe", json=PUSH_BODY).status_code == 201
        assert client.post("/api/v1/push/subscribe", json={**PUSH_BODY, "das": 60}).status_code == 201  # upsert
        assert client.post("/api/v1/push/subscribe", json={**PUSH_BODY, "crop_id": "nope"}).status_code == 404
        assert client.post("/api/v1/push/unsubscribe", json={"endpoint": PUSH_BODY["endpoint"]}).status_code == 200

    db = SessionLocal()
    subs = db.query(PushSubscription).filter(PushSubscription.endpoint == PUSH_BODY["endpoint"]).all()
    assert len(subs) == 1 and subs[0].is_active is False
    assert subs[0].sowing_date == date.today() - timedelta(days=60)
    db.close()

def test_push_disabled_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")
    with TestClient(app) as client:
        assert client.get("/api/v1/push/public-key").json()["enabled"] is False
        assert client.post("/api/v1/push/subscribe", json=PUSH_BODY).status_code == 503

async def test_push_batch_sends_and_deactivates_gone(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    monkeypatch.setattr(settings, "DRY_RUN", True)

    db = SessionLocal()
    db.query(PushSubscription).filter(PushSubscription.endpoint == PUSH_TEST_ENDPOINT).delete()
    db.add(PushSubscription(endpoint=PUSH_TEST_ENDPOINT, p256dh="k", auth="a", language="mr",
                            latitude=18.4, longitude=76.5, crop_id="wheat_maharashtra",
                            sowing_date=date.today() - timedelta(days=45)))
    db.commit()

    assert await scheduler_service.run_push_batch(db) >= 1
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == PUSH_TEST_ENDPOINT).first()
    assert sub.last_sent_at is not None

    async def gone(sub, *args, **kwargs):
        # Only the test subscription is "revoked"; real rows in the shared dev DB are left alone.
        return {"status": "GONE", "error": "410"} if sub.endpoint == PUSH_TEST_ENDPOINT else {"status": "SKIPPED"}

    monkeypatch.setattr("app.services.scheduler.task_scheduler.send_push", gone)
    await scheduler_service.run_push_batch(db)
    db.refresh(sub)
    assert sub.is_active is False
    db.close()
