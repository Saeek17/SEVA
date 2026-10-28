import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.farmer import Farmer
from app.models.advisory import AdvisoryRun, AdviceItemModel
from app.models.delivery import DeliveryLog
from app.services.scheduler.task_scheduler import scheduler_service
from app.schemas.rules import AdviceItem, AdviceAction, UrgencyLevel

router = APIRouter(prefix="/advisories", tags=["Advisories"])

@router.get("")
async def list_advisories(
    limit: int = Query(50, ge=1, le=200),
    farmer_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AdvisoryRun)
    if farmer_id:
        query = query.filter(AdvisoryRun.farmer_id == farmer_id)

    runs = query.order_by(AdvisoryRun.created_at.desc()).limit(limit).all()
    results = []

    for r in runs:
        # Load structured items
        items = []
        for it in r.advice_items:
            items.append({
                "action": it.action,
                "urgency": it.urgency,
                "reason_code": it.reason_code,
                "params": it.get_params(),
                "source_citation": it.source_citation,
                "priority_rank": it.priority_rank
            })

        # Load delivery logs
        deliveries = []
        for dl in r.delivery_logs:
            deliveries.append({
                "channel": dl.channel,
                "provider": dl.provider,
                "status": dl.status,
                "external_sid": dl.external_sid,
                "dispatched_at": dl.dispatched_at
            })

        results.append({
            "id": r.id,
            "farmer_id": r.farmer_id,
            "farmer_name": r.farmer.full_name if r.farmer else "Sandbox Farmer",
            "crop_id": r.crop_id,
            "growth_stage": r.growth_stage,
            "das": r.das,
            "data_confidence": r.data_confidence,
            "sources_used": r.sources_used,
            "generated_message": r.generated_message,
            "language": r.language,
            "validation_passed": r.validation_passed,
            "validation_notes": r.validation_notes,
            "fallback_used": r.fallback_used,
            "voice_audio_path": r.voice_audio_path,
            "created_at": r.created_at,
            "advice_items": items,
            "delivery_logs": deliveries
        })

    return results

@router.get("/{advisory_id}")
async def get_advisory(advisory_id: str, db: Session = Depends(get_db)):
    r = db.query(AdvisoryRun).filter(AdvisoryRun.id == advisory_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Advisory run not found")

    items = [
        {
            "action": it.action,
            "urgency": it.urgency,
            "reason_code": it.reason_code,
            "params": it.get_params(),
            "source_citation": it.source_citation
        }
        for it in r.advice_items
    ]

    return {
        "id": r.id,
        "farmer_id": r.farmer_id,
        "farmer_name": r.farmer.full_name if r.farmer else None,
        "crop_id": r.crop_id,
        "growth_stage": r.growth_stage,
        "das": r.das,
        "raw_weather_snapshot": r.get_weather_json(),
        "raw_soil_snapshot": r.get_soil_json(),
        "data_confidence": r.data_confidence,
        "sources_used": r.sources_used,
        "generated_message": r.generated_message,
        "language": r.language,
        "validation_passed": r.validation_passed,
        "validation_notes": r.validation_notes,
        "fallback_used": r.fallback_used,
        "voice_audio_path": r.voice_audio_path,
        "created_at": r.created_at,
        "advice_items": items,
        "delivery_logs": [
            {"channel": dl.channel, "status": dl.status, "provider": dl.provider}
            for dl in r.delivery_logs
        ]
    }

@router.post("/run-batch")
async def trigger_batch_run():
    """Manually trigger daily morning advisory generation cycle for all active farmers."""
    await scheduler_service.run_morning_batch()
    return {"status": "success", "message": "Batch advisory cycle executed successfully."}

@router.post("/farmer/{farmer_id}/trigger")
async def trigger_farmer_advisory(farmer_id: str, db: Session = Depends(get_db)):
    """Manually trigger advisory generation and delivery for a specific registered farmer."""
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    run = await scheduler_service.process_farmer_advisory(farmer, db, is_urgent_only=False)
    if not run:
        raise HTTPException(status_code=400, detail="Could not generate advisory for farmer.")

    return {
        "status": "success",
        "advisory_id": run.id,
        "generated_message": run.generated_message,
        "audio_url": run.voice_audio_path
    }
