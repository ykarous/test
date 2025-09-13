@echo off
chcp 65001 >nul
echo ========================================
echo   DÉSINSTALLATION - DOUBLAGE VIDÉO IA
echo ========================================
echo.

echo ⚠️  ATTENTION: Cette opération va supprimer:
echo    • Tous les packages Python installés pour cette app
echo    • Les modèles téléchargés
echo    • Les fichiers de cache
echo    • Les logs et fichiers temporaires
echo.

set /p CONFIRM="Êtes-vous sûr de vouloir continuer? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo ❌ Désinstallation annulée
    pause
    exit /b 0
)

echo.
echo 🗑️  Désinstallation en cours...

:: Désinstaller les packages Python
echo.
echo 📦 Désinstallation des packages Python...
python -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip
python -m pip uninstall -y opencv-python librosa soundfile pydub moviepy
python -m pip uninstall -y torch torchaudio torchvision transformers openai-whisper
python -m pip uninstall -y paddleocr easyocr Pillow
python -m pip uninstall -y numpy pandas scipy psutil requests tqdm
python -m pip uninstall -y nemo-toolkit
python -m pip uninstall -y pytest pytest-cov

:: Supprimer les répertoires de l'application
echo.
echo 📁 Suppression des répertoires...
if exist "models" (
    echo Suppression du dossier models...
    rmdir /s /q "models"
)
if exist "cache" (
    echo Suppression du dossier cache...
    rmdir /s /q "cache"
)
if exist "temp" (
    echo Suppression du dossier temp...
    rmdir /s /q "temp"
)
if exist "logs" (
    echo Suppression du dossier logs...
    rmdir /s /q "logs"
)
if exist "output" (
    echo Suppression du dossier output...
    rmdir /s /q "output"
)

:: Nettoyer le cache pip
echo.
echo 🧹 Nettoyage du cache pip...
python -m pip cache purge

echo.
echo ========================================
echo ✅ DÉSINSTALLATION TERMINÉE
echo ========================================
echo.
echo 📋 Éléments conservés (à supprimer manuellement si souhaité):
echo    • Python (installation système)
echo    • FFmpeg (installation système)
echo    • LM Studio (application séparée)
echo    • Fichiers sources de l'application
echo.
echo 💡 Pour une suppression complète:
echo    1. Désinstallez Python depuis "Programmes et fonctionnalités"
echo    2. Supprimez FFmpeg du PATH et du disque
echo    3. Désinstallez LM Studio
echo    4. Supprimez ce dossier manuellement
echo.
pause