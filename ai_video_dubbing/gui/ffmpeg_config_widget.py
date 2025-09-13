#!/usr/bin/env python3
"""
Widget de configuration FFmpeg pour l'interface graphique.
"""
import os
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QGroupBox, QMessageBox, QProgressBar,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from ..utils.ffmpeg_manager import FFmpegManager

class FFmpegTestThread(QThread):
    """Thread pour tester FFmpeg sans bloquer l'interface."""
    result_ready = pyqtSignal(dict)
    
    def __init__(self, ffmpeg_manager):
        super().__init__()
        self.ffmpeg_manager = ffmpeg_manager
    
    def run(self):
        """Teste FFmpeg en arrière-plan."""
        try:
            info = self.ffmpeg_manager.get_info()
            self.result_ready.emit(info)
        except Exception as e:
            self.result_ready.emit({'error': str(e)})

class FFmpegConfigWidget(QWidget):
    """Widget de configuration FFmpeg."""
    
    ffmpeg_configured = pyqtSignal(bool)  # Signal émis quand FFmpeg est configuré
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ffmpeg_manager = FFmpegManager()
        self.test_thread = None
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Titre
        title_label = QLabel("Configuration FFmpeg")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Groupe d'état
        self.status_group = QGroupBox("État de FFmpeg")
        status_layout = QVBoxLayout(self.status_group)
        
        # Indicateur de statut
        status_row = QHBoxLayout()
        self.status_label = QLabel("Vérification en cours...")
        self.status_icon = QLabel("⏳")
        self.status_icon.setFixedSize(24, 24)
        self.status_icon.setAlignment(Qt.AlignCenter)
        
        status_row.addWidget(self.status_icon)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_layout.addLayout(status_row)
        
        # Informations détaillées
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        status_layout.addWidget(self.info_text)
        
        layout.addWidget(self.status_group)
        
        # Groupe de configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Chemin FFmpeg
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Chemin FFmpeg:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Aucun chemin configuré")
        path_row.addWidget(self.path_edit)
        config_layout.addLayout(path_row)
        
        # Boutons d'action
        buttons_row = QHBoxLayout()
        
        self.auto_detect_btn = QPushButton("🔍 Détection Automatique")
        self.auto_detect_btn.clicked.connect(self.auto_detect_ffmpeg)
        buttons_row.addWidget(self.auto_detect_btn)
        
        self.select_btn = QPushButton("📁 Sélectionner FFmpeg")
        self.select_btn.clicked.connect(self.select_ffmpeg_manually)
        buttons_row.addWidget(self.select_btn)
        
        self.test_btn = QPushButton("🧪 Tester")
        self.test_btn.clicked.connect(self.test_ffmpeg)
        buttons_row.addWidget(self.test_btn)
        
        config_layout.addLayout(buttons_row)
        
        # Boutons utilitaires
        utils_row = QHBoxLayout()
        
        self.reset_btn = QPushButton("🔄 Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_configuration)
        utils_row.addWidget(self.reset_btn)
        
        self.download_btn = QPushButton("📥 Télécharger FFmpeg")
        self.download_btn.clicked.connect(self.show_download_info)
        utils_row.addWidget(self.download_btn)
        
        utils_row.addStretch()
        config_layout.addLayout(utils_row)
        
        layout.addWidget(config_group)
        
        # Barre de progression pour les tests
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Aide
        help_group = QGroupBox("Aide")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel(
            "FFmpeg est requis pour le traitement audio et vidéo.\n\n"
            "• Utilisez 'Détection Automatique' pour chercher FFmpeg sur votre système\n"
            "• Utilisez 'Sélectionner FFmpeg' pour choisir manuellement l'exécutable\n"
            "• Cliquez sur 'Télécharger FFmpeg' pour obtenir les instructions d'installation"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        layout.addStretch()
    
    def update_status(self):
        """Met à jour l'affichage du statut."""
        try:
            info = self.ffmpeg_manager.get_info()
            
            if info['available']:
                self.status_icon.setText("✅")
                self.status_label.setText("FFmpeg disponible et fonctionnel")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                
                # Afficher les informations
                info_text = f"Version: {info['version']}\n"
                info_text += f"FFmpeg: {info['ffmpeg_path']}\n"
                if info['ffprobe_path']:
                    info_text += f"FFprobe: {info['ffprobe_path']}\n"
                
                if info['auto_detected']:
                    info_text += "Détecté automatiquement dans le PATH système"
                else:
                    info_text += "Configuré manuellement"
                
                self.info_text.setText(info_text)
                self.path_edit.setText(info['ffmpeg_path'] or "")
                
                # Émettre le signal de configuration réussie
                self.ffmpeg_configured.emit(True)
                
            else:
                self.status_icon.setText("❌")
                self.status_label.setText("FFmpeg non disponible")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                
                self.info_text.setText(
                    "FFmpeg n'a pas été trouvé sur votre système.\n"
                    "Utilisez les boutons ci-dessous pour le configurer."
                )
                self.path_edit.setText("")
                
                # Émettre le signal d'échec de configuration
                self.ffmpeg_configured.emit(False)
                
        except Exception as e:
            self.status_icon.setText("⚠️")
            self.status_label.setText("Erreur lors de la vérification")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.info_text.setText(f"Erreur: {e}")
            self.ffmpeg_configured.emit(False)
    
    def auto_detect_ffmpeg(self):
        """Lance la détection automatique de FFmpeg."""
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Barre de progression indéterminée
        
        self.status_icon.setText("⏳")
        self.status_label.setText("Détection automatique en cours...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Lancer la détection en arrière-plan
        self.test_thread = FFmpegTestThread(self.ffmpeg_manager)
        self.test_thread.result_ready.connect(self.on_auto_detect_finished)
        
        # Simuler la détection (car elle est rapide)
        QTimer.singleShot(1000, lambda: self.ffmpeg_manager.auto_detect_ffmpeg())
        QTimer.singleShot(1500, self.on_auto_detect_finished_wrapper)
    
    def on_auto_detect_finished_wrapper(self):
        """Wrapper pour la fin de détection automatique."""
        info = self.ffmpeg_manager.get_info()
        self.on_auto_detect_finished(info)
    
    def on_auto_detect_finished(self, info):
        """Appelé quand la détection automatique est terminée."""
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        if info.get('available', False):
            QMessageBox.information(
                self,
                "Détection Réussie",
                f"FFmpeg détecté avec succès!\n\n"
                f"Version: {info.get('version', 'Inconnue')}\n"
                f"Chemin: {info.get('ffmpeg_path', 'Inconnu')}"
            )
        else:
            QMessageBox.warning(
                self,
                "Détection Échouée",
                "FFmpeg n'a pas pu être détecté automatiquement.\n\n"
                "Essayez la sélection manuelle ou téléchargez FFmpeg."
            )
        
        self.update_status()
    
    def select_ffmpeg_manually(self):
        """Permet la sélection manuelle de FFmpeg."""
        success = self.ffmpeg_manager.select_ffmpeg_manually(self)
        self.update_status()
    
    def test_ffmpeg(self):
        """Teste FFmpeg."""
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.status_icon.setText("⏳")
        self.status_label.setText("Test de FFmpeg en cours...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Lancer le test en arrière-plan
        self.test_thread = FFmpegTestThread(self.ffmpeg_manager)
        self.test_thread.result_ready.connect(self.on_test_finished)
        self.test_thread.start()
    
    def on_test_finished(self, info):
        """Appelé quand le test est terminé."""
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        if info.get('available', False):
            QMessageBox.information(
                self,
                "Test Réussi",
                f"FFmpeg fonctionne correctement!\n\n"
                f"Version: {info.get('version', 'Inconnue')}"
            )
        else:
            error_msg = info.get('error', 'Erreur inconnue')
            QMessageBox.warning(
                self,
                "Test Échoué",
                f"FFmpeg ne fonctionne pas correctement.\n\n"
                f"Erreur: {error_msg}"
            )
        
        self.update_status()
    
    def reset_configuration(self):
        """Remet à zéro la configuration FFmpeg."""
        reply = QMessageBox.question(
            self,
            "Réinitialiser Configuration",
            "Êtes-vous sûr de vouloir réinitialiser la configuration FFmpeg?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.ffmpeg_manager.reset_configuration()
            self.update_status()
            QMessageBox.information(
                self,
                "Configuration Réinitialisée",
                "La configuration FFmpeg a été réinitialisée."
            )
    
    def show_download_info(self):
        """Affiche les informations de téléchargement FFmpeg."""
        download_info = self.ffmpeg_manager.download_ffmpeg_info()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Télécharger FFmpeg")
        msg.setIcon(QMessageBox.Information)
        
        text = f"Instructions pour télécharger FFmpeg:\n\n"
        for i, instruction in enumerate(download_info['instructions'], 1):
            text += f"{i}. {instruction}\n"
        text += f"\nSite officiel: {download_info['url']}"
        
        msg.setText(text)
        
        # Bouton pour ouvrir le site
        open_btn = msg.addButton("Ouvrir le Site", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        
        msg.exec_()
        
        if msg.clickedButton() == open_btn:
            webbrowser.open(download_info['url'])
    
    def set_buttons_enabled(self, enabled: bool):
        """Active/désactive les boutons."""
        self.auto_detect_btn.setEnabled(enabled)
        self.select_btn.setEnabled(enabled)
        self.test_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
    
    def get_ffmpeg_manager(self) -> FFmpegManager:
        """Retourne le gestionnaire FFmpeg."""
        return self.ffmpeg_manager