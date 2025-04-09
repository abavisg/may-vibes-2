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
    console.log("minutes:", minutes);
    if (!minutes) return 'No duration';
    
    return `${minutes}m`;
  };

  if (isLoading) {
    return <div className="task-loading">Loading tasks...</div>;
  }

  if (error) {
    return <div className="task-error">{error}</div>;
  }

  return (
    <div className="task-container">
      <h2 className="text-xl font-semibold mb-4">Tasks</h2>
      {notionTasks.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-4">No tasks found.</p>
      ) : (
        <ul className="task-list">
          {notionTasks.map((task) => (
            <li key={task.id} className="task-item">
              <div className="task-item-content">
                <div className="flex items-center justify-between">
                  <a 
                    href={task.url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="task-title-link"
                  >
                    {task.title}
                  </a>
                  <div className="flex items-center space-x-2">
                    <span className={`item-priority priority-${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {
                        checkDuration(task)
                      }
                    </span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TaskListView; 