import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import UserProfile from './UserProfile';
import TimelineView from './TimelineView';
import CalendarView from './CalendarView';
import TaskListView from './TaskListView';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { isLoading: dataLoading, error } = useData();

  if (authLoading || dataLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-500">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Please log in to view your dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">🧠 Day Planner Dashboard</h1>
        <UserProfile />
      </div>
      
      <div className="dashboard-content">
        <div className="dashboard-grid">
          <div className="calendar-section">
            <h2 className="section-title">Google Calendar (Today)</h2>
            <CalendarView />
          </div>
          
          <div className="tasks-section">
            <h2 className="section-title">Notion Tasks / Meetings (Unscheduled)</h2>
            <TaskListView />
          </div>
        </div>
        
        <div className="timeline-section">
          <h2 className="section-title">📅 Proposed Daily Schedule</h2>
          <TimelineView />
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 