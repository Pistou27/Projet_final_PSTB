"""
Gestionnaire pour le traitement et l'extraction de contenu des documents
"""

import hashlib
from pathlib import Path
from typing import List, Dict

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from .config import RAGConfig
from .schemas import DocumentChunk
from .utils import Logger

class DocumentProcessor:
    """Gestionnaire pour le traitement et l'extraction de contenu des documents"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialise le processeur de documents
        
        Args:
            chunk_size: Taille des chunks en caractères (défaut: config)
            chunk_overlap: Chevauchement entre chunks en caractères (défaut: config)
        """
        self.chunk_size = chunk_size or RAGConfig.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or RAGConfig.CHUNK_OVERLAP
        Logger.document(f"Processeur de documents initialisé (chunk: {self.chunk_size}, overlap: {self.chunk_overlap})")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash SHA256 d'un fichier"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            Logger.error(f"Erreur calcul hash pour {file_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[int, str]:
        """Extrait le texte d'un PDF page par page"""
        if PyPDF2 is None:
            Logger.error("PyPDF2 non installé. Installer avec: pip install PyPDF2")
            return {}
        
        pages_content = {}
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        pages_content[page_num] = text.strip()
            Logger.info(f"📖 PDF extrait: {len(pages_content)} pages depuis {Path(file_path).name}")
        except Exception as e:
            Logger.error(f"Erreur extraction PDF {file_path}: {e}")
        return pages_content
    
    def extract_text_from_txt(self, file_path: str) -> Dict[int, str]:
        """Extrait le texte d'un fichier TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    return {1: content}  # Tout le contenu sur "page" 1
            Logger.info(f"📄 TXT extrait: {Path(file_path).name}")
        except Exception as e:
            Logger.error(f"Erreur extraction TXT {file_path}: {e}")
        return {}
    
    def create_chunks(self, text: str, doc_id: str, page: int, file_path: str, file_hash: str) -> List[DocumentChunk]:
        """Crée des chunks avec chevauchement depuis un texte"""
        chunks = []
        text_length = len(text)
        
        if text_length <= self.chunk_size:
            # Texte assez court, un seul chunk
            chunk = DocumentChunk.create(
                content=text,
                doc_id=doc_id,
                page=page,
                chunk_num=1,
                file_path=file_path,
                file_hash=file_hash
            )
            chunks.append(chunk)
        else:
            # Diviser en chunks avec chevauchement
            chunk_num = 1
            start = 0
            
            while start < text_length:
                end = min(start + self.chunk_size, text_length)
                chunk_text = text[start:end]
                
                # Éviter de couper au milieu des mots (sauf si le chunk est trop petit)
                if end < text_length and len(chunk_text) > 100:
                    last_space = chunk_text.rfind(' ')
                    if last_space > len(chunk_text) * 0.8:  # Au moins 80% du chunk
                        end = start + last_space
                        chunk_text = text[start:end]
                
                chunk = DocumentChunk.create(
                    content=chunk_text,
                    doc_id=doc_id,
                    page=page,
                    chunk_num=chunk_num,
                    file_path=file_path,
                    file_hash=file_hash
                )
                chunks.append(chunk)
                
                # Préparer pour le chunk suivant avec chevauchement
                start = end - self.chunk_overlap if end < text_length else end
                chunk_num += 1
                
                # Sécurité pour éviter boucle infinie
                if chunk_num > 1000:
                    Logger.warning(f"Arrêt chunking après 1000 chunks pour {doc_id}")
                    break
        
        Logger.info(f"📝 {len(chunks)} chunks créés pour {doc_id} page {page}")
        return chunks
    
    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """Traite un document complet et retourne ses chunks"""
        file_path = Path(file_path)
        doc_id = file_path.stem
        file_hash = self.calculate_file_hash(str(file_path))
        
        Logger.info(f"🔄 Traitement document: {file_path.name} (hash: {file_hash[:8]}...)")
        
        # Extraction basée sur l'extension
        if file_path.suffix.lower() == '.pdf':
            pages_content = self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() == '.txt':
            pages_content = self.extract_text_from_txt(str(file_path))
        else:
            Logger.error(f"Format de fichier non supporté: {file_path.suffix}")
            return []
        
        # Créer chunks pour chaque page
        all_chunks = []
        for page_num, page_text in pages_content.items():
            if page_text.strip():
                page_chunks = self.create_chunks(
                    page_text, doc_id, page_num, str(file_path), file_hash
                )
                all_chunks.extend(page_chunks)
        
        Logger.success(f"✅ Document traité: {len(all_chunks)} chunks total pour {file_path.name}")
        return all_chunks
