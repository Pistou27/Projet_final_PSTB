# Projet Final GenIA - Système RAG avec Qdrant et Mistral

Système de Retrieval-Augmented Generation (RAG) modulaire utilisant Qdrant comme base vectorielle, Mistral via Ollama, et une interface web moderne avec gestion de sessions.

## 🚀 Fonctionnalités

- **RAG Avancé** : Qdrant + BGE-M3 embeddings + reranking BGE
- **LLM** : Mistral via Ollama (API locale)
- **Interface Moderne** : Interface web responsive avec gestion de sessions
- **Mémoire Persistante** : SQLite pour l'historique des conversations
- **Architecture Modulaire** : Pipeline RAG séparé en modules spécialisés
- **Optimisé CPU** : Fonctionne entièrement sur CPU

## 🏗️ Architecture

### Backend
- **Pipeline RAG** : Module `rag_qdrant` avec composants séparés
- **Base Vectorielle** : Qdrant local pour stockage des embeddings
- **Embeddings** : BGE-M3 (1024 dimensions) via sentence-transformers
- **Reranking** : BGE-reranker-base pour améliorer la pertinence
- **LLM** : Mistral:latest via Ollama API
- **API** : Flask avec endpoints REST

### Frontend
- **Interface** : HTML/CSS/JavaScript responsive
- **Sessions** : Gestion complète des conversations
- **Sources** : Affichage expandable des documents sources
- **Documents** : Sidebar pour sélection de documents

## 📋 Prérequis

1. **Python 3.8+**
2. **Ollama** installé avec le modèle Mistral:
   ```bash
   ollama pull mistral:latest
   ```

## ⚙️ Installation

1. **Cloner le projet** :
```bash
git clone <repository-url>
cd Projet_Final_GenIA
```

2. **Créer l'environnement virtuel** :
```bash
python -m venv .venv
```

3. **Activer l'environnement** :
```bash
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

4. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

5. **Configuration** :
```bash
copy settings.example.env .env
# Ajuster les paramètres si nécessaire
```

## 🚀 Utilisation

### 1. Démarrer Ollama
```bash
ollama serve
```

### 2. Ajouter des documents
Placer vos documents PDF dans le dossier `data/`

### 3. Lancer l'application
```bash
cd src
python app.py
```

### 4. Accéder à l'interface
Ouvrir votre navigateur : http://127.0.0.1:5000

### 5. Première utilisation
1. Cliquer sur "📂 Indexer Documents" pour traiter vos documents
2. Utiliser l'interface de chat pour poser des questions
3. Les sessions sont automatiquement sauvegardées

## 📁 Structure du Projet

```
Projet_Final_GenIA/
├── src/                          # Code source
│   ├── app.py                   # Application Flask principale
│   ├── config.py                # Configuration centralisée
│   ├── memory_store.py          # Gestion mémoire SQLite
│   ├── incremental_ingest.py    # Ingestion incrémentale
│   ├── smart_embeddings.py      # Gestion embeddings
│   └── rag_qdrant/              # Pipeline RAG modulaire
│       ├── pipeline.py          # Pipeline principal
│       ├── qdrant_manager.py    # Gestionnaire Qdrant
│       ├── embedding_manager.py # Gestionnaire embeddings
│       ├── reranker_manager.py  # Gestionnaire reranking
│       ├── mistral_manager.py   # Gestionnaire Mistral
│       └── document_processor.py# Traitement documents
├── templates/                   # Templates HTML
│   └── chat.html               # Interface web principale
├── static/                      # Fichiers statiques
│   └── style.css               # Styles CSS
├── data/                        # Documents sources
├── vectorstore/                 # Base vectorielle Qdrant
├── memory/                      # Base SQLite mémoire
└── models/                      # Dossier pour modèles (optionnel)
```

## 🔧 Configuration

### Variables d'environnement (.env)
```env
# Répertoires
DATA_DIR=data
VECTORSTORE_DIR=vectorstore
MEMORY_DB_PATH=memory/memory.sqlite

# Modèle LLM
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=512

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## 🌐 API Endpoints

### Chat
- `POST /api/chat` - Envoyer un message
- `GET /api/sessions` - Lister les sessions
- `GET /api/sessions/<id>/history` - Historique d'une session
- `DELETE /api/sessions/<id>` - Supprimer une session

### Documents
- `POST /api/ingest` - Indexer les documents
- `GET /api/ingest/status` - Statut de l'indexation
- `POST /api/search` - Recherche dans les documents

### Système
- `GET /api/health` - Statut de l'API
- `GET /api/system/info` - Informations système

## ✨ Fonctionnalités Avancées

### Gestion des Sessions
- ✅ Création automatique de sessions
- ✅ Historique persistant des conversations
- ✅ Suppression individuelle ou en masse
- ✅ Chargement/sauvegarde automatique

### Interface Utilisateur
- ✅ Design responsive et moderne
- ✅ Sidebar sessions avec toggle
- ✅ Sidebar documents avec sélection
- ✅ Sources expandables avec contenu
- ✅ Indicateurs de statut en temps réel

### Pipeline RAG
- ✅ Embeddings BGE-M3 haute qualité
- ✅ Reranking pour améliorer la pertinence
- ✅ Ingestion incrémentale avec détection de changements
- ✅ Filtrage par document sélectionné
- ✅ Métadonnées riches (page, document, contenu)

## 🛠️ Développement

### Structure Modulaire
Le projet utilise une architecture modulaire avec :
- **Séparation des responsabilités** : Chaque composant a un rôle spécifique
- **Configuration centralisée** : Un seul point de configuration
- **Logging uniforme** : Système de log coloré et informatif
- **Gestion d'erreurs** : Gestion robuste des erreurs et fallbacks

### Tests
```bash
python -m pytest tests/
```

## 📚 Technologies Utilisées

- **Python 3.8+**
- **Flask** - Framework web
- **Qdrant** - Base vectorielle
- **BGE-M3** - Modèle d'embeddings
- **BGE-Reranker** - Reranking des résultats
- **Mistral** - Modèle de langage via Ollama
- **SQLite** - Base de données pour la mémoire
- **Sentence Transformers** - Génération d'embeddings
- **PyPDF2** - Traitement des PDFs

## 🔍 Troubleshooting

### Problèmes courants

1. **Ollama non disponible** :
   ```bash
   ollama serve
   ollama pull mistral:latest
   ```

2. **Erreur d'indexation** :
   - Vérifier que des PDFs sont dans `data/`
   - Vérifier les permissions de fichier

3. **Interface non accessible** :
   - Vérifier que Flask écoute sur le bon port
   - Vérifier les firewall/antivirus

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.
