"""
Test du widget de téléchargement des modèles NeMo
"""

import sys
import os
import signal
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Patch signal pour Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

# Variables d'environnement pour NeMo
os.environ["USE_NEMO_ONLY"] = "1"
os.environ["DISABLE_PYANNOTE"] = "1"

def main():
    """Test de l'interface de téléchargement NeMo"""
    
    print("🧪 Test du widget de téléchargement NeMo")
    print("=" * 50)
    
    try:
        # Créer l'application Qt
        app = QApplication(sys.argv)
        
        # Créer la fenêtre principale
        window = QMainWindow()
        window.setWindowTitle("Test - Téléchargement Modèles NeMo")
        window.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Importer et créer le widget de téléchargement
        from ai_video_dubbing.gui.nemo_model_downloader import NemoModelDownloader
        
        downloader = NemoModelDownloader()
        
        # Connecter les signaux pour le test
        def on_model_downloaded(model_name, model_info):
            print(f"✅ Modèle téléchargé: {model_name}")
            print(f"   Info: {model_info}")
        
        downloader.model_downloaded.connect(on_model_downloaded)
        
        layout.addWidget(downloader)
        
        # Afficher la fenêtre
        window.show()
        
        print("✅ Interface de téléchargement NeMo lancée")
        print("   - Sélectionnez une catégorie")
        print("   - Choisissez un modèle")
        print("   - Cliquez sur 'Télécharger le Modèle'")
        
        # Lancer l'application
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()