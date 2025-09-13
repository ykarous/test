#!/usr/bin/env python3
"""
Script de diagnostic pour identifier où la transcription se bloque
"""
import sys
import signal
import time
import threading
from pathlib import Path

# Patch pour NeMo sur Windows AVANT tout import
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

def test_nemo_model_loading():
    """Test le chargement d'un modèle NeMo"""
    print("🧪 Test de chargement du modèle NeMo...")
    
    try:
        import nemo.collections.asr as nemo_asr
        
        print("   📦 Import NeMo ASR: OK")
        
        # Essayer de charger un modèle simple
        print("   🔄 Tentative de chargement du modèle...")
        
        # Utiliser un timeout pour éviter le blocage
        def load_model():
            try:
                # Essayer un modèle plus petit d'abord
                model = nemo_asr.models.EncDecCTCModel.from_pretrained("nvidia/stt_en_conformer_ctc_small")
                print("   ✅ Modèle chargé avec succès!")
                return model
            except Exception as e:
                print(f"   ❌ Erreur chargement modèle: {e}")
                return None
        
        # Lancer le chargement dans un thread avec timeout
        result = [None]
        def worker():
            result[0] = load_model()
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # 30 secondes max
        
        if thread.is_alive():
            print("   ⏰ TIMEOUT: Le chargement du modèle prend trop de temps")
            print("   💡 Ceci explique pourquoi l'application se bloque")
            return False
        
        return result[0] is not None
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_whisper_fallback():
    """Test si Whisper fonctionne comme fallback"""
    print("\n🔄 Test Whisper comme fallback...")
    
    try:
        import whisper
        print("   📦 Import Whisper: OK")
        
        # Essayer de charger un modèle Whisper petit
        print("   🔄 Chargement modèle Whisper tiny...")
        model = whisper.load_model("tiny")
        print("   ✅ Whisper fonctionne!")
        return True
        
    except Exception as e:
        print(f"   ❌ Whisper échoue aussi: {e}")
        return False

def test_ai_model_manager():
    """Test l'AIModelManager avec différents modèles"""
    print("\n🤖 Test AIModelManager...")
    
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        manager = AIModelManager()
        print("   📦 AIModelManager créé: OK")
        
        # Test avec un modèle Whisper d'abord
        print("   🔄 Test avec Whisper...")
        try:
            # Simuler un appel sans vraiment charger
            has_whisper = hasattr(manager, 'transcribe_audio')
            print(f"   Méthode Whisper: {'✅' if has_whisper else '❌'}")
        except Exception as e:
            print(f"   ❌ Erreur Whisper: {e}")
        
        # Test avec NeMo
        print("   🔄 Test avec NeMo...")
        try:
            has_nemo = hasattr(manager, 'transcribe_audio_with_nemo')
            print(f"   Méthode NeMo: {'✅' if has_nemo else '❌'}")
        except Exception as e:
            print(f"   ❌ Erreur NeMo: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur AIModelManager: {e}")
        return False

def suggest_solutions():
    """Suggère des solutions"""
    print("\n💡 SOLUTIONS RECOMMANDÉES:")
    print("=" * 50)
    
    print("1. 🔄 UTILISER WHISPER TEMPORAIREMENT:")
    print("   python configure_whisper_fallback.py")
    print("   (Nous allons créer ce script)")
    
    print("\n2. 📦 TÉLÉCHARGER MODÈLES NEMO MANUELLEMENT:")
    print("   python download_nemo_models.py")
    print("   (Nous allons créer ce script)")
    
    print("\n3. 🔧 CONFIGURER HUGGINGFACE TOKEN:")
    print("   - Aller sur https://huggingface.co/settings/tokens")
    print("   - Créer un token")
    print("   - Exporter: set HF_TOKEN=your_token_here")
    
    print("\n4. ⚡ UTILISER MODÈLES PLUS PETITS:")
    print("   - Commencer avec des modèles NeMo plus petits")
    print("   - Éviter les modèles 'large' au début")

def main():
    """Point d'entrée principal"""
    print("🔍 DIAGNOSTIC DE TRANSCRIPTION")
    print("=" * 50)
    
    # Test 1: NeMo
    nemo_ok = test_nemo_model_loading()
    
    # Test 2: Whisper fallback
    whisper_ok = test_whisper_fallback()
    
    # Test 3: AIModelManager
    manager_ok = test_ai_model_manager()
    
    # Résumé
    print("\n📊 RÉSUMÉ:")
    print("=" * 30)
    print(f"NeMo:          {'✅ OK' if nemo_ok else '❌ BLOQUE'}")
    print(f"Whisper:       {'✅ OK' if whisper_ok else '❌ PROBLÈME'}")
    print(f"AIModelManager: {'✅ OK' if manager_ok else '❌ PROBLÈME'}")
    
    if not nemo_ok:
        print("\n🎯 PROBLÈME IDENTIFIÉ:")
        print("Le chargement des modèles NeMo prend trop de temps ou échoue.")
        print("C'est pourquoi l'application se bloque à 'Transcribing audio...'")
        
        suggest_solutions()
    else:
        print("\n✅ Tous les tests passent, le problème est ailleurs.")

if __name__ == "__main__":
    main()