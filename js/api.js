// ⚠️ SHARED_SECRET: This is a basic handshake key.
// Primary security is provided by Domain/Origin restriction on the backend.
const SHARED_SECRET = "miikun_shared_pass";

// ⚠️ BASE_URL: Using relative path for All-in-One VPS setup.
// If you host the frontend separately (e.g. GitHub Pages), change this to an absolute URL.
const BASE_URL = "/api";

export async function chat(sessionId, text, history, subject = "general") {
    const endpoint = BASE_URL.replace(/\/$/, '') + '/chat';
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
    const endpoint = BASE_URL.replace(/\/$/, '') + '/tts';
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
    const endpoint = BASE_URL.replace(/\/$/, '') + '/chat_full';
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
