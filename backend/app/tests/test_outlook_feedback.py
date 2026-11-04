import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.feedback import AdviceFeedback
from app.services.data_clients.aggregator import EnvironmentalAggregator

TEST_CROP = "test_feedback_crop"

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # The tests share the dev database: remove only the rows they created.
    db = SessionLocal()
    db.query(AdviceFeedback).filter(AdviceFeedback.crop_id == TEST_CROP).delete()
    db.commit()
    db.close()

def sample_daily():
    return {
        "time": ["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"],
        "precipitation_sum": [0.0, 4.2, 12.5, None, 0.0, 1.0, 0.0],
        "precipitation_probability_max": [5, 60, 90, 40, 10, 20, 0],
        "temperature_2m_max": [33.1, 31.0, 28.4, 29.9, 32.0, 33.0, 34.0],
        "temperature_2m_min": [19.0, 20.0, 21.5, 20.0, 18.0, 18.0, 19.0],
        "wind_speed_10m_max": [8.0, 12.5, 25.0, 15.0, 9.0, 7.0, 6.0],
    }

def test_daily_outlook_takes_five_days_and_handles_missing_values():
    days = EnvironmentalAggregator._daily_outlook(sample_daily())
    assert len(days) == 5
    assert days[0].date == "2026-11-04" and days[0].rain_mm == 0.0
    assert days[2].rain_mm == 12.5 and days[2].rain_prob_pct == 90
    assert days[3].rain_mm == 0.0  # a missing (None) value becomes 0, not a crash

def test_daily_outlook_empty_when_source_down():
    assert EnvironmentalAggregator._daily_outlook({}) == []
    assert EnvironmentalAggregator._daily_outlook({"time": ["2026-11-04"], "precipitation_sum": []}) == []

def test_simulate_response_includes_outlook_field():
    with TestClient(app) as client:
        resp = client.post("/api/v1/simulate", json={
            "latitude": 18.4, "longitude": 76.5, "crop_id": "wheat_maharashtra", "das": 45, "language": "mr"})
    assert resp.status_code == 200
    outlook = resp.json()["environmental_data"]["daily_outlook"]
    assert isinstance(outlook, list) and len(outlook) <= 5
    for day in outlook:
        assert {"date", "rain_mm", "rain_prob_pct", "max_temp_c"} <= set(day)

def test_feedback_is_recorded_and_summarised():
    with TestClient(app) as client:
        before = client.get("/api/v1/feedback/summary").json()
        body = {"crop_id": TEST_CROP, "action": "IRRIGATE", "reason_code": "SOIL_MOISTURE_DEPLETION", "das": 45, "language": "mr"}
        assert client.post("/api/v1/feedback", json={**body, "helpful": True}).status_code == 201
        assert client.post("/api/v1/feedback", json={**body, "helpful": False}).status_code == 201
        after = client.get("/api/v1/feedback/summary").json()
    assert after["total"] == before["total"] + 2
    assert after["helpful"] == before["helpful"] + 1
    assert after["by_action"]["IRRIGATE"]["not_helpful"] >= 1

def test_feedback_rejects_bad_input():
    with TestClient(app) as client:
        bad_lang = {"helpful": True, "crop_id": TEST_CROP, "action": "IRRIGATE", "language": "xx"}
        assert client.post("/api/v1/feedback", json=bad_lang).status_code == 422
        assert client.post("/api/v1/feedback", json={"crop_id": TEST_CROP, "action": "IRRIGATE"}).status_code == 422
