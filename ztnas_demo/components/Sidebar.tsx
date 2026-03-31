
import React from 'react';
import type { View } from '../types';
import { Shield, Users, FileLock, ListChecks } from './Icons';
import { useAuth } from '../AuthContext';
import { VIEW_PERMISSIONS } from '../constants';

interface SidebarProps {
  currentView: View;
  setCurrentView: (view: View) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView }) => {
  const { currentUser } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <Shield className="w-5 h-5" /> },
    { id: 'users-devices', label: 'Users & Devices', icon: <Users className="w-5 h-5" /> },
    { id: 'policies', label: 'Access Policies', icon: <FileLock className="w-5 h-5" /> },
    { id: 'logs', label: 'Audit Logs', icon: <ListChecks className="w-5 h-5" /> },
  ] as const;

  const allowedViews = (currentUser && VIEW_PERMISSIONS[currentUser.role]) || [];
  const visibleNavItems = navItems.filter(item => allowedViews.includes(item.id));

  return (
    <aside className="w-64 flex-shrink-0 bg-slate-950 p-4 flex flex-col">
      <div className="flex items-center space-x-2 mb-10">
        <Shield className="w-8 h-8 text-brand-400" />
        <h1 className="text-xl font-bold text-slate-100">ZTNAS</h1>
      </div>
      <nav className="flex-1">
        <ul>
          {visibleNavItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setCurrentView(item.id)}
                className={`w-full text-left flex items-center space-x-3 p-3 rounded-lg transition-colors duration-200 ${
                  currentView === item.id
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                {item.icon}
                <span className="font-medium">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="mt-auto text-center text-xs text-slate-500">
        <p>ZTNAS v1.0.0</p>
        <p>&copy; 2024 SecureCorp</p>
      </div>
    </aside>
  );
};

export default Sidebar;