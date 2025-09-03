"""
Schémas de données pour le pipeline RAG
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class DocumentChunk:
    """Représente un chunk de document avec ses métadonnées"""
    content: str
    doc_id: str
    page: int
    chunk_id: str
    file_path: str
    file_hash: str
    created_at: str
    embedding: Optional[List[float]] = None
    
    @classmethod
    def create(cls, content: str, doc_id: str, page: int, chunk_num: int, 
               file_path: str, file_hash: str) -> "DocumentChunk":
        """Factory method pour créer un chunk"""
        chunk_id = f"{doc_id}_p{page}_c{chunk_num}"
        return cls(
            content=content.strip(),
            doc_id=doc_id,
            page=page,
            chunk_id=chunk_id,
            file_path=file_path,
            file_hash=file_hash,
            created_at=datetime.now().isoformat()
        )


@dataclass
class RAGResponse:
    """Réponse structurée du système RAG"""
    answer: str
    citations: List[Dict[str, str]]
    claims: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    
    @classmethod
    def error(cls, error_message: str, processing_time: float = 0.0) -> "RAGResponse":
        """Factory method pour créer une réponse d'erreur"""
        return cls(
            answer=f"Erreur système: {error_message}",
            citations=[],
            claims=[],
            sources=[],
            confidence=0.0,
            processing_time=processing_time,
            success=False,
            error_message=error_message
        )
    
    @classmethod
    def empty(cls, processing_time: float = 0.0) -> "RAGResponse":
        """Factory method pour créer une réponse vide"""
        return cls(
            answer="Aucune information pertinente trouvée.",
            citations=[],
            claims=[],
            sources=[],
            confidence=0.0,
            processing_time=processing_time,
            success=False,
            error_message="Aucun contexte disponible"
        )


@dataclass
class DocumentIngestionResult:
    """Résultat d'ingestion d'un document individuel"""
    doc_id: str
    chunks_created: int
    pages_processed: int
    success: bool
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, doc_id: str, chunks_created: int, pages_processed: int) -> "DocumentIngestionResult":
        """Factory method pour un résultat de succès"""
        return cls(
            doc_id=doc_id,
            chunks_created=chunks_created,
            pages_processed=pages_processed,
            success=True
        )
    
    @classmethod
    def error_result(cls, doc_id: str, error: str) -> "DocumentIngestionResult":
        """Factory method pour un résultat d'erreur"""
        return cls(
            doc_id=doc_id,
            chunks_created=0,
            pages_processed=0,
            success=False,
            error=error
        )


@dataclass
class IngestionStats:
    """Statistiques d'ingestion des documents"""
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    total_chunks: int = 0
    
    def add_success(self, chunks_count: int):
        """Ajoute un document traité avec succès"""
        self.processed += 1
        self.total_chunks += chunks_count
    
    def add_skip(self):
        """Ajoute un document ignoré"""
        self.skipped += 1
    
    def add_error(self):
        """Ajoute un document en erreur"""
        self.errors += 1
    
    def to_dict(self) -> Dict[str, int]:
        """Convertit en dictionnaire"""
        return {
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_chunks": self.total_chunks
        }


@dataclass
class DocumentInfo:
    """Informations sur un document dans la collection"""
    doc_id: str
    chunks_count: int
    pages_count: int
    pages_range: str
    file_path: str
    created_at: str
    
    @classmethod
    def from_analysis(cls, doc_id: str, chunks_data: Dict[str, Any]) -> "DocumentInfo":
        """Crée une instance à partir de l'analyse des chunks"""
        pages = chunks_data["pages"]
        return cls(
            doc_id=doc_id,
            chunks_count=chunks_data["chunks_count"],
            pages_count=len(pages),
            pages_range=f"{min(pages)}-{max(pages)}" if pages else "0",
            file_path=chunks_data["file_path"],
            created_at=chunks_data["created_at"]
        )
