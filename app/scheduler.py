"""
Scheduler
=========
Uses APScheduler to trigger the daily allocation job at 07:00 AM.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def init_scheduler(app):
    """Register the daily allocation job and start the scheduler."""

    def allocation_job():
        """Wrapper that runs inside app context."""
        with app.app_context():
            from app.services.orchestrator import run_daily_allocation
            logger.info("⏰ Running daily allocation job...")
            try:
                result = run_daily_allocation()
                m = result['metrics']
                logger.info(
                    f"✅ Allocation complete | Assigned: {m['assigned_orders']} | "
                    f"Deferred: {m['deferred_orders']} | Cost: ₹{m['total_cost']}"
                )
            except Exception as e:
                logger.error(f"❌ Allocation job failed: {e}", exc_info=True)

    scheduler.add_job(
        allocation_job,
        trigger=CronTrigger(hour=7, minute=0),
        id='daily_allocation',
        name='Daily Order Allocation',
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
        logger.info("📅 Scheduler started — daily allocation at 07:00 AM")
