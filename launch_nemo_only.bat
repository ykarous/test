@echo off
echo ========================================
echo    LANCEMENT NVIDIA NEMO UNIQUEMENT
echo ========================================
echo.

echo Activation de l'environnement...
call mon_env\Scripts\activate

echo Configuration NeMo uniquement...
set USE_NEMO_ONLY=1
set FORCE_NEMO_DIARIZATION=1
set DISABLE_PYANNOTE=1
set NEMO_TRANSCRIPTION_MODEL=nvidia/stt_conformer_ctc_large
set NEMO_DIARIZATION_MODEL=nvidia/speakerverification_speakernet

echo Application du patch NeMo...
python nemo_only_patch.py

echo.
echo ========================================
echo LANCEMENT AVEC NVIDIA NEMO UNIQUEMENT
echo - Transcription: NeMo
echo - Diarisation: NeMo (pas Pyannote)
echo - VAD: NeMo
echo ========================================
echo.

python main.py

echo.
echo Application terminée
pause
