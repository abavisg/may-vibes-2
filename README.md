# Personal AI Organiser

A full-stack web application that connects to Google Calendar and Notion to create an intelligent daily plan and sends a morning email summary.

## Features

- **Google Calendar Integration**: Fetches daily events.
- **Notion Integration**: Fetches tasks from a specified database.
- **Intelligent Scheduling**: Prioritizes tasks and finds free slots in your schedule (between configurable working hours).
- **Unified Dashboard**: Displays calendar events and scheduled tasks.
- **Authentication**: Secure login via Google OAuth 2.0.
- **Database Storage**: Persists user information, OAuth tokens, and generated daily plans (PostgreSQL or SQLite).
- **Automated Email Summary**: Sends a daily plan summary via email (using APScheduler).

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Axios
- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL / SQLite, Uvicorn
- **Authentication**: Google OAuth 2.0, FastAPI Session Middleware
- **Scheduling**: APScheduler
- **APIs**: Google Calendar API, Notion API, Gmail API (via SMTP)
- **Other**: Pydantic, python-dotenv, pytz, requests

## Architecture

- **Frontend**: Handles user interface, login flow, and displays dashboard data fetched from the backend.
- **Backend**: FastAPI server providing API endpoints for authentication, data fetching (Google Calendar, Notion), plan generation, and serving dashboard data. Handles database interactions and background scheduling.
- **Database**: Stores user profiles, OAuth tokens (securely), and generated daily plans.
- **Scheduler**: Runs background jobs (e.g., daily plan generation and emailing) for authenticated users.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd personal-ai-organiser
    ```

2.  **Backend Setup**:
    - Navigate to the backend directory: `cd backend`
    - Create and activate a virtual environment:
      ```bash
      python3 -m venv venv
      source venv/bin/activate  # On Windows use `.\venv\Scripts\activate`
      ```
    - Install dependencies:
      ```bash
      pip install -r requirements.txt
      ```
    - **Environment Variables**: Create a `.env` file in the `backend` directory by copying `.env.example` (if it exists) or creating it manually. Fill in the following values:
        - **Google OAuth**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` (e.g., `http://localhost:8000/auth/google/callback` for local development)
        - **Session Secret**: `SESSION_SECRET_KEY` (generate a strong, random secret key)
        - **Frontend URL**: `FRONTEND_URL` (e.g., `http://localhost:5173`)
        - **Notion**: `NOTION_API_KEY`, `NOTION_DATABASE_ID`
        - **Email (SMTP)**: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` (Consider using a Gmail App Password)
        - **Database (Optional)**: `DATABASE_URL` (e.g., `postgresql://user:password@host:port/database`). If not set, it defaults to a local SQLite file (`./app.db`).
        - **Working Hours (Optional)**: `WORK_START_HOUR` (default 9), `WORK_END_HOUR` (default 17)
        - **Timezone (Optional)**: `USER_TIMEZONE` (default 'UTC', e.g., 'Europe/London')

3.  **Frontend Setup**:
    - Navigate to the frontend directory: `cd ../frontend`
    - Install dependencies:
      ```bash
      npm install
      ```
    - **Environment Variables (Optional)**: You can create a `.env` file in the `frontend` directory to override the default backend URL:
        - `VITE_BACKEND_URL=http://localhost:8000`

## Running the Application

1.  **Run the Backend Server**:
    - Navigate to the backend directory: `cd personal-ai-organiser/backend`
    - Activate the virtual environment: `source venv/bin/activate`
    - **For Local Development (HTTP OAuth Callback)**:
        ```bash
        # The OAUTHLIB_INSECURE_TRANSPORT=1 allows OAuth callbacks over HTTP
        # DO NOT USE THIS IN PRODUCTION - Production MUST use HTTPS
        OAUTHLIB_INSECURE_TRANSPORT=1 python3 -m uvicorn main:app --port 8000
        ```
    - **For Production (HTTPS)**:
        ```bash
        # Ensure your environment provides HTTPS (e.g., via a reverse proxy like Nginx)
        # You might run gunicorn instead of uvicorn directly in production
        uvicorn main:app --host 0.0.0.0 --port 8000 # Adjust host/port as needed
        ```
    - The backend API will be available at `http://localhost:8000` (or your configured host/port).
    - The database tables will be created automatically on startup if they don't exist.

2.  **Run the Frontend Development Server**:
    - Navigate to the frontend directory: `cd personal-ai-organiser/frontend`
    - Start the development server:
      ```bash
      npm run dev
      ```
    - Open your browser and navigate to `http://localhost:5173` (or the port specified by Vite).

## Important Notes

- **HTTPS**: Google OAuth requires HTTPS for redirect URIs in production. The `OAUTHLIB_INSECURE_TRANSPORT=1` flag is **only** for bypassing this during local development over HTTP.
- **Security**: Ensure your `SESSION_SECRET_KEY` is strong and kept secret. Do not commit your `.env` file containing sensitive credentials to version control.
- **Reloading**: Avoid using `--reload` with the backend server during development if you encounter `invalid_grant` errors during the OAuth callback, as reloads can interrupt the flow.

## License

MIT