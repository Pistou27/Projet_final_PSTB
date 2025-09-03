"""
Utilitaires communs pour le projet RAG
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

def now_utc_iso() -> str:
    """Retourne l'heure actuelle en format ISO"""
    return datetime.now().isoformat()

def now_formatted(format_str: str = '%Y-%m-%d %H:%M') -> str:
    """Retourne l'heure actuelle avec un format personnalisé"""
    return datetime.now().strftime(format_str)

def now_timestamp() -> datetime:
    """Retourne l'heure actuelle comme objet datetime"""
    return datetime.now()

def ensure_directory(path: str) -> None:
    """Créer un répertoire s'il n'existe pas"""
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_parent_directory(file_path: str) -> None:
    """Créer le répertoire parent d'un fichier s'il n'existe pas"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

def add_to_path(path: str) -> None:
    """Ajouter un chemin au sys.path s'il n'y est pas déjà"""
    if path not in sys.path:
        sys.path.insert(0, path)

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Parse JSON de manière sécurisée avec valeur par défaut"""
    try:
        return json.loads(json_str) if json_str else default
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Sérialise en JSON de manière sécurisée"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default

def get_file_size_mb(file_path: str) -> float:
    """Retourne la taille d'un fichier en MB"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except OSError:
        return 0.0

def validate_file_exists(file_path: str) -> bool:
    """Vérifier qu'un fichier existe"""
    return os.path.isfile(file_path)

def get_project_root() -> str:
    """Retourne le répertoire racine du projet"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def calculate_file_hash(file_path: str) -> str:
    """Calcule le hash SHA256 d'un fichier"""
    import hashlib
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        Logger.error(f"Erreur calcul hash pour {file_path}: {e}")
        return ""

def generate_chunk_hash(content: str, metadata: dict) -> str:
    """Générer un hash stable pour un chunk"""
    import hashlib
    signature = f"{content}|{metadata.get('source', '')}|{metadata.get('page', 0)}"
    return hashlib.md5(signature.encode('utf-8')).hexdigest()

def count_pdf_pages(pdf_path: str) -> int:
    """Compter le nombre de pages d'un PDF"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        Logger.warning(f"Erreur lors du comptage des pages pour {pdf_path}: {e}")
        return 1  # Par défaut, considérer comme 1 page

class Logger:
    """Simple logger avec emojis et niveaux"""
    
    @staticmethod
    def success(message: str) -> None:
        print(f"✅ {message}")
    
    @staticmethod
    def error(message: str) -> None:
        print(f"❌ {message}")
    
    @staticmethod
    def warning(message: str) -> None:
        print(f"⚠️  {message}")
    
    @staticmethod
    def info(message: str) -> None:
        print(f"ℹ️  {message}")
    
    @staticmethod
    def debug(message: str) -> None:
        print(f"🐛 {message}")
    
    @staticmethod
    def loading(message: str) -> None:
        print(f"🔄 {message}")
    
    @staticmethod
    def rocket(message: str) -> None:
        print(f"🚀 {message}")
    
    @staticmethod
    def robot(message: str) -> None:
        print(f"🤖 {message}")
    
    @staticmethod
    def books(message: str) -> None:
        print(f"📚 {message}")
    
    @staticmethod
    def globe(message: str) -> None:
        print(f"🌐 {message}")

# Alias pour compatibilité
log = Logger()
