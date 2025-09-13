@echo off
echo ========================================
echo    INTERFACE GRAPHIQUE NEMO - WINDOWS
echo ========================================
echo.

echo Activation environnement...
call mon_env\Scripts\activate

echo.
echo ========================================
echo LANCEMENT INTERFACE GRAPHIQUE
echo - Bug SIGKILL: Corrige
echo - Pyannote: Completement desactive  
echo - NeMo: Force pour tout
echo - Interface: PyQt5
echo ========================================
echo.

echo Lancement interface graphique...
python launch_gui_nemo.py

echo.
if errorlevel 1 (
    echo ERREUR DETECTEE
    pause
) else (
    echo INTERFACE FERMEE
    pause
)