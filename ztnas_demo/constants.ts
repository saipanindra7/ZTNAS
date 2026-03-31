import type { User, Device, AccessLog, Policy, View, Role, Application } from './types';

export const initialView: View = 'dashboard';

// In a real app, never store plain text passwords. This is a simulation.
export const ROLES: Role[] = [
  { id: 'r1', name: 'Admin' },
  { id: 'r2', name: 'Engineer' },
  { id: 'r3', name: 'Sales' },
  { id: 'r4', name: 'Guest' },
];

export const USERS: User[] = [
  { id: 'u1', name: 'Admin User', email: 'admin@admin.com', role: 'Admin', password: 'admin123', mfaMethod: 'none', mfaSecret: '', needsOnboarding: false },
  { id: 'u2', name: 'Bob Williams', email: 'bob.w@example.com', role: 'Engineer', password: 'password123', mfaMethod: 'none', mfaSecret: '', needsOnboarding: false },
  { id: 'u3', name: 'Charlie Brown', email: 'charlie.b@example.com', role: 'Sales', password: 'password123', mfaMethod: 'none', mfaSecret: '', needsOnboarding: false },
  { id: 'u4', name: 'Diana Miller', email: 'diana.m@example.com', role: 'Engineer', password: 'password123', mfaMethod: 'none', mfaSecret: '', needsOnboarding: false },
  { id: 'u5', name: 'Eve Davis', email: 'eve.d@example.com', role: 'Guest', password: 'password123', mfaMethod: 'none', mfaSecret: '', needsOnboarding: false },
];

export const DEVICES: Device[] = [
  { id: 'd1', ownerId: 'u1', name: 'Admin-MBP-16', os: 'macOS', status: 'Secured', deviceFingerprint: 'fp_mac_admin_8a8a' },
  { id: 'd2', ownerId: 'u2', name: 'Bob-ThinkPad', os: 'Windows', status: 'Secured', deviceFingerprint: 'fp_win_bob_b9b9' },
  { id: 'd3', ownerId: 'u3', name: 'Sales-iPad-Pro', os: 'iOS', status: 'Secured', deviceFingerprint: 'fp_ios_charlie_c1c1' },
  { id: 'd4', ownerId: 'u4', name: 'Diana-XPS-15', os: 'Linux', status: 'Secured', deviceFingerprint: 'fp_lin_diana_d2d2' },
  { id: 'd5', ownerId: 'u2', name: 'Bobs-Pixel-7', os: 'Android', status: 'Vulnerable', deviceFingerprint: 'fp_and_bob_e3e3' },
  { id: 'd6', ownerId: 'u5', name: 'Public-Kiosk', os: 'Windows', status: 'Vulnerable', deviceFingerprint: 'fp_win_guest_f4f4' },
];

// Logs are now generated dynamically in App.tsx to reflect policy enforcement.
export const ACCESS_LOGS: AccessLog[] = [];

export const POLICIES: Policy[] = [
    {
        id: 'p1',
        name: 'Engineer Access to AWS',
        description: 'Allows engineers to access the AWS console from secured devices during business hours.',
        subjects: ['Engineer'],
        resources: ['AWS Console'],
        conditions: ['Secured Device', 'Business Hours (9am-5pm)'],
        action: 'Allow',
        enabled: true
    },
    {
        id: 'p2',
        name: 'Admin Full Access',
        description: 'Grants administrators full access to all resources from any device.',
        subjects: ['Admin'],
        resources: ['All Resources'],
        conditions: ['MFA Verified'],
        action: 'Allow',
        enabled: true
    },
    {
        id: 'p3',
        name: 'Deny Vulnerable Devices',
        description: 'Blocks access from any device that is considered vulnerable and does not meet security standards.',
        subjects: ['All Users'],
        resources: ['All Resources'],
        conditions: ['Vulnerable Device'],
        action: 'Deny',
        enabled: true
    },
    {
        id: 'p4',
        name: 'Salesforce Access for Sales Team',
        description: 'Allows the sales team to access Salesforce from secured corporate devices.',
        subjects: ['Sales'],
        resources: ['Salesforce'],
        conditions: ['Secured Device', 'Corporate Network'],
        action: 'Allow',
        enabled: true
    },
    {
        id: 'p5',
        name: 'Guest Access to Wiki',
        description: 'Provides guests with read-only access to the Internal Wiki.',
        subjects: ['Guest'],
        resources: ['Internal Wiki'],
        conditions: ['Time-limited Session'],
        action: 'Allow',
        enabled: false
    }
];

export const APPLICATIONS: Application[] = [
    { id: 'app1', name: 'AWS Console', description: 'Amazon Web Services management console.', icon: 'Database', allowedRoles: ['Admin', 'Engineer'] },
    { id: 'app2', name: 'Salesforce', description: 'Customer Relationship Management platform.', icon: 'Briefcase', allowedRoles: ['Admin', 'Sales'] },
    { id: 'app3', name: 'GitHub', description: 'Source code and repository management.', icon: 'Code', allowedRoles: ['Admin', 'Engineer'] },
    { id: 'app4', name: 'Internal Wiki', description: 'Company knowledge base and documentation.', icon: 'BookOpen', allowedRoles: ['Admin', 'Engineer', 'Sales', 'Guest'] },
];

export const VIEW_PERMISSIONS: { [key: string]: View[] } = {
    'Admin': ['dashboard', 'users-devices', 'policies', 'logs', 'profile'],
    'Engineer': ['dashboard', 'profile'],
    'Sales': ['dashboard', 'profile'],
    'Guest': ['dashboard', 'profile'],
};