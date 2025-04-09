import os
import logging
from datetime import datetime, timedelta
import pytz

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc # For ordering
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware

# Google OAuth Imports
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests
import googleapiclient.discovery
import requests # To fetch user info

# Import project modules using relative imports
from .scheduler import start_scheduler, stop_scheduler, daily_planning_and_email_job
from .core import generate_daily_plan
from .models import SessionLocal, create_db_tables, get_db, User, OAuthToken, DailyPlan
from .email_sender import send_daily_summary_email # Import email sender

# --- Configuration & Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Google OAuth Config from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173") # Default frontend URL
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI]):
    logger.error("Google OAuth configuration missing in environment variables!")
    # Potentially raise an error or exit

if not SESSION_SECRET_KEY:
    logger.warning("SESSION_SECRET_KEY not set! Using a default (INSECURE). Set a strong key in .env")
    SESSION_SECRET_KEY = "a_default_insecure_secret_key_replace_me"

# Define OAuth Scopes (ensure these match what your app needs)
# openid, email, profile are for basic user info
# calendar.readonly is for reading calendar events
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.readonly"
]

# --- FastAPI App Initialization ---
app = FastAPI(title="Day Planner API")

# CORS Configuration
origins = [
    FRONTEND_URL, # Allow frontend origin
    "http://localhost:5173", # Explicitly add default just in case
    # Add other origins if needed (e.g., your deployed frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # <<< Important for cookies/session
    allow_methods=["*"],    # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)

# Add Session Middleware (after CORS)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# --- Database & Scheduler Lifecycle --- 
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application...")
    #create_db_tables() # Create database tables if they don't exist
    #start_scheduler() # Start the background scheduler

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down FastAPI application...")
    #stop_scheduler() # Stop the background scheduler gracefully

# --- Helper Function for OAuth Flow ---
def get_google_flow() -> Flow:
    """Creates the Google OAuth Flow object."""
    # Note: Using client_secrets dict instead of file for flexibility
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "userinfo_uri": "https://openidconnect.googleapis.com/v1/userinfo", # OpenID Connect endpoint
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "javascript_origins": ["http://localhost:8000", FRONTEND_URL] # Add origins if needed
        }
    }
    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

# --- Authentication Dependency --- 
# (This should ideally be more robust, handling token validation/refresh if needed)
async def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
         # Clear session if user_id is invalid
         request.session.clear()
         return None
    return user

async def require_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# --- Authentication Endpoints --- 
@app.get("/auth/google")
async def google_login(request: Request):
    """Initiates the Google OAuth login flow by redirecting the user to Google."""
    flow = get_google_flow()
    # Store state in session to prevent CSRF
    authorization_url, state = flow.authorization_url(
        access_type="offline", # Request refresh token
        include_granted_scopes='true',
        prompt="consent" # Force consent screen for refresh token on first login
    )
    request.session['oauth_state'] = state
    logger.info(f"Redirecting user to Google for authentication. State: {state}")
    return RedirectResponse(authorization_url)


@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handles the callback from Google after user authentication."""
    # Check for CSRF state mismatch
    state = request.query_params.get('state')
    if state != request.session.get('oauth_state'):
        logger.error("OAuth state mismatch. Potential CSRF attack.")
        raise HTTPException(status_code=401, detail="Invalid OAuth state")
    
    # Check for errors from Google
    error = request.query_params.get('error')
    if error:
        logger.error(f"Google OAuth Error: {error}")
        raise HTTPException(status_code=400, detail=f"Google OAuth Error: {error}")

    flow = get_google_flow()
    
    try:
        # Exchange authorization code for tokens
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        
        # Get user info using the obtained credentials
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"}
        )
        userinfo_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        user_info = userinfo_response.json()
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        if not google_id or not email:
            logger.error("Failed to get google_id or email from userinfo endpoint.")
            raise HTTPException(status_code=500, detail="Could not retrieve user information from Google.")

        logger.info(f"Successfully authenticated user: {email} (Google ID: {google_id})")

        # --- Database Interaction: Find or Create User and Token ---
        user = db.query(User).filter(User.google_id == google_id).first()

        expires_at_dt = None
        if credentials.expiry:
            # Ensure expiry is timezone-aware (UTC)
            # Let's be explicit about UTC conversion here
            if credentials.expiry.tzinfo is None:
                 # If google gives naive, assume UTC per library behavior
                 expires_at_dt = pytz.utc.localize(credentials.expiry)
                 logger.warning(f"Google credentials.expiry was naive ({credentials.expiry}), assuming UTC.")
            else:
                 # Convert any timezone to UTC
                 expires_at_dt = credentials.expiry.astimezone(pytz.utc)
            
            # <<< Add Logging >>>
            logger.info(f"[DEBUG][Save] Credentials Expiry Raw (User {user.id if user else 'New'}): {credentials.expiry}, Type: {type(credentials.expiry)}, TZInfo: {getattr(credentials.expiry, 'tzinfo', 'N/A')}")
            logger.info(f"[DEBUG][Save] Prepared expires_at_dt for DB (User {user.id if user else 'New'}): {expires_at_dt}, Type: {type(expires_at_dt)}, TZInfo: {getattr(expires_at_dt, 'tzinfo', 'N/A')}")
            # <<< End Logging >>>

        if user:
            # Update existing user and token
            logger.info(f"Found existing user ID: {user.id}")
            user.email = email
            user.name = name
            user.picture_url = picture
            user.updated_at = datetime.now(pytz.utc)
            
            token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
            if token:
                token.access_token = credentials.token
                # Only update refresh token if Google provided a new one
                if credentials.refresh_token:
                    token.refresh_token = credentials.refresh_token
                token.expires_at = expires_at_dt
                token.scope = " ".join(credentials.scopes)
                token.updated_at = datetime.now(pytz.utc)
                logger.info(f"Updated existing OAuth token for user ID: {user.id}")
            else:
                 # Should not happen if user exists but token doesn't, but handle defensively
                 logger.warning(f"User ID {user.id} exists, but no token found. Creating new token.")
                 new_token = OAuthToken(
                    user_id=user.id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    expires_at=expires_at_dt,
                    scope=" ".join(credentials.scopes)
                 )
                 db.add(new_token)
        else:
            # Create new user and token
            logger.info(f"Creating new user for email: {email}")
            new_user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture_url=picture
            )
            db.add(new_user)
            # Need to flush to get the new_user.id before creating token
            db.flush()
            
            new_token = OAuthToken(
                user_id=new_user.id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_at=expires_at_dt,
                scope=" ".join(credentials.scopes)
            )
            db.add(new_token)
            user = new_user # Assign newly created user
            logger.info(f"Created new user ID: {user.id} and OAuth token.")

        db.commit()
        # --- End Database Interaction ---

        # Store minimal user info (e.g., user ID) in session
        request.session['user_id'] = user.id
        request.session['user_email'] = user.email 
        logger.info(f"User ID {user.id} stored in session.")
        
        # Redirect back to the frontend
        return RedirectResponse(url=FRONTEND_URL)

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed during token exchange or userinfo fetch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to communicate with Google services.")
    except Exception as e:
        logger.error(f"An error occurred during Google OAuth callback: {e}", exc_info=True)
        db.rollback() # Rollback DB changes on error
        raise HTTPException(status_code=500, detail="An internal error occurred during authentication.")

@app.get("/user/me")
async def read_current_user(current_user: User = Depends(require_current_user)):
    """Gets info about the currently logged-in user using the dependency."""
    return {
        "id": current_user.id, 
        "email": current_user.email, 
        "name": current_user.name, 
        "picture": current_user.picture_url
    }

@app.post("/auth/logout")
async def logout(request: Request, response: Response): # Inject Response
    """Logs the user out by clearing the session."""
    user_id = request.session.get('user_id')
    if user_id:
         logger.info(f"Logging out user ID: {user_id}")
         request.session.clear()
         # Also clear cookie in response for immediate effect
         response.delete_cookie("session") 
         return {"message": "Successfully logged out"}
    else:
         return {"message": "No active session found"}

# --- End Authentication Endpoints ---


# --- Core Functionality Endpoints (Now Protected) ---

@app.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(require_current_user), db: Session = Depends(get_db)):
    """Fetches the latest daily plan saved for the current user."""
    logger.info(f"Fetching latest dashboard plan for user {current_user.id}")
    
    # Get today's date in UTC to compare consistently with DB potentially
    # Or use the user's local timezone if plan_date is stored localized
    # Assuming plan_date is stored as a date or UTC datetime in DB for simplicity here
    # today_date = datetime.now(pytz.utc).date() 
    
    latest_plan = (
        db.query(DailyPlan)
        .filter(DailyPlan.user_id == current_user.id)
        .order_by(desc(DailyPlan.plan_date)) # Get the plan for the most recent date
        .first()
    )

    if not latest_plan:
        logger.info(f"No saved plan found for user {current_user.id}. Returning empty plan.")
        # Optionally, trigger a plan generation here if none exists?
        # Or return an indication that no plan is available yet.
        return {
             "message": "No daily plan found.", 
             "plan_date": None,
             "generated_at": None,
             "plan": []
         } 

    logger.info(f"Returning saved plan from {latest_plan.plan_date} for user {current_user.id}")
    return {
        "message": "Successfully retrieved latest plan.",
        "plan_date": latest_plan.plan_date.isoformat(), # Ensure date is ISO formatted
        "generated_at": latest_plan.generated_at.isoformat() if latest_plan.generated_at else None,
        "plan": latest_plan.plan_data # Return the JSON data directly
    }

@app.post("/schedule/run/manual", status_code=202)
async def trigger_scheduling_manually(
    background_tasks: BackgroundTasks, 
    current_user: User = Depends(require_current_user), 
    db: Session = Depends(get_db)
): 
    """Manually triggers the background job for the current user ONLY.""" 
    # NOTE: This triggers the job defined in scheduler.py, which currently runs for ALL users.
    # For a user-specific manual trigger, we might need a different background task function
    # that calls generate_daily_plan directly for the current_user.id.
    # Let's create a specific function for this.
    async def run_plan_for_single_user(user_id: int):
        logger.info(f"--- Starting Manual Planning Job for User ID: {user_id} ---")
        # Need a DB session within the background task
        async_db: Session | None = None
        try:
            if not SessionLocal:
                logger.error("DB SessionLocal not init in background task.")
                return
            async_db = SessionLocal()
            plan = await generate_daily_plan(user_id=user_id, db=async_db)
            if plan is not None:
                user_email = async_db.query(User.email).filter(User.id == user_id).scalar()
                if user_email:
                     logger.info(f"Manual plan generated for user {user_id}, sending email to {user_email}...")
                     # Pass the correct recipient email
                     await send_daily_summary_email(plan, recipient_email=user_email) 
                else:
                     logger.error(f"Could not find email for user {user_id} to send manual plan.")
            else:
                 logger.error(f"Manual plan generation failed for user {user_id}.")
        except Exception as e:
            logger.error(f"Error in manual background task for user {user_id}: {e}", exc_info=True)
        finally:
            if async_db:
                async_db.close()
        logger.info(f"--- Finished Manual Planning Job for User ID: {user_id} ---")

    logger.info(f"User ID {current_user.id} requested manual trigger daily planning job.")
    background_tasks.add_task(run_plan_for_single_user, current_user.id)
    return {"message": f"Daily planning job triggered in the background for user {current_user.id}."}

@app.post("/schedule/generate/manual")
async def trigger_generate_plan_manually(
    current_user: User = Depends(require_current_user), 
    db: Session = Depends(get_db)
):
    """Manually triggers only the plan generation for the current user and returns the plan."""
    logger.info(f"User ID {current_user.id} requested manual plan generation (no email)... ")
    plan = await generate_daily_plan(user_id=current_user.id, db=db)
    if plan is None:
         raise HTTPException(status_code=500, detail="Plan generation failed.")
    logger.info(f"Manual plan generation successful for user {current_user.id}.")
    return {"message": "Plan generated successfully", "plan": plan}

@app.get("/notion/tasks")
async def get_notion_tasks_endpoint(current_user: User = Depends(require_current_user)):
    """Fetches tasks from Notion for the current user."""
    logger.info(f"Fetching Notion tasks for user {current_user.id}")
    
    try:
        from .notion import get_notion_tasks
        tasks = await get_notion_tasks()
        
        if tasks is None:
            logger.error(f"Failed to fetch Notion tasks for user {current_user.id}")
            raise HTTPException(status_code=500, detail="Failed to fetch Notion tasks")
        
        # Format tasks for the frontend
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "id": task["id"],
                "type": "task",
                "title": task["title"],
                "priority": task["priority"],
                "estimate_hours": task["estimate_hours"],
                "deadline": task["deadline"],
                "url": task["url"],
                "start": None,  # Tasks don't have a start time by default
                "end": None     # Tasks don't have an end time by default
            }
            formatted_tasks.append(formatted_task)
        
        logger.info(f"Returning {len(formatted_tasks)} Notion tasks for user {current_user.id}")
        return {
            "message": "Successfully retrieved Notion tasks.",
            "tasks": formatted_tasks
        }
    
    except Exception as e:
        logger.error(f"Error fetching Notion tasks for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching Notion tasks: {str(e)}")

@app.get("/calendar/events")
async def get_calendar_events_endpoint(current_user: User = Depends(require_current_user), db: Session = Depends(get_db)):
    """Fetches today's events from the user's Google Calendar."""
    logger.info(f"2Fetching calendar events for user {current_user.id}")
    
    try:
        from .google_calendar import get_calendar_events
        events = await get_calendar_events(user_id=current_user.id, db=db)
        
        if events is None:
            logger.error(f"Failed to fetch calendar events for user {current_user.id}")
            raise HTTPException(status_code=500, detail="Failed to fetch calendar events")
        
        # Format events for the frontend
        formatted_events = []
        for event in events:
            formatted_event = {
                "id": event["id"],
                "type": "event",
                "summary": event["summary"],
                "start": event["start"],
                "end": event["end"]
            }
            formatted_events.append(formatted_event)
        
        logger.info(f"Returning {len(formatted_events)} calendar events for user {current_user.id}")
        return {
            "message": "Successfully retrieved calendar events.",
            "events": formatted_events
        }
    
    except Exception as e:
        logger.error(f"Error fetching calendar events for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching calendar events: {str(e)}")

# --- Root Endpoint --- 
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Day Planner API"}

# TODO: Add more endpoints as needed (e.g., get specific events, get tasks, update task status via Notion?)

# TODO: Integrate routers for better organization if the app grows.
# from .routers import auth, schedule
# app.include_router(auth.router)
# app.include_router(schedule.router) 