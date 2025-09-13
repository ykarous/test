#!/usr/bin/env python3
"""
Script pour configurer l'application pour utiliser NeMo au lieu de Whisper
"""
import sys
import signal
import json
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

def check_nemo_availability():
    """Vérifie si NeMo est disponible"""
    try:
        import nemo
        import nemo.collections.asr as nemo_asr
        print(f"✅ NeMo {nemo.__version__} disponible")
        return True
    except ImportError as e:
        print(f"❌ NeMo non disponible: {e}")
        return False

def check_current_config():
    """Vérifie la configuration actuelle"""
    try:
        from ai_video_dubbing.utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        current_config = config_manager.load_pipeline_config()
        
        print(f"📋 Configuration actuelle:")
        print(f"   ASR Model: {current_config.asr_model}")
        print(f"   Target Language: {current_config.target_language}")
        print(f"   Source Separation: {current_config.enable_source_separation}")
        
        return current_config
    except Exception as e:
        print(f"⚠️  Impossible de charger la configuration: {e}")
        return None

def configure_nemo():
    """Configure l'application pour utiliser NeMo"""
    try:
        from ai_video_dubbing.utils.config_manager import ConfigManager
        from ai_video_dubbing.models.data_models import PipelineConfig
        
        config_manager = ConfigManager()
        
        # Créer une nouvelle configuration avec NeMo
        nemo_config = PipelineConfig(
            enable_source_separation=True,  # Recommandé avec NeMo
            enable_ocr=True,
            asr_model="nemo-conformer-ctc-large-fr",  # Modèle NeMo français
            ocr_model="paddleocr",
            voice_cloning_model="tortoise-tts",
            target_language="fr",
            output_codec="h264",
            output_bitrate="5M",
            temp_directory="./temp",
            max_memory_usage=0.8
        )
        
        # Sauvegarder la configuration
        success = config_manager.save_pipeline_config(nemo_config)
        
        if success:
            print("✅ Configuration NeMo sauvegardée:")
            print(f"   ASR Model: {nemo_config.asr_model}")
            print(f"   Target Language: {nemo_config.target_language}")
            print(f"   Source Separation: {nemo_config.enable_source_separation}")
            
            # Sauvegarder aussi la configuration NeMo spécifique
            nemo_settings = {
                "device": "auto",
                "enable_gpu": True,
                "batch_size": 1,
                "models": {
                    "french": "nemo-conformer-ctc-large-fr",
                    "english": "nemo-conformer-ctc-large-en",
                    "multilingual": "nemo-conformer-ctc-large-multilingual"
                }
            }
            config_manager.save_nemo_config(nemo_settings)
            
            return True
        else:
            print("❌ Échec de la sauvegarde de configuration")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nemo_transcription():
    """Test rapide de la transcription NeMo"""
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        print("🧪 Test de la transcription NeMo...")
        
        # Créer un gestionnaire de modèles
        ai_manager = AIModelManager()
        
        # Vérifier si NeMo est disponible
        if hasattr(ai_manager, 'transcribe_audio_with_nemo'):
            print("✅ Méthode transcribe_audio_with_nemo disponible")
        else:
            print("❌ Méthode transcribe_audio_with_nemo non disponible")
            return False
        
        print("✅ NeMo prêt pour la transcription")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test NeMo: {e}")
        return False

def create_nemo_config_file():
    """Crée un fichier de configuration spécifique pour NeMo"""
    config_data = {
        "asr_engine": "nemo",
        "nemo_models": {
            "french": "nemo-conformer-ctc-large-fr",
            "english": "nemo-conformer-ctc-large-en",
            "multilingual": "nemo-conformer-ctc-large-multilingual"
        },
        "device": "auto",  # auto, gpu, cpu
        "enable_gpu": True,
        "batch_size": 1,
        "enable_diarization": True,
        "diarization_model": "nemo-titanet-large"
    }
    
    config_file = Path("nemo_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration NeMo créée: {config_file}")
    return config_file

def main():
    """Point d'entrée principal"""
    print("🎯 Configuration NeMo pour AI Video Dubbing")
    print("=" * 50)
    
    # 1. Vérifier NeMo
    if not check_nemo_availability():
        print("\n💡 Pour installer NeMo:")
        print("   python install_nemo.py")
        return
    
    # 2. Vérifier la configuration actuelle
    print("\n📋 Configuration actuelle:")
    current_config = check_current_config()
    
    # 3. Configurer NeMo
    print("\n🔧 Configuration de NeMo...")
    if configure_nemo():
        print("✅ Configuration NeMo appliquée avec succès!")
    else:
        print("❌ Échec de la configuration NeMo")
        return
    
    # 4. Test de NeMo
    print("\n🧪 Test de NeMo...")
    if test_nemo_transcription():
        print("✅ NeMo prêt à l'emploi!")
    else:
        print("⚠️  NeMo configuré mais test échoué")
    
    # 5. Créer fichier de configuration NeMo
    print("\n📄 Création du fichier de configuration...")
    config_file = create_nemo_config_file()
    
    print("\n🎊 Configuration terminée!")
    print("\n💡 Instructions:")
    print("1. Redémarrez l'application: python main.py --gui")
    print("2. L'application utilisera maintenant NeMo pour la transcription")
    print("3. Les modèles NeMo seront téléchargés automatiquement au premier usage")
    print("4. GPU sera utilisé automatiquement si disponible")
    
    print("\n📋 Modèles NeMo disponibles:")
    print("   - nemo-conformer-ctc-large-fr (Français)")
    print("   - nemo-conformer-ctc-large-en (Anglais)")
    print("   - nemo-conformer-ctc-large-multilingual (Multilingue)")
    
    print("=" * 50)

if __name__ == "__main__":
    main()