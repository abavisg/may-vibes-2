import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

// TODO: Fetch and display tasks from Notion

const TaskListView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { notionTasks, isLoading, error } = useData();

  return (
    <div>
      {isLoading && <p className="text-gray-600 dark:text-gray-400">Loading tasks...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!isLoading && !error && notionTasks.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400">No tasks found in Notion.</p>
      )}
      {!isLoading && !error && notionTasks.length > 0 && (
        <ul className="space-y-2">
          {notionTasks.map((task) => (
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