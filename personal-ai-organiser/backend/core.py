# Placeholder for the core scheduling and planning logic

# Use relative imports for sibling modules
from .google_calendar import get_calendar_events
from .notion import get_notion_tasks
from .models import User, DailyPlan # Import DailyPlan

import logging
from datetime import datetime, time, timedelta, date
import pytz # For timezone handling
from sqlalchemy.orm import Session # Import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# TODO: Make these configurable per user in the future
LOCAL_TIMEZONE = pytz.timezone("Europe/London") # ADJUST to your local timezone
WORK_START_HOUR = 9
WORK_END_HOUR = 17
MIN_SLOT_DURATION_MINUTES = 15
PRIORITY_MAP = {"High": 3, "Medium": 2, "Low": 1} # Adjust if your Notion priorities differ
# --- End Configuration ---

def parse_datetime(dt_str: str | None, tzinfo: pytz.BaseTzInfo) -> datetime | None:
    """Safely parse ISO format date or datetime strings into timezone-aware datetime objects."""
    if not dt_str:
        return None
    try:
        if 'T' in dt_str: # Datetime string
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else: # Date string (assume start of day)
            dt_date = date.fromisoformat(dt_str)
            # Assume date-only events are for the local timezone
            dt = tzinfo.localize(datetime.combine(dt_date, time.min))
        
        # Ensure the datetime is timezone-aware, converting if necessary
        if dt.tzinfo is None:
            # If still naive, assume it was UTC if it had Z, otherwise assume local
            if dt_str.endswith('Z'):
                dt = pytz.utc.localize(dt)
            else:
                 dt = tzinfo.localize(dt) # This might be incorrect if original date string implied a different TZ
        
        # Convert to the target local timezone
        return dt.astimezone(tzinfo)
    except ValueError as e:
        logger.warning(f"Could not parse datetime string '{dt_str}': {e}")
        return None

def find_free_slots(events: list, today: date, tzinfo: pytz.BaseTzInfo) -> list[tuple[datetime, datetime]]:
    """Finds free time slots between events during working hours for a specific day."""
    logger.info(f"Finding free slots for {today.isoformat()} in timezone {tzinfo}")
    
    work_start_dt = tzinfo.localize(datetime.combine(today, time(WORK_START_HOUR, 0)))
    work_end_dt = tzinfo.localize(datetime.combine(today, time(WORK_END_HOUR, 0)))
    min_slot_duration = timedelta(minutes=MIN_SLOT_DURATION_MINUTES)
    
    busy_intervals: list[tuple[datetime, datetime]] = []

    for event in events:
        start_str = event.get('start')
        end_str = event.get('end')

        start_dt = parse_datetime(start_str, tzinfo)
        end_dt = parse_datetime(end_str, tzinfo)

        if not start_dt or not end_dt:
            logger.warning(f"Skipping event due to parse error: {event.get('summary')}")
            continue
            
        # Handle all-day events (parsed as start of day)
        # If it's an all-day event (time is 00:00) and duration is exactly 1 day or more, 
        # treat it as blocking the entire working day(s) it spans.
        is_all_day = start_dt.time() == time.min and (end_dt - start_dt) >= timedelta(days=1)

        if is_all_day:
             # If the all-day event *starts* today, it blocks from work_start_dt
            if start_dt.date() == today:
                effective_start = max(start_dt, work_start_dt)
            else: # Starts before today
                 effective_start = work_start_dt
            
             # If the all-day event *ends* today (or after), it blocks until work_end_dt
            if end_dt.date() >= today:
                 effective_end = min(end_dt, work_end_dt) # Clamp end time if event ends today
                 if end_dt.date() > today: # If it ends after today, blocks whole day
                     effective_end = work_end_dt
            else: # Ends before today (shouldn't happen with daily fetch, but safety)
                 continue # Doesn't affect today
            
            # Handle cases where event might start after work end or end before work start
            if effective_start < work_end_dt and effective_end > work_start_dt:
                busy_intervals.append((max(effective_start, work_start_dt), min(effective_end, work_end_dt)))
        else:
            # Regular event: Clamp to working hours and ensure it overlaps with today
            event_today_start = max(start_dt, work_start_dt)
            event_today_end = min(end_dt, work_end_dt)

            if event_today_start < event_today_end: # Ensure valid interval within working hours
                busy_intervals.append((event_today_start, event_today_end))

    if not busy_intervals:
        logger.info("No busy intervals found within working hours.")
        if work_end_dt > work_start_dt + min_slot_duration:
             return [(work_start_dt, work_end_dt)]
        else:
             return []

    # Sort intervals by start time
    busy_intervals.sort()

    # Merge overlapping intervals
    merged_busy: list[tuple[datetime, datetime]] = []
    if busy_intervals:
        current_start, current_end = busy_intervals[0]
        for next_start, next_end in busy_intervals[1:]:
            if next_start <= current_end: # Overlap or adjacent
                current_end = max(current_end, next_end)
            else:
                merged_busy.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        merged_busy.append((current_start, current_end))
    
    logger.info(f"Merged busy intervals: {merged_busy}")

    # Calculate free slots
    free_slots: list[tuple[datetime, datetime]] = []
    last_busy_end = work_start_dt

    for busy_start, busy_end in merged_busy:
        free_start = last_busy_end
        free_end = busy_start
        if free_end > free_start + min_slot_duration:
            free_slots.append((free_start, free_end))
        last_busy_end = max(last_busy_end, busy_end)

    # Add final free slot from last busy interval to end of working day
    free_start = last_busy_end
    free_end = work_end_dt
    if free_end > free_start + min_slot_duration:
        free_slots.append((free_start, free_end))

    logger.info(f"Calculated free slots: {free_slots}")
    return free_slots

def prioritize_tasks(tasks: list, today: date) -> list:
    """Prioritizes tasks based on deadline and priority property."""
    logger.info(f"Prioritizing {len(tasks)} tasks.")
    prioritized = []
    for task in tasks:
        # Skip tasks without an estimated duration
        estimate_hours = task.get('estimate_hours')
        if estimate_hours is None or estimate_hours <= 0:
            logger.debug(f"Skipping task '{task.get('title')}' - no valid estimate.")
            continue
            
        deadline_str = task.get('deadline')
        deadline_date = date.fromisoformat(deadline_str) if deadline_str else None
        priority_str = task.get('priority')

        # --- Scoring --- 
        # Deadline score: Lower number is higher priority (days until deadline)
        # Give tasks due today/past highest priority (0)
        # Give tasks with no deadline lowest priority (large number)
        deadline_score = float('inf')
        if deadline_date:
            days_until = (deadline_date - today).days
            deadline_score = max(0, days_until) # Treat past due as due today for sorting
        
        # Priority score: Higher number is higher priority
        priority_score = PRIORITY_MAP.get(priority_str, 0) # Default to 0 if priority not mapped

        task['_deadline_score'] = deadline_score
        task['_priority_score'] = priority_score
        prioritized.append(task)

    logger.info(f"prioritizing {len(prioritized)} tasks.")

    # Sort: 1st by deadline (ascending days until), 2nd by priority (descending score)
    prioritized.sort(key=lambda t: (t['_deadline_score'], -t['_priority_score']))
    
    logger.info(f"Finished prioritizing {len(prioritized)} tasks.")
    # Log the order for debugging
    # for i, task in enumerate(prioritized):
    #      logger.debug(f"  {i+1}. {task['title']} (Deadline Score: {task['_deadline_score']}, Priority Score: {task['_priority_score']})")
          
    return prioritized

def schedule_tasks(tasks: list, free_slots: list[tuple[datetime, datetime]]) -> list:
    """Schedules prioritized tasks into available free time slots."""
    logger.info(f"Attempting to schedule {len(tasks)} tasks into {len(free_slots)} free slots.")
    scheduled_tasks = []
    remaining_slots = free_slots[:] # Work with a copy

    for task in tasks:
        task_duration_hours = task.get('estimate_hours', 0)
        if task_duration_hours <= 0:
            continue # Should have been filtered by prioritize_tasks, but safety check
        
        task_duration = timedelta(hours=task_duration_hours)
        task_scheduled = False

        for i, (slot_start, slot_end) in enumerate(remaining_slots):
            slot_duration = slot_end - slot_start
            
            if slot_duration >= task_duration:
                # Fit the task into this slot
                task_start_time = slot_start
                task_end_time = slot_start + task_duration
                
                scheduled_tasks.append({
                    **task, # Copy original task data
                    'start': task_start_time, # Store as datetime objects for now
                    'end': task_end_time,
                })
                logger.info(f"Scheduled task '{task.get('title')}' from {task_start_time} to {task_end_time}")

                # Update the remaining slots
                # If task perfectly fits slot, remove slot
                if slot_duration == task_duration:
                    remaining_slots.pop(i)
                else: # Task took beginning of slot, update slot start time
                    remaining_slots[i] = (task_end_time, slot_end)
                
                task_scheduled = True
                break # Move to the next task
            
        if not task_scheduled:
             logger.warning(f"Could not find a suitable slot for task: '{task.get('title')}' (duration: {task_duration_hours}h)")
    
    logger.info(f"Scheduled {len(scheduled_tasks)} tasks.")
    return scheduled_tasks

def format_plan(scheduled_tasks: list, events: list) -> list:
    """Combines events and scheduled tasks into a sorted list for the final plan."""
    logger.info("Formatting final plan.")
    plan = []
    
    # Add original events, converting times to ISO strings
    for event in events:
        start_dt = parse_datetime(event.get('start'), LOCAL_TIMEZONE)
        end_dt = parse_datetime(event.get('end'), LOCAL_TIMEZONE)
        plan.append({
            **event,
            'start': start_dt.isoformat() if start_dt else event.get('start'),
            'end': end_dt.isoformat() if end_dt else event.get('end'),
            'type': 'event'
        })
        
    # Add scheduled tasks, converting times to ISO strings
    for task in scheduled_tasks:
         # Ensure start/end are datetime before formatting
        start_dt = task.get('start') 
        end_dt = task.get('end')
        plan.append({
             **task, 
            'start': start_dt.isoformat() if isinstance(start_dt, datetime) else None,
            'end': end_dt.isoformat() if isinstance(end_dt, datetime) else None,
            'type': 'task'
        })

    # Sort the combined plan by start time
    plan.sort(key=lambda x: x.get('start') or "") # Handle potential None start times

    logger.info(f"Final formatted plan contains {len(plan)} items.")
    return plan

# --- Main Orchestration Function ---
async def generate_daily_plan(user_id: int, db: Session):
    """Fetches data for a specific user, finds free slots, prioritizes and schedules tasks, formats plan."""
    logger.info(f"--- Starting Daily Plan Generation for User ID: {user_id} ---")
    
    # TODO: Fetch user-specific settings (timezone, work hours) from DB if implemented
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     logger.error(f"User not found for ID: {user_id}")
    #     return None
    # current_timezone = pytz.timezone(user.settings.get('timezone', "Europe/London"))
    current_timezone = LOCAL_TIMEZONE # Using global for now
    
    today_local = datetime.now(current_timezone).date()
    logger.info(f"Generating plan for date: {today_local.isoformat()} in timezone {current_timezone}")

    # 1. Fetch data (pass user_id and db to Google Calendar)
    logger.info(f"Fetching Google Calendar events for user_id: {user_id}...")
    calendar_events = await get_calendar_events(user_id=user_id, db=db) 
    logger.info(f"Fetched {len(calendar_events)} calendar events for user_id: {user_id}.")
    
    # TODO: If Notion access is per-user, refactor get_notion_tasks similarly
    # logger.info(f"Fetching Notion tasks for user_id: {user_id}...")
    # notion_tasks = await get_notion_tasks(user_id=user_id, db=db) 
    logger.info("Fetching Notion tasks (using global config for now)...")
    notion_tasks = await get_notion_tasks() # Using global Notion config for now     
    logger.info(f"Fetched {len(notion_tasks)} Notion tasks.")
    
    if calendar_events is None or notion_tasks is None:
         logger.error(f"Failed to fetch data for user_id {user_id}. Aborting plan generation.")
         return None # Indicate failure

    # 2. Identify free time slots (pass user's timezone)
    free_slots = find_free_slots(calendar_events, today_local, current_timezone)

    # 3. Prioritize and filter tasks
    prioritized_tasks = prioritize_tasks(notion_tasks, today_local)

    # 4. Schedule tasks into free slots
    tasks_scheduled_today = schedule_tasks(prioritized_tasks, free_slots)

    # 5. Handle carry-over tasks (TODO: Implement later if needed)

    # 6. Format the plan for storage/email
    final_plan = format_plan(tasks_scheduled_today, calendar_events)

    # 7. Save the plan to the database
    if final_plan:
        try:
            # Delete existing plan for the same user and date, if any
            db.query(DailyPlan).filter(
                DailyPlan.user_id == user_id, 
                DailyPlan.plan_date == today_local
            ).delete()
            # Note: For non-SQLite DBs, might need synchronize_session=False on delete
            # db.flush() # Optional: flush deletion before adding new

            new_db_plan = DailyPlan(
                user_id=user_id,
                plan_date=today_local, # Store the date the plan is for
                plan_data=final_plan # Store the formatted plan list/dict as JSON
            )
            db.add(new_db_plan)
            db.commit()
            logger.info(f"Successfully saved generated plan to database for user {user_id}, date {today_local.isoformat()}")
        except Exception as e:
            logger.error(f"Failed to save plan to database for user {user_id}: {e}", exc_info=True)
            db.rollback()
            # Decide if failure to save should prevent returning the plan
            # return None # Option: Return None if saving fails

    logger.info(f"--- Daily Plan Generation Complete for User ID: {user_id} ---")
    return final_plan # Return the generated plan whether saved or not (unless critical) 