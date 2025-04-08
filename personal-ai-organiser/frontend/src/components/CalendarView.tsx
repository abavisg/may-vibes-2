import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlanItem } from '../context/AuthContext'; // Import PlanItem type
import apiClient from '../context/apiClient';

// TODO: Fetch and display Google Calendar events

const CalendarView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [events, setEvents] = useState<PlanItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!isAuthenticated) return; // Don't fetch if not logged in
      
      setIsLoading(true);
      setError(null);
      try {
        // Fetch events directly from the Google Calendar endpoint
        const response = await apiClient.get('/calendar/events');
        if (response.data && response.data.events) {
          console.log(`Loaded ${response.data.events.length} calendar events directly from API`);
          setEvents(response.data.events);
        } else {
          console.log("No calendar events available");
          setEvents([]); // Set empty if no events data
        }
      } catch (err) {
        console.error("Failed to load calendar events:", err);
        setError("Failed to load calendar events.");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isAuthenticated]); // Re-run if auth state changes

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
      {!isLoading && !error && events.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No calendar events found for today.</p>
      )}
      {!isLoading && !error && events.length > 0 && (
        <ul className="space-y-2">
          {events.map((event) => (
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