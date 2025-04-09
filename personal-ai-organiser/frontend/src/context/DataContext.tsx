import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { useAuth } from './AuthContext';
import apiClient from './apiClient';

// Define the structure of items within the plan array
export interface PlanItem {
  type: 'event' | 'task';
  start: string | null; // ISO datetime string
  end: string | null;   // ISO datetime string
  summary?: string; // For events
  title?: string;   // For tasks
  id: string; // Event or Task ID
  // Add other potential fields from your plan data (priority, estimate, etc.)
  priority?: string | null;
  estimate_hours?: number | null;
  deadline?: string | null; // ISO date string
  url?: string | null; // e.g., Notion URL
  [key: string]: any; // Allow other properties
}

// Define the shape of the data context state
interface DataContextType {
  calendarEvents: PlanItem[];
  notionTasks: PlanItem[];
  isLoading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

// Cache configuration
const CALENDAR_CACHE_KEY = 'calendar_events_cache';
const NOTION_CACHE_KEY = 'notion_tasks_cache';
const CACHE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes in milliseconds

// Create the context with a default value
const DataContext = createContext<DataContextType | undefined>(undefined);

// Create the provider component
interface DataProviderProps {
  children: ReactNode;
}

export const DataProvider: React.FC<DataProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [calendarEvents, setCalendarEvents] = useState<PlanItem[]>([]);
  const [notionTasks, setNotionTasks] = useState<PlanItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Function to get cached data
  const getCachedData = <T,>(cacheKey: string): { data: T | null, timestamp: number } | null => {
    try {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        return JSON.parse(cachedData);
      }
    } catch (err) {
      console.error(`Error reading from cache (${cacheKey}):`, err);
    }
    return null;
  };

  // Function to set cached data
  const setCachedData = <T,>(cacheKey: string, data: T | null) => {
    try {
      if (data) {
        localStorage.setItem(cacheKey, JSON.stringify({
          data,
          timestamp: Date.now()
        }));
      } else {
        localStorage.removeItem(cacheKey);
      }
    } catch (err) {
      console.error(`Error writing to cache (${cacheKey}):`, err);
    }
  };

  // Function to check if cache is valid
  const isCacheValid = (cacheKey: string): boolean => {
    const cachedData = getCachedData(cacheKey);
    if (!cachedData) return false;
    
    const now = Date.now();
    return (now - cachedData.timestamp) < CACHE_EXPIRY_MS;
  };

  // Function to fetch calendar events
  const fetchCalendarEvents = async (): Promise<PlanItem[]> => {
    try {
      const response = await apiClient.get('/calendar/events');
      if (response.data?.events) {
        console.log(`Loaded ${response.data.events.length} calendar events from API`);
        return response.data.events;
      }
    } catch (err) {
      console.error("Failed to fetch calendar events:", err);
    }
    return [];
  };

  // Function to fetch Notion tasks
  const fetchNotionTasks = async (): Promise<PlanItem[]> => {
    try {
      const response = await apiClient.get('/notion/tasks');
      if (response.data?.tasks) {
        console.log(`Loaded ${response.data.tasks.length} Notion tasks from API`);
        return response.data.tasks;
      }
    } catch (err) {
      console.error("Failed to fetch Notion tasks:", err);
    }
    return [];
  };

  // Function to fetch data from both endpoints
  const fetchData = async (forceRefresh = false) => {
    if (!isAuthenticated) {
      setCalendarEvents([]);
      setNotionTasks([]);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      let events: PlanItem[] = [];
      let tasks: PlanItem[] = [];

      // Check if we have valid cached data for calendar events
      if (!forceRefresh && isCacheValid(CALENDAR_CACHE_KEY)) {
        const cachedData = getCachedData<PlanItem[]>(CALENDAR_CACHE_KEY);
        if (cachedData && cachedData.data) {
          console.log(`Using cached calendar events: ${cachedData.data.length} events`);
          events = cachedData.data;
        }
      } else {
        // If no valid cache or force refresh, fetch from API
        events = await fetchCalendarEvents();
        setCachedData(CALENDAR_CACHE_KEY, events);
      }

      // Check if we have valid cached data for Notion tasks
      if (!forceRefresh && isCacheValid(NOTION_CACHE_KEY)) {
        const cachedData = getCachedData<PlanItem[]>(NOTION_CACHE_KEY);
        if (cachedData && cachedData.data) {
          console.log(`Using cached Notion tasks: ${cachedData.data.length} tasks`);
          tasks = cachedData.data;
        }
      } else {
        // If no valid cache or force refresh, fetch from API
        tasks = await fetchNotionTasks();
        setCachedData(NOTION_CACHE_KEY, tasks);
      }

      console.log(`Total: ${events.length} calendar events and ${tasks.length} Notion tasks`);
      
      setCalendarEvents(events);
      setNotionTasks(tasks);
    } catch (err) {
      console.error("Failed to load data:", err);
      setError("Failed to load data from the server.");
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch data when authentication state changes
  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    } else {
      // Clear data when not authenticated
      setCalendarEvents([]);
      setNotionTasks([]);
      // Clear cache
      setCachedData(CALENDAR_CACHE_KEY, null);
      setCachedData(NOTION_CACHE_KEY, null);
    }
  }, [isAuthenticated]);

  // Function to manually refresh data
  const refreshData = async () => {
    await fetchData(true); // Force refresh from API
  };

  return (
    <DataContext.Provider 
      value={{
        calendarEvents,
        notionTasks,
        isLoading,
        error,
        refreshData
      }}>
      {children}
    </DataContext.Provider>
  );
};

// Custom hook to use the data context
export const useData = (): DataContextType => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}; 