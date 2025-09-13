@echo off
echo Test de l'interface principale...
call mon_env\Scripts\activate.bat
echo Environnement virtuel activé
python -c "import numpy; print('NumPy disponible')"
echo Lancement de l'interface principale...
python main.py --gui
pause