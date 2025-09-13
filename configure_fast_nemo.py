#!/usr/bin/env python3
"""
Configure l'application pour utiliser un modèle NeMo plus rapide
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

def configure_fast_nemo():
    """Configure un modèle NeMo plus rapide"""
    try:
        from ai_video_dubbing.utils.config_manager import ConfigManager
        from ai_video_dubbing.models.data_models import PipelineConfig
        
        config_manager = ConfigManager()
        
        # Utiliser un modèle NeMo plus petit et plus rapide
        fast_config = PipelineConfig(
            enable_source_separation=False,  # Désactiver pour plus de rapidité
            enable_ocr=True,
            asr_model="nvidia/stt_en_conformer_ctc_small",  # Modèle petit et rapide
            ocr_model="paddleocr",
            voice_cloning_model="tortoise-tts",
            target_language="en",  # Anglais pour le modèle small
            output_codec="h264",
            output_bitrate="5M",
            temp_directory="./temp",
            max_memory_usage=0.8
        )
        
        success = config_manager.save_pipeline_config(fast_config)
        
        if success:
            print("✅ Configuration NeMo rapide sauvegardée:")
            print(f"   ASR Model: {fast_config.asr_model}")
            print(f"   Target Language: {fast_config.target_language}")
            print(f"   Source Separation: {fast_config.enable_source_separation}")
            print("   📦 Modèle petit (~49MB) - téléchargement rapide")
            return True
        else:
            print("❌ Échec de la sauvegarde")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def configure_whisper_fallback():
    """Configure Whisper comme fallback temporaire"""
    try:
        from ai_video_dubbing.utils.config_manager import ConfigManager
        from ai_video_dubbing.models.data_models import PipelineConfig
        
        config_manager = ConfigManager()
        
        # Configuration Whisper rapide
        whisper_config = PipelineConfig(
            enable_source_separation=False,
            enable_ocr=True,
            asr_model="whisper-base",  # Retour à Whisper
            ocr_model="paddleocr",
            voice_cloning_model="tortoise-tts",
            target_language="fr",
            output_codec="h264",
            output_bitrate="5M",
            temp_directory="./temp",
            max_memory_usage=0.8
        )
        
        success = config_manager.save_pipeline_config(whisper_config)
        
        if success:
            print("✅ Configuration Whisper sauvegardée:")
            print(f"   ASR Model: {whisper_config.asr_model}")
            print(f"   Target Language: {whisper_config.target_language}")
            print("   ⚡ Whisper est plus rapide pour les tests")
            return True
        else:
            print("❌ Échec de la sauvegarde")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("⚡ Configuration Modèles Rapides")
    print("=" * 40)
    
    print("Choisissez une option:")
    print("1. 🚀 NeMo rapide (modèle small)")
    print("2. ⚡ Whisper (fallback temporaire)")
    print("3. 🔍 Vérifier configuration actuelle")
    
    try:
        choice = input("\nVotre choix (1/2/3): ").strip()
        
        if choice == "1":
            print("\n🚀 Configuration NeMo rapide...")
            if configure_fast_nemo():
                print("\n✅ Configuration appliquée!")
                print("💡 Redémarrez l'application pour utiliser le modèle rapide")
        
        elif choice == "2":
            print("\n⚡ Configuration Whisper...")
            if configure_whisper_fallback():
                print("\n✅ Configuration appliquée!")
                print("💡 L'application utilisera Whisper (plus rapide)")
        
        elif choice == "3":
            print("\n🔍 Configuration actuelle:")
            from ai_video_dubbing.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_pipeline_config()
            print(f"   ASR Model: {config.asr_model}")
            print(f"   Target Language: {config.target_language}")
            print(f"   Source Separation: {config.enable_source_separation}")
        
        else:
            print("❌ Choix invalide")
    
    except KeyboardInterrupt:
        print("\n👋 Annulé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    main()