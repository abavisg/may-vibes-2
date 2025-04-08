import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlanItem } from '../context/AuthContext'; // Import PlanItem type
import apiClient from '../context/apiClient';

// TODO: Fetch combined calendar events and scheduled tasks
// TODO: Implement timeline view (e.g., hourly slots)
// TODO: Implement drag and drop for task reordering (optional)

const TimelineView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState<PlanItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!isAuthenticated) return; // Don't fetch if not logged in
      
      setIsLoading(true);
      setError(null);
      try {
        // Fetch both calendar events and Notion tasks in parallel
        const [calendarResponse, notionResponse] = await Promise.all([
          apiClient.get('/calendar/events'),
          apiClient.get('/notion/tasks')
        ]);

        const calendarEvents = calendarResponse.data?.events || [];
        const notionTasks = notionResponse.data?.tasks || [];

        console.log(`Loaded ${calendarEvents.length} calendar events and ${notionTasks.length} Notion tasks directly from API`);
        
        // Combine and sort all items by start time
        const allItems = [...calendarEvents, ...notionTasks].sort((a, b) => {
          const timeA = a.start ? new Date(a.start).getTime() : 0;
          const timeB = b.start ? new Date(b.start).getTime() : 0;
          return timeA - timeB;
        });

        setItems(allItems);
      } catch (err) {
        console.error("Failed to load timeline items:", err);
        setError("Failed to load timeline items.");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isAuthenticated]); // Re-run if auth state changes

  const formatTime = (isoString: string | null): string => {
    if (!isoString) return "Time N/A";
    try {
      return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    } catch { return "Invalid Date"; }
  };

  return (
    <div>
      {isLoading && <p className="text-gray-600 dark:text-gray-400">Loading timeline...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!isLoading && !error && items.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No items found for today.</p>
      )}
      {!isLoading && !error && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((item) => (
            <li 
              key={item.id} 
              className={`p-2 border rounded ${
                item.type === 'event' 
                  ? 'bg-blue-50 dark:bg-blue-900/50 border-blue-200 dark:border-blue-700' 
                  : 'bg-green-50 dark:bg-green-900/50 border-green-200 dark:border-green-700'
              }`}
            >
              <p className={`font-medium ${
                item.type === 'event' 
                  ? 'text-blue-800 dark:text-blue-200' 
                  : 'text-green-800 dark:text-green-200'
              }`}>
                {item.summary || item.title || 'No Title'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {formatTime(item.start)} - {formatTime(item.end)}
              </p>
              {item.type === 'task' && item.priority && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Priority: {item.priority}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
       {/* TODO: Add drag-and-drop functionality here eventually */} 
    </div>
  );
};

export default TimelineView; 