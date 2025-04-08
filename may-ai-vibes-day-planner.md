🧠 May AI Vibes – Day Planner

Web app that connects to your Google Calendar and Notion to-do list, then creates an intelligent daily plan with an email summary every morning.

🚀 What It Does
The Day Planner app is your AI-powered personal assistant. It pulls in your scheduled meetings and tasks from Google Calendar and Notion, and intelligently arranges your day — ensuring goals are met, tasks are completed, and you're never double-booked. You'll receive a clear plan every morning via email to start your day with clarity.

	•	Connects to Google Calendar to import meetings and time blocks
	•	Syncs with your Notion to-do list (including tasks and meetings)
	•	Analyses your day and schedules to-dos around existing commitments
	•	Supports task prioritisation, time estimates, and deadlines
	•	Generates a daily timeline with tasks and events
	•	Sends a morning email summary with your schedule and tasks
	•	Continuously adapts to changes and missed tasks

🎯 Scope
Start with an MVP that integrates Google Calendar and Notion, generates a simple daily plan with prioritised tasks, and delivers a summary email. Future versions can add learning-based planning, energy/time preference tuning, Slack reminders, and mobile support.

⚙️ Behaviour
	•	Schedules to-do tasks intelligently into free calendar slots
	•	Respects existing meetings and busy hours
	•	Replans when meetings change or tasks are incomplete
	•	Delivers a clear and concise email every morning with your full day
	•	Lightweight web interface for viewing/editing the plan

🧱 Tech Stack
	•	Frontend: React + TailwindCSS
	•	Backend: Python (FastAPI)
	•	Database: PostgreSQL
	•	Integrations: Google Calendar API, Notion API, Gmail API or SMTP
	•	Scheduler: APScheduler or Celery
	•	Auth: Google OAuth

## Implementation Steps (Session Summary)

1.  **Project Scaffolding:**
    *   Created backend (`FastAPI`) and frontend (`React + Vite + TypeScript`) directory structure within `personal-ai-organiser/`.
    *   Set up basic FastAPI application (`main.py`) and backend `requirements.txt`.
    *   Initialized React frontend using Vite and configured Tailwind CSS.
    *   Added `.gitignore` and basic `README.md` (implied).
2.  **Backend Placeholders:**
    *   Created placeholder Python modules for Google Calendar (`google_calendar.py`), Notion (`notion.py`), Email (`email_sender.py`), Scheduler (`scheduler.py`), Auth (`auth.py`), Database models (`models.py`), and Core logic (`core.py`).
    *   Added example environment file (`backend/.env.example`, later moved).
3.  **Frontend Placeholders:**
    *   Created placeholder React components: `Dashboard.tsx`, `CalendarView.tsx`, `TaskListView.tsx`, `TimelineView.tsx`.
    *   Updated `App.tsx` to render the main `Dashboard`.
4.  **Initial Implementation:**
    *   **Google Calendar:** Implemented fetching today's events (`get_calendar_events` in `google_calendar.py`) using Google Calendar API and OAuth2. Included creating and troubleshooting the initial token generation script (`quickstart.py`).
    *   **Notion:** Implemented fetching tasks from a specified database (`get_notion_tasks` in `notion.py`) using the Notion API client.
    *   **Core Logic:** Implemented core scheduling functions in `core.py`:
        *   `find_free_slots`: Calculates available time slots based on calendar events and working hours, handling timezones.
        *   `prioritize_tasks`: Sorts Notion tasks based on deadline and priority.
        *   `schedule_tasks`: Allocates prioritized tasks into free slots.
        *   `format_plan`: Combines events and scheduled tasks into a final sorted list.
    *   Added `pytz` dependency for timezone handling.
5.  **Cleanup:** Removed redundant `frontend` directory from the workspace root.
6.  **Backend Authentication & Database:**
    *   Added `User` and `OAuthToken` SQLAlchemy models (`models.py`).
    *   Configured SQLAlchemy engine, session (`SessionLocal`), and `get_db` dependency.
    *   Integrated database table creation (`create_db_tables`) on app startup.
    *   Added `itsdangerous` dependency and configured `SessionMiddleware` for session management (`main.py`).
    *   Implemented Google OAuth web authentication flow (`/auth/google`, `/auth/google/callback`) using `google-auth-oauthlib`.
    *   Implemented logic in callback to exchange code, fetch user info, create/update `User` and `OAuthToken` records in the database, and set user ID in session.
    *   Added `/user/me` endpoint to fetch logged-in user data from session/DB.
    *   Added `/auth/logout` endpoint to clear the session.
    *   Refactored `google_calendar.py` (`get_calendar_credentials`, `get_calendar_events`) to retrieve user-specific tokens from the database and handle token refresh/update in DB.
    *   Refactored `core.py` (`generate_daily_plan`) and `scheduler.py` (`daily_planning_and_email_job`) to accept `user_id` and `db` session for user-specific processing.
    *   Updated manual trigger endpoints (`/schedule/run/manual`, `/schedule/generate/manual`) to be user-specific and protected by authentication dependency.
    *   Ensured consistent relative imports within the backend package.
    *   Troubleshot and resolved various configuration and runtime errors (`redirect_uri_mismatch`, `ModuleNotFoundError`, `InsecureTransportError`, `Database not configured`).