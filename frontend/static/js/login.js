/**
 * ZTNAS Login Page - Complete Authentication Flow
 * Uses centralized auth.js AuthService
 */

// ===== DOM ELEMENTS =====
const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('email');  // Keep ID as 'email' for HTML compatibility
const passwordInput = document.getElementById('password');
const alertBox = document.getElementById('alertBox');
const submitBtn = loginForm?.querySelector('button[type="submit"]');
const btnText = document.getElementById('btnText');

// ===== INITIALIZE AUTH =====

document.addEventListener('DOMContentLoaded', () => {
    // auth is already created as a global in auth.js
    if (typeof auth === 'undefined') {
        console.error('Auth service not loaded - auth.js must be included first');
        return;
    }

    // Never bypass MFA/device checks via auto-redirect.
    // If a stale session exists, clear it and require explicit sign in.
    if (auth.isAuthenticated()) {
        auth.logout();
    }

    // Add form submit handler
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    console.log('✓ Login page initialized');
});

// ===== LOGIN HANDLER =====

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();

    // Get input values
    const username = usernameInput?.value.trim();
    const password = passwordInput?.value.trim();

    // Clear previous alerts
    clearAlert();

    // Validate inputs
    if (!username) {
        showAlert('Please enter your username or email', 'error');
        usernameInput?.focus();
        return;
    }

    if (!password) {
        showAlert('Please enter your password', 'error');
        passwordInput?.focus();
        return;
    }

    // Disable button during submission
    if (submitBtn) {
        submitBtn.disabled = true;
        if (btnText) btnText.textContent = 'Signing in...';
    }

    try {
        // Call auth service login
        const result = await auth.login(username, password);

        if (result.success) {
            const role = result.user?.roles?.[0]?.name?.toLowerCase() || 'student';
            const isAdmin = role === 'admin';
            showAlert(`✓ Welcome ${result.user?.username || 'back'} (${role})!`, 'success');

            // If user has Authenticator App MFA configured, enforce code verification on every login.
            const { totpMethod, methodsFetchOk } = await getEnabledTotpMethod();
            let totpVerifiedThisLogin = false;
            if (!isAdmin) {
                if (!methodsFetchOk) {
                    showAlert('Unable to validate MFA methods right now. Redirecting to MFA setup...', 'error');
                    setTimeout(() => {
                        window.location.href = '/mfa-setup.html';
                    }, 1200);
                    return;
                }

                if (!totpMethod) {
                    showAlert('Authenticator app setup is required. Redirecting to MFA setup...', 'error');
                    setTimeout(() => {
                        window.location.href = '/mfa-setup.html';
                    }, 1200);
                    return;
                }

                showAlert('Authenticator verification required. Enter your app code to continue.', 'success');
                totpVerifiedThisLogin = await verifyTotpForCurrentLogin(totpMethod.id);
                if (!totpVerifiedThisLogin) {
                    auth.logout();
                    showAlert('Login rejected: invalid authenticator code.', 'error');
                    return;
                }
            }

            showAlert('✓ MFA verified. Verifying device...', 'success');

            // Device verification is performed only after MFA success (when configured).
            if (typeof deviceVerification !== 'undefined') {
                const deviceInfo = await deviceVerification.verify();
                console.log('Device verification:', deviceInfo);

                if (deviceInfo?.requires_mfa && !totpVerifiedThisLogin && totpMethod) {
                    auth.logout();
                    showAlert('Login rejected: device requires MFA verification.', 'error');
                    return;
                }
            }

            // Final policy check / redirect handling.
            await checkAndHandleMFASetup();
        } else {
            showAlert(result.error, 'error');
        }
    } finally {
        // Re-enable button
        if (submitBtn) {
            submitBtn.disabled = false;
            if (btnText) btnText.textContent = 'Sign In';
        }
    }
}

/**
 * Return enabled TOTP MFA method for current user, if configured.
 */
async function getEnabledTotpMethod() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/mfa/methods', {
            headers: {
                'Authorization': `Bearer ${auth.getToken()}`
            }
        });

        if (!response.ok) {
            return { totpMethod: null, methodsFetchOk: false };
        }

        const data = await response.json();
        const methods = Array.isArray(data?.methods) ? data.methods : [];

        const totpMethod = methods.find((method) => {
            const rawType = method?.method_type || '';
            const methodType = String(rawType).toUpperCase();
            return method?.is_enabled && methodType.includes('TOTP');
        }) || null;

        return { totpMethod, methodsFetchOk: true };
    } catch (error) {
        console.warn('Could not load MFA methods for login verification:', error);
        return { totpMethod: null, methodsFetchOk: false };
    }
}

/**
 * Prompt and verify authenticator app code for the current login.
 */
async function verifyTotpForCurrentLogin(methodId) {
    for (let attempt = 1; attempt <= 3; attempt++) {
        const input = await promptTotpCodeWithModal(attempt, 3);

        if (input === null) {
            return false;
        }

        const code = input.trim();
        if (!/^\d{6}$/.test(code)) {
            alert('Code must be exactly 6 digits.');
            continue;
        }

        try {
            const response = await fetch('http://localhost:8000/api/v1/mfa/verify', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    method_id: methodId,
                    verification_code: code
                })
            });

            if (response.ok) {
                return true;
            }
        } catch (error) {
            console.error('Error verifying authenticator code:', error);
        }

        alert('Invalid authenticator code. Please try again.');
    }

    return false;
}

/**
 * Render an inline modal to collect the TOTP code.
 * Returns entered code or null if cancelled.
 */
function promptTotpCodeWithModal(attempt, maxAttempts) {
    return new Promise((resolve) => {
        const existing = document.getElementById('totp-login-modal-overlay');
        if (existing) {
            existing.remove();
        }

        const overlay = document.createElement('div');
        overlay.id = 'totp-login-modal-overlay';
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.background = 'rgba(2, 6, 23, 0.72)';
        overlay.style.backdropFilter = 'blur(2px)';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.padding = '20px';

        const card = document.createElement('div');
        card.style.width = '100%';
        card.style.maxWidth = '420px';
        card.style.background = '#0f172a';
        card.style.border = '1px solid #334155';
        card.style.borderRadius = '12px';
        card.style.padding = '20px';
        card.style.boxShadow = '0 20px 50px rgba(0,0,0,0.45)';
        card.style.color = '#e2e8f0';

        card.innerHTML = `
            <h3 style="margin:0 0 8px 0;font-size:18px;">Authenticator Verification</h3>
            <p style="margin:0 0 12px 0;font-size:13px;color:#94a3b8;">Enter the 6-digit code from your authenticator app.</p>
            <p style="margin:0 0 14px 0;font-size:12px;color:#cbd5e1;">Attempt ${attempt} of ${maxAttempts}</p>
            <input id="totp-login-code-input" type="text" maxlength="6" inputmode="numeric" placeholder="000000"
                style="width:100%;padding:12px;border-radius:8px;border:1px solid #475569;background:#020617;color:#e2e8f0;font-size:20px;letter-spacing:4px;text-align:center;" />
            <div style="display:flex;gap:10px;margin-top:16px;">
                <button id="totp-login-cancel-btn" style="flex:1;padding:10px;border-radius:8px;border:1px solid #475569;background:transparent;color:#cbd5e1;cursor:pointer;">Cancel</button>
                <button id="totp-login-verify-btn" style="flex:1;padding:10px;border-radius:8px;border:1px solid #2563eb;background:#2563eb;color:#fff;cursor:pointer;">Verify</button>
            </div>
        `;

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        const input = card.querySelector('#totp-login-code-input');
        const verifyBtn = card.querySelector('#totp-login-verify-btn');
        const cancelBtn = card.querySelector('#totp-login-cancel-btn');

        const cleanup = () => {
            overlay.remove();
        };

        const submit = () => {
            const value = (input.value || '').trim();
            cleanup();
            resolve(value);
        };

        verifyBtn.addEventListener('click', submit);
        cancelBtn.addEventListener('click', () => {
            cleanup();
            resolve(null);
        });
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                submit();
            }
            if (event.key === 'Escape') {
                event.preventDefault();
                cleanup();
                resolve(null);
            }
        });

        setTimeout(() => input.focus(), 0);
    });
}

/**
 * Trigger MFA flow after successful device verification
 */
async function triggerMFAFlow(user) {
    // Hide login form
    if (loginForm) {
        loginForm.style.opacity = '0.5';
        loginForm.style.pointerEvents = 'none';
    }

    // Initialize and show MFA
    if (typeof mfaHandler !== 'undefined') {
        await mfaHandler.initializeMFA(user?.id);
        mfaHandler.displayMFASelection();

        // Wait for MFA completion - check periodically
        const mfaCheckInterval = setInterval(() => {
            if (mfaHandler.isMFAComplete()) {
                clearInterval(mfaCheckInterval);
                console.log('MFA completed, redirecting to dashboard...');
                setTimeout(() => {
                    const dashboard = getDashboardForRole();
                    window.location.href = dashboard;
                }, 500);
            }
        }, 500);

        // Cancel after 10 minutes
        setTimeout(() => {
            clearInterval(mfaCheckInterval);
        }, 600000);
    }
}

/**
 * Check if mandatory MFA setup is required, otherwise redirect to dashboard
 */
async function checkAndHandleMFASetup() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/mfa/status', {
            headers: {
                'Authorization': `Bearer ${auth.getToken()}`
            }
        });

        if (response.ok) {
            const status = await response.json();

            if (status.mfa_required) {
                // Redirect to mandatory MFA setup page
                showAlert('MFA setup is required. Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/mfa-setup.html';
                }, 1200);
            } else {
                // MFA already configured, proceed to dashboard
                showAlert('✓ Redirecting to dashboard...', 'success');
                setTimeout(() => {
                    const dashboard = getDashboardForRole();
                    window.location.href = dashboard;
                }, 1200);
            }
        } else {
            // Fail closed: do not grant dashboard access when MFA status is unknown.
            console.warn('Could not check MFA status, redirecting to MFA setup');
            showAlert('Unable to verify MFA status. Redirecting to MFA setup...', 'error');
            setTimeout(() => {
                window.location.href = '/mfa-setup.html';
            }, 1200);
        }
    } catch (error) {
        console.error('Error checking MFA setup:', error);
        // Fail closed: send user to MFA setup instead of dashboard on errors.
        showAlert('MFA status check failed. Redirecting to MFA setup...', 'error');
        setTimeout(() => {
            window.location.href = '/mfa-setup.html';
        }, 1200);
    }
}

// ===== NAVIGATION =====

/**
 * Navigate to register page
 */
function goToRegister() {
    window.location.href = 'register.html';
}

/**
 * Get the correct dashboard URL for the user's role
 */
function getDashboardForRole() {
    const user = auth.getCurrentUser();
    const role = user?.roles?.[0]?.name?.toLowerCase() || 'student';
    
    const dashboardMap = {
        'admin': '/admin-dashboard.html',
        'hod': '/dashboard-hod.html',
        'dean': '/dashboard-hod.html',
        'faculty': '/dashboard-faculty.html',
        'student': '/dashboard-student.html'
    };
    
    const dashboard = dashboardMap[role] || '/dashboard-student.html';
    console.log(`Routing ${role} to ${dashboard}`);
    return dashboard;
}

/**
 * Demo login for testing
 */
async function demoLogin() {
    // Pre-fill test credentials
    if (usernameInput) usernameInput.value = 'testcollege';
    if (passwordInput) passwordInput.value = 'TestCollege123';

    // Trigger login
    if (loginForm) {
        loginForm.dispatchEvent(new Event('submit'));
    }
}

// ===== UI HELPERS =====

/**
 * Show alert message
 */
function showAlert(message, type = 'success') {
    if (!alertBox) return;

    const alertClass = type === 'success' ? 'alert alert-success' : 'alert alert-error';
    const icon = type === 'success' ? '✓' : '✕';

    alertBox.innerHTML = `
        <div class="${alertClass}">
            <div class="alert-icon">${icon}</div>
            <div class="alert-content">${message}</div>
        </div>
    `;
    alertBox.style.display = 'block';

    // Scroll to alert
    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Clear alert message
 */
function clearAlert() {
    if (alertBox) {
        alertBox.innerHTML = '';
        alertBox.style.display = 'none';
    }
}
