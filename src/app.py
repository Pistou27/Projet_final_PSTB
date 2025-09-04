"""
Application Flask - Interface web et API pour le système RAG
"""
import os
import uuid
from flask import Flask, render_template, request, jsonify, session

# Local imports
from config import Config
from rag_qdrant import RAGPipeline, Logger
from rag_qdrant.config import RAGConfig
from memory_store import MemoryStore
from utils import now_utc_iso, now_formatted

# Initialisation Flask avec les bons chemins
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.urandom(24)

# Instances globales
rag_pipeline = None
memory_store = None

def initialize_app():
    """Initialiser l'application et le pipeline RAG"""
    global rag_pipeline, memory_store
    
    Logger.info("🚀 Initialisation de l'application Flask...")
    
    try:
        rag_pipeline = RAGPipeline()
        memory_store = MemoryStore()
        Logger.success("✅ Application initialisée avec succès")
        return True
            
    except Exception as e:
        Logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        return False

@app.route('/')
def index():
    """Page d'accueil avec interface de chat"""
    return render_template('chat.html')

# @app.route('/new')
# def index_new():
#     """Page d'accueil avec la nouvelle interface modulaire"""
#     return render_template('chat_new.html')

# @app.route('/test')
# def test_suite():
#     """Page de tests pour comparer les versions"""
#     return render_template('test_suite.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint API pour les requêtes de chat"""
    global rag_pipeline
    
    if not rag_pipeline:
        return jsonify({
            "error": "Système non initialisé",
            "message": "Le système RAG n'est pas encore prêt. Veuillez réessayer."
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Message manquant",
                "message": "Veuillez fournir un message."
            }), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({
                "error": "Message vide",
                "message": "Veuillez saisir un message non vide."
            }), 400
        
        # Gérer les sessions
        session_id = data.get('session_id')
        selected_documents = data.get('selected_documents', [])
        llm_provider = data.get('llm_provider', 'mistral')  # Par défaut Mistral
        
        # Convertir les noms de fichiers en doc_ids (supprimer l'extension)
        doc_ids = []
        if selected_documents:
            for doc_name in selected_documents:
                if '.' in doc_name:
                    doc_id = doc_name.rsplit('.', 1)[0]  # Supprimer l'extension
                else:
                    doc_id = doc_name
                doc_ids.append(doc_id)
        
        if not session_id:
            # Créer une nouvelle session
            session_id = str(uuid.uuid4())
            # Créer la session dans la base de données
            if memory_store:
                memory_store.create_session(session_id, "Nouvelle conversation")
        
        # Utiliser le nouveau pipeline RAG
        response = rag_pipeline.search(
            query=user_message,
            doc_ids=doc_ids if doc_ids else None,
            limit=RAGConfig.DEFAULT_TOP_K,
            use_reranking=True,
            llm_provider=llm_provider  # Ajout du paramètre LLM
        )
        
        if not response.success:
            return jsonify({
                "error": "Erreur de recherche",
                "message": response.error_message or "Erreur inconnue"
            }), 500
        
        # Préparer les sources pour la réponse
        sources_info = []
        # Utiliser response.sources au lieu de response.citations
        # Seulement si il y a des sources (pas d'absence d'information détectée)
        if response.sources:
            for source in response.sources:
                if isinstance(source, dict):
                    sources_info.append({
                        "document": source.get("doc_id", "Document inconnu"),  # Changé de "source" à "document"
                        "page": source.get("page", "N/A"),
                        "content_preview": source.get("content", f"Extrait du document {source.get('doc_id')}"),
                        "embedding_model": "BGE-M3"
                    })
                else:
                    sources_info.append({
                        "document": str(source),  # Changé de "source" à "document"
                        "page": "N/A",
                        "content_preview": "Source",
                        "embedding_model": "BGE-M3"
                    })
            Logger.info(f"📚 {len(sources_info)} sources préparées pour l'affichage")
        else:
            Logger.info("🚫 Aucune source à afficher (absence d'information détectée)")
        
        # Préparer le texte pour l'affichage HTML
        response_text = response.answer
        Logger.info(f"🔍 Réponse answer reçue: {response_text[:100]}...")
        # Convertir les \n en <br> si nécessaire (Mistral peut utiliser l'un ou l'autre)
        response_html = response_text.replace('\n', '<br>')
        
        # Sauvegarder la conversation
        if memory_store:
            try:
                memory_store.add_exchange(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_response=response_text,
                    sources=sources_info
                )
            except Exception as e:
                Logger.error(f"Erreur lors de la sauvegarde de la conversation: {e}")
        
        return jsonify({
            "response": response_html,
            "response_text": response_text,  # Version texte pour compatibilité
            "sources": sources_info,
            "session_id": session_id,
            "timestamp": now_utc_iso(),
            "documents_found": len(response.sources),
            "llm_used": True,
            "llm_provider": llm_provider,  # Ajout du provider utilisé
            "confidence": response.confidence
        })
        
    except Exception as e:
        Logger.error(f"Erreur dans /api/chat: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({
            "error": "Erreur serveur",
            "message": f"Une erreur s'est produite: {str(e)}"
        }), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """Endpoint pour recherche pure de documents (sans génération de réponse)"""
    global rag_pipeline
    
    if not rag_pipeline:
        return jsonify({
            "error": "Système non initialisé"
        }), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        k = data.get('k', 5)
        
        if not query:
            return jsonify({
                "error": "Requête manquante"
            }), 400
        
        # Rechercher des documents avec le nouveau pipeline
        response = rag_pipeline.search(
            query=query,
            limit=k,
            use_reranking=False  # Pour une recherche pure, sans LLM
        )
        
        if not response.success:
            return jsonify({
                "error": response.error_message
            }), 500
        
        # Convertir en format compatible
        results = []
        # Utiliser response.sources au lieu de response.citations
        for source in response.sources:
            if isinstance(source, dict):
                results.append({
                    "document": source.get("doc_id", "Document inconnu"),  # Changé de "source" à "document"
                    "page": source.get("page", "N/A"),
                    "content": source.get("content", f"Résultat de {source.get('doc_id')}")
                })
        
        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        Logger.error(f"❌ Erreur dans /api/search: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/ingest', methods=['GET', 'POST'])
def api_ingest():
    """API pour l'ingestion incrémentale de documents"""
    global rag_pipeline
    
    if not rag_pipeline:
        return jsonify({
            "success": False,
            "error": "Système non initialisé"
        }), 500
    
    import time
    start_time = time.time()
    
    try:
        if request.method == 'GET':
            # Pour GET, utiliser les paramètres par défaut
            data_dir = None
            rebuild = False
        else:
            # Gérer à la fois JSON et form data pour POST
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()
            
            data_dir = data.get('data_dir')
            rebuild = data.get('rebuild', False)
            
            # Convertir rebuild en booléen si c'est une chaîne
            if isinstance(rebuild, str):
                rebuild = rebuild.lower() in ('true', '1', 'yes', 'on')
        
        Logger.info(f"🔄 Début de l'ingestion incrémentale (rebuild={rebuild})")
        
        # Utiliser le nouveau pipeline pour ingérer les documents
        from pathlib import Path
        from config import Config
        
        # Répertoire par défaut s'il n'est pas spécifié
        if not data_dir:
            data_dir = Config.DATA_DIR  # Utiliser le chemin de configuration
        
        data_path = Path(data_dir)
        if not data_path.exists():
            return jsonify({
                "success": False,
                "error": f"Répertoire {data_dir} non trouvé"
            }), 400
        
        # Si rebuild, vider la collection
        if rebuild:
            rag_pipeline.clear_collection()
            Logger.info("🧹 Collection vidée pour rebuild")
        
        # Traiter tous les fichiers PDF
        processed = 0
        skipped = 0
        total_chunks = 0
        errors = []
        
        for pdf_file in data_path.glob("*.pdf"):
            doc_id = pdf_file.stem
            
            try:
                # Vérifier si le document existe déjà (si pas de rebuild)
                if not rebuild:
                    existing_docs = rag_pipeline.list_documents()
                    if any(doc.doc_id == doc_id for doc in existing_docs):
                        skipped += 1
                        Logger.info(f"⏭️  Document {doc_id} déjà ingéré")
                        continue
                
                # Ingérer le document
                stats = rag_pipeline.ingest_document(pdf_file, doc_id)
                
                if stats.success:
                    processed += 1
                    total_chunks += stats.chunks_created
                    Logger.success(f"✅ {doc_id}: {stats.chunks_created} chunks")
                else:
                    errors.append(f"{doc_id}: {stats.error}")
                    Logger.error(f"❌ Erreur {doc_id}: {stats.error}")
                    
            except Exception as e:
                errors.append(f"{doc_id}: {str(e)}")
                Logger.error(f"❌ Exception {doc_id}: {e}")
        
        result = {
            "processed": processed,
            "skipped": skipped,
            "total_chunks_added": total_chunks,
            "errors": errors
        }
        
        # Calculer le temps de traitement
        processing_time = time.time() - start_time
        
        if errors and processed == 0:
            return jsonify({
                "success": False,
                "error": f"Aucun document traité. Erreurs: {'; '.join(errors)}",
                "processing_time": f"{processing_time:.2f}s"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Ingestion incrémentale terminée",
            "processed_documents": result.get("processed", 0),
            "total_chunks": result.get("total_chunks_added", 0),
            "processing_time": f"{processing_time:.2f}s",
            "stats": {
                "files_processed": result.get("processed", 0),
                "files_skipped": result.get("skipped", 0),
                "files_errors": len(result.get("errors", [])),
                "total_chunks_added": result.get("total_chunks_added", 0),
                "errors": result.get("errors", [])
            }
        })
        
    except Exception as e:
        processing_time = time.time() - start_time
        Logger.error(f"Erreur API ingestion: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "processing_time": f"{processing_time:.2f}s"
        }), 500

@app.route('/api/ingest/status', methods=['GET'])
def api_ingest_status():
    """Vérifier le statut de l'index vectoriel Qdrant"""
    global rag_pipeline
    
    if not rag_pipeline:
        return jsonify({
            "success": False,
            "message": "Système non initialisé"
        }), 500
    
    try:
        # Obtenir les informations du nouveau pipeline
        collection_info = rag_pipeline.get_collection_info()
        documents = rag_pipeline.list_documents()
        
        # Compter les fichiers dans data/
        from config import Config
        data_files = []
        document_names = []
        if os.path.exists(Config.DATA_DIR):
            for root, dirs, files in os.walk(Config.DATA_DIR):
                for file in files:
                    if file.lower().endswith(('.pdf', '.txt', '.docx', '.csv')):
                        data_files.append(file)
                        # Extraire le nom du document sans extension pour affichage
                        doc_name = os.path.splitext(file)[0].replace('-', ' ').replace('_', ' ').title()
                        doc_id = os.path.splitext(file)[0]
                        
                        # Vérifier si ce document est indexé
                        indexed_doc = next((d for d in documents if d.doc_id == doc_id), None)
                        has_embeddings = indexed_doc is not None
                        
                        document_names.append({
                            "filename": file,
                            "display_name": doc_name,
                            "document_id": doc_id,
                            "has_embeddings": has_embeddings,
                            "embedding_models": ["BGE-M3"] if has_embeddings else [],
                            "chunks_count": indexed_doc.chunks_count if indexed_doc else 0,
                            "pages_count": indexed_doc.pages_count if indexed_doc else 0
                        })
        
        # Préparer les informations sur les documents indexés uniquement
        documents_with_embeddings = []
        for doc in documents:
            documents_with_embeddings.append({
                "document_id": doc.doc_id,
                "filename": f"{doc.doc_id}.pdf",
                "chunks_count": doc.chunks_count,
                "pages_count": doc.pages_count,
                "pages_range": doc.pages_range,
                "created_at": doc.created_at,
                "embedding_models": ["BGE-M3"],
                "has_embeddings": True
            })
        
        return jsonify({
            "success": True,
            "index_exists": True,
            "vectorstore_type": "Qdrant",
            "collections": {
                "documents": {
                    "points_count": collection_info.get("points_count", 0),
                    "status": collection_info.get("status", "unknown")
                }
            },
            "data_files_count": len(data_files),
            "data_files": data_files,
            "document_names": document_names,
            "all_document_names": [doc["display_name"] for doc in document_names],
            "processed_documents": len(documents),
            "embedding_models": {
                "BGE-M3": True  # BGE-M3 est toujours disponible si le pipeline est initialisé
            },
            "documents_with_embeddings": {
                "documents": documents_with_embeddings,
                "total_documents": len(documents)
            },
            "system_info": {
                "qdrant_available": True,  # Disponible si le pipeline est initialisé
                "mistral_available": rag_pipeline.mistral_manager.available if hasattr(rag_pipeline, 'mistral_manager') else False,
                "reranker_available": rag_pipeline.reranker_manager.available if hasattr(rag_pipeline, 'reranker_manager') else False,
                "embedding_available": True  # BGE-M3 toujours disponible
            }
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la vérification: {str(e)}"
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Endpoint simple pour vérifier le statut des documents"""
    try:
        import os
        from config import Config
        
        # Vérifier l'existence de l'index vectoriel
        vectorstore_path = os.path.join(Config.VECTORSTORE_DIR, "faiss_index")
        vectorstore_exists = os.path.exists(vectorstore_path)
        
        # Compter les documents dans le répertoire data/
        indexed_documents = 0
        if vectorstore_exists:
            # Si l'index existe, compter les fichiers traités
            for root, dirs, files in os.walk(Config.DATA_DIR):
                for file in files:
                    if file.lower().endswith(('.pdf', '.txt', '.docx', '.csv')):
                        indexed_documents += 1
        
        return jsonify({
            "success": True,
            "indexed_documents": indexed_documents,
            "vectorstore_exists": vectorstore_exists,
            "data_directory": Config.DATA_DIR
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la vérification: {str(e)}"
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Récupérer toutes les sessions"""
    global memory_store
    
    if not memory_store:
        return jsonify({
            "success": False,
            "error": "Système de mémoire non initialisé"
        }), 500
    
    try:
        sessions = memory_store.get_all_sessions()
        
        # Formater les sessions pour le front-end
        formatted_sessions = []
        for session in sessions:
            # Calculer le nombre de messages
            history = memory_store.get_conversation_history(session['session_id'])
            message_count = len(history)
            
            formatted_sessions.append({
                "session_id": session['session_id'],
                "title": session.get('title', 'Conversation sans titre'),
                "created_at": session.get('created_at', ''),
                "last_activity": session.get('last_activity', ''),
                "message_count": message_count
            })
        
        return jsonify({
            "success": True,
            "sessions": formatted_sessions
        })
        
    except Exception as e:
        Logger.error(f"Erreur lors de la récupération des sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Créer une nouvelle session"""
    global memory_store
    
    if not memory_store:
        return jsonify({
            "success": False,
            "error": "Système de mémoire non initialisé"
        }), 500
    
    try:
        data = request.get_json()
        session_id = data.get('session_id', f"session_{uuid.uuid4().hex[:8]}")
        title = data.get('title', 'Nouvelle conversation')
        
        # Créer la session dans la base de données
        memory_store.create_session(session_id, title)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "title": title,
            "message": "Session créée avec succès"
        })
        
    except Exception as e:
        Logger.error(f"Erreur dans /api/sessions POST: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Récupérer l'historique d'une session"""
    global memory_store
    
    if not memory_store:
        return jsonify({
            "success": False,
            "error": "Système de mémoire non initialisé"
        }), 500
    
    try:
        history = memory_store.get_conversation_history(session_id)
        
        # Formater l'historique pour le front-end
        formatted_history = []
        for exchange in history:
            formatted_history.append({
                "user_message": exchange.get('user_message', ''),
                "assistant_response": exchange.get('assistant_response', ''),
                "timestamp": exchange.get('timestamp', ''),
                "sources": exchange.get('sources', [])
            })
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": formatted_history
        })
        
    except Exception as e:
        Logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Supprimer une session"""
    global memory_store
    
    if not memory_store:
        return jsonify({
            "success": False,
            "error": "Système de mémoire non initialisé"
        }), 500
    
    try:
        memory_store.delete_session(session_id)
        
        return jsonify({
            "success": True,
            "message": "Session supprimée avec succès"
        })
        
    except Exception as e:
        Logger.error(f"Erreur lors de la suppression de la session: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Informations système"""
    global orchestrator
    
    if not orchestrator:
        return jsonify({
            "status": "not_initialized",
            "message": "Système non initialisé"
        })
    
    try:
        info = orchestrator.get_system_info()
        info["status"]["app_ready"] = True
        info["status"]["timestamp"] = now_utc_iso()
        
        return jsonify({
            "success": True,
            "info": info
        })
        
    except Exception as e:
        Logger.error(f"Erreur dans /api/system/info: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check de santé de l'API"""
    global orchestrator
    
    status = {
        "api": "online",
        "orchestrator": "ready" if orchestrator else "not_ready",
        "timestamp": now_utc_iso()
    }
    
    if orchestrator:
        status["rag_pipeline"] = "ready" if orchestrator.pipeline else "not_ready"
        status["memory_store"] = "ready" if orchestrator.memory_store else "not_ready"
    
    return jsonify(status)

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return jsonify({"error": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    return jsonify({"error": "Erreur serveur interne"}), 500

def create_app():
    """Factory pour créer l'application Flask"""
    return app

def main():
    """Point d'entrée principal"""
    Logger.info("🌐 Démarrage du serveur Flask...")
    
    # Initialiser l'application
    if not initialize_app():
        Logger.error("❌ Impossible de démarrer l'application")
        return
    
    # Configuration
    config = Config()
    
    print(f"🌐 Serveur disponible sur: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print("📝 Interface de chat disponible à la racine: /")
    print("🔗 API disponible sur: /api/")
    print("\nEndpoints API:")
    print("  POST /api/chat - Envoyer un message")
    print("  POST /api/search - Rechercher dans les documents")
    print("  GET  /api/sessions - Lister les sessions")
    print("  GET  /api/sessions/<id>/history - Historique session")
    print("  DELETE /api/sessions/<id> - Supprimer session")
    print("  GET  /api/system/info - Informations système")
    print("  GET  /api/health - Status de l'API")
    print("  POST /api/ingest - Ingérer les documents")
    print("  GET  /api/ingest/status - Status de l'ingestion")
    
    # Démarrer le serveur
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()
