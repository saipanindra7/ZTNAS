import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../AppContext';
import type { User, Device, Role } from '../../types';
import { X, Trash, Pencil } from '../Icons';

// --- Reusable Modal Component ---
const Modal: React.FC<{ isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode }> = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50" aria-modal="true" role="dialog">
            <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-lg w-full max-w-lg m-4">
                <div className="flex justify-between items-center p-4 border-b border-slate-700">
                    <h3 className="text-lg font-bold text-white">{title}</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>
                <div className="p-6">{children}</div>
            </div>
        </div>
    );
};

// --- User Management ---
const UserForm: React.FC<{ onClose: () => void; userToEdit?: User }> = ({ onClose, userToEdit }) => {
    const { roles, addUser, updateUser } = useAppContext();
    const [name, setName] = useState(userToEdit?.name || '');
    const [email, setEmail] = useState(userToEdit?.email || '');
    const [role, setRole] = useState(userToEdit?.role || roles[0]?.name || '');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (userToEdit) {
            updateUser({ ...userToEdit, name, email, role });
        } else {
            addUser({ name, email, role });
        }
        onClose();
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <input type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <select value={role} onChange={e => setRole(e.target.value)} className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500">
                {roles.map(r => <option key={r.id} value={r.name}>{r.name}</option>)}
            </select>
            <div className="flex justify-end pt-2">
                 <button type="submit" className="px-5 py-2.5 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">{userToEdit ? 'Update' : 'Create'} User</button>
            </div>
        </form>
    );
};

const UsersTable: React.FC<{ users: User[] }> = ({ users }) => {
    const { deleteUser } = useAppContext();
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-400">
                <thead className="text-xs text-slate-300 uppercase bg-slate-800">
                    <tr>
                        <th scope="col" className="px-6 py-3">Name</th>
                        <th scope="col" className="px-6 py-3">Email</th>
                        <th scope="col" className="px-6 py-3">Role</th>
                        <th scope="col" className="px-6 py-3">Status</th>
                        <th scope="col" className="px-6 py-3"><span className="sr-only">Actions</span></th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(user => (
                        <tr key={user.id} className="bg-slate-900 border-b border-slate-800 hover:bg-slate-800/50">
                            <th scope="row" className="px-6 py-4 font-medium text-white whitespace-nowrap">{user.name}</th>
                            <td className="px-6 py-4">{user.email}</td>
                            <td className="px-6 py-4">{user.role}</td>
                            <td className="px-6 py-4">
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${user.needsOnboarding ? 'bg-yellow-900/50 text-yellow-300' : 'bg-green-900/50 text-green-300'}`}>
                                    {user.needsOnboarding ? 'Onboarding' : 'Active'}
                                </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                                {user.id !== 'u1' && (
                                    <button onClick={() => deleteUser(user.id)} className="text-red-500 hover:text-red-400">
                                        <Trash className="w-4 h-4" />
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};


// --- Device Management ---
const DeviceForm: React.FC<{ onClose: () => void, userList: User[] }> = ({ onClose, userList }) => {
    const { addDevice } = useAppContext();
    const [name, setName] = useState('');
    const [os, setOs] = useState<'macOS' | 'Windows' | 'Linux' | 'iOS' | 'Android'>('Windows');
    const [ownerId, setOwnerId] = useState(userList[0]?.id || '');
    
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        addDevice({ name, os, ownerId });
        onClose();
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
             <input type="text" placeholder="Device Name (e.g., ENG-MBP-01)" value={name} onChange={e => setName(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <select value={ownerId} onChange={e => setOwnerId(e.target.value)} className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500">
                {userList.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select>
            <select value={os} onChange={e => setOs(e.target.value as Device['os'])} className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500">
                <option>Windows</option>
                <option>macOS</option>
                <option>Linux</option>
                <option>iOS</option>
                <option>Android</option>
            </select>
            <div className="flex justify-end pt-2">
                 <button type="submit" className="px-5 py-2.5 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Add Device</button>
            </div>
        </form>
    );
};


const DevicesTable: React.FC<{ devices: Device[] }> = ({ devices }) => {
    const { users, deleteDevice } = useAppContext();
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-400">
                <thead className="text-xs text-slate-300 uppercase bg-slate-800">
                    <tr>
                        <th scope="col" className="px-6 py-3">Device Name</th>
                        <th scope="col" className="px-6 py-3">Owner</th>
                        <th scope="col" className="px-6 py-3">OS</th>
                        <th scope="col" className="px-6 py-3">Device Fingerprint</th>
                        <th scope="col" className="px-6 py-3">Status</th>
                        <th scope="col" className="px-6 py-3"><span className="sr-only">Actions</span></th>
                    </tr>
                </thead>
                <tbody>
                    {devices.map(device => {
                        const owner = users.find(u => u.id === device.ownerId);
                        return (
                            <tr key={device.id} className="bg-slate-900 border-b border-slate-800 hover:bg-slate-800/50">
                                <th scope="row" className="px-6 py-4 font-medium text-white whitespace-nowrap">{device.name}</th>
                                <td className="px-6 py-4">{owner?.name || 'Unknown'}</td>
                                <td className="px-6 py-4">{device.os}</td>
                                <td className="px-6 py-4 font-mono text-xs">{device.deviceFingerprint}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${device.status === 'Secured' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                                        {device.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button onClick={() => deleteDevice(device.id)} className="text-red-500 hover:text-red-400"><Trash className="w-4 h-4" /></button>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

// --- Role Management ---
const RoleForm: React.FC<{ onClose: () => void; roleToEdit?: Role }> = ({ onClose, roleToEdit }) => {
    const { addRole, updateRole } = useAppContext();
    const [name, setName] = useState(roleToEdit?.name || '');
    
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (roleToEdit) {
            updateRole({ ...roleToEdit, name });
        } else {
            addRole(name);
        }
        onClose();
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <input type="text" placeholder="Role Name" value={name} onChange={e => setName(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <div className="flex justify-end pt-2">
                 <button type="submit" className="px-5 py-2.5 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">{roleToEdit ? 'Update' : 'Create'} Role</button>
            </div>
        </form>
    );
};

const RolesTable: React.FC<{ roles: Role[]; onEdit: (role: Role) => void; onDelete: (role: Role) => void; }> = ({ roles, onEdit, onDelete }) => (
    <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-400">
            <thead className="text-xs text-slate-300 uppercase bg-slate-800">
                <tr>
                    <th scope="col" className="px-6 py-3">Role Name</th>
                    <th scope="col" className="px-6 py-3"><span className="sr-only">Actions</span></th>
                </tr>
            </thead>
            <tbody>
                {roles.map(role => (
                    <tr key={role.id} className="bg-slate-900 border-b border-slate-800 hover:bg-slate-800/50">
                        <th scope="row" className="px-6 py-4 font-medium text-white whitespace-nowrap">{role.name}</th>
                        <td className="px-6 py-4 text-right space-x-4">
                            <button onClick={() => onEdit(role)} className="text-brand-400 hover:text-brand-300"><Pencil className="w-4 h-4" /></button>
                            <button onClick={() => onDelete(role)} className="text-red-500 hover:text-red-400"><Trash className="w-4 h-4" /></button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);


// --- Main View Component ---
const UsersDevicesView: React.FC = () => {
    const { users, devices, roles, deleteRole } = useAppContext();
    const [isUserModalOpen, setUserModalOpen] = useState(false);
    const [isDeviceModalOpen, setDeviceModalOpen] = useState(false);
    const [isRoleModalOpen, setRoleModalOpen] = useState(false);
    const [roleToEdit, setRoleToEdit] = useState<Role | undefined>(undefined);
    const [deleteError, setDeleteError] = useState('');

    const handleEditRole = (role: Role) => {
        setRoleToEdit(role);
        setRoleModalOpen(true);
    };

    const handleDeleteRole = (role: Role) => {
        const isAssigned = users.some(u => u.role === role.name);
        if (isAssigned) {
            setDeleteError(`Cannot delete role "${role.name}" because it is currently assigned to one or more users.`);
        } else {
            setDeleteError('');
            deleteRole(role.id);
        }
    };
    
    useEffect(() => {
        if (deleteError) {
            const timer = setTimeout(() => setDeleteError(''), 5000);
            return () => clearTimeout(timer);
        }
    }, [deleteError]);

    return (
        <>
            <Modal isOpen={isUserModalOpen} onClose={() => setUserModalOpen(false)} title="Add New User">
                <UserForm onClose={() => setUserModalOpen(false)} />
            </Modal>
            <Modal isOpen={isDeviceModalOpen} onClose={() => setDeviceModalOpen(false)} title="Add New Device">
                <DeviceForm onClose={() => setDeviceModalOpen(false)} userList={users} />
            </Modal>
             <Modal isOpen={isRoleModalOpen} onClose={() => { setRoleModalOpen(false); setRoleToEdit(undefined); }} title={roleToEdit ? 'Edit Role' : 'Create New Role'}>
                <RoleForm onClose={() => { setRoleModalOpen(false); setRoleToEdit(undefined); }} roleToEdit={roleToEdit} />
            </Modal>
            
            <div className="space-y-8">
                {/* Users Section */}
                <div className="bg-slate-800/50 p-6 rounded-xl">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-white">Users</h2>
                        <button onClick={() => setUserModalOpen(true)} className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Add User</button>
                    </div>
                    <UsersTable users={users} />
                </div>

                {/* Devices Section */}
                <div className="bg-slate-800/50 p-6 rounded-xl">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-white">Devices</h2>
                        <button onClick={() => setDeviceModalOpen(true)} className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Add Device</button>
                    </div>
                    <DevicesTable devices={devices} />
                </div>

                {/* Roles Section */}
                <div className="bg-slate-800/50 p-6 rounded-xl">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-white">Roles</h2>
                        <button onClick={() => { setRoleToEdit(undefined); setRoleModalOpen(true); }} className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Create Role</button>
                    </div>
                    {deleteError && <p className="text-sm text-red-400 bg-red-900/50 p-3 rounded-md mb-4">{deleteError}</p>}
                    <RolesTable roles={roles} onEdit={handleEditRole} onDelete={handleDeleteRole} />
                </div>
            </div>
        </>
    );
};

export default UsersDevicesView;