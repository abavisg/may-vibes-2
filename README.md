# Personal AI Organiser

## Overview
The Personal AI Organiser is a web application designed to help users manage their tasks and calendar events efficiently. It integrates with Notion to fetch tasks and displays them alongside calendar events in a user-friendly timeline view.

## Features
- Displays calendar events and Notion tasks in a timeline format.
- Supports drag-and-drop functionality for task reordering (optional).
- Automatically schedules tasks within defined working hours (9 AM to 5 PM).
- Rounds task start times to the nearest 15-minute interval.
- Provides clear visibility of task durations and time slots.

## Technologies Used
- React for the frontend
- TypeScript for type safety
- Date-fns for date manipulation
- Notion API for task management
- CSS for styling

## Getting Started

### Prerequisites
- Node.js (version 14 or higher)
- npm (Node package manager)
- Access to Notion API with a valid integration token

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/personal-ai-organiser.git
   cd personal-ai-organiser
   ```

2. Install dependencies for both frontend and backend:
   ```bash
   # Navigate to the frontend directory
   cd frontend
   npm install

   # Navigate to the backend directory
   cd ../backend
   pip install -r requirements.txt  # Assuming you have a requirements.txt for Python dependencies
   ```

### Running the Servers

#### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the frontend server:
   ```bash
   npm run dev
   ```

3. Open your browser and go to `http://localhost:5173` to view the application.

#### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```

3. Start the backend server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. Ensure the backend is running on the expected port (default is usually 8000).

### Debugging Tips
- **Frontend Debugging**: Use the browser's developer tools (F12) to inspect elements, view console logs, and debug JavaScript errors.
- **Backend Debugging**: Add print statements or use a debugger to trace the flow of data and identify issues in your Python code.
- **Check API Responses**: Use tools like Postman or curl to test your API endpoints and ensure they return the expected data.
- **Console Logs**: Utilize `console.log` in the frontend and `print` statements in the backend to track variable values and application flow.

### Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
