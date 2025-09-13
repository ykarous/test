@echo off
echo ========================================
echo    LANCEMENT NEMO UNIQUEMENT - WINDOWS
echo ========================================
echo.

echo Activation environnement...
call mon_env\Scripts\activate

echo.
echo ========================================
echo LANCEMENT AVEC NEMO UNIQUEMENT
echo - Bug SIGKILL: Corrige
echo - Pyannote: Completement desactive  
echo - NeMo: Force pour tout
echo ========================================
echo.

echo Lancement application...
python launch_nemo_only.py

echo.
if errorlevel 1 (
    echo ERREUR DETECTEE
    pause
) else (
    echo TERMINE AVEC SUCCES
    pause
)