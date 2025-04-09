# Placeholder for Notion API integration logic

import os
import logging
from notion_client import AsyncClient # Use AsyncClient for FastAPI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Notion credentials from environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = None
if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    logger.error("NOTION_TOKEN or NOTION_DATABASE_ID not found in environment variables.")
    # Application might not function correctly without Notion access.
else:
    # Initialize the Notion client
    try:
        notion = AsyncClient(auth=NOTION_TOKEN)
        logger.info("Notion client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Notion client: {e}")


async def get_notion_tasks():
    """Fetches tasks from the specified Notion database."""
    if not notion:
        logger.warning("Notion client not initialized. Cannot fetch tasks.")
        return []

    logger.info(f"Fetching tasks from Notion Database ID: {NOTION_DATABASE_ID}")

    try:
        # --- ADJUST FILTER AS NEEDED ---
        # Example filter: Fetch tasks where 'Status' is not 'Done'
        # Assumes a 'Status' property of type 'status' or 'select'.
        # Adjust the property name "Status" and the value "Done" if yours are different.
        db_filter = {
            "property": "Status", # <-- ADJUST PROPERTY NAME if different
            "status": { # Use "status" if your property type is 'Status'
                "does_not_equal": "Done" # <-- ADJUST VALUE if different
            }
            # --- OR ---
            # Use "select" if your property type is 'Select'
            # "select": {
            #    "does_not_equal": "Done" # <-- ADJUST VALUE if different
            # }
        }
        # --- END ADJUST FILTER ---

        # --- ADJUST SORTS AS NEEDED ---
        # Example sort: By 'Priority' (ascending), then 'Deadline' (ascending)
        # Assumes 'Priority' and 'Deadline' properties exist.
        db_sorts = [
            # {"property": "Priority", "direction": "ascending"}, # <-- ADJUST PROPERTY NAME
            # {"property": "Deadline", "direction": "ascending"}  # <-- ADJUST PROPERTY NAME
        ]
        # --- END ADJUST SORTS ---


        response = await notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter=db_filter if 'property' in db_filter else None, # Only apply filter if defined
            sorts=db_sorts if db_sorts else [] # Pass an empty list if db_sorts is empty, not None
        )

        #logger.info(f"Notion response: {response}")

        tasks = []
        results = response.get("results", [])
        logger.info(f"Found {len(results)} raw results from Notion.")

        for page in results:
            properties = page.get("properties", {})

            # --- IMPORTANT: Adjust these property names based on your Notion DB ---
            # Title Property (usually named 'Name' or 'Task')
            task_name_prop = properties.get("Task") # <-- ADJUST PROPERTY NAME
            # Status Property ('status' or 'select' type)
            status_prop = properties.get("Status") # <-- ADJUST PROPERTY NAME
            # Priority Property ('select' type)
            priority_prop = properties.get("Type") # <-- ADJUST PROPERTY NAME
            # Deadline Property ('date' type)
            deadline_prop = properties.get("With") # <-- ADJUST PROPERTY NAME
            # Estimate Property ('number' type, e.g., hours)
            duration_prop = properties.get("Duration") # <-- ADJUST PROPERTY NAME
            # --- End of properties to adjust ---

            # Extract title safely
            task_name = "Untitled"
            if task_name_prop and task_name_prop.get("type") == "title" and task_name_prop.get("title"):
                title_list = task_name_prop.get("title", [])
                if title_list:
                    task_name = title_list[0].get("plain_text", "Untitled")

            # Extract status safely (handles 'status' and 'select' types)
            status = None
            if status_prop:
                if status_prop.get("type") == "status" and status_prop.get("status"):
                    status = status_prop.get("status", {}).get("name")
                elif status_prop.get("type") == "select" and status_prop.get("select"):
                    status = status_prop.get("select", {}).get("name")

            # Extract priority safely (assuming 'select' type)
            priority = None
            if priority_prop and priority_prop.get("type") == "select" and priority_prop.get("select"):
                 priority = priority_prop.get("select", {}).get("name")

            # Extract deadline safely (assuming 'date' type)
            deadline = None
            if deadline_prop and deadline_prop.get("type") == "date" and deadline_prop.get("date"):
                deadline_data = deadline_prop.get("date", {}).get("start")
                if deadline_data:
                    try:
                        # Handle date-only or datetime strings
                        if 'T' in deadline_data:
                             deadline = datetime.fromisoformat(deadline_data.replace("Z", "+00:00")).date()
                        else:
                             deadline = datetime.strptime(deadline_data, '%Y-%m-%d').date()
                    except ValueError:
                         logger.warning(f"Could not parse deadline date: {deadline_data} for task {task_name}")

            # Extract estimate safely (assuming 'number' type)
            estimate = None
            if duration_prop and duration_prop.get("type") == "number":
                estimate = duration_prop.get("number")

            
            task_data = {
                "id": page.get("id"),
                "title": task_name,
                "status": status,
                "priority": priority,
                "deadline": deadline.isoformat() if deadline else None,
                "duration": estimate,
                "url": page.get("url")
            }
            logger.info(f"Task data: {task_data}")
            tasks.append(task_data)
            # logger.debug(f"Processed task: {task_data}") # Use debug level for noisy logs

        logger.info(f"Successfully processed {len(tasks)} tasks from Notion.")
        return tasks

    except Exception as e:
        # Log the full exception traceback for debugging
        logger.error(f"An error occurred while fetching Notion tasks: {e}", exc_info=True)
        # Consider how to handle specific Notion API errors if needed
        # from notion_client import APIResponseError
        # if isinstance(e, APIResponseError):
        #     logger.error(f"Notion API Error: {e.code} - {e.body}")
        return [] # Return empty list on error

# --- Optional: Direct testing block ---
# To use: uncomment the block and run `python personal-ai-organiser/backend/notion.py`
# import asyncio
#
# async def main_test():
#     print("--- Testing Notion Task Fetching ---")
#     tasks = await get_notion_tasks()
#     if tasks is not None: # Check if list returned (even if empty) vs None on init error
#         print(f"Fetched {len(tasks)} Tasks:")
#         for i, task in enumerate(tasks):
#             print(f"{i+1}. ID: {task['id']}")
#             print(f"   Title: {task['title']}")
#             print(f"   Status: {task['status']}")
#             print(f"   Priority: {task['priority']}")
#             print(f"   Deadline: {task['deadline']}")
#             print(f"   Estimate (h): {task['duration']}")
#             print(f"   URL: {task['url']}")
#             print("-" * 10)
#     else:
#         print("Could not fetch tasks (client init error or other critical issue).")
#
# if __name__ == "__main__":
#      # Check if Notion client was initialized before trying to run test
#      if notion:
#          asyncio.run(main_test())
#      else:
#          print("Notion client failed to initialize. Cannot run test.")
# --- End optional testing block --- 