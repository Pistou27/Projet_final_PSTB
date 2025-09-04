/**
 * Constants for the RAG Chat application
 */
export const CONSTANTS = {
    // API Endpoints
    API: {
        CHAT: '/api/chat',
        SESSIONS: '/api/sessions',
        INGEST: '/api/ingest',
        INGEST_STATUS: '/api/ingest/status'
    },
    
    // LLM Providers
    LLM_PROVIDERS: {
        MISTRAL: 'mistral',
        GROQ: 'groq'
    },
    
    // Message types
    MESSAGE_TYPES: {
        USER: 'user',
        ASSISTANT: 'assistant'
    },
    
    // Notification types
    NOTIFICATION_TYPES: {
        INFO: 'info',
        SUCCESS: 'success',
        ERROR: 'error'
    },
    
    // Local storage keys
    STORAGE_KEYS: {
        SIDEBAR_HIDDEN: 'sidebarHidden',
        SELECTED_DOCUMENTS: 'selectedDocuments',
        LLM_PROVIDER: 'llmProvider'
    },
    
    // UI Constants
    UI: {
        MAX_SOURCES_DISPLAY: 5,
        LOADING_ANIMATION_INTERVAL: 500,
        MESSAGE_INPUT_MAX_LENGTH: 1000
    },
    
    // No info detection phrases
    NO_INFO_PHRASES: [
        "il n'y a pas d'information",
        "aucune information",
        "pas d'information sur",
        "ne contient pas d'information",
        "n'est pas mentionné",
        "pas de mention",
        "contexte ne contient pas",
        "documents ne contiennent pas",
        "je ne trouve pas d'information",
        "il n'existe pas d'indication",
        "aucune indication",
        "pas d'indication sur",
        "ne présente pas d'information",
        "n'indique pas",
        "pas précisé",
        "non mentionné",
        "absent des documents"
    ]
};
