#!/usr/bin/env python3
"""
Test rapide de l'interface graphique
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

def test_gui_launch():
    """Test de lancement de l'interface graphique"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        
        app = QApplication([])
        
        # Essayer de lancer l'interface comme le fait main.py
        try:
            from ai_video_dubbing.gui.enhanced_main_window import EnhancedMainWindow
            print("✅ Interface améliorée disponible")
            window = EnhancedMainWindow()
            gui_type = "améliorée"
        except ImportError:
            try:
                from ai_video_dubbing.gui.main_window_qt import MainWindowQt
                print("✅ Interface standard disponible")
                window = MainWindowQt()
                gui_type = "standard"
            except ImportError:
                from ai_video_dubbing.gui.lightweight_main_window import LightweightMainWindow
                print("✅ Interface légère disponible")
                window = LightweightMainWindow()
                gui_type = "légère"
        
        # Afficher brièvement la fenêtre
        window.show()
        print(f"✅ Interface {gui_type} lancée avec succès")
        
        # Fermer automatiquement après 1 seconde
        QTimer.singleShot(1000, app.quit)
        app.exec_()
        
        print("✅ Interface fermée proprement")
        return True
        
    except Exception as e:
        print(f"❌ Erreur GUI: {e}")
        return False

if __name__ == "__main__":
    print("🖥️  Test rapide de l'interface graphique...")
    success = test_gui_launch()
    
    if success:
        print("🎉 Interface graphique fonctionnelle!")
    else:
        print("⚠️  Problème avec l'interface graphique")