# Placeholder for the scheduling engine logic using APScheduler

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

# Ensure imports point to the correct modules using relative paths
from .core import generate_daily_plan
from .email_sender import send_daily_summary_email
from .models import SessionLocal, User # Import DB session and User model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = AsyncIOScheduler()

async def daily_planning_and_email_job():
    """Job that generates the plan and sends the email for ALL registered users."""
    logger.info("--- Starting Scheduled Daily Planning Job for All Users --- ")
    
    db: Session | None = None # Define db with Optional type hint
    try:
        # Create a new database session for this job run
        # Important: Don't use FastAPI's get_db() dependency directly in scheduler
        if not SessionLocal:
            logger.error("Database SessionLocal not initialized in scheduler. Cannot run job.")
            return
            
        db = SessionLocal()
        
        # 1. Get all registered users
        users = db.query(User).all()
        if not users:
             logger.info("No registered users found. Skipping plan generation.")
             return
             
        logger.info(f"Found {len(users)} users to process.")

        for user in users:
             logger.info(f"--- Processing User ID: {user.id} (Email: {user.email}) ---")
             try:
                 # 2. Generate the plan for the current user
                 plan = await generate_daily_plan(user_id=user.id, db=db) 
                 
                 # 3. Send the email summary if plan generation was successful
                 if plan is not None: 
                     logger.info(f"Plan generated successfully for user {user.id}. Proceeding to send email to {user.email}.")
                     # Pass the specific user's email address
                     success = await send_daily_summary_email(plan, recipient_email=user.email)
                     
                     if success:
                         logger.info(f"Daily summary email sent successfully for user {user.id}.")
                     else:
                         logger.error(f"Failed to send daily summary email for user {user.id}.")
                 else:
                     logger.error(f"Plan generation failed for user {user.id}. Skipping email.")
                     
             except Exception as e:
                 # Log error for specific user but continue with others
                 logger.error(f"Error processing plan for user ID {user.id}: {e}", exc_info=True)
                 # Optional: Rollback any DB changes for this specific user if applicable
                 # db.rollback()
                 
             logger.info(f"--- Finished processing User ID: {user.id} ---")

    except Exception as e:
         logger.error(f"An overall error occurred during the scheduled job: {e}", exc_info=True)
         if db: # Rollback if session was created
             db.rollback()
    finally:
        if db:
            db.close() # Ensure session is closed
            logger.info("Database session closed for scheduled job.")
            
    logger.info("--- Scheduled Daily Planning Job Finished --- ")

def schedule_daily_job():
    """Adds the daily planning job to the scheduler."""
    # TODO: Make the trigger time configurable (e.g., from user settings/env)
    # Example: Run daily at 5:00 AM local time according to where the server runs
    trigger = CronTrigger(hour=5, minute=0)

    job_id = "daily_planning_email"
    
    # Check if job already exists to prevent duplicates on reload
    if scheduler.get_job(job_id):
         logger.warning(f"Job with id '{job_id}' already exists. Skipping scheduling.")
         return
         
    scheduler.add_job(
        daily_planning_and_email_job, 
        trigger=trigger,
        id=job_id, 
        name="Daily Plan Generation and Email",
        replace_existing=True # Replace if somehow it exists but get_job missed?
    )
    logger.info(f"Scheduled '{job_id}' job to run daily at: {trigger}")

def start_scheduler():
    """Starts the APScheduler."""
    if scheduler.running:
         logger.warning("Scheduler is already running.")
         return
         
    try:
        schedule_daily_job() # Add the job before starting
        scheduler.start()
        logger.info("APScheduler started successfully.")
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}", exc_info=True)

def stop_scheduler():
     """Stops the APScheduler gracefully."""
     if scheduler.running:
          logger.info("Shutting down APScheduler...")
          scheduler.shutdown()
          logger.info("APScheduler shut down.")
     else:
          logger.info("APScheduler is not running.")

# You will call start_scheduler() in your FastAPI startup event
# and stop_scheduler() in the shutdown event. 