// Zeus Voice AI — Frontend App
// Auto-detect API URL
const API_BASE = (() => {
    const host = window.location.host;
    // If on Vercel, backend is on Render
    if (host.includes('vercel.app')) {
        return 'https://zeus-voice-ai.onrender.com';
    }
    return 'http://localhost:8000';
})();

// State
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let isProcessing = false;
let authToken = null;

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const chatScreen = document.getElementById('chat-screen');
const googleSigninBtn = document.getElementById('google-signin-btn');
const logoutBtn = document.getElementById('logout-btn');
const chatMessages = document.getElementById('chat-messages');
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status-text');
const userEmail = document.getElementById('user-email');
const audioPlayer = document.getElementById('audio-player');

// ============ AUTH ============

// Check if returning user (token in sessionStorage)
function checkAuth() {
    const token = sessionStorage.getItem('zeus_token');
    const email = sessionStorage.getItem('zeus_email');
    if (token && email) {
        authToken = token;
        showChatScreen(email);
        verifyToken();
    }
}

async function verifyToken() {
    try {
        const res = await fetch(`${API_BASE}/auth/status`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        if (!data.authenticated) {
            logout();
        }
    } catch (e) {
        // Backend might not be running — show chat anyway
        addMessage('system', 'Backend connecting... Make sure the server is running.');
    }
}

// Google Sign-In
googleSigninBtn.addEventListener('click', () => {
    window.location.href = `${API_BASE}/auth/google`;
});

// Handle OAuth callback — check URL for token
function handleCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const email = params.get('email');
    if (token && email) {
        authToken = token;
        sessionStorage.setItem('zeus_token', token);
        sessionStorage.setItem('zeus_email', email);
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        showChatScreen(email);
        addMessage('assistant', "Connected! I can now access your Gmail and Calendar. Try asking me something like 'Read my latest email' or 'What is on my calendar today?'");
    }
}

// Logout
logoutBtn.addEventListener('click', logout);

function logout() {
    authToken = null;
    sessionStorage.removeItem('zeus_token');
    sessionStorage.removeItem('zeus_email');
    loginScreen.classList.remove('hidden');
    chatScreen.classList.add('hidden');
    chatMessages.innerHTML = `
        <div class="message assistant">
            Hey, I'm Zeus. Sign in with Google to connect your email and calendar, then ask me anything.
        </div>
    `;
}

function showChatScreen(email) {
    loginScreen.classList.add('hidden');
    chatScreen.classList.remove('hidden');
    userEmail.textContent = email;
}

// ============ MICROPHONE ============

micBtn.addEventListener('click', () => {
    if (isProcessing) return;

    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    if (!authToken) {
        addMessage('system', 'Please sign in with Google first.');
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            // Process the audio
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await processAudio(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add('recording');
        statusText.textContent = 'Listening...';
    } catch (err) {
        console.error('Mic error:', err);
        statusText.textContent = 'Microphone access denied. Check browser permissions.';
        setTimeout(() => statusText.textContent = 'Tap the mic to start', 3000);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    isRecording = false;
    micBtn.classList.remove('recording');
}

async function processAudio(audioBlob) {
    isProcessing = true;
    micBtn.classList.remove('recording');
    micBtn.classList.add('loading');
    statusText.textContent = 'Processing...';

    // Show typing indicator
    const typingEl = document.createElement('div');
    typingEl.className = 'typing-indicator';
    typingEl.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        const res = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        // Remove typing indicator
        typingEl.remove();

        if (!res.ok) {
            const err = await res.json();
            addMessage('system', err.detail || 'Something went wrong. Please try again.');
            isProcessing = false;
            micBtn.classList.remove('loading');
            statusText.textContent = 'Tap the mic to start';
            return;
        }

        const data = await res.json();

        // Show transcript as user message
        addMessage('user', data.transcript);

        // Show response
        addMessage('assistant', data.text);

        // Play audio response
        if (data.audio_url) {
            audioPlayer.src = `${API_BASE}${data.audio_url}`;
            audioPlayer.play().catch(e => console.log('Audio autoplay blocked:', e));
        }

    } catch (err) {
        typingEl.remove();
        console.error('API error:', err);
        addMessage('system', 'Network error. Make sure the server is running.');
    }

    isProcessing = false;
    micBtn.classList.remove('loading');
    statusText.textContent = 'Tap the mic to start';
}

// ============ UI HELPERS ============

function addMessage(role, text) {
    const msg = document.createElement('div');
    msg.className = `message ${role}`;
    msg.textContent = text;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============ INIT ============

// Check OAuth callback first
handleCallback();

// Then check if already authenticated
checkAuth();
