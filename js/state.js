export const AppState = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking'
};

function generateUUID() {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
            (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        );
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

class StateManager {
    constructor() {
        this.currentState = AppState.IDLE;
        this.listeners = [];
        this.sessionId = this._getOrCreateSessionId();
        this.currentSubject = 'general';
        this.isOptedOut = this._checkOptOut();
    }

    _getOrCreateSessionId() {
        let sid = localStorage.getItem('miikun_session_id');
        if (!sid) {
            sid = generateUUID();
            localStorage.setItem('miikun_session_id', sid);
        }
        return sid;
    }

    _checkOptOut() {
        const urlParams = new URLSearchParams(window.location.search);
        const optoutParam = urlParams.get('optout');

        if (optoutParam === 'true') {
            localStorage.setItem('miikun_optout', 'true');
            return true;
        }

        return localStorage.getItem('miikun_optout') === 'true';
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
