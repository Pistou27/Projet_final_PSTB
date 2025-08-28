# Instructions pour télécharger le modèle Mistral-7B GGUF

Vous devez télécharger le modèle Mistral-7B au format GGUF pour faire fonctionner ce système.

## Option 1: Téléchargement direct depuis Hugging Face

1. Aller sur: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF
2. Télécharger le fichier: `mistral-7b-instruct-v0.1.Q4_K_M.gguf` (environ 4.1 GB)
3. Renommer le fichier en: `mistral-7b-instruct.Q4_K_M.gguf`
4. Placer le fichier dans le dossier `models/`

## Option 2: Utilisation de git-lfs (si installé)

```bash
cd models
git lfs install
git clone https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF
mv "Mistral-7B-Instruct-v0.1-GGUF/mistral-7b-instruct-v0.1.Q4_K_M.gguf" "mistral-7b-instruct.Q4_K_M.gguf"
rm -rf Mistral-7B-Instruct-v0.1-GGUF
```

## Option 3: Utilisation de wget (Linux/Mac)

```bash
cd models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
mv mistral-7b-instruct-v0.1.Q4_K_M.gguf mistral-7b-instruct.Q4_K_M.gguf
```

## Vérification

Le fichier final doit être:
- Nom: `mistral-7b-instruct.Q4_K_M.gguf`
- Emplacement: `models/mistral-7b-instruct.Q4_K_M.gguf`
- Taille: environ 4.1 GB

Une fois le modèle téléchargé, vous pouvez procéder à l'installation et au lancement du système.
