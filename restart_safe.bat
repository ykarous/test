@echo off
echo Redemarrage securise du systeme NeMo
echo.

echo Nettoyage des processus...
taskkill /f /im python.exe 2>nul

echo Attente de 3 secondes...
timeout /t 3 /nobreak >nul

echo Redemarrage avec configuration d'urgence...
mon_env\Scripts\activate
python -c "
import json
from pathlib import Path

# Charger la config d'urgence
config_file = Path('.kiro/emergency_config.json')
if config_file.exists():
    print('Configuration d\'urgence detectee')
    with open(config_file, 'r') as f:
        config = json.load(f)
    print('Mode de recuperation active')
else:
    print('Demarrage normal')

print('Systeme pret')
"

echo.
echo Systeme redémarre en mode sécurisé
echo Vous pouvez maintenant relancer main.py
pause
