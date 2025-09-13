"""Test d'intégration complet pour l'AIModelManager amélioré"""
import asyncio
import tempfile
import time
from pathlib import Path

from ai_video_dubbing.processors.unified_async_interface import (
    UnifiedAsyncInterface, OperationType, OperationStatus
)

async def test_unified_async_interface():
    """Test de l'interface asynchrone unifiée"""
    
    print("🚀 Test de l'interface asynchrone unifiée")
    print("=" * 50)
    
    interface = UnifiedAsyncInterface()
    
    # Test des callbacks
    progress_updates = []
    completion_results = []
    status_changes = []
    
    def progress_callback(progress):
        progress_updates.append(progress)
        print(f"📊 Progression: {progress.operation_id} - {progress.progress_percent:.1f}% - {progress.current_step}")
    
    def completion_callback(result):
        completion_results.append(result)
        print(f"✅ Terminé: {result.operation_id} - {'Succès' if result.success else 'Échec'}")
    
    def status_change_callback(operation_id, status):
        status_changes.append((operation_id, status))
        print(f"🔄 Changement de statut: {operation_id} -> {status.value}")
    
    interface.add_progress_callback(progress_callback)
    interface.add_completion_callback(completion_callback)
    interface.add_status_change_callback(status_change_callback)
    
    print("✅ Callbacks configurés")
    
    # Test d'opération simple
    async def simple_operation(progress_callback):
        """Opération de test simple"""
        await progress_callback(progress_percent=10, current_step="Initialisation")
        await asyncio.sleep(0.1)
        
        await progress_callback(progress_percent=50, current_step="Traitement")
        await asyncio.sleep(0.1)
        
        await progress_callback(progress_percent=90, current_step="Finalisation")
        await asyncio.sleep(0.1)
        
        return {"result": "success", "data": "test_data"}
    
    # Démarrer l'opération
    operation_id = await interface.start_operation(
        operation_type=OperationType.TRANSCRIPTION,
        operation_func=simple_operation,
        estimated_duration=1.0,
        metadata={"test": True}
    )
    
    print(f"✅ Opération démarrée: {operation_id}")
    
    # Attendre la completion
    await asyncio.sleep(1)
    
    # Vérifier les résultats
    assert len(completion_results) > 0, "Au moins un résultat de completion attendu"
    assert len(progress_updates) > 0, "Au moins une mise à jour de progression attendue"
    assert len(status_changes) > 0, "Au moins un changement de statut attendu"
    
    print(f"✅ Callbacks vérifiés: {len(progress_updates)} progressions, {len(completion_results)} completions")
    
    # Test des statistiques
    stats = interface.get_operation_statistics()
    print("📊 Statistiques des opérations:")
    print(f"  - Total: {stats['total_operations']}")
    print(f"  - Actives: {stats['active_operations']}")
    print(f"  - Terminées: {stats['completed_operations']}")
    print(f"  - Par type: {stats['by_type']}")
    
    # Test d'opération avec erreur
    async def failing_operation(progress_callback):
        """Opération qui échoue"""
        await progress_callback(progress_percent=20, current_step="Démarrage")
        await asyncio.sleep(0.1)
        raise Exception("Test d'erreur")
    
    error_operation_id = await interface.start_operation(
        operation_type=OperationType.DIAGNOSTIC,
        operation_func=failing_operation
    )
    
    await asyncio.sleep(0.5)
    
    # Vérifier que l'erreur a été gérée
    error_results = [r for r in completion_results if not r.success]
    assert len(error_results) > 0, "Au moins un résultat d'erreur attendu"
    
    print("✅ Gestion d'erreur vérifiée")
    
    # Test d'annulation
    async def long_operation(progress_callback):
        """Opération longue pour tester l'annulation"""
        for i in range(100):
            await progress_callback(progress_percent=i, current_step=f"Étape {i}")
            await asyncio.sleep(0.01)
        return "completed"
    
    cancel_operation_id = await interface.start_operation(
        operation_type=OperationType.OPTIMIZATION,
        operation_func=long_operation
    )
    
    # Attendre un peu puis annuler
    await asyncio.sleep(0.1)
    cancelled = await interface.cancel_operation(cancel_operation_id)
    
    assert cancelled, "L'annulation devrait réussir"
    print("✅ Annulation d'opération vérifiée")
    
    # Test de l'historique
    history = interface.get_operation_history()
    print(f"📚 Historique: {len(history)} opérations")
    
    # Test par type
    transcription_ops = interface.get_operations_by_type(OperationType.TRANSCRIPTION)
    print(f"🎤 Opérations de transcription: {len(transcription_ops)}")
    
    # Fermeture
    await interface.shutdown()
    print("✅ Interface fermée proprement")

async def test_integration_workflow():
    """Test du workflow d'intégration complet"""
    
    print("\n🔗 Test du workflow d'intégration complet")
    print("=" * 45)
    
    interface = UnifiedAsyncInterface()
    
    # Simuler un workflow de transcription complet
    workflow_steps = []
    
    async def step_1_validation(progress_callback):
        """Étape 1: Validation du fichier audio"""
        await progress_callback(progress_percent=10, current_step="Vérification du fichier")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=50, current_step="Analyse des métadonnées")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=100, current_step="Validation terminée")
        workflow_steps.append("validation")
        return {"valid": True, "duration": 120}
    
    async def step_2_model_selection(progress_callback):
        """Étape 2: Sélection du modèle optimal"""
        await progress_callback(progress_percent=20, current_step="Analyse des ressources")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=60, current_step="Sélection du modèle")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=100, current_step="Modèle sélectionné")
        workflow_steps.append("model_selection")
        return {"model": "whisper-base", "confidence": 0.9}
    
    async def step_3_transcription(progress_callback):
        """Étape 3: Transcription"""
        await progress_callback(progress_percent=5, current_step="Chargement du modèle")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=30, current_step="Transcription en cours")
        await asyncio.sleep(0.1)
        
        await progress_callback(progress_percent=80, current_step="Post-traitement")
        await asyncio.sleep(0.05)
        
        await progress_callback(progress_percent=100, current_step="Transcription terminée")
        workflow_steps.append("transcription")
        return {"text": "Transcription simulée réussie", "confidence": 0.95}
    
    # Exécuter le workflow
    print("🔄 Exécution du workflow de transcription...")
    
    # Étape 1
    validation_id = await interface.start_operation(
        operation_type=OperationType.MODEL_VALIDATION,
        operation_func=step_1_validation,
        metadata={"step": 1, "name": "validation"}
    )
    
    # Attendre la completion de l'étape 1
    while validation_id in interface.active_operations:
        await asyncio.sleep(0.01)
    
    # Étape 2
    selection_id = await interface.start_operation(
        operation_type=OperationType.OPTIMIZATION,
        operation_func=step_2_model_selection,
        metadata={"step": 2, "name": "model_selection"}
    )
    
    # Attendre la completion de l'étape 2
    while selection_id in interface.active_operations:
        await asyncio.sleep(0.01)
    
    # Étape 3
    transcription_id = await interface.start_operation(
        operation_type=OperationType.TRANSCRIPTION,
        operation_func=step_3_transcription,
        metadata={"step": 3, "name": "transcription"}
    )
    
    # Attendre la completion de l'étape 3
    while transcription_id in interface.active_operations:
        await asyncio.sleep(0.01)
    
    # Vérifier que toutes les étapes ont été exécutées
    expected_steps = ["validation", "model_selection", "transcription"]
    assert workflow_steps == expected_steps, f"Workflow incomplet: {workflow_steps} vs {expected_steps}"
    
    print("✅ Workflow de transcription complet exécuté")
    print(f"  - Étapes: {' -> '.join(workflow_steps)}")
    
    # Vérifier les statistiques finales
    final_stats = interface.get_operation_statistics()
    print(f"📊 Statistiques finales: {final_stats['total_operations']} opérations")
    
    await interface.shutdown()

async def test_concurrent_operations():
    """Test des opérations concurrentes"""
    
    print("\n⚡ Test des opérations concurrentes")
    print("=" * 35)
    
    interface = UnifiedAsyncInterface()
    
    # Créer plusieurs opérations concurrentes
    async def concurrent_operation(operation_id, duration):
        """Opération concurrente"""
        async def operation(progress_callback):
            steps = 10
            for i in range(steps):
                progress = (i + 1) / steps * 100
                await progress_callback(
                    progress_percent=progress,
                    current_step=f"Étape {i+1}/{steps}"
                )
                await asyncio.sleep(duration / steps)
            return f"Result from {operation_id}"
        
        return await interface.start_operation(
            operation_type=OperationType.TRANSCRIPTION,
            operation_func=operation,
            metadata={"concurrent_test": True, "operation_id": operation_id}
        )
    
    # Démarrer plusieurs opérations
    operation_ids = []
    for i in range(3):
        op_id = await concurrent_operation(f"op_{i}", 0.2)
        operation_ids.append(op_id)
        print(f"✅ Opération {i+1} démarrée: {op_id}")
    
    # Attendre que toutes se terminent
    start_time = time.time()
    while any(op_id in interface.active_operations for op_id in operation_ids):
        await asyncio.sleep(0.01)
    
    execution_time = time.time() - start_time
    print(f"✅ {len(operation_ids)} opérations concurrentes terminées en {execution_time:.2f}s")
    
    # Vérifier que les opérations ont bien été exécutées en parallèle
    # (le temps total devrait être proche de la durée d'une opération, pas de la somme)
    assert execution_time < 0.5, "Les opérations devraient s'exécuter en parallèle"
    
    await interface.shutdown()

async def main():
    """Fonction principale de test"""
    print("🚀 Tests d'intégration complets")
    print("=" * 40)
    
    await test_unified_async_interface()
    await test_integration_workflow()
    await test_concurrent_operations()
    
    print("\n" + "=" * 40)
    print("🎯 Tous les tests d'intégration réussis!")
    print("\n📋 Fonctionnalités validées:")
    print("  ✅ Interface asynchrone unifiée")
    print("  ✅ Gestion des callbacks et événements")
    print("  ✅ Gestion des erreurs et annulations")
    print("  ✅ Workflow d'intégration complet")
    print("  ✅ Opérations concurrentes")
    print("  ✅ Statistiques et historique")
    print("  ✅ Fermeture propre des ressources")

if __name__ == "__main__":
    asyncio.run(main())