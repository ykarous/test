"""
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
    
    print("\n1. Variables d'environnement:")
    for var in required_vars:
        value = os.environ.get(var, "NON DÉFINIE")
        status = "✅" if value == "1" else "❌"
        print(f"   {status} {var} = {value}")
    
    # 2. Vérifier les imports NeMo
    print("\n2. Imports NeMo:")
    
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
    print("\n3. État Pyannote:")
    
    if "pyannote" in sys.modules:
        print("   ⚠️ Pyannote détecté dans sys.modules")
    else:
        print("   ✅ Pyannote non chargé")
    
    # 4. Vérifier les modèles configurés
    print("\n4. Modèles configurés:")
    
    model_vars = [
        "NEMO_TRANSCRIPTION_MODEL",
        "NEMO_DIARIZATION_MODEL"
    ]
    
    for var in model_vars:
        value = os.environ.get(var, "NON DÉFINI")
        print(f"   📋 {var}: {value}")
    
    print("\n🎯 Vérification terminée")
    return True

if __name__ == "__main__":
    verify_nemo_setup()
