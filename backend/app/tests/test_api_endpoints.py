import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.farmer import Farmer

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

def test_register_and_list_farmers(client):
    test_phone = "+919822334455"
    db = SessionLocal()
    from app.security import hash_phone
    db.query(Farmer).filter(Farmer.phone_hash == hash_phone(test_phone)).delete()
    db.commit()
    db.close()

    # Register new farmer
    payload = {
        "full_name": "Suresh Deshmukh",
        "phone_number": test_phone,
        "language": "mr",
        "latitude": 19.8762,
        "longitude": 75.3433,
        "district": "Aurangabad / Chhatrapati Sambhajinagar",
        "crop_id": "soybean_maharashtra",
        "sowing_date": "2024-06-25",
        "consent_sms": True,
        "consent_voice": True
    }
    resp = client.post("/api/v1/farmers", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Suresh Deshmukh"
    assert data["phone_masked"].endswith("4455")
    farmer_id = data["id"]

    # List farmers
    list_resp = client.get("/api/v1/farmers")
    assert list_resp.status_code == 200
    farmers = list_resp.json()
    assert any(f["id"] == farmer_id for f in farmers)

    # Duplicate phone rejection
    dup_resp = client.post("/api/v1/farmers", json=payload)
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"]

def test_simulate_farmer_pipeline(client):
    # Run sandbox simulation for wheat at CRI stage
    sim_payload = {
        "latitude": 18.5204,
        "longitude": 73.8567,
        "crop_id": "wheat_maharashtra",
        "das": 21,
        "language": "hi",
        "farmer_name": "Demo Farmer Pune"
    }
    resp = client.post("/api/v1/simulate", json=sim_payload)
    assert resp.status_code == 200
    sim_data = resp.json()
    assert sim_data["status"] == "success"
    assert sim_data["crop_id"] == "wheat_maharashtra"
    assert sim_data["growth_stage"] == "Crown Root Initiation (CRI)"
    assert len(sim_data["advice_items"]) >= 1
    assert len(sim_data["generated_message"]) <= 320
    assert sim_data["voice_audio_url"].startswith("/api/v1/delivery/audio/")

def test_trigger_batch_advisories(client):
    resp = client.post("/api/v1/advisories/run-batch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

    # Check that advisories list has records
    adv_resp = client.get("/api/v1/advisories")
    assert adv_resp.status_code == 200
    advisories = adv_resp.json()
    assert len(advisories) >= 1
    assert "advice_items" in advisories[0]
    assert "delivery_logs" in advisories[0]
