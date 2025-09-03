"""
RAG Qdrant - Pipeline RAG modulaire avec Qdrant et Mistral

Un système de recherche intelligente dans vos documents PDF utilisant:
- Qdrant pour la recherche vectorielle
- BGE-M3 pour les embeddings
- BGE-reranker pour le reranking
- Mistral via Ollama pour la génération

Modules principaux:
- pipeline: Pipeline RAG complet
- cli: Interface en ligne de commande
- config: Configuration centralisée
- schemas: Structures de données
"""

from .pipeline import RAGPipeline
from .config import RAGConfig
from .schemas import DocumentChunk, RAGResponse, IngestionStats, DocumentInfo
from .utils import Logger

__version__ = "1.0.0"
__author__ = "Votre Nom"
__email__ = "votre.email@exemple.com"

# Exports principaux
__all__ = [
    "RAGPipeline",
    "RAGConfig", 
    "DocumentChunk",
    "RAGResponse",
    "IngestionStats",
    "DocumentInfo",
    "Logger"
]

# Configuration par défaut au niveau du package
def setup_default_logging():
    """Configure le logging par défaut pour le package"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Auto-configuration au chargement du module
setup_default_logging()

# Message de bienvenue
Logger.info("🚀 RAG Qdrant package chargé")
