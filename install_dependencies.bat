@echo off
chcp 65001 >nul
echo ========================================
echo   INSTALLATEUR - DOUBLAGE VIDÉO IA
echo ========================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo 💡 Téléchargez Python depuis https://python.org
    echo    Assurez-vous de cocher "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python détecté
python --version

:: Vérifier la version de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Version Python: %PYTHON_VERSION%

:: Mettre à jour pip
echo.
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip

:: Installer les dépendances de base
echo.
echo 🔧 Installation des dépendances principales...
python -m pip install -r requirements.txt

:: Vérifier si CUDA est disponible pour PyTorch
echo.
echo 🔍 Vérification du support GPU...
python -c "import torch; print('✅ PyTorch installé'); print('🎮 CUDA disponible:', torch.cuda.is_available())" 2>nul
if errorlevel 1 (
    echo ⚠️  Problème avec PyTorch, tentative de réinstallation...
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

:: Installer FFmpeg (nécessaire pour le traitement audio/vidéo)
echo.
echo 🎬 Vérification de FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg non détecté
    echo 💡 Installation recommandée:
    echo    1. Téléchargez FFmpeg depuis https://ffmpeg.org/download.html
    echo    2. Extrayez dans C:\ffmpeg
    echo    3. Ajoutez C:\ffmpeg\bin au PATH système
    echo.
    echo 🔄 Tentative d'installation automatique via chocolatey...
    choco install ffmpeg -y >nul 2>&1
    if errorlevel 1 (
        echo ❌ Installation automatique échouée
        echo 📋 Installation manuelle requise
    ) else (
        echo ✅ FFmpeg installé via Chocolatey
    )
) else (
    echo ✅ FFmpeg détecté
)

:: Créer les répertoires nécessaires
echo.
echo 📁 Création des répertoires...
if not exist "models" mkdir models
if not exist "cache" mkdir cache
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
echo ✅ Répertoires créés

:: Test des imports principaux
echo.
echo 🧪 Test des dépendances critiques...

python -c "
import sys
import traceback

dependencies = [
    ('PyQt5', 'Interface graphique'),
    ('cv2', 'Traitement vidéo (OpenCV)'),
    ('librosa', 'Traitement audio'),
    ('torch', 'PyTorch (IA)'),
    ('transformers', 'Transformers (IA)'),
    ('whisper', 'Whisper (Transcription)'),
    ('requests', 'Requêtes HTTP'),
    ('numpy', 'Calculs numériques'),
    ('PIL', 'Traitement d\'images')
]

failed = []
for module, description in dependencies:
    try:
        __import__(module)
        print(f'✅ {module} - {description}')
    except ImportError as e:
        print(f'❌ {module} - {description} - ÉCHEC')
        failed.append(module)

if failed:
    print(f'\n⚠️  {len(failed)} dépendance(s) manquante(s): {', '.join(failed)}')
    sys.exit(1)
else:
    print(f'\n🎉 Toutes les dépendances critiques sont installées!')
"

if errorlevel 1 (
    echo.
    echo ❌ Certaines dépendances critiques sont manquantes
    echo 🔧 Tentative de réparation...
    
    :: Réinstaller les packages problématiques
    python -m pip install --force-reinstall PyQt5 opencv-python librosa torch transformers openai-whisper
    
    echo.
    echo 🔄 Nouveau test après réparation...
    python -c "
import sys
try:
    import PyQt5, cv2, librosa, torch, transformers, whisper
    print('✅ Réparation réussie!')
except ImportError as e:
    print('❌ Problèmes persistants:', str(e))
    sys.exit(1)
"
)

:: Installation optionnelle de NVIDIA NeMo
echo.
echo 🤖 Installation optionnelle de NVIDIA NeMo...
set /p INSTALL_NEMO="Installer NVIDIA NeMo? (y/N): "
if /i "%INSTALL_NEMO%"=="y" (
    echo 📦 Installation de NeMo (peut prendre plusieurs minutes)...
    python -m pip install nemo-toolkit[all]
    if errorlevel 1 (
        echo ⚠️  Installation NeMo échouée, continuons sans NeMo
    ) else (
        echo ✅ NVIDIA NeMo installé avec succès
    )
) else (
    echo ⏭️  NeMo ignoré (installation optionnelle)
)

:: Vérification finale
echo.
echo 🏁 VÉRIFICATION FINALE
echo ========================================

python -c "
print('🐍 Python:', end=' ')
import sys
print(f'{sys.version.split()[0]}')

print('🎮 GPU Support:', end=' ')
try:
    import torch
    if torch.cuda.is_available():
        print(f'✅ CUDA {torch.version.cuda}')
        print(f'   GPU: {torch.cuda.get_device_name(0)}')
    else:
        print('❌ CPU seulement')
except:
    print('❌ PyTorch non disponible')

print('🎬 FFmpeg:', end=' ')
import subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f'✅ {version_line.split()[2]}')
    else:
        print('❌ Non détecté')
except:
    print('❌ Non disponible')

print('📦 Packages installés:', end=' ')
import pkg_resources
installed = [pkg.project_name for pkg in pkg_resources.working_set]
critical = ['PyQt5', 'opencv-python', 'librosa', 'torch', 'transformers', 'openai-whisper']
missing = [pkg for pkg in critical if not any(pkg.lower() in inst.lower() for inst in installed)]
if missing:
    print(f'❌ Manquants: {missing}')
else:
    print('✅ Tous les packages critiques présents')
"

echo.
echo ========================================
echo 🎉 INSTALLATION TERMINÉE!
echo ========================================
echo.
echo 💡 Prochaines étapes:
echo    1. Lancez l'application avec: start_application.bat
echo    2. Ou directement: python main.py
echo.
echo 📋 Optionnel - Installez manuellement:
echo    • LM Studio (https://lmstudio.ai) pour modèles locaux
echo    • NVIDIA NeMo si pas installé automatiquement
echo    • FFmpeg si la détection a échoué
echo.
pause