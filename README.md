# Application de Doublage Vidéo par IA

Une application complète pour automatiser le processus de doublage vidéo en utilisant l'intelligence artificielle.

## Fonctionnalités

- **Extraction audio** : Support des formats MP4, MKV, AVI
- **Détection d'activité vocale (VAD)** : Identification précise des segments de parole
- **Diarisation des locuteurs** : Identification automatique des différents locuteurs
- **OCR des sous-titres** : Extraction automatique des sous-titres incrustés
- **Transcription ASR** : Transcription audio avec horodatages précis
- **Alignement intelligent** : Synchronisation OCR/ASR avec correction d'erreurs
- **Clonage de voix** : Génération de nouvelles voix basées sur les échantillons originaux
- **Séparation de source** : Isolation optionnelle des dialogues, musique et effets
- **Export vidéo** : Génération de la vidéo finale avec audio doublé

## Architecture

Le système est organisé en modules :

```
ai_video_dubbing/
├── models/          # Modèles de données
├── gui/             # Interface graphique
├── pipeline/        # Orchestration du traitement
├── processors/      # Traitement vidéo/audio/IA
├── utils/           # Utilitaires (fichiers, stockage)
└── interfaces/      # Interfaces de base
```

## Installation

1. Cloner le repository
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Installer FFmpeg (requis pour le traitement vidéo)

## Utilisation

### Interface graphique
```bash
python main.py --gui
```

### Ligne de commande
```bash
python main.py --input video.mp4 --output dubbed_video.mp4
```

### Avec configuration personnalisée
```bash
python main.py --input video.mp4 --output dubbed_video.mp4 --config config/custom_config.json
```

## Configuration

Voir `config/default_config.json` pour les options disponibles :

- `enable_source_separation` : Activer la séparation de source
- `asr_model` : Modèle de reconnaissance vocale
- `ocr_model` : Modèle d'OCR
- `voice_cloning_model` : Modèle de clonage de voix
- `output_codec` : Codec de sortie vidéo
- `output_bitrate` : Débit de sortie
- `temp_directory` : Répertoire temporaire
- `max_memory_usage` : Utilisation mémoire maximale (0.0-1.0)

## Tests

```bash
pytest tests/
```

## Développement

Le projet suit une architecture modulaire avec des interfaces bien définies pour faciliter les tests et l'extensibilité.

### Structure des phases de traitement

1. **Phase d'Analyse** : Extraction audio, VAD, diarisation
2. **Phase d'Extraction** : OCR des sous-titres, transcription ASR, alignement
3. **Phase de Préparation** : Segmentation audio, création d'échantillons de référence
4. **Phase de Synthèse** : Clonage de voix, mixage, export final

## Licence

[À définir]