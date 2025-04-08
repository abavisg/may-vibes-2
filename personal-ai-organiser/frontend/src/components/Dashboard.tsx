import React from 'react';
import CalendarView from './CalendarView';
import TaskListView from './TaskListView';
import TimelineView from './TimelineView';
import { useAuth } from '../context/AuthContext';
import LoginButton from './LoginButton';
import UserProfile from './UserProfile';

const Dashboard: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  console.log("Dashboard State:", { isLoading, isAuthenticated, user });
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">AI Day Planner Dashboard</h1>
      {/* TODO: Add Google OAuth Login/Logout Button */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Today's Calendar</h2>
          <CalendarView />
        </div>
        <div className="md:col-span-1 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Notion Tasks</h2>
          <TaskListView />
        </div>
        <div className="md:col-span-1 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Daily Timeline</h2>
          <TimelineView />
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 