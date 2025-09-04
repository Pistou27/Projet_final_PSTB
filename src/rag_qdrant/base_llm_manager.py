"""
Classe de base abstraite pour les gestionnaires LLM
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any

from .utils import Logger

class BaseLLMManager(ABC):
    """Classe de base abstraite pour tous les gestionnaires LLM"""
    
    def __init__(self, model_name: str):
        """
        Initialise le gestionnaire LLM
        
        Args:
            model_name: Nom du modèle à utiliser
        """
        self.model_name = model_name
        self.client = None
        self.available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self):
        """Vérifie la disponibilité du service LLM - À implémenter par les sous-classes"""
        pass
    
    @abstractmethod
    def _generate_raw_response(self, prompt: str, temperature: float) -> str:
        """Génère une réponse brute - À implémenter par les sous-classes"""
        pass
    
    def generate_response(self, prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        """Génère une réponse avec le LLM au format JSON strict"""
        
        if not self.available:
            return {
                "answer": f"{self.__class__.__name__} non disponible",
                "citations": [],
                "claims": [],
                "error": f"{self.__class__.__name__} non configuré"
            }
        
        try:
            # Prompt enrichi pour forcer le format JSON
            structured_prompt = self._build_structured_prompt(prompt)
            
            # Génération avec le LLM spécifique
            raw_response = self._generate_raw_response(structured_prompt, temperature)
            
            Logger.info(f"🔍 Réponse brute {self.__class__.__name__}: {raw_response[:200]}...")
            
            # Nettoyer et valider le JSON
            return self._parse_and_validate_response(raw_response)
                
        except Exception as e:
            Logger.error(f"Erreur génération {self.__class__.__name__}: {e}")
            return {
                "answer": f"Erreur lors de la génération avec {self.__class__.__name__}: {str(e)}",
                "citations": [],
                "claims": [],
                "error": str(e)
            }
    
    def _build_structured_prompt(self, prompt: str) -> str:
        """Construit le prompt structuré pour forcer le format JSON"""
        return f"""{prompt}

IMPORTANT: Tu DOIS répondre UNIQUEMENT au format JSON suivant, sans aucun autre texte.

RÈGLES POUR LES CITATIONS ET RÉPONSES :
- Si tu peux répondre à la question avec les documents fournis, inclus les citations des pages pertinentes
- Si tu ne peux PAS répondre à la question car l'information n'est pas dans les documents, laisse le tableau "citations" VIDE []
- Si tu dis qu'il n'y a pas d'information, d'indication, ou que quelque chose n'est pas mentionné, tu NE DOIS PAS inclure de citations

RÈGLES POUR LE STYLE DE RÉPONSE :
- Si tu as des citations à inclure (c'est-à-dire si tu peux répondre avec les documents), commence TOUJOURS ta réponse par "C'est très simple, "
- Si tu n'as pas de citations (pas d'information trouvée), ne commence PAS par "C'est très simple"
- Structure ta réponse sur plusieurs lignes pour une meilleure lisibilité
- Utilise des sauts de ligne (<br>) pour séparer les différentes parties de ta réponse
- Organise les informations par points ou paragraphes quand c'est approprié
- Mets un <br> après "C'est très simple," pour commencer sur une nouvelle ligne

Format JSON requis :
{{
  "answer": "C'est très simple,<br><br>ta réponse détaillée en français ici<br><br>avec des sauts de ligne<br>pour une meilleure structure",
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
    
    def _parse_and_validate_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse et valide la réponse JSON"""
        try:
            # Enlever les blocs de code markdown si présents
            cleaned_response = raw_response
            if '```' in cleaned_response:
                # Extraire le contenu entre les blocs de code
                lines = cleaned_response.split('\n')
                json_lines = []
                in_json_block = False
                
                for line in lines:
                    if line.startswith('```'):
                        in_json_block = not in_json_block
                        continue
                    if in_json_block or ('{' in line or '}' in line or '"' in line):
                        json_lines.append(line)
                
                cleaned_response = '\n'.join(json_lines).strip()
            
            # Nettoyer les espaces et caractères parasites
            cleaned_response = cleaned_response.strip()
            
            # Essayer de trouver le JSON s'il y a du texte avant/après
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_response = cleaned_response[start_idx:end_idx + 1]
            
            Logger.info(f"🧹 JSON nettoyé: {cleaned_response[:100]}...")
            
            # Parser le JSON
            parsed_response = json.loads(cleaned_response)
            
            # Valider la structure
            required_keys = ["answer", "citations", "claims"]
            if all(key in parsed_response for key in required_keys):
                # Vérifier si la réponse indique une absence d'information
                answer = parsed_response.get("answer", "").lower()
                
                # Mots-clés indiquant une absence d'information
                no_info_phrases = [
                    "il n'y a pas d'information",
                    "aucune information",
                    "pas d'information sur",
                    "ne contient pas d'information",
                    "n'est pas mentionné",
                    "pas de mention",
                    "contexte ne contient pas",
                    "documents ne contiennent pas",
                    "je ne trouve pas d'information",
                    "il n'existe pas d'indication",
                    "aucune indication",
                    "pas d'indication sur",
                    "ne présente pas d'information",
                    "n'indique pas",
                    "pas précisé",
                    "non mentionné",
                    "absent des documents"
                ]
                
                # Si la réponse indique une absence d'information, vider les citations
                if any(phrase in answer for phrase in no_info_phrases):
                    parsed_response["citations"] = []
                    parsed_response["claims"] = []
                    Logger.info("🚫 Absence d'information détectée - citations supprimées")
                
                return parsed_response
            else:
                raise ValueError("Structure JSON invalide")
                
        except (json.JSONDecodeError, ValueError) as e:
            Logger.warning(f"Réponse JSON invalide, reformatage: {e}")
            # Fallback vers structure JSON basique
            clean_text = raw_response.replace('\n', ' ').strip()
            return {
                "answer": clean_text,
                "citations": [],
                "claims": [{"text": clean_text, "citations": []}]
            }
    
    def is_available(self) -> bool:
        """Vérifie si le LLM est disponible"""
        return self.available
