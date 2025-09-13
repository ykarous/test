@echo off
echo Lancement de l'interface PyQt5...
call mon_env\Scripts\activate.bat
echo 1 | python start_app_safe.py
pause