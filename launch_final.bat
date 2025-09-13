@echo off
echo ========================================
echo    LANCEMENT FINAL NEMO OPTIMISE
echo ========================================
echo.

echo Activation environnement...
call mon_env\Scripts\activate

echo Configuration NeMo pour Windows...
set USE_NEMO_ONLY=1
set FORCE_NEMO_DIARIZATION=1
set DISABLE_PYANNOTE=1
set NEMO_WINDOWS_MODE=1
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

echo Application des patches...
python fix_nemo_windows.py

echo.
echo ========================================
echo CONFIGURATION FINALE:
echo - Framework: NVIDIA NeMo uniquement
echo - Transcription: NeMo
echo - Diarisation: NeMo (PAS Pyannote)
echo - Optimisations: Activées
echo - Windows: Patches appliqués
echo ========================================
echo.

echo Lancement de l'application...
python main.py

echo.
echo Application terminée
pause
