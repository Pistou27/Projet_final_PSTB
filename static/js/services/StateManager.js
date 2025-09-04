import { StorageUtils } from '../utils/storage.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Global state manager for the application
 */
export class StateManager {
    constructor() {
        this.state = {
            isLoading: false,
            currentSessionId: null,
            sessionsVisible: false,
            selectedDocuments: new Set(),
            currentLLMProvider: CONSTANTS.LLM_PROVIDERS.MISTRAL
        };
        
        this.listeners = new Map();
        this._loadFromStorage();
    }
    
    /**
     * Subscribe to state changes
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
        
        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(key);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index > -1) {
                    callbacks.splice(index, 1);
                }
            }
        };
    }
    
    /**
     * Update state and notify listeners
     */
    setState(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        
        // Save to storage if needed
        this._saveToStorage(key, value);
        
        // Notify listeners
        const callbacks = this.listeners.get(key);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(value, oldValue);
                } catch (error) {
                    console.error('State listener error:', error);
                }
            });
        }
    }
    
    /**
     * Get state value
     */
    getState(key) {
        return this.state[key];
    }
    
    /**
     * Get all state
     */
    getAllState() {
        return { ...this.state };
    }
    
    /**
     * Load persistent state from storage
     */
    _loadFromStorage() {
        // Load sidebar visibility
        const sidebarHidden = StorageUtils.get(CONSTANTS.STORAGE_KEYS.SIDEBAR_HIDDEN, false);
        this.state.sessionsVisible = !sidebarHidden;
        
        // Load selected documents
        const selectedDocs = StorageUtils.get(CONSTANTS.STORAGE_KEYS.SELECTED_DOCUMENTS, []);
        this.state.selectedDocuments = new Set(selectedDocs);
        
        // Load LLM provider
        const llmProvider = StorageUtils.get(CONSTANTS.STORAGE_KEYS.LLM_PROVIDER, CONSTANTS.LLM_PROVIDERS.MISTRAL);
        this.state.currentLLMProvider = llmProvider;
    }
    
    /**
     * Save state to storage
     */
    _saveToStorage(key, value) {
        switch (key) {
            case 'sessionsVisible':
                StorageUtils.set(CONSTANTS.STORAGE_KEYS.SIDEBAR_HIDDEN, !value);
                break;
            case 'selectedDocuments':
                StorageUtils.set(CONSTANTS.STORAGE_KEYS.SELECTED_DOCUMENTS, Array.from(value));
                break;
            case 'currentLLMProvider':
                StorageUtils.set(CONSTANTS.STORAGE_KEYS.LLM_PROVIDER, value);
                break;
        }
    }
    
    // Convenience methods for common state operations
    
    /**
     * Set loading state
     */
    setLoading(isLoading) {
        this.setState('isLoading', isLoading);
    }
    
    /**
     * Set current session
     */
    setCurrentSession(sessionId) {
        this.setState('currentSessionId', sessionId);
    }
    
    /**
     * Toggle sessions visibility
     */
    toggleSessionsVisibility() {
        this.setState('sessionsVisible', !this.state.sessionsVisible);
    }
    
    /**
     * Set selected documents
     */
    setSelectedDocuments(documents) {
        this.setState('selectedDocuments', new Set(documents));
    }
    
    /**
     * Toggle LLM provider
     */
    toggleLLMProvider() {
        const newProvider = this.state.currentLLMProvider === CONSTANTS.LLM_PROVIDERS.MISTRAL 
            ? CONSTANTS.LLM_PROVIDERS.GROQ 
            : CONSTANTS.LLM_PROVIDERS.MISTRAL;
        this.setState('currentLLMProvider', newProvider);
    }
}

// Create singleton instance
export const stateManager = new StateManager();
