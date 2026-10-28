import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "wheat_maharashtra" in data["available_crops"]
    assert "soybean_maharashtra" in data["available_crops"]

def test_list_crops_endpoint(client):
    response = client.get("/api/v1/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) >= 2
    crop_ids = [c["crop_id"] for c in crops]
    assert "wheat_maharashtra" in crop_ids
    assert "soybean_maharashtra" in crop_ids

def test_get_crop_detail(client):
    response = client.get("/api/v1/crops/wheat_maharashtra")
    assert response.status_code == 200
    data = response.json()
    assert data["crop_id"] == "wheat_maharashtra"
    assert len(data["stages"]) >= 4

def test_resolve_crop_stage(client):
    response = client.get("/api/v1/crops/wheat_maharashtra/stage/21")
    assert response.status_code == 200
    data = response.json()
    assert data["das"] == 21
    assert data["stage"]["stage_id"] == "germination_crown_root"
    assert data["stage"]["critical_for_irrigation"] is True
