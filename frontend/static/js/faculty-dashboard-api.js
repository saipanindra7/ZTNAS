/**
 * ZTNAS Faculty Dashboard API Client
 * Handles all API calls for faculty operations
 */

const API_BASE = 'http://localhost:8000/api/v1';

class FacultyAPIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    /**
     * Get faculty dashboard summary
     */
    async getDashboardSummary() {
        try {
            const response = await fetch(`${API_BASE}/faculty/dashboard`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    await this.refreshToken();
                    return this.getDashboardSummary();
                }
                throw new Error('Failed to fetch dashboard summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard summary:', error);
            return {
                classes_count: 0,
                students_count: 0,
                average_attendance: 0
            };
        }
    }

    /**
     * Get faculty's classes
     */
    async getMyClasses() {
        try {
            const response = await fetch(`${API_BASE}/faculty/my-classes`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch classes');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching classes:', error);
            return [];
        }
    }

    /**
     * Get students in a class
     */
    async getClassStudents(classId) {
        try {
            const response = await fetch(`${API_BASE}/faculty/classes/${classId}/students`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch class students');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching class students:', error);
            return [];
        }
    }

    /**
     * Mark attendance for a class
     */
    async markAttendance(classId, attendanceDate, records) {
        try {
            const response = await fetch(`${API_BASE}/faculty/attendance/mark`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    class_id: classId,
                    attendance_date: attendanceDate,
                    records: records
                })
            });

            if (!response.ok) {
                throw new Error('Failed to mark attendance');
            }

            return await response.json();
        } catch (error) {
            console.error('Error marking attendance:', error);
            throw error;
        }
    }

    /**
     * Enter marks for a class
     */
    async enterMarks(classId, examType, records) {
        try {
            const response = await fetch(`${API_BASE}/faculty/marks/enter`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    class_id: classId,
                    exam_type: examType,
                    records: records
                })
            });

            if (!response.ok) {
                throw new Error('Failed to enter marks');
            }

            return await response.json();
        } catch (error) {
            console.error('Error entering marks:', error);
            throw error;
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
const facultyAPI = new FacultyAPIClient();

/**
 * Dashboard Functions
 */

async function loadFacultyDashboard() {
    showLoading(true);
    try {
        const summary = await facultyAPI.getDashboardSummary();

        safeSetText('classes-count', summary.classes_count ?? 0);
        safeSetText('students-count', summary.students_count ?? 0);

        const avgAttendance = Number(
            summary.average_attendance_percentage ?? summary.average_attendance ?? 0
        );
        safeSetText('avg-attendance', `${avgAttendance.toFixed(2)}%`);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadClassesList() {
    showLoading(true);
    try {
        const classes = await facultyAPI.getMyClasses();
        const tbody = document.getElementById('classes-table-body');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (classes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No classes assigned</td></tr>';
            return;
        }

        classes.forEach(cls => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${cls.name || '—'}</td>
                <td>${cls.subject || cls.code || '—'}</td>
                <td>Sem ${cls.semester ?? '—'}</td>
                <td>${cls.student_count ?? 0}</td>
                <td>
                    <button onclick="selectClassForAttendance(${cls.id})" class="btn-small">Mark Attendance</button>
                    <button onclick="selectClassForMarks(${cls.id})" class="btn-small">Enter Marks</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading classes:', error);
        showNotification('Failed to load classes', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadStudentsForMarking(classId) {
    showLoading(true);
    try {
        const students = await facultyAPI.getClassStudents(classId);
        const tbody = document.getElementById('marking-students-tbody');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        students.forEach(student => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${student.name || student.username || '—'}</td>
                <td>${student.email || '—'}</td>
                <td>
                    <input type="number" placeholder="Marks" class="marks-input" data-student-id="${student.student_id}" min="0" max="100" step="0.5">
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Failed to load students', 'error');
    } finally {
        showLoading(false);
    }
}

// Mark attendance submission
async function submitAttendance() {
    try {
        const classId = document.getElementById('attendance-class-select').value;
        const date = document.getElementById('attendance-date').value;
        
        if (!classId || !date) {
            alert('Please select class and date');
            return;
        }

        const records = [];
        document.querySelectorAll('.attendance-status').forEach(select => {
            const status = select.value;
            if (status) {
                records.push({
                    student_id: parseInt(select.getAttribute('data-student-id')),
                    status: status,
                    remarks: ''
                });
            }
        });

        if (records.length === 0) {
            alert('Please select status for at least one student');
            return;
        }

        showLoading(true);
        const result = await facultyAPI.markAttendance(classId, date, records);
        alert('Attendance marked successfully!');
        
        // Clear the form
        document.getElementById('attendance-class-select').value = '';
        document.getElementById('attendance-date').value = '';
        document.getElementById('attendance-records-tbody').innerHTML = '';
    } catch (error) {
        alert('Failed to submit attendance: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Enter marks submission
async function submitMarks() {
    try {
        const classId = document.getElementById('marks-class-select').value;
        const examType = document.getElementById('exam-type-select').value;
        
        if (!classId || !examType) {
            alert('Please select class and exam type');
            return;
        }

        const records = [];
        document.querySelectorAll('.marks-input').forEach(input => {
            const marks = parseFloat(input.value);
            if (!isNaN(marks) && marks >= 0 && marks <= 100) {
                records.push({
                    student_id: parseInt(input.getAttribute('data-student-id')),
                    marks_obtained: marks,
                    total_marks: 100
                });
            }
        });

        if (records.length === 0) {
            alert('Please enter valid marks for at least one student');
            return;
        }

        showLoading(true);
        const result = await facultyAPI.enterMarks(classId, examType, records);
        alert('Marks entered successfully!');
        
        // Clear the form
        document.getElementById('marks-class-select').value = '';
        document.getElementById('exam-type-select').value = '';
        document.getElementById('marks-table-body').innerHTML = '';
    } catch (error) {
        alert('Failed to submit marks: ' + error.message);
    } finally {
        showLoading(false);
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
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function selectClassForAttendance(classId) {
    document.getElementById('attendance-class-select').value = classId;
    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('attendance-view').style.display = 'block';
}

function selectClassForMarks(classId) {
    document.getElementById('marks-class-select').value = classId;
    document.getElementById('marks-class-select').dispatchEvent(new Event('change'));
    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('marks-view').style.display = 'block';
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login.html';
}
