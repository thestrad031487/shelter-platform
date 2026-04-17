from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from agents.updater import run_update
from agents.narrator import run_narrator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

def job_update():
    log.info("Running scheduled update...")
    try:
        run_update()
    except Exception as e:
        log.error(f"Update failed: {e}")

def job_narrate():
    log.info("Running scheduled narrator...")
    try:
        run_narrator()
    except Exception as e:
        log.error(f"Narrator failed: {e}")

scheduler = BlockingScheduler()

scheduler.add_job(job_update, IntervalTrigger(hours=6), id='update', name='Shelter update')
scheduler.add_job(job_narrate, CronTrigger(hour=8, minute=0), id='narrate', name='Daily narrative')

log.info("Scheduler started — update every 6h, narrate daily at 08:00 UTC")

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    log.info("Scheduler stopped.")
