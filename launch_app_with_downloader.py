"""
Lanceur de l'application avec interface de téléchargement des modèles NeMo
"""

import os
import sys
import signal
from pathlib import Path
from unittest.mock import MagicMock

# Patch signal Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

print("✅ Signal SIGKILL patché pour Windows")

# Variables d'environnement
env_vars = {
    "USE_NEMO_ONLY": "1",
    "DISABLE_PYANNOTE": "1", 
    "FORCE_NEMO_DIARIZATION": "1",
    "NEMO_MODEL_NAME": "nvidia/stt_en_fastconformer_ctc_large",
    "PYANNOTE_BLOCKED": "1",
    "NEMO_DOWNLOADER_ENABLED": "1"
}

for key, value in env_vars.items():
    os.environ[key] = value

print("🎯 Variables d'environnement configurées")

# Mock Pyannote modules
pyannote_mocks = [
    "pyannote",
    "pyannote.core", 
    "pyannote.core.utils",
    "pyannote.audio",
    "pyannote.audio.pipelines",
    "pyannote.audio.pipelines.speaker_diarization"
]

for module_name in pyannote_mocks:
    if module_name not in sys.modules:
        mock = MagicMock()
        mock.Pipeline = MagicMock()
        mock.Pipeline.from_pretrained = MagicMock(return_value=None)
        mock.SpeakerDiarization = MagicMock(return_value=None)
        mock.Segment = MagicMock()
        mock.Timeline = MagicMock()
        mock.Annotation = MagicMock()
        mock.utils = MagicMock()
        sys.modules[module_name] = mock

print("🚫 Pyannote complètement bloqué")

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

# Lancement application
print("🚀 Lancement application avec téléchargeur de modèles NeMo...")
print("=" * 60)

try:
    import main
    
    # Mode GUI avec focus sur les paramètres
    if len(sys.argv) == 1:
        sys.argv.append("--gui")
    
    print("📥 Interface de téléchargement des modèles NeMo disponible dans:")
    print("   Paramètres > Onglet '📥 Modèles NeMo'")
    print()
    print("🎯 Fonctionnalités disponibles:")
    print("   - Téléchargement de modèles FastConformer")
    print("   - Modèles multilingues")
    print("   - Gestion des modèles téléchargés")
    print("   - Test des modèles")
    print()
    
    main.main()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")