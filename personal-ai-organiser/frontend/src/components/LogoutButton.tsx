import React from 'react';
import { useAuth } from '../context/AuthContext';

const LogoutButton: React.FC = () => {
  const { logout } = useAuth();

  return (
    <button
      onClick={logout}
      className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
    >
      Logout
    </button>
  );
};

export default LogoutButton; 