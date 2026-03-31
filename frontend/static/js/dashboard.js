// ========================================
// ZTNAS Dashboard JavaScript - College Role-Based Access
// ========================================

console.log('Dashboard.js loading...');

// Initialize after auth loads
let authToken = null;
let currentUser = null;

function initAuthData() {
    authToken = auth.getToken();
    currentUser = auth.getCurrentUser();
    console.log('Auth token found:', !!authToken);
    console.log('Current user:', currentUser);
}

// Chart instances for cleanup
let charts = {};

// ========================================
// ROLE-BASED CONFIGURATION
// ========================================

const ROLE_CONFIG = {
    hod: {
        displayName: 'Head of Department',
        icon: '👨‍💼',
        navItems: ['dashboard', 'users-devices', 'policies', 'logs', 'profile'],
        permissions: ['view_all_reports', 'manage_faculty', 'view_policies']
    },
    faculty: {
        displayName: 'Faculty Member',
        icon: '👨‍🏫',
        navItems: ['dashboard', 'users-devices', 'profile'],
        permissions: ['view_own_reports', 'view_student_data']
    },
    student: {
        displayName: 'Student',
        icon: '👨‍🎓',
        navItems: ['dashboard', 'profile'],
        permissions: ['view_own_data']
    },
    admin: {
        displayName: 'System Administrator',
        icon: '🔐',
        navItems: ['dashboard', 'users-devices', 'policies', 'logs', 'profile'],
        permissions: ['admin_full_access']
    }
};

function getUserRole() {
    // Use centralized auth service
    return auth.getUserRole();
}

function getRoleConfig() {
    const role = getUserRole();
    return ROLE_CONFIG[role] || ROLE_CONFIG.student;
}

// ========================================
// INITIALIZATION
// ========================================

function initializeDashboard() {
    // Initialize auth data first
    initAuthData();
    
    // Check authentication using auth service
    if (!auth.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    const roleConfig = getRoleConfig();
    
    console.log('Dashboard initializing with token:', authToken?.substring(0, 20) + '...');
    console.log('User role:', getUserRole());
    console.log('Role config:', roleConfig);

    // Customize page title based on role
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
        pageTitle.innerHTML = `${roleConfig.icon} ${roleConfig.displayName} Dashboard`;
    }

    // Filter navigation items based on role
    configureRoleBasedNavigation(roleConfig);

    // Setup navigation event listeners
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const view = this.getAttribute('data-view');
            if (view) {
                e.preventDefault();
                switchView(view);
            }
        });
    });

    // Setup modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });

    // Close modals when clicking overlay
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                const modal = this.closest('.modal');
                if (modal) {
                    closeModal(modal.id);
                }
            }
        });
    });

    // Set user name in header
    if (currentUser && currentUser.username) {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            userNameEl.textContent = currentUser.username;
        }
    }

    // Display device verification info
    if (typeof deviceVerification !== 'undefined') {
        try {
            deviceVerification.displayVerificationUI();
            console.log('Device verification UI displayed');
        } catch (err) {
            console.warn('Could not display device verification UI:', err);
        }
    }

    // Load initial data
    console.log('Loading dashboard data...');
    loadDashboardData();
    setInterval(loadDashboardData, 30000); // Refresh every 30s
}

    // Initialize when DOM is ready
if (document.readyState === 'loading') {
    // DOM not ready yet
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    // DOM already ready
    initializeDashboard();
}

// ========================================
// ROLE-BASED NAVIGATION CONFIGURATION
// ========================================

function configureRoleBasedNavigation(roleConfig) {
    const navItems = document.querySelectorAll('.nav-item:not(.admin-only)');
    
    navItems.forEach(item => {
        const view = item.getAttribute('data-view');
        
        if (roleConfig.navItems.includes(view)) {
            // Show this nav item
            item.style.display = 'flex';
        } else {
            // Hide this nav item
            item.style.display = 'none';
        }
    });

    // Show admin panel link if user is admin
    const role = getUserRole();
    const adminPanelBtn = document.getElementById('adminPanelBtn');
    if (adminPanelBtn) {
        adminPanelBtn.style.display = role === 'admin' ? 'flex' : 'none';
    }
    
    if (role === 'student') {
        // Students can only see their own data
        const el1 = document.getElementById('users-devices-view');
        if (el1) el1.style.display = 'none';
        const el2 = document.getElementById('policies-view');
        if (el2) el2.style.display = 'none';
        const el3 = document.getElementById('logs-view');
        if (el3) el3.style.display = 'none';
    } else if (role === 'faculty') {
        // Faculty can see their reports and student data
        const el1 = document.getElementById('logs-view');
        if (el1) el1.style.display = 'none';
        const el2 = document.getElementById('policies-view');
        if (el2) el2.style.display = 'none';
    } else if (role === 'hod') {
        // HOD sees everything
    } else if (role === 'admin') {
        // Admin sees everything
    }
}

// ========================================
// NAVIGATION & VIEW MANAGEMENT
// ========================================

function switchView(view) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-view="${view}"]`)?.classList.add('active');

    // Hide all views
    document.querySelectorAll('.view').forEach(section => {
        section.classList.remove('active');
    });

    // Show target view
    const viewEl = document.getElementById(`${view}-view`);
    if (viewEl) {
        viewEl.classList.add('active');
        
        // Load view-specific data
        switch(view) {
            case 'users-devices':
                loadUsersDevicesData();
                break;
            case 'policies':
                loadPoliciesData();
                break;
            case 'logs':
                loadLogsData();
                break;
            case 'profile':
                loadProfileData();
                break;
            default:
                loadDashboardData();
        }
    }
}

// ========================================
// MODAL MANAGEMENT
// ========================================

function showAddUserModal() {
    const modal = document.getElementById('addUserModal');
    if (modal) {
        modal.classList.add('active');
        document.getElementById('addUserForm')?.reset();
    }
}

function showAddPolicyModal() {
    const modal = document.getElementById('addPolicyModal');
    if (modal) {
        modal.classList.add('active');
        document.getElementById('addPolicyForm')?.reset();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// ========================================
// DASHBOARD DATA LOADING
// ========================================

async function loadDashboardData() {
    try {
        console.log('Fetching dashboard data...');
        
        // Fetch each piece of data independently with fallback
        let users = [];
        let riskData = null;
        let anomalies = [];
        
        try {
            users = await fetchAPI('/auth/users', 'GET');
        } catch (err) {
            console.warn('Could not load users:', err);
        }

        try {
            riskData = await fetchAPI('/zero-trust/risk/timeline', 'GET');
        } catch (err) {
            console.warn('Could not load risk data:', err);
        }

        try {
            anomalies = await fetchAPI('/zero-trust/anomalies/recent', 'GET');
        } catch (err) {
            console.warn('Could not load anomalies:', err);
        }

        // Update metrics safely
        document.getElementById('stat-active-users').textContent = users?.length || 0;
        
        let mfaEnrolled = 0;
        if (Array.isArray(users)) {
            mfaEnrolled = users.filter(u => u.mfa_enabled).length;
        }
        document.getElementById('stat-mfa-enrolled').textContent = mfaEnrolled;

        let highRiskCount = 0;
        if (riskData && Array.isArray(riskData.timeline)) {
            highRiskCount = riskData.timeline.filter(r => 
                r.risk_level === 'HIGH' || r.risk_level === 'CRITICAL'
            ).length;
        }
        document.getElementById('stat-risk-events').textContent = highRiskCount;

        document.getElementById('stat-anomalies').textContent = (anomalies?.length || 0);

        // Update recent events table
        populateRecentEvents(riskData?.timeline || []);

        // Create risk distribution chart
        try {
            createRiskChart(riskData?.timeline || []);
        } catch (err) {
            console.warn('Could not create chart:', err);
        }

        console.log('Dashboard data loaded successfully');

    } catch (error) {
        console.error('Error in loadDashboardData:', error);
        showAlert('Dashboard data loading encountered an issue', 'error');
    }
}

async function loadUsersDevicesData() {
    try {
        const [usersResponse, devicesResponse] = await Promise.all([
            fetchAPI('/auth/users', 'GET'),
            fetchAPI('/zero-trust/devices/trusted', 'GET')
        ]);

        // Extract arrays from API responses
        const users = usersResponse?.users || [];
        const devices = devicesResponse?.devices || [];
        
        populateUsersDevicesTable(users, devices);
    } catch (error) {
        console.error('Error loading users/devices data:', error);
        showAlert('Failed to load users and devices', 'error');
    }
}

async function loadPoliciesData() {
    try {
        const response = await fetchAPI('/auth/policies', 'GET');
        const policies = response?.policies || [];
        populatePoliciesTable(policies);
    } catch (error) {
        console.error('Error loading policies:', error);
        showAlert('Failed to load policies', 'error');
    }
}

async function loadLogsData() {
    try {
        const response = await fetchAPI('/auth/audit/logs', 'GET');
        const logs = response?.logs || [];
        populateLogsTable(logs);
    } catch (error) {
        console.error('Error loading logs:', error);
        showAlert('Failed to load logs', 'error');
    }
}

async function loadProfileData() {
    try {
        const profile = currentUser;
        if (profile) {
            document.getElementById('profile-name').value = profile.name || profile.username || 'N/A';
            document.getElementById('profile-email').value = profile.email || 'N/A';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

// ========================================
// TABLE POPULATION
// ========================================

function populateRecentAccessTable(events) {
    const tbody = document.getElementById('devices-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    if (!events || events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No recent events</td></tr>';
        return;
    }

    events.slice(0, 10).forEach(event => {
        const riskBadge = createRiskBadge(event.risk_level);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${event.user_id || 'N/A'}</td>
            <td>${formatTimestamp(event.timestamp)}</td>
            <td>${riskBadge}</td>
            <td>${event.device_info?.device_name || 'Unknown'}</td>
            <td>${event.access_location || 'N/A'}</td>
            <td>${event.access_decision || 'ALLOWED'}</td>
        `;
        tbody.appendChild(row);
    });
}

function populateRecentEvents(events) {
    populateRecentAccessTable(events);
}

function populateUsersDevicesTable(users, devices) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    users.forEach(user => {
        const userDevices = devices.filter(d => d.user_id === user.id);
        const row = document.createElement('tr');
        const statusBadge = user.is_active ? '<span class="status-badge active">✓ Active</span>' : 
                           '<span class="status-badge inactive">✗ Inactive</span>';
        
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${statusBadge}</td>
            <td>${user.mfa_enabled ? '✓ Enabled' : '✗ Not Set'}</td>
            <td>${userDevices.length}</td>
            <td>
                <button class="btn-secondary btn-sm" onclick="editUser('${user.id}')">Edit</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No users</td></tr>';
    }
}

function populatePoliciesTable(policies) {
    const tbody = document.getElementById('policies-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    policies.forEach(policy => {
        const row = document.createElement('tr');
        const statusBadge = policy.is_active ? '<span class="status-badge active">✓ Active</span>' : 
                           '<span class="status-badge inactive">✗ Inactive</span>';
        
        row.innerHTML = `
            <td>${policy.name || 'Unnamed'}</td>
            <td>${policy.description || 'N/A'}</td>
            <td>${statusBadge}</td>
            <td>${policy.conditions?.length || 0}</td>
            <td>${formatTimestamp(policy.created_at)}</td>
            <td>
                <button class="btn-secondary btn-sm" onclick="editPolicy('${policy.id}')">Edit</button>
                <button class="btn-danger btn-sm" onclick="deletePolicy('${policy.id}')">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    if (policies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No policies</td></tr>';
    }
}

function populateLogsTable(logs) {
    const tbody = document.getElementById('logs-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    logs.slice(0, 50).forEach(log => {
        const row = document.createElement('tr');
        const statusClass = log.status === 'success' ? 'status-success' : 'status-error';
        
        row.innerHTML = `
            <td>${formatTimestamp(log.timestamp)}</td>
            <td>${log.user_id || 'System'}</td>
            <td><code>${log.action}</code></td>
            <td>${log.resource || 'N/A'}</td>
            <td><span class="${statusClass}">${log.status?.toUpperCase()}</span></td>
            <td><code>${log.ip_address || 'N/A'}</code></td>
        `;
        tbody.appendChild(row);
    });

    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No logs</td></tr>';
    }
}

// ========================================
// CHARTS
// ========================================

function createRiskChart(data) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded yet, skipping chart creation');
        return;
    }

    destroyChart('risk-chart');

    const ctx = document.getElementById('risk-chart')?.getContext('2d');
    if (!ctx) {
        console.warn('Risk chart container not found');
        return;
    }

    if (!data || data.length === 0) {
        console.warn('No data for risk chart');
        return;
    }

    const riskCounts = {
        'MINIMAL': 0,
        'LOW': 0,
        'MEDIUM': 0,
        'HIGH': 0,
        'CRITICAL': 0
    };

    data.forEach(item => {
        riskCounts[item.risk_level] = (riskCounts[item.risk_level] || 0) + 1;
    });

    try {
        charts['risk-chart'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(riskCounts),
                datasets: [{
                    data: Object.values(riskCounts),
                    backgroundColor: [
                        '#28a745',  // MINIMAL
                        '#0066cc',  // LOW
                        '#ffc107',  // MEDIUM
                        '#ff6b35',  // HIGH
                        '#dc3545'   // CRITICAL
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed;
                            }
                        }
                    }
                }
            }
        });
        console.log('Risk chart created successfully');
    } catch (err) {
        console.error('Error creating risk chart:', err);
    }
}

function createRiskTrendChart(data) {
    destroyChart('risk-trend-chart');

    const ctx = document.getElementById('risk-trend-chart')?.getContext('2d');
    if (!ctx) return;

    // Group data by date
    const dateRisks = {};
    data.forEach(item => {
        const date = new Date(item.timestamp).toLocaleDateString();
        if (!dateRisks[date]) dateRisks[date] = [];
        dateRisks[date].push(item.risk_score || 0.5);
    });

    const labels = Object.keys(dateRisks).slice(-7);
    const avgRisks = labels.map(date => {
        const risks = dateRisks[date];
        return (risks.reduce((a, b) => a + b, 0) / risks.length).toFixed(2);
    });

    charts['risk-trend-chart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Risk Score',
                data: avgRisks,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointBackgroundColor: '#0066cc'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Risk Score'
                    }
                }
            }
        }
    });
}

function createDeviceTrustChart(devices) {
    destroyChart('device-trust-chart');

    const container = document.getElementById('device-trust-chart');
    if (!container) return;

    const trustLevels = {
        'Trusted': 0,
        'Medium': 0,
        'Low': 0
    };

    devices.forEach(device => {
        if (device.trust_score > 0.7) trustLevels['Trusted']++;
        else if (device.trust_score > 0.4) trustLevels['Medium']++;
        else trustLevels['Low']++;
    });

    const ctx = document.createElement('canvas');
    ctx.id = 'device-trust-chart';
    container.innerHTML = '';
    container.appendChild(ctx);

    charts['device-trust-chart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(trustLevels),
            datasets: [{
                label: 'Devices',
                data: Object.values(trustLevels),
                backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function createLoginPatternChart(hours) {
    destroyChart('login-pattern-chart');

    const ctx = document.getElementById('login-pattern-chart')?.getContext('2d');
    if (!ctx) return;

    const hourLabels = Array.from({length: 24}, (_, i) => `${i}:00`);
    const hourData = hourLabels.map(hour => {
        const h = parseInt(hour);
        return hours[h] || Math.random() * 10;
    });

    charts['login-pattern-chart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hourLabels,
            datasets: [{
                label: 'Logins by Hour',
                data: hourData,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createLocationDistribution(locations) {
    const container = document.getElementById('location-distribution');
    if (!container) return;

    container.innerHTML = '';
    
    if (!locations || locations.length === 0) {
        container.innerHTML = '<p class="text-muted">No location data available</p>';
        return;
    }

    const listHTML = locations.slice(0, 5)
        .map(loc => `<div style="padding: 8px 0; border-bottom: 1px solid #e9ecef;">
            📍 ${loc.city || 'Unknown'}, ${loc.country || 'Unknown'}
            <span style="color: #999; font-size: 12px;"> (${loc.count} logins)</span>
        </div>`)
        .join('');
    
    container.innerHTML = listHTML;
}

function createRiskBreakdown(risks) {
    const container = document.getElementById('risk-breakdown');
    if (!container) return;

    // Calculate average risk factors
    let totalRisk = 0;
    let count = 0;
    let deviceRisk = 0, behaviorRisk = 0, networkRisk = 0, timeRisk = 0, authRisk = 0;

    risks.forEach(r => {
        totalRisk += r.risk_score || 0.5;
        const factors = r.risk_factors || {};
        deviceRisk += (1 - (factors.device_score || 0.5)) * 0.25;
        behaviorRisk += (1 - (factors.behavior_score || 0.5)) * 0.20;
        networkRisk += factors.network_risk || 0;
        timeRisk += factors.time_risk || 0;
        authRisk += factors.auth_risk || 0;
        count++;
    });

    if (count === 0) return;

    const avg = (n) => (n / count).toFixed(2);

    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
            <div style="padding: 12px; background: rgba(0, 102, 204, 0.1); border-radius: 8px;">
                <strong>Device Risk</strong>
                <div style="font-size: 24px; color: #0066cc; margin-top: 4px;">${avg(deviceRisk)}</div>
            </div>
            <div style="padding: 12px; background: rgba(255, 107, 53, 0.1); border-radius: 8px;">
                <strong>Network Risk</strong>
                <div style="font-size: 24px; color: #ff6b35; margin-top: 4px;">${avg(networkRisk)}</div>
            </div>
            <div style="padding: 12px; background: rgba(255, 193, 7, 0.1); border-radius: 8px;">
                <strong>Behavior Risk</strong>
                <div style="font-size: 24px; color: #ffc107; margin-top: 4px;">${avg(behaviorRisk)}</div>
            </div>
            <div style="padding: 12px; background: rgba(220, 53, 69, 0.1); border-radius: 8px;">
                <strong>Auth Risk</strong>
                <div style="font-size: 24px; color: #dc3545; margin-top: 4px;">${avg(authRisk)}</div>
            </div>
        </div>
    `;
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function createRiskBadge(level) {
    const levels = {
        'MINIMAL': 'risk-minimal',
        'LOW': 'risk-low',
        'MEDIUM': 'risk-medium',
        'HIGH': 'risk-high',
        'CRITICAL': 'risk-critical'
    };
    
    const className = levels[level] || levels['MEDIUM'];
    return `<span class="risk-badge ${className}">${level}</span>`;
}

function createTrustBadge(score) {
    let label = 'Low', className = 'risk-high';
    if (score > 0.7) {
        label = 'High';
        className = 'risk-minimal';
    } else if (score > 0.4) {
        label = 'Medium';
        className = 'risk-medium';
    }
    
    return `<span class="risk-badge ${className}">${label} (${score.toFixed(2)})</span>`;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function formatPercent(value) {
    return (value * 100).toFixed(1) + '%';
}

function destroyChart(chartId) {
    if (charts[chartId]) {
        charts[chartId].destroy();
        delete charts[chartId];
    }
}

// ========================================
// API CALLS
// ========================================

async function fetchAPI(endpoint, method = 'GET', body = null) {
    // Delegate to centralized auth service
    return await auth.fetchAPI(endpoint, method, body);
}

// ========================================
// ACTIONS
// ========================================

async function editUser(userId) {
    showAlert(`Editing user: ${userId}`);
    showAddUserModal();
}

async function editPolicy(policyId) {
    showAlert(`Editing policy: ${policyId}`);
    showAddPolicyModal();
}

async function deletePolicy(policyId) {
    if (!confirm('Delete this policy?')) return;
    
    try {
        await fetchAPI(`/zero-trust/policies/${policyId}`, 'DELETE');
        showAlert('Policy deleted successfully', 'success');
        loadPoliciesData();
    } catch (error) {
        showAlert('Failed to delete policy', 'error');
    }
}

function logout() {
    auth.logout();
    window.location.href = 'login.html';
}

/**
 * Navigate to admin panel for admin users
 */
function goToAdminPanel() {
    window.location.href = 'admin-dashboard.html';
}

// ========================================
// NOTIFICATIONS & HELPERS
// ========================================

function showAlert(message, type = 'info') {
    // Log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 2000;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}
