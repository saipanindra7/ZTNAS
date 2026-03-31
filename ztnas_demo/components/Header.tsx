import React, { useState, useEffect, useRef } from 'react';
import { Bell, UserCircle, LogOut, Settings, AlertTriangle, CheckCircle } from './Icons';
import type { View, AccessLog } from '../types';
import { useAuth } from '../AuthContext';
import { useAppContext } from '../AppContext';

const LogNotificationItem: React.FC<{ log: AccessLog }> = ({ log }) => {
    const { users } = useAppContext();
    const user = users.find(u => u.id === log.userId);
    const StatusIcon = log.status === 'Allowed' ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" /> : <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />;

    return (
        <div className="flex items-start space-x-3 p-3 hover:bg-slate-700/50 rounded-lg cursor-pointer">
            {StatusIcon}
            <div className="flex-1">
                <p className="text-sm text-slate-200">
                    <span className="font-semibold">{user?.name || log.userId}</span> requested access to <span className="font-semibold text-brand-400">{log.resource}</span>
                </p>
                <p className="text-xs text-slate-400">{log.location} - {new Date(log.timestamp).toLocaleTimeString()}</p>
            </div>
        </div>
    );
};

interface HeaderProps {
    title: string;
    setCurrentView: (view: View) => void;
}

const Header: React.FC<HeaderProps> = ({ title, setCurrentView }) => {
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [isNotificationsOpen, setNotificationsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const { currentUser, logout } = useAuth();
  const { accessLogs } = useAppContext();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    logout();
  };

  const navigateToProfile = () => {
    setCurrentView('profile');
    setDropdownOpen(false);
  }

  return (
    <header className="flex justify-between items-center">
      <h1 className="text-2xl md:text-3xl font-bold text-slate-100">{title}</h1>
      <div className="flex items-center space-x-4">
        <div className="relative" ref={notificationsRef}>
            <button onClick={() => setNotificationsOpen(prev => !prev)} className="relative text-slate-400 hover:text-white transition-colors">
            <Bell className="w-6 h-6" />
            {accessLogs.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
            )}
            </button>
            {isNotificationsOpen && (
                 <div className="absolute right-0 mt-2 w-80 bg-slate-800 border border-slate-700 rounded-md shadow-lg z-10">
                    <div className="p-3 border-b border-slate-700">
                        <h4 className="font-semibold text-white">Recent Activity</h4>
                    </div>
                    <div className="py-1 max-h-96 overflow-y-auto">
                        {accessLogs.length > 0 ? (
                            accessLogs.slice(0, 5).map(log => <LogNotificationItem key={log.id} log={log} />)
                        ) : (
                            <p className="text-center text-slate-400 py-4 text-sm">No recent activity.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
        <div className="relative" ref={dropdownRef}>
            <button onClick={() => setDropdownOpen(prev => !prev)} className="flex items-center space-x-2 p-1 rounded-md hover:bg-slate-800 transition-colors">
                <UserCircle className="w-8 h-8 text-slate-400" />
                {currentUser && (
                    <div className="hidden md:block text-left">
                        <p className="text-sm font-semibold text-white">{currentUser.name}</p>
                        <p className="text-xs text-slate-400">{currentUser.role}</p>
                    </div>
                )}
            </button>
            {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-md shadow-lg z-10">
                    <div className="py-1">
                         <button onClick={navigateToProfile} className="w-full text-left flex items-center px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition-colors">
                           <Settings className="w-4 h-4 mr-3" />
                           My Profile
                        </button>
                        <button onClick={handleLogout} className="w-full text-left flex items-center px-4 py-2 text-sm text-red-400 hover:bg-slate-700 hover:text-white transition-colors">
                           <LogOut className="w-4 h-4 mr-3" />
                           Log Out
                        </button>
                    </div>
                </div>
            )}
        </div>
      </div>
    </header>
  );
};

export default Header;