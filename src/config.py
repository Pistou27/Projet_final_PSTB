"""
Configuration du projet - Lecture des variables d'environnement
"""
import os
from dotenv import load_dotenv
from utils import Logger, ensure_directory, ensure_parent_directory, get_project_root

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration centralisée du projet"""
    
    # Chemins
    BASE_DIR = get_project_root()
    DATA_DIR = os.path.join(BASE_DIR, os.getenv("DATA_DIR", "data"))
    VECTORSTORE_DIR = os.path.join(BASE_DIR, os.getenv("VECTORSTORE_DIR", "vectorstore"))
    MEMORY_DB_PATH = os.path.join(BASE_DIR, os.getenv("MEMORY_DB_PATH", "memory/memory.sqlite"))
    MODEL_PATH = os.path.join(BASE_DIR, os.getenv("MODEL_PATH", "models/mistral-7b-instruct.Q4_K_M.gguf"))
    
    # Configuration du modèle LLM
    MODEL_N_CTX = int(os.getenv("MODEL_N_CTX", "4096"))
    MODEL_N_THREADS = int(os.getenv("MODEL_N_THREADS", "4"))
    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
    MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "512"))
    
    # Configuration RAG
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "10"))
    RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Configuration des embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Configuration Ollama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Configuration Flask
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Créer les répertoires nécessaires s'ils n'existent pas"""
        ensure_directory(cls.DATA_DIR)
        ensure_directory(cls.VECTORSTORE_DIR)
        ensure_parent_directory(cls.MEMORY_DB_PATH)
        ensure_parent_directory(cls.MODEL_PATH)
    
    @classmethod
    def validate_model_path(cls):
        """Vérifier que le modèle existe (optionnel pour le mode fallback)"""
        if os.path.exists(cls.MODEL_PATH):
            Logger.success(f"Modèle trouvé: {cls.MODEL_PATH}")
            return True
        else:
            Logger.warning(f"Modèle non trouvé: {cls.MODEL_PATH}")
            Logger.info("Le système fonctionnera en mode LLM simplifié")
            Logger.info("Pour utiliser Mistral-7B, consultez models/README_MODEL_DOWNLOAD.md")
            return False
    
    @classmethod
    def print_config(cls):
        """Afficher la configuration actuelle"""
        print("=== Configuration ===")
        print(f"Répertoire données: {cls.DATA_DIR}")
        print(f"Répertoire vectorstore: {cls.VECTORSTORE_DIR}")
        print(f"Base de données mémoire: {cls.MEMORY_DB_PATH}")
        print(f"Modèle LLM: {cls.MODEL_PATH}")
        print(f"Modèle embeddings: {cls.EMBEDDING_MODEL}")
        print(f"Top-K RAG: {cls.RAG_TOP_K}")
        print(f"Flask: {cls.FLASK_HOST}:{cls.FLASK_PORT}")
        print("===================")
