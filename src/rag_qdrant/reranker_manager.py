"""
Gestionnaire pour le reranking BGE (optionnel)
"""

from typing import List

try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    FlagReranker = None
    RERANKER_AVAILABLE = False

from .config import RAGConfig
from .utils import Logger

class RerankerManager:
    """Gestionnaire pour le reranking BGE"""
    
    def __init__(self, model_name: str = None):
        """
        Initialise le gestionnaire de reranking
        
        Args:
            model_name: Nom du modèle reranker à utiliser (défaut: config)
        """
        self.model_name = model_name or RAGConfig.RERANKER_MODEL
        self.reranker = None
        self.available = RERANKER_AVAILABLE
        
        if self.available:
            self._load_model()
        else:
            Logger.warning("⚠️ FlagEmbedding non disponible - reranking désactivé")
    
    def _load_model(self):
        """Charge le modèle de reranking"""
        if not self.available:
            return
            
        try:
            Logger.loading(f"Chargement reranker: {self.model_name}")
            self.reranker = FlagReranker(self.model_name, use_fp16=True)
            Logger.success(f"✅ Reranker BGE chargé")
        except Exception as e:
            Logger.error(f"Erreur chargement reranker: {e}")
            self.available = False
    
    def rerank(self, query: str, passages: List[str]) -> List[float]:
        """Rerank les passages par rapport à la query"""
        if not self.available or not self.reranker:
            Logger.warning("Reranker non disponible - utilisation scores par défaut")
            # Retourner des scores décroissants artificiels
            return [1.0 - (i * 0.01) for i in range(len(passages))]
        
        try:
            # Préparer les paires query-passage
            pairs = [[query, passage] for passage in passages]
            scores = self.reranker.compute_score(pairs, normalize=True)
            
            # S'assurer que c'est une liste
            if not isinstance(scores, list):
                scores = [scores]
            
            return scores
        except Exception as e:
            Logger.error(f"Erreur reranking: {e}")
            return [1.0 - (i * 0.01) for i in range(len(passages))]
    
    def is_available(self) -> bool:
        """Vérifie si le reranker est disponible"""
        return self.available and self.reranker is not None
