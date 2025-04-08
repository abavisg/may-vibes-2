import axios from 'axios';

// Determine the backend URL. Use environment variable if set, otherwise default.
// Ensure you have VITE_BACKEND_URL=http://localhost:8000 in your frontend/.env file
const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Create an axios instance
const apiClient = axios.create({
  baseURL: backendUrl, // Base URL for all requests
  withCredentials: true, // Crucial: Send cookies (like session ID) with requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add interceptors for request or response handling (e.g., refreshing tokens)
// apiClient.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     // Handle specific errors like 401 Unauthorized
//     if (error.response && error.response.status === 401) {
//       // Maybe trigger a logout or token refresh mechanism
//       console.error("API request unauthorized");
//       // Example: Call logout function from AuthContext?
//     }
//     return Promise.reject(error);
//   }
// );

export default apiClient; 