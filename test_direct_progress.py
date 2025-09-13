#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Test direct avec rechargement forcé")

try:
    # Importer directement depuis le fichier
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "progress_interface", 
        "ai_video_dubbing/performance/progress_interface.py"
    )
    pi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pi)
    
    print("✅ Module chargé directement")
    
    # Tester les classes
    interface = pi.RealTimeProgressInterface(update_interval=0.1)
    print("✅ Interface créée avec update_interval")
    
    # Tester les méthodes manquantes
    if hasattr(interface, 'add_ui_callback'):
        print("✅ add_ui_callback disponible")
        interface.add_ui_callback(lambda x, y: None)
        print("✅ add_ui_callback fonctionne")
    else:
        print("❌ add_ui_callback manquante")
        
    if hasattr(interface, 'cancel_all_operations'):
        print("✅ cancel_all_operations disponible")
    else:
        print("❌ cancel_all_operations manquante")
    
    # Tester ProgressTracker
    import asyncio
    
    async def test_tracker():
        tracker = await interface.track_operation(
            operation_type=pi.OperationType.DOWNLOAD,
            total_steps=5,
            initial_task="Test"
        )
        print(f"✅ Tracker créé: {tracker.progress.operation_id}")
        
        if hasattr(tracker, 'complete'):
            print("✅ tracker.complete disponible")
            await tracker.complete("Test terminé")
            print("✅ tracker.complete fonctionne")
        else:
            print("❌ tracker.complete manquante")
    
    asyncio.run(test_tracker())
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()