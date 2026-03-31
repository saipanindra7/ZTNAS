import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider, useAuth } from './AuthContext';
import { AppProvider } from './AppContext';
import LoginView from './components/LoginView';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const AuthWrapper = () => {
    const { isAuthenticated, currentUser } = useAuth();
    
    if (isAuthenticated && currentUser) {
        return <App />;
    }
    return <LoginView />;
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <AppProvider>
      <AuthProvider>
        <AuthWrapper />
      </AuthProvider>
    </AppProvider>
  </React.StrictMode>
);
