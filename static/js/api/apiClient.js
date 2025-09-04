import { CONSTANTS } from '../utils/constants.js';

/**
 * Centralized API client for all HTTP requests
 */
export class ApiClient {
    constructor() {
        this.baseHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    /**
     * Generic fetch wrapper with error handling
     */
    async request(url, options = {}) {
        try {
            const config = {
                headers: this.baseHeaders,
                ...options
            };
            
            if (config.body && typeof config.body === 'object') {
                config.body = JSON.stringify(config.body);
            } else if (config.body === null || config.body === undefined) {
                // Si body est null/undefined, on l'enlève pour éviter les erreurs
                delete config.body;
            }
            
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return { success: true, data };
            
        } catch (error) {
            console.error(`API request failed for ${url}:`, error);
            return { 
                success: false, 
                error: error.message,
                originalError: error 
            };
        }
    }
    
    /**
     * GET request
     */
    async get(url) {
        return this.request(url, { method: 'GET' });
    }
    
    /**
     * POST request
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: data
        });
    }
    
    /**
     * PUT request
     */
    async put(url, data = null) {
        return this.request(url, {
            method: 'PUT',
            body: data
        });
    }
    
    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// Create singleton instance
export const apiClient = new ApiClient();
