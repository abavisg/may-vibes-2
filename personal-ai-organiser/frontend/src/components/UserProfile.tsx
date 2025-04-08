import React from 'react';
import { useAuth } from '../context/AuthContext';
import LogoutButton from './LogoutButton';

const UserProfile: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return null; // Or a loading indicator/placeholder
  }

  return (
    <div className="flex items-center space-x-4 p-2 bg-gray-200 dark:bg-gray-700 rounded-lg">
      {user.picture && (
        <img 
          src={user.picture} 
          alt={user.name || 'User avatar'} 
          className="w-10 h-10 rounded-full"
        />
      )}
      <div className="text-sm">
        <div className="font-medium text-gray-900 dark:text-white">{user.name || 'User'}</div>
        <div className="text-gray-600 dark:text-gray-400">{user.email}</div>
      </div>
      <LogoutButton />
    </div>
  );
};

export default UserProfile; 