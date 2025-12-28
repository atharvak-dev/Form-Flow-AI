/**
 * FormFlow AI - Background Service Worker
 * 
 * Manages WebSocket connections to backend and message routing
 * between content scripts, popup, and FastAPI server.
 */

// Configuration
const CONFIG = {
    BACKEND_URL: 'http://localhost:8000',
    WS_URL: 'ws://localhost:8000/ws',
    RECONNECT_DELAY: 1000,
    MAX_RECONNECT_DELAY: 30000,
    MAX_RECONNECT_ATTEMPTS: 5,
    HEALTH_CHECK_TIMEOUT: 5000
};

// State
let activeSessions = new Map(); // tab_id -> session_data
let reconnectAttempts = 0;

// =============================================================================
// Message Handling
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    handleMessage(message, sender)
        .then(sendResponse)
        .catch(error => {
            console.error('Message handling error:', error);
            sendResponse({ success: false, error: error.message });
        });
    return true; // Indicates async response
});

async function handleMessage(message, sender) {
    const tabId = sender.tab?.id;

    switch (message.type) {
        case 'START_SESSION':
            return await startSession(tabId, message.formSchema, message.formUrl);

        case 'SEND_MESSAGE':
            return await sendUserMessage(tabId, message.text);

        case 'END_SESSION':
            return await endSession(tabId);

        case 'GET_SESSION_STATUS':
            return getSessionStatus(tabId);

        case 'CHECK_BACKEND':
            return await checkBackendHealth();

        case 'GET_EXTRACTED_DATA':
            return getExtractedData(tabId);

        default:
            console.warn('Unknown message type:', message.type);
            return { success: false, error: 'Unknown message type' };
    }
}

// =============================================================================
// Session Management
// =============================================================================

async function startSession(tabId, formSchema, formUrl) {
    try {
        console.log('Starting session for tab:', tabId);

        // Create session via API
        const response = await fetch(`${CONFIG.BACKEND_URL}/conversation/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                form_schema: formSchema,
                form_url: formUrl
            })
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }

        const data = await response.json();

        // Store session
        activeSessions.set(tabId, {
            sessionId: data.session_id,
            formUrl: formUrl,
            extractedFields: {},
            isListening: false,
            createdAt: Date.now()
        });

        console.log('Session created:', data.session_id);

        return {
            success: true,
            sessionId: data.session_id,
            greeting: data.greeting,
            nextQuestions: data.next_questions,
            remainingCount: data.remaining_fields_count
        };

    } catch (error) {
        console.error('Failed to start session:', error);
        return { success: false, error: error.message };
    }
}

async function sendUserMessage(tabId, text) {
    const session = activeSessions.get(tabId);
    if (!session) {
        console.error(`No active session found for tab ${tabId}. Active sessions:`, [...activeSessions.keys()]);
        return {
            success: false,
            error: 'No active session. Please click "Fill with Voice" button to start.',
            debug: { tabId, activeSessionTabs: [...activeSessions.keys()] }
        };
    }

    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/conversation/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: session.sessionId,
                message: text
            })
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }

        const data = await response.json();

        // Update local state
        Object.assign(session.extractedFields, data.extracted_values);

        return {
            success: true,
            response: data.response,
            extractedValues: data.extracted_values,
            confidenceScores: data.confidence_scores,
            needsConfirmation: data.needs_confirmation,
            remainingCount: data.remaining_fields_count,
            isComplete: data.is_complete,
            nextQuestions: data.next_questions
        };

    } catch (error) {
        console.error('Failed to send message:', error);
        return { success: false, error: error.message };
    }
}

async function endSession(tabId) {
    const session = activeSessions.get(tabId);
    if (!session) {
        return { success: true, message: 'No session to end' };
    }

    try {
        const response = await fetch(
            `${CONFIG.BACKEND_URL}/conversation/session/${session.sessionId}`,
            { method: 'DELETE' }
        );

        const data = await response.json();
        activeSessions.delete(tabId);

        return {
            success: true,
            finalData: data.final_data,
            fieldsCollected: data.fields_collected
        };

    } catch (error) {
        // Still remove local session even if backend fails
        activeSessions.delete(tabId);
        return { success: true, message: 'Session ended locally' };
    }
}

function getSessionStatus(tabId) {
    const session = activeSessions.get(tabId);
    if (!session) {
        return { hasSession: false };
    }

    return {
        hasSession: true,
        sessionId: session.sessionId,
        extractedFields: session.extractedFields,
        isListening: session.isListening
    };
}

function getExtractedData(tabId) {
    const session = activeSessions.get(tabId);
    return {
        success: true,
        data: session?.extractedFields || {}
    };
}

// =============================================================================
// Backend Health Check
// =============================================================================

async function checkBackendHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.HEALTH_CHECK_TIMEOUT);

        const response = await fetch(`${CONFIG.BACKEND_URL}/health`, {
            method: 'GET',
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            const isHealthy = ['healthy', 'degraded'].includes(data.status);
            console.log('Backend health check:', data.status);
            return {
                success: true,
                healthy: isHealthy,
                status: data.status,
                version: data.version
            };
        }
        return { success: false, healthy: false };

    } catch (error) {
        console.error('Health check error:', error.message);
        return { success: false, healthy: false, error: error.message };
    }
}

// =============================================================================
// Tab Management
// =============================================================================

// Clean up sessions when tabs are closed
chrome.tabs.onRemoved.addListener((tabId) => {
    if (activeSessions.has(tabId)) {
        console.log('Tab closed, cleaning up session:', tabId);
        endSession(tabId);
    }
});

// Handle tab updates (navigation)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'loading' && activeSessions.has(tabId)) {
        const session = activeSessions.get(tabId);
        // Only end session if navigating to a different domain
        try {
            const sessionDomain = new URL(session.formUrl).hostname;
            const newDomain = tab.url ? new URL(tab.url).hostname : sessionDomain;

            if (sessionDomain !== newDomain) {
                console.log('Tab navigating to different domain, ending session:', tabId);
                endSession(tabId);
            } else {
                console.log('Tab navigating within same domain, keeping session:', tabId);
            }
        } catch (e) {
            // If URL parsing fails, be conservative and keep the session
            console.log('URL parsing failed, keeping session:', tabId);
        }
    }
});

// =============================================================================
// Installation
// =============================================================================

chrome.runtime.onInstalled.addListener((details) => {
    console.log('FormFlow AI installed:', details.reason);

    // Set default settings
    chrome.storage.local.set({
        settings: {
            autoDetectForms: true,
            voiceSpeed: 1.0,
            language: 'en-US',
            showOverlay: true
        }
    });
});

console.log('FormFlow AI background worker initialized');
