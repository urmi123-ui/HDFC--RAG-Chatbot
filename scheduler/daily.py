import sys
import os
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path so we can import from ingestion
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ingestion.run import main as run_ingestion_pipeline

def job():
    print(f"[{datetime.now(pytz.timezone('Asia/Kolkata'))}] Starting daily scheduled ingestion job...")
    try:
        run_ingestion_pipeline()
        print(f"[{datetime.now(pytz.timezone('Asia/Kolkata'))}] Daily scheduled ingestion job complete.")
    except Exception as e:
        print(f"[{datetime.now(pytz.timezone('Asia/Kolkata'))}] Daily scheduled ingestion job failed: {e}", file=sys.stderr)

def main():
    scheduler = BlockingScheduler()
    # Schedule job to run every day at 10:00 AM IST
    trigger = CronTrigger(hour=10, minute=0, timezone=pytz.timezone('Asia/Kolkata'))
    scheduler.add_job(job, trigger, id='daily_ingestion')
    
    print("--- HDFC MF Assistant Daily Scheduler ---")
    print("Scheduled to run daily at 10:00 AM IST (Asia/Kolkata).")
    print("Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()
