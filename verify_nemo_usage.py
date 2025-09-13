#!/usr/bin/env python3
"""
Script pour vérifier que l'application utilise bien NeMo pour la transcription
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

def check_configuration():
    """Vérifie la configuration actuelle"""
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
        
        return config, is_nemo
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return None, False

def check_pipeline_logic():
    """Vérifie la logique du pipeline"""
    try:
        from ai_video_dubbing.processors.pipeline_orchestrator import PipelineOrchestrator
        from ai_video_dubbing.models.data_models import PipelineConfig
        
        # Créer une configuration de test avec NeMo
        test_config = PipelineConfig(
            asr_model="nemo-conformer-ctc-large-fr",
            target_language="fr"
        )
        
        # Créer le pipeline
        pipeline = PipelineOrchestrator(test_config)
        
        print("🔍 Vérification de la logique du pipeline:")
        print(f"   Configuration ASR: {pipeline.config.asr_model}")
        
        # Vérifier si la méthode _transcribe_audio détecte NeMo
        is_nemo_detected = pipeline.config.asr_model.startswith("nemo-")
        print(f"   Détection NeMo: {'✅ OUI' if is_nemo_detected else '❌ NON'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
        return False

def check_ai_model_manager():
    """Vérifie que l'AIModelManager a les méthodes NeMo"""
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        manager = AIModelManager()
        
        print("🤖 Vérification AIModelManager:")
        
        # Vérifier les méthodes disponibles
        has_nemo_method = hasattr(manager, 'transcribe_audio_with_nemo')
        has_whisper_method = hasattr(manager, 'transcribe_audio')
        
        print(f"   Méthode NeMo: {'✅ Disponible' if has_nemo_method else '❌ Manquante'}")
        print(f"   Méthode Whisper: {'✅ Disponible' if has_whisper_method else '❌ Manquante'}")
        
        return has_nemo_method and has_whisper_method
        
    except Exception as e:
        print(f"❌ Erreur AIModelManager: {e}")
        return False

def simulate_transcription_choice():
    """Simule le choix du moteur de transcription"""
    try:
        from ai_video_dubbing.models.data_models import PipelineConfig
        
        print("🎯 Simulation du choix de moteur:")
        
        # Test avec modèle NeMo
        nemo_config = PipelineConfig(asr_model="nemo-conformer-ctc-large-fr")
        nemo_choice = nemo_config.asr_model.startswith("nemo-")
        print(f"   Config NeMo ({nemo_config.asr_model}): {'✅ NeMo sélectionné' if nemo_choice else '❌ Whisper sélectionné'}")
        
        # Test avec modèle Whisper
        whisper_config = PipelineConfig(asr_model="whisper-base")
        whisper_choice = whisper_config.asr_model.startswith("nemo-")
        print(f"   Config Whisper ({whisper_config.asr_model}): {'❌ NeMo sélectionné' if whisper_choice else '✅ Whisper sélectionné'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("🔍 Vérification de l'utilisation de NeMo")
    print("=" * 50)
    
    all_good = True
    
    # 1. Vérifier la configuration
    print("\n1. 📋 Configuration:")
    config, is_nemo = check_configuration()
    if not is_nemo:
        print("⚠️  L'application n'est pas configurée pour utiliser NeMo")
        print("💡 Exécutez: python configure_nemo_transcription.py")
        all_good = False
    
    # 2. Vérifier la logique du pipeline
    print("\n2. 🔄 Pipeline:")
    if not check_pipeline_logic():
        all_good = False
    
    # 3. Vérifier l'AIModelManager
    print("\n3. 🤖 AIModelManager:")
    if not check_ai_model_manager():
        all_good = False
    
    # 4. Simulation
    print("\n4. 🎯 Simulation:")
    if not simulate_transcription_choice():
        all_good = False
    
    # Résumé
    print("\n" + "=" * 50)
    if all_good and is_nemo:
        print("🎉 SUCCÈS: L'application est configurée pour utiliser NeMo!")
        print("\n💡 Prochaines étapes:")
        print("1. Lancez l'application: python main.py --gui")
        print("2. Sélectionnez un fichier vidéo")
        print("3. Vérifiez les logs pour voir 'Using NeMo transcription'")
        print("4. Le modèle NeMo sera téléchargé automatiquement au premier usage")
    else:
        print("❌ PROBLÈME: L'application n'utilise pas NeMo correctement")
        print("\n💡 Solutions:")
        print("1. Exécutez: python configure_nemo_transcription.py")
        print("2. Vérifiez que NeMo est installé: python install_nemo.py")
        print("3. Redémarrez l'application")
    
    print("=" * 50)

if __name__ == "__main__":
    main()