@echo off
chcp 65001 >nul
echo ========================================
echo   MISE À JOUR - DOUBLAGE VIDÉO IA
echo ========================================
echo.

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non détecté
    echo 💡 Exécutez d'abord: install_dependencies.bat
    pause
    exit /b 1
)

echo ✅ Python détecté
python --version

:: Mettre à jour pip
echo.
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip

:: Mettre à jour les packages principaux
echo.
echo 🔄 Mise à jour des packages principaux...
python -m pip install --upgrade -r requirements.txt

:: Mise à jour spécifique de PyTorch (important pour compatibilité)
echo.
echo 🧠 Mise à jour de PyTorch...
python -c "
import torch
print('Version actuelle de PyTorch:', torch.__version__)
"

set /p UPDATE_TORCH="Mettre à jour PyTorch? (y/N): "
if /i "%UPDATE_TORCH%"=="y" (
    echo 🔄 Mise à jour de PyTorch...
    python -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
)

:: Mise à jour optionnelle de NeMo
echo.
python -c "
try:
    import nemo
    print('✅ NeMo détecté, version:', nemo.__version__)
    update_nemo = True
except ImportError:
    print('⚪ NeMo non installé')
    update_nemo = False
" > temp_nemo_check.txt

findstr "NeMo détecté" temp_nemo_check.txt >nul
if not errorlevel 1 (
    set /p UPDATE_NEMO="Mettre à jour NeMo? (y/N): "
    if /i "!UPDATE_NEMO!"=="y" (
        echo 🤖 Mise à jour de NeMo...
        python -m pip install --upgrade nemo-toolkit[all]
    )
)
del temp_nemo_check.txt 2>nul

:: Nettoyer les packages obsolètes
echo.
echo 🧹 Nettoyage des packages obsolètes...
python -m pip list --outdated

set /p CLEAN_OLD="Nettoyer les packages obsolètes? (y/N): "
if /i "%CLEAN_OLD%"=="y" (
    echo 🗑️  Nettoyage en cours...
    python -m pip install --upgrade pip-autoremove
    pip-autoremove -y
)

:: Vérification post-mise à jour
echo.
echo 🧪 Vérification post-mise à jour...
python -c "
import sys
packages = ['PyQt5', 'cv2', 'librosa', 'torch', 'transformers', 'whisper']
failed = []

for package in packages:
    try:
        module = __import__(package)
        if hasattr(module, '__version__'):
            version = module.__version__
        else:
            version = 'N/A'
        print(f'✅ {package}: {version}')
    except ImportError:
        print(f'❌ {package}: MANQUANT')
        failed.append(package)

if failed:
    print(f'\n⚠️  Packages manquants après mise à jour: {failed}')
    print('🔧 Réexécutez install_dependencies.bat')
    sys.exit(1)
else:
    print('\n✅ Tous les packages critiques sont à jour')
"

if errorlevel 1 (
    echo.
    echo ❌ Problèmes détectés après mise à jour
    echo 🔧 Réinstallation recommandée: install_dependencies.bat
    pause
    exit /b 1
)

:: Test rapide de l'application
echo.
echo 🚀 Test rapide de l'application...
python -c "
try:
    from ai_video_dubbing.processors.ai_model_manager import AIModelManager
    print('✅ Composants principaux fonctionnels')
except Exception as e:
    print('❌ Erreur dans les composants:', e)
"

echo.
echo ========================================
echo ✅ MISE À JOUR TERMINÉE!
echo ========================================
echo.
echo 💡 Changements appliqués:
echo    • Packages Python mis à jour
echo    • Compatibilité vérifiée
echo    • Composants testés
echo.
echo 🚀 Testez l'application avec: start_application.bat
echo.
pause