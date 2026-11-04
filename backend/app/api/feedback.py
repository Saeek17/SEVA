import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import AdviceFeedback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackCreate(BaseModel):
    helpful: bool
    crop_id: str = Field(..., min_length=2, max_length=100)
    action: str = Field(..., min_length=2, max_length=40)
    reason_code: Optional[str] = Field(default=None, max_length=80)
    das: Optional[int] = Field(default=None, ge=0, le=500)
    language: str = Field(default="mr", pattern="^(hi|mr|en)$")

@router.post("", status_code=201)
async def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    """Record whether an advice card was useful. Anonymous: no phone, farmer id or coordinates."""
    db.add(AdviceFeedback(**payload.model_dump()))
    db.commit()
    return {"status": "recorded"}

@router.get("/summary")
async def feedback_summary(db: Session = Depends(get_db)) -> Dict[str, object]:
    """Totals for the admin dashboard and for pilot reporting."""
    total = db.query(func.count(AdviceFeedback.id)).scalar() or 0
    helpful = db.query(func.count(AdviceFeedback.id)).filter(AdviceFeedback.helpful.is_(True)).scalar() or 0
    rows = (
        db.query(AdviceFeedback.action, AdviceFeedback.helpful, func.count(AdviceFeedback.id))
        .group_by(AdviceFeedback.action, AdviceFeedback.helpful)
        .all()
    )
    by_action: Dict[str, Dict[str, int]] = {}
    for action, is_helpful, n in rows:
        bucket = by_action.setdefault(action, {"helpful": 0, "not_helpful": 0})
        bucket["helpful" if is_helpful else "not_helpful"] += n
    return {
        "total": total,
        "helpful": helpful,
        "not_helpful": total - helpful,
        "helpful_pct": round(100 * helpful / total, 1) if total else None,
        "by_action": by_action,
    }
