/**
 * Device Verification & Trust Module
 * Checks browser, OS, device fingerprint before allowing access
 */

class DeviceVerification {
    constructor() {
        this.deviceInfo = this.collectDeviceInfo();
        this.trustScore = 0;
        this.needsMFA = false;
    }

    /**
     * Collect device information
     */
    collectDeviceInfo() {
        const ua = navigator.userAgent;
        const browserInfo = this.getBrowserInfo(ua);
        const osInfo = this.getOSInfo(ua);
        
        return {
            device_id: this.getDeviceId(),
            browser: browserInfo.name,
            browser_version: browserInfo.version,
            os: osInfo.name,
            os_version: osInfo.version,
            user_agent: ua,
            timestamp: new Date().toISOString(),
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language
        };
    }

    /**
     * Get or create device ID (stored in localStorage)
     */
    getDeviceId() {
        let deviceId = localStorage.getItem('ztnas_device_id');
        if (!deviceId) {
            deviceId = 'device_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            localStorage.setItem('ztnas_device_id', deviceId);
        }
        return deviceId;
    }

    /**
     * Extract browser information
     */
    getBrowserInfo(ua) {
        let browserName = 'Unknown';
        let browserVersion = 'Unknown';

        if (ua.indexOf('Edg') > -1) {
            browserName = 'Microsoft Edge';
            browserVersion = ua.split('Edg/')[1]?.split(' ')[0] || 'Unknown';
        } else if (ua.indexOf('Chrome') > -1 && ua.indexOf('Chromium') === -1) {
            browserName = 'Google Chrome';
            browserVersion = ua.split('Chrome/')[1]?.split(' ')[0] || 'Unknown';
        } else if (ua.indexOf('Safari') > -1 && ua.indexOf('Chrome') === -1) {
            browserName = 'Safari';
            browserVersion = ua.split('Version/')[1]?.split(' ')[0] || 'Unknown';
        } else if (ua.indexOf('Firefox') > -1) {
            browserName = 'Mozilla Firefox';
            browserVersion = ua.split('Firefox/')[1] || 'Unknown';
        }

        return { name: browserName, version: browserVersion };
    }

    /**
     * Extract OS information
     */
    getOSInfo(ua) {
        let osName = 'Unknown';
        let osVersion = 'Unknown';

        if (ua.indexOf('Win') > -1) {
            osName = 'Windows';
            if (ua.indexOf('Windows NT 10.0') > -1) osVersion = '10/11';
            else if (ua.indexOf('Windows NT 6.3') > -1) osVersion = '8.1';
        } else if (ua.indexOf('Mac') > -1) {
            osName = 'macOS';
            osVersion = ua.split('Mac OS X ')[1]?.split(' ')[0] || 'Unknown';
        } else if (ua.indexOf('Linux') > -1) {
            osName = 'Linux';
            osVersion = 'Unknown';
        } else if (ua.indexOf('iPhone') > -1 || ua.indexOf('iPad') > -1) {
            osName = 'iOS';
            osVersion = ua.split('OS ')[1]?.split(' ')[0] || 'Unknown';
        } else if (ua.indexOf('Android') > -1) {
            osName = 'Android';
            osVersion = ua.split('Android ')[1]?.split(';')[0] || 'Unknown';
        }

        return { name: osName, version: osVersion };
    }

    /**
     * Calculate trust score based on device info
     */
    calculateTrustScore() {
        let score = 100;

        // Check if device is known (has been used before)
        const lastDeviceId = sessionStorage.getItem('ztnas_last_device_id');
        if (lastDeviceId !== this.deviceInfo.device_id) {
            score -= 30; // New device = lower trust
        } else {
            score += 20; // Known device = bonus
        }

        // Save current device
        sessionStorage.setItem('ztnas_last_device_id', this.deviceInfo.device_id);

        // Check browser consistency
        const lastBrowser = sessionStorage.getItem('ztnas_last_browser');
        if (lastBrowser && lastBrowser !== this.deviceInfo.browser) {
            score -= 15; // Different browser = lower trust
        } else {
            score += 10; // Same browser = bonus
        }
        sessionStorage.setItem('ztnas_last_browser', this.deviceInfo.browser);

        // Check OS consistency
        const lastOS = sessionStorage.getItem('ztnas_last_os');
        if (lastOS && lastOS !== this.deviceInfo.os) {
            score -= 20; // Different OS = significant drop
        }
        sessionStorage.setItem('ztnas_last_os', this.deviceInfo.os);

        this.trustScore = Math.max(0, Math.min(100, score));
        return this.trustScore;
    }

    /**
     * Determine if MFA is needed
     */
    determineMFANeeded() {
        // MFA needed if:
        // 1. New device
        // 2. Different browser/OS
        // 3. First login
        // 4. Trust score below 70
        
        const isNewDevice = sessionStorage.getItem('ztnas_last_device_id') === null;
        const isDifferentEnvironment = 
            sessionStorage.getItem('ztnas_last_browser') !== this.deviceInfo.browser ||
            sessionStorage.getItem('ztnas_last_os') !== this.deviceInfo.os;

        this.needsMFA = isNewDevice || isDifferentEnvironment || this.trustScore < 70;
        return this.needsMFA;
    }

    /**
     * Verify device and return trust status
     */
    verify() {
        this.calculateTrustScore();
        this.determineMFANeeded();

        return {
            device_info: this.deviceInfo,
            trust_score: this.trustScore,
            requires_mfa: this.needsMFA,
            trusted_status: this.trustScore >= 80 ? 'TRUSTED' : 'UNTRUSTED'
        };
    }

    /**
     * Display device verification UI
     */
    displayVerificationUI() {
        const html = `
            <div class="device-verification-container" id="deviceVerification">
                <div class="verification-card">
                    <h2>🔐 Device Verification</h2>
                    <div class="verification-details">
                        <div class="detail-row">
                            <span class="label">Browser:</span>
                            <span class="value">${this.deviceInfo.browser} ${this.deviceInfo.browser_version}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Operating System:</span>
                            <span class="value">${this.deviceInfo.os} ${this.deviceInfo.os_version}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Resolution:</span>
                            <span class="value">${this.deviceInfo.screen_resolution}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Timezone:</span>
                            <span class="value">${this.deviceInfo.timezone}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Device ID:</span>
                            <span class="value">${this.deviceInfo.device_id}</span>
                        </div>
                    </div>
                    
                    <div class="trust-score">
                        <p>Device Trust Score: <strong>${this.trustScore}%</strong></p>
                        <div class="trust-bar">
                            <div class="trust-fill" style="width: ${this.trustScore}%"></div>
                        </div>
                        <p class="trust-status">${this.trustScore >= 80 ? '✓ Device Trusted' : '⚠ New/Untrusted Device'}</p>
                    </div>
                    
                    ${this.needsMFA ? `
                        <div class="mfa-notice">
                            <p>🔑 Multi-Factor Authentication Required</p>
                            <small>This is a new or unrecognized device. Please complete additional verification.</small>
                        </div>
                    ` : `
                        <div class="trusted-notice">
                            <p>✓ Device Verified</p>
                            <small>This device has been recognized. You may proceed.</small>
                        </div>
                    `}
                </div>
            </div>
        `;

        // Insert before dashboard content
        const mainContent = document.querySelector('.main-content') || document.body;
        const div = document.createElement('div');
        div.innerHTML = html;
        mainContent.insertBefore(div.firstElementChild, mainContent.firstChild);

        return this.needsMFA;
    }
}

// Create global instance
const deviceVerification = new DeviceVerification();
