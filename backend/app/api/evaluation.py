from fastapi import APIRouter
from app.services.evaluation.gkms_evaluator import GKMSEvaluator

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

@router.get("/run")
async def run_evaluation():
    """
    Run evaluation harness comparing KisanSaathi rules engine against
    real IMD GKMS district agromet advisories.
    """
    return GKMSEvaluator.run_evaluation()

@router.get("/benchmarks")
async def list_benchmarks():
    """Return raw benchmark dataset records and instructions."""
    benchmarks = GKMSEvaluator.load_benchmarks()
    return {
        "count": len(benchmarks),
        "benchmark_file": str(GKMSEvaluator.get_benchmark_file_path()),
        "data": benchmarks
    }
