import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import { useAppContext } from '../AppContext';
import type { User, MfaMethod } from '../types';
import { Shield, Key, Grid, CheckCircle, Sun, Moon, Star, Heart, Cloud, Zap, Anchor, Gift, Coffee } from './Icons';

type View = 
    | 'login' 
    | 'onboardingDevice' 
    | 'onboardingPassword' 
    | 'mfaSelection'
    | 'mfaSetupKey'
    | 'mfaSetupPicture'
    | 'mfaVerifyPicture';

// --- Main Login Component ---
const LoginView: React.FC = () => {
    const [user, setUser] = useState<User | null>(null);
    const [view, setView] = useState<View>('login');
    const [error, setError] = useState('');
    const { setAuthenticatedState } = useAuth();

    const handleLoginSuccess = (loggedInUser: User) => {
        setError('');
        if (loggedInUser.needsOnboarding) {
            setUser(loggedInUser);
            setView('onboardingDevice');
        } else if (loggedInUser.mfaMethod === 'picture') {
            setUser(loggedInUser);
            setView('mfaVerifyPicture');
        } else {
            // Handles 'securityKey' (auto-login for demo) and 'none'
            setAuthenticatedState(loggedInUser);
        }
    };
    
    const renderContent = () => {
        switch (view) {
            case 'login':
                return <LoginForm onSuccess={handleLoginSuccess} setError={setError} />;
            case 'onboardingDevice':
                return user && <OnboardingDeviceCheck user={user} onSuccess={() => setView('onboardingPassword')} setError={setError} />;
            case 'onboardingPassword':
                return user && <OnboardingPasswordSetup 
                    user={user} 
                    setError={setError} 
                    onSuccess={(updatedUser) => {
                        setUser(updatedUser);
                        setView('mfaSelection');
                    }}
                />;
            case 'mfaSelection':
                 return user && <MfaSelection onSelect={(mfaView) => setView(mfaView)} onBack={() => setView('onboardingPassword')} />
            case 'mfaSetupKey':
                return user && <MfaSetupSecurityKeyForm user={user} setError={setError} />;
            case 'mfaSetupPicture':
                return user && <MfaSetupPicturePasswordForm user={user} setError={setError} />;
            case 'mfaVerifyPicture':
                return user && <MfaVerifyPicturePasswordForm user={user} setError={setError} />;
            default:
                return <LoginForm onSuccess={handleLoginSuccess} setError={setError} />;
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 font-sans p-4">
            <div className="w-full max-w-md">
                <div className="flex justify-center items-center space-x-3 mb-6">
                    <Shield className="w-10 h-10 text-brand-400" />
                    <h1 className="text-3xl font-bold text-slate-100">ZTNAS</h1>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl shadow-lg p-8">
                    {error && <p className="text-sm text-red-400 bg-red-900/50 p-3 rounded-md mb-4 text-center">{error}</p>}
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

// --- Sub-components for each authentication step ---

const LoginForm: React.FC<{ onSuccess: (user: User) => void, setError: (msg: string) => void }> = ({ onSuccess, setError }) => {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const user = await login(email, password);
            onSuccess(user);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <h2 className="text-xl font-bold text-center text-white mb-6">Secure Sign-In</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
                <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
                <p className="text-xs text-slate-400">Leave password blank for new user setup.</p>
                <button type="submit" disabled={isLoading} className="w-full px-5 py-3 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors disabled:bg-slate-600">
                    {isLoading ? 'Verifying...' : 'Sign In'}
                </button>
            </form>
        </>
    );
};

const OnboardingDeviceCheck: React.FC<{ user: User, onSuccess: () => void, setError: (msg: string) => void }> = ({ user, onSuccess, setError }) => {
    const { devices } = useAppContext();
    const [isVerifying, setIsVerifying] = useState(true);
    const assignedDevice = devices.find(d => d.ownerId === user.id);

    useEffect(() => {
        setError('');
        const timer = setTimeout(() => {
            if (assignedDevice) {
                onSuccess();
            } else {
                setError(`No device has been assigned to ${user.email}. Please contact your administrator.`);
            }
            setIsVerifying(false);
        }, 2000);
        return () => clearTimeout(timer);
    }, [assignedDevice, user.email, onSuccess, setError]);
    
    return (
        <div className="text-center">
            <h2 className="text-xl font-bold text-white mb-4">Verifying Your Device</h2>
            <p className="text-slate-400 mb-6">Please wait while we confirm that you are using the device assigned to you by your administrator.</p>
            {isVerifying && <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-400 mx-auto"></div>}
            {assignedDevice && !isVerifying && <p className="text-green-400">Device Verified: {assignedDevice.name}</p>}
        </div>
    );
};

const OnboardingPasswordSetup: React.FC<{ user: User, setError: (msg: string) => void, onSuccess: (user: User) => void }> = ({ user, setError, onSuccess }) => {
    const { completeOnboarding } = useAuth();
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password.length < 8) {
            setError('Password must be at least 8 characters long.');
            return;
        }
        if (password !== confirm) {
            setError('Passwords do not match.');
            return;
        }
        setError('');
        try {
            const updatedUser = await completeOnboarding(user.id, password);
            onSuccess(updatedUser);
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <>
            <h2 className="text-xl font-bold text-center text-white mb-6">Create Your Password</h2>
            <p className="text-center text-slate-400 mb-4 text-sm">Welcome, {user.name}. Please set a secure password to activate your account.</p>
            <form onSubmit={handleSubmit} className="space-y-4">
                <input type="password" placeholder="New Password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
                <input type="password" placeholder="Confirm Password" value={confirm} onChange={e => setConfirm(e.target.value)} required className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-brand-500 focus:border-brand-500" />
                <button type="submit" className="w-full px-5 py-3 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Set Password & Continue</button>
            </form>
        </>
    );
};

const MfaSelection: React.FC<{ onSelect: (view: View) => void; onBack: () => void; }> = ({ onSelect, onBack }) => {
    const mfaOptions = [
        { id: 'mfaSetupPicture', icon: <Grid className="w-6 h-6"/>, title: 'Picture Password', description: 'Select a sequence of memorable images.' },
        { id: 'mfaSetupKey', icon: <Key className="w-6 h-6"/>, title: 'Security Key', description: 'Use a physical key like a YubiKey.' },
    ];
    return (
        <div>
            <h2 className="text-xl font-bold text-center text-white mb-2">Secure Your Account</h2>
            <p className="text-center text-slate-400 mb-6 text-sm">Please select a multi-factor authentication method.</p>
            <div className="space-y-3">
                {mfaOptions.map(opt => (
                     <button key={opt.id} onClick={() => onSelect(opt.id as View)} className="w-full flex items-center space-x-4 p-4 bg-slate-900/50 hover:bg-slate-700/50 border border-slate-700 rounded-lg transition-colors">
                        <div className="text-brand-400">{opt.icon}</div>
                        <div className="text-left">
                            <p className="font-semibold text-white">{opt.title}</p>
                            <p className="text-xs text-slate-400">{opt.description}</p>
                        </div>
                    </button>
                ))}
            </div>
             <div className="mt-6 text-center">
                <button onClick={onBack} className="text-sm text-slate-400 hover:text-white transition-colors">
                    &larr; Back to Password Setup
                </button>
            </div>
        </div>
    );
};

const MfaSetupSecurityKeyForm: React.FC<{ user: User, setError: (msg: string) => void }> = ({ user, setError }) => {
    const { setAuthenticatedState } = useAuth();
    const { updateUser } = useAppContext();
    const [status, setStatus] = useState<'idle' | 'registering' | 'success'>('idle');
    const timeoutRef = useRef<number | null>(null);

    const cleanup = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    };

    useEffect(() => {
        return cleanup;
    }, []);

    const handleRegister = () => {
        setStatus('registering');
        setError('');
        // Simulate waiting for a physical key tap. Time out after 10 seconds.
        timeoutRef.current = window.setTimeout(() => {
            setError('Security key registration timed out. Please try again.');
            setStatus('idle');
        }, 10000);
    };
    
    const handleSimulatedTouch = () => {
        cleanup();
        setStatus('success');
        const updatedUser = { ...user, mfaMethod: 'securityKey' as MfaMethod };
        updateUser(updatedUser);
        // In a real app, you'd wait for user to click another button.
        // For demo, we auto-login after a short delay.
        setTimeout(() => setAuthenticatedState(updatedUser), 1500);
    };


    return (
        <div className="text-center">
             <h2 className="text-xl font-bold text-white mb-4">Set Up Security Key</h2>
             <Key className="w-20 h-20 text-slate-500 mx-auto my-6" />
             {status === 'idle' && (
                <>
                    <p className="text-slate-400 mb-6">Register a physical security key (e.g., YubiKey, Titan Key) for the most secure way to sign in.</p>
                    <button onClick={handleRegister} className="w-full px-5 py-3 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors">Register Key</button>
                </>
             )}
              {status === 'registering' && (
                <>
                    <p className="text-slate-300 mb-6">Please insert and touch your security key now...</p>
                    <div className="animate-pulse rounded-full h-8 w-8 bg-brand-500 mx-auto mb-4"></div>
                    <button onClick={handleSimulatedTouch} className="w-full px-5 py-2 text-sm font-semibold text-white bg-slate-600 rounded-lg hover:bg-slate-500 transition-colors">
                        Simulate Key Touch
                    </button>
                </>
             )}
              {status === 'success' && (
                <>
                    <div className="flex justify-center items-center space-x-2 text-green-400">
                        <CheckCircle className="w-8 h-8"/>
                        <p className="text-lg font-semibold">Security Key Registered!</p>
                    </div>
                    <p className="text-slate-400 mt-2 text-sm">You will be logged in automatically.</p>
                </>
             )}
        </div>
    );
};

// --- Picture Password Components ---
const PicturePasswordGrid: React.FC<{ onSelect: (index: number) => void, selection: number[] }> = ({ onSelect, selection }) => {
    const icons = [Sun, Moon, Star, Heart, Cloud, Zap, Anchor, Gift, Coffee];
    return (
        <div className="grid grid-cols-3 gap-4 my-6">
            {icons.map((Icon, index) => {
                const isSelected = selection.includes(index);
                const selectionNumber = selection.indexOf(index) + 1;
                return (
                    <button key={index} onClick={() => onSelect(index)} className={`relative aspect-square flex items-center justify-center rounded-lg border-2 transition-all ${isSelected ? 'bg-brand-500/30 border-brand-400' : 'bg-slate-900/50 border-slate-700 hover:border-slate-500'}`}>
                        <Icon className={`w-10 h-10 ${isSelected ? 'text-brand-300' : 'text-slate-400'}`} />
                        {isSelected && <span className="absolute -top-2 -right-2 flex items-center justify-center w-6 h-6 bg-brand-500 text-white text-sm font-bold rounded-full">{selectionNumber}</span>}
                    </button>
                );
            })}
        </div>
    );
};

const MfaSetupPicturePasswordForm: React.FC<{ user: User, setError: (msg: string) => void }> = ({ user, setError }) => {
    const { setAuthenticatedState } = useAuth();
    const { updateUser } = useAppContext();
    const [selection, setSelection] = useState<number[]>([]);

    const handleSelect = (index: number) => {
        if (selection.length < 3 && !selection.includes(index)) {
            setSelection(prev => [...prev, index]);
        }
    };

    const handleConfirm = () => {
        if (selection.length === 3) {
            setError('');
            const updatedUser = { ...user, mfaMethod: 'picture' as MfaMethod, picturePasswordSelection: selection };
            updateUser(updatedUser);
            setAuthenticatedState(updatedUser);
        } else {
            setError('Please select exactly 3 images.');
        }
    };

    return (
        <>
            <h2 className="text-xl font-bold text-center text-white mb-4">Set Up Picture Password</h2>
            <p className="text-center text-slate-400 mb-4 text-sm">Select 3 images in an order you will remember. This will be your second factor.</p>
            <PicturePasswordGrid onSelect={handleSelect} selection={selection} />
            <div className="flex items-center justify-between">
                <button onClick={() => setSelection([])} className="text-sm text-slate-400 hover:text-white">Reset</button>
                <button onClick={handleConfirm} disabled={selection.length !== 3} className="px-5 py-3 text-sm font-semibold text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors disabled:bg-slate-600">
                    Confirm & Finish Setup ({selection.length}/3)
                </button>
            </div>
        </>
    );
};

const MfaVerifyPicturePasswordForm: React.FC<{ user: User, setError: (msg: string) => void }> = ({ user, setError }) => {
    const { setAuthenticatedState } = useAuth();
    const [selection, setSelection] = useState<number[]>([]);

    useEffect(() => {
        if (selection.length === user.picturePasswordSelection?.length) {
            const isMatch = JSON.stringify(selection) === JSON.stringify(user.picturePasswordSelection);
            if (isMatch) {
                setError('');
                setTimeout(() => setAuthenticatedState(user), 300); // Short delay for user feedback
            } else {
                setError('Incorrect picture sequence. Please try again.');
                setTimeout(() => setSelection([]), 1000); // Reset after a delay
            }
        }
    }, [selection, user, setAuthenticatedState, setError]);

    const handleSelect = (index: number) => {
        if (selection.length < (user.picturePasswordSelection?.length || 3)) {
            setSelection(prev => [...prev, index]);
        }
    };

    return (
        <>
            <h2 className="text-xl font-bold text-center text-white mb-4">Verify Picture Password</h2>
            <p className="text-center text-slate-400 mb-4 text-sm">Please select your images in the correct order.</p>
            <PicturePasswordGrid onSelect={handleSelect} selection={selection} />
            <div className="text-center text-sm text-slate-500">
                Selected {selection.length} of {user.picturePasswordSelection?.length || 3}
            </div>
        </>
    );
};

export default LoginView;