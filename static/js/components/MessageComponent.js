import { DOMUtils } from '../utils/dom.js';
import { CONSTANTS } from '../utils/constants.js';

/**
 * Message component for rendering chat messages
 */
export class MessageComponent {
    constructor(container) {
        this.container = container;
    }
    
    /**
     * Add message to chat
     */
    add(content, type, sources = null, llmProvider = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.id = DOMUtils.generateId('msg');
        
        let messageContent = this._formatContent(content, type, llmProvider);
        messageDiv.innerHTML = messageContent;
        
        // Add sources if provided and appropriate
        if (sources && sources.length > 0 && !this._hasNoInfoIndication(messageContent)) {
            const sourcesDiv = this._createSourcesDiv(messageDiv.id, sources);
            messageDiv.appendChild(sourcesDiv);
        }
        
        this.container.appendChild(messageDiv);
        DOMUtils.scrollToBottom(this.container);
        
        return messageDiv;
    }
    
    /**
     * Format message content
     */
    _formatContent(content, type, llmProvider = null) {
        let messageContent = '';
        
        if (type === CONSTANTS.MESSAGE_TYPES.USER) {
            messageContent = DOMUtils.escapeHtml(content);
        } else {
            messageContent = content; // Assistant messages can contain HTML
            
            // Add LLM provider badge for assistant messages
            if (llmProvider) {
                const providerBadge = this._createProviderBadge(llmProvider);
                messageContent = providerBadge + '<br>' + messageContent;
            }
        }
        
        return messageContent;
    }
    
    /**
     * Create LLM provider badge
     */
    _createProviderBadge(llmProvider) {
        return llmProvider === CONSTANTS.LLM_PROVIDERS.GROQ ? 
            '<span class="llm-badge groq-badge">🚀 Groq</span>' : 
            '<span class="llm-badge mistral-badge">🤖 Mistral</span>';
    }
    
    /**
     * Check if message indicates no information found
     */
    _hasNoInfoIndication(messageContent) {
        const responseText = messageContent.toLowerCase();
        return CONSTANTS.NO_INFO_PHRASES.some(phrase => responseText.includes(phrase));
    }
    
    /**
     * Create sources div
     */
    _createSourcesDiv(messageId, sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        
        const maxSources = CONSTANTS.UI.MAX_SOURCES_DISPLAY;
        const displaySources = sources.slice(0, maxSources);
        const remainingSources = sources.length - maxSources;
        
        let sourcesHtml = '<strong>📚 Sources :</strong><br>' + 
            displaySources.map((source, index) => this._createSourceItem(messageId, source, index)).join('');
        
        // Add indicator for additional sources
        if (remainingSources > 0) {
            sourcesHtml += this._createMoreSourcesIndicator(remainingSources, sources.length);
        }
        
        sourcesDiv.innerHTML = sourcesHtml;
        return sourcesDiv;
    }
    
    /**
     * Create individual source item
     */
    _createSourceItem(messageId, source, index) {
        const sourceId = `${messageId}_src_${index}`;
        return `
            <div class="source-item">
                <div class="source-header" onclick="toggleSource('${sourceId}')">
                    <span>• ${source.document} (page ${source.page})</span>
                    <span class="source-toggle">▼</span>
                </div>
                <div class="source-content" id="${sourceId}" style="display: none; margin-left: 20px; margin-top: 5px; padding: 10px; background-color: #f5f5f5; border-radius: 5px; font-size: 0.9em; color: #555;">
                    ${source.content_preview || 'Contenu non disponible'}
                </div>
            </div>
        `;
    }
    
    /**
     * Create more sources indicator
     */
    _createMoreSourcesIndicator(remainingSources, totalSources) {
        return `
            <div class="more-sources-indicator" style="margin-top: 10px; padding: 8px; background-color: #e9ecef; border-radius: 5px; font-size: 0.85em; color: #6c757d; text-align: center; font-style: italic;">
                📋 ... et ${remainingSources} source${remainingSources > 1 ? 's' : ''} supplémentaire${remainingSources > 1 ? 's' : ''} (${totalSources} au total)
            </div>
        `;
    }
    
    /**
     * Clear all messages
     */
    clear() {
        this.container.innerHTML = '';
        // Add default welcome message
        this.add(
            '👋 Bonjour ! Je suis votre assistant IA spécialisé dans l\'analyse de documents.<br>Posez-moi des questions sur les documents disponibles et je vous répondrai en français avec les références des pages sources.',
            CONSTANTS.MESSAGE_TYPES.ASSISTANT
        );
    }
    
    /**
     * Load session history
     */
    loadHistory(history) {
        this.clear();
        
        history.forEach(exchange => {
            this.add(exchange.user_message, CONSTANTS.MESSAGE_TYPES.USER);
            this.add(exchange.assistant_response, CONSTANTS.MESSAGE_TYPES.ASSISTANT, exchange.sources);
        });
    }
}
