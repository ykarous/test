@echo off
echo 🎯 Installation NVIDIA NeMo
echo ========================================

REM Activer l'environnement virtuel s'il existe
if exist "mon_env\Scripts\activate.bat" (
    echo 🔧 Activation de l'environnement virtuel...
    call mon_env\Scripts\activate.bat
)

REM Lancer le script Python d'installation
python install_nemo.py

echo ========================================
echo 🎉 Installation terminée!
pause