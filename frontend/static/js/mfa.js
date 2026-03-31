// MFA Frontend JavaScript - Multi-Factor Authentication
// Uses centralized auth service

let currentMethod = null;
let pictureImageData = null;
let pictureMethodId = null;
let pictureTaps = [];
let verifyTaps = [];

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    // Wait for auth to be ready
    if (typeof auth === 'undefined') {
        console.error('Auth service not loaded');
        return;
    }
    
    if (!auth.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }
    
    console.log('✓ MFA page loaded for user:', auth.getCurrentUser()?.username);
});

// ==================== Setup Panel Management ====================

function selectMethod(method) {
    currentMethod = method;
    closeAllPanels();
    
    const panelId = `${method}-setup`;
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.classList.remove('hidden');
        
        // Initialize method-specific setup
        if (method === 'totp') initTOTPSetup();
        if (method === 'picture') initPicturePasswordSetup();
    }
}

function closeSetup() {
    closeAllPanels();
    currentMethod = null;
}

function closeAllPanels() {
    document.querySelectorAll('.setup-panel').forEach(panel => {
        panel.classList.add('hidden');
    });
}

// ==================== Logout ======================

function logoutUser() {
    if (confirm('Are you sure you want to logout?')) {
        auth.logout();
        window.location.href = 'login.html';
    }
}

// ==================== TOTP Setup ====================

async function initTOTPSetup() {
    if (!auth.isAuthenticated()) {
        alert('Not authenticated. Please log in first.');
        window.location.href = 'login.html';
        return;
    }
    
    try {
        const response = await auth.fetchAPI('/mfa/totp/setup', 'POST');
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error('Failed to setup TOTP');
        }
        
        const data = await response.json();
        
        // Display QR code
        document.getElementById('totp-qr').innerHTML = `<img src="${data.qr_code_url}" alt="QR Code">`;
        document.getElementById('totp-secret').textContent = data.manual_entry_key;
        
        // Store secret for verification
        window.totpSecret = data.secret;
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to setup TOTP: ' + error.message);
    }
}

async function verifyTOTP() {
    const code = document.getElementById('totp-code').value;
    
    if (!/^\d{6}$/.test(code)) {
        alert('Please enter a valid 6-digit code');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/totp/enroll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                totp_code: code,
                secret: window.totpSecret
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Verification failed');
        }
        
        alert('TOTP MFA successfully enabled!');
        closeSetup();
        loadMFAMethods();
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to verify TOTP: ' + error.message);
    }
}

// ==================== SMS OTP Setup ====================

async function startSMSOTP() {
    const phone = document.getElementById('sms-phone').value;
    
    if (!/^\+?1?\d{9,15}$/.test(phone)) {
        alert('Please enter a valid phone number');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/sms/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ phone_number: phone })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send SMS OTP');
        }
        
        window.smsMethodId = (await response.json()).method_id;
        document.getElementById('sms-verify-step').classList.remove('hidden');
    } catch (error) {
        alert('Failed to send SMS: ' + error.message);
    }
}

async function verifySMSOTP() {
    const code = document.getElementById('sms-code').value;
    
    if (!/^\d{6}$/.test(code)) {
        alert('Please enter a valid 6-digit code');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/otp/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                method_id: window.smsMethodId,
                otp_code: code
            })
        });
        
        if (!response.ok) {
            throw new Error('Invalid OTP code');
        }
        
        alert('SMS OTP MFA successfully enabled!');
        closeSetup();
        loadMFAMethods();
    } catch (error) {
        alert('Failed to verify SMS OTP: ' + error.message);
    }
}

async function resendSMSOTP() {
    try {
        await fetch(`${API_BASE}/mfa/otp/resend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ method_id: window.smsMethodId })
        });
        alert('New SMS OTP sent');
    } catch (error) {
        alert('Failed to resend SMS: ' + error.message);
    }
}

// ==================== Email OTP Setup ====================

async function startEmailOTP() {
    try {
        const response = await fetch(`${API_BASE}/mfa/email/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error('Failed to send email OTP');
        }
        
        window.emailMethodId = (await response.json()).method_id;
        document.getElementById('email-verify-step').classList.remove('hidden');
    } catch (error) {
        alert('Failed to send email: ' + error.message);
    }
}

async function verifyEmailOTP() {
    const code = document.getElementById('email-code').value;
    
    if (!/^\d{6}$/.test(code)) {
        alert('Please enter a valid 6-digit code');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/otp/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                method_id: window.emailMethodId,
                otp_code: code
            })
        });
        
        if (!response.ok) {
            throw new Error('Invalid OTP code');
        }
        
        alert('Email OTP MFA successfully enabled!');
        closeSetup();
        loadMFAMethods();
    } catch (error) {
        alert('Failed to verify email OTP: ' + error.message);
    }
}

async function resendEmailOTP() {
    try {
        await fetch(`${API_BASE}/mfa/otp/resend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ method_id: window.emailMethodId })
        });
        alert('New email OTP sent');
    } catch (error) {
        alert('Failed to resend email: ' + error.message);
    }
}

// ==================== Picture Password Setup ====================

function initPicturePasswordSetup() {
    pictureTaps = [];
    verifyTaps = [];
    pictureImageData = null;
    pictureMethodId = null;
}

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file
    if (file.size > 5 * 1024 * 1024) {
        alert('File is too large. Max 5MB');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        pictureImageData = e.target.result;
        
        // Display preview
        const preview = document.getElementById('image-preview');
        preview.innerHTML = `<img src="${pictureImageData}" alt="Selected image">`;
        preview.classList.remove('hidden');
        
        // Upload to backend
        try {
            const base64Data = pictureImageData.split(',')[1];
            const format = file.type.split('/')[1].toLowerCase();
            
            const response = await fetch(`${API_BASE}/mfa/picture/setup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    image_data: base64Data,
                    image_format: format
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to upload image');
            }
            
            const data = await response.json();
            pictureMethodId = data.image_hash;
            
            // Move to tap definition step
            document.getElementById('picture-upload-step').classList.add('hidden');
            document.getElementById('picture-taps-step').classList.remove('hidden');
            
            // Initialize canvas
            setupPictureCanvas();
        } catch (error) {
            alert('Failed to upload image: ' + error.message);
        }
    };
    reader.readAsDataURL(file);
}

function setupPictureCanvas() {
    const canvas = document.getElementById('picture-canvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = () => {
        canvas.width = Math.min(img.width, 600);
        canvas.height = img.height * (canvas.width / img.width);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Add click handler
        canvas.addEventListener('click', (e) => addPictureTap(e, canvas, pictureTaps, 'tap-count', 'tap-instructions'));
    };
    img.src = pictureImageData;
}

function addPictureTap(event, canvas, taps, countId, instructionsId) {
    if (taps.length >= 5) {
        alert('Maximum 5 taps allowed');
        return;
    }
    
    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const sequence = taps.length + 1;
    
    taps.push({ x, y, sequence });
    
    // Update UI
    document.getElementById(countId).textContent = taps.length;
    
    // Draw tap point on canvas
    drawTapPoint(canvas, x, y, sequence);
    
    // Enable confirm button if enough taps
    if (taps.length >= 3) {
        document.getElementById('confirm-taps-btn').disabled = false;
    }
}

function drawTapPoint(canvas, x, y, sequence) {
    const ctx = canvas.getContext('2d');
    const radius = 20;
    
    // Draw circle
    ctx.fillStyle = 'rgba(0, 102, 204, 0.5)';
    ctx.beginPath();
    ctx.arc(x * canvas.width, y * canvas.height, radius, 0, 2 * Math.PI);
    ctx.fill();
    
    // Draw number
    ctx.fillStyle = 'white';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(sequence, x * canvas.width, y * canvas.height);
}

function resetPictureTaps() {
    pictureTaps = [];
    document.getElementById('tap-count').textContent = '0';
    document.getElementById('confirm-taps-btn').disabled = true;
    setupPictureCanvas(); // Redraw
}

async function confirmPicturePassword() {
    if (pictureTaps.length < 3) {
        alert('Please define at least 3 tap points');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/picture/define`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                image_hash: pictureMethodId,
                taps: pictureTaps,
                tolerance_radius: 0.05
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save tap pattern');
        }
        
        const data = await response.json();
        pictureMethodId = data.method_id;
        
        // Move to verification step
        document.getElementById('picture-taps-step').classList.add('hidden');
        document.getElementById('picture-verify-step').classList.remove('hidden');
        
        setupPictureVerifyCanvas();
    } catch (error) {
        alert('Failed to save pattern: ' + error.message);
    }
}

function setupPictureVerifyCanvas() {
    const canvas = document.getElementById('picture-verify-canvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = () => {
        canvas.width = Math.min(img.width, 600);
        canvas.height = img.height * (canvas.width / img.width);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        canvas.addEventListener('click', (e) => addPictureTap(e, canvas, verifyTaps, 'verify-tap-count', null));
    };
    img.src = pictureImageData;
}

function resetPictureVerifyTaps() {
    verifyTaps = [];
    document.getElementById('verify-tap-count').textContent = '0';
    setupPictureVerifyCanvas();
}

async function verifyPicturePassword() {
    if (verifyTaps.length !== pictureTaps.length) {
        alert(`Please tap exactly ${pictureTaps.length} points`);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mfa/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                method_id: pictureMethodId,
                verification_data: { taps: verifyTaps }
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Verification failed');
        }
        
        alert('Picture Password MFA successfully enabled!');
        closeSetup();
        loadMFAMethods();
    } catch (error) {
        alert('Failed to verify pattern: ' + error.message);
    }
}

// ==================== Backup Codes ====================

async function generateBackupCodes() {
    try {
        const response = await fetch(`${API_BASE}/mfa/backup-codes/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate backup codes');
        }
        
        const data = await response.json();
        
        // Display codes
        const codesDisplay = document.getElementById('backup-codes-display');
        codesDisplay.innerHTML = data.codes.map(code => `<code>${code}</code>`).join('');
        window.backupCodes = data.codes;
    } catch (error) {
        alert('Failed to generate backup codes: ' + error.message);
    }
}

function copyBackupCodes() {
    const codes = window.backupCodes.join('\n');
    navigator.clipboard.writeText(codes).then(() => {
        alert('Backup codes copied to clipboard');
    });
}

function downloadBackupCodes() {
    const codes = window.backupCodes.join('\n');
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(codes));
    element.setAttribute('download', 'backup_codes.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

async function confirmBackupCodes() {
    alert('Backup codes saved. You can now use them for emergency access.');
    closeSetup();
    loadMFAMethods();
}

// ==================== Load & Display MFA Methods ====================

async function loadMFAMethods() {
    try {
        const response = await fetch(`${API_BASE}/mfa/methods`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load MFA methods');
        }
        
        const data = await response.json();
        displayMFAMethods(data.methods);
    } catch (error) {
        console.error('Error loading MFA methods:', error);
    }
}

function displayMFAMethods(methods) {
    const list = document.getElementById('methods-list');
    
    if (methods.length === 0) {
        list.innerHTML = '<p class="text-muted">No MFA methods enabled yet</p>';
        return;
    }
    
    list.innerHTML = methods.map(method => `
        <div class="method-item">
            <div class="method-info">
                <h4>${getMethodName(method.method_type)}</h4>
                <p>Created: ${new Date(method.created_at).toLocaleDateString()}</p>
            </div>
            <div class="method-status">
                ${method.is_enabled ? '<span class="status-badge status-enabled">Enabled</span>' : ''}
                ${method.is_primary ? '<span class="status-badge status-primary">Primary</span>' : ''}
                <button class="btn-secondary" onclick="setPrimaryMFA(${method.id})">Set Primary</button>
                <button class="btn-secondary" style="background-color: var(--danger-color)" onclick="disableMFA(${method.id})">Remove</button>
            </div>
        </div>
    `).join('');
}

function getMethodName(type) {
    const names = {
        'TOTP': 'Authenticator App',
        'SMS_OTP': 'SMS Code',
        'EMAIL_OTP': 'Email Code',
        'PICTURE_PASSWORD': 'Picture Password',
        'FIDO2': 'Hardware Token',
        'BACKUP_CODES': 'Backup Codes'
    };
    return names[type] || type;
}

async function setPrimaryMFA(methodId) {
    try {
        await fetch(`${API_BASE}/mfa/methods/${methodId}/set-primary`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        loadMFAMethods();
    } catch (error) {
        alert('Failed to set primary MFA: ' + error.message);
    }
}

async function disableMFA(methodId) {
    if (!confirm('Are you sure you want to remove this MFA method?')) return;
    
    const password = prompt('Enter your password to confirm:');
    if (!password) return;
    
    try {
        await fetch(`${API_BASE}/mfa/methods/${methodId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ password })
        });
        loadMFAMethods();
    } catch (error) {
        alert('Failed to remove MFA method: ' + error.message);
    }
}

// ==================== Initialize Page ====================

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!authToken) {
        alert('Not authenticated. Please log in first.');
        window.location.href = 'login.html';
        return;
    }
    
    // Load existing MFA methods
    loadMFAMethods();
});
