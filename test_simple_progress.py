#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Test simple de la nouvelle interface")

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
    
    # Tester les méthodes
    print(f"Méthodes disponibles: {[m for m in dir(interface) if not m.startswith('_')]}")
    
    if hasattr(interface, 'add_ui_callback'):
        print("✅ add_ui_callback disponible")
    else:
        print("❌ add_ui_callback manquante")
        
    if hasattr(interface, 'cancel_all_operations'):
        print("✅ cancel_all_operations disponible")
    else:
        print("❌ cancel_all_operations manquante")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()