# Placeholder for Google Calendar API integration logic

import os
from datetime import datetime, timedelta
import logging
import pytz

import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy.orm import Session
from .models import User, OAuthToken # Use relative import for models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Google Client info from environment (needed for refresh)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Scopes should ideally match those requested during auth
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.readonly"
]


async def get_calendar_credentials(user_id: int, db: Session) -> Credentials | None:
    """Gets valid Google Calendar credentials for a user, refreshing if needed."""
    logger.info(f"Attempting to retrieve OAuth token for user_id: {user_id}")
    
    # Get token from database
    token_info = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
    if not token_info:
        logger.warning(f"No OAuth token found for user_id {user_id}")
        return None

    # Convert expiry to aware UTC datetime for comparison
    if token_info.expires_at.tzinfo is None:
        # If naive, assume UTC
        expiry_dt = pytz.utc.localize(token_info.expires_at)
        logger.warning(f"Token expiry was naive ({token_info.expires_at}), assuming UTC.")
    else:
        # Convert any timezone to UTC
        expiry_dt = token_info.expires_at.astimezone(pytz.utc)
    
    # <<< Add Logging >>>
    logger.info(f"[DEBUG][Load] DB Expiry Raw (User {user_id}): {token_info.expires_at}, Type: {type(token_info.expires_at)}, TZInfo: {getattr(token_info.expires_at, 'tzinfo', 'N/A')}")
    logger.info(f"[DEBUG][Load] Prepared Expiry for Credentials (User {user_id}): {expiry_dt}, Type: {type(expiry_dt)}, TZInfo: {getattr(expiry_dt, 'tzinfo', 'N/A')}")
    # <<< End Logging >>>

    # Manual expiry check with buffer
    now = datetime.now(pytz.utc)
    buffer = timedelta(minutes=5)  # 5-minute buffer
    is_expired = expiry_dt <= (now + buffer)
    
    logger.info(f"[ManualCheck] Token for user {user_id} {'appears expired' if is_expired else 'is still valid'} (Expiry: {expiry_dt}, Now: {now}).")

    if is_expired and token_info.refresh_token:
        logger.info(f"Attempting credential refresh for user_id {user_id}...")
        try:
            # Create credentials object for refresh
            creds = Credentials(
                token=token_info.access_token,
                refresh_token=token_info.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=token_info.scope.split() if token_info.scope else SCOPES  # Split existing scope or use default
            )
            
            # Refresh the credentials
            creds.refresh(google.auth.transport.requests.Request())
            
            # Update token info in database
            token_info.access_token = creds.token
            token_info.expires_at = creds.expiry
            # Only update refresh token if a new one was provided
            if creds.refresh_token:
                token_info.refresh_token = creds.refresh_token
            # Ensure scope is stored as a space-separated string
            token_info.scope = " ".join(creds.scopes) if isinstance(creds.scopes, (list, tuple)) else creds.scopes
            token_info.updated_at = datetime.now(pytz.utc)
            
            db.commit()
            logger.info(f"Credentials refreshed successfully for user_id: {user_id}")
            
            # Return the refreshed credentials
            return creds
            
        except Exception as e:
            logger.error(f"Failed to refresh credentials for user_id {user_id}: {str(e)}", exc_info=True)
            db.rollback()
            return None
    elif is_expired:
        logger.warning(f"Token expired for user_id {user_id} but no refresh token available")
        return None
    
    # If not expired, create and return credentials
    return Credentials(
        token=token_info.access_token,
        refresh_token=token_info.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_info.scope.split() if token_info.scope else SCOPES  # Split existing scope or use default
    )


async def get_calendar_events(user_id: int, db: Session) -> list:
    """Fetches today's events from the specific user's primary Google Calendar."""
    logger.info(f"Fetching calendar events for user_id: {user_id}")
    
    # Properly await the coroutine
    creds = await get_calendar_credentials(user_id=user_id, db=db)

    if not creds:
        logger.warning(f"Could not obtain valid credentials for user_id {user_id}. Cannot fetch calendar events.")
        return [] # Return empty list if auth failed/not available

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API for today's events
        # Assuming the core logic will handle timezone conversion based on LOCAL_TIMEZONE
        now_utc = datetime.now(pytz.utc)
        today_start_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=pytz.utc)
        today_end_utc = today_start_utc + timedelta(days=1)

        logger.info(f"Getting events for user_id {user_id} between {today_start_utc.isoformat()} and {today_end_utc.isoformat()}")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=today_start_utc.isoformat(),
                timeMax=today_end_utc.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            logger.info(f"No upcoming events found for today for user_id: {user_id}.")
            return []

        formatted_events = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            formatted_events.append({
                "summary": event.get("summary", "No Title"),
                "start": start,
                "end": end,
                "id": event["id"]
                # Consider adding original timezone info if needed later
                # "timeZone": event.get("start", {}).get("timeZone") 
            })
            # logger.debug(f"Event found for user {user_id}: {event.get('summary', 'No Title')} ({start})")

        logger.info(f"Successfully fetched {len(formatted_events)} events for user_id: {user_id}")
        return formatted_events

    except HttpError as error:
        logger.error(f"An API error occurred for user_id {user_id}: {error}")
        if error.resp.status == 401:
             logger.error(f"Authentication error for user_id {user_id}. Token might be invalid or revoked.")
             # TODO: Maybe mark token as invalid in DB or notify user
        elif error.resp.status == 403:
            logger.error(f"Permission denied for user_id {user_id}. Check API scopes/enablement. Details: {error.content}")
        # Handle other specific errors as needed
        return [] # Return empty on error
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching events for user_id {user_id}: {e}", exc_info=True)
        return [] 