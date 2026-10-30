import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Set
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.farmer import Farmer
from app.models.advisory import AdvisoryRun, AdviceItemModel
from app.models.delivery import DeliveryLog
from app.models.push import PushSubscription
from app.security import decrypt_phone, hash_phone
from app.services.data_clients.aggregator import EnvironmentalAggregator
from app.services.crop_engine.loader import crop_loader
from app.services.crop_engine.stage_calculator import StageCalculator
from app.services.crop_engine.rules_engine import RulesEngine
from app.services.advice_generator.generator import AdviceGenerator
from app.services.delivery.tts_service import GoogleTTSService
from app.services.delivery.twilio_provider import TwilioDeliveryProvider
from app.services.delivery.push_service import send_push, push_enabled
from app.config import settings
from app.services.scheduler.deduplicator import AlertDeduplicator
from app.schemas.rules import UrgencyLevel

logger = logging.getLogger(__name__)

class KisanScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.aggregator = EnvironmentalAggregator()
        self.generator = AdviceGenerator()
        self.delivery = TwilioDeliveryProvider()

    def start(self):
        if not self.scheduler.running:
            # Morning advisory cycle: 06:30 IST daily (SMS / WhatsApp / voice + web push)
            self.scheduler.add_job(
                self.run_morning_batch,
                CronTrigger(hour=settings.MORNING_BATCH_HOUR, minute=settings.MORNING_BATCH_MINUTE, timezone="Asia/Kolkata"),
                id="morning_advisory_batch",
                replace_existing=True
            )
            # Hourly emergency weather hazard check
            self.scheduler.add_job(
                self.run_hourly_hazard_check,
                CronTrigger(minute=0, timezone="Asia/Kolkata"),
                id="hourly_hazard_check",
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("APScheduler initialized for morning advice and hourly hazard alerts.")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler stopped.")

    async def run_morning_batch(self):
        logger.info("Starting Daily Morning Farmer Advisory Cycle...")
        db = SessionLocal()
        try:
            active_farmers = db.query(Farmer).filter(Farmer.is_active == True).all()
            logger.info(f"Processing morning advisories for {len(active_farmers)} active farmers.")
            for farmer in active_farmers:
                try:
                    await self.process_farmer_advisory(farmer, db, is_urgent_only=False)
                except Exception as e:
                    logger.error(f"Error processing morning advice for farmer {farmer.id}: {e}")
            await self.run_push_batch(db)
        finally:
            db.close()

    async def run_push_batch(self, db: Session) -> int:
        """Send today's advice as a Web Push notification to every active PWA subscriber."""
        if not push_enabled():
            return 0
        sent = 0
        for sub in db.query(PushSubscription).filter(PushSubscription.is_active == True).all():
            try:
                msg = await self.build_push_message(sub)
                if not msg:
                    continue
                title = {"mr": "किसान साथी", "hi": "किसान साथी", "en": "KisanSaathi"}.get(sub.language, "KisanSaathi")
                res = await send_push(sub, title, msg)
                if res["status"] == "GONE":
                    sub.is_active = False
                elif res["status"] == "SENT":
                    sub.last_sent_at = datetime.utcnow()
                    sent += 1
            except Exception as e:
                logger.error(f"Push failed for subscription {sub.id}: {e}")
        db.commit()
        logger.info(f"Web push sent to {sent} subscribers.")
        return sent

    async def build_push_message(self, sub: PushSubscription) -> Optional[str]:
        crop = crop_loader.get_crop(sub.crop_id)
        if not crop:
            return None
        das = StageCalculator.calculate_das(sub.sowing_date)
        stage, _ = StageCalculator.resolve_stage(crop, das)
        env = await self.aggregator.get_environmental_snapshot(sub.latitude, sub.longitude)
        advice_items = RulesEngine.evaluate(crop, stage, das, env)
        if not advice_items:
            return None
        msg, _, _, _ = await self.generator.generate_advisory(crop, stage, das, advice_items, language=sub.language)
        return msg

    async def call_back_farmer(self, phone: str, db: Session) -> bool:
        """Missed-call IVR: ring the caller back and play today's voice advice. Returns False if unregistered."""
        farmer = db.query(Farmer).filter(Farmer.phone_hash == hash_phone(phone), Farmer.is_active == True).first()
        if not farmer:
            return False
        # Missed calls are free to the caller but each callback costs us money: allow one per 10 minutes.
        recent = (
            db.query(DeliveryLog.id)
            .join(AdvisoryRun, DeliveryLog.advisory_run_id == AdvisoryRun.id)
            .filter(
                AdvisoryRun.farmer_id == farmer.id,
                DeliveryLog.channel == "VOICE",
                DeliveryLog.dispatched_at >= datetime.utcnow() - timedelta(minutes=10),
            )
            .first()
        )
        if recent:
            logger.info(f"Skipping missed-call callback for farmer {farmer.id}: called back within last 10 minutes.")
            return True
        run = await self.process_farmer_advisory(farmer, db, is_urgent_only=False, channels={"VOICE"})
        return run is not None
    async def run_hourly_hazard_check(self):
        logger.info("Executing hourly weather hazard check...")
        db = SessionLocal()
        try:
            active_farmers = db.query(Farmer).filter(Farmer.is_active == True).all()
            for farmer in active_farmers:
                try:
                    await self.process_farmer_advisory(farmer, db, is_urgent_only=True)
                except Exception as e:
                    logger.error(f"Error during hazard check for farmer {farmer.id}: {e}")
        finally:
            db.close()

    async def process_farmer_advisory(
        self,
        farmer: Farmer,
        db: Session,
        is_urgent_only: bool = False,
        channels: Optional[Set[str]] = None
    ) -> Optional[AdvisoryRun]:
        crop = crop_loader.get_crop(farmer.crop_id)
        if not crop:
            logger.warning(f"Farmer {farmer.id} has unrecognized crop_id: {farmer.crop_id}")
            return None

        das = StageCalculator.calculate_das(farmer.sowing_date)
        stage, _ = StageCalculator.resolve_stage(crop, das)

        # 1. Fetch live environmental facts
        env = await self.aggregator.get_environmental_snapshot(farmer.latitude, farmer.longitude)

        # 2. Evaluate deterministic rules
        advice_items = RulesEngine.evaluate(crop, stage, das, env)
        if not advice_items:
            return None

        # If running hourly hazard check, only dispatch if new HIGH-urgency alerts exist
        if is_urgent_only:
            high_urgency = [item for item in advice_items if item.urgency == UrgencyLevel.HIGH]
            if not high_urgency:
                return None
            # Check 24-hr deduplication
            deduped_items = []
            for item in high_urgency:
                if not AlertDeduplicator.is_duplicate_alert(db, farmer.id, item.reason_code):
                    deduped_items.append(item)
            if not deduped_items:
                return None
            advice_items = deduped_items

        # 3. Generate vernacular message with validation & DLT fallback
        msg, passed, notes, fallback = await self.generator.generate_advisory(
            crop, stage, das, advice_items, language=farmer.language
        )

        # 4. Synthesize voice audio
        audio_url = await GoogleTTSService.synthesize(msg, language=farmer.language)

        # 5. Persist AdvisoryRun
        run = AdvisoryRun(
            farmer_id=farmer.id,
            crop_id=farmer.crop_id,
            growth_stage=stage.name_en,
            das=das,
            raw_weather_snapshot=json.dumps(env.model_dump(), default=str),
            raw_soil_snapshot=json.dumps({"texture": env.soil_texture_class, "sm_0_7": env.soil_moisture_0_7cm_pct}),
            data_confidence=env.data_confidence,
            sources_used=", ".join(env.sources_used),
            generated_message=msg,
            language=farmer.language,
            validation_passed=passed,
            validation_notes=notes,
            fallback_used=fallback,
            voice_audio_path=audio_url
        )
        db.add(run)
        db.flush() # Populate run.id

        # Persist advice items
        for rank, item in enumerate(advice_items, 1):
            db_item = AdviceItemModel(
                advisory_run_id=run.id,
                action=item.action.value,
                urgency=item.urgency.value,
                reason_code=item.reason_code,
                params_json=json.dumps(item.params, ensure_ascii=False),
                source_citation=item.sources_used[-1] if item.sources_used else "Agro Rule",
                priority_rank=rank
            )
            db.add(db_item)

        # 6. Deliver: WhatsApp first (falls back to SMS), then voice, honouring consent.
        #    `channels` limits delivery (e.g. {"VOICE"} for missed-call callbacks).
        raw_phone = decrypt_phone(farmer.phone_encrypted)

        def wants(channel: str) -> bool:
            return channels is None or channel in channels

        def log_delivery(channel: str, res: dict):
            db.add(DeliveryLog(
                advisory_run_id=run.id,
                channel=channel,
                provider=res["provider"],
                external_sid=res.get("sid"),
                status=res["status"],
                error_message=res.get("error")
            ))

        if farmer.consent_sms and (wants("WHATSAPP") or wants("SMS")):
            delivered = False
            if wants("WHATSAPP"):
                wa_res = await self.delivery.send_whatsapp(raw_phone, msg, run.id)
                if wa_res["status"] != "SKIPPED":
                    log_delivery("WHATSAPP", wa_res)
                    delivered = wa_res["status"] in ("SENT", "DELIVERED", "QUEUED")
            if not delivered and wants("SMS"):
                log_delivery("SMS", await self.delivery.send_sms(raw_phone, msg, run.id))

        if farmer.consent_voice and wants("VOICE"):
            log_delivery("VOICE", await self.delivery.make_voice_call(raw_phone, audio_url, run.id))

        db.commit()
        db.refresh(run)
        logger.info(f"Successfully processed advisory run {run.id} for farmer {farmer.id}")
        return run

scheduler_service = KisanScheduler()
