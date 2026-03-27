import { state, AppState } from './state.js';

export class AudioIO {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResultCallback = null;
        this.onErrorCallback = null;
        this.audioElement = new Audio();

        this.setupRecognition();
    }

    setupRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error("Speech Recognition not supported in this browser.");
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'ja-JP';
        this.recognition.continuous = false;
        this.recognition.interimResults = false;

        this.recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            if (this.onResultCallback) this.onResultCallback(text);
            state.setState(AppState.THINKING);
        };

        this.recognition.onerror = (event) => {
            console.error("STT Error:", event.error);
            if (this.onErrorCallback) this.onErrorCallback(event.error);
            state.setState(AppState.IDLE);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            if (state.getState() === AppState.LISTENING) {
                state.setState(AppState.IDLE);
            }
        };
    }

    startListening(onResult, onError) {
        if (!this.recognition) return;
        this.onResultCallback = onResult;
        this.onErrorCallback = onError;

        try {
            this.recognition.start();
            this.isListening = true;
            state.setState(AppState.LISTENING);
        } catch (e) {
            console.error("Recognition already started:", e);
        }
    }

    async playTts(audioUrl) {
        return new Promise((resolve) => {
            state.setState(AppState.SPEAKING);
            this.audioElement.src = audioUrl;
            this.audioElement.onended = () => {
                state.setState(AppState.IDLE);
                resolve();
            };
            this.audioElement.onerror = (e) => {
                console.error("Audio playback error:", e);
                state.setState(AppState.IDLE);
                resolve();
            };
            this.audioElement.play().catch(err => {
                console.error("Audio play failed:", err);
                state.setState(AppState.IDLE);
                resolve();
            });
        });
    }

    // Helper to check if currently speaking for lip-sync
    isSpeaking() {
        return !this.audioElement.paused && !this.audioElement.ended;
    }

    getAudioVolume() {
        // Basic volume analysis if needed for lip-sync
        return this.audioElement.paused ? 0 : 0.5; // Placeholder
    }
}
