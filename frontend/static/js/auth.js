/**
 * ZTNAS Authentication Utility Module
 * Centralized authentication service for login, registration, token management
 */

class AuthService {
    constructor() {
        this.API_BASE = 'http://localhost:8000/api/v1';
        this.TOKEN_KEY = 'access_token';
        this.REFRESH_TOKEN_KEY = 'refresh_token';
        this.USER_KEY = 'user';
        this.TOKEN_EXPIRY_KEY = 'token_expiry';
    }

    // ===== AUTHENTICATION STATE =====

    /**
     * Get current authentication token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    /**
     * Get refresh token
     */
    getRefreshToken() {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;

        // Treat expired tokens as unauthenticated and clean stale state.
        if (this.isTokenExpired()) {
            this.logout();
            return false;
        }

        return true;
    }

    /**
     * Get current user object
     */
    getCurrentUser() {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    }

    /**
     * Get user role
     */
    getUserRole() {
        const user = this.getCurrentUser();
        return user?.role || user?.roles?.[0]?.name?.toLowerCase() || 'student';
    }

    // ===== LOGIN / REGISTER / LOGOUT =====

    /**
     * Login user with credentials
     * @param {string} username - Username or email
     * @param {string} password - Password
     * @param {string} deviceName - Optional device name for tracking
     * @returns {Promise<{success: boolean, user: Object, error: string}>}
     */
    async login(username, password, deviceName = null) {
        try {
            const response = await fetch(`${this.API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    password,
                    device_name: deviceName || 'Web Browser'
                })
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    error: this._parseLoginError(data.detail || 'Login failed')
                };
            }

            // Store tokens
            localStorage.setItem(this.TOKEN_KEY, data.access_token);
            localStorage.setItem(this.REFRESH_TOKEN_KEY, data.refresh_token);
            
            // Store token expiry
            const expiryTime = new Date().getTime() + (data.expires_in * 1000);
            localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime);

            // Fetch user data from /auth/me endpoint
            const user = await this.fetchCurrentUser();
            if (user) {
                localStorage.setItem(this.USER_KEY, JSON.stringify(user));
                return { success: true, user };
            } else {
                return {
                    success: true,
                    user: null,
                    warning: 'Login successful but could not fetch user details'
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: 'Network error. Make sure the backend is running.'
            };
        }
    }

    /**
     * Register new user
     * @param {Object} userData - {email, username, password, firstName, lastName}
     * @returns {Promise<{success: boolean, error: string}>}
     */
    async register(userData) {
        try {
            const { email, username, password, firstName = '', lastName = '' } = userData;

            // Validate required fields
            if (!email || !username || !password) {
                return { success: false, error: 'Email, username, and password are required' };
            }

            const response = await fetch(`${this.API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    username,
                    password,
                    first_name: firstName,
                    last_name: lastName
                })
            });

            if (!response.ok) {
                const data = await response.json();
                return {
                    success: false,
                    error: data.detail || 'Registration failed'
                };
            }

            return { success: true };
        } catch (error) {
            console.error('Registration error:', error);
            return {
                success: false,
                error: 'Network error. Make sure the backend is running.'
            };
        }
    }

    /**
     * Logout user
     */
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    }

    // ===== USER DATA =====

    /**
     * Fetch current user details from backend
     */
    async fetchCurrentUser() {
        try {
            const token = this.getToken();
            if (!token) return null;

            const response = await fetch(`${this.API_BASE}/auth/me`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                return await response.json();
            } else if (response.status === 401) {
                // Token expired or invalid
                await this.refreshAccessToken();
                // Retry with new token
                const newToken = this.getToken();
                if (newToken) {
                    const retryResponse = await fetch(`${this.API_BASE}/auth/me`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${newToken}`
                        }
                    });
                    if (retryResponse.ok) {
                        return await retryResponse.json();
                    }
                }
                return null;
            }
            return null;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            return null;
        }
    }

    // ===== TOKEN MANAGEMENT =====

    /**
     * Check if token is expired
     */
    isTokenExpired() {
        const expiryTime = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
        if (!expiryTime) return true;
        return new Date().getTime() > parseInt(expiryTime);
    }

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        try {
            const refreshToken = this.getRefreshToken();
            if (!refreshToken) {
                this.logout();
                return false;
            }

            const response = await fetch(`${this.API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) {
                // Refresh token expired, need to login again
                this.logout();
                return false;
            }

            const data = await response.json();
            localStorage.setItem(this.TOKEN_KEY, data.access_token);
            localStorage.setItem(this.REFRESH_TOKEN_KEY, data.refresh_token);
            
            const expiryTime = new Date().getTime() + (data.expires_in * 1000);
            localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime);

            return true;
        } catch (error) {
            console.error('Token refresh error:', error);
            this.logout();
            return false;
        }
    }

    // ===== PROTECTED API CALLS =====

    /**
     * Make authenticated API call
     */
    async fetchAPI(endpoint, method = 'GET', body = null) {
        const token = this.getToken();

        // Check if token needs refresh
        if (this.isTokenExpired()) {
            const refreshed = await this.refreshAccessToken();
            if (!refreshed) {
                // Token refresh failed, redirect to login
                this.logout();
                window.location.href = 'login.html';
                return null;
            }
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.API_BASE}${endpoint}`, options);

            if (response.status === 401) {
                // Unauthorized - token invalid or expired
                this.logout();
                window.location.href = 'login.html';
                return null;
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // ===== HELPERS =====

    /**
     * Parse login errors for user-friendly messages
     */
    _parseLoginError(errorMsg) {
        if (errorMsg && typeof errorMsg === 'object') {
            const code = errorMsg.code || '';
            const message = errorMsg.message || 'Login failed';

            if (code === 'MFA_REQUIRED') {
                return 'MFA setup is required before accessing the dashboard.';
            }

            return message;
        }

        const msg = String(errorMsg || 'Login failed');

        if (msg.includes('Invalid credentials') || msg.includes('password')) {
            return 'Invalid username or password. Please check and try again.';
        }
        if (msg.includes('email') || msg.includes('not found')) {
            return 'Username not found. Please check or register a new account.';
        }
        if (msg.includes('locked')) {
            return 'Account temporarily locked due to too many failed attempts. Please try again later.';
        }
        if (msg.includes('inactive') || msg.includes('disabled')) {
            return 'Your account is inactive. Please contact administration.';
        }
        return msg;
    }

    /**
     * Validate password strength
     */
    validatePasswordStrength(password) {
        const issues = [];
        
        if (password.length < 8) issues.push('at least 8 characters');
        if (!/[A-Z]/.test(password)) issues.push('uppercase letter');
        if (!/[a-z]/.test(password)) issues.push('lowercase letter');
        if (!/\d/.test(password)) issues.push('number');
        if (!/[!@#$%^&*]/.test(password)) issues.push('special character (!@#$%^&*)');

        return {
            isStrong: issues.length === 0,
            issues,
            message: issues.length === 0 
                ? 'Password strength is good' 
                : `Password must contain: ${issues.join(', ')}`
        };
    }

    /**
     * Check if password matches
     */
    passwordsMatch(password, confirm) {
        return password === confirm;
    }
}

// Create global instance
const auth = new AuthService();
