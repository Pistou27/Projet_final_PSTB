"""
Gestionnaire pour les embeddings BGE-M3
"""

from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from .config import RAGConfig
from .utils import Logger

class EmbeddingManager:
    """Gestionnaire pour les embeddings BGE-M3"""
    
    def __init__(self, model_name: str = None):
        """
        Initialise le gestionnaire d'embeddings
        
        Args:
            model_name: Nom du modèle BGE à utiliser (défaut: config)
        """
        self.model_name = model_name or RAGConfig.EMBEDDING_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle BGE-M3"""
        if SentenceTransformer is None:
            Logger.error("sentence_transformers non installé. Installer avec: pip install sentence-transformers")
            raise ImportError("sentence_transformers manquant")
        
        try:
            Logger.loading(f"Chargement modèle embedding: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            Logger.success(f"✅ Modèle BGE-M3 chargé")
        except Exception as e:
            Logger.error(f"Erreur chargement modèle embedding: {e}")
            raise
    
    def encode_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """Encode une liste de textes en embeddings"""
        if not self.model:
            raise RuntimeError("Modèle embedding non chargé")
        
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=show_progress
            )
            return embeddings.tolist()
        except Exception as e:
            Logger.error(f"Erreur encoding embeddings: {e}")
            raise
    
    def encode_single(self, text: str) -> List[float]:
        """Encode un seul texte en embedding"""
        return self.encode_texts([text], show_progress=False)[0]
    
    def is_available(self) -> bool:
        """Vérifie si le modèle est disponible"""
        return self.model is not None
