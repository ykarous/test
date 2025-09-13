# Configuration FFmpeg - AI Video Dubbing

## 🎯 Objectif

Ce système permet de configurer FFmpeg directement depuis l'interface graphique de l'application, sans avoir besoin de modifier le PATH système.

## ✨ Fonctionnalités

### 🔍 Détection Automatique
- Recherche FFmpeg dans le PATH système
- Scan des emplacements courants selon l'OS
- Validation automatique du fonctionnement

### 📁 Sélection Manuelle
- Interface graphique pour sélectionner l'exécutable FFmpeg
- Validation automatique du fichier sélectionné
- Détection automatique de FFprobe dans le même répertoire

### 💾 Sauvegarde Configuration
- Configuration sauvegardée automatiquement
- Rechargement au démarrage de l'application
- Possibilité de réinitialiser

### 🧪 Test Intégré
- Test de fonctionnement de FFmpeg
- Affichage de la version
- Vérification des capacités

## 🚀 Utilisation

### 1. Lancement du Test
```bash
python test_ffmpeg_config.py
```

### 2. Démonstration Complète
```bash
python demo_ffmpeg_integration.py
```

### 3. Intégration dans l'Application
```python
from ai_video_dubbing.gui.ffmpeg_config_widget import FFmpegConfigWidget
from ai_video_dubbing.utils.ffmpeg_manager import FFmpegManager

# Créer le gestionnaire FFmpeg
ffmpeg_manager = FFmpegManager()

# Vérifier la disponibilité
if ffmpeg_manager.is_available():
    print("FFmpeg disponible!")
else:
    print("FFmpeg non configuré")

# Utiliser dans l'interface
config_widget = FFmpegConfigWidget()
config_widget.show()
```

## 📋 Emplacements de Recherche

### Windows
- `C:/ffmpeg/bin`
- `C:/Program Files/ffmpeg/bin`
- `C:/Program Files (x86)/ffmpeg/bin`
- `~/ffmpeg/bin`
- `~/Downloads/ffmpeg/bin`
- `C:/ProgramData/chocolatey/bin` (Chocolatey)

### macOS
- `/usr/local/bin` (Homebrew)
- `/opt/homebrew/bin`
- `/usr/bin`
- `~/bin`

### Linux
- `/usr/bin`
- `/usr/local/bin`
- `/opt/ffmpeg/bin`
- `~/.local/bin`

## 🔧 API du Gestionnaire FFmpeg

### FFmpegManager

```python
# Initialisation
manager = FFmpegManager()

# Détection automatique
success = manager.auto_detect_ffmpeg()

# Sélection manuelle (avec interface graphique)
success = manager.select_ffmpeg_manually(parent_widget)

# Vérification disponibilité
available = manager.is_available()

# Obtenir les chemins
ffmpeg_path = manager.get_ffmpeg_path()
ffprobe_path = manager.get_ffprobe_path()

# Obtenir la version
version = manager.get_version()

# Exécuter des commandes
result = manager.run_ffmpeg_command(['-i', 'input.mp4', 'output.wav'])
result = manager.run_ffprobe_command(['-v', 'quiet', '-print_format', 'json', 'input.mp4'])

# Réinitialiser
manager.reset_configuration()
```

### MediaUtils

```python
# Initialisation
media_utils = MediaUtils(ffmpeg_manager)

# Extraire audio
success = media_utils.extract_audio('video.mp4', 'audio.wav')

# Obtenir informations vidéo
info = media_utils.get_video_info('video.mp4')

# Extraire des frames
frames = media_utils.extract_frames('video.mp4', 'frames_dir/', fps=1.0)

# Convertir format audio
success = media_utils.convert_audio_format('input.mp3', 'output.wav')

# Fusionner audio/vidéo
success = media_utils.merge_audio_video('video.mp4', 'audio.wav', 'output.mp4')
```

## 🎨 Interface Graphique

### Widget de Configuration
- **Statut en temps réel** : Affichage de l'état de FFmpeg
- **Boutons d'action** : Détection auto, sélection manuelle, test
- **Informations détaillées** : Version, chemin, statut
- **Instructions d'aide** : Guide d'installation et d'utilisation

### Intégration dans l'Application
- **Onglet FFmpeg** dans le panneau de configuration
- **Signal de configuration** émis lors des changements
- **Sauvegarde automatique** des paramètres

## 📥 Installation FFmpeg

### Windows
1. Téléchargez depuis [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Extrayez dans `C:\ffmpeg`
3. Utilisez le bouton "Sélectionner FFmpeg" pour pointer vers `C:\ffmpeg\bin\ffmpeg.exe`

### macOS
```bash
# Avec Homebrew
brew install ffmpeg

# Ou téléchargez depuis le site officiel
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

## 🔒 Sécurité

- **Validation des exécutables** : Vérification que le fichier sélectionné est bien FFmpeg
- **Test de fonctionnement** : Validation avant sauvegarde
- **Gestion des erreurs** : Messages d'erreur explicites
- **Timeout** : Protection contre les blocages

## 🐛 Dépannage

### FFmpeg non détecté
1. Vérifiez que FFmpeg est installé
2. Utilisez la sélection manuelle
3. Vérifiez les permissions d'exécution

### Erreur de validation
1. Assurez-vous que le fichier sélectionné est l'exécutable FFmpeg
2. Vérifiez que FFmpeg fonctionne en ligne de commande
3. Réinstallez FFmpeg si nécessaire

### Configuration perdue
1. Utilisez "Réinitialiser" puis reconfigurez
2. Vérifiez les permissions d'écriture
3. Relancez l'application

## 📝 Logs

Les logs de FFmpeg sont disponibles dans :
- **Console de l'application** pour les opérations courantes
- **Fichiers de log** pour le débogage avancé
- **Messages d'erreur** dans l'interface graphique

## 🔄 Mise à Jour

Pour mettre à jour FFmpeg :
1. Téléchargez la nouvelle version
2. Remplacez l'ancienne installation
3. Testez avec le bouton "Tester" dans l'interface
4. Reconfigurez si nécessaire avec "Sélectionner FFmpeg"