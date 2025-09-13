@echo off
echo ========================================
echo    FASTCONFORMER NEMO - WINDOWS
echo ========================================
echo.

echo Activation environnement...
call mon_env\Scripts\activate

echo.
echo ========================================
echo LANCEMENT AVEC FASTCONFORMER
echo - Modele: FastConformer CTC Large (463MB)
echo - Status: Telecharge et en cache
echo - Bug SIGKILL: Corrige
echo - Pyannote: Completement desactive  
echo ========================================
echo.

echo Lancement application FastConformer...
python launch_with_fastconformer.py

echo.
if errorlevel 1 (
    echo ERREUR DETECTEE
    pause
) else (
    echo APPLICATION FERMEE
    pause
)