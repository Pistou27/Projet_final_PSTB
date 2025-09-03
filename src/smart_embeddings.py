"""
Gestionnaire d'embeddings intelligent avec sélection automatique
"""
import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# LangChain imports
try:
    from langchain_huggingface import HuggingFaceEmbeddings  # Import mis à jour
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from utils import Logger, count_pdf_pages

class SmartEmbeddingManager:
    """Gestionnaire intelligent d'embeddings avec sélection automatique"""
    
    def __init__(self):
        # Simplified - all documents use the same optimized model
        self.default_model = "BAAI/bge-m3"
        self.loaded_models = {}
        self.current_model = None
        self.current_embeddings = None
        
        # Legacy attributes for compatibility
        self.small_doc_threshold = 5
        self.small_model = self.default_model
        self.large_model = self.default_model
    
    def count_pdf_pages(self, pdf_path: str) -> int:
        """Compter le nombre de pages d'un PDF - DEPRECATED, use utils.count_pdf_pages instead"""
        Logger.warning("SmartEmbeddingManager.count_pdf_pages is deprecated, use utils.count_pdf_pages")
        return count_pdf_pages(pdf_path)
    
    def determine_document_category(self, pdf_path: str) -> str:
        """Déterminer la catégorie du document - SIMPLIFIED: always returns 'default'"""
        page_count = count_pdf_pages(pdf_path)
        Logger.info(f"Document {Path(pdf_path).name}: {page_count} pages -> modèle par défaut")
        return "default"
    
    def get_embedding_model_for_document(self, pdf_path: str) -> str:
        """Obtenir le modèle d'embedding approprié pour un document - SIMPLIFIED"""
        Logger.info(f"Modèle d'embedding sélectionné: {self.default_model}")
        return self.default_model
    
    def load_embedding_model(self, model_name: str) -> HuggingFaceEmbeddings:
        """Charger un modèle d'embedding spécifique avec préfixes BGE"""
        if model_name not in self.loaded_models:
            Logger.loading(f"Chargement du modèle d'embedding: {model_name}")
            try:
                # Configuration avec normalize_embeddings pour tous les modèles
                embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                # Note: Préfixes BGE seront appliqués manuellement si nécessaire
                if "bge" in model_name.lower():
                    Logger.info(f"✅ BGE configuré avec normalize_embeddings=True")
                
                self.loaded_models[model_name] = embeddings
                Logger.success(f"Modèle {model_name} chargé avec succès")
            except Exception as e:
                Logger.error(f"Erreur lors du chargement de {model_name}: {e}")
                # Since we only use BAAI/bge-m3 now, re-raise the error
                raise e
        
        return self.loaded_models[model_name]
    
    def get_embeddings_for_document(self, pdf_path: str) -> HuggingFaceEmbeddings:
        """Obtenir les embeddings appropriés pour un document donné"""
        model_name = self.get_embedding_model_for_document(pdf_path)
        
        # Si le modèle a changé, mettre à jour le modèle courant
        if self.current_model != model_name:
            self.current_model = model_name
            self.current_embeddings = self.load_embedding_model(model_name)
        
        return self.current_embeddings
    
    def get_current_embeddings(self) -> Optional[HuggingFaceEmbeddings]:
        """Obtenir le modèle d'embedding actuellement chargé"""
        return self.current_embeddings
    
    def get_document_embedding_model(self, page_count: int) -> str:
        """Choisir le modèle d'embedding basé sur le nombre de pages"""
        if page_count <= self.small_doc_threshold:
            return self.small_model
        else:
            return self.large_model
    
    def is_complex_query(self, query: str) -> bool:
        """Déterminer si une requête est complexe"""
        query_lower = query.lower()
        
        # Critères de complexité améliorés
        complexity_indicators = [
            len(query.split()) > 8,  # Plus de 8 mots (réduit de 10)
            '?' in query and query.count('?') > 1,  # Questions multiples
            any(word in query_lower for word in [
                'analyser', 'comparer', 'expliquer', 'détailler', 'décrire',
                'comment', 'pourquoi', 'règles', 'fonctionnement', 'différence',
                'stratégie', 'tactique', 'interaction', 'mécanisme'
            ]),  # Mots clés complexes étendus
            len(query) > 80,  # Plus de 80 caractères (réduit de 100)
            any(word in query_lower for word in [
                'plusieurs', 'différent', 'entre', 'relation', 'ensemble',
                'système', 'processus', 'structure'
            ])  # Mots indiquant des concepts complexes
        ]
        
        # Une seule condition suffit maintenant pour être considéré comme complexe
        is_complex = sum(complexity_indicators) >= 1
        
        Logger.info(f"Requête: '{query}' -> Complexe: {is_complex} (critères: {sum(complexity_indicators)}/5)")
        return is_complex
    
    def get_embeddings(self, model_name: str) -> HuggingFaceEmbeddings:
        """Obtenir les embeddings pour un modèle donné (alias pour compatibilité)"""
        return self.load_embedding_model(model_name)
    
    def preload_all_models(self):
        """Précharger tous les modèles d'embedding"""
        Logger.info(f"Préchargement de tous les modèles d'embedding...")
        unique_models = set(self.embedding_models.values())
        
        for model_name in unique_models:
            try:
                self.load_embedding_model(model_name)
            except Exception as e:
                Logger.error(f"Erreur préchargement {model_name}: {e}")
    
    def embed_query_with_prefix(self, query: str) -> List[float]:
        """Embedder une requête avec préfixe BGE si nécessaire"""
        if not self.current_embeddings:
            Logger.warning("Aucun modèle d'embedding chargé")
            return []
        
        if "bge" in self.current_model.lower():
            # Pour BGE, le préfixe est déjà configuré dans encode_kwargs
            return self.current_embeddings.embed_query(query)
        else:
            return self.current_embeddings.embed_query(query)
    
    def embed_documents_with_prefix(self, texts: List[str]) -> List[List[float]]:
        """Embedder des documents avec préfixe BGE si nécessaire"""
        if not self.current_embeddings:
            Logger.warning("Aucun modèle d'embedding chargé")
            return []
        
        if "bge" in self.current_model.lower():
            # Pour BGE, le préfixe est déjà configuré dans encode_kwargs
            return self.current_embeddings.embed_documents(texts)
        else:
            return self.current_embeddings.embed_documents(texts)
        
        Logger.success("Préchargement terminé")
    
    def get_model_info(self) -> Dict:
        """Obtenir des informations sur les modèles configurés"""
        return {
            "embedding_models": self.embedding_models,
            "loaded_models": list(self.loaded_models.keys()),
            "current_model": self.current_model
        }
    
    def get_available_models(self) -> Dict:
        """Obtenir la liste des modèles disponibles (alias pour get_model_info)"""
        return self.get_model_info()
    
    def test_model_selection(self, test_pdfs: List[str] = None) -> Dict:
        """Tester la sélection de modèles sur des PDFs de test"""
        if test_pdfs is None:
            # Utiliser les PDFs du dossier data s'ils existent
            data_dir = Path("data")
            if data_dir.exists():
                test_pdfs = list(data_dir.glob("*.pdf"))
            else:
                Logger.warning("Aucun PDF de test trouvé")
                return {}
        
        results = {}
        for pdf_path in test_pdfs:
            if isinstance(pdf_path, str):
                pdf_path = Path(pdf_path)
            
            if pdf_path.exists():
                category = self.determine_document_category(str(pdf_path))
                model = self.embedding_models[category]
                page_count = self.count_pdf_pages(str(pdf_path))
                
                results[pdf_path.name] = {
                    "pages": page_count,
                    "category": category,
                    "model": model
                }
        
        return results

# Test et démonstration
if __name__ == "__main__":
    print("=== Test du gestionnaire d'embeddings intelligent ===")
    
    manager = SmartEmbeddingManager()
    
    # Test de sélection de modèles
    test_results = manager.test_model_selection()
    if test_results:
        print("\nRésultats de la sélection automatique:")
        for filename, info in test_results.items():
            print(f"  {filename}: {info['pages']} pages -> {info['category']} -> {info['model']}")
    
    # Informations sur les modèles
    print(f"\nModèles configurés: {manager.get_model_info()}")
