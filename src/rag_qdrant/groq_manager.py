"""
Gestionnaire pour le LLM Groq Cloud API
"""

import os
from typing import Dict, Any

try:
    from groq import Groq
except ImportError:
    Groq = None

from .utils import Logger
from .base_llm_manager import BaseLLMManager

class GroqManager(BaseLLMManager):
    """Gestionnaire pour le LLM Groq via l'API Cloud"""
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialise le gestionnaire Groq
        
        Args:
            model_name: Nom du modèle Groq à utiliser
        """
        super().__init__(model_name)
    
    def _check_availability(self):
        """Vérifie la disponibilité de l'API Groq"""
        if not Groq:
            Logger.error("❌ Package groq non installé. Installer avec: pip install groq")
            return
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            Logger.error("❌ GROQ_API_KEY non définie dans les variables d'environnement")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            self.available = True
            Logger.success(f"✅ Groq disponible: {self.model_name}")
                
        except Exception as e:
            Logger.error(f"Erreur initialisation Groq: {e}")
    
    def _generate_raw_response(self, prompt: str, temperature: float) -> str:
        """Génère une réponse brute avec l'API Groq"""
        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.model_name,
            temperature=temperature,
            max_tokens=2000,
            top_p=0.9
        )
        
        return completion.choices[0].message.content.strip()
