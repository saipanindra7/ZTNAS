/**
 * ZTNAS HOD Dashboard API Client
 * Handles department head operations and approvals
 */

const API_BASE = 'http://localhost:8000/api/v1';

class HODAPIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    /**
     * Get HOD dashboard summary
     */
    async getDashboardSummary() {
        try {
            const response = await fetch(`${API_BASE}/hod/dashboard-summary`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch dashboard summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard summary:', error);
            return {
                faculty_count: 0,
                students_count: 0,
                classes_count: 0,
                pending_approvals: 0
            };
        }
    }

    /**
     * Get all faculty in department
     */
    async getFaculty() {
        try {
            const response = await fetch(`${API_BASE}/hod/faculty`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch faculty');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching faculty:', error);
            return [];
        }
    }

    /**
     * Get department students
     */
    async getStudents(search = '') {
        try {
            const params = search ? `?search=${search}` : '';
            const response = await fetch(`${API_BASE}/hod/students${params}`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch students');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching students:', error);
            return [];
        }
    }

    /**
     * Get pending device requests
     */
    async getPendingDeviceRequests() {
        // Endpoint is not available in current backend build.
        // Return an empty list to keep Approvals UI functional without noisy 404s.
        return [];
    }

    /**
     * Approve a device request
     */
    async approveDevice(deviceId) {
        try {
            const response = await fetch(`${API_BASE}/hod/approve-device/${deviceId}`, {
                method: 'POST',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to approve device');
            }

            return await response.json();
        } catch (error) {
            console.error('Error approving device:', error);
            throw error;
        }
    }

    /**
     * Reject a device request
     */
    async rejectDevice(deviceId, reason = 'Not approved') {
        try {
            const response = await fetch(`${API_BASE}/hod/reject-device/${deviceId}?reason=${reason}`, {
                method: 'POST',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to reject device');
            }

            return await response.json();
        } catch (error) {
            console.error('Error rejecting device:', error);
            throw error;
        }
    }

    /**
     * Get attendance overview
     */
    async getAttendanceOverview() {
        try {
            const response = await fetch(`${API_BASE}/hod/attendance-overview`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch attendance overview');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching attendance overview:', error);
            return [];
        }
    }

    /**
     * Get audit logs
     */
    async getAuditLogs(days = 30) {
        try {
            const response = await fetch(`${API_BASE}/hod/audit-logs?days=${days}`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch audit logs');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching audit logs:', error);
            return [];
        }
    }

    /**
     * Refresh access token
     */
    async refreshToken() {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                window.location.href = '/login.html';
                return;
            }

            const response = await fetch(`${API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                this.token = data.access_token;
                this.headers['Authorization'] = `Bearer ${this.token}`;
            } else {
                window.location.href = '/login.html';
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            window.location.href = '/login.html';
        }
    }
}

// Global API client
const hodAPI = new HODAPIClient();

/**
 * Dashboard Functions
 */

async function loadHODDashboard() {
    showLoading(true);
    try {
        const summary = await hodAPI.getDashboardSummary();

        // Primary target: explicit ids (if present in newer templates)
        safeSetText('faculty-count', summary.faculty_count ?? 0);
        safeSetText('students-count', summary.students_count ?? 0);
        safeSetText('classes-count', summary.classes_count ?? 0);
        safeSetText('pending-approvals-count', summary.pending_approvals ?? 0);

        // Fallback target: static card layout used by current dashboard-hod.html
        const dashboardCards = document.querySelectorAll('#dashboard-view .card-value');
        if (dashboardCards.length >= 4) {
            dashboardCards[0].textContent = String(summary.faculty_count ?? 0);
            dashboardCards[1].textContent = String(summary.students_count ?? 0);
            dashboardCards[2].textContent = String(summary.classes_count ?? 0);
            dashboardCards[3].textContent = String(summary.pending_approvals ?? 0);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadFacultyList() {
    showLoading(true);
    try {
        const faculty = await hodAPI.getFaculty();
        const tbody = getTableBody('faculty-table-body', 'faculty');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (faculty.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No faculty members</td></tr>';
            return;
        }

        faculty.forEach(f => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${f.name || f.username || '—'}</td>
                <td>${f.email}</td>
                <td>${f.designation || 'Faculty'}</td>
                <td>${f.classes_count ?? 0}</td>
                <td><span class="badge badge-active">Active</span></td>
                <td>
                    <button class="btn-small" onclick="removeFaculty(${f.faculty_id})">Remove</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading faculty:', error);
        showNotification('Failed to load faculty list', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadStudentsList() {
    showLoading(true);
    try {
        const students = await hodAPI.getStudents();
        const tbody = getTableBody('students-table-body', 'students');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No students found</td></tr>';
            return;
        }

        students.forEach(s => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${s.student_id || '—'}</td>
                <td>${s.name || s.username || '—'}</td>
                <td>${s.enrollment_year || '—'}</td>
                <td>${s.email}</td>
                <td>${s.attendance_percentage.toFixed(2)}%</td>
                <td>${(s.gpa ?? s.average_marks ?? 0).toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Failed to load students list', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadPendingApprovals() {
    showLoading(true);
    try {
        const requests = await hodAPI.getPendingDeviceRequests();
        const tbody = getTableBody('approvals-table-body', 'approvals');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No pending approvals</td></tr>';
            return;
        }

        requests.forEach(req => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${req.student_name || req.username || '—'}</td>
                <td>${req.request_type || 'Device Access'}</td>
                <td>${req.details || req.device_name || '—'}</td>
                <td>${req.request_date || req.created_at || '—'}</td>
                <td>
                    <button class="btn-approve" onclick="approveDeviceRequest(${req.id})">Approve</button>
                    <button class="btn-reject" onclick="rejectDeviceRequest(${req.id})">Reject</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading approvals:', error);
        showNotification('Failed to load pending approvals', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadAttendanceOverview() {
    showLoading(true);
    try {
        const overview = await hodAPI.getAttendanceOverview();
        const tbody = getTableBody('attendance-overview-tbody', 'attendance');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (overview.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No attendance data</td></tr>';
            return;
        }

        overview.forEach(item => {
            const row = document.createElement('tr');
            const avg = item.average_attendance ?? item.attendance_percentage ?? 0;
            row.innerHTML = `
                <td>${item.class_name}</td>
                <td>${item.faculty_name || item.class_code || '—'}</td>
                <td>${item.total_students}</td>
                <td>${Math.round((avg / 100) * item.total_students)}</td>
                <td>${Math.max(0, item.total_students - Math.round((avg / 100) * item.total_students))}</td>
                <td><span class="badge badge-active">${avg.toFixed(2)}%</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading attendance overview:', error);
        showNotification('Failed to load attendance overview', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadAuditLogs() {
    showLoading(true);
    try {
        const logs = await hodAPI.getAuditLogs(30);
        const tbody = getTableBody('audit-logs-tbody', 'audit');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No audit logs</td></tr>';
            return;
        }

        logs.slice(0, 20).forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.timestamp}</td>
                <td>${log.username}</td>
                <td>${log.action}</td>
                <td>${log.resource || '—'}</td>
                <td><span class="badge ${String(log.status).toLowerCase() === 'success' ? 'badge-active' : 'badge-warning'}">${log.status}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading audit logs:', error);
        showNotification('Failed to load audit logs', 'error');
    } finally {
        showLoading(false);
    }
}

// Approval handlers
async function approveDeviceRequest(deviceId) {
    if (confirm('Are you sure you want to approve this device?')) {
        showLoading(true);
        try {
            const result = await hodAPI.approveDevice(deviceId);
            showNotification('Device approved successfully', 'success');
            loadPendingApprovals();
        } catch (error) {
            showNotification('Failed to approve device: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }
}

async function rejectDeviceRequest(deviceId) {
    const reason = prompt('Reason for rejection:', 'Not meet security requirements');
    if (reason) {
        showLoading(true);
        try {
            const result = await hodAPI.rejectDevice(deviceId, reason);
            showNotification('Device rejected successfully', 'success');
            loadPendingApprovals();
        } catch (error) {
            showNotification('Failed to reject device: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }
}

function removeFaculty(facultyId) {
    if (confirm('Are you sure you want to remove this faculty member?')) {
        showNotification('Faculty removal would be implemented in next phase', 'info');
    }
}

// Helper functions
function showLoading(show) {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

function safeSetText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = String(value);
    }
}

function getTableBody(preferredId, viewId) {
    const byId = document.getElementById(preferredId);
    if (byId) return byId;
    return document.querySelector(`#${viewId}-view tbody`);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db'};
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 1000;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login.html';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // dashboard-hod.html already includes its own inline navigation/view controller.
    // Skip external initializer there to avoid duplicate handlers and view conflicts.
    if (typeof window.switchView === 'function') {
        return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    loadHODDashboard();
    setupHODNavigation();
});

function setupHODNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const viewId = link.getAttribute('data-view');
            if (!viewId) return;
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            document.querySelectorAll('[id$="-view"]').forEach(view => {
                view.style.display = 'none';
            });
            
            const view = document.getElementById(viewId + '-view');
            if (view) {
                view.style.display = 'block';
                
                switch (viewId) {
                    case 'faculty':
                        loadFacultyList();
                        break;
                    case 'students':
                        loadStudentsList();
                        break;
                    case 'approvals':
                        loadPendingApprovals();
                        break;
                    case 'attendance':
                        loadAttendanceOverview();
                        break;
                    case 'audit':
                        loadAuditLogs();
                        break;
                    case 'dashboard':
                        loadHODDashboard();
                        break;
                }
            }
        });
    });
}
