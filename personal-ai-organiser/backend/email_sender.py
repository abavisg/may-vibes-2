# Placeholder for email sending logic (Gmail API or SMTP)

import os
import smtplib
import ssl
import logging
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Email credentials from environment variables
SENDER_EMAIL = os.getenv("EMAIL_SENDER_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD") # Use App Password for Gmail
DEFAULT_RECIPIENT_EMAIL = os.getenv("EMAIL_RECIPIENT_ADDRESS") # Renamed for clarity
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465)) # Default to 465 for SSL

def format_plan_for_email(plan: list) -> str:
    """Formats the combined plan (events and tasks) into a readable HTML email body."""
    html_body = "<html><head><style>" \
                "body { font-family: sans-serif; }" \
                "ul { list-style: none; padding-left: 0; }" \
                "li { margin-bottom: 15px; padding: 10px; border-radius: 5px; }" \
                ".event { background-color: #e0f2fe; border-left: 5px solid #3b82f6; }" \
                ".task { background-color: #fef3c7; border-left: 5px solid #f59e0b; }" \
                ".time { font-weight: bold; display: block; margin-bottom: 5px; }" \
                ".title { font-size: 1.1em; }" \
                ".details { font-size: 0.9em; color: #555; }" \
                "</style></head><body>"
    html_body += "<h2>Your AI-Generated Daily Plan</h2>"
    html_body += "<ul>"

    if not plan:
        html_body += "<li>No events or scheduled tasks for today.</li>"
    else:
        for item in plan:
            item_type = item.get('type', 'event') # Default to event if type missing
            css_class = 'event' if item_type == 'event' else 'task'
            
            start_str = item.get('start')
            end_str = item.get('end')
            time_str = "All Day" if 'T' not in start_str else ""
            
            try:
                if 'T' in start_str:
                    start_dt = datetime.fromisoformat(start_str)
                    start_time = start_dt.strftime("%I:%M %p") # Format time
                    if end_str and 'T' in end_str:
                         end_dt = datetime.fromisoformat(end_str)
                         end_time = end_dt.strftime("%I:%M %p")
                         time_str = f"{start_time} - {end_time}"
                    else:
                         time_str = start_time
                # Handle date-only string if needed, though format_plan should provide datetime ISO strings
                elif start_str: 
                     start_dt_date = datetime.fromisoformat(start_str)
                     time_str = f"All Day ({start_dt_date.strftime('%Y-%m-%d')})"
                     
            except Exception as e:
                 logger.warning(f"Could not parse time for email item '{item.get('summary', item.get('title'))}': {e}")
                 time_str = "Time TBD"

            title = item.get('summary') if item_type == 'event' else item.get('title', 'Untitled Task')
            
            html_body += f'<li class="{css_class}">'
            html_body += f'<span class="time">{time_str}</span>'
            html_body += f'<span class="title">{title}</span>'
            
            # Add details for tasks
            if item_type == 'task':
                details = []
                if item.get('priority'): details.append(f"Priority: {item['priority']}")
                if item.get('duration'): details.append(f"Est: {item['duration']}h")
                if item.get('deadline'): details.append(f"Deadline: {item['deadline']}")
                if details:
                    html_body += f'<div class="details">{' | '.join(details)}</div>'
                if item.get('url'):
                    html_body += f'<div class="details"><a href="{item['url']}">View in Notion</a></div>'

            html_body += "</li>"

    html_body += "</ul></body></html>"
    return html_body

async def send_daily_summary_email(plan: list, recipient_email: str | None = None):
    """Sends the daily plan summary email using SMTP.

    Args:
        plan: The list representing the daily plan.
        recipient_email: The email address to send the plan to. 
                         If None, falls back to DEFAULT_RECIPIENT_EMAIL from .env.
    """
    target_email = recipient_email or DEFAULT_RECIPIENT_EMAIL
    
    if not target_email:
         logger.error("No recipient email address provided or configured in .env. Cannot send email.")
         return False
         
    if not all([SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        logger.error("Email sender configuration missing in environment variables. Cannot send email.")
        return False

    logger.info(f"Preparing to send daily summary email to {target_email}")

    message = EmailMessage()
    message["Subject"] = f"Your Daily Plan for {datetime.now().strftime('%Y-%m-%d')}"
    message["From"] = SENDER_EMAIL
    message["To"] = target_email # Use the target email address

    # Format the plan into an HTML body
    email_body = format_plan_for_email(plan)
    message.set_content("Please enable HTML to view your daily plan.") # Fallback
    message.add_alternative(email_body, subtype='html')

    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT} using SSL...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            logger.info("Logging into SMTP server...")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            logger.info(f"Sending email to {target_email}...")
            server.send_message(message)
            logger.info(f"Daily summary email successfully sent to {target_email}")
            return True
    except smtplib.SMTPAuthenticationError as e:
         logger.error(f"SMTP Authentication Error: {e}. Check sender email/password (App Password?).")
         return False
    except smtplib.SMTPConnectError as e:
         logger.error(f"SMTP Connection Error: {e}. Check SMTP server/port.")
         return False
    except ssl.SSLError as e:
         logger.error(f"SSL Error: {e}. Check port (maybe use STARTTLS on 587 instead?).")
         return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email to {target_email}: {e}", exc_info=True)
        return False 