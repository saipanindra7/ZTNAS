/**
 * ZTNAS Admin Roles & Privileges Management API Client
 * Handles role creation, permission management, and privilege assignment
 */

const API_BASE = 'http://localhost:8000/api/v1';

class AdminRoleAPIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    /**
     * Get all roles with their permissions
     */
    async getRoles() {
        try {
            const response = await fetch(`${API_BASE}/admin/roles`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch roles');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching roles:', error);
            return [];
        }
    }

    /**
     * Create a new role
     */
    async createRole(name, description, isActive = true) {
        try {
            const response = await fetch(`${API_BASE}/admin/roles`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    name: name,
                    description: description,
                    is_active: isActive
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create role');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating role:', error);
            throw error;
        }
    }

    /**
     * Update a role
     */
    async updateRole(roleId, name, description, isActive) {
        try {
            const response = await fetch(`${API_BASE}/admin/roles/${roleId}`, {
                method: 'PUT',
                headers: this.headers,
                body: JSON.stringify({
                    name: name,
                    description: description,
                    is_active: isActive
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update role');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating role:', error);
            throw error;
        }
    }

    /**
     * Delete a role
     */
    async deleteRole(roleId) {
        try {
            const response = await fetch(`${API_BASE}/admin/roles/${roleId}`, {
                method: 'DELETE',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to delete role');
            }

            return await response.json();
        } catch (error) {
            console.error('Error deleting role:', error);
            throw error;
        }
    }

    /**
     * Get all permissions
     */
    async getPermissions() {
        try {
            const response = await fetch(`${API_BASE}/admin/permissions`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch permissions');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching permissions:', error);
            return [];
        }
    }

    /**
     * Create a new permission
     */
    async createPermission(name, description, resource) {
        try {
            const response = await fetch(`${API_BASE}/admin/permissions`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    name: name,
                    description: description,
                    resource: resource
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create permission');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating permission:', error);
            throw error;
        }
    }

    /**
     * Assign permissions to a role
     */
    async assignPermissionsToRole(roleId, permissionIds) {
        try {
            const response = await fetch(`${API_BASE}/admin/roles/${roleId}/permissions`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    role_id: roleId,
                    permission_ids: permissionIds
                })
            });

            if (!response.ok) {
                throw new Error('Failed to assign permissions');
            }

            return await response.json();
        } catch (error) {
            console.error('Error assigning permissions:', error);
            throw error;
        }
    }

    /**
     * Assign roles to a user
     */
    async assignRolesToUser(userId, roleIds) {
        try {
            const response = await fetch(`${API_BASE}/admin/users/${userId}/roles`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    role_ids: roleIds
                })
            });

            if (!response.ok) {
                throw new Error('Failed to assign roles');
            }

            return await response.json();
        } catch (error) {
            console.error('Error assigning roles:', error);
            throw error;
        }
    }

    /**
     * Get roles assigned to a user
     */
    async getUserRoles(userId) {
        try {
            const response = await fetch(`${API_BASE}/admin/users/${userId}/roles`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user roles');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching user roles:', error);
            return [];
        }
    }

    /**
     * Get privilege changes audit log
     */
    async getPrivilegeChanges(days = 30) {
        try {
            const response = await fetch(`${API_BASE}/admin/privilege-changes?days=${days}`, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Failed to fetch privilege changes');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching privilege changes:', error);
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
const adminRoleAPI = new AdminRoleAPIClient();

/**
 * Dashboard Functions
 */

async function loadRolesList() {
    showLoading(true);
    try {
        const roles = await adminRoleAPI.getRoles();
        const tbody = document.getElementById('roles-table-body');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (roles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No roles found</td></tr>';
            return;
        }

        roles.forEach(role => {
            const row = document.createElement('tr');
            const statusBadge = role.is_active ? 
                '<span class="badge-active">Active</span>' : 
                '<span class="badge-inactive">Inactive</span>';
            
            row.innerHTML = `
                <td>${role.name}</td>
                <td>${role.description}</td>
                <td>${role.user_count}</td>
                <td>${role.permissions.length}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn-small" onclick="editRole(${role.id})">Edit</button>
                    <button class="btn-small" onclick="manageRolePermissions(${role.id})">Permissions</button>
                    <button class="btn-small btn-danger" onclick="deleteRole(${role.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading roles:', error);
        showNotification('Failed to load roles', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadPermissionsList() {
    showLoading(true);
    try {
        const permissions = await adminRoleAPI.getPermissions();
        const tbody = document.getElementById('permissions-table-body');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (permissions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No permissions found</td></tr>';
            return;
        }

        const groupedByResource = {};
        permissions.forEach(perm => {
            if (!groupedByResource[perm.resource]) {
                groupedByResource[perm.resource] = [];
            }
            groupedByResource[perm.resource].push(perm);
        });

        Object.entries(groupedByResource).forEach(([resource, perms]) => {
            perms.forEach((perm, index) => {
                const row = document.createElement('tr');
                const resourceCell = index === 0 ? 
                    `<td rowspan="${perms.length}">${resource}</td>` : '';
                
                row.innerHTML = `
                    ${resourceCell}
                    <td>${perm.name}</td>
                    <td>${perm.description}</td>
                    <td>
                        <button class="btn-small">Edit</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
    } catch (error) {
        console.error('Error loading permissions:', error);
        showNotification('Failed to load permissions', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadPrivilegeChanges() {
    showLoading(true);
    try {
        const changes = await adminRoleAPI.getPrivilegeChanges(30);
        const tbody = document.getElementById('privilege-changes-tbody');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (changes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No privilege changes</td></tr>';
            return;
        }

        changes.slice(0, 50).forEach(change => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${change.timestamp}</td>
                <td>${change.admin}</td>
                <td>${change.action}</td>
                <td>${change.resource_type}</td>
                <td>${change.resource_id}</td>
                <td><span class="status-${change.status.toLowerCase()}">${change.status}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading privilege changes:', error);
        showNotification('Failed to load privilege changes', 'error');
    } finally {
        showLoading(false);
    }
}

// Edit role
async function editRole(roleId) {
    const roles = await adminRoleAPI.getRoles();
    const role = roles.find(r => r.id === roleId);
    
    if (!role) return;
    
    const newName = prompt('Role Name:', role.name);
    if (newName === null) return;
    
    const newDesc = prompt('Description:', role.description);
    if (newDesc === null) return;
    
    showLoading(true);
    try {
        const result = await adminRoleAPI.updateRole(roleId, newName, newDesc, role.is_active);
        showNotification('Role updated successfully', 'success');
        loadRolesList();
    } catch (error) {
        showNotification('Failed to update role: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete role
async function deleteRole(roleId) {
    if (confirm('Are you sure you want to delete this role? This action cannot be undone.')) {
        showLoading(true);
        try {
            const result = await adminRoleAPI.deleteRole(roleId);
            showNotification(result.message, 'success');
            loadRolesList();
        } catch (error) {
            showNotification('Failed to delete role: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }
}

// Manage permissions for a role
async function manageRolePermissions(roleId) {
    const roles = await adminRoleAPI.getRoles();
    const role = roles.find(r => r.id === roleId);
    
    if (!role) return;
    
    const allPermissions = await adminRoleAPI.getPermissions();
    
    // Show permission selection modal
    showPermissionModal(roleId, role, allPermissions);
}

function showPermissionModal(roleId, role, allPermissions) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        padding: 30px;
        border-radius: 10px;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    const title = document.createElement('h3');
    title.textContent = `Manage Permissions for ${role.name}`;
    content.appendChild(title);
    
    const permList = document.createElement('div');
    const currentPermIds = role.permissions.map(p => p.id);
    
    allPermissions.forEach(perm => {
        const label = document.createElement('label');
        label.style.cssText = 'display: block; margin: 10px 0; cursor: pointer;';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = perm.id;
        checkbox.checked = currentPermIds.includes(perm.id);
        
        const span = document.createElement('span');
        span.textContent = ` ${perm.name} (${perm.resource})`;
        
        label.appendChild(checkbox);
        label.appendChild(span);
        permList.appendChild(label);
    });
    
    content.appendChild(permList);
    
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.className = 'btn-primary';
    saveBtn.onclick = async () => {
        const selectedIds = [];
        permList.querySelectorAll('input:checked').forEach(checkbox => {
            selectedIds.push(parseInt(checkbox.value));
        });
        
        showLoading(true);
        try {
            await adminRoleAPI.assignPermissionsToRole(roleId, selectedIds);
            showNotification('Permissions updated successfully', 'success');
            modal.remove();
            loadRolesList();
        } catch (error) {
            showNotification('Failed to update permissions: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    };
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'btn-secondary';
    cancelBtn.style.marginLeft = '10px';
    cancelBtn.onclick = () => modal.remove();
    
    content.appendChild(saveBtn);
    content.appendChild(cancelBtn);
    
    modal.appendChild(content);
    document.body.appendChild(modal);
}

// Helper functions
function showLoading(show) {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
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
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    setupAdminNavigation();
    loadRolesList();
});

function setupAdminNavigation() {
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
                    case 'roles':
                        loadRolesList();
                        break;
                    case 'permissions':
                        loadPermissionsList();
                        break;
                    case 'audit':
                        loadPrivilegeChanges();
                        break;
                }
            }
        });
    });
}
