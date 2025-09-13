#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Test d'import direct")

try:
    # Test d'import du module
    import ai_video_dubbing.performance.progress_interface
    print("✅ Module importé")
    
    # Test d'accès aux classes
    from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface
    print("✅ RealTimeProgressInterface importée")
    
    # Test de création d'instance
    interface = RealTimeProgressInterface()
    print("✅ Instance créée")
    
    print(f"Type de l'interface: {type(interface)}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()