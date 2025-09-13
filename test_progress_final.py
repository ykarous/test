"""
Test final de l'interface de progression après rechargement
"""
import sys
import importlib

# Forcer le rechargement du module
if 'ai_video_dubbing.performance.progress_interface' in sys.modules:
    importlib.reload(sys.modules['ai_video_dubbing.performance.progress_interface'])

import asyncio
import time
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_final_integration():
    """Test final d'intégration"""
    print("Test final de l'interface de progression...")
    
    # Créer l'interface
    progress_interface = RealTimeProgressInterface(ui_update_interval=0.1)
    
    # Vérifier que toutes les méthodes existent
    methods_to_check = [
        'track_operation',
        'complete_operation', 
        'get_global_statistics',
        'add_ui_callback',
        'add_notification_callback',
        'shutdown'
    ]
    
    for method in methods_to_check:
        if hasattr(progress_interface, method):
            print(f"✅ Méthode {method} trouvée")
        else:
            print(f"❌ Méthode {method} manquante")
            return
    
    # Callback simple pour capturer les mises à jour
    updates_received = []
    
    def simple_callback(event_type, data):
        updates_received.append((event_type, data))
        print(f"Callback: {event_type} - {data.get('operation_id', 'N/A')}")
    
    # Ajouter les callbacks
    progress_interface.add_ui_callback(simple_callback)
    progress_interface.add_notification_callback(simple_callback)
    
    # Démarrer une opération
    tracker = await progress_interface.track_operation(
        operation_type="test_operation",
        estimated_duration=1.0
    )
    
    print(f"Opération démarrée: {tracker.progress.operation_id}")
    
    # Simuler du travail
    for i in range(3):
        await tracker.update(
            progress_percent=i * 33,
            current_step=f"Étape {i+1}/3",
            current_message=f"Traitement {i+1}/3"
        )
        await asyncio.sleep(0.2)
    
    # Terminer l'opération
    await progress_interface.complete_operation(tracker.progress.operation_id, success=True)
    
    # Attendre les callbacks finaux
    await asyncio.sleep(0.3)
    
    # Vérifier les résultats
    print(f"Callbacks reçus: {len(updates_received)}")
    
    # Statistiques
    try:
        stats = progress_interface.get_global_statistics()
        print(f"Statistiques: {stats}")
        print("✅ Statistiques récupérées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des statistiques: {e}")
    
    # Nettoyage
    await progress_interface.shutdown()
    
    print("✅ Test final terminé")

if __name__ == "__main__":
    asyncio.run(test_final_integration())