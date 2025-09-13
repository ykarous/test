"""
Téléchargement et configuration du modèle NeMo FastConformer
"""

import os
import sys
import signal
from pathlib import Path

# Patch signal pour Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM

# Variables d'environnement
os.environ["USE_NEMO_ONLY"] = "1"
os.environ["DISABLE_PYANNOTE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"  # Activer pour voir le téléchargement

print("🚀 TÉLÉCHARGEMENT MODÈLE NEMO FASTCONFORMER")
print("=" * 60)

try:
    print("1. Import NeMo...")
    import nemo.collections.asr as nemo_asr
    print("   ✅ NeMo importé")
    
    print("\n2. Liste des modèles FastConformer disponibles...")
    
    # Modèles FastConformer populaires
    fastconformer_models = [
        "nvidia/stt_en_fastconformer_transducer_large",
        "nvidia/stt_en_fastconformer_transducer_xlarge", 
        "nvidia/stt_en_fastconformer_hybrid_large_streaming_multi",
        "nvidia/stt_multilingual_fastconformer_hybrid_large_pc",
        "nvidia/stt_en_fastconformer_hybrid_large_streaming_1040ms",
        "nvidia/stt_en_fastconformer_ctc_large"
    ]
    
    print("   Modèles disponibles:")
    for i, model in enumerate(fastconformer_models, 1):
        print(f"   {i}. {model}")
    
    print(f"\n3. Tentative de téléchargement du modèle multilingue...")
    
    # Essayer le modèle multilingue en premier
    target_model = "nvidia/stt_multilingual_fastconformer_hybrid_large_pc"
    
    print(f"   📥 Téléchargement: {target_model}")
    print("   (Cela peut prendre plusieurs minutes...)")
    
    try:
        model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.from_pretrained(target_model)
        print(f"   ✅ Modèle téléchargé avec succès!")
        
        # Tester le modèle
        print(f"\n4. Test du modèle...")
        
        # Créer un fichier audio de test
        import numpy as np
        import soundfile as sf
        
        # Générer un signal de test (bruit blanc léger)
        sample_rate = 16000
        duration = 2.0
        samples = np.random.normal(0, 0.1, int(sample_rate * duration)).astype(np.float32)
        
        test_audio = "test_fastconformer.wav"
        sf.write(test_audio, samples, sample_rate)
        
        # Transcrire
        transcription = model.transcribe([test_audio])
        print(f"   ✅ Test transcription: {transcription}")
        
        # Nettoyer
        os.remove(test_audio)
        
        # Sauvegarder les informations du modèle
        model_info = {
            "model_name": target_model,
            "model_type": "FastConformer Hybrid",
            "languages": "Multilingue",
            "sample_rate": 16000,
            "status": "ready"
        }
        
        import json
        with open("nemo_model_config.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        print(f"\n✅ MODÈLE FASTCONFORMER PRÊT!")
        print(f"   - Modèle: {target_model}")
        print(f"   - Type: Hybrid (CTC + Transducer)")
        print(f"   - Langues: Multilingue")
        print(f"   - Configuration sauvée: nemo_model_config.json")
        
    except Exception as e:
        print(f"   ❌ Erreur téléchargement modèle principal: {e}")
        
        # Essayer un modèle plus simple
        print(f"\n   🔄 Essai modèle alternatif...")
        fallback_model = "nvidia/stt_en_fastconformer_ctc_large"
        
        try:
            print(f"   📥 Téléchargement: {fallback_model}")
            model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained(fallback_model)
            print(f"   ✅ Modèle alternatif téléchargé!")
            
            model_info = {
                "model_name": fallback_model,
                "model_type": "FastConformer CTC",
                "languages": "Anglais",
                "sample_rate": 16000,
                "status": "ready"
            }
            
            with open("nemo_model_config.json", 'w') as f:
                json.dump(model_info, f, indent=2)
                
            print(f"   ✅ Modèle alternatif configuré")
            
        except Exception as e2:
            print(f"   ❌ Erreur modèle alternatif: {e2}")
            
            # Créer une configuration par défaut
            print(f"\n   ⚠️ Création configuration par défaut...")
            default_config = {
                "model_name": "local_fallback",
                "model_type": "FastConformer",
                "languages": "Auto-detect",
                "sample_rate": 16000,
                "status": "fallback",
                "note": "Utilise les modèles locaux disponibles"
            }
            
            with open("nemo_model_config.json", 'w') as f:
                json.dump(default_config, f, indent=2)
            
            print(f"   ✅ Configuration par défaut créée")

except Exception as e:
    print(f"❌ Erreur critique: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "=" * 60)
print("Téléchargement terminé")
print("Vous pouvez maintenant lancer l'application avec le modèle FastConformer")