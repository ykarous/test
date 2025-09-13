"""
Script pour désactiver temporairement Pyannote et débloquer NeMo
"""

import os
import sys
from pathlib import Path

def disable_pyannote_temporarily():
    """Désactive temporairement Pyannote pour se concentrer sur NeMo"""
    
    print("🔧 Désactivation temporaire de Pyannote")
    print("=" * 50)
    
    # 1. Variables d'environnement pour désactiver Pyannote
    env_vars = {
        "DISABLE_PYANNOTE": "1",
        "SKIP_DIARIZATION": "1", 
        "USE_SINGLE_SPEAKER": "1",
        "PYANNOTE_OFFLINE": "1"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key} = {value}")
    
    # 2. Créer un patch pour ignorer Pyannote
    patch_code = '''
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
'''
    
    # Sauvegarder le patch
    with open("pyannote_patch.py", 'w', encoding='utf-8') as f:
        f.write(patch_code)
    
    print("   ✅ Patch sauvegardé: pyannote_patch.py")
    
    # 3. Créer un lanceur sans Pyannote
    launcher_script = '''@echo off
echo ========================================
echo    LANCEMENT SANS PYANNOTE
echo ========================================
echo.

echo Activation de l'environnement...
call mon_env\\Scripts\\activate

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
'''
    
    with open("launch_without_pyannote.bat", 'w') as f:
        f.write(launcher_script)
    
    print("   ✅ Lanceur créé: launch_without_pyannote.bat")
    
    # 4. Instructions
    print(f"\n💡 Instructions:")
    print(f"   1. Utilisez: launch_without_pyannote.bat")
    print(f"   2. Ou manuellement:")
    print(f"      - python pyannote_patch.py")
    print(f"      - python main.py")
    print(f"\n⚠️ Note: La diarisation sera désactivée temporairement")
    print(f"   Pour réactiver Pyannote plus tard:")
    print(f"   1. Obtenez un token HF: https://hf.co/settings/tokens")
    print(f"   2. Acceptez les conditions: https://hf.co/pyannote/segmentation")
    print(f"   3. Exécutez: huggingface-cli login")

def create_nemo_focus_config():
    """Crée une configuration focalisée sur NeMo uniquement"""
    
    print(f"\n⚙️ Configuration focalisée NeMo")
    
    nemo_config = {
        "version": "1.0",
        "mode": "nemo_only",
        "description": "Configuration focalisée sur NeMo sans Pyannote",
        
        "audio_processing": {
            "disable_diarization": True,
            "assume_single_speaker": True,
            "chunk_duration_seconds": 30,
            "overlap_seconds": 2
        },
        
        "nemo_settings": {
            "model_name": "nvidia/stt_conformer_ctc_small",  # Modèle plus léger
            "batch_size": 1,
            "enable_gpu": True,
            "fallback_to_cpu": True,
            "max_audio_length": 300  # 5 minutes max
        },
        
        "fallback_options": {
            "use_whisper_if_nemo_fails": True,
            "whisper_model": "base",
            "timeout_seconds": 120
        },
        
        "performance": {
            "enable_optimizations": True,
            "cache_models": True,
            "parallel_processing": False,  # Désactiver pour éviter les blocages
            "memory_limit_mb": 2048
        }
    }
    
    try:
        config_dir = Path(".kiro")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "nemo_focus_config.json", 'w') as f:
            import json
            json.dump(nemo_config, f, indent=2)
        
        print("   ✅ Configuration NeMo sauvegardée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("🎯 DÉSACTIVATION PYANNOTE POUR DÉBLOQUER NEMO")
    print("=" * 60)
    
    try:
        # Désactiver Pyannote
        disable_pyannote_temporarily()
        
        # Configuration NeMo
        create_nemo_focus_config()
        
        print(f"\n✅ CONFIGURATION TERMINÉE")
        print(f"\n🚀 Prochaines étapes:")
        print(f"   1. Lancez: launch_without_pyannote.bat")
        print(f"   2. Testez la transcription NeMo sans diarisation")
        print(f"   3. Si ça fonctionne, configurez Pyannote plus tard")
        
        print(f"\n📋 Fichiers créés:")
        files = ["pyannote_patch.py", "launch_without_pyannote.bat", ".kiro/nemo_focus_config.json"]
        for file_path in files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    main()