import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlanItem } from '../context/AuthContext'; // Import PlanItem type

// TODO: Fetch combined calendar events and scheduled tasks
// TODO: Implement timeline view (e.g., hourly slots)
// TODO: Implement drag and drop for task reordering (optional)

const TimelineView: React.FC = () => {
  const { fetchDashboardData, isAuthenticated } = useAuth();
  const [plan, setPlan] = useState<PlanItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!isAuthenticated) return;
      
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchDashboardData();
        if (data && data.plan) {
          setPlan(data.plan); // Use the combined plan directly
        } else {
          setPlan([]);
        }
      } catch (err) {
        console.error("Failed to load timeline data:", err);
        setError("Failed to load timeline data.");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isAuthenticated, fetchDashboardData]);

  const formatTime = (isoString: string | null): string => {
      if (!isoString) return "Time N/A";
      // Handle potential date-only strings
      if (!isoString.includes('T')) return "All Day"; 
      try {
         return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      } catch { return "Invalid Date"; }
  };

  return (
    <div>
      {isLoading && <p className="text-gray-600 dark:text-gray-400">Loading timeline...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!isLoading && !error && plan.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No plan available for today.</p>
      )}
      {!isLoading && !error && plan.length > 0 && (
        <ul className="space-y-2">
          {plan.map((item) => {
            const isEvent = item.type === 'event';
            const bgColor = isEvent ? 'bg-blue-50 dark:bg-blue-900/50' : 'bg-yellow-50 dark:bg-yellow-900/50';
            const borderColor = isEvent ? 'border-blue-200 dark:border-blue-700' : 'border-yellow-200 dark:border-yellow-700';
            const titleColor = isEvent ? 'text-blue-800 dark:text-blue-200' : 'text-yellow-800 dark:text-yellow-200';
            const title = isEvent ? item.summary : item.title;
            
            return (
              <li key={item.id} className={`p-2 border rounded ${bgColor} ${borderColor}`}>
                <p className={`font-medium ${titleColor}`}>{title || (isEvent ? 'No Title' : 'Untitled Task')}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                    {formatTime(item.start)} - {formatTime(item.end)}
                </p>
                {/* Optionally add task details again here if desired */}
              </li>
            );
          })}
        </ul>
      )}
       {/* TODO: Add drag-and-drop functionality here eventually */} 
    </div>
  );
};

export default TimelineView; 