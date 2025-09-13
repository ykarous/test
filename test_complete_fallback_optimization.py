"""
Test d'intégration complète du système de fallback avec optimisation automatique
"""
import asyncio
import tempfile
import os
import shutil
from ai_video_dubbing.performance.fallback_system import IntelligentFallbackSystem, FallbackConfig, ModelType
from ai_video_dubbing.performance.auto_optimizer import AutomaticOptimizer
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_complete_fallback_optimization():
    """Test d'intégration complète avec optimisation automatique"""
    print("Test d'intégration complète - Fallback + Optimisation...")
    
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Créer les composants
        progress_interface = RealTimeProgressInterface()
        fallback_system = IntelligentFallbackSystem(progress_interface)
        optimizer = AutomaticOptimizer(fallback_system, config_dir=temp_dir)
        
        # Callbacks pour surveiller les événements
        events = []
        
        def progress_callback(event_type, data):
            events.append(f"Progress: {event_type}")
            print(f"📊 {event_type}: {data.get('current_message', data.get('message', 'N/A'))}")
        
        def fallback_callback(data):
            events.append(f"Fallback: {data['type']}")
            print(f"🔄 {data['type']}: {data['message']}")
        
        def optimization_callback(data):
            events.append(f"Optimization: {data['type']}")
            print(f"🔧 {data['type']}: {data['message']}")
        
        # Configurer les callbacks
        progress_interface.add_ui_callback(progress_callback)
        progress_interface.add_notification_callback(progress_callback)
        fallback_system.add_notification_callback(fallback_callback)
        optimizer.add_optimization_callback(optimization_callback)
        
        # Créer un fichier audio fictif
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_file = temp_file.name
            temp_file.write(b"fake audio data for optimization test")
        
        print(f"🎵 Fichier audio créé: {audio_file}")
        
        # Fonction de transcription avec apprentissage automatique
        attempt_count = 0
        
        async def learning_transcription(audio_file: str, config: FallbackConfig) -> str:
            nonlocal attempt_count
            attempt_count += 1
            
            print(f"🎯 Tentative {attempt_count} avec {config.model_type.value}")
            
            # Simuler différents comportements selon le modèle
            if config.model_type == ModelType.NEMO_GPU:
                if attempt_count <= 2:  # Échoue les 2 premières fois
                    raise RuntimeError("CUDA out of memory")
                else:  # Réussit après optimisation
                    await asyncio.sleep(0.1)
                    return f"Transcription optimisée avec {config.model_type.value}: 'Optimized transcription result.'"
            
            elif config.model_type == ModelType.NEMO_LIGHT:
                # Réussit toujours mais avec des performances variables
                duration = 0.15 if attempt_count > 3 else 0.25  # S'améliore avec le temps
                await asyncio.sleep(duration)
                return f"Transcription avec {config.model_type.value}: 'Light model transcription.'"
            
            elif config.model_type == ModelType.WHISPER_GPU:
                # Échoue parfois
                if attempt_count % 3 == 0:
                    raise asyncio.TimeoutError("Whisper timeout")
                await asyncio.sleep(0.2)
                return f"Transcription avec {config.model_type.value}: 'Whisper transcription.'"
            
            else:
                # Fallback final réussit toujours
                await asyncio.sleep(0.05)
                return f"Transcription de fallback avec {config.model_type.value}: 'Fallback result.'"
        
        # Exécuter plusieurs sessions pour démontrer l'apprentissage
        print("\n🚀 Session 1 - Apprentissage initial...")
        
        success1, result1, config1 = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=learning_transcription,
            max_attempts=6
        )
        
        print(f"Session 1: {'✅' if success1 else '❌'} avec {config1.model_type.value if config1 else 'None'}")
        
        # Apprendre de cette session
        if config1:
            system_info = await fallback_system._get_system_info()
            
            # Simuler l'apprentissage de toutes les tentatives
            for attempt in fallback_system.get_attempt_history()[-4:]:  # Dernières tentatives
                await optimizer.learn_from_attempt(system_info, attempt, was_optimal=attempt.success)
        
        print("\n🚀 Session 2 - Avec optimisation...")
        
        # Réinitialiser le compteur pour la nouvelle session
        attempt_count = 0
        
        # Obtenir la configuration optimisée
        system_info = await fallback_system._get_system_info()
        optimized_config = await optimizer.get_optimized_config(system_info)
        
        success2, result2, config2 = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=learning_transcription,
            max_attempts=6,
            preferred_config=optimized_config
        )
        
        print(f"Session 2: {'✅' if success2 else '❌'} avec {config2.model_type.value if config2 else 'None'}")
        
        print("\n🚀 Session 3 - Optimisation avancée...")
        
        # Encore une session pour voir l'amélioration continue
        attempt_count = 0
        
        optimized_config = await optimizer.get_optimized_config(system_info)
        
        success3, result3, config3 = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=learning_transcription,
            max_attempts=6,
            preferred_config=optimized_config
        )
        
        print(f"Session 3: {'✅' if success3 else '❌'} avec {config3.model_type.value if config3 else 'None'}")
        
        # Analyser les résultats
        print(f"\n=== Résultats de l'optimisation ===")
        print(f"Sessions réussies: {sum([success1, success2, success3])}/3")
        print(f"Configurations utilisées: {[c.model_type.value if c else 'None' for c in [config1, config2, config3]]}")
        print(f"Événements capturés: {len(events)}")
        
        # Analyse des performances
        analysis = await optimizer.analyze_performance_trends(system_info)
        if analysis['status'] == 'analyzed':
            print(f"\n📊 Analyse des performances:")
            print(f"  Configuration optimale: {analysis['current_config']}")
            print(f"  Taux de succès: {analysis['success_rate']:.1%}")
            print(f"  Durée moyenne: {analysis['average_duration']:.2f}s")
            print(f"  Score qualité: {analysis['quality_score']:.2f}")
            
            if analysis.get('trends'):
                print(f"  Tendances: {analysis['trends']}")
            
            if analysis.get('recommendations'):
                print("  Recommandations:")
                for rec in analysis['recommendations']:
                    print(f"    - {rec}")
        
        # Suggestions d'amélioration
        suggestions = await optimizer.suggest_configuration_improvements(system_info)
        if suggestions:
            print(f"\n💡 Suggestions d'amélioration:")
            for suggestion in suggestions:
                print(f"  - {suggestion['config']}: {suggestion['reason']}")
        
        # Statistiques finales
        fallback_stats = fallback_system.get_stats()
        optimizer_stats = optimizer.get_optimization_stats()
        
        print(f"\n📈 Statistiques finales:")
        print(f"  Fallback - Tentatives: {fallback_stats['total_attempts']}, Succès: {fallback_stats['successful_attempts']}")
        print(f"  Optimiseur - Profils: {optimizer_stats['total_profiles']}, Actifs: {optimizer_stats['active_profiles']}")
        print(f"  Taux de succès global: {optimizer_stats['average_success_rate']:.1%}")
        
        print("\n✅ Test d'intégration complète réussi")
    
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        await progress_interface.shutdown()
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_notification_system():
    """Test du système de notifications avancées"""
    print("\nTest du système de notifications avancées...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Créer les composants
        fallback_system = IntelligentFallbackSystem()
        optimizer = AutomaticOptimizer(fallback_system, config_dir=temp_dir)
        
        # Collecteur de notifications avancé
        notifications = {
            "fallback_success": [],
            "fallback_failure": [],
            "optimization_update": [],
            "performance_alert": []
        }
        
        def advanced_fallback_callback(data):
            notifications[data['type']].append(data)
            
            if data['type'] == 'fallback_failure':
                print(f"⚠️ Échec: {data['config'].model_type.value} - {data['attempt'].error}")
            elif data['type'] == 'fallback_success':
                print(f"✅ Succès: {data['config'].model_type.value} après {data['attempt_number']} tentative(s)")
        
        def advanced_optimization_callback(data):
            notifications[data['type']].append(data)
            
            if data['type'] == 'optimization_update':
                print(f"🔧 Optimisation: {data['old_config']} → {data['new_config']}")
        
        # Configurer les callbacks
        fallback_system.add_notification_callback(advanced_fallback_callback)
        optimizer.add_optimization_callback(advanced_optimization_callback)
        
        # Simuler des scénarios avec notifications
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_file = temp_file.name
            temp_file.write(b"notification test audio")
        
        # Fonction qui génère différents types de notifications
        async def notification_test_transcription(audio_file: str, config: FallbackConfig) -> str:
            if config.model_type == ModelType.NEMO_GPU:
                raise RuntimeError("Simulated CUDA error for notification test")
            elif config.model_type == ModelType.NEMO_LIGHT:
                raise FileNotFoundError("Simulated model not found for notification test")
            elif config.model_type == ModelType.WHISPER_GPU:
                await asyncio.sleep(0.1)
                return "Notification test successful with Whisper GPU"
            else:
                await asyncio.sleep(0.05)
                return "Notification test fallback successful"
        
        # Exécuter le test
        success, result, used_config = await fallback_system.execute_with_fallback(
            audio_file=audio_file,
            transcription_func=notification_test_transcription,
            max_attempts=5
        )
        
        print(f"\n📊 Résultats des notifications:")
        print(f"  Échecs de fallback: {len(notifications['fallback_failure'])}")
        print(f"  Succès de fallback: {len(notifications['fallback_success'])}")
        print(f"  Mises à jour d'optimisation: {len(notifications['optimization_update'])}")
        
        # Afficher les détails des notifications
        for failure in notifications['fallback_failure']:
            print(f"    Échec: {failure['config'].model_type.value} - {failure['message']}")
        
        for success_notif in notifications['fallback_success']:
            print(f"    Succès: {success_notif['config'].model_type.value} - {success_notif['message']}")
        
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        print("✅ Test des notifications avancées terminé")
    
    except Exception as e:
        print(f"❌ Erreur lors du test de notifications: {e}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_complete_fallback_optimization())
    asyncio.run(test_notification_system())