import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { AuthProvider } from './context/AuthContext.tsx' // Import the AuthProvider
import { DataProvider } from './context/DataContext.tsx' // Import the DataProvider

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider> {/* Wrap App with AuthProvider */} 
      <DataProvider> {/* Wrap App with DataProvider */}
        <App />
      </DataProvider>
    </AuthProvider>
  </React.StrictMode>,
)
