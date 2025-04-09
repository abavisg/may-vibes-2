import React, { createContext, useState, useContext, ReactNode, useEffect, useRef } from 'react';
import apiClient from './apiClient';

// Define the shape of the user object
export interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
}

// Define the shape of the auth context state
export interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  user: User | null;
  login: () => void;
  logout: () => void;
  refreshUserData: () => Promise<void>;
}

// Cache configuration
const CACHE_KEY = 'user_data_cache';
const CACHE_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes in milliseconds

// Create the context with a default value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  
  // Use a ref to track if we've already logged the API call in this session
  const hasLoggedApiCall = useRef<boolean>(false);

  // Function to get cached user data
  const getCachedUserData = (): { user: User | null, timestamp: number } | null => {
    try {
      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        return JSON.parse(cachedData);
      }
    } catch (err) {
      console.error("Error reading from cache:", err);
    }
    return null;
  };

  // Function to set cached user data
  const setCachedUserData = (userData: User | null) => {
    try {
      if (userData) {
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          user: userData,
          timestamp: Date.now()
        }));
      } else {
        localStorage.removeItem(CACHE_KEY);
      }
    } catch (err) {
      console.error("Error writing to cache:", err);
    }
  };

  // Function to check if cache is valid
  const isCacheValid = (): boolean => {
    const cachedData = getCachedUserData();
    if (!cachedData) return false;
    
    const now = Date.now();
    return (now - cachedData.timestamp) < CACHE_EXPIRY_MS;
  };

  // Function to fetch user data from API
  const fetchUserData = async (): Promise<User | null> => {
    try {
      const response = await apiClient.get<User>('/user/me');
      if (response.status === 200 && response.data) {
        // Only log once per session to avoid duplicate logs in StrictMode
        if (!hasLoggedApiCall.current) {
          console.log("User data fetched from API:", response.data);
          hasLoggedApiCall.current = true;
        }
        return response.data;
      }
    } catch (err) {
      console.error("Failed to fetch user data:", err);
    }
    return null;
  };

  // Function to refresh user data
  const refreshUserData = async (): Promise<void> => {
    setIsLoading(true);
    try {
      // Reset the logging flag when manually refreshing
      hasLoggedApiCall.current = false;
      const userData = await fetchUserData();
      if (userData) {
        setIsAuthenticated(true);
        setUser(userData);
        setCachedUserData(userData);
      } else {
        setIsAuthenticated(false);
        setUser(null);
        setCachedUserData(null);
      }
    } catch (err) {
      console.error("Error refreshing user data:", err);
      setError("Failed to refresh user data");
    } finally {
      setIsLoading(false);
    }
  };

  // Check authentication status when the component mounts
  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      try {
        // Check if we have valid cached data
        if (isCacheValid()) {
          const cachedData = getCachedUserData();
          if (cachedData && cachedData.user) {
            // Only log once per session to avoid duplicate logs in StrictMode
            if (!hasLoggedApiCall.current) {
              console.log("Using cached user data:", cachedData.user);
              hasLoggedApiCall.current = true;
            }
            setIsAuthenticated(true);
            setUser(cachedData.user);
            setIsLoading(false);
            return;
          }
        }

        // If no valid cache, fetch from API
        const userData = await fetchUserData();
        if (userData) {
          setIsAuthenticated(true);
          setUser(userData);
          setCachedUserData(userData);
        } else {
          setIsAuthenticated(false);
          setUser(null);
          setCachedUserData(null);
        }
      } catch (err) {
        console.error("Auth check failed:", err);
        setIsAuthenticated(false);
        setUser(null);
        setCachedUserData(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Function to initiate login
  const login = () => {
    window.location.href = '/auth/google';
  };

  // Function to logout
  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
      setIsAuthenticated(false);
      setUser(null);
      setCachedUserData(null); // Clear cache on logout
      // Reset the logging flag on logout
      hasLoggedApiCall.current = false;
    } catch (err) {
      console.error("Logout failed:", err);
      setError("Failed to logout. Please try again.");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        error,
        user,
        login,
        logout,
        refreshUserData
      }}
    >
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