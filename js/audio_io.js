import { state, AppState } from './state.js';

export class AudioIO {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResultCallback = null;
        this.onErrorCallback = null;
        this.audioElement = new Audio();
        this.audioElement.crossOrigin = "anonymous";

        // Audio Analysis for Visualizer
        this.audioContext = null;
        this.analyser = null;
        this.microphoneStream = null;
        this.sourceNode = null;

        this.setupRecognition();
    }

    async initAudioContext() {
        if (this.audioContext) return;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
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

    async startListening(onResult, onError) {
        if (!this.recognition) return;
        this.onResultCallback = onResult;
        this.onErrorCallback = onError;

        await this.initAudioContext();

        try {
            // Setup Microphone for analysis
            if (!this.microphoneStream) {
                this.microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const micSource = this.audioContext.createMediaStreamSource(this.microphoneStream);
                micSource.connect(this.analyser);
            }

            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            this.recognition.start();
            this.isListening = true;
            state.setState(AppState.LISTENING);
        } catch (e) {
            console.error("Microphone or Recognition error:", e);
            if (onError) onError(e);
        }
    }

    async playTts(audioUrl, fallbackText = null) {
        await this.initAudioContext();

        return new Promise((resolve) => {
            state.setState(AppState.SPEAKING);

            if (!audioUrl && fallbackText) {
                this.playNativeTts(fallbackText).then(resolve);
                return;
            }

            this.audioElement.src = audioUrl;

            // Connect Audio Element to Analyser (only once)
            if (!this.sourceNode) {
                this.sourceNode = this.audioContext.createMediaElementSource(this.audioElement);
                this.sourceNode.connect(this.analyser);
                this.analyser.connect(this.audioContext.destination);
            }
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

    async playNativeTts(text) {
        return new Promise((resolve) => {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ja-JP';
            utterance.onend = () => {
                state.setState(AppState.IDLE);
                resolve();
            };
            utterance.onerror = () => {
                state.setState(AppState.IDLE);
                resolve();
            };
            window.speechSynthesis.speak(utterance);
        });
    }

    // Helper to check if currently speaking for lip-sync
    isSpeaking() {
        return !this.audioElement.paused && !this.audioElement.ended;
    }

    getVolumeData() {
        if (!this.analyser) return new Uint8Array(0);
        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);
        return dataArray;
    }
}
