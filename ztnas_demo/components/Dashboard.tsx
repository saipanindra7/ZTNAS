import React from 'react';
import type { View } from '../types';
import DashboardOverview from './views/DashboardOverview';
import UsersDevicesView from './views/UsersDevicesView';
import PoliciesView from './views/PoliciesView';
import LogsView from './views/LogsView';
import ProfileView from './views/ProfileView';
import Header from './Header';
import { useAuth } from '../AuthContext';
import { VIEW_PERMISSIONS } from '../constants';
import { AlertTriangle } from './Icons';

interface DashboardProps {
  currentView: View;
  setCurrentView: (view: View) => void;
}

const AccessDenied: React.FC = () => (
    <div className="bg-slate-800/50 p-8 rounded-xl text-center flex flex-col items-center">
        <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-red-400">Access Denied</h2>
        <p className="mt-2 text-slate-300">You do not have permission to view this page.</p>
    </div>
);


const Dashboard: React.FC<DashboardProps> = ({ currentView, setCurrentView }) => {
  const { currentUser } = useAuth();
  
  const renderView = () => {
    const allowedViews = (currentUser && VIEW_PERMISSIONS[currentUser.role]) || [];
    if (!allowedViews.includes(currentView)) {
        return <AccessDenied />;
    }

    switch (currentView) {
      case 'dashboard':
        return <DashboardOverview />;
      case 'users-devices':
        return <UsersDevicesView />;
      case 'policies':
        return <PoliciesView />;
      case 'logs':
        return <LogsView />;
      case 'profile':
        return <ProfileView />;
      default:
        return <DashboardOverview />;
    }
  };

  const getTitle = () => {
    switch (currentView) {
      case 'dashboard': return 'Dashboard Overview';
      case 'users-devices': return 'Users & Devices Management';
      case 'policies': return 'Access Control Policies';
      case 'logs': return 'System Audit Logs';
      case 'profile': return 'User Profile';
      default: return 'Dashboard';
    }
  };


  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <Header title={getTitle()} setCurrentView={setCurrentView} />
      <div className="mt-6">
        {renderView()}
      </div>
    </div>
  );
};

export default Dashboard;