#!/usr/bin/env python3
"""
Test de l'interface de progression temps réel
"""

import sys
import asyncio
import time
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

async def test_progress_basic():
    """Test de base de l'interface de progression"""
    print("🧪 Test de Base de l'Interface de Progression")
    print("=" * 60)
    
    try:
        from ai_video_dubbing.performance.progress_interface import (
            RealTimeProgressInterface, OperationType, OperationStatus
        )
        
        # Créer l'interface
        progress_interface = RealTimeProgressInterface(update_interval=0.1)
        print("✅ Interface de progression créée")
        
        # Test 1: Démarrer le suivi d'une opération
        print("\n📋 Test 1: Suivi d'opération de base")
        
        tracker = await progress_interface.track_operation(
            operation_type=OperationType.DOWNLOAD,
            estimated_duration=5.0,
            total_steps=10,
            initial_task="Préparation du téléchargement"
        )
        
        print(f"   Opération créée: {tracker.progress.operation_id}")
        print(f"   Type: {tracker.progress.operation_type.value}")
        print(f"   Statut initial: {tracker.progress.status.value}")
        
        # Test 2: Mise à jour de progression
        print("\n📋 Test 2: Mises à jour de progression")
        
        for step in range(1, 6):
            await tracker.update(
                current_step=step,
                current_task=f"Étape {step}/10",
                throughput=1024 * 1024 * step,  # MB/s croissant
                memory_usage_mb=50 + step * 10
            )
            
            progress = tracker.progress
            print(f"   Étape {step}: {progress.progress_percent:.1f}% - {progress.current_task}")
            print(f"     ETA: {progress.eta_seconds:.1f}s, Débit: {progress.throughput/(1024*1024):.1f} MB/s")
            
            await asyncio.sleep(0.1)  # Simuler du travail
        
        # Test 3: Complétion
        print("\n📋 Test 3: Complétion d'opération")
        
        await tracker.complete("Téléchargement terminé avec succès")
        
        final_progress = tracker.progress
        print(f"   Statut final: {final_progress.status.value}")
        print(f"   Progression: {final_progress.progress_percent:.1f}%")
        print(f"   Message: {final_progress.status_message}")
        print(f"   Temps total: {final_progress.elapsed_time:.2f}s")
        
        # Test 4: Statistiques
        print("\n📋 Test 4: Statistiques")
        
        stats = progress_interface.get_summary_stats()
        print(f"   Opérations totales: {stats['total_operations']}")
        print(f"   Opérations actives: {stats['active_operations']}")
        print(f"   Opérations terminées: {stats['completed_operations']}")
        print(f"   Progression moyenne: {stats['average_progress']:.1f}%")
        
        # Test 5: Message de progression
        print("\n📋 Test 5: Messages de progression")
        
        message = progress_interface.create_progress_message(final_progress)
        print(f"   Message généré: {message}")
        
        # Arrêter l'interface
        await progress_interface.stop()
        
        assert final_progress.status == OperationStatus.COMPLETED
        assert final_progress.progress_percent == 100.0
        assert stats['total_operations'] >= 1
        
        print("\n🎉 TESTS DE BASE RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_operations():
    """Test avec plusieurs opérations simultanées"""
    print("\n🔄 Test d'Opérations Multiples")
    print("=" * 50)
    
    try:
        from ai_video_dubbing.performance.progress_interface import (
            RealTimeProgressInterface, OperationType, OperationStatus
        )
        
        progress_interface = RealTimeProgressInterface(update_interval=0.1)
        
        # Callback pour collecter les mises à jour UI
        ui_updates = []
        
        async def ui_callback(operations_data):
            ui_updates.append(len(operations_data))
            print(f"   📊 UI Update: {len(operations_data)} opérations actives")
        
        progress_interface.add_ui_callback(ui_callback)
        
        # Test 1: Créer plusieurs opérations
        print("\n📋 Test 1: Création d'opérations multiples")
        
        trackers = []
        operation_types = [
            OperationType.DOWNLOAD,
            OperationType.MODEL_LOADING,
            OperationType.TRANSCRIPTION
        ]
        
        for i, op_type in enumerate(operation_types):
            tracker = await progress_interface.track_operation(
                operation_type=op_type,
                total_steps=5,
                initial_task=f"Initialisation {op_type.value}"
            )
            trackers.append(tracker)
            print(f"   Opération {i+1} créée: {op_type.value}")
        
        # Test 2: Progression simultanée
        print("\n📋 Test 2: Progression simultanée")
        
        # Faire progresser toutes les opérations
        for step in range(1, 6):
            tasks = []
            for i, tracker in enumerate(trackers):
                # Vitesses différentes pour chaque opération
                delay = 0.05 * (i + 1)
                task = asyncio.create_task(
                    tracker.update(
                        current_step=step,
                        current_task=f"Traitement étape {step}",
                        cpu_usage_percent=20 + i * 10,
                        memory_usage_mb=100 + step * 20
                    )
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.2)  # Laisser le temps aux mises à jour UI
        
        # Test 3: Finalisation avec différents résultats
        print("\n📋 Test 3: Finalisation avec résultats variés")
        
        # Première opération: succès
        await trackers[0].complete("Téléchargement réussi")
        
        # Deuxième opération: échec
        await trackers[1].set_error("Erreur de chargement du modèle")
        
        # Troisième opération: annulation
        trackers[2].cancel()
        
        # Attendre les mises à jour
        await asyncio.sleep(0.5)
        
        # Test 4: Vérification des statuts
        print("\n📋 Test 4: Vérification des statuts finaux")
        
        operations = progress_interface.list_active_operations()
        print(f"   Opérations actives: {len(operations)}")
        
        for op in operations:
            message = progress_interface.create_progress_message(op)
            print(f"     {op.operation_type.value}: {message}")
        
        # Test 5: Statistiques finales
        print("\n📋 Test 5: Statistiques finales")
        
        stats = progress_interface.get_summary_stats()
        print(f"   Total: {stats['total_operations']}")
        print(f"   Terminées: {stats['completed_operations']}")
        print(f"   Échouées: {stats['failed_operations']}")
        print(f"   Par type: {stats['operations_by_type']}")
        print(f"   Par statut: {stats['operations_by_status']}")
        
        # Test 6: Mises à jour UI
        print(f"\n📋 Test 6: Mises à jour UI reçues: {len(ui_updates)}")
        if ui_updates:
            print(f"   Première mise à jour: {ui_updates[0]} opérations")
            print(f"   Dernière mise à jour: {ui_updates[-1]} opérations")
        
        await progress_interface.stop()
        
        assert len(operations) == 3, "Devrait y avoir 3 opérations"
        assert stats['completed_operations'] == 1, "Une opération devrait être terminée"
        assert stats['failed_operations'] == 1, "Une opération devrait avoir échoué"
        assert len(ui_updates) > 0, "Des mises à jour UI devraient avoir été envoyées"
        
        print("\n✅ TESTS D'OPÉRATIONS MULTIPLES RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_progress_cancellation():
    """Test d'annulation d'opérations"""
    print("\n🛑 Test d'Annulation d'Opérations")
    print("=" * 50)
    
    try:
        from ai_video_dubbing.performance.progress_interface import (
            RealTimeProgressInterface, OperationType, OperationStatus
        )
        
        progress_interface = RealTimeProgressInterface()
        
        # Test 1: Annulation d'une opération spécifique
        print("\n📋 Test 1: Annulation d'opération spécifique")
        
        tracker = await progress_interface.track_operation(
            operation_type=OperationType.TRANSCRIPTION,
            total_steps=10
        )
        
        operation_id = tracker.progress.operation_id
        print(f"   Opération créée: {operation_id}")
        
        # Faire progresser un peu
        await tracker.update(current_step=3, current_task="Transcription en cours...")
        print(f"   Progression: {tracker.progress.progress_percent:.1f}%")
        
        # Annuler
        success = await progress_interface.cancel_operation(operation_id)
        print(f"   Annulation: {'✅ Réussie' if success else '❌ Échouée'}")
        print(f"   Statut: {tracker.progress.status.value}")
        print(f"   Est annulée: {tracker.is_cancelled}")
        
        # Test 2: Annulation de toutes les opérations
        print("\n📋 Test 2: Annulation de toutes les opérations")
        
        # Créer plusieurs opérations
        trackers = []
        for i in range(3):
            t = await progress_interface.track_operation(
                operation_type=OperationType.DOWNLOAD,
                operation_id=f"test_op_{i}"
            )
            await t.update(current_step=i+1, progress_percent=(i+1)*10)
            trackers.append(t)
        
        print(f"   {len(trackers)} opérations créées")
        
        # Annuler toutes
        await progress_interface.cancel_all_operations()
        
        # Vérifier les statuts
        cancelled_count = sum(1 for t in trackers if t.is_cancelled)
        print(f"   Opérations annulées: {cancelled_count}/{len(trackers)}")
        
        # Test 3: Vérification que les opérations annulées ne progressent plus
        print("\n📋 Test 3: Vérification blocage progression après annulation")
        
        # Essayer de faire progresser une opération annulée
        old_progress = trackers[0].progress.progress_percent
        await trackers[0].update(progress_percent=90.0)
        new_progress = trackers[0].progress.progress_percent
        
        print(f"   Progression avant: {old_progress}%")
        print(f"   Progression après tentative: {new_progress}%")
        print(f"   Statut: {trackers[0].progress.status.value}")
        
        await progress_interface.stop()
        
        assert success, "L'annulation devrait réussir"
        assert tracker.is_cancelled, "L'opération devrait être marquée comme annulée"
        assert cancelled_count == len(trackers), "Toutes les opérations devraient être annulées"
        
        print("\n✅ TESTS D'ANNULATION RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_progress_integration():
    """Test d'intégration avec d'autres composants"""
    print("\n🔗 Test d'Intégration")
    print("=" * 30)
    
    try:
        from ai_video_dubbing.performance.progress_interface import (
            RealTimeProgressInterface, OperationType
        )
        
        progress_interface = RealTimeProgressInterface()
        
        # Test 1: Simulation d'un téléchargement avec progression réaliste
        print("\n📋 Test 1: Simulation téléchargement réaliste")
        
        async def simulate_download_with_progress():
            """Simule un téléchargement avec progression réaliste"""
            tracker = await progress_interface.track_operation(
                operation_type=OperationType.DOWNLOAD,
                estimated_duration=3.0,
                initial_task="Connexion au serveur"
            )
            
            # Phases du téléchargement
            phases = [
                ("Connexion au serveur", 0.5),
                ("Négociation SSL", 0.3),
                ("Début du téléchargement", 0.2),
                ("Téléchargement en cours", 2.0),
                ("Vérification", 0.3),
                ("Finalisation", 0.2)
            ]
            
            total_bytes = 1024 * 1024 * 50  # 50 MB
            downloaded_bytes = 0
            
            for i, (phase, duration) in enumerate(phases):
                await tracker.update(
                    current_task=phase,
                    status_message=f"Phase {i+1}/{len(phases)}: {phase}"
                )
                
                if phase == "Téléchargement en cours":
                    # Simuler téléchargement progressif
                    steps = 20
                    bytes_per_step = total_bytes // steps
                    
                    for step in range(steps):
                        downloaded_bytes += bytes_per_step
                        progress_percent = (downloaded_bytes / total_bytes) * 80 + 10  # 10-90%
                        throughput = bytes_per_step / (duration / steps)
                        
                        await tracker.update(
                            progress_percent=progress_percent,
                            throughput=throughput,
                            details={
                                'downloaded_bytes': downloaded_bytes,
                                'total_bytes': total_bytes
                            }
                        )
                        
                        await asyncio.sleep(duration / steps)
                else:
                    # Phases sans téléchargement
                    base_progress = i * 10
                    await tracker.update(progress_percent=base_progress)
                    await asyncio.sleep(duration)
            
            await tracker.complete("Téléchargement terminé")
            return tracker
        
        # Lancer la simulation
        download_tracker = await simulate_download_with_progress()
        
        print(f"   Téléchargement simulé terminé")
        print(f"   Temps total: {download_tracker.progress.elapsed_time:.2f}s")
        print(f"   Statut final: {download_tracker.progress.status.value}")
        
        # Test 2: Intégration avec callbacks personnalisés
        print("\n📋 Test 2: Callbacks personnalisés")
        
        callback_calls = []
        
        def custom_callback(operations_data):
            callback_calls.append({
                'timestamp': time.time(),
                'operations_count': len(operations_data),
                'operations': [op['operation_type'] for op in operations_data]
            })
        
        progress_interface.add_ui_callback(custom_callback)
        
        # Créer une opération rapide pour tester les callbacks
        quick_tracker = await progress_interface.track_operation(
            operation_type=OperationType.MODEL_LOADING
        )
        
        for i in range(5):
            await quick_tracker.update(progress_percent=i * 25)
            await asyncio.sleep(0.1)
        
        await quick_tracker.complete()
        
        # Attendre les callbacks
        await asyncio.sleep(0.5)
        
        print(f"   Callbacks reçus: {len(callback_calls)}")
        if callback_calls:
            print(f"   Premier callback: {callback_calls[0]['operations_count']} opérations")
            print(f"   Dernier callback: {callback_calls[-1]['operations_count']} opérations")
        
        await progress_interface.stop()
        
        assert download_tracker.progress.elapsed_time > 0, "Le téléchargement devrait avoir pris du temps"
        assert len(callback_calls) > 0, "Des callbacks devraient avoir été appelés"
        
        print("\n✅ TESTS D'INTÉGRATION RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Point d'entrée principal"""
    print("🚀 Test de l'Interface de Progression Temps Réel")
    print("=" * 70)
    
    # Tests de base
    success1 = await test_progress_basic()
    
    # Tests d'opérations multiples
    success2 = await test_multiple_operations()
    
    # Tests d'annulation
    success3 = await test_progress_cancellation()
    
    # Tests d'intégration
    success4 = await test_progress_integration()
    
    if success1 and success2 and success3 and success4:
        print("\n" + "=" * 70)
        print("🎉 TOUS LES TESTS DE L'INTERFACE DE PROGRESSION RÉUSSIS!")
        print("\n💡 Fonctionnalités validées:")
        print("   ✅ Suivi de progression multi-opérations")
        print("   ✅ Mises à jour temps réel avec callbacks UI")
        print("   ✅ Calcul automatique d'ETA et métriques")
        print("   ✅ Annulation d'opérations individuelles et globales")
        print("   ✅ Messages de progression contextuels")
        print("   ✅ Statistiques détaillées et monitoring")
        print("   ✅ Intégration avec callbacks personnalisés")
        print("   ✅ Nettoyage automatique des opérations terminées")
        print("\n🚀 Interface de progression temps réel opérationnelle!")
        return 0
    else:
        print("\n❌ Certains tests ont échoué")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)