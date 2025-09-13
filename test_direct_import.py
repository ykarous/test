"""
Test d'import direct pour vérifier le fichier progress_interface.py
"""
import sys
import os

# Ajouter le chemin au module
sys.path.insert(0, os.path.join(os.getcwd(), 'ai_video_dubbing', 'performance'))

try:
    import progress_interface
    print("✅ Module progress_interface importé")
    print(f"Contenu du module: {dir(progress_interface)}")
    
    if hasattr(progress_interface, 'RealTimeProgressInterface'):
        print("✅ RealTimeProgressInterface trouvée")
        interface = progress_interface.RealTimeProgressInterface()
        print("✅ Instance créée")
        
        # Vérifier les méthodes
        methods = ['get_global_statistics', 'track_operation', 'complete_operation']
        for method in methods:
            if hasattr(interface, method):
                print(f"✅ Méthode {method} trouvée")
            else:
                print(f"❌ Méthode {method} manquante")
    else:
        print("❌ RealTimeProgressInterface non trouvée")
        
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
    import traceback
    traceback.print_exc()