@echo off
echo ========================================
echo   AI Video Dubbing - Interface PyQt5
echo ========================================
echo.
echo Activation de l'environnement virtuel...
call mon_env\Scripts\activate.bat

echo Lancement de l'application...
python main.py --gui

echo.
echo Application fermée.
pause