@echo off
echo Installation de pyannote.audio...
call mon_env\Scripts\activate.bat
pip install pyannote.audio
echo.
echo pyannote.audio installé avec succès!
pause