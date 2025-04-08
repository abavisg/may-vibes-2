# quickstart.py
import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_PATH = "token.json"
CREDS_PATH = "credentials.json"

def main():
    """Shows basic usage of the Google Calendar API.
    Performs the initial OAuth2 flow using port 8080 and saves credentials to token.json.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            logger.info(f"Credentials loaded from {TOKEN_PATH}")
        except Exception as e:
             logger.error(f"Error loading {TOKEN_PATH}, will re-authenticate: {e}")


    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh credentials, re-authenticating: {e}")
                creds = None # Force re-authentication

        # Only run the flow if creds are still missing/invalid
        if not creds or not creds.valid:
            if os.path.exists(CREDS_PATH):
                logger.info(f"Credentials file found at {CREDS_PATH}. Starting auth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                # Use fixed port 8080, ensure it's in Google Cloud Console Redirect URIs
                try:
                    creds = flow.run_local_server(port=8080)
                    logger.info("Authentication flow completed.")
                except OSError as e:
                    if e.errno == 48: # Address already in use
                         logger.error("ERROR: Port 8080 is already in use by another application.")
                         logger.error("Please stop the other application or choose a different port.")
                         logger.error("If changing port, update Google Cloud Console Redirect URIs and this script.")
                    else:
                        logger.error(f"An OS error occurred during auth flow: {e}")
                    return # Exit if port is in use or other OS error
                except Exception as e:
                    logger.error(f"An unexpected error occurred during auth flow: {e}")
                    return # Exit on other errors

            else:
                logger.error(f"Credentials file ({CREDS_PATH}) not found. Cannot authenticate.")
                logger.error("Please download your credentials from Google Cloud Console and save as credentials.json")
                return # Exit if credentials file is missing

        # Save the credentials for the next run (only if flow ran successfully)
        if creds: # Ensure creds object exists after potential flow run
            try:
                with open(TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())
                logger.info(f"Credentials saved to {TOKEN_PATH}")
            except Exception as e:
                 logger.error(f"Error saving credentials to {TOKEN_PATH}: {e}")

    # Test the API (Optional part, just confirms credentials work)
    if creds and creds.valid:
        try:
            service = build("calendar", "v3", credentials=creds)
            logger.info("Successfully built calendar service. Credentials appear valid.")
            # You could add a simple API call here if you want, like listing calendars
            # now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            # events_result = service.events().list(
            #     calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime"
            # ).execute()
            # events = events_result.get("items", [])
            # if not events:
            #     logger.info("No upcoming events found for testing.")
            # else:
            #      logger.info(f"Found {len(events)} upcoming events (test).")

        except HttpError as error:
            logger.error(f"An API error occurred during test: {error}")
        except Exception as e:
             logger.error(f"An unexpected error occurred during test: {e}")
    else:
         logger.warning("Could not obtain valid credentials for API test.")


if __name__ == "__main__":
    main()