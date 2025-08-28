# Projet Final GenIA - Système RAG avec LLM CPU

Système de Retrieval-Augmented Generation (RAG) utilisant Mistral-7B en mode CPU avec mémoire conversationnelle et interface web Flask.

## Architecture

- **LLM**: Mistral-7B (GGUF via llama-cpp-python)
- **RAG**: FAISS + HuggingFace embeddings (all-MiniLM-L6-v2)
- **Orchestration**: LangChain 0.2+
- **Frontend**: Flask (interface simple + endpoint /api/chat)
- **Mémoire**: SQLite pour la persistance des conversations
- **Optimisé**: CPU uniquement

## Installation

1. Créer l'environnement virtuel:
```bash
python3 -m venv venv
```

2. Activer l'environnement:
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Copier la configuration:
```bash
copy settings.example.env .env
```

5. Télécharger le modèle Mistral-7B GGUF et le placer dans `models/`:
   - Nom attendu: `mistral-7b-instruct.Q4_K_M.gguf`

## Utilisation

1. **Ingestion des documents** (première fois):
```bash
python src/ingest.py
```

2. **Démarrer le serveur Flask**:
```bash
python src/app.py
```

3. Accéder à l'interface: http://127.0.0.1:5000

## Structure des répertoires

- `data/`: Documents sources (PDF, TXT, DOCX, CSV)
- `models/`: Modèle GGUF Mistral-7B
- `memory/`: Base de données SQLite pour la mémoire
- `vectorstore/`: Index FAISS persistant
- `src/`: Code source Python
- `static/` & `templates/`: Interface web

## Fonctionnalités

- ✅ RAG avec recherche sémantique
- ✅ Mémoire conversationnelle persistante
- ✅ Réponses en français
- ✅ Indication des pages sources pour les PDFs
- ✅ Interface web simple et efficace
- ✅ Optimisé pour CPU uniquement
