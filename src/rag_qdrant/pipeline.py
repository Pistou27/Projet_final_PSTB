"""

Pipeline principal RAG avec Qdrant et Mistral
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from .config import RAGConfig
from .schemas import DocumentChunk, RAGResponse, IngestionStats, DocumentInfo, DocumentIngestionResult
from .utils import Logger, timer
from .document_processor import DocumentProcessor
from .embedding_manager import EmbeddingManager
from .reranker_manager import RerankerManager
from .qdrant_manager import QdrantManager
from .mistral_manager import MistralManager
from .groq_manager import GroqManager

class RAGPipeline:
    """Pipeline RAG complet avec ingestion et recherche"""
    
    def __init__(self, collection_name: str = None):
        """
        Initialise le pipeline RAG
        
        Args:
            collection_name: Nom de la collection Qdrant (défaut: config)
        """
        self.collection_name = collection_name or RAGConfig.COLLECTION_NAME
        
        # Initialiser les composants
        self.doc_processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
        self.reranker_manager = RerankerManager()
        self.qdrant_manager = QdrantManager(collection_name=self.collection_name)
        self.mistral_manager = MistralManager()
        self.groq_manager = GroqManager()
        
        Logger.info(f"🔧 Pipeline RAG initialisé pour collection: {self.collection_name}")
    
    @timer
    def ingest_document(self, doc_path: Path, doc_id: str) -> IngestionStats:
        """
        Ingère un document dans la base vectorielle
        
        Args:
            doc_path: Chemin vers le document PDF
            doc_id: Identifiant unique du document
            
        Returns:
            Statistiques d'ingestion
        """
        Logger.info(f"📄 Démarrage ingestion: {doc_id}")
        
        try:
            # 1. Extraction et chunking
            chunks = self.doc_processor.process_document(str(doc_path))
            Logger.info(f"📋 {len(chunks)} chunks extraits")
            
            # 2. Génération des embeddings
            embeddings = self.embedding_manager.encode_texts([chunk.content for chunk in chunks])
            Logger.info(f"🔢 {len(embeddings)} embeddings générés")
            
            # 3. Assignation des embeddings aux chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # 4. Stockage dans Qdrant
            self.qdrant_manager.store_chunks(chunks)
            Logger.success(f"✅ Document {doc_id} ingéré avec succès")
            
            # Calculer le nombre de pages
            pages_processed = len(set(chunk.page for chunk in chunks)) if chunks else 0
            
            return DocumentIngestionResult.success_result(
                doc_id=doc_id,
                chunks_created=len(chunks),
                pages_processed=pages_processed
            )
            
        except Exception as e:
            Logger.error(f"❌ Erreur ingestion {doc_id}: {e}")
            return DocumentIngestionResult.error_result(
                doc_id=doc_id,
                error=str(e)
            )
    
    @timer
    def search(self, query: str, doc_ids: Optional[List[str]] = None, 
               limit: int = None, use_reranking: bool = True, llm_provider: str = "mistral") -> RAGResponse:
        """
        Recherche sémantique avec RAG
        
        Args:
            query: Question de l'utilisateur
            doc_ids: Liste des documents à filtrer (optionnel)
            limit: Nombre de résultats max (défaut: config)
            use_reranking: Utiliser le reranking (défaut: True)
            llm_provider: Fournisseur LLM ("mistral" ou "groq", défaut: "mistral")
            
        Returns:
            Réponse RAG complète
        """
        limit = limit or RAGConfig.DEFAULT_TOP_K
        
        Logger.info(f"🔍 Recherche: '{query}'")
        if doc_ids:
            Logger.info(f"📚 Filtrage sur documents: {doc_ids}")
        
        try:
            # 1. Générer l'embedding de la requête
            query_embedding = self.embedding_manager.encode_single(query)
            
            # 2. Recherche vectorielle dans Qdrant
            search_results = self.qdrant_manager.search_similar(
                query_embedding=query_embedding,
                limit=limit * 2 if use_reranking else limit,  # Plus de résultats pour le reranking
                doc_ids=doc_ids
            )
            
            # Convertir les résultats en DocumentChunk
            chunks = []
            for result in search_results:
                chunk = DocumentChunk(
                    content=result["content"],
                    doc_id=result["doc_id"],
                    page=result["page"],
                    chunk_id=result["chunk_id"],
                    file_path="",  # Pas stocké dans Qdrant
                    file_hash="",  # Pas nécessaire ici
                    created_at=""  # Pas nécessaire ici
                )
                chunks.append(chunk)
            
            Logger.info(f"🎯 {len(chunks)} chunks trouvés")
            
            # 3. Reranking (optionnel)
            if use_reranking and chunks and self.reranker_manager.is_available():
                # Extraire les textes pour le reranking
                passages = [chunk.content for chunk in chunks]
                scores = self.reranker_manager.rerank(query, passages)
                
                # Trier par score et garder le top_k configuré
                chunk_scores = list(zip(chunks, scores))
                chunk_scores.sort(key=lambda x: x[1], reverse=True)
                rerank_limit = min(limit, RAGConfig.DEFAULT_RERANK_TOP_K)
                chunks = [chunk for chunk, score in chunk_scores[:rerank_limit]]
                Logger.info(f"🏆 {len(chunks)} chunks après reranking")
            
            # 4. Construire le contexte
            context = self._build_context(chunks)
            
            # 5. Génération avec LLM choisi
            prompt = self._build_prompt(query, context)
            
            if llm_provider == "groq" and self.groq_manager.is_available():
                response = self.groq_manager.generate_response(prompt)
                Logger.info(f"🤖 Réponse générée avec Groq: {llm_provider}")
            else:
                response = self.mistral_manager.generate_response(prompt)
                Logger.info(f"🤖 Réponse générée avec Mistral (fallback ou choix)")
            
            # 6. Enrichir avec métadonnées et sources
            sources = []
            
            # Si il n'y a pas de citations (absence d'info détectée), ne pas ajouter de sources
            if response.get("citations", []):
                for chunk in chunks:
                    sources.append({
                        "doc_id": chunk.doc_id,
                        "page": chunk.page,
                        "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        "score": getattr(chunk, 'score', 0.8)  # Score si disponible
                    })
                Logger.info(f"📚 {len(sources)} sources ajoutées")
            else:
                Logger.info("🚫 Aucune source ajoutée (absence d'information détectée)")
            
            response["sources"] = sources
            response["confidence"] = 0.8  # Valeur par défaut
            response["processing_time"] = 0.0  # À calculer
            response["success"] = True
            
            Logger.success(f"✅ Réponse générée avec {len(chunks)} chunks")
            
            return RAGResponse(
                answer=response["answer"],
                citations=response["citations"],
                claims=response["claims"],
                sources=response["sources"],
                confidence=response["confidence"],
                processing_time=response["processing_time"],
                success=response["success"]
            )
            
        except Exception as e:
            Logger.error(f"❌ Erreur recherche: {e}")
            return RAGResponse(
                answer=f"Erreur lors de la recherche: {str(e)}",
                citations=[],
                claims=[],
                sources=[],
                confidence=0.0,
                processing_time=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _build_context(self, chunks: List[DocumentChunk]) -> str:
        """Construit le contexte à partir des chunks récupérés"""
        if not chunks:
            return "Aucun document pertinent trouvé."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_part = f"""
Document: {chunk.doc_id}
Page: {chunk.page}
Contenu: {chunk.content}
---"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Construit le prompt pour Mistral"""
        return f"""Tu es un assistant IA spécialisé dans l'analyse de documents de jeux de société.

Contexte extrait des documents:
{context}

Question: {query}

Instructions:
1. Réponds uniquement en français
2. Base ta réponse sur le contexte fourni
3. Si l'information n'est pas dans le contexte, dis-le clairement
4. Cite tes sources en indiquant le document et la page

Réponds en français avec les détails pertinents du contexte."""
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la collection"""
        return self.qdrant_manager.get_collection_info()
    
    def list_documents(self) -> List[DocumentInfo]:
        """Liste tous les documents dans la collection"""
        return self.qdrant_manager.list_documents()
    
    def delete_document(self, doc_id: str) -> bool:
        """Supprime un document de la collection"""
        return self.qdrant_manager.delete_document(doc_id)
    
    def clear_collection(self) -> bool:
        """Vide complètement la collection"""
        return self.qdrant_manager.clear_collection()
    
    def health_check(self) -> Dict[str, bool]:
        """Vérifie la santé de tous les composants"""
        return {
            "embedding_manager": self.embedding_manager.is_available(),
            "reranker_manager": self.reranker_manager.is_available(),
            "qdrant_manager": self.qdrant_manager.is_available(),
            "mistral_manager": self.mistral_manager.is_available(),
            "groq_manager": self.groq_manager.is_available()
        }
