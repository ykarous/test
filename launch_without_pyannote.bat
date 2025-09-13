@echo off
echo ========================================
echo    LANCEMENT SANS PYANNOTE
echo ========================================
echo.

echo Activation de l'environnement...
call mon_env\Scripts\activate

echo Application du patch Pyannote...
python pyannote_patch.py

echo Configuration des variables...
set DISABLE_PYANNOTE=1
set SKIP_DIARIZATION=1
set USE_SINGLE_SPEAKER=1

echo.
echo Lancement de l'application (sans diarisation)...
echo ATTENTION: La diarisation sera désactivée
echo.

python main.py

echo.
echo Application terminée
pause
