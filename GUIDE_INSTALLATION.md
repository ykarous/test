# 📋 Guide d'Installation - Application de Doublage Vidéo par IA

## 🎯 Prérequis Système

### Configuration Minimale
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8 GB minimum, 16 GB recommandé
- **Stockage**: 10 GB d'espace libre
- **Processeur**: Intel i5 ou AMD Ryzen 5 (ou équivalent)

### Configuration Recommandée
- **OS**: Windows 11 (64-bit)
- **RAM**: 32 GB ou plus
- **Stockage**: 50 GB d'espace libre (SSD recommandé)
- **Processeur**: Intel i7/i9 ou AMD Ryzen 7/9
- **GPU**: NVIDIA RTX 3060 ou supérieur (pour accélération IA)

## 📦 Logiciels à Installer Manuellement

### 1. Python 3.9-3.11 ⭐ OBLIGATOIRE
```
📥 Téléchargement: https://python.org/downloads/
⚙️  Installation:
   ✅ Cocher "Add Python to PATH"
   ✅ Cocher "Install for all users"
   ✅ Installation personnalisée recommandée
```

### 2. Git (Optionnel mais recommandé)
```
📥 Téléchargement: https://git-scm.com/download/win
⚙️  Installation: Configuration par défaut
```

### 3. FFmpeg ⭐ OBLIGATOIRE
```
📥 Téléchargement: https://ffmpeg.org/download.html#build-windows
⚙️  Installation manuelle:
   1. Télécharger la version "release builds"
   2. Extraire dans C:\ffmpeg
   3. Ajouter C:\ffmpeg\bin au PATH système
   
🔄 Installation automatique (alternative):
   • Installer Chocolatey: https://chocolatey.org/install
   • Exécuter: choco install ffmpeg
```

### 4. Microsoft Visual C++ Redistributable
```
📥 Téléchargement: https://aka.ms/vs/17/release/vc_redist.x64.exe
⚙️  Installation: Exécuter le fichier téléchargé
```

## 🚀 Installation Automatique

### Étape 1: Télécharger l'Application
```bash
# Option A: Avec Git
git clone [URL_DU_REPOSITORY]
cd ai-video-dubbing

# Option B: Téléchargement ZIP
# Extraire le ZIP dans un dossier de votre choix
```

### Étape 2: Installation des Dépendances
```batch
# Exécuter l'installateur automatique
install_dependencies.bat
```

### Étape 3: Test de l'Installation
```batch
# Vérifier que tout fonctionne
test_installation.bat
```

### Étape 4: Démarrage de l'Application
```batch
# Lancer l'application
start_application.bat
```

## 📋 Liste Complète des Dépendances

### Dépendances Python Critiques
```
Interface Graphique:
├── PyQt5 >= 5.15.0          # Interface utilisateur
├── PyQt5-Qt5 >= 5.15.0      # Composants Qt
└── PyQt5-sip >= 12.8.0      # Bindings Python-Qt

Traitement Audio/Vidéo:
├── opencv-python >= 4.8.0   # Traitement vidéo
├── librosa >= 0.10.0        # Analyse audio
├── soundfile >= 0.12.0      # Lecture/écriture audio
├── pydub >= 0.25.0          # Manipulation audio
└── moviepy >= 1.0.3         # Édition vidéo

Intelligence Artificielle:
├── torch >= 2.0.0           # Framework IA principal
├── torchaudio >= 2.0.0      # IA audio
├── torchvision >= 0.15.0    # IA vision
├── transformers >= 4.30.0   # Modèles de langage
├── openai-whisper >= 20231117 # Transcription
└── sentence-transformers >= 2.2.0 # Embeddings

OCR (Reconnaissance de Texte):
├── paddleocr >= 2.7.0       # OCR principal
├── easyocr >= 1.7.0         # OCR alternatif
└── Pillow >= 10.0.0         # Traitement d'images

Utilitaires:
├── numpy >= 1.24.0          # Calculs numériques
├── pandas >= 2.0.0          # Manipulation de données
├── scipy >= 1.10.0          # Calculs scientifiques
├── psutil >= 5.9.0          # Informations système
├── requests >= 2.31.0       # Requêtes HTTP
└── tqdm >= 4.65.0           # Barres de progression
```

### Dépendances Optionnelles
```
NVIDIA NeMo:
└── nemo-toolkit >= 1.20.0   # IA avancée (très volumineux)

Accélération GPU:
└── nvidia-ml-py >= 12.0.0   # Monitoring GPU

Développement:
├── pytest >= 7.4.0          # Tests
└── pytest-cov >= 4.1.0      # Couverture de tests
```

### Logiciels Externes Optionnels
```
LM Studio:
├── 📥 https://lmstudio.ai
├── 💾 ~2-10 GB par modèle
└── 🎯 Modèles multimodaux pour OCR avancé

CUDA Toolkit (pour GPU NVIDIA):
├── 📥 https://developer.nvidia.com/cuda-downloads
├── 💾 ~3 GB
└── 🎯 Accélération GPU pour l'IA
```

## 🔧 Configuration Post-Installation

### 1. Variables d'Environnement
```batch
# Ajouter au PATH système:
C:\Python311\Scripts
C:\ffmpeg\bin

# Variables optionnelles:
CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0
```

### 2. Configuration GPU (Optionnel)
```python
# Vérifier le support CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Si CUDA non détecté, réinstaller PyTorch:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. Configuration LM Studio (Optionnel)
```
1. Installer LM Studio
2. Télécharger un modèle multimodal:
   • LLaVA 1.6 (recommandé)
   • Qwen-VL
   • CogVLM
3. Démarrer le serveur local (port 1234)
```

## 🚨 Résolution de Problèmes

### Erreurs Communes

#### "Python n'est pas reconnu"
```
Solution:
1. Réinstaller Python avec "Add to PATH"
2. Ou ajouter manuellement au PATH:
   C:\Python311
   C:\Python311\Scripts
```

#### "FFmpeg n'est pas reconnu"
```
Solution:
1. Télécharger FFmpeg
2. Extraire dans C:\ffmpeg
3. Ajouter C:\ffmpeg\bin au PATH
4. Redémarrer l'invite de commande
```

#### "Erreur d'importation PyQt5"
```
Solution:
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5 PyQt5-Qt5 PyQt5-sip
```

#### "CUDA non disponible"
```
Solution (optionnel):
1. Installer CUDA Toolkit
2. Réinstaller PyTorch avec support CUDA:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### "Erreur de mémoire"
```
Solution:
1. Fermer les applications inutiles
2. Utiliser des modèles plus petits
3. Augmenter la mémoire virtuelle Windows
```

### Logs et Diagnostic
```
📁 Logs de l'application: ./logs/
📁 Logs d'installation: Affichés dans la console
🔧 Test complet: test_installation.bat
```

## 📞 Support

### Vérifications Avant Support
1. ✅ Exécuter `test_installation.bat`
2. ✅ Vérifier les logs dans `./logs/`
3. ✅ Tester avec `python main.py` directement
4. ✅ Vérifier l'espace disque disponible

### Informations à Fournir
- Version de Windows
- Version de Python (`python --version`)
- Résultat de `test_installation.bat`
- Messages d'erreur complets
- Configuration matérielle (RAM, GPU)

## 🎉 Utilisation

Une fois l'installation terminée:

1. **Démarrage Normal**: `start_application.bat`
2. **Démarrage Direct**: `python main.py`
3. **Test Rapide**: `test_installation.bat`

L'application devrait se lancer avec une interface graphique complète et toutes les fonctionnalités d'IA disponibles selon votre configuration matérielle.