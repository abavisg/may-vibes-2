import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlanItem } from '../context/AuthContext'; // Import PlanItem type

// TODO: Fetch and display tasks from Notion

const TaskListView: React.FC = () => {
  const { fetchDashboardData, isAuthenticated } = useAuth();
  const [tasks, setTasks] = useState<PlanItem[]>([]);
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
          // Filter only tasks from the plan
          setTasks(data.plan.filter(item => item.type === 'task'));
        } else {
          setTasks([]);
        }
      } catch (err) {
        console.error("Failed to load tasks:", err);
        setError("Failed to load tasks.");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isAuthenticated, fetchDashboardData]);

  return (
    <div>
      {isLoading && <p className="text-gray-600 dark:text-gray-400">Loading tasks...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!isLoading && !error && tasks.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No tasks found in the plan.</p>
      )}
      {!isLoading && !error && tasks.length > 0 && (
        <ul className="space-y-2">
          {tasks.map((task) => (
            <li key={task.id} className="p-2 border rounded bg-yellow-50 dark:bg-yellow-900/50 border-yellow-200 dark:border-yellow-700">
              <p className="font-medium text-yellow-800 dark:text-yellow-200">{task.title || 'Untitled Task'}</p>
              {/* Display Task Details */}
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1 space-x-2">
                {task.priority && <span>Prio: {task.priority}</span>}
                {task.estimate_hours && <span>Est: {task.estimate_hours}h</span>}
                {task.deadline && <span>Due: {task.deadline}</span>}
              </div>
               {task.url && 
                <a 
                  href={task.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                >
                  View in Notion
                </a>
              }
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TaskListView; 