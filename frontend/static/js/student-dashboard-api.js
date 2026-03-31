/**
 * ZTNAS Student Dashboard API Client
 * Handles all API calls to backend for student data
 */

const API_BASE = 'http://localhost:8000/api/v1';

class StudentAPIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    /**
     * Get student dashboard summary
     * @returns {Promise<{attendance_percentage, average_grade, total_marks, total_fee, paid_fee, pending_fee, fee_status}>}
     */
    async getDashboardSummary() {
        try {
            const response = await fetch(`${API_BASE}/student/dashboard-summary`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.refreshToken();
                    return this.getDashboardSummary();
                }
                throw new Error('Failed to fetch dashboard summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard summary:', error);
            return {
                attendance_percentage: 0,
                average_grade: 'N/A',
                total_marks: 0,
                total_fee: 0,
                paid_fee: 0,
                pending_fee: 0,
                fee_status: 'ERROR'
            };
        }
    }

    /**
     * Get attendance records
     * @param {number} days - Number of days to fetch (default 30)
     * @returns {Promise<Array>}
     */
    async getAttendance(days = 30) {
        try {
            const response = await fetch(
                `${API_BASE}/student/attendance?days=${days}`,
                {
                    method: 'GET',
                    headers: this.headers
                }
            );

            if (!response.ok) {
                if (response.status === 401) {
                    await this.refreshToken();
                    return this.getAttendance(days);
                }
                throw new Error('Failed to fetch attendance');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching attendance:', error);
            return [];
        }
    }

    /**
     * Get attendance summary
     * @returns {Promise<{total_classes, present_count, attendance_percentage}>}
     */
    async getAttendanceSummary() {
        try {
            const response = await fetch(`${API_BASE}/student/attendance/summary`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch attendance summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching attendance summary:', error);
            return {
                total_classes: 0,
                present_count: 0,
                attendance_percentage: 0
            };
        }
    }

    /**
     * Get marks records
     * @returns {Promise<Array>}
     */
    async getMarks() {
        try {
            const response = await fetch(`${API_BASE}/student/marks`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    await this.refreshToken();
                    return this.getMarks();
                }
                throw new Error('Failed to fetch marks');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching marks:', error);
            return [];
        }
    }

    /**
     * Get marks summary
     * @returns {Promise<{average_marks, highest_marks, lowest_marks, total_exams, average_grade}>}
     */
    async getMarksSummary() {
        try {
            const response = await fetch(`${API_BASE}/student/marks/summary`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch marks summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching marks summary:', error);
            return {
                average_marks: 0,
                highest_marks: 0,
                lowest_marks: 0,
                total_exams: 0,
                average_grade: 'N/A'
            };
        }
    }

    /**
     * Get fees records
     * @returns {Promise<Array>}
     */
    async getFees() {
        try {
            const response = await fetch(`${API_BASE}/student/fees`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    await this.refreshToken();
                    return this.getFees();
                }
                throw new Error('Failed to fetch fees');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching fees:', error);
            return [];
        }
    }

    /**
     * Get fees summary
     * @returns {Promise<{total_fee, paid_fee, pending_fee, fee_status}>}
     */
    async getFeesSummary() {
        try {
            const response = await fetch(`${API_BASE}/student/fees/summary`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch fees summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching fees summary:', error);
            return {
                total_fee: 0,
                paid_fee: 0,
                pending_fee: 0,
                fee_status: 'ERROR'
            };
        }
    }

    /**
     * Refresh access token
     * @returns {Promise<void>}
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

// Create global API client instance
const studentAPI = new StudentAPIClient();

/**
 * Dashboard Functions for UI Updates
 */

async function loadDashboardView() {
    showLoading(true);
    try {
        const summary = await studentAPI.getDashboardSummary();
        
        // Update statistics cards
        safeSetText('attendance-percent', `${summary.attendance_percentage ?? 0}%`);
        safeSetText('attendance-percentage', `${summary.attendance_percentage ?? 0}%`);
        safeSetText('average-grade', summary.average_grade ?? 'N/A');

        const pendingFee = Number(summary.pending_fee ?? summary.pending_fees ?? 0);
        const paidFee = Number(summary.paid_fee ?? summary.paid_fees ?? 0);
        safeSetText('pending-fees', `₹${pendingFee.toFixed(2)}`);
        safeSetText('paid-fees', `₹${paidFee.toFixed(2)}`);

        // Update status indicators
        const feeStatus = document.getElementById('fee-status');
        if (feeStatus) {
            const status = summary.fee_status || 'PENDING';
            feeStatus.textContent = status;
            feeStatus.className = 'fee-status ' + 
                (status === 'PAID' ? 'status-paid' : 
                 status === 'PENDING' ? 'status-pending' : 'status-partial');
        }

        // Fallback update for current static card layout
        safeSetText('devices-count', summary.devices_count ?? summary.active_devices ?? 0);
        safeSetText('classes-today', summary.classes_today ?? summary.today_classes ?? 0);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadAttendanceView() {
    showLoading(true);
    try {
        const records = await studentAPI.getAttendance(30);
        const tbody = getTableBody('attendance-table-body', 'attendance-table');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No attendance records found</td></tr>';
            return;
        }

        records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.attendance_date}</td>
                <td>${record.class_name}</td>
                <td><span class="status ${record.status.toLowerCase()}">${record.status}</span></td>
                <td>${record.remarks || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading attendance:', error);
        showNotification('Failed to load attendance data', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadMarksView() {
    showLoading(true);
    try {
        const records = await studentAPI.getMarks();
        const tbody = getTableBody('marks-table-body', 'marks-table');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No marks records found</td></tr>';
            return;
        }

        records.forEach(record => {
            const row = document.createElement('tr');
            const percentage = (record.marks_obtained / record.total_marks * 100).toFixed(1);
            row.innerHTML = `
                <td>${record.class_name}</td>
                <td>${record.exam_type}</td>
                <td>${record.marks_obtained}/${record.total_marks}</td>
                <td>${percentage}%</td>
                <td><span class="grade">${record.grade}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading marks:', error);
        showNotification('Failed to load marks data', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadFeesView() {
    showLoading(true);
    try {
        const records = await studentAPI.getFees();
        const tbody = getTableBody('fees-table-body', 'fees-table');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No fee records found</td></tr>';
            return;
        }

        records.forEach(record => {
            const row = document.createElement('tr');
            const remaining = record.total_fee - record.paid_amount;
            row.innerHTML = `
                <td>${record.academic_year}</td>
                <td>Sem ${record.semester}</td>
                <td>₹${record.total_fee.toFixed(2)}</td>
                <td>₹${record.paid_amount.toFixed(2)}</td>
                <td>₹${remaining.toFixed(2)}</td>
                <td><span class="fee-status ${record.fee_status.toLowerCase()}">${record.fee_status}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading fees:', error);
        showNotification('Failed to load fees data', 'error');
    } finally {
        showLoading(false);
    }
}

// Helper Functions
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

function getTableBody(primaryId, fallbackId) {
    const primary = document.getElementById(primaryId);
    if (primary) return primary;
    return document.getElementById(fallbackId);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#e74c3c' : '#27ae60'};
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // If inline page script already manages view switching, avoid duplicate handlers.
    if (typeof window.switchView === 'function') {
        return;
    }

    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    // Load initial dashboard
    loadDashboardView();

    // Set up navigation
    setupNavigation();
});

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const viewId = link.getAttribute('data-view');
            if (!viewId) return;
            
            // Remove active class from all
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Hide all content sections
            document.querySelectorAll('[id$="-view"]').forEach(view => {
                view.style.display = 'none';
            });
            
            // Show selected view
            const view = document.getElementById(viewId + '-view');
            if (view) {
                view.style.display = 'block';
                
                // Load data based on view
                switch (viewId) {
                    case 'attendance':
                        loadAttendanceView();
                        break;
                    case 'marks':
                        loadMarksView();
                        break;
                    case 'fees':
                        loadFeesView();
                        break;
                    case 'dashboard':
                        loadDashboardView();
                        break;
                }
            }
        });
    });
}

// Logout handler
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login.html';
}
