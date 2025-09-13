"""
Fenêtre principale PyQt5 de l'application de doublage vidéo par IA.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ..models.data_models import PipelineConfig, ProgressInfo
from ..processors.pipeline_orchestrator import PipelineOrchestrator, PipelineState
from .config_panel_qt import ConfigPanelQt


class ProcessingThread(QThread):
    """Thread pour le traitement en arrière-plan."""
    
    progress_updated = pyqtSignal(object)  # ProgressInfo
    processing_completed = pyqtSignal(object)  # Result
    processing_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, orchestrator, video_path):
        super().__init__()
        self.orchestrator = orchestrator
        self.video_path = video_path
    
    def run(self):
        """Exécute le traitement."""
        try:
            result = self.orchestrator.execute_pipeline(self.video_path)
            self.processing_completed.emit(result)
        except Exception as e:
            self.processing_failed.emit(str(e))


class MainWindowQt(QMainWindow):
    """Fenêtre principale PyQt5 de l'application."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Variables
        self.selected_video_path = ""
        self.pipeline_orchestrator: Optional[PipelineOrchestrator] = None
        self.processing_thread: Optional[ProcessingThread] = None
        self.config_panel: Optional[ConfigPanelQt] = None
        
        # Configuration par défaut
        self.current_config = PipelineConfig()
        
        # Initialiser l'interface
        self.init_ui()
        self.setup_connections()
        
        # Centrer la fenêtre
        self.center_window()
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        self.setWindowTitle("🎬 AI Video Dubbing - Doublage Vidéo par IA")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(700, 500)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("🎬 AI Video Dubbing")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Doublage vidéo automatique par intelligence artificielle")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # Section sélection de fichier
        file_group = QGroupBox("📁 Sélection du fichier vidéo")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Aucun fichier sélectionné...")
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Parcourir...")
        self.browse_button.clicked.connect(self.browse_video_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(file_group)
        
        # Section configuration
        config_group = QGroupBox("⚙️ Configuration")
        config_layout = QVBoxLayout(config_group)
        
        self.config_button = QPushButton("Configurer les options")
        self.config_button.clicked.connect(self.open_config_panel)
        config_layout.addWidget(self.config_button)
        
        self.config_summary_label = QLabel(self.get_config_summary())
        self.config_summary_label.setStyleSheet("color: gray; font-size: 9pt;")
        config_layout.addWidget(self.config_summary_label)
        
        layout.addWidget(config_group)
        
        # Section actions
        actions_group = QGroupBox("🚀 Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.start_button = QPushButton("Démarrer le doublage")
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setEnabled(False)
        actions_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)
        actions_layout.addWidget(self.cancel_button)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Section informations
        info_group = QGroupBox("ℹ️ Informations")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(200)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
        
        # Log initial
        self.log_info("🎬 Application AI Video Dubbing démarrée")
        self.log_info("Sélectionnez un fichier vidéo pour commencer")
    
    def setup_connections(self):
        """Configure les connexions de signaux."""
        pass
    
    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def browse_video_file(self):
        """Ouvre le dialogue de sélection de fichier vidéo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mkv *.mov *.wmv);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.selected_video_path = file_path
            self.file_path_edit.setText(file_path)
            self.log_info(f"Fichier sélectionné: {file_path}")
            self.update_start_button_state()
    
    def open_config_panel(self):
        """Ouvre le panneau de configuration PyQt5."""
        if self.config_panel is None or not self.config_panel.isVisible():
            self.config_panel = ConfigPanelQt()
            self.config_panel.setWindowTitle("Configuration - AI Video Dubbing")
            self.config_panel.resize(800, 600)
            
            # Charger la configuration actuelle
            self.config_panel.load_config(self.current_config)
            
            # Connecter le signal de changement de configuration
            self.config_panel.config_changed.connect(self.on_config_changed)
            
            self.config_panel.show()
        else:
            self.config_panel.raise_()
            self.config_panel.activateWindow()
    
    def on_config_changed(self, new_config: PipelineConfig):
        """Appelé quand la configuration change."""
        self.current_config = new_config
        self.config_summary_label.setText(self.get_config_summary())
        self.log_info("Configuration mise à jour")
    
    def get_config_summary(self) -> str:
        """Retourne un résumé de la configuration."""
        summary_parts = []
        
        if self.current_config.enable_source_separation:
            summary_parts.append("Séparation de source")
        
        if self.current_config.enable_ocr:
            summary_parts.append("OCR activé")
        
        summary_parts.append(f"ASR: {self.current_config.asr_model}")
        summary_parts.append(f"Langue: {self.current_config.target_language}")
        
        return " • ".join(summary_parts) if summary_parts else "Configuration par défaut"
    
    def start_processing(self):
        """Démarre le traitement du doublage."""
        if not self.selected_video_path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier vidéo.")
            return
        
        if not Path(self.selected_video_path).exists():
            QMessageBox.warning(self, "Erreur", "Le fichier vidéo sélectionné n'existe pas.")
            return
        
        try:
            # Créer l'orchestrateur
            self.pipeline_orchestrator = PipelineOrchestrator(self.current_config)
            
            # Enregistrer le callback de progression
            self.pipeline_orchestrator.register_progress_callback(self.on_progress_update_direct)
            
            # Créer et démarrer le thread de traitement
            self.processing_thread = ProcessingThread(
                self.pipeline_orchestrator,
                self.selected_video_path
            )
            
            # Connecter les signaux
            self.processing_thread.progress_updated.connect(self.on_progress_update)
            self.processing_thread.processing_completed.connect(self.on_processing_completed)
            self.processing_thread.processing_failed.connect(self.on_processing_failed)
            
            # Mettre à jour l'interface
            self.set_processing_state(True)
            self.log_info(f"Démarrage du traitement: {self.selected_video_path}")
            
            # Démarrer le traitement
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage: {str(e)}")
            self.set_processing_state(False)
    
    def cancel_processing(self):
        """Annule le traitement en cours."""
        if self.pipeline_orchestrator:
            self.pipeline_orchestrator.cancel_processing()
            self.log_info("Annulation du traitement demandée...")
        
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        
        self.set_processing_state(False)
    
    def on_progress_update_direct(self, progress_info: ProgressInfo):
        """Appelé directement par l'orchestrateur (thread-safe)."""
        # Émettre le signal pour mettre à jour l'interface dans le thread principal
        if self.processing_thread:
            self.processing_thread.progress_updated.emit(progress_info)
    
    def on_progress_update(self, progress_info: ProgressInfo):
        """Appelé lors des mises à jour de progression (thread principal)."""
        progress_percentage = int(progress_info.progress * 100)
        self.progress_bar.setValue(progress_percentage)
        self.status_bar.showMessage(f"[{progress_percentage}%] {progress_info.message}")
        self.log_info(f"[{progress_percentage}%] {progress_info.stage.value}: {progress_info.message}")
    
    def on_processing_completed(self, result):
        """Appelé quand le traitement est terminé avec succès."""
        self.set_processing_state(False)
        
        self.log_info("✅ Traitement terminé avec succès!")
        self.log_info(f"Fichier de sortie: {result.output_video_path}")
        self.log_info(f"Temps de traitement: {result.processing_time:.2f}s")
        
        QMessageBox.information(
            self,
            "Traitement terminé",
            f"✅ Traitement terminé avec succès!\n\n"
            f"Fichier de sortie: {result.output_video_path}\n"
            f"Temps de traitement: {result.processing_time:.2f}s"
        )
    
    def on_processing_failed(self, error_message: str):
        """Appelé quand le traitement échoue."""
        self.set_processing_state(False)
        
        self.log_info(f"❌ Traitement échoué: {error_message}")
        
        QMessageBox.critical(
            self,
            "Erreur de traitement",
            f"Le traitement a échoué:\n\n{error_message}\n\n"
            f"Consultez les informations ci-dessous pour plus de détails."
        )
    
    def set_processing_state(self, processing: bool):
        """Met à jour l'état de l'interface selon le traitement."""
        if processing:
            self.start_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.browse_button.setEnabled(False)
            self.config_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_bar.showMessage("Traitement en cours...")
        else:
            self.start_button.setEnabled(bool(self.selected_video_path))
            self.cancel_button.setEnabled(False)
            self.browse_button.setEnabled(True)
            self.config_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("Prêt")
    
    def update_start_button_state(self):
        """Met à jour l'état du bouton de démarrage."""
        self.start_button.setEnabled(bool(self.selected_video_path))
    
    def log_info(self, message: str):
        """Ajoute un message dans la zone d'informations."""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.info_text.append(formatted_message)
        
        # Faire défiler vers le bas
        scrollbar = self.info_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Appelé lors de la fermeture de la fenêtre."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Fermeture",
                "Un traitement est en cours. Voulez-vous vraiment fermer l'application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cancel_processing()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Point d'entrée principal pour l'interface PyQt5."""
    app = QApplication(sys.argv)
    
    # Créer et afficher la fenêtre principale
    window = MainWindowQt()
    window.show()
    
    # Lancer la boucle d'événements
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()