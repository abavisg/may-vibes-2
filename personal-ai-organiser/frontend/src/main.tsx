import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { AuthProvider } from './context/AuthContext.tsx' // Import the AuthProvider

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider> {/* Wrap App with AuthProvider */} 
      <App />
    </AuthProvider>
  </React.StrictMode>,
)
