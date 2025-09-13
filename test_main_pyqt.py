#!/usr/bin/env python3
"""
Test de la nouvelle interface principale PyQt5.
"""
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt5.QtWidgets import QApplication
    from ai_video_dubbing.gui.main_window_qt import MainWindowQt
    
    def main():
        """Lance l'interface principale PyQt5."""
        app = QApplication(sys.argv)
        
        # Créer et afficher la fenêtre principale
        window = MainWindowQt()
        window.show()
        
        print("Interface principale PyQt5 lancée!")
        print("Fonctionnalités disponibles:")
        print("- Sélection de fichier vidéo")
        print("- Configuration avec boutons Sauvegarder/Charger")
        print("- Traitement avec barre de progression")
        print("- Logs en temps réel")
        
        # Lancer la boucle d'événements
        sys.exit(app.exec_())
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Assurez-vous que PyQt5 est installé:")
    print("pip install PyQt5")
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()