#!/usr/bin/env python3
"""
Script simple pour vérifier la configuration NeMo
"""
import sys
import signal
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

def main():
    print("🔍 Vérification Configuration NeMo")
    print("=" * 40)
    
    try:
        from ai_video_dubbing.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_pipeline_config()
        
        print("📋 Configuration actuelle:")
        print(f"   ASR Model: {config.asr_model}")
        print(f"   Target Language: {config.target_language}")
        print(f"   Source Separation: {config.enable_source_separation}")
        
        # Vérifier si c'est un modèle NeMo
        is_nemo = config.asr_model.startswith("nemo-")
        print(f"   Utilise NeMo: {'✅ OUI' if is_nemo else '❌ NON'}")
        
        if is_nemo:
            print("\n🎉 SUCCÈS: L'application utilisera NeMo!")
            print("\n💡 Quand vous lancez l'application:")
            print("1. Les logs montreront 'Using NeMo transcription'")
            print("2. Le modèle sera téléchargé automatiquement")
            print("3. GPU sera utilisé si disponible")
        else:
            print("\n⚠️  L'application utilise encore Whisper")
            print("💡 Exécutez: python configure_nemo_transcription.py")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    main()