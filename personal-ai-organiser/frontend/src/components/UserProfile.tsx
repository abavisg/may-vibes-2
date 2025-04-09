import React from 'react';
import { useAuth } from '../context/AuthContext';
import LoginButton from './LoginButton';

const UserProfile: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) {
    return <LoginButton />;
  }

  return (
    <div className="sticky top-4 right-4 z-50 flex items-center justify-end space-x-2 bg-white dark:bg-gray-800 rounded-lg shadow-md p-2 ml-auto">
      {user.picture && (
        <img 
          src={user.picture} 
          alt={user.name || 'User'} 
          className="w-8 h-8 rounded-full"
        />
      )}
      <div className="text-right">
        <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate max-w-[120px]">
          {user.name || 'User'}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[120px]">
          {user.email}
        </p>
      </div>
      <button
        onClick={logout}
        className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded transition-colors"
      >
        Logout
      </button>
    </div>
  );
};

export default UserProfile; 