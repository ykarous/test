"""
Test du système de fallback intelligent
"""
import asyncio
import tempfile
import os
from ai_video_dubbing.performance.fallback_system import (
    IntelligentFallbackSystem, FallbackConfig, ModelType, FallbackReason
)
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_fallback_system():
    """Test basique du système de fallback"""
    print("Test du système de fallback intelligent...")
    
    # Créer l'interface de progression
    progress_interface = RealTimeProgressInterface()
    
    # Créer le système de fallback
    fallback_system = IntelligentFallbackSystem(progress_interface)
    
    # Callback de notification
    notifications = []
    
    def notification_callback(data):
        notifications.append(data)
        print(f"Notification: {data['type']} - {data['message']}")
    
    fallback_system.add_notification_callback(notification_callback)
    
    # Créer un fichier audio fictif
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio_file = temp_file.name
        temp_file.write(b"fake audio data")
    
    try:
        # Fonction de transcription simulée qui échoue parfois
        attempt_count = 0
        
        async def mock_transcription(audio_file: str, config: FallbackConfig) -> str:
            nonlocal attempt_count
            attempt_count += 1
            
            print(f"Tentative de transcription avec {config.model_type.value}")
            
            # Simuler différents types d'échecs selon le modèle
            if config.model_type == ModelType.NEMO_GPU:
                # Simuler une erreur CUDA
                raise RuntimeError("CUDA out of memory")
            elif config.model_type == ModelType.NEMO_LIGHT:
                # Simuler une erreur de chargement de modèle
                raise FileNotFoundError("Model file not found")
            elif config.model_type == ModelType.WHISPER_GPU:
                # Simuler un timeout
                await asyncio.sleep(0.1)
                raise asyncio.TimeoutError("Operation timed out")
            elif config.model_type == ModelType.NEMO_CPU:
                # Celui-ci réussit
                await asyncio.sleep(0.05)
                return f"Transcription réussie avec {config.model_type.value}: 'Hello, this is a test transcription.'"
            else:
                # Fallback final réussit toujours
                await asyncio.sleep(0.02)
                return f"Transcription de fallback avec {config.model_type.value}: 'Hello, test.'"
        
        # Exécuter avec fallback
        success, result, used_config = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=mock_transcription,
            max_attempts=None
        )
        
        print(f"\n=== Résultats ===")
        print(f"Succès: {success}")
        print(f"Résultat: {result}")
        print(f"Configuration utilisée: {used_config.model_type.value if used_config else None}")
        print(f"Notifications reçues: {len(notifications)}")
        
        # Statistiques
        stats = fallback_system.get_stats()
        print(f"Statistiques: {stats}")
        
        # Historique
        history = fallback_system.get_attempt_history()
        print(f"Tentatives dans l'historique: {len(history)}")
        for i, attempt in enumerate(history):
            print(f"  {i+1}. {attempt.config.model_type.value}: "
                  f"{'✅' if attempt.success else '❌'} "
                  f"({attempt.duration:.2f}s)")
            if attempt.error:
                print(f"     Erreur: {attempt.error}")
        
        if success:
            print("✅ Test de fallback réussi")
        else:
            print("❌ Test de fallback échoué")
    
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        await progress_interface.shutdown()

async def test_specific_fallbacks():
    """Test des méthodes de fallback spécifiques"""
    print("\nTest des méthodes de fallback spécifiques...")
    
    fallback_system = IntelligentFallbackSystem()
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio_file = temp_file.name
        temp_file.write(b"fake audio data")
    
    try:
        # Test NeMo Light
        print("Test NeMo Light...")
        success, result = await fallback_system.try_nemo_light(audio_file)
        print(f"NeMo Light: {'✅' if success else '❌'} - {result}")
        
        # Test NeMo CPU
        print("Test NeMo CPU...")
        success, result = await fallback_system.try_nemo_cpu(audio_file)
        print(f"NeMo CPU: {'✅' if success else '❌'} - {result}")
        
        # Test Whisper
        print("Test Whisper...")
        success, result = await fallback_system.try_whisper(audio_file, "base")
        print(f"Whisper: {'✅' if success else '❌'} - {result}")
        
        # Test Whisper Tiny
        print("Test Whisper Tiny...")
        success, result = await fallback_system.try_whisper(audio_file, "tiny")
        print(f"Whisper Tiny: {'✅' if success else '❌'} - {result}")
        
        print("✅ Tests spécifiques terminés")
    
    except Exception as e:
        print(f"❌ Erreur lors des tests spécifiques: {e}")
    
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

async def test_system_requirements():
    """Test de la vérification des exigences système"""
    print("\nTest de la vérification des exigences système...")
    
    fallback_system = IntelligentFallbackSystem()
    
    # Obtenir les informations système réelles
    system_info = await fallback_system._get_system_info()
    print(f"Informations système: {system_info}")
    
    # Tester chaque configuration
    for config in fallback_system.fallback_chain:
        meets_req = config.meets_requirements(system_info)
        print(f"{config.model_type.value}: {'✅' if meets_req else '❌'} "
              f"(mémoire: {config.max_memory_mb}MB, device: {config.device})")
    
    # Configuration recommandée
    recommended = fallback_system.get_recommended_config()
    if recommended:
        print(f"Configuration recommandée: {recommended.model_type.value}")
    else:
        print("Aucune configuration recommandée")
    
    print("✅ Test des exigences système terminé")

async def test_performance_optimization():
    """Test d'optimisation automatique des paramètres"""
    print("\nTest d'optimisation automatique...")
    
    fallback_system = IntelligentFallbackSystem()
    
    # Simuler plusieurs exécutions pour collecter des données
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio_file = temp_file.name
        temp_file.write(b"fake audio data")
    
    try:
        # Fonction de transcription qui réussit toujours avec le dernier fallback
        async def always_succeed_last(audio_file: str, config: FallbackConfig) -> str:
            if config.model_type in [ModelType.WHISPER_CPU, ModelType.WHISPER_TINY]:
                return f"Success with {config.model_type.value}"
            else:
                raise RuntimeError(f"Simulated failure with {config.model_type.value}")
        
        # Exécuter plusieurs fois pour collecter des statistiques
        for i in range(3):
            print(f"Exécution {i+1}/3...")
            success, result, used_config = await fallback_system.execute_with_fallback(
                audio_file=audio_file,
                transcription_func=always_succeed_last,
                max_attempts=6
            )
            print(f"  Résultat: {'✅' if success else '❌'} avec {used_config.model_type.value if used_config else 'None'}")
        
        # Analyser les statistiques
        stats = fallback_system.get_stats()
        print(f"\n=== Statistiques d'optimisation ===")
        print(f"Tentatives totales: {stats['total_attempts']}")
        print(f"Succès: {stats['successful_attempts']}")
        print(f"Temps moyen: {stats['average_fallback_time']:.2f}s")
        print(f"Usage par modèle: {stats['fallback_usage']}")
        print(f"Erreurs communes: {stats['common_errors']}")
        
        print("✅ Test d'optimisation terminé")
    
    except Exception as e:
        print(f"❌ Erreur lors du test d'optimisation: {e}")
    
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    asyncio.run(test_fallback_system())
    asyncio.run(test_specific_fallbacks())
    asyncio.run(test_system_requirements())
    asyncio.run(test_performance_optimization())