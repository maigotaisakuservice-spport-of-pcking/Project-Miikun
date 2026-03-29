// ⚠️ SHARED_SECRET: This is a basic handshake key.
// Primary security is provided by Domain/Origin restriction on the backend.
const SHARED_SECRET = "miikun_shared_pass";
const BASE_URL = "/api";

export async function chat(sessionId, text, history, subject = "general") {
    const response = await fetch(`${BASE_URL}/chat`, {
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
    const response = await fetch(`${BASE_URL}/tts?text=${encodeURIComponent(text)}`, {
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
    const response = await fetch(`${BASE_URL}/chat_full`, {
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
