@echo off
chcp 65001 >nul
title Application de Doublage Vidéo par IA

echo ========================================
echo   DOUBLAGE VIDÉO PAR IA - DÉMARRAGE
echo ========================================
echo.

:: Vérifier si Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non détecté
    echo 💡 Exécutez d'abord: install_dependencies.bat
    pause
    exit /b 1
)

:: Vérifier les dépendances critiques
echo 🔍 Vérification des dépendances...
python -c "
import sys
try:
    import PyQt5
    print('✅ Interface graphique (PyQt5)')
except ImportError:
    print('❌ PyQt5 manquant')
    sys.exit(1)

try:
    import cv2
    print('✅ Traitement vidéo (OpenCV)')
except ImportError:
    print('❌ OpenCV manquant')
    sys.exit(1)

try:
    import librosa
    print('✅ Traitement audio (Librosa)')
except ImportError:
    print('❌ Librosa manquant')
    sys.exit(1)

try:
    import torch
    print('✅ Intelligence artificielle (PyTorch)')
    if torch.cuda.is_available():
        print('  🎮 Accélération GPU disponible')
    else:
        print('  🖥️  Mode CPU seulement')
except ImportError:
    print('❌ PyTorch manquant')
    sys.exit(1)
"

if errorlevel 1 (
    echo.
    echo ❌ Dépendances manquantes détectées
    echo 🔧 Exécutez: install_dependencies.bat
    pause
    exit /b 1
)

:: Créer les répertoires si nécessaire
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "output" mkdir output

:: Définir les variables d'environnement
set PYTHONPATH=%CD%;%PYTHONPATH%
set AI_VIDEO_DUBBING_LOG_LEVEL=INFO

:: Vérifier les services optionnels
echo.
echo 🔍 Vérification des services optionnels...

:: LM Studio
python -c "
import requests
try:
    response = requests.get('http://localhost:1234/v1/models', timeout=2)
    if response.status_code == 200:
        print('✅ LM Studio connecté (localhost:1234)')
    else:
        print('⚠️  LM Studio détecté mais non fonctionnel')
except:
    print('⚪ LM Studio non détecté (optionnel)')
" 2>nul

:: NVIDIA NeMo
python -c "
try:
    import nemo
    print('✅ NVIDIA NeMo disponible')
except ImportError:
    print('⚪ NVIDIA NeMo non installé (optionnel)')
" 2>nul

:: FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg non détecté - fonctionnalités limitées
) else (
    echo ✅ FFmpeg disponible
)

echo.
echo 🚀 Démarrage de l'application...
echo ========================================

:: Démarrer l'application avec gestion d'erreur
python main.py
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
if %EXIT_CODE% equ 0 (
    echo ✅ Application fermée normalement
) else (
    echo ❌ Application fermée avec erreur (code: %EXIT_CODE%)
    echo.
    echo 📋 Vérifiez les logs dans le dossier 'logs'
    echo 🔧 Si le problème persiste:
    echo    1. Réexécutez install_dependencies.bat
    echo    2. Vérifiez que tous les fichiers sont présents
    echo    3. Consultez la documentation
)

echo.
pause