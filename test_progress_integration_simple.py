"""
Test d'intégration simple pour l'interface de progression
"""
import asyncio
import time
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_basic_operation():
    """Test basique d'une opération avec progression"""
    print("Test d'intégration basique...")
    
    # Créer l'interface
    progress_interface = RealTimeProgressInterface(ui_update_interval=0.1)
    
    # Callback simple pour capturer les mises à jour
    updates_received = []
    
    def simple_callback(event_type, data):
        updates_received.append((event_type, data))
        print(f"Callback reçu: {event_type} - {data.get('operation_id', 'N/A')}")
    
    # Ajouter le callback
    progress_interface.add_ui_callback(simple_callback)
    progress_interface.add_notification_callback(simple_callback)
    
    # Démarrer une opération
    tracker = await progress_interface.track_operation(
        operation_type="test_operation",
        estimated_duration=2.0
    )
    
    print(f"Opération démarrée: {tracker.progress.operation_id}")
    
    # Simuler du travail avec mises à jour
    for i in range(5):
        await tracker.update(
            progress_percent=i * 20,
            current_step=f"Étape {i+1}/5",
            current_message=f"Traitement en cours... {i+1}/5"
        )
        await asyncio.sleep(0.2)
    
    # Terminer l'opération
    await progress_interface.complete_operation(tracker.progress.operation_id, success=True)
    
    # Attendre un peu pour les callbacks finaux
    await asyncio.sleep(0.5)
    
    # Vérifier les résultats
    print(f"Callbacks reçus: {len(updates_received)}")
    for event_type, data in updates_received:
        print(f"  - {event_type}: {data.get('message', data.get('operation_id', 'N/A'))}")
    
    # Statistiques
    stats = progress_interface.get_global_statistics()
    print(f"Statistiques: {stats}")
    
    # Nettoyage
    await progress_interface.shutdown()
    
    print("✅ Test d'intégration basique réussi")

if __name__ == "__main__":
    asyncio.run(test_basic_operation())