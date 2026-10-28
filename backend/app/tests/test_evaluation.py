import pytest
from app.services.evaluation.gkms_evaluator import GKMSEvaluator
from fastapi.testclient import TestClient
from app.main import app

def test_load_benchmarks():
    benchmarks = GKMSEvaluator.load_benchmarks()
    assert len(benchmarks) >= 4
    first = benchmarks[0]
    assert "district" in first
    assert "expert_advice" in first
    assert "observed_conditions" in first

def test_run_evaluation():
    results = GKMSEvaluator.run_evaluation()
    assert results["status"] == "success"
    assert results["total_evaluated"] >= 4
    # Check that agreement percentages are computed
    assert 0.0 <= results["overall_exact_agreement_pct"] <= 100.0
    assert 0.0 <= results["irrigation_agreement_pct"] <= 100.0
    assert 0.0 <= results["spraying_agreement_pct"] <= 100.0
    assert results["irrigation_agreement_pct"] >= 75.0 # High alignment with ground truth
    assert isinstance(results["records"], list)
    assert isinstance(results["mismatches"], list)

def test_evaluation_api_endpoints():
    with TestClient(app) as client:
        resp = client.get("/api/v1/evaluation/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "irrigation_agreement_pct" in data

        resp_bench = client.get("/api/v1/evaluation/benchmarks")
        assert resp_bench.status_code == 200
        bench_data = resp_bench.json()
        assert bench_data["count"] >= 4
