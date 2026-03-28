import { state, AppState } from './state.js';
import { VRMLoader } from './vrm_loader.js';
import { AudioIO } from './audio_io.js';
import { chatFull } from './api.js';

class MiikunApp {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.micButton = document.getElementById('mic-button');
        this.micRing = document.getElementById('mic-ring');
        this.waveform = document.getElementById('waveform');
        this.statusText = document.getElementById('status-text');
        this.loadingIndicator = document.getElementById('loading-indicator');

        this.vrmLoader = new VRMLoader('miikun-canvas');
        this.audioIO = new AudioIO();
        this.history = [];

        this.init();
        this.updateWaveform();
    }

    updateWaveform() {
        requestAnimationFrame(() => this.updateWaveform());

        const curState = state.getState();
        if (curState === AppState.LISTENING || curState === AppState.SPEAKING) {
            const data = this.audioIO.getVolumeData();
            if (data.length > 0) {
                // Pick 5 samples for the 5 bars
                const bars = this.waveform.querySelectorAll('div');
                const indices = [10, 30, 50, 70, 90];
                bars.forEach((bar, i) => {
                    const val = data[indices[i]] || 0;
                    const scale = 0.1 + (val / 255) * 1.5;
                    bar.style.transform = `scaleY(${scale})`;
                });
            }
        } else {
            // Reset bars
            const bars = this.waveform.querySelectorAll('div');
            bars.forEach(bar => bar.style.transform = `scaleY(1)`);
        }
    }

    async init() {
        // Load VRM
        try {
            await this.vrmLoader.loadVRM('assets/miikun.vrm');
        } catch (e) {
            console.warn("VRM file not found or placeholder detected. Ensure assets/miikun.vrm is a valid VRM file.");
            // Optional: Provide a visual indicator in logs if needed.
        }

        // Subscribe to state changes
        state.subscribe((newState) => this.handleStateChange(newState));

        // UI Listeners
        this.micButton.addEventListener('click', () => {
            if (state.getState() === AppState.IDLE) {
                this.startSession();
            }
        });

        // Add Welcome Message (Optional)
        // this.addMessage('miikun', 'やっほー！今日は何して遊ぶ？それとも勉強する？');
    }

    handleStateChange(newState) {
        console.log("State Changed:", newState);

        switch (newState) {
            case AppState.IDLE:
                this.micRing.classList.remove('mic-pulse');
                this.micButton.classList.remove('opacity-50', 'cursor-not-allowed');
                this.waveform.classList.add('opacity-10');
                this.waveform.classList.remove('opacity-100');
                this.statusText.classList.add('opacity-0');
                this.loadingIndicator.classList.add('opacity-0');
                this.vrmLoader.setSpeaking(false);
                this.vrmLoader.setLeaning(false);
                break;

            case AppState.LISTENING:
                this.micRing.classList.add('mic-pulse', 'border-blue-400/80');
                this.waveform.classList.remove('opacity-10');
                this.waveform.classList.add('opacity-100');
                const bars = this.waveform.querySelectorAll('div');
                bars.forEach(bar => bar.classList.remove('animate-wave-1', 'animate-wave-2', 'animate-wave-3'));
                this.statusText.classList.remove('opacity-0');
                this.statusText.innerText = "Listening...";
                this.vrmLoader.setLeaning(true);
                break;

            case AppState.THINKING:
                this.micButton.classList.add('opacity-50', 'cursor-not-allowed');
                this.loadingIndicator.classList.remove('opacity-0');
                this.statusText.innerText = "Thinking...";
                break;

            case AppState.SPEAKING:
                this.micButton.classList.add('opacity-50', 'cursor-not-allowed');
                this.waveform.classList.remove('opacity-10');
                this.waveform.classList.add('opacity-100');
                this.statusText.innerText = "Speaking...";
                this.vrmLoader.setSpeaking(true);
                break;
        }
    }

    startSession() {
        this.audioIO.startListening(
            (text) => this.processUserText(text),
            (error) => this.handleError(error)
        );
    }

    async processUserText(text) {
        this.addMessage('user', text);

        try {
            state.setState(AppState.THINKING);

            // Get reply and audio from API (using combined endpoint for better performance)
            const result = await chatFull(state.sessionId, text, this.history);

            if (result.status === 'success') {
                this.addMessage('miikun', result.reply_text);

                // Emotion handling
                if (result.emotion) {
                    this.vrmLoader.setEmotion(result.emotion);
                }

                // Audio Playback with Fallback
                if (result.audio) {
                    const audioUrl = `data:audio/wav;base64,${result.audio}`;
                    await this.audioIO.playTts(audioUrl, result.reply_text);
                } else {
                    // Fallback to browser TTS
                    await this.audioIO.playTts(null, result.reply_text);
                }

                // Update History
                this.history.push({ role: 'user', content: text });
                this.history.push({ role: 'assistant', content: result.reply_text });

                // Keep history manageable
                if (this.history.length > 20) {
                    this.history.splice(0, 2);
                }
            } else {
                throw new Error("API reported failure");
            }

        } catch (e) {
            this.handleError(e);
        } finally {
            state.setState(AppState.IDLE);
        }
    }

    addMessage(sender, text) {
        const div = document.createElement('div');
        div.className = `message message-${sender}`;
        div.innerText = (sender === 'miikun' ? 'Miikun: ' : '') + text;
        this.chatContainer.appendChild(div);

        // Auto scroll
        this.chatContainer.scrollTo({
            top: this.chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    handleError(error) {
        console.error("App Error:", error);
        const div = document.createElement('div');
        div.className = "message message-error";
        div.innerText = "聞き取れなかったみたい。もう一度言ってくれる？";
        this.chatContainer.appendChild(div);
        state.setState(AppState.IDLE);
    }
}

// Start App
document.addEventListener('DOMContentLoaded', () => {
    new MiikunApp();
});
