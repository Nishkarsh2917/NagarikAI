"""
Daily scheduler. APScheduler in-process — simple to demo.
For production, replace with Celery beat or a managed cron + worker.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.ingestion.pipeline import run_all

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()

    if not settings.enable_scheduler:
        logger.info("Scheduler disabled by config.")
        return None

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone=settings.ingestion_cron_tz)
    _scheduler.add_job(
        _scheduled_run,
        CronTrigger(
            hour=settings.ingestion_cron_hour,
            minute=settings.ingestion_cron_minute,
            timezone=settings.ingestion_cron_tz,
        ),
        id="daily_ingestion",
        replace_existing=True,
        max_instances=1,           # never let two runs overlap
        coalesce=True,             # if we missed ticks (sleeping host), only run once
        misfire_grace_time=3600,   # forgive up to 1h late runs
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: daily at %02d:%02d %s",
        settings.ingestion_cron_hour,
        settings.ingestion_cron_minute,
        settings.ingestion_cron_tz,
    )
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


def _scheduled_run() -> None:
    logger.info("Scheduled ingestion run starting…")
    try:
        result = run_all()
        logger.info("Scheduled ingestion done: %s", result)
    except Exception:
        logger.exception("Scheduled ingestion crashed")
