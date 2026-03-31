/**
 * Multi-Factor Authentication (MFA) Module
 * Supports TOTP, Email OTP, and other MFA methods
 */

class MFAHandler {
    constructor() {
        this.mfaMethods = [];
        this.selectedMethod = null;
        this.mfaComplete = false;
    }

    /**
     * Initialize MFA for user
     */
    async initializeMFA(userId) {
        try {
            // In a real system, this would fetch available MFA methods from backend
            // For now, we'll simulate common methods
            this.mfaMethods = [
                { id: 'email', name: 'Email OTP', icon: '📧', available: true },
                { id: 'totp', name: 'Authenticator App', icon: '🔐', available: true },
                { id: 'sms', name: 'SMS OTP', icon: '📱', available: false }
            ];
            
            return this.mfaMethods;
        } catch (error) {
            console.error('Failed to initialize MFA:', error);
            return [];
        }
    }

    /**
     * Display MFA method selection UI
     */
    displayMFASelection() {
        const html = `
            <div class="mfa-container" id="mfaContainer">
                <div class="mfa-card">
                    <h2>🔐 Multi-Factor Authentication</h2>
                    <p>Choose a verification method to secure your account:</p>
                    
                    <div class="mfa-methods">
                        ${this.mfaMethods.map(method => `
                            <button 
                                class="mfa-method ${!method.available ? 'disabled' : ''}" 
                                ${!method.available ? 'disabled' : ''}
                                onclick="mfaHandler.selectMethod('${method.id}')"
                            >
                                <span class="method-icon">${method.icon}</span>
                                <span class="method-name">${method.name}</span>
                                ${!method.available ? '<span class="coming-soon">Coming Soon</span>' : ''}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        const mainContent = document.querySelector('.main-content') || document.body;
        const div = document.createElement('div');
        div.innerHTML = html;
        mainContent.insertBefore(div.firstElementChild, mainContent.firstChild);
    }

    /**
     * Select MFA method and show verification UI
     */
    selectMethod(methodId) {
        this.selectedMethod = methodId;
        this.displayMFAVerification(methodId);
    }

    /**
     * Display MFA verification UI based on method
     */
    displayMFAVerification(methodId) {
        let html = '';

        if (methodId === 'email') {
            html = `
                <div class="mfa-verification" id="mfaVerification">
                    <div class="mfa-card">
                        <h2>📧 Email Verification</h2>
                        <p>We've sent a verification code to your email address.</p>
                        <p>Check your inbox and enter the code below:</p>
                        
                        <div class="code-input-container">
                            <input 
                                type="text" 
                                id="mfaCode" 
                                class="mfa-code-input" 
                                placeholder="000000" 
                                maxlength="6"
                                autocomplete="off"
                            />
                        </div>
                        
                        <button class="btn btn-primary" onclick="mfaHandler.verifyMFACode()">
                            Verify Code
                        </button>
                        
                        <button class="btn btn-secondary" onclick="mfaHandler.displayMFASelection()">
                            Try Different Method
                        </button>
                        
                        <p class="resend-note">
                            Didn't receive the code? 
                            <a href="#" onclick="mfaHandler.resendCode()">Resend</a>
                        </p>
                    </div>
                </div>
            `;
        } else if (methodId === 'totp') {
            html = `
                <div class="mfa-verification" id="mfaVerification">
                    <div class="mfa-card">
                        <h2>🔐 Authenticator App</h2>
                        <p>Enter the 6-digit code from your authenticator app:</p>
                        
                        <div class="code-input-container">
                            <input 
                                type="text" 
                                id="mfaCode" 
                                class="mfa-code-input" 
                                placeholder="000000" 
                                maxlength="6"
                                autocomplete="off"
                            />
                        </div>
                        
                        <button class="btn btn-primary" onclick="mfaHandler.verifyMFACode()">
                            Verify Code
                        </button>
                        
                        <button class="btn btn-secondary" onclick="mfaHandler.displayMFASelection()">
                            Try Different Method
                        </button>
                    </div>
                </div>
            `;
        }

        // Replace the MFA selection with verification UI
        const mfaContainer = document.getElementById('mfaContainer');
        if (mfaContainer) {
            mfaContainer.innerHTML = html;
        }

        // Focus on code input
        setTimeout(() => {
            document.getElementById('mfaCode')?.focus();
        }, 100);
    }

    /**
     * Verify MFA code
     */
    async verifyMFACode() {
        const codeInput = document.getElementById('mfaCode');
        const code = codeInput.value.trim();

        if (!code || code.length !== 6) {
            alert('Please enter a valid 6-digit code');
            return;
        }

        try {
            // Simulate MFA verification
            // In a real system, this would send to backend
            console.log('Verifying MFA code:', code);

            // Show loading state
            codeInput.disabled = true;
            const buttons = document.querySelectorAll('.mfa-verification button');
            buttons.forEach(b => b.disabled = true);

            // Simulate verification delay
            await new Promise(resolve => setTimeout(resolve, 1500));

            // For demo, accept any 6-digit code
            if (/^\d{6}$/.test(code)) {
                this.mfaComplete = true;
                this.completeMFA();
            } else {
                alert('Invalid code. Please try again.');
                codeInput.disabled = false;
                buttons.forEach(b => b.disabled = false);
                codeInput.value = '';
                codeInput.focus();
            }
        } catch (error) {
            console.error('MFA verification failed:', error);
            alert('Verification failed. Please try again.');
            codeInput.disabled = false;
            const buttons = document.querySelectorAll('.mfa-verification button');
            buttons.forEach(b => b.disabled = false);
        }
    }

    /**
     * Resend MFA code
     */
    async resendCode() {
        console.log('Resending MFA code via:', this.selectedMethod);
        alert('Verification code sent to your ' + (this.selectedMethod === 'email' ? 'email' : 'registered device'));
    }

    /**
     * Mark MFA as complete and show dashboard
     */
    completeMFA() {
        // Remove MFA container
        const mfaContainer = document.getElementById('mfaContainer');
        if (mfaContainer) {
            mfaContainer.style.transition = 'opacity 0.3s ease';
            mfaContainer.style.opacity = '0';
            setTimeout(() => {
                mfaContainer.remove();
                // Show dashboard
                document.getElementById('dashboard-view')?.classList.add('active');
            }, 300);
        }

        // Save MFA completion status
        sessionStorage.setItem('ztnas_mfa_complete', 'true');
    }

    /**
     * Check if MFA has been completed in this session
     */
    isMFAComplete() {
        return sessionStorage.getItem('ztnas_mfa_complete') === 'true';
    }
}

// Create global instance
const mfaHandler = new MFAHandler();
