"""
Orchestrateur principal - Point d'entrée pour les tests et la coordination
"""
import os
import sys
import uuid
from typing import Dict, Any

# Local imports
from config import Config
from rag_pipeline import RAGPipeline
from memory_store import MemoryStore
from utils import Logger

class Orchestrator:
    """Orchestrateur principal du système RAG avec mémoire"""
    
    def __init__(self):
        self.config = Config
        self.rag_pipeline = None
        self.memory_store = None
        self.current_session_id = None
    
    def initialize(self):
        """Initialiser tous les composants"""
        Logger.info("=== Initialisation de l'Orchestrateur ===")
        
        try:
            # Vérifier la configuration
            self.config.ensure_directories()
            self.config.print_config()
            
            # Initialiser la mémoire
            Logger.books("Initialisation de la mémoire...")
            self.memory_store = MemoryStore()
            
            # Initialiser le pipeline RAG
            Logger.robot("Initialisation du pipeline RAG...")
            self.rag_pipeline = RAGPipeline()
            self.rag_pipeline.initialize()
            
            Logger.success("Orchestrateur initialisé avec succès")
            return True
            
        except Exception as e:
            Logger.error(f"Erreur lors de l'initialisation: {e}")
            return False
    
    def create_new_session(self, title: str = None) -> str:
        """Créer une nouvelle session de conversation"""
        session_id = str(uuid.uuid4())
        title = title or f"Conversation {session_id[:8]}"
        
        self.memory_store.create_session(session_id, title)
        self.current_session_id = session_id
        
        Logger.info(f"Nouvelle session créée: {session_id}")
        return session_id
    
    def set_session(self, session_id: str):
        """Définir la session active"""
        session_info = self.memory_store.get_session_info(session_id)
        if session_info:
            self.current_session_id = session_id
            Logger.info(f"Session active: {session_id}")
        else:
            Logger.error(f"Session non trouvée: {session_id}")
    
    def process_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Traiter une requête avec mémoire conversationnelle"""
        if not self.rag_pipeline or not self.memory_store:
            raise RuntimeError("Orchestrateur non initialisé")
        
        # Utiliser la session fournie ou la session courante
        working_session_id = session_id or self.current_session_id
        
        if not working_session_id:
            working_session_id = self.create_new_session()
        
        # Récupérer le contexte de conversation
        chat_history = self.memory_store.get_recent_context(working_session_id, 3)
        
        # Générer la réponse
        response, sources = self.rag_pipeline.generate_response(query, chat_history)
        
        # Sauvegarder l'échange
        self.memory_store.add_exchange(
            session_id=working_session_id,
            user_message=query,
            assistant_response=response,
            sources=sources
        )
        
        return {
            "session_id": working_session_id,
            "query": query,
            "response": response,
            "sources": sources,
            "chat_history": chat_history
        }
    
    def get_session_history(self, session_id: str, limit: int = 10) -> list:
        """Récupérer l'historique d'une session"""
        if not self.memory_store:
            return []
        
        return self.memory_store.get_conversation_history(session_id, limit)
    
    def get_all_sessions(self) -> list:
        """Récupérer toutes les sessions"""
        if not self.memory_store:
            return []
        
        return self.memory_store.get_all_sessions()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtenir des informations sur le système"""
        info = {
            "config": {
                "model_path": self.config.MODEL_PATH,
                "data_dir": self.config.DATA_DIR,
                "vectorstore_dir": self.config.VECTORSTORE_DIR,
                "embedding_model": self.config.EMBEDDING_MODEL
            },
            "status": {
                "rag_pipeline_ready": self.rag_pipeline is not None,
                "memory_store_ready": self.memory_store is not None,
                "current_session": self.current_session_id
            }
        }
        
        # Ajouter les infos du vectorstore si disponible
        if self.rag_pipeline:
            vectorstore_info = self.rag_pipeline.get_vectorstore_info()
            info["vectorstore"] = vectorstore_info
        
        return info

def interactive_demo():
    """Démo interactive en ligne de commande"""
    orchestrator = Orchestrator()
    
    if not orchestrator.initialize():
        Logger.error("Impossible d'initialiser l'orchestrateur")
        return
    
    print("\n🎯 Démo interactive du système RAG")
    print("Tapez 'quit' pour quitter, 'info' pour les infos système")
    print("=" * 50)
    
    # Créer une session
    session_id = orchestrator.create_new_session("Session de démonstration")
    
    while True:
        try:
            query = input("\n💬 Votre question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Au revoir!")
                break
            
            if query.lower() == 'info':
                info = orchestrator.get_system_info()
                print(f"\n📊 Informations système:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
                continue
            
            if not query:
                continue
            
            Logger.robot("Traitement en cours...")
            
            # Traiter la requête
            result = orchestrator.process_query(query, session_id)
            
            print(f"\n📝 Réponse:")
            print(result["response"])
            
            if result["sources"]:
                Logger.books(f"Sources: {', '.join(result['sources'])}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            Logger.error(f"Erreur: {e}")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            interactive_demo()
        elif sys.argv[1] == "test":
            # Test rapide
            orchestrator = Orchestrator()
            if orchestrator.initialize():
                result = orchestrator.process_query("Quelles sont les règles principales ?")
                print(f"Test réussi: {result['response']}")
        else:
            print("Usage: python orchestrator.py [demo|test]")
    else:
        interactive_demo()

if __name__ == "__main__":
    main()
