import React, { useState } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { useAppContext } from '../../AppContext';
import { useAuth } from '../../AuthContext';
import type { AccessLog, Application } from '../../types';
import { AlertTriangle, CheckCircle, Laptop, Users, FileLock, Activity, Code, Briefcase, Database, BookOpen } from '../Icons';

const StatCard: React.FC<{ title: string; value: string | number; icon: React.ReactNode; }> = ({ title, value, icon }) => (
  <div className="bg-slate-800/50 p-6 rounded-xl flex items-center space-x-4">
    <div className="bg-slate-900 p-3 rounded-full">{icon}</div>
    <div>
      <p className="text-slate-400 text-sm">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  </div>
);

const LogItem: React.FC<{ log: AccessLog }> = ({ log }) => {
    const { users } = useAppContext();
    const user = users.find(u => u.id === log.userId);
    const StatusIcon = log.status === 'Allowed' ? <CheckCircle className="w-5 h-5 text-green-500" /> : <AlertTriangle className="w-5 h-5 text-red-500" />;

    return (
        <div className="flex items-center justify-between p-3 hover:bg-slate-800/50 rounded-lg">
            <div className="flex items-center space-x-3">
                {StatusIcon}
                <div>
                    <p className="text-sm font-medium text-slate-100">
                        {user?.name || log.userId} requested access to <span className="font-semibold text-brand-400">{log.resource}</span>
                    </p>
                    <p className="text-xs text-slate-400">{log.location} - {log.ip}</p>
                </div>
            </div>
            <div className="text-sm text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</div>
        </div>
    );
};

const ApplicationCard: React.FC<{ app: Application; onClick: () => void; }> = ({ app, onClick }) => {
    const icons: { [key in Application['icon']]: React.ReactNode } = {
        Code: <Code className="w-8 h-8 text-brand-400" />,
        Briefcase: <Briefcase className="w-8 h-8 text-brand-400" />,
        Database: <Database className="w-8 h-8 text-brand-400" />,
        BookOpen: <BookOpen className="w-8 h-8 text-brand-400" />,
    };

    return (
        <button onClick={onClick} className="bg-slate-900/50 p-4 rounded-lg flex items-center space-x-4 border border-slate-700 hover:border-brand-500 transition-colors w-full text-left">
            {icons[app.icon]}
            <div>
                <p className="font-bold text-white">{app.name}</p>
                <p className="text-xs text-slate-400">{app.description}</p>
            </div>
        </button>
    );
};

const UserDashboardView: React.FC = () => {
    const { currentUser } = useAuth();
    const { accessLogs, devices, policies, applications, logApplicationAccess } = useAppContext();
    const [lastAccessed, setLastAccessed] = useState<string | null>(null);


    if (!currentUser) return null;

    const userLogs = accessLogs.filter(log => log.userId === currentUser.id).slice(0, 5);
    const userDevices = devices.filter(d => d.ownerId === currentUser.id);
    const userPolicies = policies.filter(p => p.subjects.includes(currentUser.role) || p.subjects.includes('All Users'));
    const userApps = applications.filter(app => app.allowedRoles.includes(currentUser.role));

    const handleAppClick = (appName: string) => {
        logApplicationAccess(currentUser.id, appName);
        setLastAccessed(appName);
        setTimeout(() => setLastAccessed(null), 3000);
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <StatCard title="My Devices" value={userDevices.length} icon={<Laptop className="w-6 h-6 text-brand-400" />} />
                <StatCard title="Applicable Policies" value={userPolicies.length} icon={<FileLock className="w-6 h-6 text-sky-400" />} />
                <StatCard title="My Recent Activity" value={userLogs.length} icon={<Activity className="w-6 h-6 text-amber-400" />} />
            </div>

            <div className="bg-slate-800/50 p-6 rounded-xl">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-white">My Applications</h2>
                     {lastAccessed && (
                        <div className="bg-green-900/50 text-green-300 text-xs font-medium px-3 py-1 rounded-full animate-pulse">
                            Accessed {lastAccessed}!
                        </div>
                    )}
                </div>
                {userApps.length > 0 ? (
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {userApps.map(app => <ApplicationCard key={app.id} app={app} onClick={() => handleAppClick(app.name)} />)}
                    </div>
                ) : (
                    <p className="text-slate-400">You do not have access to any applications.</p>
                )}
            </div>

            <div className="bg-slate-800/50 p-6 rounded-xl">
                <h2 className="text-xl font-bold text-white mb-4">My Activity</h2>
                <div className="space-y-2">
                    {userLogs.length > 0 ? userLogs.map(log => <LogItem key={log.id} log={log} />) : <p className="text-slate-400">No recent activity found.</p>}
                </div>
            </div>
        </div>
    );
};

const AdminDashboardView: React.FC = () => {
  const { accessLogs, users, devices, policies } = useAppContext();

  const riskData = accessLogs.reduce((acc, log) => {
    const level = log.riskLevel;
    const existing = acc.find(item => item.name === level);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name: level, value: 1 });
    }
    return acc;
  }, [] as { name: 'Low' | 'Medium' | 'High'; value: number; }[]);

  const COLORS: { [key: string]: string } = {
    Low: '#10b981', // green-500
    Medium: '#f59e0b', // amber-500
    High: '#ef4444', // red-500
  };

  const recentLogs = accessLogs.slice(0, 5);
  const securedDevices = devices.filter(d => d.status === 'Secured').length;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            <StatCard title="Active Users" value={users.length} icon={<Users className="w-6 h-6 text-brand-400" />} />
            <StatCard title="Secured Devices" value={`${securedDevices} / ${devices.length}`} icon={<Laptop className="w-6 h-6 text-green-400" />} />
            <StatCard title="Security Policies" value={policies.length} icon={<CheckCircle className="w-6 h-6 text-sky-400" />} />
        </div>
        <div className="bg-slate-800/50 p-6 rounded-xl">
            <h2 className="text-xl font-bold text-white mb-4">Recent Activity</h2>
            <div className="space-y-2">
                {recentLogs.map(log => <LogItem key={log.id} log={log} />)}
            </div>
        </div>
      </div>
      <div className="bg-slate-800/50 p-6 rounded-xl flex flex-col">
        <h2 className="text-xl font-bold text-white mb-4">Risk Assessment</h2>
        <div className="flex-1 flex items-center justify-center">
             <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                    <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                        {riskData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                        ))}
                    </Pie>
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        </div>
        <div className="mt-4 text-center">
            <p className="text-slate-300">
                <span className="font-bold text-red-500">{riskData.find(d => d.name === 'High')?.value || 0}</span> high-risk events detected in the last 24h.
            </p>
            <button className="mt-2 text-sm text-brand-400 hover:text-brand-300">View All Alerts</button>
        </div>
      </div>
    </div>
  );
};

const DashboardOverview: React.FC = () => {
    const { currentUser } = useAuth();
    if (!currentUser) {
        return null; // Or a loading spinner
    }

    return currentUser.role === 'Admin' ? <AdminDashboardView /> : <UserDashboardView />;
};

export default DashboardOverview;