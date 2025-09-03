"""
Gestion de la mémoire conversationnelle avec SQLite
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config import Config
from utils import safe_json_loads, safe_json_dumps, now_timestamp

class MemoryStore:
    """Gestionnaire de mémoire conversationnelle persistante"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.MEMORY_DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Initialiser la base de données SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    context_used TEXT,
                    sources TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    title TEXT
                )
            """)
            
            conn.commit()
    
    def create_session(self, session_id: str, title: str = "Nouvelle conversation") -> str:
        """Créer une nouvelle session de conversation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (session_id, title, last_activity)
                VALUES (?, ?, ?)
            """, (session_id, title, datetime.now()))
            conn.commit()
        return session_id
    
    def add_exchange(self, session_id: str, user_message: str, assistant_response: str, 
                    context_used: List[str] = None, sources: List[str] = None):
        """Ajouter un échange à la conversation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Mettre à jour l'activité de la session
            cursor.execute("""
                UPDATE sessions SET last_activity = ? WHERE session_id = ?
            """, (now_timestamp(), session_id))
            
            # Ajouter l'échange
            context_json = safe_json_dumps(context_used) if context_used else None
            sources_json = safe_json_dumps(sources) if sources else None
            
            cursor.execute("""
                INSERT INTO conversations 
                (session_id, user_message, assistant_response, context_used, sources)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_message, assistant_response, context_json, sources_json))
            
            conn.commit()
    
    def add_message(self, session_id: str, role: str, content: str):
        """Ajouter un message individuel à la conversation (pour compatibilité)"""
        # Cette méthode stocke temporairement les messages pour les assembler en échanges
        # Pour l'instant, on va simplement mettre à jour l'activité de la session
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET last_activity = ? WHERE session_id = ?
            """, (now_timestamp(), session_id))
            conn.commit()
        
        # Note: Une implémentation plus complète pourrait stocker les messages individuels
        # et les assembler en échanges complets plus tard
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Récupérer l'historique de conversation pour une session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, user_message, assistant_response, sources
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, limit))
            
            rows = cursor.fetchall()
            
            history = []
            for row in reversed(rows):  # Inverser pour avoir l'ordre chronologique
                timestamp, user_msg, assistant_msg, sources_json = row
                sources = safe_json_loads(sources_json, [])
                
                history.append({
                    "timestamp": timestamp,
                    "user_message": user_msg,
                    "assistant_response": assistant_msg,
                    "sources": sources
                })
            
            return history
    
    def get_conversation(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Alias pour get_conversation_history (pour compatibilité)"""
        return self.get_conversation_history(session_id, limit)
    
    def get_recent_context(self, session_id: str, num_exchanges: int = 3) -> str:
        """Récupérer le contexte récent pour alimenter le prompt"""
        history = self.get_conversation_history(session_id, num_exchanges)
        
        if not history:
            return ""
        
        context_parts = []
        for exchange in history:
            context_parts.append(f"Utilisateur: {exchange['user_message']}")
            context_parts.append(f"Assistant: {exchange['assistant_response']}")
        
        return "\n".join(context_parts)
    
    def get_all_sessions(self) -> List[Dict]:
        """Récupérer toutes les sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, title, created_at, last_activity,
                       (SELECT COUNT(*) FROM conversations WHERE session_id = s.session_id) as message_count
                FROM sessions s
                ORDER BY last_activity DESC
            """)
            
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                session_id, title, created_at, last_activity, message_count = row
                sessions.append({
                    "session_id": session_id,
                    "title": title,
                    "created_at": created_at,
                    "last_activity": last_activity,
                    "message_count": message_count
                })
            
            return sessions
    
    def delete_session(self, session_id: str):
        """Supprimer une session et tous ses messages"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Récupérer les informations d'une session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, created_at, last_activity 
                FROM sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                title, created_at, last_activity = row
                return {
                    "session_id": session_id,
                    "title": title,
                    "created_at": created_at,
                    "last_activity": last_activity
                }
            return None
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques de la base de données de mémoire"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Compter les sessions
                cursor.execute("SELECT COUNT(*) FROM sessions")
                session_count = cursor.fetchone()[0]
                
                # Compter les messages
                cursor.execute("SELECT COUNT(*) FROM conversation_history")
                message_count = cursor.fetchone()[0]
                
                # Obtenir la session la plus récente
                cursor.execute("""
                    SELECT last_activity 
                    FROM sessions 
                    ORDER BY last_activity DESC 
                    LIMIT 1
                """)
                last_activity_row = cursor.fetchone()
                last_activity = last_activity_row[0] if last_activity_row else None
                
                return {
                    "database_path": self.db_path,
                    "session_count": session_count,
                    "total_messages": message_count,
                    "last_activity": last_activity,
                    "status": "active"
                }
                
        except Exception as e:
            return {
                "database_path": self.db_path,
                "session_count": 0,
                "total_messages": 0,
                "last_activity": None,
                "status": f"error: {str(e)}"
            }
