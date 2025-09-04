import { apiClient } from './apiClient.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Document API service
 */
export class DocumentApi {
    /**
     * Get documents status
     */
    static async getDocumentsStatus() {
        return apiClient.get(CONSTANTS.API.INGEST_STATUS);
    }
    
    /**
     * Trigger document ingestion
     */
    static async triggerIngestion() {
        return apiClient.post(CONSTANTS.API.INGEST, {});
    }
}
