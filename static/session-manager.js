// Session Management with Inactivity Logout
const SESSION_TIMEOUT = 15 * 60 * 1000; // 15 minutes
const WARNING_TIME = 10 * 60 * 1000; // 10 minutes (5 minutes before logout)
let inactivityTimer = null;
let warningTimer = null;
let isWarningShown = false;

function resetInactivityTimer() {
    // Clear existing timers
    if (inactivityTimer) clearTimeout(inactivityTimer);
    if (warningTimer) clearTimeout(warningTimer);
    isWarningShown = false;
    
    // Hide warning if shown
    const warningModal = document.getElementById('session-warning-modal');
    if (warningModal) {
        warningModal.style.display = 'none';
    }
    
    // Set warning timer
    warningTimer = setTimeout(showSessionWarning, WARNING_TIME);
    
    // Set logout timer
    inactivityTimer = setTimeout(forceLogout, SESSION_TIMEOUT);
}

function showSessionWarning() {
    if (isWarningShown) return;
    isWarningShown = true;
    
    const warningModal = document.getElementById('session-warning-modal');
    if (!warningModal) {
        createWarningModal();
        document.getElementById('session-warning-modal').style.display = 'block';
    } else {
        warningModal.style.display = 'block';
    }
}

function createWarningModal() {
    if (document.getElementById('session-warning-modal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'session-warning-modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        z-index: 2000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        animation: fadeIn 0.2s ease;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: var(--bg-secondary, #151932);
        margin: 10% auto;
        padding: 30px;
        border: 1px solid var(--border-color, #2d3142);
        border-radius: 12px;
        width: 90%;
        max-width: 400px;
        text-align: center;
        color: var(--text-primary, #e4e6eb);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    `;
    
    content.innerHTML = `
        <h2 style="margin-bottom: 15px; color: var(--text-primary, #e4e6eb);">⏱️ Session Timeout Warning</h2>
        <p style="margin-bottom: 20px; color: var(--text-secondary, #b0b3b8); font-size: 15px;">
            Your session will expire in <strong>5 minutes</strong> due to inactivity.
        </p>
        <p style="margin-bottom: 20px; color: var(--text-tertiary, #8a8d91); font-size: 13px;">
            Click below to stay logged in.
        </p>
        <div style="display: flex; gap: 10px; justify-content: center;">
            <button id="stay-logged-in-btn" style="
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            ">Stay Logged In</button>
            <button id="logout-now-btn" style="
                background: var(--bg-tertiary, #1e2139);
                color: var(--text-secondary, #b0b3b8);
                border: 1px solid var(--border-color, #2d3142);
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            ">Logout Now</button>
        </div>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('stay-logged-in-btn').addEventListener('click', () => {
        modal.style.display = 'none';
        resetInactivityTimer();
    });
    
    document.getElementById('logout-now-btn').addEventListener('click', forceLogout);
}

function forceLogout() {
    localStorage.removeItem('access_token');
    sessionStorage.clear();
    window.location.href = '/static/login.html?expired=true';
}

// Track user activity
function setupActivityListeners() {
    // Only run session timeout for logged-in users
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('Session manager: No auth token, skipping timeout setup');
        return;
    }
    
    console.log('Session manager: Starting inactivity timers');
    
    const events = ['mousedown', 'keydown', 'scroll', 'click', 'touchstart'];
    
    events.forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });
    
    // Start initial timer
    resetInactivityTimer();
}

// Initialize when DOM is ready (only once)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupActivityListeners);
} else {
    setupActivityListeners();
}
