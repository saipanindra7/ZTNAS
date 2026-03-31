export type View = 'dashboard' | 'users-devices' | 'policies' | 'logs' | 'profile';
export type MfaMethod = 'none' | 'securityKey' | 'picture';

export interface Role {
  id: string;
  name: string;
}

export interface User {
  id:string;
  name: string;
  email: string;
  role: string;
  password?: string; // Optional for new users
  mfaMethod: MfaMethod;
  mfaSecret: string; // Simulated secret for TOTP
  needsOnboarding: boolean;
  picturePasswordSelection?: number[];
}

export interface Device {
  id: string;
  ownerId: string;
  name: string;
  os: 'macOS' | 'Windows' | 'Linux' | 'iOS' | 'Android';
  status: 'Secured' | 'Vulnerable';
  deviceFingerprint: string; // Unique identifier for device verification
}

export interface AccessLog {
  id: string;
  timestamp: Date;
  userId: string;
  deviceId: string;
  resource: string;
  location: string;
  ip: string;
  status: 'Allowed' | 'Denied';
  riskLevel: 'Low' | 'Medium' | 'High';
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  subjects: string[]; // e.g., roles like 'Engineer'
  resources: string[]; // e.g., 'GitHub', 'AWS Console'
  conditions: string[]; // e.g., 'From Corporate IP', 'During Business Hours'
  action: 'Allow' | 'Deny';
  enabled: boolean;
}

export interface Application {
    id: string;
    name: string;
    description: string;
    icon: 'Code' | 'Briefcase' | 'Database' | 'BookOpen';
    allowedRoles: string[]; // Role names
}

// Main application data context
export interface AppContextType {
  users: User[];
  devices: Device[];
  policies: Policy[];
  accessLogs: AccessLog[];
  roles: Role[];
  applications: Application[];
  addUser: (user: Omit<User, 'id' | 'password' | 'mfaMethod' | 'mfaSecret' | 'needsOnboarding'>) => User;
  updateUser: (user: User) => void;
  deleteUser: (userId: string) => void;
  addDevice: (device: Omit<Device, 'id' | 'status' | 'deviceFingerprint'>) => Device;
  updateDevice: (device: Device) => void;
  deleteDevice: (deviceId: string) => void;
  addPolicy: (policy: Omit<Policy, 'id' | 'enabled'>) => void;
  togglePolicyEnabled: (policyId: string) => void;
  addLog: (log: Omit<AccessLog, 'id' | 'timestamp'>) => void;
  logApplicationAccess: (userId: string, resourceName: string) => void;
  addRole: (roleName: string) => void;
  updateRole: (role: Role) => void;
  deleteRole: (roleId: string) => void;
}

// Authentication context
export interface AuthContextType {
    currentUser: User | null;
    isAuthenticated: boolean;
    login: (email: string, password?: string) => Promise<User>;
    logout: () => void;
    completeOnboarding: (userId: string, password_raw: string) => Promise<User>;
    setAuthenticatedState: (user: User) => void;
}