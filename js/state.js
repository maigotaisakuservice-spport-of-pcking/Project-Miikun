export const AppState = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking'
};

class StateManager {
    constructor() {
        this.currentState = AppState.IDLE;
        this.listeners = [];
        this.sessionId = this._getOrCreateSessionId();
        this.currentSubject = 'general';
    }

    _getOrCreateSessionId() {
        let sid = localStorage.getItem('miikun_session_id');
        if (!sid) {
            sid = crypto.randomUUID();
            localStorage.setItem('miikun_session_id', sid);
        }
        return sid;
    }

    setState(newState) {
        if (this.currentState === newState) return;
        this.currentState = newState;
        this.notify(newState);
    }

    getState() {
        return this.currentState;
    }

    subscribe(callback) {
        this.listeners.push(callback);
    }

    notify(state) {
        this.listeners.forEach(cb => cb(state));
    }

    setSubject(subject) {
        this.currentSubject = subject;
        this.notify(this.currentState); // Refresh UI if needed
    }
}

export const state = new StateManager();
