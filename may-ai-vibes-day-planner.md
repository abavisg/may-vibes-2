🧠 May AI Vibes – Day Planner

Web app that connects to your Google Calendar and Notion to-do list, then creates an intelligent daily plan with an email summary every morning.

🚀 What It Does
The Day Planner app is your AI-powered personal assistant. It pulls in your scheduled meetings and tasks from Google Calendar and Notion, and intelligently arranges your day — ensuring goals are met, tasks are completed, and you’re never double-booked. You’ll receive a clear plan every morning via email to start your day with clarity.

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