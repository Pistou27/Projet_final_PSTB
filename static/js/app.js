import { DOMUtils } from './utils/dom.js';
import { CONSTANTS } from './utils/constants.js';
import { stateManager } from './services/StateManager.js';
import { NotificationManager } from './components/NotificationManager.js';
import { MessageComponent } from './components/MessageComponent.js';
import { ChatApi } from './api/chatApi.js';
import { SessionApi } from './api/sessionApi.js';
import { DocumentApi } from './api/documentApi.js';

/**
 * Main application class
 */
class ChatApp {
    constructor() {
        this.elements = {};
        this.managers = {};
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        this._initElements();
        this._initManagers();
        this._initEventListeners();
        this._initStateSubscriptions();
        
        // Initial setup
        this._updateSendButton();
        this._focusInput();
        this._initializeSidebarState();
        
        // Load initial data
        await this._loadDocuments();
        this._updateLLMProviderButton();
        
        // Attach sidebar event listeners after DOM is fully ready
        this._attachSidebarEventListeners();
        
        console.log('Chat application initialized successfully');
        console.log('Event listeners attached to:', {
            toggleSidebarBtn: !!this.elements.toggleSidebarBtn,
            statusBtn: !!this.elements.statusBtn,
            ingestBtn: !!this.elements.ingestBtn,
            llmProviderBtn: !!this.elements.llmProviderBtn,
            toggleDocsBtn: !!this.elements.toggleDocsBtn
        });
    }
    
    /**
     * Initialize DOM elements
     */
    _initElements() {
        this.elements = {
            messagesContainer: DOMUtils.getElementById('messages'),
            messageInput: DOMUtils.getElementById('messageInput'),
            sendButton: DOMUtils.getElementById('sendButton'),
            statusBtn: DOMUtils.getElementById('statusBtn'),
            ingestBtn: DOMUtils.getElementById('ingestBtn'),
            sessionsSidebar: DOMUtils.getElementById('sessionsSidebar'),
            sessionsList: DOMUtils.getElementById('sessionsList'),
            documentsSidebar: DOMUtils.getElementById('documentsSidebar'),
            documentsList: DOMUtils.getElementById('documentsList'),
            llmProviderBtn: DOMUtils.getElementById('llmProviderBtn'),
            toggleSidebarBtn: DOMUtils.getElementById('toggleSidebarBtn'),
            toggleDocsBtn: DOMUtils.getElementById('toggleDocsBtn'),
            chatContainer: DOMUtils.getElementById('chatContainer')
        };
        
        // Debug: Log which elements were found
        console.log('DOM elements found:', Object.entries(this.elements).map(([key, value]) => [key, !!value]));
    }
    
    /**
     * Initialize managers
     */
    _initManagers() {
        this.managers.notification = new NotificationManager(this.elements.messagesContainer);
        this.managers.message = new MessageComponent(this.elements.messagesContainer);
    }
    
    /**
     * Initialize event listeners
     */
    _initEventListeners() {
        // Input events
        this.elements.messageInput?.addEventListener('input', () => this._updateSendButton());
        this.elements.messageInput?.addEventListener('keypress', (e) => this._handleKeyPress(e));
        
        // Button events
        this.elements.sendButton?.addEventListener('click', () => this._sendMessage());
        this.elements.toggleSidebarBtn?.addEventListener('click', () => this._toggleSidebar());
        this.elements.statusBtn?.addEventListener('click', () => this._checkDocumentsStatus());
        this.elements.ingestBtn?.addEventListener('click', () => this._triggerIngestion());
        this.elements.llmProviderBtn?.addEventListener('click', () => this._toggleLLMProvider());
        this.elements.toggleDocsBtn?.addEventListener('click', () => this._toggleDocumentsSidebar());
        
        // Global functions for backward compatibility
        window.toggleSidebar = () => {
            console.log('DEBUG: window.toggleSidebar called');
            this._toggleSidebar();
        };
        window.toggleDocumentsSidebar = () => {
            console.log('DEBUG: window.toggleDocumentsSidebar called');
            this._toggleDocumentsSidebar();
        };
        window.toggleLLMProvider = () => this._toggleLLMProvider();
        window.checkDocumentsStatus = () => this._checkDocumentsStatus();
        window.triggerIngestion = () => this._triggerIngestion();
        window.createNewSession = () => this._createNewSession();
        window.deleteAllSessions = () => this._deleteAllSessions();
        window.toggleSource = (sourceId) => this._toggleSource(sourceId);
        
        console.log('DEBUG: Global functions exposed:', {
            toggleSidebar: typeof window.toggleSidebar,
            toggleDocumentsSidebar: typeof window.toggleDocumentsSidebar
        });
    }
    
    /**
     * Attach sidebar event listeners (called after DOM is ready)
     */
    _attachSidebarEventListeners() {
        console.log('DEBUG: Attaching sidebar event listeners');
        
        // Close buttons for sidebars - use more specific selectors and search in all elements (even hidden)
        const closeSidebar = document.querySelector('#sessionsSidebar .close-sessions-btn');
        const closeDocs = document.querySelector('#documentsSidebar .close-docs-btn');
        
        console.log('DEBUG: Close buttons found:', {
            closeSidebar: !!closeSidebar,
            closeDocs: !!closeDocs
        });
        
        if (closeSidebar) {
            closeSidebar.addEventListener('click', (e) => {
                console.log('DEBUG: Close sidebar clicked via event listener');
                e.preventDefault();
                e.stopPropagation();
                this._toggleSidebar();
            });
        }
        
        if (closeDocs) {
            closeDocs.addEventListener('click', (e) => {
                console.log('DEBUG: Close docs clicked via event listener');
                e.preventDefault();
                e.stopPropagation();
                this._toggleDocumentsSidebar();
            });
        }
        
        // Session buttons
        const newSessionBtn = document.querySelector('.new-session-btn');
        const deleteAllBtn = document.querySelector('.delete-all-sessions-btn');
        const sessionCloseBtn = document.querySelector('.close-sessions-btn');
        const docsCloseBtn = document.querySelector('.close-docs-btn');
        
        console.log('Sidebar buttons found:', {
            newSessionBtn: !!newSessionBtn,
            deleteAllBtn: !!deleteAllBtn,
            sessionCloseBtn: !!sessionCloseBtn,
            docsCloseBtn: !!docsCloseBtn
        });
        
        // Use event delegation for reliability
        document.addEventListener('click', (e) => {
            // Debug: log all clicks to see what's happening
            if (e.target.matches('button')) {
                console.log('DEBUG: Button clicked - class:', e.target.className, 'text:', e.target.textContent.trim());
            }
            
            if (e.target.matches('.new-session-btn')) {
                e.preventDefault();
                console.log('New session button clicked (delegation)');
                this._createNewSession();
            } else if (e.target.matches('.delete-all-sessions-btn')) {
                e.preventDefault();
                console.log('Delete all sessions button clicked (delegation)');
                this._deleteAllSessions();
            } else if (e.target.matches('.close-sessions-btn') || 
                      (e.target.matches('.session-btn') && e.target.textContent.trim() === '✕')) {
                e.preventDefault();
                console.log('DEBUG: Session close button clicked (delegation) - class:', e.target.className);
                this._toggleSidebar();
            } else if (e.target.matches('.close-docs-btn') || 
                      (e.target.matches('.docs-toggle-btn') && e.target.textContent.trim() === '✕')) {
                e.preventDefault();
                console.log('DEBUG: Docs close button clicked (delegation) - class:', e.target.className);
                this._toggleDocumentsSidebar();
            }
        });
        
        // Direct event listeners as backup
        newSessionBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('New session button clicked (direct)');
            this._createNewSession();
        });
        deleteAllBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Delete all sessions button clicked (direct)');
            this._deleteAllSessions();
        });
        sessionCloseBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Session close button clicked (direct)');
            this._toggleSidebar();
        });
        docsCloseBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Docs close button clicked (direct)');
            this._toggleDocumentsSidebar();
        });
        
        console.log('Sidebar event listeners attached');
    }
    
    /**
     * Initialize state subscriptions
     */
    _initStateSubscriptions() {
        // Subscribe to loading state changes
        stateManager.subscribe('isLoading', (isLoading) => {
            this._updateSendButton();
        });
        
        // Subscribe to sessions visibility changes
        stateManager.subscribe('sessionsVisible', (visible) => {
            this._updateSidebarVisibility(visible);
        });
        
        // Subscribe to LLM provider changes
        stateManager.subscribe('currentLLMProvider', (provider) => {
            this._updateLLMProviderButton();
            this.managers.notification.info(
                `🤖 Basculé vers ${provider === CONSTANTS.LLM_PROVIDERS.GROQ ? 'Groq Cloud' : 'Mistral Local'}`
            );
        });
    }
    
    /**
     * Handle key press events
     */
    _handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._sendMessage();
        }
    }
    
    /**
     * Update send button state
     */
    _updateSendButton() {
        const hasText = this.elements.messageInput?.value.trim().length > 0;
        const isLoading = stateManager.getState('isLoading');
        
        if (this.elements.sendButton) {
            this.elements.sendButton.disabled = !hasText || isLoading;
        }
    }
    
    /**
     * Focus input
     */
    _focusInput() {
        this.elements.messageInput?.focus();
    }
    
    /**
     * Send message
     */
    async _sendMessage() {
        const message = this.elements.messageInput?.value.trim();
        if (!message || stateManager.getState('isLoading')) return;
        
        // Add user message
        this.managers.message.add(message, CONSTANTS.MESSAGE_TYPES.USER);
        this.elements.messageInput.value = '';
        this._updateSendButton();
        
        // Set loading state
        stateManager.setLoading(true);
        const loading = this.managers.notification.showLoading();
        
        try {
            const currentSessionId = stateManager.getState('currentSessionId');
            const selectedDocuments = Array.from(stateManager.getState('selectedDocuments'));
            const llmProvider = stateManager.getState('currentLLMProvider');
            
            const result = await ChatApi.sendMessage(message, currentSessionId, selectedDocuments, llmProvider);
            
            if (result.success && result.data.response) {
                // Update session ID if created
                if (result.data.session_id && !currentSessionId) {
                    stateManager.setCurrentSession(result.data.session_id);
                    await this._loadSessions();
                }
                
                // Add response
                this.managers.message.add(
                    result.data.response,
                    CONSTANTS.MESSAGE_TYPES.ASSISTANT,
                    result.data.sources,
                    result.data.llm_provider
                );
            } else {
                this.managers.notification.error(
                    `❌ Erreur: ${result.data?.error || result.error || 'Erreur inconnue'}`
                );
            }
            
        } catch (error) {
            console.error('Send message error:', error);
            this.managers.notification.error(`❌ Erreur de connexion: ${error.message}`);
        } finally {
            loading.stop();
            stateManager.setLoading(false);
        }
    }
    
    /**
     * Toggle sidebar visibility
     */
    _toggleSidebar() {
        console.log('DEBUG: _toggleSidebar method called');
        stateManager.toggleSessionsVisibility();
    }
    
    /**
     * Update sidebar visibility
     */
    _updateSidebarVisibility(visible) {
        const sidebar = this.elements.sessionsSidebar;
        const container = this.elements.chatContainer;
        const toggleBtn = this.elements.toggleSidebarBtn;
        
        if (visible) {
            DOMUtils.removeClass(sidebar, 'hidden');
            DOMUtils.removeClass(container, 'sidebar-hidden');
            if (toggleBtn) toggleBtn.innerHTML = '💬 Sessions';
            this._loadSessions();
        } else {
            DOMUtils.addClass(sidebar, 'hidden');
            DOMUtils.addClass(container, 'sidebar-hidden');
            if (toggleBtn) toggleBtn.innerHTML = '💬 Afficher';
        }
    }
    
    /**
     * Initialize sidebar state
     */
    _initializeSidebarState() {
        const visible = stateManager.getState('sessionsVisible');
        this._updateSidebarVisibility(visible);
    }
    
    /**
     * Toggle LLM provider
     */
    _toggleLLMProvider() {
        console.log('Toggle LLM provider called');
        stateManager.toggleLLMProvider();
    }
    
    /**
     * Update LLM provider button
     */
    _updateLLMProviderButton() {
        const provider = stateManager.getState('currentLLMProvider');
        const btn = this.elements.llmProviderBtn;
        
        if (!btn) return;
        
        if (provider === CONSTANTS.LLM_PROVIDERS.GROQ) {
            btn.innerHTML = '🚀 Groq';
            btn.title = 'Utiliser Groq Cloud (llama-3.3-70b-versatile)';
            btn.style.backgroundColor = '#4CAF50';
        } else {
            btn.innerHTML = '🤖 Mistral';
            btn.title = 'Utiliser Mistral Local';
            btn.style.backgroundColor = '#2196F3';
        }
    }
    
    /**
     * Toggle documents sidebar
     */
    _toggleDocumentsSidebar() {
        console.log('DEBUG: _toggleDocumentsSidebar method called');
        const sidebar = this.elements.documentsSidebar;
        const toggleBtn = this.elements.toggleDocsBtn;
        
        if (!sidebar || !toggleBtn) {
            console.warn('Documents sidebar elements not found');
            return;
        }
        
        const isHidden = DOMUtils.toggleClass(sidebar, 'hidden');
        
        if (isHidden) {
            toggleBtn.innerHTML = '📚 Afficher Règles';
            toggleBtn.title = 'Afficher les documents';
        } else {
            toggleBtn.innerHTML = '📚 Règles';
            toggleBtn.title = 'Masquer les documents';
        }
        
        console.log('Documents sidebar toggled:', isHidden ? 'hidden' : 'visible');
    }
    
    /**
     * Check documents status
     */
    async _checkDocumentsStatus() {
        console.log('Check documents status called');
        const btn = this.elements.statusBtn;
        if (!btn) return;
        
        btn.disabled = true;
        btn.textContent = '🔄 Vérification...';
        
        try {
            const result = await DocumentApi.getDocumentsStatus();
            
            if (result.success && result.data.success) {
                const data = result.data;
                if (data.all_document_names && data.all_document_names.length > 0) {
                    const documentsList = data.all_document_names.join(', ');
                    const statusText = data.index_exists ? '✅ Documents indexés' : '📄 Documents disponibles';
                    
                    const message = `📚 <strong>${statusText} :</strong><br>${documentsList}`;
                    this.managers.notification.show(message, data.index_exists ? 'success' : 'info');
                } else {
                    this.managers.notification.error(
                        '📭 <strong>Aucun document trouvé</strong><br>Veuillez ajouter des fichiers PDF dans le dossier data/'
                    );
                }
            } else {
                this.managers.notification.error(
                    `❌ Erreur lors de la vérification : ${result.data?.message || result.error}`
                );
            }
        } catch (error) {
            this.managers.notification.error(`❌ Erreur de connexion : ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '📊 Statut Documents';
        }
    }
    
    /**
     * Trigger document ingestion
     */
    async _triggerIngestion() {
        console.log('Trigger ingestion called');
        const btn = this.elements.ingestBtn;
        if (!btn) return;
        
        btn.disabled = true;
        btn.textContent = '🔄 Indexation...';
        
        this.managers.notification.info(
            '🚀 <strong>Début de l\'indexation des documents...</strong><br>Cette opération peut prendre quelques minutes.'
        );
        
        try {
            const result = await DocumentApi.triggerIngestion();
            
            if (result.success && result.data.success) {
                const data = result.data;
                const processed = data.processed_documents || 0;
                const chunks = data.total_chunks || 0;
                const skipped = data.stats ? data.stats.files_skipped || 0 : 0;
                const processing_time = data.processing_time || "Non disponible";
                
                let message;
                if (chunks > 0) {
                    message = `✅ <strong>Indexation terminée avec succès !</strong><br>
                        • Documents traités : <strong>${processed}</strong><br>
                        • Chunks créés : <strong>${chunks}</strong><br>
                        • Temps de traitement : <strong>${processing_time}</strong>`;
                } else if (skipped > 0) {
                    message = `ℹ️ <strong>Indexation terminée !</strong><br>
                        • Documents déjà indexés : <strong>${skipped}</strong><br>
                        • Nouveaux chunks : <strong>${chunks}</strong><br>
                        • Temps de traitement : <strong>${processing_time}</strong><br>
                        <em>Tous les documents sont déjà à jour dans l'index.</em>`;
                } else {
                    message = `✅ <strong>Indexation terminée !</strong><br>
                        • Documents traités : <strong>${processed}</strong><br>
                        • Chunks créés : <strong>${chunks}</strong><br>
                        • Temps de traitement : <strong>${processing_time}</strong>`;
                }
                
                this.managers.notification.show(message, chunks > 0 ? 'success' : 'info');
            } else {
                this.managers.notification.error(`❌ Erreur lors de l'indexation : ${result.data?.error || result.error}`);
            }
        } catch (error) {
            this.managers.notification.error(`❌ Erreur de connexion : ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '📂 Indexer Documents';
        }
    }
    
    /**
     * Load sessions
     */
    async _loadSessions() {
        try {
            const result = await SessionApi.getSessions();
            
            if (result.success && result.data.success) {
                this._displaySessions(result.data.sessions);
            } else {
                console.error('Error loading sessions:', result.data?.error || result.error);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }
    
    /**
     * Display sessions in sidebar
     */
    _displaySessions(sessions) {
        const container = this.elements.sessionsList;
        if (!container) return;
        
        container.innerHTML = '';
        
        if (sessions.length === 0) {
            container.innerHTML = '<div style="padding: 1rem; text-align: center; color: #6c757d;">Aucune session trouvée</div>';
            return;
        }
        
        const currentSessionId = stateManager.getState('currentSessionId');
        
        sessions.forEach(session => {
            const sessionDiv = document.createElement('div');
            sessionDiv.className = `session-item ${session.session_id === currentSessionId ? 'active' : ''}`;
            sessionDiv.onclick = () => this._selectSession(session.session_id);
            
            const lastActivity = DOMUtils.formatDate(session.last_activity);
            
            sessionDiv.innerHTML = `
                <div class="session-title">${session.title || 'Session sans titre'}</div>
                <div class="session-meta">
                    ${session.message_count} messages • ${lastActivity}
                    <button class="session-btn delete" onclick="event.stopPropagation(); window.deleteSession('${session.session_id}')">
                        🗑️
                    </button>
                </div>
            `;
            
            container.appendChild(sessionDiv);
        });
        
        // Add global function for session deletion
        window.deleteSession = (sessionId) => this._deleteSession(sessionId);
    }
    
    /**
     * Create new session
     */
    async _createNewSession() {
        console.log('Create new session called');
        try {
            const sessionId = 'session_' + Date.now();
            const result = await SessionApi.createSession(sessionId, 'Nouvelle conversation');
            
            if (result.success && result.data.success) {
                stateManager.setCurrentSession(sessionId);
                this.managers.message.clear();
                await this._loadSessions();
                this.managers.notification.success('✅ Nouvelle session créée !');
            } else {
                this.managers.notification.error(`❌ Erreur lors de la création : ${result.data?.error || result.error}`);
            }
        } catch (error) {
            this.managers.notification.error(`❌ Erreur de connexion : ${error.message}`);
        }
    }
    
    /**
     * Select session
     */
    async _selectSession(sessionId) {
        const currentSessionId = stateManager.getState('currentSessionId');
        if (sessionId === currentSessionId) return;
        
        stateManager.setCurrentSession(sessionId);
        this.managers.message.clear();
        
        try {
            const result = await SessionApi.getSessionHistory(sessionId);
            
            if (result.success && result.data.success) {
                this.managers.message.loadHistory(result.data.history);
                await this._loadSessions(); // Refresh to update active state
                this.managers.notification.info(`📂 Session chargée (${result.data.history.length} messages)`);
            } else {
                this.managers.notification.error(`❌ Erreur lors du chargement : ${result.data?.error || result.error}`);
            }
        } catch (error) {
            this.managers.notification.error(`❌ Erreur de connexion : ${error.message}`);
        }
    }
    
    /**
     * Delete session
     */
    async _deleteSession(sessionId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette session ?')) return;
        
        try {
            const result = await SessionApi.deleteSession(sessionId);
            
            if (result.success && result.data.success) {
                const currentSessionId = stateManager.getState('currentSessionId');
                if (sessionId === currentSessionId) {
                    stateManager.setCurrentSession(null);
                    this.managers.message.clear();
                }
                await this._loadSessions();
                this.managers.notification.success('✅ Session supprimée !');
            } else {
                this.managers.notification.error(`❌ Erreur lors de la suppression : ${result.data?.error || result.error}`);
            }
        } catch (error) {
            this.managers.notification.error(`❌ Erreur de connexion : ${error.message}`);
        }
    }
    
    /**
     * Delete all sessions
     */
    async _deleteAllSessions() {
        if (!confirm('⚠️ Êtes-vous sûr de vouloir supprimer TOUTES les sessions ? Cette action est irréversible !')) return;
        
        const deleteAllBtn = document.querySelector('.delete-all-sessions-btn');
        if (deleteAllBtn) {
            deleteAllBtn.disabled = true;
            deleteAllBtn.textContent = '🔄 Suppression...';
        }
        
        try {
            // Get all sessions first
            const sessionsResult = await SessionApi.getSessions();
            
            if (!sessionsResult.success || !sessionsResult.data.success) {
                throw new Error('Impossible de récupérer la liste des sessions');
            }
            
            const sessions = sessionsResult.data.sessions;
            if (sessions.length === 0) {
                this.managers.notification.info('ℹ️ Aucune session à supprimer.');
                return;
            }
            
            // Delete each session
            let deletedCount = 0;
            let errors = 0;
            
            for (const session of sessions) {
                try {
                    const result = await SessionApi.deleteSession(session.session_id);
                    if (result.success && result.data.success) {
                        deletedCount++;
                    } else {
                        errors++;
                    }
                } catch (error) {
                    errors++;
                }
            }
            
            // Reset current session
            stateManager.setCurrentSession(null);
            this.managers.message.clear();
            
            // Refresh sessions list
            await this._loadSessions();
            
            // Show result notification
            if (errors === 0) {
                this.managers.notification.success(`✅ Toutes les sessions ont été supprimées ! (${deletedCount} sessions)`);
            } else {
                this.managers.notification.error(`⚠️ ${deletedCount} sessions supprimées, ${errors} erreurs.`);
            }
            
        } catch (error) {
            this.managers.notification.error(`❌ Erreur lors de la suppression : ${error.message}`);
        } finally {
            if (deleteAllBtn) {
                deleteAllBtn.disabled = false;
                deleteAllBtn.textContent = '🗑️ Supprimer Toutes les Sessions';
            }
        }
    }
    
    /**
     * Load documents
     */
    async _loadDocuments() {
        try {
            const result = await DocumentApi.getDocumentsStatus();
            
            if (result.success && result.data.success && result.data.document_names) {
                this._displayDocuments(result.data.document_names);
                
                // Select only the first document by default
                const selectedDocs = result.data.document_names.length > 0 
                    ? [result.data.document_names[0].filename] 
                    : [];
                stateManager.setSelectedDocuments(selectedDocs);
                this._updateDocumentSelection();
            } else {
                const container = this.elements.documentsList;
                if (container) {
                    container.innerHTML = '<div style="padding: 1rem; text-align: center; color: #6c757d;">Aucun document trouvé</div>';
                }
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            const container = this.elements.documentsList;
            if (container) {
                container.innerHTML = '<div style="padding: 1rem; text-align: center; color: #dc3545;">Erreur de chargement</div>';
            }
        }
    }
    
    /**
     * Display documents
     */
    _displayDocuments(documents) {
        const container = this.elements.documentsList;
        if (!container) return;
        
        container.innerHTML = '';
        
        documents.forEach(doc => {
            const docDiv = document.createElement('div');
            docDiv.className = 'document-item';
            docDiv.onclick = () => this._toggleDocumentSelection(doc.filename);
            
            const selectedDocuments = stateManager.getState('selectedDocuments');
            const isSelected = selectedDocuments.has(doc.filename);
            
            // Create embedding models display
            let embeddingInfo = '';
            if (doc.embedding_models && doc.embedding_models.length > 0) {
                const embeddingList = doc.embedding_models.map(model => {
                    if (model.includes('all-MiniLM-L6-v2')) return 'MiniLM-L6-v2';
                    if (model.includes('bge-m3')) return 'BGE-M3';
                    if (model.includes('BAAI/bge-m3')) return 'BGE-M3';
                    if (model.includes('sentence-transformers/all-MiniLM-L6-v2')) return 'MiniLM-L6-v2';
                    const parts = model.split('/');
                    return parts[parts.length - 1] || model;
                }).join(', ');
                embeddingInfo = `<div class="document-embeddings">🔗 ${embeddingList}</div>`;
            } else {
                embeddingInfo = '<div class="document-embeddings no-embeddings">❌ Non indexé</div>';
            }
            
            docDiv.innerHTML = `
                <div class="document-header">
                    <input type="checkbox" class="document-checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="window.toggleDocumentSelection('${doc.filename}')">
                    <div class="document-name">${doc.display_name}</div>
                    <div class="document-status ${doc.has_embeddings ? 'embedded' : 'not-embedded'}">
                        ${doc.has_embeddings ? '✅' : '❌'}
                    </div>
                </div>
                ${embeddingInfo}
            `;
            
            if (isSelected) {
                DOMUtils.addClass(docDiv, 'selected');
            }
            
            container.appendChild(docDiv);
        });
        
        // Add global function for document selection
        window.toggleDocumentSelection = (filename) => this._toggleDocumentSelection(filename);
    }
    
    /**
     * Toggle document selection
     */
    _toggleDocumentSelection(filename) {
        // Clear all selections first (radio button behavior)
        stateManager.setSelectedDocuments([filename]);
        this._updateDocumentSelection();
    }
    
    /**
     * Update document selection display
     */
    _updateDocumentSelection() {
        const container = this.elements.documentsList;
        if (!container) return;
        
        const checkboxes = container.querySelectorAll('.document-checkbox');
        const items = container.querySelectorAll('.document-item');
        const selectedDocuments = stateManager.getState('selectedDocuments');
        
        checkboxes.forEach((checkbox, index) => {
            const item = items[index];
            const filename = checkbox.getAttribute('onchange').match(/'([^']+)'/)[1];
            
            const isSelected = selectedDocuments.has(filename);
            checkbox.checked = isSelected;
            
            if (isSelected) {
                DOMUtils.addClass(item, 'selected');
            } else {
                DOMUtils.removeClass(item, 'selected');
            }
        });
        
        console.log('Selected documents:', Array.from(selectedDocuments));
    }
    
    /**
     * Toggle source content visibility
     */
    _toggleSource(sourceId) {
        const sourceContent = document.getElementById(sourceId);
        const toggle = sourceContent?.previousElementSibling?.querySelector('.source-toggle');
        
        if (sourceContent && toggle) {
            if (sourceContent.style.display === 'none') {
                sourceContent.style.display = 'block';
                toggle.textContent = '▲';
                toggle.style.transform = 'rotate(180deg)';
            } else {
                sourceContent.style.display = 'none';
                toggle.textContent = '▼';
                toggle.style.transform = 'rotate(0deg)';
            }
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
