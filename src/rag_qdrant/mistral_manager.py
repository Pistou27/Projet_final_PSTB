"""
Gestionnaire pour le LLM Mistral via Ollama
"""

import json
from typing import Dict, Any

try:
    import ollama
except ImportError:
    ollama = None

from .config import RAGConfig
from .utils import Logger

class MistralManager:
    """Gestionnaire pour le LLM Mistral via Ollama"""
    
    def __init__(self, model_name: str = None):
        """
        Initialise le gestionnaire Mistral
        
        Args:
            model_name: Nom du modèle Mistral à utiliser (défaut: config)
        """
        self.model_name = model_name or RAGConfig.MISTRAL_MODEL
        self.client = None
        self.available = False
        self._check_availability()
    
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
    
    def generate_response(self, prompt: str, temperature: float = None) -> Dict[str, Any]:
        """Génère une réponse avec Mistral au format JSON strict"""
        temperature = temperature or RAGConfig.GENERATION_TEMPERATURE
        
        if not self.available:
            return {
                "answer": "Mistral non disponible",
                "citations": [],
                "claims": [],
                "error": "Mistral/Ollama non configuré"
            }
        
        try:
            # Prompt enrichi pour forcer le format JSON
            structured_prompt = f"""{prompt}

IMPORTANT: Tu DOIS répondre UNIQUEMENT au format JSON suivant, sans aucun autre texte :
{{
  "answer": "ta réponse détaillée en français ici",
  "citations": [
    {{"doc_id": "nom_du_document", "page": "numéro_de_page"}}
  ],
  "claims": [
    {{
      "text": "affirmation_précise_extraite_de_la_réponse",
      "citations": [
        {{"doc_id": "nom_du_document", "page": "numéro_de_page"}}
      ]
    }}
  ]
}}

Réponse JSON:"""

            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": structured_prompt}],
                options={
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": RAGConfig.GENERATION_MAX_TOKENS
                }
            )
            
            raw_response = response['message']['content'].strip()
            
            # Nettoyer et valider le JSON
            try:
                # Enlever les blocs de code markdown si présents
                if raw_response.startswith('```'):
                    lines = raw_response.split('\n')
                    start_idx = 1 if lines[0].startswith('```') else 0
                    end_idx = -1 if lines[-1].startswith('```') else len(lines)
                    raw_response = '\n'.join(lines[start_idx:end_idx])
                
                # Parser le JSON
                parsed_response = json.loads(raw_response)
                
                # Valider la structure
                required_keys = ["answer", "citations", "claims"]
                if all(key in parsed_response for key in required_keys):
                    return parsed_response
                else:
                    raise ValueError("Structure JSON invalide")
                    
            except (json.JSONDecodeError, ValueError) as e:
                Logger.warning(f"Réponse JSON invalide, reformatage: {e}")
                # Fallback vers structure JSON basique
                clean_text = raw_response.replace('"', '\\"').replace('\n', ' ')
                return {
                    "answer": clean_text,
                    "citations": [],
                    "claims": [{"text": clean_text, "citations": []}]
                }
                
        except Exception as e:
            Logger.error(f"Erreur génération Mistral: {e}")
            return {
                "answer": f"Erreur lors de la génération: {str(e)}",
                "citations": [],
                "claims": [],
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Vérifie si Mistral est disponible"""
        return self.available
