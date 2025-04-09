import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import './Timeline.css';

// TODO: Fetch and display Google Calendar events

const CalendarView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { calendarEvents, isLoading, error } = useData();

  const formatTime = (isoString: string | null): string => {
    if (!isoString) return "Time N/A";
    try {
      return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    } catch { return "Invalid Date"; }
  };

  if (isLoading) {
    return <div className="calendar-loading">Loading calendar events...</div>;
  }

  if (error) {
    return <div className="calendar-error">{error}</div>;
  }

  return (
    <div className="calendar-container">
      {calendarEvents.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-2">No calendar events found for today.</p>
      ) : (
        <ul className="calendar-list">
          {calendarEvents.map((event) => (
            <li key={event.id} className="calendar-item">
              <div className="calendar-item-content">
                <span className="calendar-time">{formatTime(event.start)}</span>
                <span className="calendar-summary">{event.summary}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CalendarView; 