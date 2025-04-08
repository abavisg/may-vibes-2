import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import apiClient from './apiClient';


// Define the shape of the user object
interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
}

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

// Define the shape of the response from the /dashboard endpoint
export interface DashboardData {
  message: string;
  plan_date: string | null;
  generated_at: string | null;
  plan: PlanItem[];
}

// Define the shape of the auth context state
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean; // To handle initial auth check
  login: () => void; // Redirects to backend login
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>; // Function to check auth status on load
  fetchDashboardData: () => Promise<DashboardData | null>; // Add fetch function
}

// Create the context with a default value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start loading

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Function to check authentication status with the backend
  const checkAuth = async () => {
    setIsLoading(true);
    try {
      // Use apiClient to handle request with credentials
      const response = await apiClient.get<User>(`${backendUrl}/user/me`);
      if (response.status === 200 && response.data) {
        setUser(response.data);
        setIsAuthenticated(true);
        console.log("User authenticated:", response.data);
      } else {
        // Handle cases where API returns OK but no data? Unlikely with current backend
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error: any) {
      // Axios throws for non-2xx status codes
      // Assume 401 means not authenticated, other errors might be server issues
      if (error.response && error.response.status === 401) {
          console.log("User not authenticated.");
      } else {
          console.error("Error checking auth status:", error);
          // Handle other errors (e.g., network error, server error)
      }
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Check authentication status when the provider mounts
  useEffect(() => {
    checkAuth();
  }, []);

  // Function to initiate login (redirect)
  const login = () => {
    // Redirect the user to the backend Google OAuth endpoint
    window.location.href = `${backendUrl}/auth/google`;
  };

  // Function to handle logout
  const logout = async () => {
    try {
      await apiClient.post(`${backendUrl}/auth/logout`);
      setUser(null);
      setIsAuthenticated(false);
      // Optionally redirect to home page or login page after logout
      // window.location.href = '/';
      console.log("Logout successful");
    } catch (error) {
      console.error("Logout failed:", error);
      // Handle logout errors if necessary
    }
  };

  // --- Fetch Dashboard Data --- 
  const fetchDashboardData = async (): Promise<DashboardData | null> => {
      if (!isAuthenticated) {
          console.log("Cannot fetch dashboard data: User not authenticated.");
          return null;
      }
      try {
          console.log("Fetching dashboard data...");
          const response = await apiClient.get<DashboardData>(`${backendUrl}/dashboard`);
          if (response.status === 200 && response.data) {
              console.log("Dashboard data fetched:", response.data);
              return response.data;
          } else {
              console.warn("Received non-200 status or no data from /dashboard");
              return null;
          }
      } catch (error: any) {
          console.error("Error fetching dashboard data:", error);
          if (error.response && error.response.status === 401) {
              // Might indicate session expired on backend, trigger re-check/logout?
              checkAuth(); // Re-check auth status
          }
          // Handle other errors (network, server internal)
          return null;
      }
  };
  // --- End Fetch Dashboard Data ---

  return (
    <AuthContext.Provider 
        value={{
             isAuthenticated, 
             user, 
             isLoading, 
             login, 
             logout, 
             checkAuth,
             fetchDashboardData // Provide the fetch function
         }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 