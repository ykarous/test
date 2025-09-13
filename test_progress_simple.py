#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Test simple de l'interface de progression")

try:
    import ai_video_dubbing.performance.progress_interface as pi
    print(f"Module importé: {pi}")
    print(f"Contenu du module: {dir(pi)}")
    
    if hasattr(pi, 'RealTimeProgressInterface'):
        print("✅ RealTimeProgressInterface trouvée")
        interface = pi.RealTimeProgressInterface()
        print("✅ Instance créée")
    else:
        print("❌ RealTimeProgressInterface non trouvée")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()