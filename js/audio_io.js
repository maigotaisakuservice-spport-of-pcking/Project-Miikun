import { state, AppState } from './state.js';

export class AudioIO {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResultCallback = null;
        this.onInterimResultCallback = null;
        this.onErrorCallback = null;
        this.audioElement = new Audio();
        this.audioElement.crossOrigin = "anonymous";

        // Audio Analysis for Visualizer
        this.audioContext = null;
        this.analyser = null;
        this.microphoneStream = null;
        this.sourceNode = null;

        this.lastTranscript = "";

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
        this.recognition.continuous = true; // Changed to true for better toggle control
        this.recognition.interimResults = true;

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            if (finalTranscript) {
                this.lastTranscript += finalTranscript;
                if (this.onResultCallback) this.onResultCallback(this.lastTranscript, true);
            }

            if (interimTranscript && this.onInterimResultCallback) {
                this.onInterimResultCallback(this.lastTranscript + interimTranscript);
            }
        };

        this.recognition.onerror = (event) => {
            if (event.error === 'no-speech') return; // Ignore no-speech error for continuous mode
            console.error("STT Error:", event.error);
            if (this.onErrorCallback) this.onErrorCallback(event.error);
            state.setState(AppState.IDLE);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            // If we ended but state is still LISTENING, it means it timed out or was auto-stopped
            if (state.getState() === AppState.LISTENING) {
                this.finishListening();
            }
        };
    }

    async startListening(onResult, onInterim, onError) {
        if (!this.recognition) return;
        this.onResultCallback = onResult;
        this.onInterimResultCallback = onInterim;
        this.onErrorCallback = onError;
        this.lastTranscript = "";

        await this.initAudioContext();

        try {
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

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            // Note: onend will be triggered, calling finishListening
        }
    }

    finishListening() {
        if (this.lastTranscript.trim()) {
            if (this.onResultCallback) this.onResultCallback(this.lastTranscript, false);
            state.setState(AppState.THINKING);
        } else {
            state.setState(AppState.IDLE);
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
