"""
Gestionnaire d'ingestion incrémentale single-process avec hash et upsert
"""
import os
import hashlib
import threading
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Local imports
from config import Config
from smart_embeddings import SmartEmbeddingManager
from utils import Logger

# Singleton global pour le client Qdrant
_global_qdrant_client = None
_global_qdrant_lock = threading.Lock()
_ingest_queue_lock = threading.Lock()

class IncrementalQdrantIngester:
    """Gestionnaire d'ingestion incrémentale avec hash et upsert"""
    
    def __init__(self):
        self.config = Config
        self.qdrant_path = os.path.join(self.config.VECTORSTORE_DIR, "qdrant_db")
        self.embedding_manager = SmartEmbeddingManager()
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Base de données des hashes pour éviter les doublons
        self.processed_hashes = set()
        self._load_processed_hashes()
    
    def get_global_client(self) -> QdrantClient:
        """Obtenir le client Qdrant singleton"""
        global _global_qdrant_client
        
        with _global_qdrant_lock:
            if _global_qdrant_client is None:
                os.makedirs(self.qdrant_path, exist_ok=True)
                _global_qdrant_client = QdrantClient(path=self.qdrant_path)
                Logger.info(f"✅ Client Qdrant singleton créé: {self.qdrant_path}")
            
            return _global_qdrant_client
    
    def _generate_chunk_hash(self, content: str, metadata: dict) -> str:
        """Générer un hash stable pour un chunk"""
        # Créer une signature unique basée sur le contenu et les métadonnées critiques
        signature = f"{content}|{metadata.get('source', '')}|{metadata.get('page', 0)}"
        return hashlib.md5(signature.encode('utf-8')).hexdigest()
    
    def _generate_point_id(self, doc_path: str, page: int, chunk_idx: int, chunk_hash: str) -> int:
        """Générer un ID stable pour un point Qdrant (entier positif)"""
        # Créer un hash stable et le convertir en entier positif
        id_string = f"{Path(doc_path).stem}_p{page}_c{chunk_idx}_{chunk_hash[:8]}"
        # Utiliser hash() pour convertir en entier, puis prendre la valeur absolue
        return abs(hash(id_string)) % (2**31 - 1)  # Limiter à 31 bits pour éviter les débordements
    
    def _load_processed_hashes(self):
        """Charger les hashes déjà traités depuis Qdrant"""
        try:
            client = self.get_global_client()
            collections = client.get_collections().collections
            
            for collection in collections:
                if collection.name.startswith("documents_"):
                    # Récupérer tous les points pour obtenir leurs hashes
                    points, _ = client.scroll(
                        collection_name=collection.name,
                        limit=10000,  # Ajuster selon vos besoins
                        with_payload=True
                    )
                    
                    for point in points:
                        chunk_hash = point.payload.get('chunk_hash')
                        if chunk_hash:
                            self.processed_hashes.add(chunk_hash)
            
            Logger.info(f"Chargé {len(self.processed_hashes)} hashes de chunks existants")
            
        except Exception as e:
            Logger.warning(f"Erreur lors du chargement des hashes: {e}")
            self.processed_hashes = set()
    
    def _ensure_collection(self, embedding_model: str) -> str:
        """S'assurer que la collection existe"""
        collection_name = f"documents_{embedding_model.replace('/', '_').replace('-', '_')}"
        client = self.get_global_client()
        
        try:
            # Vérifier si la collection existe
            collections = client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)
            
            if not exists:
                # Obtenir la dimension du modèle
                embeddings = self.embedding_manager.get_embeddings(embedding_model)
                test_embedding = embeddings.embed_query("test")
                vector_size = len(test_embedding)
                
                Logger.info(f"Création de la collection '{collection_name}' avec dimension {vector_size}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                Logger.success(f"Collection '{collection_name}' créée")
            
            return collection_name
            
        except Exception as e:
            Logger.error(f"Erreur lors de la création de la collection: {e}")
            raise
    
    def process_document_incremental(self, file_path: str) -> Dict:
        """Traiter un document de manière incrémentale avec hash et upsert"""
        with _ingest_queue_lock:  # Mutex pour traiter un document à la fois
            
            file_path = Path(file_path).resolve()
            Logger.info(f"Traitement incrémental de: {file_path.name}")
            
            try:
                # Charger le document
                loader = PyPDFLoader(str(file_path))
                pages = loader.load()
                
                if not pages:
                    Logger.warning(f"Aucune page trouvée dans {file_path.name}")
                    return {"status": "skipped", "reason": "no_pages", "chunks_added": 0}
                
                # Déterminer le modèle d'embedding basé sur la taille
                page_count = len(pages)
                embedding_model = self.embedding_manager.get_document_embedding_model(page_count)
                Logger.info(f"Document {file_path.name}: {page_count} pages -> modèle: {embedding_model}")
                
                # S'assurer que la collection existe
                collection_name = self._ensure_collection(embedding_model)
                
                # Obtenir les embeddings
                embeddings = self.embedding_manager.get_embeddings(embedding_model)
                
                # Traiter les pages et créer les chunks
                all_chunks = []
                chunks_added = 0
                chunks_skipped = 0
                
                for page_idx, page in enumerate(pages):
                    # Splitter la page en chunks
                    page_chunks = self.text_splitter.split_text(page.page_content)
                    
                    for chunk_idx, chunk_content in enumerate(page_chunks):
                        # Créer les métadonnées
                        metadata = {
                            "source": str(file_path),
                            "page": page_idx + 1,
                            "chunk_index": chunk_idx,
                            "total_pages": page_count,
                            "embedding_model": embedding_model,
                            "ingestion_date": datetime.now().isoformat()
                        }
                        
                        # Générer le hash du chunk
                        chunk_hash = self._generate_chunk_hash(chunk_content, metadata)
                        metadata["chunk_hash"] = chunk_hash
                        
                        # Vérifier si ce chunk a déjà été traité
                        if chunk_hash in self.processed_hashes:
                            chunks_skipped += 1
                            continue
                        
                        # Générer l'ID stable du point
                        point_id = self._generate_point_id(str(file_path), page_idx + 1, chunk_idx, chunk_hash)
                        
                        # Créer l'embedding
                        vector = embeddings.embed_query(chunk_content)
                        
                        # Upsert dans Qdrant
                        client = self.get_global_client()
                        point = PointStruct(
                            id=point_id,
                            vector=vector,
                            payload={
                                "content": chunk_content,
                                **metadata
                            }
                        )
                        
                        client.upsert(
                            collection_name=collection_name,
                            points=[point]
                        )
                        
                        # Marquer ce hash comme traité
                        self.processed_hashes.add(chunk_hash)
                        chunks_added += 1
                
                Logger.success(f"Document {file_path.name}: {chunks_added} chunks ajoutés, {chunks_skipped} ignorés")
                
                return {
                    "status": "success",
                    "chunks_added": chunks_added,
                    "chunks_skipped": chunks_skipped,
                    "total_chunks": chunks_added + chunks_skipped,
                    "embedding_model": embedding_model,
                    "collection": collection_name
                }
                
            except Exception as e:
                Logger.error(f"Erreur lors du traitement de {file_path.name}: {e}")
                return {
                    "status": "error", 
                    "error": str(e),
                    "chunks_added": 0
                }
    
    def process_directory_incremental(self, data_dir: str = None) -> Dict:
        """Traiter tous les nouveaux documents d'un répertoire"""
        if data_dir is None:
            data_dir = self.config.DATA_DIR
        
        data_path = Path(data_dir)
        if not data_path.exists():
            return {"error": f"Répertoire non trouvé: {data_dir}"}
        
        # Trouver tous les PDFs
        pdf_files = list(data_path.glob("*.pdf"))
        if not pdf_files:
            return {"error": "Aucun fichier PDF trouvé"}
        
        Logger.info(f"🔄 Traitement incrémental de {len(pdf_files)} fichiers PDF...")
        
        results = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "total_chunks_added": 0,
            "files_details": {}
        }
        
        for pdf_file in pdf_files:
            result = self.process_document_incremental(str(pdf_file))
            
            results["files_details"][pdf_file.name] = result
            
            if result["status"] == "success":
                if result["chunks_added"] > 0:
                    results["processed"] += 1
                    results["total_chunks_added"] += result["chunks_added"]
                else:
                    results["skipped"] += 1
            elif result["status"] == "error":
                results["errors"] += 1
        
        Logger.success(f"Ingestion incrémentale terminée: {results['processed']} traités, {results['skipped']} ignorés, {results['errors']} erreurs")
        return results
    
    def get_collections_info(self) -> Dict:
        """Obtenir les informations sur les collections"""
        try:
            client = self.get_global_client()
            collections = client.get_collections().collections
            
            info = {}
            for collection in collections:
                if collection.name.startswith("documents_"):
                    collection_details = client.get_collection(collection.name)
                    
                    # Obtenir les documents uniques dans cette collection
                    documents = set()
                    try:
                        # Récupérer quelques points pour obtenir les métadonnées
                        points, _ = client.scroll(
                            collection_name=collection.name,
                            limit=1000,  # Limiter pour éviter de surcharger
                            with_payload=True
                        )
                        
                        for point in points:
                            if point.payload and 'source' in point.payload:
                                # Extraire le nom du fichier de la source
                                source = point.payload['source']
                                filename = os.path.basename(source)
                                documents.add(filename)
                    except Exception as e:
                        Logger.warning(f"Impossible de récupérer les documents de {collection.name}: {e}")
                    
                    info[collection.name] = {
                        "points_count": collection_details.points_count,
                        "vector_size": collection_details.config.params.vectors.size,
                        "documents": list(documents)
                    }
            
            return info
            
        except Exception as e:
            Logger.error(f"Erreur lors de la récupération des informations de collections: {e}")
            return {"error": str(e)}

def close_global_client():
    """Fermer le client global (pour cleanup)"""
    global _global_qdrant_client
    with _global_qdrant_lock:
        if _global_qdrant_client:
            try:
                _global_qdrant_client.close()
            except:
                pass
            _global_qdrant_client = None
            Logger.info("🔒 Client Qdrant singleton fermé")
