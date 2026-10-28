import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.advisory import AdvisoryRun, AdviceItemModel

logger = logging.getLogger(__name__)

class AlertDeduplicator:
    """
    Prevents re-sending identical high-urgency alerts to the same farmer within a 24-hour window.
    """
    DEDUPLICATION_WINDOW_HOURS = 24

    @classmethod
    def is_duplicate_alert(cls, db: Session, farmer_id: str, reason_code: str) -> bool:
        since = datetime.utcnow() - timedelta(hours=cls.DEDUPLICATION_WINDOW_HOURS)

        # Query recent advisory runs for this farmer
        recent_run_ids = (
            db.query(AdvisoryRun.id)
            .filter(AdvisoryRun.farmer_id == farmer_id, AdvisoryRun.created_at >= since)
        )

        # Check if identical reason code was dispatched in that window
        exists = (
            db.query(AdviceItemModel)
            .filter(
                AdviceItemModel.advisory_run_id.in_(recent_run_ids.scalar_subquery()),
                AdviceItemModel.reason_code == reason_code
            )
            .first()
        )

        if exists:
            logger.info(f"Deduplication hit: Alert '{reason_code}' already sent to farmer {farmer_id} in last 24h.")
            return True
        return False
