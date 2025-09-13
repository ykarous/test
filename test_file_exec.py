#!/usr/bin/env python3
print("Test d'exécution du fichier progress_interface.py")

try:
    with open('ai_video_dubbing/performance/progress_interface.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Taille du fichier: {len(content)} caractères")
    
    # Exécuter le contenu
    exec(content)
    print("✅ Fichier exécuté avec succès")
    
    # Tester si les classes sont disponibles
    if 'RealTimeProgressInterface' in locals():
        interface = RealTimeProgressInterface()
        print("✅ RealTimeProgressInterface créée")
        
        methods = [m for m in dir(interface) if not m.startswith('_')]
        print(f"Méthodes: {methods}")
        
        if hasattr(interface, 'add_ui_callback'):
            print("✅ add_ui_callback trouvée")
        else:
            print("❌ add_ui_callback manquante")
    else:
        print("❌ RealTimeProgressInterface non trouvée")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()