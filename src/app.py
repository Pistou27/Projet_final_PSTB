"""
Application Flask - Interface web et API pour le système RAG
"""
import os
import uuid
from flask import Flask, render_template, request, jsonify, session

# Local imports
from config import Config
from orchestrator import Orchestrator
from utils import Logger, now_utc_iso, now_formatted

# Initialisation Flask avec les bons chemins
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.urandom(24)

# Instance globale de l'orchestrateur
orchestrator = None

def initialize_app():
    """Initialiser l'application et l'orchestrateur"""
    global orchestrator
    
    Logger.rocket("Initialisation de l'application Flask...")
    
    try:
        orchestrator = Orchestrator()
        success = orchestrator.initialize()
        
        if success:
            Logger.success("Application initialisée avec succès")
            return True
        else:
            Logger.error("Échec de l'initialisation")
            return False
            
    except Exception as e:
        Logger.error(f"Erreur lors de l'initialisation: {e}")
        return False

@app.route('/')
def index():
    """Page d'accueil avec interface de chat"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint API pour les requêtes de chat"""
    global orchestrator
    
    if not orchestrator:
        return jsonify({
            "error": "Système non initialisé",
            "message": "Le système RAG n'est pas encore prêt. Veuillez réessayer."
        }), 500
    
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
        
        if not session_id:
            # Créer une nouvelle session
            session_id = str(uuid.uuid4())
            orchestrator.memory_store.create_session(
                session_id, 
                f"Chat {now_formatted('%Y-%m-%d %H:%M')}"
            )
        
        # Traiter la requête
        result = orchestrator.process_query(user_message, session_id)
        
        return jsonify({
            "response": result['response'],
            "sources": result['sources'],
            "session_id": result['session_id'],
            "timestamp": now_utc_iso()
        })
        
    except Exception as e:
        Logger.error(f"Erreur dans /api/chat: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({
            "error": "Erreur serveur",
            "message": f"Une erreur s'est produite: {str(e)}"
        }), 500

@app.route('/api/ingest', methods=['POST'])
def api_ingest():
    """Lancer l'ingestion des documents"""
    try:
        import sys
        import os
        import importlib
        
        # S'assurer que le dossier src est dans le path
        src_path = os.path.dirname(__file__)
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Importer et recharger le module
        import ingest
        importlib.reload(ingest)
        from ingest import DocumentIngester
        
        # Créer une instance d'ingester
        ingester = DocumentIngester()
        
        # Vérifier que la méthode existe
        if not hasattr(ingester, 'run_ingestion'):
            return jsonify({"success": False, "error": "Méthode run_ingestion non trouvée"}), 500
        
        # Lancer l'ingestion
        Logger.books("Début de l'ingestion via API...")
        success, files_processed = ingester.run_ingestion()
        
        if success:
            # Recharger l'index vectoriel dans l'orchestrateur
            global orchestrator
            if orchestrator and orchestrator.rag_pipeline:
                orchestrator.rag_pipeline._load_vectorstore()
            
            return jsonify({
                "success": True,
                "message": "Ingestion terminée avec succès. L'index vectoriel a été mis à jour.",
                "files_processed": files_processed
            })
        else:
            return jsonify({
                "success": False,
                "message": "Erreur lors de l'ingestion des documents."
            }), 500
            
    except Exception as e:
        print(f"Erreur lors de l'ingestion: {e}")
        return jsonify({
            "success": False,
            "message": f"Erreur lors de l'ingestion: {str(e)}"
        }), 500

@app.route('/api/ingest/status', methods=['GET'])
def api_ingest_status():
    """Vérifier le statut de l'index vectoriel"""
    try:
        import os
        from config import Config
        
        vectorstore_path = os.path.join(Config.VECTORSTORE_DIR, "faiss_index")
        index_exists = os.path.exists(vectorstore_path)
        
        if index_exists:
            # Compter les fichiers dans data/
            data_files = []
            for root, dirs, files in os.walk(Config.DATA_DIR):
                for file in files:
                    if file.lower().endswith(('.pdf', '.txt', '.docx', '.csv')):
                        data_files.append(file)
            
            return jsonify({
                "success": True,
                "index_exists": True,
                "data_files_count": len(data_files),
                "data_files": data_files
            })
        else:
            return jsonify({
                "success": True,
                "index_exists": False,
                "message": "Aucun index vectoriel trouvé. Lancez l'ingestion."
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
    global orchestrator
    
    if not orchestrator:
        return jsonify({"error": "Système non initialisé"}), 500
    
    try:
        sessions = orchestrator.get_all_sessions()
        return jsonify({
            "success": True,
            "sessions": sessions
        })
        
    except Exception as e:
        print(f"Erreur dans /api/sessions: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Créer une nouvelle session"""
    global orchestrator
    
    if not orchestrator:
        return jsonify({"error": "Système non initialisé"}), 500
    
    try:
        data = request.get_json()
        session_id = data.get('session_id', f"session_{uuid.uuid4().hex[:8]}")
        title = data.get('title', 'Nouvelle conversation')
        
        orchestrator.memory_store.create_session(session_id, title)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "title": title,
            "message": "Session créée avec succès"
        })
        
    except Exception as e:
        print(f"Erreur dans /api/sessions POST: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Récupérer l'historique d'une session"""
    global orchestrator
    
    if not orchestrator:
        return jsonify({"error": "Système non initialisé"}), 500
    
    try:
        limit = request.args.get('limit', 20, type=int)
        history = orchestrator.get_session_history(session_id, limit)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
        
    except Exception as e:
        print(f"Erreur dans /api/sessions/{session_id}/history: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Supprimer une session"""
    global orchestrator
    
    if not orchestrator:
        return jsonify({"error": "Système non initialisé"}), 500
    
    try:
        orchestrator.memory_store.delete_session(session_id)
        
        return jsonify({
            "success": True,
            "message": "Session supprimée"
        })
        
    except Exception as e:
        print(f"Erreur dans DELETE /api/sessions/{session_id}: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

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
        status["rag_pipeline"] = "ready" if orchestrator.rag_pipeline else "not_ready"
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
    Logger.globe("Démarrage du serveur Flask...")
    
    # Initialiser l'application
    if not initialize_app():
        Logger.error("Impossible de démarrer l'application")
        return
    
    # Configuration
    config = Config()
    
    print(f"🌐 Serveur disponible sur: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print("📝 Interface de chat disponible à la racine: /")
    print("🔗 API disponible sur: /api/")
    print("\nEndpoints API:")
    print("  POST /api/chat - Envoyer un message")
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
