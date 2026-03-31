import React, { useState, useMemo } from 'react';
import { useAppContext } from '../../AppContext';

const getStatusBadge = (status: 'Allowed' | 'Denied') => {
    return status === 'Allowed'
        ? <span className="flex items-center text-xs font-medium text-green-400"><span className="w-2 h-2 mr-2 rounded-full bg-green-500"></span>Allowed</span>
        : <span className="flex items-center text-xs font-medium text-red-400"><span className="w-2 h-2 mr-2 rounded-full bg-red-500"></span>Denied</span>;
};

const getRiskBadge = (risk: 'Low' | 'Medium' | 'High') => {
    switch (risk) {
        case 'Low':
            return <span className="px-2 py-1 text-xs font-medium text-green-300 bg-green-900/50 rounded-full">Low</span>;
        case 'Medium':
            return <span className="px-2 py-1 text-xs font-medium text-amber-300 bg-amber-900/50 rounded-full">Medium</span>;
        case 'High':
            return <span className="px-2 py-1 text-xs font-medium text-red-300 bg-red-900/50 rounded-full">High</span>;
    }
};

const LogsView: React.FC = () => {
    const [filter, setFilter] = useState('');
    const { accessLogs, users, devices } = useAppContext();

    const filteredLogs = useMemo(() => {
        if (!filter) return accessLogs;
        const lowercasedFilter = filter.toLowerCase();
        return accessLogs.filter(log => {
            const user = users.find(u => u.id === log.userId);
            const device = devices.find(d => d.id === log.deviceId);
            return (
                user?.name.toLowerCase().includes(lowercasedFilter) ||
                device?.name.toLowerCase().includes(lowercasedFilter) ||
                log.resource.toLowerCase().includes(lowercasedFilter) ||
                log.ip.includes(lowercasedFilter) ||
                log.location.toLowerCase().includes(lowercasedFilter)
            );
        });
    }, [filter, accessLogs, users, devices]);

    return (
        <div className="bg-slate-800/50 p-6 rounded-xl">
             <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-white">System Audit Logs</h2>
                <input
                    type="text"
                    placeholder="Search logs..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="bg-slate-900 border border-slate-700 text-white placeholder-slate-400 text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block w-full md:w-1/3 p-2.5"
                />
            </div>
             <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-400">
                    <thead className="text-xs text-slate-300 uppercase bg-slate-800">
                        <tr>
                            <th scope="col" className="px-6 py-3">Timestamp</th>
                            <th scope="col" className="px-6 py-3">User</th>
                            <th scope="col" className="px-6 py-3">Device</th>
                            <th scope="col" className="px-6 py-3">Resource</th>
                            <th scope="col" className="px-6 py-3">Location</th>
                            <th scope="col" className="px-6 py-3">Status</th>
                            <th scope="col" className="px-6 py-3">Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredLogs.map(log => {
                            const user = users.find(u => u.id === log.userId);
                            const device = devices.find(d => d.id === log.deviceId);
                            return (
                                <tr key={log.id} className="bg-slate-900 border-b border-slate-800 hover:bg-slate-800/50">
                                    <td className="px-6 py-4">{log.timestamp.toLocaleString()}</td>
                                    <td className="px-6 py-4 font-medium text-white">{user?.name || log.userId}</td>
                                    <td className="px-6 py-4">{device?.name || log.deviceId}</td>
                                    <td className="px-6 py-4">{log.resource}</td>
                                    <td className="px-6 py-4">{log.location}</td>
                                    <td className="px-6 py-4">{getStatusBadge(log.status)}</td>
                                    <td className="px-6 py-4">{getRiskBadge(log.riskLevel)}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
             {filteredLogs.length === 0 && (
                <div className="text-center py-10">
                    <p className="text-slate-400">No logs found matching your search.</p>
                </div>
            )}
        </div>
    );
};

export default LogsView;