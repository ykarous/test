
# Patch pour ignorer Pyannote temporairement
import sys
import os
from unittest.mock import MagicMock

# Vérifier si on doit désactiver Pyannote
if os.environ.get("DISABLE_PYANNOTE") == "1":
    print("🔧 Pyannote désactivé - utilisation du fallback")
    
    # Mock des modules Pyannote
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = None
    
    # Remplacer les imports Pyannote par des mocks
    sys.modules["pyannote"] = MagicMock()
    sys.modules["pyannote.audio"] = MagicMock()
    sys.modules["pyannote.audio.pipelines"] = MagicMock()
    sys.modules["pyannote.audio.pipelines.speaker_diarization"] = MagicMock()
    
    # Mock de la classe SpeakerDiarization
    class MockSpeakerDiarization:
        def __init__(self, *args, **kwargs):
            pass
        
        def __call__(self, *args, **kwargs):
            # Retourner un résultat de fallback simple
            return None
    
    sys.modules["pyannote.audio.pipelines.speaker_diarization"].SpeakerDiarization = MockSpeakerDiarization
    
    print("   ✅ Modules Pyannote mockés")

print("🎯 Patch Pyannote appliqué")
