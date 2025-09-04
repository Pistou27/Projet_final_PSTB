"""
Gestionnaire pour le LLM Mistral via Ollama
"""

from typing import Dict, Any

try:
    import ollama
except ImportError:
    ollama = None

from .config import RAGConfig
from .utils import Logger
from .base_llm_manager import BaseLLMManager

class MistralManager(BaseLLMManager):
    """Gestionnaire pour le LLM Mistral via Ollama"""
    
    def __init__(self, model_name: str = None):
        """
        Initialise le gestionnaire Mistral
        
        Args:
            model_name: Nom du modèle Mistral à utiliser (défaut: config)
        """
        super().__init__(model_name or RAGConfig.MISTRAL_MODEL)
    
    def _check_availability(self):
        """Vérifie la disponibilité d'Ollama et Mistral"""
        if not ollama:
            Logger.error("❌ Ollama non installé. Installer avec: pip install ollama")
            return
        
        try:
            self.client = ollama.Client()
            models = self.client.list()
            
            available_models = []
            if hasattr(models, 'models'):
                available_models = [model.model for model in models.models]
            elif isinstance(models, dict) and 'models' in models:
                available_models = [model['name'] for model in models['models']]
            
            if self.model_name in available_models:
                self.available = True
                Logger.success(f"✅ Mistral disponible: {self.model_name}")
            else:
                Logger.error(f"❌ Modèle {self.model_name} non trouvé")
                Logger.info(f"Modèles disponibles: {', '.join(available_models)}")
                Logger.info(f"Pour installer: ollama pull {self.model_name}")
                
        except Exception as e:
            Logger.error(f"Erreur vérification Ollama: {e}")
    
    def _generate_raw_response(self, prompt: str, temperature: float) -> str:
        """Génère une réponse brute avec Ollama/Mistral"""
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_predict": RAGConfig.GENERATION_MAX_TOKENS
            }
        )
        
        return response['message']['content'].strip()
