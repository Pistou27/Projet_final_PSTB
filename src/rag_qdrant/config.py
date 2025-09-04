"""
Configuration centralisée pour le pipeline RAG Qdrant
"""

import os
from pathlib import Path

class RAGConfig:
    """Configuration du système RAG"""
    
    # Modèles
    EMBEDDING_MODEL = "BAAI/bge-m3"
    RERANKER_MODEL = "BAAI/bge-reranker-base"
    MISTRAL_MODEL = "mistral:latest"
    
    # Chunking
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    
    # Recherche
    DEFAULT_TOP_K = 20
    DEFAULT_RERANK_TOP_K = 10
    
    # Qdrant
    VECTOR_SIZE = 1024  # BGE-M3 embedding size
    COLLECTION_NAME = "documents"
    QDRANT_PATH = "vectorstore/qdrant_local"  # Chemin depuis la racine du projet
    
    # Mistral/Ollama
    OLLAMA_HOST = "http://localhost:11434"
    GENERATION_TEMPERATURE = 0.2
    GENERATION_MAX_TOKENS = 2000
    
    # Répertoires
    DATA_DIR = "data"
    
    @classmethod
    def get_qdrant_path(cls) -> str:
        """Retourne le chemin Qdrant avec création du répertoire"""
        # Obtenir le chemin absolu depuis la racine du projet
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent  # Remonte de src/rag_qdrant vers la racine
        qdrant_path = project_root / "vectorstore" / "qdrant_local"
        qdrant_path.mkdir(parents=True, exist_ok=True)
        return str(qdrant_path)
