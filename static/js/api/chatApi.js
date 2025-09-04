import { apiClient } from './apiClient.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Chat API service
 */
export class ChatApi {
    /**
     * Send chat message
     */
    static async sendMessage(message, sessionId = null, selectedDocuments = [], llmProvider = CONSTANTS.LLM_PROVIDERS.MISTRAL) {
        const payload = {
            message,
            session_id: sessionId,
            selected_documents: selectedDocuments,
            llm_provider: llmProvider
        };
        
        return apiClient.post(CONSTANTS.API.CHAT, payload);
    }
}
