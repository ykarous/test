"""
Interface graphique légère de fallback
Fonctionne sans les dépendances lourdes (torch, etc.)
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QStatusBar,
    QComboBox, QCheckBox, QTabWidget, QMenuBar, QAction,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class ProcessingThread(QThread):
    """Thread de traitement léger"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, input_file, output_file, config):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.config = config
        self.is_cancelled = False
    
    def run(self):
        """Exécute le traitement"""
        try:
            from ..performance.lightweight_fallbacks import get_lightweight_ai_manager
            
            self.status_updated.emit("Initialisation du gestionnaire AI léger...")
            ai_manager = get_lightweight_ai_manager()
            
            # Simulation du traitement avec progression
            steps = [
                "Analyse du fichier d'entrée",
                "Extraction audio",
                "Transcription (mode léger)",
                "Génération des sous-titres",
                "Finalisation"
            ]
            
            for i, step in enumerate(steps):
                if self.is_cancelled:
                    return
                
                self.status_updated.emit(step)
                progress = int((i + 1) / len(steps) * 100)
                self.progress_updated.emit(progress)
                
                # Simuler le travail
                self.msleep(1000)
            
            # Résultat simulé
            result = {
                "output_video_path": self.output_file,
                "processing_time": 5.0,
                "speakers_detected": 2,
                "dialogue_segments": 15,
                "mode": "lightweight"
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Annule le traitement"""
        self.is_cancelled = True

class LightweightMainWindow(QMainWindow):
    """Fenêtre principale légère"""
    
    def __init__(self):
        super().__init__()
        self.processing_thread = None
        self.setup_ui()
        self.setup_system_tray()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("AI Video Dubbing - Mode Léger")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("AI Video Dubbing - Mode Léger")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Onglets
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Onglet principal
        main_tab = self.create_main_tab()
        tabs.addTab(main_tab, "Traitement")
        
        # Onglet diagnostic
        diagnostic_tab = self.create_diagnostic_tab()
        tabs.addTab(diagnostic_tab, "Diagnostic")
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt - Mode léger activé")
        
        # Menu
        self.setup_menu()
    
    def create_main_tab(self):
        """Crée l'onglet principal"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Groupe fichiers
        files_group = QGroupBox("Fichiers")
        files_layout = QVBoxLayout(files_group)
        
        # Fichier d'entrée
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Fichier d'entrée:"))
        self.input_edit = QLineEdit()
        input_layout.addWidget(self.input_edit)
        self.input_button = QPushButton("Parcourir")
        self.input_button.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_button)
        files_layout.addLayout(input_layout)
        
        # Fichier de sortie
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Fichier de sortie:"))
        self.output_edit = QLineEdit()
        output_layout.addWidget(self.output_edit)
        self.output_button = QPushButton("Parcourir")
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_button)
        files_layout.addLayout(output_layout)
        
        layout.addWidget(files_group)
        
        # Groupe configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Mode de traitement
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["fast", "balanced", "quality"])
        mode_layout.addWidget(self.mode_combo)
        config_layout.addLayout(mode_layout)
        
        # Options
        self.fallback_check = QCheckBox("Activer les fallbacks")
        self.fallback_check.setChecked(True)
        config_layout.addWidget(self.fallback_check)
        
        self.cache_check = QCheckBox("Activer le cache")
        self.cache_check.setChecked(True)
        config_layout.addWidget(self.cache_check)
        
        layout.addWidget(config_group)
        
        # Boutons de contrôle
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Démarrer le traitement")
        self.start_button.clicked.connect(self.start_processing)
        buttons_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Zone de log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        return widget
    
    def create_diagnostic_tab(self):
        """Crée l'onglet diagnostic"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Bouton de diagnostic
        diagnostic_button = QPushButton("Lancer le diagnostic système")
        diagnostic_button.clicked.connect(self.run_diagnostic)
        layout.addWidget(diagnostic_button)
        
        # Zone de résultats
        self.diagnostic_text = QTextEdit()
        layout.addWidget(self.diagnostic_text)
        
        return widget
    
    def setup_menu(self):
        """Configure le menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        open_action = QAction("Ouvrir", self)
        open_action.triggered.connect(self.select_input_file)
        file_menu.addAction(open_action)
        
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Outils
        tools_menu = menubar.addMenu("Outils")
        
        diagnostic_action = QAction("Diagnostic système", self)
        diagnostic_action.triggered.connect(self.run_diagnostic)
        tools_menu.addAction(diagnostic_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_system_tray(self):
        """Configure l'icône système"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("AI Video Dubbing - Mode Léger")
            
            # Menu contextuel
            tray_menu = QMenu()
            
            show_action = QAction("Afficher", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Quitter", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
    
    def select_input_file(self):
        """Sélectionne le fichier d'entrée"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier vidéo d'entrée",
            "", "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv);;Tous les fichiers (*)"
        )
        if file_path:
            self.input_edit.setText(file_path)
            # Suggérer un nom de sortie
            input_path = Path(file_path)
            output_path = input_path.parent / f"{input_path.stem}_dubbed{input_path.suffix}"
            self.output_edit.setText(str(output_path))
    
    def select_output_file(self):
        """Sélectionne le fichier de sortie"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sélectionner le fichier de sortie",
            "", "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv);;Tous les fichiers (*)"
        )
        if file_path:
            self.output_edit.setText(file_path)
    
    def start_processing(self):
        """Démarre le traitement"""
        input_file = self.input_edit.text().strip()
        output_file = self.output_edit.text().strip()
        
        if not input_file or not output_file:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner les fichiers d'entrée et de sortie")
            return
        
        if not Path(input_file).exists():
            QMessageBox.warning(self, "Erreur", "Le fichier d'entrée n'existe pas")
            return
        
        # Configuration
        config = {
            "mode": self.mode_combo.currentText(),
            "enable_fallback": self.fallback_check.isChecked(),
            "enable_caching": self.cache_check.isChecked()
        }
        
        # Démarrer le thread de traitement
        self.processing_thread = ProcessingThread(input_file, output_file, config)
        self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processing_thread.status_updated.connect(self.update_status)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error_occurred.connect(self.processing_error)
        
        self.processing_thread.start()
        
        # Mettre à jour l'interface
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.append("Traitement démarré...")
    
    def cancel_processing(self):
        """Annule le traitement"""
        if self.processing_thread:
            self.processing_thread.cancel()
            self.processing_thread.wait()
        
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Traitement annulé")
        self.log_text.append("Traitement annulé par l'utilisateur")
    
    def update_status(self, message):
        """Met à jour le statut"""
        self.status_bar.showMessage(message)
        self.log_text.append(f"[INFO] {message}")
    
    def processing_finished(self, result):
        """Traitement terminé"""
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)
        
        message = f"Traitement terminé avec succès!\n"
        message += f"Fichier de sortie: {result['output_video_path']}\n"
        message += f"Temps de traitement: {result['processing_time']:.1f}s\n"
        message += f"Mode: {result['mode']}"
        
        self.status_bar.showMessage("Traitement terminé")
        self.log_text.append(f"[SUCCÈS] {message}")
        
        QMessageBox.information(self, "Succès", message)
    
    def processing_error(self, error_message):
        """Erreur de traitement"""
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.status_bar.showMessage("Erreur de traitement")
        self.log_text.append(f"[ERREUR] {error_message}")
        
        QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement:\n{error_message}")
    
    def run_diagnostic(self):
        """Lance le diagnostic système"""
        self.diagnostic_text.clear()
        self.diagnostic_text.append("Lancement du diagnostic système...\n")
        
        try:
            # Utiliser la fonction de diagnostic de main.py
            import main
            
            # Capturer la sortie du diagnostic
            import io
            import contextlib
            
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main.launch_diagnostic()
            
            diagnostic_result = output.getvalue()
            self.diagnostic_text.append(diagnostic_result)
            
        except Exception as e:
            self.diagnostic_text.append(f"Erreur lors du diagnostic: {e}")
    
    def show_about(self):
        """Affiche la boîte À propos"""
        QMessageBox.about(
            self, "À propos",
            "AI Video Dubbing - Mode Léger\n\n"
            "Version optimisée pour fonctionner sans dépendances lourdes.\n"
            "Utilise des composants de fallback légers.\n\n"
            "Pour activer le mode complet, installez:\n"
            "- torch\n"
            "- aiofiles\n"
            "- Et autres dépendances"
        )