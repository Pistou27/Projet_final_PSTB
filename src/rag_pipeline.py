"""
Pipeline RAG avec LangChain et alternative LLM
"""
import os
from typing import List, Dict, Tuple, Optional

# LangChain imports
try:
    from langchain_community.llms import LlamaCpp
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

# Try the new HuggingFace embeddings first, fallback to community version
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    HUGGINGFACE_NEW = True
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        HUGGINGFACE_NEW = False
    except ImportError:
        raise ImportError("Neither langchain-huggingface nor langchain-community.embeddings is available")
    
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# Local imports
from config import Config
from utils_pdf import format_source_with_pages
from utils import Logger, validate_file_exists

class SimpleLLM:
    """Simple LLM fallback implementation for when llama-cpp-python is not available"""
    
    def __init__(self, model_path=None, **kwargs):
        self.model_path = model_path
        Logger.warning("LlamaCpp non disponible. Utilisation d'un LLM de fallback simple.")
        Logger.info("Pour utiliser Mistral-7B, installez llama-cpp-python avec Visual Studio Build Tools.")
    
    def invoke(self, prompt: str) -> str:
        """Generate a simple response based on the prompt"""
        # Simple pattern matching for common questions
        if "règles" in prompt.lower() or "rule" in prompt.lower():
            return (
                "D'après les documents fournis, voici les principales règles identifiées. "
                "Je ne peux fournir qu'une réponse générale car le modèle LLM complet "
                "n'est pas disponible. Veuillez consulter les sources mentionnées pour "
                "plus de détails."
            )
        elif "comment" in prompt.lower() or "how" in prompt.lower():
            return (
                "Pour répondre à votre question sur le 'comment', je vous recommande "
                "de consulter les documents sources mentionnés. Le système fonctionne "
                "en mode limité car le modèle LLM principal n'est pas installé."
            )
        elif "qu'est-ce" in prompt.lower() or "what" in prompt.lower():
            return (
                "Basé sur les documents analysés, voici une réponse générale. "
                "Pour une analyse plus précise, veuillez installer llama-cpp-python "
                "avec les Build Tools Visual Studio."
            )
        else:
            return (
                "Je peux voir que vous avez posé une question sur les documents disponibles. "
                "Cependant, le modèle LLM complet n'est pas disponible. "
                "Les documents pertinents sont listés dans les sources ci-dessous. "
                "Pour obtenir des réponses détaillées, installez llama-cpp-python."
            )

class OllamaLLM:
    """LLM utilisant Ollama pour les modèles locaux"""
    
    def __init__(self, model_name="mistral:latest", host="http://localhost:11434", **kwargs):
        self.model_name = model_name
        self.host = host
        self.available = False
        try:
            import ollama
            self.client = ollama.Client(host=host)
            
            # Test de connexion simple
            try:
                # Test avec une requête simple
                test_response = self.client.generate(model=model_name, prompt="test", stream=False)
                if test_response:
                    Logger.success(f"Modèle Ollama trouvé et testé: {model_name}")
                    self.available = True
                    return
            except Exception as model_error:
                Logger.warning(f"Test du modèle {model_name} échoué: {model_error}")
            
            # Si le test direct échoue, essayer de lister les modèles
            try:
                models_response = self.client.list()
                available_models = []
                
                # Différentes façons de parser la réponse selon la version d'Ollama
                if hasattr(models_response, 'models'):
                    available_models = [model.model for model in models_response.models]
                elif isinstance(models_response, dict) and 'models' in models_response:
                    available_models = [model.get('name', model.get('model', '')) for model in models_response['models']]
                elif isinstance(models_response, list):
                    available_models = [model.get('name', model.get('model', '')) for model in models_response]
                
                available_models = [m for m in available_models if m]  # Filtrer les chaînes vides
                
                if available_models:
                    Logger.info(f"Modèles Ollama disponibles: {', '.join(available_models)}")
                    if model_name in available_models:
                        self.available = True
                        Logger.success(f"Modèle {model_name} trouvé dans la liste")
                    else:
                        # Utiliser le premier modèle disponible
                        self.model_name = available_models[0]
                        self.available = True
                        Logger.info(f"Utilisation du modèle: {self.model_name}")
                else:
                    Logger.warning("Aucun modèle Ollama trouvé")
                    
            except Exception as list_error:
                Logger.warning(f"Impossible de lister les modèles Ollama: {list_error}")
                
        except ImportError:
            Logger.error("Module 'ollama' non installé. Utilisez: pip install ollama")
            self.available = False
        except Exception as e:
            Logger.error(f"Erreur lors de l'initialisation d'Ollama: {e}")
            self.available = False
    
    def invoke(self, prompt: str) -> str:
        """Générer une réponse avec Ollama"""
        if not self.available:
            return "Erreur: Ollama n'est pas disponible"
        
        try:
            # Essayer d'abord avec generate (plus simple)
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={
                    'temperature': 0.1,
                    'top_p': 0.9,
                    'num_predict': 500
                }
            )
            
            if 'response' in response:
                return response['response']
            else:
                Logger.warning("Réponse Ollama inattendue, essai avec chat...")
                # Fallback vers chat
                chat_response = self.client.chat(
                    model=self.model_name,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    options={
                        'temperature': 0.1,
                        'top_p': 0.9,
                        'num_predict': 500
                    }
                )
                return chat_response['message']['content']
                
        except Exception as e:
            Logger.error(f"Erreur Ollama: {e}")
            return f"Erreur lors de la génération: {str(e)}"

class RAGPipeline:
    """Pipeline de Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.config = Config
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
    
    def _init_llm(self):
        """Initialiser le modèle LLM avec priorité: Ollama > Mistral-7B > Fallback"""
        
        # Tentative 1: Ollama (priorité)
        Logger.robot("Tentative d'initialisation avec Ollama...")
        ollama_llm = OllamaLLM(self.config.OLLAMA_MODEL, self.config.OLLAMA_HOST)
        if ollama_llm.available:
            self.llm = ollama_llm
            Logger.success("LLM Ollama initialisé avec succès")
            return
        
        # Tentative 2: Mistral-7B avec llama-cpp-python
        if LLAMA_CPP_AVAILABLE and validate_file_exists(self.config.MODEL_PATH):
            Logger.loading(f"Chargement du modèle LLM: {self.config.MODEL_PATH}")
            try:
                self.llm = LlamaCpp(
                    model_path=self.config.MODEL_PATH,
                    n_ctx=self.config.MODEL_N_CTX,
                    n_threads=self.config.MODEL_N_THREADS,
                    temperature=self.config.MODEL_TEMPERATURE,
                    max_tokens=self.config.MODEL_MAX_TOKENS,
                    verbose=False
                )
                print("✓ Modèle LLM Mistral-7B chargé")
                return
            except Exception as e:
                print(f"⚠️  Erreur chargement Mistral-7B: {e}")
        
        # Tentative 3: Fallback simple
        if not LLAMA_CPP_AVAILABLE:
            print("⚠️  llama-cpp-python non installé")
        elif not os.path.exists(self.config.MODEL_PATH):
            print(f"⚠️  Modèle non trouvé: {self.config.MODEL_PATH}")
        print("   Utilisation du LLM de fallback simple")
        self.llm = SimpleLLM()
    
    def _init_embeddings(self):
        """Initialiser le modèle d'embeddings"""
        print(f"Chargement des embeddings: {self.config.EMBEDDING_MODEL}")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✓ Embeddings chargés")
    
    def _load_vectorstore(self):
        """Charger l'index vectoriel FAISS"""
        vectorstore_path = os.path.join(self.config.VECTORSTORE_DIR, "faiss_index")
        
        if not os.path.exists(os.path.join(vectorstore_path, "index.faiss")):
            raise FileNotFoundError(
                f"Index vectoriel non trouvé: {vectorstore_path}\n"
                f"Veuillez d'abord exécuter l'ingestion: python src/ingest.py"
            )
        
        print(f"Chargement de l'index vectoriel: {vectorstore_path}")
        
        if not self.embeddings:
            self._init_embeddings()
        
        self.vectorstore = FAISS.load_local(
            vectorstore_path, 
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.config.RAG_TOP_K}
        )
        print("✓ Index vectoriel chargé")
    
    def _create_french_prompt(self) -> PromptTemplate:
        """Créer le template de prompt en français"""
        template = """Tu es un assistant IA spécialisé dans l'analyse de documents. 
Tu dois répondre UNIQUEMENT en français et être précis dans tes réponses.

INSTRUCTIONS IMPORTANTES:
1. Réponds TOUJOURS en français, même si la question est en anglais
2. Base tes réponses UNIQUEMENT sur le contexte fourni ci-dessous
3. Si l'information n'est pas dans le contexte, dis "Je ne trouve pas cette information dans les documents fournis. Excusez-moi."
4. Indique TOUJOURS les sources avec les numéros de page quand c'est possible
5. Sois concis mais complet dans tes réponses

CONTEXTE PRÉCÉDENT:
{chat_history}

CONTEXTE DOCUMENTAIRE:
{context}

QUESTION: {question}

RÉPONSE (en français uniquement):"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question", "chat_history"]
        )
    
    def _format_documents_with_sources(self, docs: List[Document]) -> Tuple[str, List[str]]:
        """Formater les documents avec leurs sources"""
        context_parts = []
        sources = []
        
        for i, doc in enumerate(docs, 1):
            # Formatage du contenu
            content = doc.page_content.strip()
            metadata = doc.metadata
            
            # Information de source avec pages
            source_info = format_source_with_pages(metadata)
            sources.append(source_info)
            
            # Ajouter au contexte
            context_parts.append(f"[Document {i}] {source_info}:\n{content}")
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    def initialize(self):
        """Initialiser tous les composants du pipeline"""
        try:
            # Initialiser les composants
            self._init_llm()
            self._load_vectorstore()
            
            print("✓ Pipeline RAG initialisé avec succès")
            
        except Exception as e:
            print(f"✗ Erreur lors de l'initialisation: {e}")
            raise
    
    def search_documents(self, query: str) -> List[Document]:
        """Rechercher des documents pertinents"""
        if not self.retriever:
            raise RuntimeError("Pipeline non initialisé. Appelez d'abord initialize()")
        
        # Recherche avec filtre de similarité
        docs = self.retriever.get_relevant_documents(query)
        
        # Filtrer par seuil de similarité si nécessaire
        # (Pour FAISS, on peut utiliser similarity_search_with_score)
        try:
            scored_docs = self.vectorstore.similarity_search_with_score(
                query, k=self.config.RAG_TOP_K
            )
            
            # Filtrer par seuil
            filtered_docs = [
                doc for doc, score in scored_docs 
                if score >= self.config.RAG_SIMILARITY_THRESHOLD
            ]
            
            return filtered_docs if filtered_docs else docs[:3]  # Au moins 3 docs
            
        except Exception:
            return docs
    
    def generate_response(self, query: str, chat_history: str = "") -> Tuple[str, List[str]]:
        """Générer une réponse avec RAG"""
        if not self.llm:
            raise RuntimeError("Pipeline non initialisé. Appelez d'abord initialize()")
        
        # Rechercher documents pertinents
        relevant_docs = self.search_documents(query)
        
        if not relevant_docs:
            return (
                "Je ne trouve pas d'informations pertinentes dans les documents fournis. "
                "Excusez-moi, pourriez-vous reformuler votre question ?",
                []
            )
        
        # Formater le contexte et extraire les sources
        context, sources = self._format_documents_with_sources(relevant_docs)
        
        # Créer le prompt
        prompt_template = self._create_french_prompt()
        prompt = prompt_template.format(
            context=context,
            question=query,
            chat_history=chat_history
        )
        
        # Générer la réponse
        try:
            response = self.llm.invoke(prompt)
            
            # Nettoyer la réponse
            if isinstance(response, str):
                response = response.strip()
            else:
                response = str(response).strip()
            
            # Ajouter les sources à la fin si elles ne sont pas déjà mentionnées
            if sources and not any(src.split()[0] in response for src in sources):
                sources_text = "\n\nSources: " + " | ".join(sources)
                response += sources_text
            
            return response, sources
            
        except Exception as e:
            print(f"Erreur lors de la génération: {e}")
            return (
                "Excusez-moi, une erreur s'est produite lors de la génération de la réponse. "
                "Veuillez réessayer.",
                sources
            )
    
    def get_vectorstore_info(self) -> Dict:
        """Obtenir des informations sur l'index vectoriel"""
        if not self.vectorstore:
            return {"error": "Index vectoriel non chargé"}
        
        try:
            # Obtenir le nombre de documents
            index_size = self.vectorstore.index.ntotal
            
            return {
                "index_size": index_size,
                "embedding_model": self.config.EMBEDDING_MODEL,
                "top_k": self.config.RAG_TOP_K,
                "similarity_threshold": self.config.RAG_SIMILARITY_THRESHOLD,
                "llm_type": "Mistral-7B" if LLAMA_CPP_AVAILABLE else "SimpleLLM (Fallback)"
            }
        except Exception as e:
            return {"error": f"Erreur lors de la récupération des infos: {e}"}

def test_pipeline():
    """Test basique du pipeline"""
    try:
        pipeline = RAGPipeline()
        pipeline.initialize()
        
        # Test avec une question simple
        test_query = "Quelles sont les règles principales ?"
        response, sources = pipeline.generate_response(test_query)
        
        print("=== Test du Pipeline RAG ===")
        print(f"Question: {test_query}")
        print(f"Réponse: {response}")
        print(f"Sources: {sources}")
        print("============================")
        
    except Exception as e:
        print(f"Erreur lors du test: {e}")

if __name__ == "__main__":
    test_pipeline()
