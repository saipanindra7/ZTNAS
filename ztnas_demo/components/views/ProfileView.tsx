import React from 'react';
import { useAppContext } from '../../AppContext';
import { useAuth } from '../../AuthContext';
import { UserCircle } from '../Icons';
import type { Device, MfaMethod } from '../../types';

const getStatusBadge = (status: 'Secured' | 'Vulnerable') => {
    return status === 'Secured'
        ? <span className="px-2 py-1 text-xs font-medium text-green-300 bg-green-900/50 rounded-full">Secured</span>
        : <span className="px-2 py-1 text-xs font-medium text-red-300 bg-red-900/50 rounded-full">Vulnerable</span>;
};

const DevicesTable: React.FC<{ devices: Device[] }> = ({ devices }) => (
    <div className="overflow-x-auto mt-4">
        <table className="w-full text-sm text-left text-slate-400">
            <thead className="text-xs text-slate-300 uppercase bg-slate-800">
                <tr>
                    <th scope="col" className="px-6 py-3">Device Name</th>
                    <th scope="col" className="px-6 py-3">Operating System</th>
                    <th scope="col" className="px-6 py-3">Status</th>
                </tr>
            </thead>
            <tbody>
                {devices.map(device => (
                    <tr key={device.id} className="bg-slate-900 border-b border-slate-800 hover:bg-slate-800/50">
                        <th scope="row" className="px-6 py-4 font-medium text-white whitespace-nowrap">{device.name}</th>
                        <td className="px-6 py-4">{device.os}</td>
                        <td className="px-6 py-4">{getStatusBadge(device.status)}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

const getMfaMethodName = (method: MfaMethod) => {
    switch (method) {
        // Fix: Removed 'totp' case as it is not a valid MfaMethod type.
        case 'securityKey': return 'Security Key';
        case 'picture': return 'Picture Password';
        default: return 'Not Enabled';
    }
}


const ProfileView: React.FC = () => {
    const { devices } = useAppContext();
    const { currentUser } = useAuth();
    
    const userDevices = devices.filter(d => d.ownerId === currentUser?.id);

    if (!currentUser) {
        return (
            <div className="bg-slate-800/50 p-6 rounded-xl text-center">
                <p className="text-slate-300">User not found. Please log in again.</p>
            </div>
        );
    }

    const mfaStatus = getMfaMethodName(currentUser.mfaMethod);

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
                 <div className="bg-slate-800/50 p-6 rounded-xl text-center">
                    <UserCircle className="w-24 h-24 mx-auto text-slate-500" />
                    <h2 className="mt-4 text-2xl font-bold text-white">{currentUser.name}</h2>
                    <p className="text-brand-400">{currentUser.role}</p>
                    <p className="mt-2 text-slate-400">{currentUser.email}</p>
                    <p className={`mt-2 text-sm ${currentUser.mfaMethod === 'none' ? 'text-amber-400' : 'text-green-400'}`}>MFA: {mfaStatus}</p>
                    <div className="mt-6 flex flex-col sm:flex-row md:flex-col gap-3">
                         <button className="w-full px-4 py-2 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Edit Profile</button>
                         <button className="w-full px-4 py-2 text-sm font-semibold text-white bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">Change Password</button>
                    </div>
                 </div>
            </div>
            <div className="md:col-span-2">
                 <div className="bg-slate-800/50 p-6 rounded-xl">
                     <h3 className="text-xl font-bold text-white mb-4">Registered Devices</h3>
                     {userDevices.length > 0 ? (
                        <DevicesTable devices={userDevices} />
                     ) : (
                        <p className="text-slate-400">No devices registered for this user.</p>
                     )}
                 </div>
            </div>
        </div>
    );
};

export default ProfileView;