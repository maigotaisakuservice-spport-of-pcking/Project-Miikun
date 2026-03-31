// ⚠️ SHARED_SECRET: This is a basic handshake key.
// Primary security is provided by Domain/Origin restriction on the backend.
const SHARED_SECRET = "miikun_shared_pass";

// If using GitHub Pages or a separate frontend, set your VPS URL here:
// Example: const BASE_URL = "https://your-domain.com/api";
const BASE_URL = window.location.hostname.includes('github.io') 
    ? "https://miikun-ai-server.pdg.f5.si/api" // Ensure absolute URL with protocol
    : "/api";

export async function chat(sessionId, text, history, subject = "general") {
    const endpoint = BASE_URL.endsWith('/') ? `${BASE_URL}chat` : `${BASE_URL}/chat`;
    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": SHARED_SECRET
        },
        body: JSON.stringify({
            session_id: sessionId,
            subject: subject,
            text: text,
            history: history
        })
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
}

export async function getTtsAudio(text) {
    const endpoint = BASE_URL.endsWith('/') ? `${BASE_URL}tts` : `${BASE_URL}/tts`;
    const response = await fetch(`${endpoint}?text=${encodeURIComponent(text)}`, {
        method: "GET",
        headers: {
            "x-api-key": SHARED_SECRET
        }
    });

    if (!response.ok) {
        throw new Error(`TTS API error: ${response.status}`);
    }

    const blob = await response.blob();
    return URL.createObjectURL(blob);
}

// Full endpoint (text + audio) for better performance
export async function chatFull(sessionId, text, history, subject = "general") {
    // If BASE_URL is absolute, we need to ensure trailing slash logic is handled
    const endpoint = BASE_URL.endsWith('/') ? `${BASE_URL}chat_full` : `${BASE_URL}/chat_full`;
    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": SHARED_SECRET
        },
        body: JSON.stringify({
            session_id: sessionId,
            subject: subject,
            text: text,
            history: history
        })
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
}
