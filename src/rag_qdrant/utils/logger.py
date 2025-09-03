"""
Logger centralisé avec emojis pour le pipeline RAG
"""

class Logger:
    """Logger simple avec emojis et niveaux"""
    
    @staticmethod
    def success(message: str) -> None:
        """Message de succès"""
        print(f"✅ {message}")
    
    @staticmethod
    def error(message: str) -> None:
        """Message d'erreur"""
        print(f"❌ {message}")
    
    @staticmethod
    def warning(message: str) -> None:
        """Message d'avertissement"""
        print(f"⚠️  {message}")
    
    @staticmethod
    def info(message: str) -> None:
        """Message d'information"""
        print(f"ℹ️  {message}")
    
    @staticmethod
    def debug(message: str) -> None:
        """Message de debug"""
        print(f"🐛 {message}")
    
    @staticmethod
    def loading(message: str) -> None:
        """Message de chargement"""
        print(f"🔄 {message}")
    
    @staticmethod
    def rocket(message: str) -> None:
        """Message de démarrage"""
        print(f"🚀 {message}")
    
    @staticmethod
    def robot(message: str) -> None:
        """Message du système"""
        print(f"🤖 {message}")
    
    @staticmethod
    def search(message: str) -> None:
        """Message de recherche"""
        print(f"🔍 {message}")
    
    @staticmethod
    def document(message: str) -> None:
        """Message relatif aux documents"""
        print(f"📄 {message}")
    
    @staticmethod
    def target(message: str) -> None:
        """Message de ciblage/filtrage"""
        print(f"🎯 {message}")
    
    @staticmethod
    def global_search(message: str) -> None:
        """Message de recherche globale"""
        print(f"🌐 {message}")
    
    @staticmethod
    def stats(message: str) -> None:
        """Message de statistiques"""
        print(f"📊 {message}")
    
    @staticmethod
    def books(message: str) -> None:
        """Message relatif aux livres/documents"""
        print(f"📚 {message}")
