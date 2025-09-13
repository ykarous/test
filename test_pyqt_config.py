#!/usr/bin/env python3
"""
Test direct de l'interface de configuration PyQt5.
"""
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt5.QtWidgets import QApplication
    from ai_video_dubbing.gui.config_panel_qt import ConfigPanelQt
    
    def main():
        """Lance directement l'interface de configuration PyQt5."""
        app = QApplication(sys.argv)
        
        # Créer la fenêtre de configuration
        config_window = ConfigPanelQt()
        config_window.setWindowTitle("Test Configuration PyQt5 - AI Video Dubbing")
        config_window.resize(800, 600)
        config_window.show()
        
        print("Interface PyQt5 lancée!")
        print("Vérifiez que les boutons suivants sont présents:")
        print("- 🔄 Réinitialiser")
        print("- 📁 Charger")
        print("- 💾 Sauvegarder")
        print("- ✅ Appliquer")
        
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