import { apiClient } from './apiClient.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Session API service
 */
export class SessionApi {
    /**
     * Get all sessions
     */
    static async getSessions() {
        return apiClient.get(CONSTANTS.API.SESSIONS);
    }
    
    /**
     * Create new session
     */
    static async createSession(sessionId, title = 'Nouvelle conversation') {
        const payload = {
            session_id: sessionId,
            title
        };
        
        return apiClient.post(CONSTANTS.API.SESSIONS, payload);
    }
    
    /**
     * Get session history
     */
    static async getSessionHistory(sessionId) {
        return apiClient.get(`${CONSTANTS.API.SESSIONS}/${sessionId}/history`);
    }
    
    /**
     * Delete session
     */
    static async deleteSession(sessionId) {
        return apiClient.delete(`${CONSTANTS.API.SESSIONS}/${sessionId}`);
    }
}
