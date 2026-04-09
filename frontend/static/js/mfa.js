// MFA Frontend JavaScript - Legacy MFA page support
// Uses centralized auth service from auth.js

const API_BASE = 'http://localhost:8000/api/v1';

let currentMethod = null;
let pictureImageData = null;
let pictureMethodId = null;
let pictureTaps = [];
let verifyTaps = [];
let smsMethodId = null;
let emailMethodId = null;
let totpSecret = null;
let backupCodes = [];

function getAuthTokenOrRedirect() {
    if (typeof auth === 'undefined' || !auth.isAuthenticated()) {
        window.location.href = '/login.html';
        return null;
    }
    return auth.getToken();
}

async function apiFetch(path, method = 'GET', body = null) {
    const token = getAuthTokenOrRedirect();
    if (!token) return null;

    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
            const err = await response.json();
            detail = err?.detail || detail;
        } catch (e) {
            // Ignore JSON parse failures.
        }
        throw new Error(detail);
    }

    return response.json();
}

function closeAllPanels() {
    document.querySelectorAll('.setup-panel').forEach((panel) => panel.classList.add('hidden'));
}

function closeSetup() {
    closeAllPanels();
    currentMethod = null;
}

function selectMethod(method) {
    if (method === 'fido2') {
        alert('FIDO2 setup is not available in this build yet. Use TOTP, Email OTP, Picture Password, or Backup Codes.');
        return;
    }

    currentMethod = method;
    closeAllPanels();
    const panel = document.getElementById(`${method}-setup`);
    if (!panel) return;

    panel.classList.remove('hidden');
    if (method === 'totp') initTOTPSetup();
    if (method === 'picture') initPicturePasswordSetup();
    if (method === 'backup') generateBackupCodes();
}

function logoutUser() {
    if (confirm('Are you sure you want to logout?')) {
        auth.logout();
        window.location.href = '/login.html';
    }
}

// ==================== TOTP ====================

async function initTOTPSetup() {
    try {
        const data = await apiFetch('/mfa/totp/setup', 'POST', {});
        if (!data) return;
        totpSecret = data.secret;
        document.getElementById('totp-qr').innerHTML = `<img src="${data.qr_code_url}" alt="QR Code">`;
        document.getElementById('totp-secret').textContent = data.manual_entry_key;
    } catch (error) {
        alert(`Failed to setup TOTP: ${error.message}`);
    }
}

async function verifyTOTP() {
    const code = (document.getElementById('totp-code')?.value || '').trim();
    if (!/^\d{6}$/.test(code)) {
        alert('Please enter a valid 6-digit code.');
        return;
    }

    if (!totpSecret) {
        alert('TOTP setup session expired. Please restart setup.');
        return;
    }

    try {
        await apiFetch(`/mfa/totp/enroll?secret=${encodeURIComponent(totpSecret)}`, 'POST', { totp_code: code });
        alert('TOTP MFA successfully enabled.');
        closeSetup();
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to verify TOTP: ${error.message}`);
    }
}

// ==================== SMS OTP ====================

async function startSMSOTP() {
    const phone = (document.getElementById('sms-phone')?.value || '').trim();
    if (!/^\+?\d{9,15}$/.test(phone)) {
        alert('Please enter a valid phone number.');
        return;
    }

    try {
        const data = await apiFetch('/mfa/sms/setup', 'POST', { phone_number: phone });
        smsMethodId = data?.method_id || null;
        document.getElementById('sms-verify-step')?.classList.remove('hidden');
    } catch (error) {
        alert(`Failed to send SMS OTP: ${error.message}`);
    }
}

async function verifySMSOTP() {
    const code = (document.getElementById('sms-code')?.value || '').trim();
    if (!/^\d{6}$/.test(code) || !smsMethodId) {
        alert('Please enter a valid code after requesting SMS OTP.');
        return;
    }

    try {
        await apiFetch('/mfa/otp/verify', 'POST', { method_id: smsMethodId, otp_code: code });
        alert('SMS OTP MFA successfully enabled.');
        closeSetup();
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to verify SMS OTP: ${error.message}`);
    }
}

async function resendSMSOTP() {
    if (!smsMethodId) {
        alert('Start SMS OTP setup first.');
        return;
    }
    try {
        await apiFetch('/mfa/otp/resend', 'POST', { method_id: smsMethodId });
        alert('A new SMS OTP has been sent.');
    } catch (error) {
        alert(`Failed to resend SMS OTP: ${error.message}`);
    }
}

// ==================== Email OTP ====================

async function startEmailOTP() {
    try {
        const data = await apiFetch('/mfa/email/setup', 'POST', {});
        emailMethodId = data?.method_id || null;
        document.getElementById('email-verify-step')?.classList.remove('hidden');
    } catch (error) {
        alert(`Failed to send Email OTP: ${error.message}`);
    }
}

async function verifyEmailOTP() {
    const code = (document.getElementById('email-code')?.value || '').trim();
    if (!/^\d{6}$/.test(code) || !emailMethodId) {
        alert('Please enter a valid code after requesting Email OTP.');
        return;
    }

    try {
        await apiFetch('/mfa/otp/verify', 'POST', { method_id: emailMethodId, otp_code: code });
        alert('Email OTP MFA successfully enabled.');
        closeSetup();
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to verify Email OTP: ${error.message}`);
    }
}

async function resendEmailOTP() {
    if (!emailMethodId) {
        alert('Start Email OTP setup first.');
        return;
    }
    try {
        await apiFetch('/mfa/otp/resend', 'POST', { method_id: emailMethodId });
        alert('A new Email OTP has been sent.');
    } catch (error) {
        alert(`Failed to resend Email OTP: ${error.message}`);
    }
}

// ==================== Picture Password ====================

function initPicturePasswordSetup() {
    pictureImageData = null;
    pictureMethodId = null;
    pictureTaps = [];
    verifyTaps = [];
    const uploadStep = document.getElementById('picture-upload-step');
    const tapsStep = document.getElementById('picture-taps-step');
    const verifyStep = document.getElementById('picture-verify-step');
    uploadStep?.classList.remove('hidden');
    tapsStep?.classList.add('hidden');
    verifyStep?.classList.add('hidden');
}

async function handleImageUpload(event) {
    const file = event?.target?.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
        alert('File is too large. Max 5MB.');
        return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
        pictureImageData = e.target.result;
        const preview = document.getElementById('image-preview');
        if (preview) {
            preview.innerHTML = `<img src="${pictureImageData}" alt="Selected image">`;
            preview.classList.remove('hidden');
        }

        try {
            const base64Data = String(pictureImageData).split(',')[1];
            const format = (file.type || 'image/png').split('/')[1] || 'png';
            await apiFetch('/mfa/picture/setup', 'POST', {
                image_data: base64Data,
                image_format: format,
            });

            document.getElementById('picture-upload-step')?.classList.add('hidden');
            document.getElementById('picture-taps-step')?.classList.remove('hidden');
            setupPictureCanvas();
        } catch (error) {
            alert(`Failed to upload image: ${error.message}`);
        }
    };
    reader.readAsDataURL(file);
}

function setupPictureCanvas() {
    const canvas = document.getElementById('picture-canvas');
    if (!canvas || !pictureImageData) return;
    const ctx = canvas.getContext('2d');

    const img = new Image();
    img.onload = () => {
        canvas.width = Math.min(img.width, 600);
        canvas.height = Math.max(200, Math.floor(img.height * (canvas.width / img.width)));
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        canvas.onclick = (e) => {
            addPictureTap(e, canvas, pictureTaps, 'tap-count');
        };
    };
    img.src = pictureImageData;
}

function setupPictureVerifyCanvas() {
    const canvas = document.getElementById('picture-verify-canvas');
    if (!canvas || !pictureImageData) return;
    const ctx = canvas.getContext('2d');

    const img = new Image();
    img.onload = () => {
        canvas.width = Math.min(img.width, 600);
        canvas.height = Math.max(200, Math.floor(img.height * (canvas.width / img.width)));
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        canvas.onclick = (e) => {
            addPictureTap(e, canvas, verifyTaps, 'verify-tap-count');
        };
    };
    img.src = pictureImageData;
}

function addPictureTap(event, canvas, taps, countId) {
    if (taps.length >= 5) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const sequence = taps.length + 1;

    taps.push({ x, y, sequence });
    const counter = document.getElementById(countId);
    if (counter) counter.textContent = String(taps.length);

    drawTapPoint(canvas, x, y, sequence);
    const confirmBtn = document.getElementById('confirm-taps-btn');
    if (confirmBtn && taps === pictureTaps) {
        confirmBtn.disabled = pictureTaps.length < 3;
    }
}

function drawTapPoint(canvas, x, y, sequence) {
    const ctx = canvas.getContext('2d');
    const cx = x * canvas.width;
    const cy = y * canvas.height;
    ctx.fillStyle = 'rgba(37, 99, 235, 0.75)';
    ctx.beginPath();
    ctx.arc(cx, cy, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(sequence), cx, cy);
}

function resetPictureTaps() {
    pictureTaps = [];
    const counter = document.getElementById('tap-count');
    if (counter) counter.textContent = '0';
    const confirmBtn = document.getElementById('confirm-taps-btn');
    if (confirmBtn) confirmBtn.disabled = true;
    setupPictureCanvas();
}

async function confirmPicturePassword() {
    if (!pictureImageData || pictureTaps.length < 3) {
        alert('Define at least 3 tap points first.');
        return;
    }

    try {
        const base64Data = String(pictureImageData).split(',')[1];
        const setupData = await apiFetch('/mfa/picture/setup', 'POST', {
            image_data: base64Data,
            image_format: 'png',
        });

        const defineData = await apiFetch('/mfa/picture/define', 'POST', {
            image_hash: setupData?.image_hash,
            taps: pictureTaps,
            tolerance_radius: 0.05,
        });

        pictureMethodId = defineData?.method_id || null;
        document.getElementById('picture-taps-step')?.classList.add('hidden');
        document.getElementById('picture-verify-step')?.classList.remove('hidden');
        setupPictureVerifyCanvas();
    } catch (error) {
        alert(`Failed to save picture pattern: ${error.message}`);
    }
}

function resetPictureVerifyTaps() {
    verifyTaps = [];
    const counter = document.getElementById('verify-tap-count');
    if (counter) counter.textContent = '0';
    setupPictureVerifyCanvas();
}

async function verifyPicturePassword() {
    if (!pictureMethodId || verifyTaps.length !== pictureTaps.length) {
        alert(`Please tap exactly ${pictureTaps.length} points.`);
        return;
    }

    try {
        await apiFetch('/mfa/verify', 'POST', {
            method_id: pictureMethodId,
            verification_code: '',
            verification_data: { taps: verifyTaps },
        });
        alert('Picture Password MFA successfully enabled.');
        closeSetup();
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to verify picture password: ${error.message}`);
    }
}

// ==================== Backup Codes ====================

async function generateBackupCodes() {
    try {
        const data = await apiFetch('/mfa/backup-codes/generate', 'POST');
        backupCodes = Array.isArray(data?.codes) ? data.codes : [];
        const codesDisplay = document.getElementById('backup-codes-display');
        if (codesDisplay) {
            codesDisplay.innerHTML = backupCodes.map((code) => `<code>${code}</code>`).join('<br>');
        }
    } catch (error) {
        alert(`Failed to generate backup codes: ${error.message}`);
    }
}

function copyBackupCodes() {
    if (!backupCodes.length) {
        alert('No backup codes available.');
        return;
    }
    navigator.clipboard.writeText(backupCodes.join('\n')).then(() => {
        alert('Backup codes copied to clipboard.');
    });
}

function downloadBackupCodes() {
    if (!backupCodes.length) {
        alert('No backup codes available.');
        return;
    }
    const element = document.createElement('a');
    element.href = `data:text/plain;charset=utf-8,${encodeURIComponent(backupCodes.join('\n'))}`;
    element.download = 'backup_codes.txt';
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function confirmBackupCodes() {
    alert('Backup codes saved.');
    closeSetup();
    loadMFAMethods();
}

// ==================== Method Management ====================

function getMethodName(type) {
    const value = String(type || '').toUpperCase();
    const names = {
        TOTP: 'Authenticator App',
        SMS_OTP: 'SMS OTP',
        EMAIL_OTP: 'Email OTP',
        PICTURE_PASSWORD: 'Picture Password',
        BACKUP_CODES: 'Backup Codes',
    };
    return names[value] || value;
}

function displayMFAMethods(methods) {
    const list = document.getElementById('methods-list');
    if (!list) return;

    if (!Array.isArray(methods) || methods.length === 0) {
        list.innerHTML = '<p class="text-muted">No MFA methods enabled yet</p>';
        return;
    }

    list.innerHTML = methods.map((method) => {
        const created = method.created_at ? new Date(method.created_at).toLocaleString() : '-';
        return `
            <div class="method-item">
                <div class="method-info">
                    <h4>${getMethodName(method.method_type)}</h4>
                    <p>Created: ${created}</p>
                </div>
                <div class="method-status">
                    ${method.is_enabled ? '<span class="status-badge status-enabled">Enabled</span>' : ''}
                    ${method.is_primary ? '<span class="status-badge status-primary">Primary</span>' : ''}
                    <button class="btn-secondary" onclick="setPrimaryMFA(${method.id})">Set Primary</button>
                    <button class="btn-secondary" onclick="disableMFA(${method.id})">Remove</button>
                </div>
            </div>
        `;
    }).join('');
}

async function loadMFAMethods() {
    try {
        const data = await apiFetch('/mfa/methods');
        displayMFAMethods(data?.methods || []);
    } catch (error) {
        console.error('Failed to load MFA methods:', error);
    }
}

async function setPrimaryMFA(methodId) {
    try {
        await apiFetch(`/mfa/methods/${methodId}/set-primary`, 'POST');
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to set primary MFA: ${error.message}`);
    }
}

async function disableMFA(methodId) {
    if (!confirm('Are you sure you want to remove this MFA method?')) return;
    const password = prompt('Enter your password to confirm:');
    if (!password) return;

    try {
        await apiFetch(`/mfa/methods/${methodId}`, 'DELETE', { password });
        await loadMFAMethods();
    } catch (error) {
        alert(`Failed to remove MFA method: ${error.message}`);
    }
}

function registerFIDO2() {
    alert('FIDO2 registration is not implemented in this build.');
}

document.addEventListener('DOMContentLoaded', async () => {
    if (!getAuthTokenOrRedirect()) return;
    await loadMFAMethods();
});
