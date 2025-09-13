#!/usr/bin/env python3
"""
Démonstration de l'intégration FFmpeg avec interface graphique.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from ai_video_dubbing.gui.config_panel_qt import ConfigPanelQt
from ai_video_dubbing.utils.ffmpeg_manager import FFmpegManager
from ai_video_dubbing.utils.media_utils import MediaUtils

class MediaProcessingThread(QThread):
    """Thread pour traiter les médias en arrière-plan."""
    
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, media_utils, video_path, operation):
        super().__init__()
        self.media_utils = media_utils
        self.video_path = video_path
        self.operation = operation
    
    def run(self):
        """Exécute l'opération média."""
        try:
            if self.operation == "info":
                self.progress_update.emit("Extraction des informations vidéo...")
                info = self.media_utils.get_video_info(self.video_path)
                
                result_text = "=== INFORMATIONS VIDÉO ===\n\n"
                result_text += f"Durée: {info.get('duration', 0):.2f} secondes\n"
                result_text += f"Résolution: {info.get('width', 0)}x{info.get('height', 0)}\n"
                result_text += f"FPS: {info.get('fps', 0):.2f}\n"
                result_text += f"Codec vidéo: {info.get('video_codec', 'unknown')}\n"
                result_text += f"Codec audio: {info.get('audio_codec', 'unknown')}\n"
                result_text += f"Fréquence audio: {info.get('audio_sample_rate', 0)} Hz\n"
                result_text += f"Taille fichier: {info.get('file_size', 0) / (1024*1024):.2f} MB"
                
                self.finished.emit(True, result_text)
                
            elif self.operation == "extract_audio":
                self.progress_update.emit("Extraction de l'audio...")
                output_path = str(Path(self.video_path).with_suffix('.wav'))
                
                success = self.media_utils.extract_audio(self.video_path, output_path)
                
                if success:
                    self.finished.emit(True, f"Audio extrait avec succès: {output_path}")
                else:
                    self.finished.emit(False, "Échec de l'extraction audio")
                    
        except Exception as e:
            self.finished.emit(False, f"Erreur: {e}")

class FFmpegDemoWindow(QMainWindow):
    """Fenêtre de démonstration FFmpeg."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Démonstration FFmpeg - AI Video Dubbing")
        self.setGeometry(100, 100, 800, 600)
        
        # Gestionnaires
        self.ffmpeg_manager = FFmpegManager()
        self.media_utils = MediaUtils(self.ffmpeg_manager)
        self.processing_thread = None
        
        self.init_ui()
        self.update_ffmpeg_status()
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("🎬 Démonstration FFmpeg")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Statut FFmpeg
        self.status_group = QGroupBox("Statut FFmpeg")
        status_layout = QVBoxLayout(self.status_group)
        
        self.status_label = QLabel("Vérification en cours...")
        status_layout.addWidget(self.status_label)
        
        status_buttons = QHBoxLayout()
        
        self.config_btn = QPushButton("⚙️ Configurer FFmpeg")
        self.config_btn.clicked.connect(self.open_config)
        status_buttons.addWidget(self.config_btn)
        
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.update_ffmpeg_status)
        status_buttons.addWidget(self.refresh_btn)
        
        status_buttons.addStretch()
        status_layout.addLayout(status_buttons)
        
        layout.addWidget(self.status_group)
        
        # Sélection de fichier
        file_group = QGroupBox("Fichier vidéo")
        file_layout = QVBoxLayout(file_group)
        
        file_row = QHBoxLayout()
        self.file_path_label = QLabel("Aucun fichier sélectionné")
        file_row.addWidget(self.file_path_label)
        
        self.select_file_btn = QPushButton("📁 Sélectionner")
        self.select_file_btn.clicked.connect(self.select_video_file)
        file_row.addWidget(self.select_file_btn)
        
        file_layout.addLayout(file_row)
        layout.addWidget(file_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.info_btn = QPushButton("ℹ️ Informations vidéo")
        self.info_btn.clicked.connect(self.get_video_info)
        self.info_btn.setEnabled(False)
        actions_layout.addWidget(self.info_btn)
        
        self.extract_audio_btn = QPushButton("🎵 Extraire audio")
        self.extract_audio_btn.clicked.connect(self.extract_audio)
        self.extract_audio_btn.setEnabled(False)
        actions_layout.addWidget(self.extract_audio_btn)
        
        actions_layout.addStretch()
        layout.addWidget(actions_group)
        
        # Résultats
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Variables
        self.selected_video_path = None
    
    def update_ffmpeg_status(self):
        """Met à jour le statut FFmpeg."""
        try:
            info = self.ffmpeg_manager.get_info()
            
            if info['available']:
                self.status_label.setText(
                    f"✅ FFmpeg disponible - Version: {info['version']}\n"
                    f"Chemin: {info['ffmpeg_path']}"
                )
                self.status_label.setStyleSheet("color: green;")
                
                # Activer les boutons si un fichier est sélectionné
                if self.selected_video_path:
                    self.info_btn.setEnabled(True)
                    self.extract_audio_btn.setEnabled(True)
            else:
                self.status_label.setText("❌ FFmpeg non disponible")
                self.status_label.setStyleSheet("color: red;")
                
                # Désactiver les boutons
                self.info_btn.setEnabled(False)
                self.extract_audio_btn.setEnabled(False)
                
        except Exception as e:
            self.status_label.setText(f"⚠️ Erreur: {e}")
            self.status_label.setStyleSheet("color: orange;")
    
    def open_config(self):
        """Ouvre le panneau de configuration."""
        config_window = ConfigPanelQt()
        config_window.setWindowTitle("Configuration FFmpeg")
        config_window.resize(700, 600)
        
        # Connecter le signal de configuration FFmpeg
        if hasattr(config_window, 'ffmpeg_widget'):
            config_window.ffmpeg_widget.ffmpeg_configured.connect(
                lambda success: self.on_ffmpeg_configured(success, config_window)
            )
        
        config_window.exec_()
    
    def on_ffmpeg_configured(self, success, config_window):
        """Appelé quand FFmpeg est configuré."""
        if success:
            # Mettre à jour le gestionnaire FFmpeg
            self.ffmpeg_manager = config_window.get_ffmpeg_manager()
            self.media_utils = MediaUtils(self.ffmpeg_manager)
            self.update_ffmpeg_status()
            
            QMessageBox.information(
                self,
                "Configuration",
                "FFmpeg configuré avec succès!"
            )
    
    def select_video_file(self):
        """Sélectionne un fichier vidéo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.selected_video_path = file_path
            self.file_path_label.setText(f"Fichier: {Path(file_path).name}")
            
            # Activer les boutons si FFmpeg est disponible
            if self.ffmpeg_manager.is_available():
                self.info_btn.setEnabled(True)
                self.extract_audio_btn.setEnabled(True)
    
    def get_video_info(self):
        """Obtient les informations de la vidéo."""
        if not self.selected_video_path:
            return
        
        self.results_text.clear()
        self.results_text.append("Traitement en cours...")
        
        # Désactiver les boutons
        self.set_buttons_enabled(False)
        
        # Lancer le traitement en arrière-plan
        self.processing_thread = MediaProcessingThread(
            self.media_utils, self.selected_video_path, "info"
        )
        self.processing_thread.progress_update.connect(self.on_progress_update)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()
    
    def extract_audio(self):
        """Extrait l'audio de la vidéo."""
        if not self.selected_video_path:
            return
        
        self.results_text.clear()
        self.results_text.append("Extraction audio en cours...")
        
        # Désactiver les boutons
        self.set_buttons_enabled(False)
        
        # Lancer le traitement en arrière-plan
        self.processing_thread = MediaProcessingThread(
            self.media_utils, self.selected_video_path, "extract_audio"
        )
        self.processing_thread.progress_update.connect(self.on_progress_update)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()
    
    def on_progress_update(self, message):
        """Met à jour le progrès."""
        self.results_text.append(f"⏳ {message}")
    
    def on_processing_finished(self, success, message):
        """Appelé quand le traitement est terminé."""
        self.results_text.clear()
        
        if success:
            self.results_text.append(f"✅ {message}")
        else:
            self.results_text.append(f"❌ {message}")
        
        # Réactiver les boutons
        self.set_buttons_enabled(True)
    
    def set_buttons_enabled(self, enabled):
        """Active/désactive les boutons."""
        self.info_btn.setEnabled(enabled and self.selected_video_path and self.ffmpeg_manager.is_available())
        self.extract_audio_btn.setEnabled(enabled and self.selected_video_path and self.ffmpeg_manager.is_available())
        self.select_file_btn.setEnabled(enabled)
        self.config_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)

def main():
    """Fonction principale."""
    app = QApplication(sys.argv)
    
    window = FFmpegDemoWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()