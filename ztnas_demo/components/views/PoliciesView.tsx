import React, {useState} from 'react';
import { useAppContext } from '../../AppContext';
import type { Policy } from '../../types';
import { X } from '../Icons';


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

// --- Form Component ---
const PolicyForm: React.FC<{ onClose: () => void }> = ({ onClose }) => {
    const { addPolicy } = useAppContext();
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [subjects, setSubjects] = useState('');
    const [resources, setResources] = useState('');
    const [conditions, setConditions] = useState('');
    const [action, setAction] = useState<'Allow' | 'Deny'>('Allow');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (name && description && subjects && resources && conditions) {
            addPolicy({ 
                name, 
                description, 
                subjects: subjects.split(',').map(s => s.trim()), 
                resources: resources.split(',').map(r => r.trim()),
                conditions: conditions.split(',').map(c => c.trim()),
                action 
            });
            onClose();
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <input type="text" placeholder="Policy Name" value={name} onChange={e => setName(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <textarea placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500 h-24" />
            <input type="text" placeholder="Subjects (comma-separated, e.g., Engineer, Sales)" value={subjects} onChange={e => setSubjects(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <input type="text" placeholder="Resources (comma-separated, e.g., AWS Console)" value={resources} onChange={e => setResources(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <input type="text" placeholder="Conditions (comma-separated, e.g., Compliant Device)" value={conditions} onChange={e => setConditions(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
            <select value={action} onChange={e => setAction(e.target.value as Policy['action'])} className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500">
                <option>Allow</option>
                <option>Deny</option>
            </select>
            <div className="flex justify-end pt-2">
                 <button type="submit" className="px-5 py-2.5 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Create Policy</button>
            </div>
        </form>
    );
};


const ToggleSwitch: React.FC<{ enabled: boolean; onChange: () => void }> = ({ enabled, onChange }) => (
    <button onClick={onChange} className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${enabled ? 'bg-brand-600' : 'bg-slate-600'}`}>
        <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${enabled ? 'translate-x-6' : 'translate-x-1'}`} />
    </button>
);


const PolicyCard: React.FC<{ policy: Policy }> = ({ policy }) => {
    const { togglePolicyEnabled } = useAppContext();
    return (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-brand-500 transition-all duration-300 flex flex-col">
            <div className="flex justify-between items-start">
                <h3 className="text-lg font-bold text-white pr-4">{policy.name}</h3>
                <span className={`flex-shrink-0 px-3 py-1 text-sm font-semibold rounded-full ${policy.action === 'Allow' ? 'bg-blue-500/20 text-blue-300' : 'bg-red-500/20 text-red-300'}`}>
                    {policy.action}
                </span>
            </div>
            <p className="mt-3 text-sm text-slate-400 flex-grow">{policy.description}</p>
            <div className="mt-4 space-y-2 text-sm">
                <div>
                    <span className="font-semibold text-slate-300">Subjects: </span>
                    <span className="text-slate-400">{policy.subjects.join(', ')}</span>
                </div>
                <div>
                    <span className="font-semibold text-slate-300">Resources: </span>
                    <span className="text-slate-400">{policy.resources.join(', ')}</span>
                </div>
                <div>
                    <span className="font-semibold text-slate-300">Conditions: </span>
                    <span className="text-slate-400">{policy.conditions.join(', ')}</span>
                </div>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-700 flex justify-between items-center">
                <span className={`text-sm font-semibold ${policy.enabled ? 'text-green-400' : 'text-slate-400'}`}>
                    {policy.enabled ? 'Enabled' : 'Disabled'}
                </span>
                <ToggleSwitch enabled={policy.enabled} onChange={() => togglePolicyEnabled(policy.id)} />
            </div>
        </div>
    );
}


const PoliciesView: React.FC = () => {
    const { policies } = useAppContext();
    const [isModalOpen, setModalOpen] = useState(false);

    return (
        <>
            <Modal isOpen={isModalOpen} onClose={() => setModalOpen(false)} title="Create New Access Policy">
                <PolicyForm onClose={() => setModalOpen(false)} />
            </Modal>
            <div>
                <div className="flex justify-between items-center mb-6">
                    <p className="text-slate-400">Displaying {policies.length} configured policies.</p>
                    <button onClick={() => setModalOpen(true)} className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Create New Policy</button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {policies.map(policy => <PolicyCard key={policy.id} policy={policy} />)}
                </div>
            </div>
        </>
    );
};

export default PoliciesView;