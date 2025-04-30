# Personal AI Organiser

A web application that helps users manage their tasks and calendar events efficiently by integrating with Notion and presenting everything in a visual timeline.

## Features

- **Calendar + Task View** – Displays calendar events and Notion tasks in a unified timeline format.
- **Auto Scheduling** – Automatically arranges tasks within working hours (9 AM to 5 PM).
- **Smart Time Slots** – Rounds task start times to the nearest 15-minute interval.
- **Drag-and-Drop UI** – (Optional) Reorder tasks interactively on the timeline.
- **Visual Clarity** – Easily see task durations and gaps in your schedule.

## Tech stack

- React (frontend)
- TypeScript
- Notion API (task integration)
- Date-fns (date manipulation)
- CSS (styling)
- FastAPI + Python (backend)

## Architecture

- **Frontend**: Built with React and TypeScript, communicates with backend API, renders task+calendar timeline.
- **Backend**: FastAPI server that pulls task data from Notion and formats it for frontend use.
- **Data Flow**: Backend → Notion API → Formatted Tasks → Frontend Timeline View.

## API Endpoints

[To be documented if needed, based on the backend FastAPI endpoints.]


## Setup the application

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/personal-ai-organiser.git
   cd personal-ai-organiser
   ```

2. Install frontend dependencies:

   ```bash
   cd frontend
   npm install
   ```

3. Install backend dependencies:

   ```bash
   cd ../backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Run the application

### Frontend

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser.

### Backend

```bash
cd backend
source venv/bin/activate  # Windows: .\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Backend should be available at `http://localhost:8000`

## License

MIT