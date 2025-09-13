#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface
    print("✅ Import réussi")
    
    # Test simple
    interface = RealTimeProgressInterface()
    print("✅ Instance créée")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()