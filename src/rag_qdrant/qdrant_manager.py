"""
Gestionnaire pour les opérations Qdrant avec filtrage par documents
"""

from typing import List, Dict, Any, Optional, Union

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, Filter, 
        FieldCondition, MatchValue, MatchAny
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    QDRANT_AVAILABLE = False

from .config import RAGConfig
from .schemas import DocumentChunk, DocumentInfo
from .utils import Logger

class QdrantManager:
    """Gestionnaire pour les opérations Qdrant en mode local"""
    
    def __init__(self, collection_name: str = None):
        """
        Initialise le gestionnaire Qdrant en mode local
        
        Args:
            collection_name: Nom de la collection (défaut: config)
        """
        if not QDRANT_AVAILABLE:
            Logger.error("qdrant-client non installé. Installer avec: pip install qdrant-client")
            raise ImportError("qdrant-client manquant")
        
        self.collection_name = collection_name or RAGConfig.COLLECTION_NAME
        self.client = None
        self.vector_size = RAGConfig.VECTOR_SIZE
        self._connect()
    
    def _connect(self):
        """Établit la connexion avec Qdrant en mode local"""
        try:
            qdrant_path = RAGConfig.get_qdrant_path()
            self.client = QdrantClient(path=qdrant_path)
            Logger.success(f"✅ Connexion Qdrant locale établie ({qdrant_path})")
            self._ensure_collection()
        except Exception as e:
            Logger.error(f"Erreur connexion Qdrant: {e}")
            raise
    
    def is_available(self) -> bool:
        """Vérifie si Qdrant est disponible"""
        try:
            if self.client is None:
                return False
            # Test simple pour vérifier la connexion
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    def _ensure_collection(self):
        """Assure que la collection existe"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                Logger.info(f"Création collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                Logger.success(f"✅ Collection {self.collection_name} créée")
            else:
                Logger.info(f"Collection {self.collection_name} existe déjà")
        except Exception as e:
            Logger.error(f"Erreur gestion collection: {e}")
            raise
    
    def check_document_exists(self, file_hash: str) -> bool:
        """Vérifie si un document existe déjà par son hash"""
        try:
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_hash",
                            match=MatchValue(value=file_hash)
                        )
                    ]
                ),
                limit=1
            )
            return len(result[0]) > 0
        except Exception as e:
            Logger.error(f"Erreur vérification document: {e}")
            return False
    
    def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Stocke les chunks dans Qdrant"""
        if not chunks:
            return True
        
        try:
            points = []
            for i, chunk in enumerate(chunks):
                if not chunk.embedding:
                    Logger.warning(f"Chunk sans embedding ignoré: {chunk.chunk_id}")
                    continue
                
                point = PointStruct(
                    id=hash(chunk.chunk_id) % (2**63 - 1),  # ID numérique unique
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "doc_id": chunk.doc_id,
                        "page": chunk.page,
                        "chunk_id": chunk.chunk_id,
                        "file_path": chunk.file_path,
                        "file_hash": chunk.file_hash,
                        "created_at": chunk.created_at
                    }
                )
                points.append(point)
            
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                Logger.success(f"✅ {len(points)} chunks stockés dans Qdrant")
                return True
            else:
                Logger.warning("Aucun chunk valide à stocker")
                return False
                
        except Exception as e:
            Logger.error(f"Erreur stockage chunks: {e}")
            return False
    
    def search_similar(self, query_embedding: List[float], limit: int = 10, 
                      doc_ids: Optional[Union[str, List[str]]] = None) -> List[Dict[str, Any]]:
        """
        Recherche les chunks similaires avec filtrage par document(s)
        
        Args:
            query_embedding: Embedding de la requête
            limit: Nombre maximum de résultats
            doc_ids: ID(s) de document(s) pour filtrer la recherche
                    - str: recherche dans un seul document
                    - List[str]: recherche dans plusieurs documents
                    - None: recherche dans tous les documents
        
        Returns:
            Liste des chunks pertinents avec métadonnées
        """
        try:
            search_filter = None
            
            # Construire le filtre selon le type de doc_ids
            if doc_ids:
                if isinstance(doc_ids, str):
                    # Un seul document : utiliser MatchValue
                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key="doc_id",
                                match=MatchValue(value=doc_ids)
                            )
                        ]
                    )
                    Logger.target(f"Recherche filtrée sur le document: {doc_ids}")
                    
                elif isinstance(doc_ids, list) and len(doc_ids) > 0:
                    # Plusieurs documents : utiliser MatchAny
                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key="doc_id",
                                match=MatchAny(any=doc_ids)
                            )
                        ]
                    )
                    Logger.target(f"Recherche filtrée sur {len(doc_ids)} documents: {', '.join(doc_ids)}")
            else:
                Logger.global_search("Recherche dans tous les documents")
            
            # Effectuer la recherche
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True
            )
            
            # Formatter les résultats
            formatted_results = [
                {
                    "content": result.payload["content"],
                    "doc_id": result.payload["doc_id"],
                    "page": result.payload["page"],
                    "chunk_id": result.payload["chunk_id"],
                    "score": result.score,
                    "metadata": result.payload
                }
                for result in results
            ]
            
            Logger.stats(f"{len(formatted_results)} chunks trouvés")
            return formatted_results
            
        except Exception as e:
            Logger.error(f"Erreur recherche similaire: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            Logger.error(f"Erreur info collection: {e}")
            return {}
    
    def list_documents(self) -> List[DocumentInfo]:
        """
        Liste tous les documents disponibles dans la collection
        
        Returns:
            Liste des documents avec statistiques
        """
        try:
            # Récupérer tous les points pour analyser les documents
            all_points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Limite élevée pour récupérer tous les documents
                with_payload=True
            )
            
            # Analyser les documents
            documents = {}
            for point in all_points:
                doc_id = point.payload.get("doc_id", "inconnu")
                page = point.payload.get("page", 1)
                
                if doc_id not in documents:
                    documents[doc_id] = {
                        "chunks_count": 0,
                        "pages": set(),
                        "file_path": point.payload.get("file_path", ""),
                        "created_at": point.payload.get("created_at", "")
                    }
                
                documents[doc_id]["chunks_count"] += 1
                documents[doc_id]["pages"].add(page)
            
            # Convertir en objets DocumentInfo
            result = []
            for doc_id, info in documents.items():
                doc_info = DocumentInfo.from_analysis(doc_id, info)
                result.append(doc_info)
            
            # Trier par doc_id
            result.sort(key=lambda x: x.doc_id)
            
            Logger.books(f"{len(result)} documents trouvés dans la collection")
            return result
            
        except Exception as e:
            Logger.error(f"Erreur listage documents: {e}")
            return []

    def clear_collection(self) -> bool:
        """Vide complètement la collection"""
        try:
            self.client.delete_collection(self.collection_name)
            Logger.info(f"🧹 Collection {self.collection_name} supprimée")
            
            # Recréer la collection
            self._ensure_collection()
            Logger.success(f"✅ Collection {self.collection_name} recréée")
            return True
            
        except Exception as e:
            Logger.error(f"Erreur lors du vidage de la collection: {e}")
            return False
