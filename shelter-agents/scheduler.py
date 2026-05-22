from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from agents.updater import run_update
from agents.narrator import run_narrator
import logging
import uvicorn
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

api = FastAPI()

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

@api.post("/update")
def trigger_update():
    log.info("Manual update triggered via API")
    try:
        run_update()
        run_narrator()
        return {"status": "ok", "message": "Update and narrator complete"}
    except Exception as e:
        log.error(f"Manual update failed: {e}")
        return {"status": "error", "message": str(e)}

@api.get("/health")
def health():
    return {"status": "ok"}

scheduler = BackgroundScheduler()
scheduler.add_job(job_update, IntervalTrigger(hours=6), id='update', name='Shelter update')
scheduler.add_job(job_narrate, CronTrigger(hour=8, minute=0), id='narrate', name='Daily narrative')
scheduler.start()
log.info("Scheduler started — update every 6h, narrate daily at 08:00 UTC")

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8001)
