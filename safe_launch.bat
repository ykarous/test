@echo off
echo ========================================
echo    LANCEUR SECURISE NEMO
echo ========================================
echo.

echo Configuration de l'environnement...
call mon_env\Scripts\activate

echo Application des patches...
python nemo_patches.py

echo Demarrage du monitoring...
start /b python process_monitor.py

echo.
echo Lancement de l'application principale...
echo ATTENTION: Si l'application se bloque, appuyez sur Ctrl+C
echo.

python main.py

echo.
echo Application terminee
pause
