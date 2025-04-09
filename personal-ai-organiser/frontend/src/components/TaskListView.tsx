import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import './Timeline.css';

// TODO: Fetch and display tasks from Notion

const TaskListView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { notionTasks, isLoading, error } = useData();

  const getPriorityColor = (priority: string | null | undefined): string => {
    if (!priority) return 'low';
    
    switch (priority.toLowerCase()) {
      case 'high':
        return 'high';
      case 'medium':
        return 'medium';
      case 'low':
        return 'low';
      default:
        return 'low';
    }
  };

  const checkDuration = (task: any): string => {
    console.log("task:", task);
    return task.duration ? formatDuration(task.duration) :'No duration'
  };

  const formatDuration = (minutes: number | null | undefined): string => {
    if (!minutes) return 'No duration';
    return `${minutes} minutes`;
  };

  if (isLoading) {
    return <div className="task-loading">Loading tasks...</div>;
  }

  if (error) {
    return <div className="task-error">{error}</div>;
  }

  return (
    <div className="task-container">
      {notionTasks.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-4">No tasks found.</p>
      ) : (
        <ul className="task-list">
          {notionTasks.map((task) => (
            <li key={task.id} className="task-item py-1">
              <a 
                href={task.url || '#'} 
                target="_blank" 
                rel="noopener noreferrer"
                className="task-title-link hover:underline"
              >
                {task.title}
              </a>
              <span className="text-gray-600 dark:text-gray-400">
                {task.priority ? ` (${task.priority})` : ''}: {formatDuration(task.duration)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TaskListView; 