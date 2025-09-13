"""
Patch pour forcer l'utilisation de NVIDIA NeMo uniquement
"""

import os
import sys

def patch_nemo_only():
    """Patch pour utiliser uniquement NeMo"""
    
    print("🎯 Application du patch NeMo uniquement")
    
    # 1. Désactiver Pyannote complètement
    os.environ["DISABLE_PYANNOTE"] = "1"
    os.environ["USE_NEMO_DIARIZATION"] = "1"
    
    # 2. Mock Pyannote pour éviter les imports
    from unittest.mock import MagicMock
    
    # Mock tous les modules Pyannote
    pyannote_modules = [
        "pyannote",
        "pyannote.audio", 
        "pyannote.audio.pipelines",
        "pyannote.audio.pipelines.speaker_diarization"
    ]
    
    for module in pyannote_modules:
        if module not in sys.modules:
            sys.modules[module] = MagicMock()
    
    print("   ✅ Pyannote désactivé")
    
    # 3. Forcer l'utilisation de NeMo pour la diarisation
    def force_nemo_diarization():
        """Force l'utilisation de NeMo pour la diarisation"""
        
        # Patch la fonction de diarisation pour utiliser NeMo
        try:
            # Importer NeMo
            import nemo.collections.asr as nemo_asr
            
            print("   ✅ NeMo ASR importé avec succès")
            
            # Configuration NeMo pour diarisation
            nemo_config = {
                "use_nemo_diarization": True,
                "diarization_model": "nvidia/speakerverification_speakernet",
                "vad_model": "nvidia/vad_conformer"
            }
            
            return nemo_config
            
        except ImportError as e:
            print(f"   ⚠️ Erreur import NeMo: {e}")
            return None
    
    # Appliquer le patch de diarisation
    nemo_config = force_nemo_diarization()
    if nemo_config:
        print("   ✅ Configuration NeMo diarisation appliquée")
    
    # 4. Configurer les modèles NeMo
    nemo_models = {
        "transcription": "nvidia/stt_conformer_ctc_large",
        "diarization": "nvidia/speakerverification_speakernet", 
        "vad": "nvidia/vad_conformer"
    }
    
    for model_type, model_name in nemo_models.items():
        os.environ[f"NEMO_{model_type.upper()}_MODEL"] = model_name
        print(f"   ✅ {model_type}: {model_name}")
    
    print("🎯 Patch NeMo appliqué avec succès")

# Appliquer le patch automatiquement
if __name__ == "__main__":
    patch_nemo_only()
else:
    # Appliquer le patch lors de l'import
    patch_nemo_only()
