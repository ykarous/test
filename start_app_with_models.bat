@echo off
echo ========================================
echo    APPLICATION AVEC TELECHARGEUR NEMO
echo ========================================
echo.

echo Activation environnement...
call mon_env\Scripts\activate

echo.
echo ========================================
echo LANCEMENT APPLICATION COMPLETE
echo - Interface de telechargement des modeles
echo - Gestion des modeles NeMo
echo - FastConformer disponible
echo - Bug SIGKILL: Corrige
echo ========================================
echo.

echo Lancement application...
python launch_app_with_downloader.py

echo.
if errorlevel 1 (
    echo ERREUR DETECTEE
    pause
) else (
    echo APPLICATION FERMEE
    pause
)