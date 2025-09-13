@echo off
echo 🎯 Installation automatique de PyTorch
echo ========================================

REM Activer l'environnement virtuel s'il existe
if exist "mon_env\Scripts\activate.bat" (
    echo 🔧 Activation de l'environnement virtuel...
    call mon_env\Scripts\activate.bat
)

REM Lancer le script Python d'installation
python install_pytorch.py

echo ========================================
echo 🎉 Installation terminée!
pause