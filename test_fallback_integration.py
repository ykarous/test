"""
Test d'intégration du système de fallback avec les autres composants
"""
import asyncio
import tempfile
import os
from ai_video_dubbing.performance.fallback_system import IntelligentFallbackSystem
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface
from ai_video_dubbing.performance.download_manager import IntelligentDownloadManager

async def test_integrated_fallback_system():
    """Test d'intégration complète du système de fallback"""
    print("Test d'intégration du système de fallback...")
    
    # Créer les composants
    progress_interface = RealTimeProgressInterface()
    download_manager = IntelligentDownloadManager(progress_interface=progress_interface)
    fallback_system = IntelligentFallbackSystem(progress_interface)
    
    # Callbacks pour surveiller les événements
    events = []
    
    def progress_callback(event_type, data):
        events.append(f"Progress: {event_type} - {data.get('operation_id', 'N/A')}")
        print(f"📊 {event_type}: {data.get('current_message', data.get('message', 'N/A'))}")
    
    def fallback_callback(data):
        events.append(f"Fallback: {data['type']} - {data['message']}")
        print(f"🔄 {data['type']}: {data['message']}")
    
    # Configurer les callbacks
    progress_interface.add_ui_callback(progress_callback)
    progress_interface.add_notification_callback(progress_callback)
    fallback_system.add_notification_callback(fallback_callback)
    
    # Créer un fichier audio fictif
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio_file = temp_file.name
        temp_file.write(b"fake audio data for transcription")
    
    try:
        print(f"Fichier audio créé: {audio_file}")
        
        # Fonction de transcription intégrée qui utilise le download_manager
        async def integrated_transcription(audio_file: str, config):
            print(f"🎯 Transcription intégrée avec {config.model_type.value}")
            
            # Simuler le téléchargement du modèle si nécessaire
            model_url = f"https://example.com/models/{config.model_name}.bin"
            model_path = f"/tmp/{config.model_name}.bin"
            
            # Simuler différents scénarios selon le type de modèle
            if config.model_type.value == "nemo_gpu":
                # Simuler une erreur CUDA
                raise RuntimeError("CUDA out of memory")
            elif config.model_type.value == "nemo_light":
                # Simuler un téléchargement de modèle qui échoue
                print(f"📥 Tentative de téléchargement du modèle {config.model_name}...")
                await asyncio.sleep(0.1)
                raise FileNotFoundError(f"Model {config.model_name} not found")
            elif config.model_type.value == "whisper_gpu":
                # Simuler un timeout
                print(f"⏱️ Chargement du modèle {config.model_name}...")
                await asyncio.sleep(0.2)
                raise asyncio.TimeoutError("Model loading timeout")
            elif config.model_type.value == "nemo_cpu":
                # Celui-ci réussit après un "téléchargement"
                print(f"📥 Téléchargement simulé du modèle {config.model_name}...")
                await asyncio.sleep(0.1)
                print(f"🎵 Transcription avec {config.model_name}...")
                await asyncio.sleep(0.1)
                return f"Transcription réussie avec NeMo CPU: 'Bonjour, ceci est un test de transcription intégrée.'"
            else:
                # Fallback final
                print(f"🎵 Transcription rapide avec {config.model_name}...")
                await asyncio.sleep(0.05)
                return f"Transcription de fallback avec {config.model_type.value}: 'Hello, test.'"
        
        # Exécuter la transcription avec fallback
        print("\n🚀 Démarrage de la transcription avec fallback intégré...")
        
        success, result, used_config = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=integrated_transcription,
            max_attempts=6
        )
        
        print(f"\n=== Résultats de l'intégration ===")
        print(f"Succès: {'✅' if success else '❌'}")
        print(f"Résultat: {result}")
        print(f"Configuration utilisée: {used_config.model_type.value if used_config else 'Aucune'}")
        print(f"Événements capturés: {len(events)}")
        
        # Afficher quelques événements
        print("\n📋 Derniers événements:")
        for event in events[-5:]:
            print(f"  - {event}")
        
        # Statistiques des composants
        fallback_stats = fallback_system.get_stats()
        download_stats = download_manager.get_download_stats()
        progress_stats = progress_interface.get_global_statistics()
        
        print(f"\n📊 Statistiques:")
        print(f"  Fallback: {fallback_stats['total_attempts']} tentatives, {fallback_stats['successful_attempts']} succès")
        print(f"  Téléchargements: {download_stats['total_downloads']} total")
        print(f"  Progression: {progress_stats['total_operations']} opérations")
        
        # Test de la configuration recommandée
        recommended = await fallback_system.get_recommended_config()
        if recommended:
            print(f"  Configuration recommandée: {recommended.model_type.value}")
        
        if success:
            print("\n✅ Test d'intégration réussi")
        else:
            print("\n❌ Test d'intégration échoué")
    
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        await progress_interface.shutdown()

async def test_fallback_with_real_conditions():
    """Test du fallback avec des conditions système réelles"""
    print("\nTest du fallback avec conditions système réelles...")
    
    fallback_system = IntelligentFallbackSystem()
    
    # Obtenir les vraies informations système
    system_info = await fallback_system._get_system_info()
    print(f"💻 Système détecté:")
    print(f"  - Mémoire disponible: {system_info['available_memory_mb']} MB")
    print(f"  - CPU cores: {system_info['cpu_cores']}")
    print(f"  - CUDA disponible: {system_info['cuda_available']}")
    if system_info['cuda_available']:
        print(f"  - Mémoire CUDA: {system_info['cuda_memory_mb']} MB")
    
    # Analyser quelles configurations sont compatibles
    compatible_configs = []
    for config in fallback_system.fallback_chain:
        if config.meets_requirements(system_info):
            compatible_configs.append(config)
            print(f"✅ {config.model_type.value} - Compatible")
        else:
            print(f"❌ {config.model_type.value} - Non compatible")
    
    print(f"\n🎯 {len(compatible_configs)} configurations compatibles sur {len(fallback_system.fallback_chain)}")
    
    # Configuration recommandée
    recommended = await fallback_system.get_recommended_config()
    if recommended:
        print(f"🏆 Configuration recommandée: {recommended.model_type.value}")
        print(f"   - Qualité: {recommended.quality_score:.1f}")
        print(f"   - Vitesse: {recommended.speed_score:.1f}")
        print(f"   - Mémoire max: {recommended.max_memory_mb} MB")
        print(f"   - Device: {recommended.device}")
    
    print("✅ Test des conditions système terminé")

if __name__ == "__main__":
    asyncio.run(test_integrated_fallback_system())
    asyncio.run(test_fallback_with_real_conditions())