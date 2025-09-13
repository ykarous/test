#!/usr/bin/env python3
"""
Démarrage sécurisé de l'application avec gestion d'erreurs.
"""
import sys
import os
import traceback
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Vérifie les dépendances requises."""
    print("🔍 Vérification des dépendances...")
    
    missing_deps = []
    
    try:
        import PyQt5
        print("  ✅ PyQt5 disponible")
    except ImportError:
        missing_deps.append("PyQt5")
        print("  ❌ PyQt5 manquant")
    
    try:
        import cv2
        print("  ✅ OpenCV disponible")
    except ImportError:
        print("  ⚠️ OpenCV manquant (optionnel)")
    
    try:
        import numpy
        print("  ✅ NumPy disponible")
    except ImportError:
        print("  ⚠️ NumPy manquant (optionnel)")
    
    if missing_deps:
        print(f"\n❌ Dépendances manquantes: {', '.join(missing_deps)}")
        print("\n🔧 Pour installer les dépendances:")
        print("pip install PyQt5")
        print("pip install opencv-python numpy  # Optionnel")
        return False
    
    return True

def start_application():
    """Démarre l'application principale."""
    print("\n🚀 Démarrage de l'application...")
    
    try:
        # Import de l'application
        from PyQt5.QtWidgets import QApplication
        from ai_video_dubbing.gui.config_panel_qt import ConfigPanelQt
        
        # Créer l'application Qt
        app = QApplication(sys.argv)
        
        # Créer la fenêtre principale (panneau de configuration pour commencer)
        window = ConfigPanelQt()
        window.setWindowTitle("AI Video Dubbing - Configuration")
        window.resize(800, 600)
        window.show()
        
        print("✅ Application démarrée avec succès!")
        print("\n📝 Instructions:")
        print("1. Configurez FFmpeg dans l'onglet 'FFmpeg'")
        print("2. Ajustez les autres paramètres selon vos besoins")
        print("3. Cliquez sur 'Appliquer' pour sauvegarder")
        
        # Lancer la boucle d'événements
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        traceback.print_exc()
        return False

def start_ffmpeg_demo():
    """Démarre la démonstration FFmpeg."""
    print("\n🎬 Démarrage de la démonstration FFmpeg...")
    
    try:
        from demo_ffmpeg_integration import main as demo_main
        demo_main()
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de la démo: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale."""
    print("🎬 AI Video Dubbing - Démarrage Sécurisé")
    print("=" * 50)
    
    # Vérifier les dépendances
    if not check_dependencies():
        return
    
    # Menu de choix
    print("\n📋 Options de démarrage:")
    print("1. Application principale (Configuration)")
    print("2. Démonstration FFmpeg")
    print("3. Test de démarrage (diagnostic)")
    print("4. Quitter")
    
    while True:
        try:
            choice = input("\n👉 Votre choix (1-4): ").strip()
            
            if choice == "1":
                start_application()
                break
            elif choice == "2":
                start_ffmpeg_demo()
                break
            elif choice == "3":
                os.system("python test_startup.py")
                break
            elif choice == "4":
                print("👋 Au revoir!")
                break
            else:
                print("❌ Choix invalide. Veuillez entrer 1, 2, 3 ou 4.")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()