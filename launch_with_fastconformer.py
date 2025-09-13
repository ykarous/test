"""
Lanceur avec modèle FastConformer spécifique
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
    "NEMO_MODEL_NAME": "nvidia/stt_en_fastconformer_ctc_large",
    "NEMO_MODEL_TYPE": "FastConformer",
    "HF_HUB_DISABLE_PROGRESS_BARS": "1"
}

for key, value in critical_env.items():
    os.environ[key] = value

print("🎯 Variables d'environnement configurées")
print(f"   📦 Modèle: {os.environ['NEMO_MODEL_NAME']}")

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

# 4. VÉRIFICATION DU MODÈLE FASTCONFORMER
print("🔍 Vérification du modèle FastConformer...")

try:
    import nemo.collections.asr as nemo_asr
    
    # Vérifier que le modèle est en cache
    model_name = "nvidia/stt_en_fastconformer_ctc_large"
    print(f"   📦 Chargement: {model_name}")
    
    # Charger le modèle (depuis le cache)
    model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained(model_name)
    print(f"   ✅ Modèle FastConformer chargé depuis le cache")
    print(f"   📊 Type: {type(model).__name__}")
    
    # Sauvegarder la référence du modèle pour l'application
    os.environ["NEMO_MODEL_LOADED"] = "1"
    
except Exception as e:
    print(f"   ⚠️ Erreur chargement modèle: {e}")
    print(f"   🔄 L'application utilisera le téléchargement automatique")

# 5. LANCEMENT DE L'APPLICATION
print("🚀 Lancement application avec FastConformer...")
print("=" * 60)

try:
    # Importer et lancer l'application principale
    import main
    
    # Forcer le mode GUI si pas d'arguments
    if len(sys.argv) == 1:
        sys.argv.append("--gui")
    
    # Lancer l'application
    main.main()
    
except Exception as e:
    print(f"❌ Erreur de lancement: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")