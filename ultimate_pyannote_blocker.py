"""
Bloqueur ultime de Pyannote - Patch tous les imports
"""

import sys
import os
from unittest.mock import MagicMock

# Bloquer TOUS les imports Pyannote avant qu'ils ne se chargent
class PyannoteBlocker:
    def __init__(self):
        self.blocked_modules = [
            'pyannote',
            'pyannote.core',
            'pyannote.core.utils',
            'pyannote.audio',
            'pyannote.audio.core',
            'pyannote.audio.pipelines',
            'pyannote.audio.pipelines.speaker_diarization',
            'pyannote.database',
            'pyannote.metrics'
        ]
        
    def block_all(self):
        """Bloque tous les modules Pyannote"""
        for module_name in self.blocked_modules:
            if module_name not in sys.modules:
                # Créer un mock complet
                mock_module = MagicMock()
                
                # Ajouter des attributs spécifiques selon le module
                if 'Pipeline' in module_name or 'speaker_diarization' in module_name:
                    mock_module.Pipeline = MagicMock()
                    mock_module.Pipeline.from_pretrained = MagicMock(return_value=None)
                    mock_module.SpeakerDiarization = MagicMock(return_value=None)
                
                if 'core' in module_name:
                    mock_module.Segment = MagicMock()
                    mock_module.Timeline = MagicMock()
                    mock_module.Annotation = MagicMock()
                    mock_module.utils = MagicMock()
                
                # Injecter le mock dans sys.modules
                sys.modules[module_name] = mock_module
                
        print(f"🚫 {len(self.blocked_modules)} modules Pyannote bloqués")

# Appliquer le blocage immédiatement
blocker = PyannoteBlocker()
blocker.block_all()

# Variables d'environnement critiques
os.environ["USE_NEMO_ONLY"] = "1"
os.environ["DISABLE_PYANNOTE"] = "1"
os.environ["FORCE_NEMO_DIARIZATION"] = "1"
os.environ["PYANNOTE_BLOCKED"] = "1"

print("✅ Pyannote complètement bloqué au niveau système")
print("🎯 Variables d'environnement configurées")

# Test du blocage
try:
    import pyannote.core.utils
    print("⚠️ Import pyannote.core.utils réussi (ne devrait pas arriver)")
except Exception as e:
    print("✅ Import pyannote.core.utils bloqué avec succès")

try:
    from pyannote.audio import Pipeline
    print("⚠️ Import Pipeline réussi (ne devrait pas arriver)")
except Exception as e:
    print("✅ Import Pipeline bloqué avec succès")

print("\n🚀 Blocage Pyannote terminé - Prêt pour NeMo uniquement")