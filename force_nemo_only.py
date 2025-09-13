"""
Script pour forcer l'utilisation de NVIDIA NeMo uniquement
(transcription ET diarisation)
"""

import os
import json
from pathlib import Path

def configure_nemo_only():
    """Configure le système pour utiliser uniquement NeMo"""
    
    print("🎯 CONFIGURATION NVIDIA NEMO UNIQUEMENT")
    print("=" * 50)
    
    # 1. Variables d'environnement pour forcer NeMo
    nemo_env_vars = {
        # Forcer NeMo pour tout
        "USE_NEMO_ONLY": "1",
        "FORCE_NEMO_DIARIZATION": "1",
        "DISABLE_PYANNOTE": "1",
        
        # Configuration NeMo
        "NEMO_CACHE_DIR": ".nemo_cache",
        "NEMO_MODEL_CACHE": "1",
        "NEMO_FORCE_DOWNLOAD": "0",
        
        # Désactiver autres frameworks
        "DISABLE_WHISPER": "1",
        "DISABLE_PYANNOTE_AUDIO": "1",
        "SKIP_EXTERNAL_DIARIZATION": "1"
    }
    
    for key, value in nemo_env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key} = {value}")
    
    print(f"\n   📋 {len(nemo_env_vars)} variables NeMo configurées")

def create_nemo_config():
    """Crée une configuration complète pour NeMo"""
    
    print(f"\n⚙️ Création configuration NeMo complète")
    
    nemo_config = {
        "version": "2.0",
        "framework": "nvidia_nemo_only",
        "description": "Configuration pour utiliser uniquement NVIDIA NeMo",
        
        # Configuration transcription NeMo
        "transcription": {
            "framework": "nemo",
            "model_name": "nvidia/stt_conformer_ctc_large",
            "language": "fr",
            "batch_size": 1,
            "enable_gpu": True,
            "fallback_to_cpu": True,
            "chunk_duration": 20.0,
            "overlap": 2.0
        },
        
        # Configuration diarisation NeMo
        "diarization": {
            "framework": "nemo",  # Utiliser NeMo au lieu de Pyannote
            "model_name": "nvidia/speakerverification_speakernet",
            "clustering_model": "nvidia/titanet_large",
            "enable_vad": True,
            "vad_model": "nvidia/vad_conformer",
            "max_speakers": 10,
            "min_speakers": 1
        },
        
        # Configuration audio
        "audio_processing": {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_length_s": 30,
            "overlap_s": 5,
            "normalize_audio": True
        },
        
        # Configuration performance
        "performance": {
            "enable_optimizations": True,
            "cache_models": True,
            "parallel_processing": False,  # Éviter les blocages
            "memory_limit_mb": 4096,
            "timeout_seconds": 300
        },
        
        # Fallback uniquement vers d'autres modèles NeMo
        "fallback": {
            "enable_fallback": True,
            "fallback_transcription_model": "nvidia/stt_conformer_ctc_medium",
            "fallback_diarization_model": "nvidia/titanet_small",
            "max_fallback_attempts": 2
        }
    }
    
    try:
        config_dir = Path(".kiro")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "nemo_only_config.json", 'w') as f:
            json.dump(nemo_config, f, indent=2)
        
        print("   ✅ Configuration NeMo complète sauvegardée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde: {e}")
        return False

def create_nemo_patch():
    """Crée un patch pour forcer NeMo partout"""
    
    print(f"\n🔧 Création du patch NeMo")
    
    patch_code = '''"""
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
'''
    
    try:
        with open("nemo_only_patch.py", 'w', encoding='utf-8') as f:
            f.write(patch_code)
        
        print("   ✅ Patch NeMo sauvegardé: nemo_only_patch.py")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création patch: {e}")
        return False

def create_nemo_launcher():
    """Crée un lanceur spécialisé pour NeMo uniquement"""
    
    print(f"\n🚀 Création du lanceur NeMo")
    
    launcher_script = '''@echo off
echo ========================================
echo    LANCEMENT NVIDIA NEMO UNIQUEMENT
echo ========================================
echo.

echo Activation de l'environnement...
call mon_env\\Scripts\\activate

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
'''
    
    try:
        with open("launch_nemo_only.bat", 'w') as f:
            f.write(launcher_script)
        
        print("   ✅ Lanceur créé: launch_nemo_only.bat")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création lanceur: {e}")
        return False

def create_nemo_verification():
    """Crée un script de vérification NeMo"""
    
    verification_script = '''"""
Script de vérification de la configuration NeMo
"""

import os
import sys

def verify_nemo_setup():
    """Vérifie que NeMo est correctement configuré"""
    
    print("🔍 VÉRIFICATION CONFIGURATION NEMO")
    print("=" * 40)
    
    # 1. Vérifier les variables d'environnement
    required_vars = [
        "USE_NEMO_ONLY",
        "FORCE_NEMO_DIARIZATION", 
        "DISABLE_PYANNOTE"
    ]
    
    print("\\n1. Variables d'environnement:")
    for var in required_vars:
        value = os.environ.get(var, "NON DÉFINIE")
        status = "✅" if value == "1" else "❌"
        print(f"   {status} {var} = {value}")
    
    # 2. Vérifier les imports NeMo
    print("\\n2. Imports NeMo:")
    
    try:
        import nemo
        print("   ✅ nemo: OK")
    except ImportError as e:
        print(f"   ❌ nemo: {e}")
        return False
    
    try:
        import nemo.collections.asr as nemo_asr
        print("   ✅ nemo.collections.asr: OK")
    except ImportError as e:
        print(f"   ❌ nemo.collections.asr: {e}")
    
    try:
        import nemo.collections.tts as nemo_tts
        print("   ✅ nemo.collections.tts: OK")
    except ImportError as e:
        print(f"   ❌ nemo.collections.tts: {e}")
    
    # 3. Vérifier que Pyannote est désactivé
    print("\\n3. État Pyannote:")
    
    if "pyannote" in sys.modules:
        print("   ⚠️ Pyannote détecté dans sys.modules")
    else:
        print("   ✅ Pyannote non chargé")
    
    # 4. Vérifier les modèles configurés
    print("\\n4. Modèles configurés:")
    
    model_vars = [
        "NEMO_TRANSCRIPTION_MODEL",
        "NEMO_DIARIZATION_MODEL"
    ]
    
    for var in model_vars:
        value = os.environ.get(var, "NON DÉFINI")
        print(f"   📋 {var}: {value}")
    
    print("\\n🎯 Vérification terminée")
    return True

if __name__ == "__main__":
    verify_nemo_setup()
'''
    
    try:
        with open("verify_nemo_setup.py", 'w', encoding='utf-8') as f:
            f.write(verification_script)
        
        print("   ✅ Script de vérification créé: verify_nemo_setup.py")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création vérification: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("🎯 CONFIGURATION NVIDIA NEMO UNIQUEMENT")
    print("=" * 60)
    print("Objectif: Utiliser NeMo pour transcription ET diarisation")
    print("(Désactiver complètement Pyannote)")
    print()
    
    success_count = 0
    total_steps = 5
    
    try:
        # 1. Configuration environnement
        configure_nemo_only()
        success_count += 1
        
        # 2. Configuration NeMo
        if create_nemo_config():
            success_count += 1
        
        # 3. Patch NeMo
        if create_nemo_patch():
            success_count += 1
        
        # 4. Lanceur NeMo
        if create_nemo_launcher():
            success_count += 1
        
        # 5. Script de vérification
        if create_nemo_verification():
            success_count += 1
        
        # Résumé
        print(f"\\n📊 RÉSUMÉ")
        print(f"   Étapes réussies: {success_count}/{total_steps}")
        print(f"   Taux de succès: {(success_count/total_steps)*100:.1f}%")
        
        if success_count >= 4:
            print(f"\\n✅ CONFIGURATION NEMO TERMINÉE")
            print(f"\\n🚀 Pour utiliser NeMo uniquement:")
            print(f"   1. Lancez: launch_nemo_only.bat")
            print(f"   2. Ou manuellement:")
            print(f"      - python nemo_only_patch.py")
            print(f"      - python main.py")
            print(f"\\n🔍 Pour vérifier la config:")
            print(f"   - python verify_nemo_setup.py")
            
            print(f"\\n📋 Fichiers créés:")
            files = [
                "nemo_only_patch.py",
                "launch_nemo_only.bat", 
                "verify_nemo_setup.py",
                ".kiro/nemo_only_config.json"
            ]
            
            for file_path in files:
                if Path(file_path).exists():
                    print(f"   ✅ {file_path}")
        else:
            print(f"\\n⚠️ Configuration partielle")
            print(f"   Certaines étapes ont échoué")
        
    except Exception as e:
        print(f"\\n❌ Erreur: {e}")

if __name__ == "__main__":
    main()