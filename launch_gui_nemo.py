"""
Lanceur GUI avec NeMo uniquement - Windows
"""

import os
import sys
import signal
from unittest.mock import MagicMock

# 1. PATCH SIGNAL POUR NEMO WINDOWS
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

print("✅ Signal SIGKILL patché pour Windows")

# 2. VARIABLES D'ENVIRONNEMENT CRITIQUES
critical_env = {
    "USE_NEMO_ONLY": "1",
    "DISABLE_PYANNOTE": "1",
    "FORCE_NEMO_DIARIZATION": "1",
    "SKIP_PYANNOTE_IMPORT": "1",
    "NEMO_WINDOWS_PATCH": "1",
    "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    "TRANSFORMERS_OFFLINE": "0"
}

for key, value in critical_env.items():
    os.environ[key] = value

print("🎯 Variables d'environnement configurées")

# 3. MOCK COMPLET DE PYANNOTE
pyannote_modules = [
    "pyannote",
    "pyannote.audio", 
    "pyannote.audio.pipelines",
    "pyannote.audio.pipelines.speaker_diarization",
    "pyannote.core",
    "pyannote.database"
]

for module in pyannote_modules:
    if module not in sys.modules:
        mock = MagicMock()
        if "Pipeline" in module or "speaker_diarization" in module:
            mock.Pipeline = MagicMock()
            mock.Pipeline.from_pretrained = MagicMock(return_value=None)
            mock.SpeakerDiarization = MagicMock(return_value=None)
        sys.modules[module] = mock

print("🚫 Pyannote complètement désactivé")

# 4. LANCEMENT DE L'INTERFACE GRAPHIQUE
print("🚀 Lancement interface graphique avec NeMo...")
print("=" * 50)

try:
    # Importer et lancer main avec GUI
    import main
    
    # Forcer le mode GUI
    sys.argv = [sys.argv[0], "--gui"]
    
    # Lancer l'application
    main.main()
    
except Exception as e:
    print(f"❌ Erreur de lancement GUI: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")