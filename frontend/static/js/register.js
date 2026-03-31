/**
 * ZTNAS Register Page - User Registration Flow
 * Uses centralized auth.js AuthService
 */

// ===== DOM ELEMENTS =====
const registerForm = document.getElementById('registerForm');
const nameInput = document.getElementById('name');
const firstNameInput = null;  // Extract from name input
const lastNameInput = null;
const emailInput = document.getElementById('email');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const confirmInput = document.getElementById('confirm');
const agreeCheckbox = document.getElementById('agree');
const alertBox = document.getElementById('alertBox');
const submitBtn = registerForm?.querySelector('button[type="submit"]');
const strengthBars = document.querySelectorAll('.strength-bar');

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    // Wait for auth to be ready
    if (typeof auth === 'undefined') {
        console.error('Auth service not loaded');
        return;
    }

    // Never reuse an existing session on register page. Registration must be followed
    // by a fresh login so device verification + MFA checks run.
    if (auth.isAuthenticated()) {
        auth.logout();
    }

    // Add form submit handler
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Add password input listener for strength indicator
    if (passwordInput) {
        passwordInput.addEventListener('input', updatePasswordStrength);
    }

    console.log('✓ Register page initialized');
});

// ===== REGISTRATION HANDLER =====

/**
 * Handle registration form submission
 */
async function handleRegister(e) {
    e.preventDefault();

    // Get input values
    const fullName = nameInput?.value.trim();
    const email = emailInput?.value.trim();
    const username = usernameInput?.value.trim();
    const password = passwordInput?.value.trim();
    const confirmPassword = confirmInput?.value.trim();
    const agreedToTerms = agreeCheckbox?.checked;

    // Clear previous alerts
    clearAlert();

    // ===== VALIDATION =====

    // Required fields
    if (!fullName) {
        showAlert('Please enter your full name', 'error');
        nameInput?.focus();
        return;
    }

    if (!email) {
        showAlert('Please enter your email address', 'error');
        emailInput?.focus();
        return;
    }

    if (!username) {
        showAlert('Please enter a username', 'error');
        usernameInput?.focus();
        return;
    }

    if (!password) {
        showAlert('Please enter a password', 'error');
        passwordInput?.focus();
        return;
    }

    if (!confirmPassword) {
        showAlert('Please confirm your password', 'error');
        confirmInput?.focus();
        return;
    }

    if (!agreedToTerms) {
        showAlert('Please agree to the Terms of Service to continue', 'error');
        agreeCheckbox?.focus();
        return;
    }

    // Password matching
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        confirmInput?.focus();
        return;
    }

    // Password strength
    const strengthCheck = auth.validatePasswordStrength(password);
    if (!strengthCheck.isStrong) {
        showAlert(strengthCheck.message, 'error');
        passwordInput?.focus();
        return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        emailInput?.focus();
        return;
    }

    // ===== SUBMIT =====

    // Disable button during submission
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating Account...';
    }

    try {
        // Split name into first and last
        const nameParts = fullName.trim().split(/\s+/);
        const firstName = nameParts[0];
        const lastName = nameParts.length > 1 ? nameParts.slice(1).join(' ') : '';

        // Call auth service register
        const result = await auth.register({
            email,
            username,
            password,
            firstName,
            lastName
        });

        if (result.success) {
            // Ensure no stale/previous session survives registration flow.
            auth.logout();

            showAlert(
                '✓ Account created successfully! Redirecting to login...',
                'success'
            );

            // Clear form
            if (registerForm) registerForm.reset();
            clearPasswordStrength();

            // Redirect after brief delay
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 1500);
        } else {
            showAlert(result.error, 'error');
        }
    } finally {
        // Re-enable button
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Account';
        }
    }
}

// ===== PASSWORD STRENGTH =====

/**
 * Update password strength indicator as user types
 */
function updatePasswordStrength() {
    const password = passwordInput?.value || '';
    const strengthCheck = auth.validatePasswordStrength(password);
    const strength = strengthCheck.issues.length;

    // Calculate strength level (0-4)
    let level = 4 - strength;
    if (!password) level = 0;

    // Update bars
    strengthBars.forEach((bar, index) => {
        bar.className = 'strength-bar';  // Reset
        
        if (index < level) {
            if (level === 1) bar.classList.add('weak');
            else if (level === 2) bar.classList.add('fair');
            else if (level === 3) bar.classList.add('good');
            else if (level === 4) bar.classList.add('strong');
        }
    });
}

/**
 * Clear password strength indicator
 */
function clearPasswordStrength() {
    strengthBars.forEach(bar => {
        bar.className = 'strength-bar';
    });
}

// ===== NAVIGATION =====

/**
 * Navigate to login page
 */
function goToLogin() {
    window.location.href = '/login.html';
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
