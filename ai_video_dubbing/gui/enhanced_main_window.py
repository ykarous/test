"""
Fenêtre principale améliorée avec feedback temps réel et intégration des composants de performance
"""

import sys
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QTabWidget,
    QFileDialog, QMessageBox, QProgressBar, QStatusBar, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QCheckBox, QSlider, QFrame, QScrollArea,
    QToolBar, QAction, QMenu, QSystemTrayIcon, QDialog, QDialogButtonBox,
    QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QMovie

# Imports des composants de performance
from ..processors.enhanced_ai_model_manager import EnhancedAIModelManager, TranscriptionConfig, TranscriptionMode
from ..processors.unified_async_interface import UnifiedAsyncInterface, OperationType, OperationStatus
from ..performance.model_notifications import SmartNotificationManager, ModelNotification, NotificationType
from ..performance.diagnostic_engine import DiagnosticEngine
from ..performance.model_actions import ModelActionManager

logger = logging.getLogger(__name__)

@dataclass
class UITheme:
    """Thème de l'interface utilisateur"""
    primary_color: str = "#2196F3"
    secondary_color: str = "#FFC107"
    success_color: str = "#4CAF50"
    warning_color: str = "#FF9800"
    error_color: str = "#F44336"
    background_color: str = "#FAFAFA"
    text_color: str = "#212121"
    accent_color: str = "#03DAC6"

class RealTimeProgressWidget(QWidget):
    """Widget de progression temps réel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_operations = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du widget de progression"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header = QLabel("Opérations en cours")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Zone de défilement pour les opérations
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.operations_widget = QWidget()
        self.operations_layout = QVBoxLayout(self.operations_widget)
        
        scroll_area.setWidget(self.operations_widget)
        layout.addWidget(scroll_area)
        
        # Statistiques globales
        self.stats_label = QLabel("Aucune opération active")
        self.stats_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.stats_label)
    
    def add_operation(self, operation_id: str, operation_type: str, description: str):
        """Ajoute une nouvelle opération à suivre"""
        
        operation_frame = QFrame()
        operation_frame.setFrameStyle(QFrame.StyledPanel)
        operation_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(operation_frame)
        
        # En-tête de l'opération
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"{operation_type}: {description}")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title_label)
        
        # Bouton d'annulation
        cancel_button = QPushButton("Annuler")
        cancel_button.setMaximumWidth(80)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        cancel_button.clicked.connect(lambda: self.cancel_operation(operation_id))
        header_layout.addWidget(cancel_button)
        
        layout.addLayout(header_layout)
        
        # Barre de progression
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(progress_bar)
        
        # Label de statut
        status_label = QLabel("Initialisation...")
        status_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(status_label)
        
        # Temps estimé
        time_label = QLabel("Temps estimé: Calcul en cours...")
        time_label.setStyleSheet("color: #888; font-size: 8pt;")
        layout.addWidget(time_label)
        
        self.operations_layout.addWidget(operation_frame)
        
        # Stocker les références
        self.active_operations[operation_id] = {
            'frame': operation_frame,
            'progress_bar': progress_bar,
            'status_label': status_label,
            'time_label': time_label,
            'cancel_button': cancel_button,
            'start_time': time.time()
        }
        
        self.update_stats()
    
    def update_operation(self, operation_id: str, progress_percent: float, 
                        current_step: str, remaining_time: float = None):
        """Met à jour une opération"""
        
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        # Mettre à jour la barre de progression
        operation['progress_bar'].setValue(int(progress_percent))
        
        # Mettre à jour le statut
        operation['status_label'].setText(current_step)
        
        # Mettre à jour le temps
        if remaining_time is not None:
            if remaining_time > 60:
                time_text = f"Temps restant: {int(remaining_time // 60)}m {int(remaining_time % 60)}s"
            else:
                time_text = f"Temps restant: {int(remaining_time)}s"
        else:
            elapsed = time.time() - operation['start_time']
            time_text = f"Temps écoulé: {int(elapsed)}s"
        
        operation['time_label'].setText(time_text)
        
        # Changer la couleur selon le progrès
        if progress_percent >= 90:
            color = "#4CAF50"  # Vert
        elif progress_percent >= 50:
            color = "#2196F3"  # Bleu
        else:
            color = "#FF9800"  # Orange
        
        operation['progress_bar'].setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
    
    def complete_operation(self, operation_id: str, success: bool, message: str = ""):
        """Marque une opération comme terminée"""
        
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        # Mettre à jour l'interface
        if success:
            operation['progress_bar'].setValue(100)
            operation['status_label'].setText(f"✅ Terminé: {message}")
            operation['status_label'].setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            operation['status_label'].setText(f"❌ Échec: {message}")
            operation['status_label'].setStyleSheet("color: #f44336; font-weight: bold;")
        
        # Désactiver le bouton d'annulation
        operation['cancel_button'].setEnabled(False)
        operation['cancel_button'].setText("Terminé")
        
        # Programmer la suppression après 5 secondes
        QTimer.singleShot(5000, lambda: self.remove_operation(operation_id))
    
    def remove_operation(self, operation_id: str):
        """Supprime une opération de l'affichage"""
        
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        self.operations_layout.removeWidget(operation['frame'])
        operation['frame'].deleteLater()
        
        del self.active_operations[operation_id]
        self.update_stats()
    
    def cancel_operation(self, operation_id: str):
        """Annule une opération"""
        # Signal émis vers le gestionnaire principal
        self.parent().cancel_operation_requested.emit(operation_id)
    
    def update_stats(self):
        """Met à jour les statistiques globales"""
        count = len(self.active_operations)
        if count == 0:
            self.stats_label.setText("Aucune opération active")
        elif count == 1:
            self.stats_label.setText("1 opération en cours")
        else:
            self.stats_label.setText(f"{count} opérations en cours")

class NotificationWidget(QWidget):
    """Widget de notifications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications = []
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du widget de notifications"""
        layout = QVBoxLayout(self)
        
        # En-tête avec compteur
        header_layout = QHBoxLayout()
        
        self.header_label = QLabel("Notifications")
        self.header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.header_label)
        
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("""
            QLabel {
                background-color: #f44336;
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        self.count_label.setMaximumWidth(30)
        header_layout.addWidget(self.count_label)
        
        # Bouton pour marquer tout comme lu
        clear_button = QPushButton("Tout marquer comme lu")
        clear_button.setMaximumWidth(150)
        clear_button.clicked.connect(self.mark_all_read)
        header_layout.addWidget(clear_button)
        
        layout.addLayout(header_layout)
        
        # Zone de défilement pour les notifications
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)
        
        self.notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_widget)
        
        scroll_area.setWidget(self.notifications_widget)
        layout.addWidget(scroll_area)
    
    def add_notification(self, notification: ModelNotification):
        """Ajoute une nouvelle notification"""
        
        notification_frame = QFrame()
        notification_frame.setFrameStyle(QFrame.StyledPanel)
        
        # Couleur selon le type
        colors = {
            NotificationType.INFO: "#2196F3",
            NotificationType.SUCCESS: "#4CAF50",
            NotificationType.WARNING: "#FF9800",
            NotificationType.ERROR: "#f44336",
            NotificationType.DISK_SPACE_LOW: "#FF5722",
            NotificationType.MODEL_CORRUPTED: "#9C27B0",
            NotificationType.UPDATE_AVAILABLE: "#00BCD4"
        }
        
        color = colors.get(notification.notification_type, "#666")
        
        notification_frame.setStyleSheet(f"""
            QFrame {{
                border-left: 4px solid {color};
                background-color: white;
                margin: 2px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(notification_frame)
        
        # En-tête avec titre et heure
        header_layout = QHBoxLayout()
        
        title_label = QLabel(notification.title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title_label)
        
        time_label = QLabel(time.strftime("%H:%M", time.localtime(notification.timestamp)))
        time_label.setStyleSheet("color: #888; font-size: 9pt;")
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(notification.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #333; margin: 5px 0;")
        layout.addWidget(message_label)
        
        # Actions si disponibles
        if notification.actions:
            actions_layout = QHBoxLayout()
            
            for action in notification.actions[:3]:  # Limiter à 3 actions
                action_button = QPushButton(action.replace("_", " ").title())
                action_button.setMaximumWidth(120)
                action_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-size: 9pt;
                    }}
                    QPushButton:hover {{
                        opacity: 0.8;
                    }}
                """)
                action_button.clicked.connect(
                    lambda checked, a=action, n=notification: self.execute_action(a, n)
                )
                actions_layout.addWidget(action_button)
            
            layout.addLayout(actions_layout)
        
        # Bouton de fermeture
        close_button = QPushButton("×")
        close_button.setMaximumSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14pt;
                font-weight: bold;
                color: #999;
            }
            QPushButton:hover {
                color: #f44336;
            }
        """)
        close_button.clicked.connect(
            lambda: self.remove_notification(notification.notification_id, notification_frame)
        )
        
        # Positionner le bouton de fermeture en haut à droite
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_button)
        layout.insertLayout(0, close_layout)
        
        self.notifications_layout.insertWidget(0, notification_frame)  # Ajouter en haut
        self.notifications.append({
            'id': notification.notification_id,
            'frame': notification_frame,
            'notification': notification
        })
        
        self.update_count()
    
    def remove_notification(self, notification_id: str, frame: QFrame):
        """Supprime une notification"""
        
        self.notifications_layout.removeWidget(frame)
        frame.deleteLater()
        
        self.notifications = [n for n in self.notifications if n['id'] != notification_id]
        self.update_count()
    
    def mark_all_read(self):
        """Marque toutes les notifications comme lues"""
        
        for notification_data in self.notifications[:]:
            self.remove_notification(
                notification_data['id'], 
                notification_data['frame']
            )
    
    def update_count(self):
        """Met à jour le compteur de notifications"""
        count = len(self.notifications)
        self.count_label.setText(str(count))
        
        if count == 0:
            self.count_label.setVisible(False)
        else:
            self.count_label.setVisible(True)
    
    def execute_action(self, action: str, notification: ModelNotification):
        """Exécute une action de notification"""
        # Signal émis vers le gestionnaire principal
        self.parent().notification_action_requested.emit(action, notification)

class DiagnosticWidget(QWidget):
    """Widget de diagnostic système"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du widget de diagnostic"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header = QLabel("Diagnostic Système")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.run_diagnostic_button = QPushButton("Exécuter Diagnostic")
        self.run_diagnostic_button.clicked.connect(self.run_diagnostic)
        buttons_layout.addWidget(self.run_diagnostic_button)
        
        self.optimize_button = QPushButton("Optimiser Système")
        self.optimize_button.clicked.connect(self.optimize_system)
        buttons_layout.addWidget(self.optimize_button)
        
        layout.addLayout(buttons_layout)
        
        # Zone de résultats
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Métriques système
        metrics_group = QGroupBox("Métriques Système")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("Mémoire: --")
        self.disk_label = QLabel("Disque: --")
        self.gpu_label = QLabel("GPU: --")
        
        for label in [self.cpu_label, self.memory_label, self.disk_label, self.gpu_label]:
            label.setStyleSheet("padding: 5px; font-family: monospace;")
            metrics_layout.addWidget(label)
        
        layout.addWidget(metrics_group)
        
        # Timer pour mise à jour automatique
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Mise à jour toutes les 5 secondes
    
    def run_diagnostic(self):
        """Lance un diagnostic complet"""
        self.results_text.append("🔍 Lancement du diagnostic système...")
        # Signal émis vers le gestionnaire principal
        self.parent().diagnostic_requested.emit()
    
    def optimize_system(self):
        """Lance l'optimisation système"""
        self.results_text.append("⚡ Lancement de l'optimisation système...")
        # Signal émis vers le gestionnaire principal
        self.parent().optimization_requested.emit()
    
    def update_metrics(self):
        """Met à jour les métriques système"""
        # Simulation des métriques (dans une vraie implémentation, utiliser psutil)
        import random
        
        cpu_usage = random.randint(10, 80)
        memory_usage = random.randint(30, 90)
        disk_usage = random.randint(20, 95)
        gpu_usage = random.randint(0, 100)
        
        self.cpu_label.setText(f"CPU: {cpu_usage}%")
        self.memory_label.setText(f"Mémoire: {memory_usage}%")
        self.disk_label.setText(f"Disque: {disk_usage}%")
        self.gpu_label.setText(f"GPU: {gpu_usage}%")
        
        # Changer les couleurs selon l'usage
        for label, usage in [(self.cpu_label, cpu_usage), (self.memory_label, memory_usage), 
                           (self.disk_label, disk_usage), (self.gpu_label, gpu_usage)]:
            if usage > 80:
                color = "#f44336"  # Rouge
            elif usage > 60:
                color = "#FF9800"  # Orange
            else:
                color = "#4CAF50"  # Vert
            
            label.setStyleSheet(f"padding: 5px; font-family: monospace; color: {color};")
    
    def add_diagnostic_result(self, result: str):
        """Ajoute un résultat de diagnostic"""
        self.results_text.append(result)

class EnhancedMainWindow(QMainWindow):
    """Fenêtre principale améliorée avec feedback temps réel"""
    
    # Signaux pour la communication avec les composants
    cancel_operation_requested = pyqtSignal(str)
    notification_action_requested = pyqtSignal(str, object)
    diagnostic_requested = pyqtSignal()
    optimization_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Composants de performance
        self.ai_manager = None
        self.async_interface = None
        self.notification_manager = None
        self.diagnostic_engine = None
        
        # État de l'interface
        self.current_theme = UITheme()
        self.is_processing = False
        
        # System tray
        self.tray_icon = None
        
        # Configuration de l'interface
        self.setup_ui()
        self.setup_performance_components()
        self.setup_system_tray()
        self.setup_connections()
        
        # Démarrer les mises à jour automatiques
        self.start_auto_updates()
        
        self.logger.info("Enhanced Main Window initialized")
    
    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        
        self.setWindowTitle("AI Video Dubbing - Enhanced Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central avec splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panneau gauche - Contrôles principaux
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Panneau droit - Feedback temps réel
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Proportions du splitter
        main_splitter.setSizes([800, 600])
        
        # Barre d'outils
        self.create_toolbar()
        
        # Barre de statut
        self.create_status_bar()
        
        # Menu
        self.create_menu_bar()
        
        # Appliquer le thème
        self.apply_theme()
    
    def create_left_panel(self) -> QWidget:
        """Crée le panneau gauche avec les contrôles principaux"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Groupe de sélection de fichier
        file_group = QGroupBox("Fichier Vidéo")
        file_layout = QVBoxLayout(file_group)
        
        file_input_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Sélectionnez un fichier vidéo...")
        file_input_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Parcourir")
        browse_button.clicked.connect(self.browse_file)
        file_input_layout.addWidget(browse_button)
        
        file_layout.addLayout(file_input_layout)
        layout.addWidget(file_group)
        
        # Groupe de configuration de transcription
        config_group = QGroupBox("Configuration de Transcription")
        config_layout = QVBoxLayout(config_group)
        
        # Mode de transcription
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Fast", "Balanced", "Quality", "Adaptive"])
        self.mode_combo.setCurrentText("Balanced")
        mode_layout.addWidget(self.mode_combo)
        
        config_layout.addLayout(mode_layout)
        
        # Langue
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Langue:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "Français", "Anglais", "Espagnol", "Allemand"])
        lang_layout.addWidget(self.language_combo)
        
        config_layout.addLayout(lang_layout)
        
        # Options avancées
        self.enable_fallback_check = QCheckBox("Activer le fallback intelligent")
        self.enable_fallback_check.setChecked(True)
        config_layout.addWidget(self.enable_fallback_check)
        
        self.enable_cache_check = QCheckBox("Utiliser le cache")
        self.enable_cache_check.setChecked(True)
        config_layout.addWidget(self.enable_cache_check)
        
        # Seuil de qualité
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Seuil de qualité:"))
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(50, 100)
        self.quality_slider.setValue(80)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        quality_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel("80%")
        quality_layout.addWidget(self.quality_label)
        
        config_layout.addLayout(quality_layout)
        
        layout.addWidget(config_group)
        
        # Boutons d'action
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.start_button = QPushButton("Démarrer la Transcription")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_theme.primary_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
            QPushButton:disabled {{
                background-color: #ccc;
            }}
        """)
        self.start_button.clicked.connect(self.start_transcription)
        actions_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Arrêter Toutes les Opérations")
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_theme.error_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: #d32f2f;
            }}
        """)
        self.stop_button.clicked.connect(self.stop_all_operations)
        self.stop_button.setEnabled(False)
        actions_layout.addWidget(self.stop_button)
        
        layout.addWidget(actions_group)
        
        # Zone de résultats
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Stretch pour pousser tout vers le haut
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Crée le panneau droit avec le feedback temps réel"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Onglets pour organiser les informations
        tabs = QTabWidget()
        
        # Onglet Progression
        self.progress_widget = RealTimeProgressWidget(self)
        tabs.addTab(self.progress_widget, "Progression")
        
        # Onglet Notifications
        self.notification_widget = NotificationWidget(self)
        tabs.addTab(self.notification_widget, "Notifications")
        
        # Onglet Diagnostic
        self.diagnostic_widget = DiagnosticWidget(self)
        tabs.addTab(self.diagnostic_widget, "Diagnostic")
        
        layout.addWidget(tabs)
        
        return panel
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        
        toolbar = QToolBar("Actions Principales")
        self.addToolBar(toolbar)
        
        # Action de diagnostic rapide
        diagnostic_action = QAction("🔍 Diagnostic", self)
        diagnostic_action.setStatusTip("Exécuter un diagnostic rapide")
        diagnostic_action.triggered.connect(self.quick_diagnostic)
        toolbar.addAction(diagnostic_action)
        
        # Action d'optimisation
        optimize_action = QAction("⚡ Optimiser", self)
        optimize_action.setStatusTip("Optimiser les performances")
        optimize_action.triggered.connect(self.quick_optimize)
        toolbar.addAction(optimize_action)
        
        toolbar.addSeparator()
        
        # Action de nettoyage
        cleanup_action = QAction("🧹 Nettoyer", self)
        cleanup_action.setStatusTip("Nettoyer les ressources")
        cleanup_action.triggered.connect(self.cleanup_resources)
        toolbar.addAction(cleanup_action)
        
        # Action de statistiques
        stats_action = QAction("📊 Statistiques", self)
        stats_action.setStatusTip("Afficher les statistiques")
        stats_action.triggered.connect(self.show_statistics)
        toolbar.addAction(stats_action)
    
    def create_status_bar(self):
        """Crée la barre de statut"""
        
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Label de statut principal
        self.status_label = QLabel("Prêt")
        status_bar.addWidget(self.status_label)
        
        # Séparateur
        status_bar.addPermanentWidget(QLabel("|"))
        
        # Compteur d'opérations
        self.operations_count_label = QLabel("0 opérations")
        status_bar.addPermanentWidget(self.operations_count_label)
        
        # Séparateur
        status_bar.addPermanentWidget(QLabel("|"))
        
        # Utilisation mémoire
        self.memory_label = QLabel("Mémoire: --")
        status_bar.addPermanentWidget(self.memory_label)
    
    def create_menu_bar(self):
        """Crée la barre de menu"""
        
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        open_action = QAction('Ouvrir Vidéo', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Quitter', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Performance
        perf_menu = menubar.addMenu('Performance')
        
        diagnostic_action = QAction('Diagnostic Complet', self)
        diagnostic_action.triggered.connect(self.full_diagnostic)
        perf_menu.addAction(diagnostic_action)
        
        optimize_action = QAction('Optimisation Système', self)
        optimize_action.triggered.connect(self.system_optimization)
        perf_menu.addAction(optimize_action)
        
        perf_menu.addSeparator()
        
        cache_action = QAction('Gérer le Cache', self)
        cache_action.triggered.connect(self.manage_cache)
        perf_menu.addAction(cache_action)
        
        models_action = QAction('Gérer les Modèles', self)
        models_action.triggered.connect(self.manage_models)
        perf_menu.addAction(models_action)
        
        # Menu Aide
        help_menu = menubar.addMenu('Aide')
        
        about_action = QAction('À propos', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_system_tray(self):
        """Configure la barre d'état système"""
        
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("System tray not available")
            return
        
        # Créer l'icône de la barre d'état
        self.tray_icon = QSystemTrayIcon(self)
        
        # Utiliser une icône par défaut ou créer une icône simple
        try:
            # Essayer de charger une icône personnalisée
            icon = QIcon("icon.png")  # Vous pouvez ajouter votre icône ici
        except:
            # Créer une icône simple si aucune n'est disponible
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(self.current_theme.primary_color))
            icon = QIcon(pixmap)
        
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("AI Video Dubbing - Enhanced")
        
        # Menu contextuel de la barre d'état
        tray_menu = QMenu()
        
        # Actions du menu
        show_action = QAction("Afficher", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Masquer", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        diagnostic_action = QAction("Diagnostic Rapide", self)
        diagnostic_action.triggered.connect(self.quick_diagnostic)
        tray_menu.addAction(diagnostic_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connecter les signaux
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Afficher l'icône
        self.tray_icon.show()
        
        self.logger.info("System tray configured")
    
    def tray_icon_activated(self, reason):
        """Gère l'activation de l'icône de la barre d'état"""
        
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def show_tray_notification(self, title: str, message: str, icon_type=QSystemTrayIcon.Information):
        """Affiche une notification dans la barre d'état système"""
        
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon_type, 3000)  # 3 secondes
    
    def apply_theme(self):
        """Applique le thème à l'interface"""
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.current_theme.background_color};
                color: {self.current_theme.text_color};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.current_theme.primary_color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {self.current_theme.background_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.current_theme.primary_color};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.current_theme.primary_color};
                color: white;
            }}
        """)
    
    def setup_performance_components(self):
        """Initialise les composants de performance"""
        
        try:
            # Enhanced AI Manager
            self.ai_manager = EnhancedAIModelManager()
            
            # Interface asynchrone unifiée
            self.async_interface = UnifiedAsyncInterface()
            
            # Gestionnaire de notifications
            self.notification_manager = SmartNotificationManager()
            
            # Moteur de diagnostic
            self.diagnostic_engine = DiagnosticEngine()
            
            self.logger.info("Performance components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize performance components: {e}")
            self.show_error("Erreur d'initialisation", 
                          f"Impossible d'initialiser les composants de performance: {e}")
    
    def setup_connections(self):
        """Configure les connexions entre les composants"""
        
        # Connexions des signaux internes
        self.cancel_operation_requested.connect(self.handle_cancel_operation)
        self.notification_action_requested.connect(self.handle_notification_action)
        self.diagnostic_requested.connect(self.handle_diagnostic_request)
        self.optimization_requested.connect(self.handle_optimization_request)
        
        # Connexions des composants de performance
        if self.async_interface:
            self.async_interface.add_progress_callback(self.handle_progress_update)
            self.async_interface.add_completion_callback(self.handle_operation_completion)
        
        if self.notification_manager:
            self.notification_manager.add_global_callback(self.handle_new_notification)
    
    def start_auto_updates(self):
        """Démarre les mises à jour automatiques"""
        
        # Timer pour les mises à jour de statut
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Toutes les secondes
        
        # Timer pour les métriques système
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_system_metrics)
        self.metrics_timer.start(5000)  # Toutes les 5 secondes
    
    # Méthodes d'interface utilisateur
    
    def browse_file(self):
        """Ouvre le dialogue de sélection de fichier"""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def update_quality_label(self, value):
        """Met à jour le label du seuil de qualité"""
        self.quality_label.setText(f"{value}%")
    
    def start_transcription(self):
        """Démarre la transcription"""
        
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            self.show_error("Erreur", "Veuillez sélectionner un fichier vidéo")
            return
        
        if not Path(file_path).exists():
            self.show_error("Erreur", "Le fichier sélectionné n'existe pas")
            return
        
        # Créer la configuration
        mode_map = {
            "Fast": TranscriptionMode.FAST,
            "Balanced": TranscriptionMode.BALANCED,
            "Quality": TranscriptionMode.QUALITY,
            "Adaptive": TranscriptionMode.ADAPTIVE
        }
        
        config = TranscriptionConfig(
            mode=mode_map[self.mode_combo.currentText()],
            language=self.language_combo.currentText() if self.language_combo.currentText() != "Auto" else None,
            enable_fallback=self.enable_fallback_check.isChecked(),
            enable_caching=self.enable_cache_check.isChecked(),
            quality_threshold=self.quality_slider.value() / 100.0
        )
        
        # Démarrer l'opération asynchrone
        self.start_async_transcription(file_path, config)
    
    def start_async_transcription(self, file_path: str, config: TranscriptionConfig):
        """Démarre la transcription de manière asynchrone"""
        
        if not self.ai_manager or not self.async_interface:
            self.show_error("Erreur", "Composants de performance non initialisés")
            return
        
        try:
            # Fonction de transcription à exécuter
            async def transcription_operation(progress_callback):
                return await self.ai_manager.transcribe_with_performance_optimization(
                    audio_path=file_path,
                    config=config,
                    progress_callback=progress_callback
                )
            
            # Démarrer l'opération
            operation_id = asyncio.create_task(
                self.async_interface.start_operation(
                    operation_type=OperationType.TRANSCRIPTION,
                    operation_func=transcription_operation,
                    estimated_duration=self.estimate_transcription_duration(file_path),
                    metadata={
                        "file_path": file_path,
                        "mode": config.mode.value,
                        "language": config.language
                    }
                )
            )
            
            # Ajouter à l'interface de progression
            self.progress_widget.add_operation(
                operation_id.get_name() if hasattr(operation_id, 'get_name') else str(operation_id),
                "Transcription",
                Path(file_path).name
            )
            
            # Mettre à jour l'état de l'interface
            self.is_processing = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Transcription en cours...")
            
            self.logger.info(f"Started transcription for {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to start transcription: {e}")
            self.show_error("Erreur", f"Impossible de démarrer la transcription: {e}")
    
    def stop_all_operations(self):
        """Arrête toutes les opérations en cours"""
        
        if self.async_interface:
            asyncio.create_task(self.async_interface.cancel_all_operations())
        
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Opérations annulées")
    
    def estimate_transcription_duration(self, file_path: str) -> float:
        """Estime la durée de transcription"""
        # Estimation basique - dans une vraie implémentation, analyser le fichier
        return 120.0  # 2 minutes par défaut
    
    # Gestionnaires d'événements
    
    def handle_progress_update(self, progress):
        """Gère les mises à jour de progression"""
        
        self.progress_widget.update_operation(
            progress.operation_id,
            progress.progress_percent,
            progress.current_step,
            progress.remaining_time
        )
    
    def handle_operation_completion(self, result):
        """Gère la completion d'une opération"""
        
        self.progress_widget.complete_operation(
            result.operation_id,
            result.success,
            "Terminé avec succès" if result.success else result.error
        )
        
        if result.success and result.result:
            # Afficher les résultats de transcription
            if hasattr(result.result, 'transcription') and hasattr(result.result.transcription, 'result'):
                text = result.result.transcription.result.text
                self.results_text.append(f"✅ Transcription terminée:\n{text}\n")
        
        # Mettre à jour l'état si c'était la dernière opération
        if not self.async_interface.list_active_operations():
            self.is_processing = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Prêt")
    
    def handle_new_notification(self, notification):
        """Gère les nouvelles notifications"""
        self.notification_widget.add_notification(notification)
    
    def handle_cancel_operation(self, operation_id: str):
        """Gère l'annulation d'une opération"""
        if self.async_interface:
            asyncio.create_task(self.async_interface.cancel_operation(operation_id))
    
    def handle_notification_action(self, action: str, notification):
        """Gère les actions de notification"""
        self.logger.info(f"Executing notification action: {action}")
        # Implémenter les actions spécifiques selon le type
    
    def handle_diagnostic_request(self):
        """Gère les demandes de diagnostic"""
        if self.diagnostic_engine:
            # Démarrer un diagnostic asynchrone
            self.diagnostic_widget.add_diagnostic_result("🔍 Diagnostic en cours...")
    
    def handle_optimization_request(self):
        """Gère les demandes d'optimisation"""
        if self.ai_manager:
            # Démarrer une optimisation asynchrone
            self.diagnostic_widget.add_diagnostic_result("⚡ Optimisation en cours...")
    
    # Méthodes utilitaires
    
    def update_status(self):
        """Met à jour la barre de statut"""
        
        if self.async_interface:
            active_ops = len(self.async_interface.list_active_operations())
            self.operations_count_label.setText(f"{active_ops} opération{'s' if active_ops != 1 else ''}")
    
    def update_system_metrics(self):
        """Met à jour les métriques système"""
        
        # Simulation - dans une vraie implémentation, utiliser psutil
        import random
        memory_usage = random.randint(30, 80)
        self.memory_label.setText(f"Mémoire: {memory_usage}%")
    
    def show_error(self, title: str, message: str):
        """Affiche un message d'erreur"""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Affiche un message d'information"""
        QMessageBox.information(self, title, message)
    
    # Actions de menu et toolbar
    
    def quick_diagnostic(self):
        """Diagnostic rapide"""
        self.diagnostic_widget.run_diagnostic()
    
    def quick_optimize(self):
        """Optimisation rapide"""
        self.diagnostic_widget.optimize_system()
    
    def cleanup_resources(self):
        """Nettoie les ressources"""
        if self.ai_manager:
            asyncio.create_task(self.ai_manager.cleanup_resources())
        self.show_info("Nettoyage", "Nettoyage des ressources en cours...")
    
    def show_statistics(self):
        """Affiche les statistiques"""
        if self.async_interface:
            stats = self.async_interface.get_operation_statistics()
            stats_text = f"""Statistiques des opérations:
            
Total: {stats['total_operations']}
Actives: {stats['active_operations']}
Terminées: {stats['completed_operations']}
Échouées: {stats['failed_operations']}
Annulées: {stats['cancelled_operations']}

Durée moyenne: {stats['average_duration']:.2f}s
"""
            self.show_info("Statistiques", stats_text)
    
    def full_diagnostic(self):
        """Diagnostic complet"""
        self.diagnostic_widget.run_diagnostic()
    
    def system_optimization(self):
        """Optimisation système"""
        self.diagnostic_widget.optimize_system()
    
    def manage_cache(self):
        """Gestion du cache"""
        try:
            if hasattr(self.ai_manager, 'cache_manager'):
                cache_manager = self.ai_manager.cache_manager
                
                # Obtenir les statistiques du cache
                cache_info = {
                    "Taille du cache": f"{cache_manager.get_cache_size() / (1024*1024):.1f} MB",
                    "Nombre d'entrées": cache_manager.get_cache_count(),
                    "Dernière utilisation": cache_manager.get_last_access_time(),
                }
                
                # Créer le dialogue de gestion du cache
                dialog = QDialog(self)
                dialog.setWindowTitle("Gestionnaire de Cache")
                dialog.setModal(True)
                dialog.resize(400, 300)
                
                layout = QVBoxLayout(dialog)
                
                # Informations du cache
                info_group = QGroupBox("Informations du Cache")
                info_layout = QVBoxLayout(info_group)
                
                for key, value in cache_info.items():
                    info_layout.addWidget(QLabel(f"{key}: {value}"))
                
                layout.addWidget(info_group)
                
                # Actions
                actions_group = QGroupBox("Actions")
                actions_layout = QVBoxLayout(actions_group)
                
                clear_cache_btn = QPushButton("Vider le Cache")
                clear_cache_btn.clicked.connect(lambda: self.clear_cache_and_refresh(cache_manager, dialog))
                actions_layout.addWidget(clear_cache_btn)
                
                optimize_cache_btn = QPushButton("Optimiser le Cache")
                optimize_cache_btn.clicked.connect(lambda: self.optimize_cache_and_refresh(cache_manager, dialog))
                actions_layout.addWidget(optimize_cache_btn)
                
                layout.addWidget(actions_group)
                
                # Boutons de dialogue
                button_box = QDialogButtonBox(QDialogButtonBox.Close)
                button_box.rejected.connect(dialog.reject)
                layout.addWidget(button_box)
                
                dialog.exec_()
            else:
                self.show_info("Cache", "Gestionnaire de cache non disponible")
                
        except Exception as e:
            self.show_error("Erreur Cache", f"Erreur lors de l'accès au cache: {e}")
    
    def clear_cache_and_refresh(self, cache_manager, dialog):
        """Vide le cache et rafraîchit l'affichage"""
        try:
            cache_manager.clear_cache()
            self.show_tray_notification("Cache", "Cache vidé avec succès")
            dialog.accept()
        except Exception as e:
            self.show_error("Erreur", f"Erreur lors du vidage du cache: {e}")
    
    def optimize_cache_and_refresh(self, cache_manager, dialog):
        """Optimise le cache et rafraîchit l'affichage"""
        try:
            cache_manager.optimize_cache()
            self.show_tray_notification("Cache", "Cache optimisé avec succès")
            dialog.accept()
        except Exception as e:
            self.show_error("Erreur", f"Erreur lors de l'optimisation du cache: {e}")
    
    def manage_models(self):
        """Gestion des modèles"""
        try:
            if hasattr(self.ai_manager, 'model_manager'):
                model_manager = self.ai_manager.model_manager
                
                # Créer le dialogue de gestion des modèles
                dialog = QDialog(self)
                dialog.setWindowTitle("Gestionnaire de Modèles")
                dialog.setModal(True)
                dialog.resize(600, 400)
                
                layout = QVBoxLayout(dialog)
                
                # Liste des modèles
                models_group = QGroupBox("Modèles Disponibles")
                models_layout = QVBoxLayout(models_group)
                
                # Table des modèles
                models_table = QTableWidget()
                models_table.setColumnCount(4)
                models_table.setHorizontalHeaderLabels(["Nom", "Taille", "Statut", "Dernière utilisation"])
                
                # Remplir la table avec les modèles disponibles
                available_models = model_manager.get_available_models()
                models_table.setRowCount(len(available_models))
                
                for i, model in enumerate(available_models):
                    models_table.setItem(i, 0, QTableWidgetItem(model.name))
                    models_table.setItem(i, 1, QTableWidgetItem(f"{model.size_mb} MB"))
                    models_table.setItem(i, 2, QTableWidgetItem(model.status))
                    models_table.setItem(i, 3, QTableWidgetItem(str(model.last_used or "Jamais")))
                
                models_layout.addWidget(models_table)
                layout.addWidget(models_group)
                
                # Actions sur les modèles
                actions_group = QGroupBox("Actions")
                actions_layout = QHBoxLayout(actions_group)
                
                download_btn = QPushButton("Télécharger Nouveau")
                download_btn.clicked.connect(lambda: self.download_model_dialog(model_manager))
                actions_layout.addWidget(download_btn)
                
                validate_btn = QPushButton("Valider Modèles")
                validate_btn.clicked.connect(lambda: self.validate_models(model_manager))
                actions_layout.addWidget(validate_btn)
                
                cleanup_btn = QPushButton("Nettoyer")
                cleanup_btn.clicked.connect(lambda: self.cleanup_models(model_manager))
                actions_layout.addWidget(cleanup_btn)
                
                layout.addWidget(actions_group)
                
                # Boutons de dialogue
                button_box = QDialogButtonBox(QDialogButtonBox.Close)
                button_box.rejected.connect(dialog.reject)
                layout.addWidget(button_box)
                
                dialog.exec_()
            else:
                self.show_info("Modèles", "Gestionnaire de modèles non disponible")
                
        except Exception as e:
            self.show_error("Erreur Modèles", f"Erreur lors de l'accès aux modèles: {e}")
    
    def download_model_dialog(self, model_manager):
        """Dialogue pour télécharger un nouveau modèle"""
        model_name, ok = QInputDialog.getText(self, "Télécharger Modèle", "Nom du modèle à télécharger:")
        if ok and model_name:
            try:
                # Lancer le téléchargement en arrière-plan
                self.show_tray_notification("Téléchargement", f"Téléchargement de {model_name} commencé")
                # Ici vous pourriez ajouter la logique de téléchargement asynchrone
            except Exception as e:
                self.show_error("Erreur", f"Erreur lors du téléchargement: {e}")
    
    def validate_models(self, model_manager):
        """Valide tous les modèles"""
        try:
            # Validation des modèles
            self.show_tray_notification("Validation", "Validation des modèles en cours...")
            # Ici vous pourriez ajouter la logique de validation
        except Exception as e:
            self.show_error("Erreur", f"Erreur lors de la validation: {e}")
    
    def cleanup_models(self, model_manager):
        """Nettoie les modèles inutilisés"""
        try:
            # Nettoyage des modèles
            self.show_tray_notification("Nettoyage", "Nettoyage des modèles terminé")
            # Ici vous pourriez ajouter la logique de nettoyage
        except Exception as e:
            self.show_error("Erreur", f"Erreur lors du nettoyage: {e}")
    
    def show_about(self):
        """Affiche les informations sur l'application"""
        about_text = """AI Video Dubbing - Enhanced Interface

Version: 2.0.0
Avec optimisations de performance avancées

Fonctionnalités:
• Transcription avec IA optimisée
• Feedback temps réel
• Système de fallback intelligent
• Notifications avancées
• Diagnostic et optimisation automatiques
• Interface utilisateur moderne

© 2024 - Développé avec PyQt5"""
        
        self.show_info("À propos", about_text)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        
        if self.is_processing:
            reply = QMessageBox.question(
                self,
                "Fermeture",
                "Des opérations sont en cours. Voulez-vous vraiment quitter?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Arrêter tous les composants
        if self.async_interface:
            asyncio.create_task(self.async_interface.shutdown())
        
        if self.ai_manager:
            asyncio.create_task(self.ai_manager.shutdown())
        
        if self.notification_manager:
            asyncio.create_task(self.notification_manager.close())
        
        self.logger.info("Enhanced Main Window closing")
        event.accept()


def main():
    """Fonction principale pour lancer l'application"""
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI Video Dubbing Enhanced")
    app.setApplicationVersion("2.0.0")
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer et afficher la fenêtre principale
    window = EnhancedMainWindow()
    window.show()
    
    # Lancer l'application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()