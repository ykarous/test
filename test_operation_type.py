#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Test de OperationType")

try:
    # Forcer le rechargement du module
    import importlib
    import ai_video_dubbing.performance.progress_interface
    importlib.reload(ai_video_dubbing.performance.progress_interface)
    
    from ai_video_dubbing.performance.progress_interface import OperationType, OperationStatus
    print("✅ OperationType importée")
    print(f"Types disponibles: {list(OperationType)}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()