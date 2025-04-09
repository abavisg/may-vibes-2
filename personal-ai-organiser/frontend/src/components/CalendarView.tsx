import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

// TODO: Fetch and display Google Calendar events

const CalendarView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { calendarEvents, isLoading, error } = useData();

  const formatTime = (isoString: string | null): string => {
      if (!isoString) return "Time N/A";
      try {
         // Simple time formatting, adjust as needed
         return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      } catch { return "Invalid Date"; }
  };

  return (
    <div>
      {isLoading && <p className="text-gray-600 dark:text-gray-400">Loading calendar...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!isLoading && !error && calendarEvents.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No calendar events found for today.</p>
      )}
      {!isLoading && !error && calendarEvents.length > 0 && (
        <ul className="space-y-2">
          {calendarEvents.map((event) => (
            <li key={event.id} className="p-2 border rounded bg-blue-50 dark:bg-blue-900/50 border-blue-200 dark:border-blue-700">
              <p className="font-medium text-blue-800 dark:text-blue-200">{event.summary || 'No Title'}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {formatTime(event.start)} - {formatTime(event.end)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CalendarView; 