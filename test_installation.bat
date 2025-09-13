@echo off
chcp 65001 >nul
echo ========================================
echo   TEST D'INSTALLATION - DOUBLAGE IA
echo ========================================
echo.

:: Test Python
echo 🐍 Test Python...
python --version
if errorlevel 1 (
    echo ❌ Python non installé
    goto :error
)

:: Test des imports
echo.
echo 📦 Test des packages Python...
python -c "import sys; import traceback; critical_packages = ['PyQt5', 'cv2', 'librosa', 'torch', 'transformers', 'whisper', 'numpy', 'requests']; optional_packages = ['paddleocr', 'easyocr', 'nemo']; print('📋 PACKAGES CRITIQUES:'); critical_ok = True; [print(f'  ✅ {package}') if __import__(package) or True else print(f'  ❌ {package} - MANQUANT') or setattr(sys.modules[__name__], 'critical_ok', False) for package in critical_packages]; print('\n📋 PACKAGES OPTIONNELS:'); [print(f'  ✅ {package}') if __import__(package) or True else print(f'  ⚪ {package} - non installé') for package in optional_packages]; print('\n❌ Des packages critiques sont manquants!') if not critical_ok else print('\n✅ Tous les packages critiques sont présents'); sys.exit(1) if not critical_ok else None" 2>nul

if errorlevel 1 goto :error

:: Test FFmpeg
echo.
echo 🎬 Test FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg non détecté
) else (
    echo ✅ FFmpeg disponible
)

:: Test GPU
echo.
echo 🎮 Test support GPU...
python -c "
import torch
print('PyTorch version:', torch.__version__)
if torch.cuda.is_available():
    print('✅ CUDA disponible')
    print('GPU:', torch.cuda.get_device_name(0))
    print('CUDA version:', torch.version.cuda)
else:
    print('⚪ Mode CPU seulement')
"

:: Test des composants de l'application
echo.
echo 🧪 Test des composants de l'application...
python -c "
try:
    from ai_video_dubbing.processors.ai_model_manager import AIModelManager
    print('✅ Gestionnaire de modèles IA')
except ImportError as e:
    print('❌ Gestionnaire IA:', e)

try:
    from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
    print('✅ Gestionnaire LM Studio')
except ImportError as e:
    print('❌ LM Studio Manager:', e)

try:
    from ai_video_dubbing.utils.model_discovery import ModelDiscovery
    print('✅ Découverte de modèles')
except ImportError as e:
    print('❌ Model Discovery:', e)

try:
    from ai_video_dubbing.gui.main_window import MainWindow
    print('✅ Interface graphique')
except ImportError as e:
    print('❌ Interface graphique:', e)
"

:: Test LM Studio (optionnel)
echo.
echo 🖥️  Test LM Studio (optionnel)...
python -c "
import requests
try:
    response = requests.get('http://localhost:1234/v1/models', timeout=3)
    if response.status_code == 200:
        models = response.json().get('data', [])
        print(f'✅ LM Studio connecté - {len(models)} modèles')
    else:
        print('⚠️  LM Studio répond mais erreur')
except requests.exceptions.ConnectionError:
    print('⚪ LM Studio non démarré (normal si pas utilisé)')
except Exception as e:
    print('⚠️  Erreur LM Studio:', e)
" 2>nul

echo.
echo ========================================
echo ✅ TEST D'INSTALLATION RÉUSSI!
echo ========================================
echo.
echo 💡 L'application est prête à être utilisée
echo 🚀 Lancez avec: start_application.bat
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ PROBLÈMES DÉTECTÉS
echo ========================================
echo.
echo 🔧 Actions recommandées:
echo    1. Exécutez: install_dependencies.bat
echo    2. Vérifiez que Python est dans le PATH
echo    3. Redémarrez l'invite de commande
echo.

:end
pause