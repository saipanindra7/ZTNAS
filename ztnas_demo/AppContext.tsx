import React, { useState, createContext, useContext, useEffect, useCallback } from 'react';
import type { AppContextType, User, Device, Policy, AccessLog, Role, Application } from './types';
import { USERS as INITIAL_USERS, DEVICES as INITIAL_DEVICES, POLICIES as INITIAL_POLICIES, ROLES as INITIAL_ROLES, APPLICATIONS as INITIAL_APPLICATIONS } from './constants';

const AppContext = createContext<AppContextType | null>(null);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [devices, setDevices] = useState<Device[]>(INITIAL_DEVICES);
  const [policies, setPolicies] = useState<Policy[]>(INITIAL_POLICIES);
  const [accessLogs, setAccessLogs] = useState<AccessLog[]>([]);
  const [roles, setRoles] = useState<Role[]>(INITIAL_ROLES);
  const [applications, setApplications] = useState<Application[]>(INITIAL_APPLICATIONS);

  // --- Policy Evaluation Engine ---
  const evaluateAccess = useCallback((userId: string, deviceId: string, resource: string): { status: 'Allowed' | 'Denied'; reason: string, riskLevel: 'Low' | 'Medium' | 'High' } => {
    const user = users.find(u => u.id === userId);
    const device = devices.find(d => d.id === deviceId);

    if (!user || !device) {
      return { status: 'Denied', reason: 'Unknown user or device', riskLevel: 'High' };
    }

    const enabledPolicies = policies.filter(p => p.enabled);
    const matchingPolicies = enabledPolicies.filter(p => {
      const subjectMatch = p.subjects.includes(user.role) || p.subjects.includes('All Users');
      const resourceMatch = p.resources.includes(resource) || p.resources.includes('All Resources');
      
      if (!subjectMatch || !resourceMatch) return false;

      // In a real ZTNA, this would be a complex evaluation of real-time signals
      const conditionsMet = p.conditions.every(cond => {
        switch(cond) {
          case 'Secured Device':
            return device.status === 'Secured';
          case 'Vulnerable Device':
            return device.status === 'Vulnerable';
          // For simulation, we assume these conditions are met if the policy is being evaluated
          case 'Business Hours (9am-5pm)':
          case 'MFA Verified':
            return user.mfaMethod !== 'none';
          case 'Corporate Network':
          case 'Time-limited Session':
            return true;
          default:
            return false;
        }
      });

      return conditionsMet;
    });
    
    // Deny policies take precedence
    const denyPolicy = matchingPolicies.find(p => p.action === 'Deny');
    if (denyPolicy) {
      return { status: 'Denied', reason: `Policy Violation: ${denyPolicy.name}`, riskLevel: 'High' };
    }

    const allowPolicy = matchingPolicies.find(p => p.action === 'Allow');
    if (allowPolicy) {
      return { status: 'Allowed', reason: `Policy Match: ${allowPolicy.name}`, riskLevel: device.status === 'Vulnerable' ? 'Medium' : 'Low' };
    }
    
    // Default Deny: If no policies explicitly allow access, deny it.
    return { status: 'Denied', reason: 'No matching allow policy', riskLevel: 'Medium' };
  }, [users, devices, policies]);


  const addLog = useCallback((log: Omit<AccessLog, 'id' | 'timestamp'>) => {
    setAccessLogs(prevLogs => {
      const newLog: AccessLog = {
        ...log,
        id: `log-${Date.now()}-${Math.random()}`,
        timestamp: new Date(),
      };
      return [newLog, ...prevLogs].slice(0, 100); // Keep logs capped at 100 entries
    });
  }, []);

  // --- Real-time Access Simulation ---
  useEffect(() => {
    const simulateAccess = () => {
      if (users.length === 0 || devices.length === 0) return;
      const randomUser = users[Math.floor(Math.random() * users.length)];
      const userDevices = devices.filter(d => d.ownerId === randomUser.id);
      const randomDevice = userDevices.length > 0 ? userDevices[Math.floor(Math.random() * userDevices.length)] : devices[Math.floor(Math.random() * devices.length)];
      
      const resources = ['AWS Console', 'GitHub', 'Salesforce', 'Internal Wiki', 'Root Database'];
      const randomResource = resources[Math.floor(Math.random() * resources.length)];
      
      const locations = ['New York, USA', 'London, UK', 'Tokyo, JP', 'Sydney, AU', 'Remote'];
      const randomLocation = locations[Math.floor(Math.random() * locations.length)];
      
      const randomIp = `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;

      const result = evaluateAccess(randomUser.id, randomDevice.id, randomResource);

      addLog({
        userId: randomUser.id,
        deviceId: randomDevice.id,
        resource: randomResource,
        location: randomLocation,
        ip: randomIp,
        status: result.status,
        riskLevel: result.riskLevel,
      });
    };

    const interval = setInterval(simulateAccess, 3000); // Simulate an access attempt every 3 seconds
    return () => clearInterval(interval);
  }, [users, devices, evaluateAccess, addLog]);


  // --- CRUD Operations ---
  const addUser = (user: Omit<User, 'id' | 'password' | 'mfaMethod' | 'mfaSecret' | 'needsOnboarding'>): User => {
    const newUser: User = {
      ...user,
      id: `u${Date.now()}`,
      mfaMethod: 'none', // New users must set up MFA
      mfaSecret: '', // Secret is not used for non-TOTP methods
      needsOnboarding: true,
    };
    setUsers(prev => [...prev, newUser]);
    return newUser;
  };
  
  const updateUser = (updatedUser: User) => {
    setUsers(prev => prev.map(user => user.id === updatedUser.id ? updatedUser : user));
  };

  const deleteUser = (userId: string) => {
    // Prevent deletion of the main admin user to avoid lockout
    if (userId === 'u1') {
      alert("Deletion of the primary admin user is not permitted.");
      return;
    }
    // Delete the user
    setUsers(prev => prev.filter(u => u.id !== userId));
    // Cascade delete to their devices
    setDevices(prev => prev.filter(d => d.ownerId !== userId));
  };
  
  const addDevice = (device: Omit<Device, 'id' | 'status' | 'deviceFingerprint'>): Device => {
    const newDevice: Device = {
        ...device,
        id: `d${Date.now()}`,
        status: 'Secured', // Assume new devices are provisioned securely
        deviceFingerprint: `fp_${device.os.toLowerCase().slice(0,3)}_${device.ownerId}_${Math.random().toString(16).slice(2,6)}`,
    };
    setDevices(prev => [...prev, newDevice]);
    return newDevice;
  };

  const updateDevice = (updatedDevice: Device) => {
    setDevices(prev => prev.map(device => device.id === updatedDevice.id ? updatedDevice : device));
  };

  const deleteDevice = (deviceId: string) => {
    setDevices(prev => prev.filter(d => d.id !== deviceId));
  };

  const addPolicy = (policy: Omit<Policy, 'id' | 'enabled'>) => {
    const newPolicy: Policy = {
      ...policy,
      id: `p${Date.now()}`,
      enabled: true,
    };
    setPolicies(prev => [...prev, newPolicy]);
  };
  
  const togglePolicyEnabled = (policyId: string) => {
    setPolicies(prev => prev.map(p => p.id === policyId ? { ...p, enabled: !p.enabled } : p));
  };

  const logApplicationAccess = (userId: string, resourceName: string) => {
    const userDevices = devices.filter(d => d.ownerId === userId);
    const deviceToLog = userDevices.find(d => d.status === 'Secured') || userDevices[0];

    if (!deviceToLog) {
      console.warn(`User ${userId} has no devices; cannot log application access.`);
      return;
    }

    const result = evaluateAccess(userId, deviceToLog.id, resourceName);
    
    addLog({
      userId: userId,
      deviceId: deviceToLog.id,
      resource: resourceName,
      location: 'Corporate HQ, USA',
      ip: '10.1.1.5',
      status: result.status,
      riskLevel: result.riskLevel,
    });
  };
  
  const addRole = (roleName: string) => {
    const newRole: Role = { id: `r${Date.now()}`, name: roleName };
    setRoles(prev => [...prev, newRole]);
  };

  const updateRole = (updatedRole: Role) => {
    setRoles(prev => prev.map(role => role.id === updatedRole.id ? updatedRole : role));
  };

  const deleteRole = (roleId: string) => {
    setRoles(prev => prev.filter(r => r.id !== roleId));
  };


  const contextValue: AppContextType = {
    users,
    devices,
    policies,
    accessLogs,
    roles,
    applications,
    addUser,
    updateUser,
    deleteUser,
    addDevice,
    updateDevice,
    deleteDevice,
    addPolicy,
    togglePolicyEnabled,
    addLog,
    logApplicationAccess,
    addRole,
    updateRole,
    deleteRole,
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};