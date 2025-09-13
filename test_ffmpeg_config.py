#!/usr/bin/env python3
"""
Test de la configuration FFmpeg avec interface graphique.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ai_video_dubbing.gui.ffmpeg_config_widget import FFmpegConfigWidget

class TestWindow(QMainWindow):
    """Fenêtre de test pour la configuration FFmpeg."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Configuration FFmpeg")
        self.setGeometry(100, 100, 600, 500)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Widget de configuration FFmpeg
        self.ffmpeg_widget = FFmpegConfigWidget()
        self.ffmpeg_widget.ffmpeg_configured.connect(self.on_ffmpeg_configured)
        layout.addWidget(self.ffmpeg_widget)
    
    def on_ffmpeg_configured(self, success: bool):
        """Appelé quand FFmpeg est configuré."""
        if success:
            print("✅ FFmpeg configuré avec succès!")
        else:
            print("❌ Échec de la configuration FFmpeg")

def main():
    """Fonction principale."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()