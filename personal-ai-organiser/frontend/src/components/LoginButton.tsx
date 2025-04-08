import React from 'react';
import { useAuth } from '../context/AuthContext';

const LoginButton: React.FC = () => {
  const { login } = useAuth();

  return (
    <button
      onClick={login}
      className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
    >
      Login with Google
    </button>
  );
};

export default LoginButton; 