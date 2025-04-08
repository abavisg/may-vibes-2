# Placeholder for Google Calendar API integration logic

import os
from datetime import datetime, timedelta
import logging
import pytz

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


def get_calendar_credentials(user_id: int, db: Session) -> Credentials | None:
    """Gets valid Google Calendar API credentials for a specific user from the database.

    Loads token from DB, reconstructs Credentials object, and refreshes if necessary,
    saving the updated token back to the DB.
    Returns None if no token is found or refresh fails.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google Client ID or Secret not configured. Cannot refresh tokens.")
        return None

    logger.info(f"Attempting to retrieve OAuth token for user_id: {user_id}")
    token_info = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()

    if not token_info:
        logger.warning(f"No OAuth token found in database for user_id: {user_id}")
        return None

    # Reconstruct the Credentials object from stored info
    try:
        # Ensure expires_at from DB is timezone-aware UTC
        db_expiry = token_info.expires_at
        aware_expiry_dt_utc = None
        logger.info(f"[DEBUG][Load] DB Expiry Raw (User {user_id}): {db_expiry}, Type: {type(db_expiry)}, TZInfo: {getattr(db_expiry, 'tzinfo', 'N/A')}")
        if db_expiry:
            if isinstance(db_expiry, datetime):
                 if db_expiry.tzinfo is None:
                      aware_expiry_dt_utc = pytz.utc.localize(db_expiry)
                 else:
                      aware_expiry_dt_utc = db_expiry.astimezone(pytz.utc)
            else:
                 # Handle case where it might not be a datetime object (though it should be)
                 logger.error(f"DB expiry for user {user_id} was not a datetime object: {type(db_expiry)}")
                 # Potentially return None or raise error
        logger.info(f"[DEBUG][Load] Prepared Expiry for Credentials (User {user_id}): {aware_expiry_dt_utc}, Type: {type(aware_expiry_dt_utc)}, TZInfo: {getattr(aware_expiry_dt_utc, 'tzinfo', 'N/A')}")

        # --- Manual Expiry Check --- 
        is_expired = False
        if aware_expiry_dt_utc:
             now_utc = datetime.now(pytz.utc)
             # Check if expiry is in the past (adding a small buffer)
             buffer = timedelta(seconds=60)
             if now_utc >= (aware_expiry_dt_utc - buffer):
                 is_expired = True
                 logger.info(f"[ManualCheck] Token for user {user_id} appears expired (Expiry: {aware_expiry_dt_utc}, Now: {now_utc}).")
             else:
                 logger.info(f"[ManualCheck] Token for user {user_id} is not expired.")
        else:
             # No expiry time usually means it's invalid or needs refresh if possible
             logger.warning(f"[ManualCheck] Token for user {user_id} has no expiry date.")
             # Consider it potentially expired if no expiry is set, rely on refresh token presence
             is_expired = True 
        # --- End Manual Expiry Check ---

        # --- Refresh Logic (if needed) ---
        current_access_token = token_info.access_token
        current_refresh_token = token_info.refresh_token
        current_scopes = token_info.scope.split() if token_info.scope else SCOPES
        refreshed_successfully = False

        if is_expired:
            if current_refresh_token:
                 logger.info(f"Attempting credential refresh for user_id {user_id}...")
                 # Create a temporary creds object just for refresh
                 temp_creds = Credentials(None, refresh_token=current_refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET)
                 try:
                     temp_creds.refresh(Request())
                     # Update variables with refreshed data
                     current_access_token = temp_creds.token
                     if temp_creds.expiry:
                         if temp_creds.expiry.tzinfo is None:
                             aware_expiry_dt_utc = pytz.utc.localize(temp_creds.expiry)
                         else:
                             aware_expiry_dt_utc = temp_creds.expiry.astimezone(pytz.utc)
                     else:
                         aware_expiry_dt_utc = None # No expiry after refresh?
                     # Note: Refresh token usually stays the same, Google might revoke it.
                     # temp_creds.refresh_token might be None after refresh.
                     # Keep the one we originally had unless logic dictates otherwise.
                     current_scopes = temp_creds.scopes
                     refreshed_successfully = True
                     logger.info(f"Credentials refreshed successfully for user_id: {user_id}")

                     # --- Update DB with refreshed token --- 
                     token_info.access_token = current_access_token
                     token_info.expires_at = aware_expiry_dt_utc
                     token_info.scope = " ".join(current_scopes)
                     token_info.updated_at = datetime.now(pytz.utc)
                     try:
                         db.commit()
                         logger.info(f"Updated refreshed token in DB for user_id: {user_id}")
                     except Exception as db_err:
                          logger.error(f"DB Error updating refreshed token for user_id {user_id}: {db_err}", exc_info=True)
                          db.rollback()
                          # Fail if DB update fails after successful refresh?
                          # return None 
                 except Exception as refresh_err:
                      logger.error(f"Failed to refresh credentials for user_id {user_id}: {refresh_err}", exc_info=True)
                      return None # Refresh failed
            else:
                 logger.warning(f"Credentials expired for user_id {user_id}, but no refresh token available.")
                 return None # Cannot proceed

        # --- Create Final Credentials Object --- 
        # Use potentially updated values after successful refresh
        # Convert aware datetime to naive for the Credentials object to avoid comparison issues
        naive_expiry = None
        if aware_expiry_dt_utc:
            naive_expiry = aware_expiry_dt_utc.replace(tzinfo=None)
            logger.info(f"Using naive expiry datetime for Credentials: {naive_expiry}")
        
        final_creds = Credentials(
            token=current_access_token,
            refresh_token=current_refresh_token, # Keep original refresh token
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=current_scopes,
            expiry=naive_expiry  # Use naive datetime to avoid comparison issues
        )
        logger.info(f"Final Credentials object ready for user_id: {user_id}")
        return final_creds

    except Exception as e:
        logger.error(f"Failed to process credentials object for user_id {user_id}: {e}", exc_info=True)
        return None


async def get_calendar_events(user_id: int, db: Session) -> list:
    """Fetches today's events from the specific user's primary Google Calendar."""
    logger.info(f"Fetching calendar events for user_id: {user_id}")
    creds = get_calendar_credentials(user_id=user_id, db=db)

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