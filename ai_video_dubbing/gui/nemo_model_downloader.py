"""
Widget de téléchargement des modèles NeMo
"""

import os
import sys
import json
import signal
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QProgressBar, QTextEdit, QListWidget,
    QListWidgetItem, QMessageBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import logging

# Patch signal pour NeMo Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM

class ModelDownloadThread(QThread):
    """Thread pour télécharger les modèles NeMo en arrière-plan"""
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    download_finished = pyqtSignal(bool, str, dict)  # success, message, model_info
    
    def __init__(self, model_name: str, model_type: str):
        super().__init__()
        self.model_name = model_name
        self.model_type = model_type
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Télécharge le modèle NeMo"""
        try:
            self.progress_updated.emit(10, f"Initialisation NeMo...")
            
            # Mock Pyannote pour éviter les conflits
            from unittest.mock import MagicMock
            pyannote_modules = [
                "pyannote", "pyannote.core", "pyannote.core.utils",
                "pyannote.audio", "pyannote.audio.pipelines"
            ]
            
            for module_name in pyannote_modules:
                if module_name not in sys.modules:
                    sys.modules[module_name] = MagicMock()
            
            self.progress_updated.emit(20, f"Import NeMo...")
            import nemo.collections.asr as nemo_asr
            
            self.progress_updated.emit(30, f"Téléchargement {self.model_name}...")
            
            # Sélectionner la classe de modèle appropriée
            model_classes = {
                "FastConformer CTC": nemo_asr.models.EncDecCTCModelBPE,
                "FastConformer Hybrid": nemo_asr.models.EncDecHybridRNNTCTCBPEModel,
                "Conformer CTC": nemo_asr.models.EncDecCTCModelBPE,
                "Conformer Transducer": nemo_asr.models.EncDecRNNTBPEModel
            }
            
            model_class = model_classes.get(self.model_type, nemo_asr.models.EncDecCTCModelBPE)
            
            self.progress_updated.emit(50, f"Chargement du modèle...")
            
            # Télécharger et charger le modèle
            model = model_class.from_pretrained(self.model_name)
            
            self.progress_updated.emit(80, f"Vérification du modèle...")
            
            # Obtenir les informations du modèle
            model_info = {
                "name": self.model_name,
                "type": self.model_type,
                "class": model_class.__name__,
                "sample_rate": getattr(model, 'sample_rate', 16000),
                "vocab_size": getattr(model, 'vocab_size', 'Unknown'),
                "status": "ready",
                "download_date": str(Path.cwd()),
                "cache_location": str(Path.home() / ".cache" / "huggingface" / "hub")
            }
            
            self.progress_updated.emit(100, f"Téléchargement terminé!")
            
            self.download_finished.emit(True, f"Modèle {self.model_name} téléchargé avec succès!", model_info)
            
        except Exception as e:
            self.logger.error(f"Erreur téléchargement modèle: {e}")
            self.download_finished.emit(False, f"Erreur: {str(e)}", {})

class NemoModelDownloader(QWidget):
    """Widget pour télécharger et gérer les modèles NeMo"""
    
    model_downloaded = pyqtSignal(str, dict)  # model_name, model_info
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.download_thread = None
        self.downloaded_models = {}
        
        self.init_ui()
        self.load_available_models()
        self.load_downloaded_models()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel("📥 Téléchargement des Modèles NeMo")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Section sélection de modèle
        selection_group = QGroupBox("Sélection du Modèle")
        selection_layout = QVBoxLayout(selection_group)
        
        # Catégorie de modèle
        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Catégorie:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "ASR - Reconnaissance Vocale",
            "Diarisation - Séparation Locuteurs", 
            "VAD - Détection Voix",
            "Multilingue - Plusieurs Langues"
        ])
        self.category_combo.currentTextChanged.connect(self.update_model_list)
        category_row.addWidget(self.category_combo)
        category_row.addStretch()
        selection_layout.addLayout(category_row)
        
        # Modèle spécifique
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Modèle:"))
        self.model_combo = QComboBox()
        model_row.addWidget(self.model_combo)
        
        self.model_info_btn = QPushButton("ℹ️ Info")
        self.model_info_btn.clicked.connect(self.show_model_info)
        model_row.addWidget(self.model_info_btn)
        model_row.addStretch()
        selection_layout.addLayout(model_row)
        
        layout.addWidget(selection_group)
        
        # Section téléchargement
        download_group = QGroupBox("Téléchargement")
        download_layout = QVBoxLayout(download_group)
        
        # Bouton de téléchargement
        download_row = QHBoxLayout()
        self.download_btn = QPushButton("📥 Télécharger le Modèle")
        self.download_btn.clicked.connect(self.start_download)
        download_row.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        download_row.addWidget(self.cancel_btn)
        download_row.addStretch()
        download_layout.addLayout(download_row)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        download_layout.addWidget(self.progress_bar)
        
        # Status du téléchargement
        self.status_label = QLabel("Prêt à télécharger")
        download_layout.addWidget(self.status_label)
        
        layout.addWidget(download_group)
        
        # Section modèles téléchargés
        downloaded_group = QGroupBox("Modèles Téléchargés")
        downloaded_layout = QVBoxLayout(downloaded_group)
        
        self.downloaded_list = QListWidget()
        downloaded_layout.addWidget(self.downloaded_list)
        
        # Actions sur les modèles téléchargés
        actions_row = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_downloaded_models)
        actions_row.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.clicked.connect(self.delete_selected_model)
        actions_row.addWidget(self.delete_btn)
        
        self.test_btn = QPushButton("🧪 Tester")
        self.test_btn.clicked.connect(self.test_selected_model)
        actions_row.addWidget(self.test_btn)
        actions_row.addStretch()
        downloaded_layout.addLayout(actions_row)
        
        layout.addWidget(downloaded_group)
        
        # Section informations
        info_group = QGroupBox("Informations")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
    
    def load_available_models(self):
        """Charge la liste des modèles disponibles"""
        self.available_models = {
            "ASR - Reconnaissance Vocale": {
                "nvidia/stt_en_fastconformer_ctc_large": {
                    "type": "FastConformer CTC",
                    "language": "Anglais",
                    "size": "463MB",
                    "description": "Modèle FastConformer CTC pour l'anglais, haute précision"
                },
                "nvidia/stt_fr_fastconformer_ctc_large": {
                    "type": "FastConformer CTC", 
                    "language": "Français",
                    "size": "450MB",
                    "description": "Modèle FastConformer CTC pour le français"
                },
                "nvidia/stt_en_conformer_ctc_large": {
                    "type": "Conformer CTC",
                    "language": "Anglais", 
                    "size": "400MB",
                    "description": "Modèle Conformer CTC classique pour l'anglais"
                }
            },
            "Multilingue - Plusieurs Langues": {
                "nvidia/stt_multilingual_fastconformer_hybrid_large_pc": {
                    "type": "FastConformer Hybrid",
                    "language": "Multilingue",
                    "size": "600MB", 
                    "description": "Modèle multilingue avec support de nombreuses langues"
                }
            },
            "Diarisation - Séparation Locuteurs": {
                "nvidia/speakerverification_en_titanet_large": {
                    "type": "TitaNet",
                    "language": "Anglais",
                    "size": "200MB",
                    "description": "Modèle de vérification et diarisation de locuteurs"
                }
            },
            "VAD - Détection Voix": {
                "nvidia/vad_multilingual_marblenet": {
                    "type": "MarbleNet",
                    "language": "Multilingue", 
                    "size": "50MB",
                    "description": "Détection d'activité vocale multilingue"
                }
            }
        }
        
        self.update_model_list()
    
    def update_model_list(self):
        """Met à jour la liste des modèles selon la catégorie"""
        category = self.category_combo.currentText()
        self.model_combo.clear()
        
        if category in self.available_models:
            models = self.available_models[category]
            for model_name in models.keys():
                model_info = models[model_name]
                display_name = f"{model_name.split('/')[-1]} ({model_info['size']})"
                self.model_combo.addItem(display_name, model_name)
    
    def show_model_info(self):
        """Affiche les informations détaillées du modèle sélectionné"""
        if self.model_combo.currentData():
            model_name = self.model_combo.currentData()
            category = self.category_combo.currentText()
            
            if category in self.available_models and model_name in self.available_models[category]:
                model_info = self.available_models[category][model_name]
                
                info_text = f"""
Modèle: {model_name}
Type: {model_info['type']}
Langue: {model_info['language']}
Taille: {model_info['size']}
Description: {model_info['description']}
                """.strip()
                
                QMessageBox.information(self, "Informations du Modèle", info_text)
    
    def start_download(self):
        """Démarre le téléchargement du modèle sélectionné"""
        if not self.model_combo.currentData():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un modèle à télécharger.")
            return
        
        model_name = self.model_combo.currentData()
        category = self.category_combo.currentText()
        model_info = self.available_models[category][model_name]
        
        # Confirmer le téléchargement
        reply = QMessageBox.question(
            self,
            "Confirmer le téléchargement",
            f"Télécharger le modèle:\n{model_name}\n\nTaille: {model_info['size']}\n\nContinuer?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Démarrer le téléchargement
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.download_thread = ModelDownloadThread(model_name, model_info['type'])
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.download_finished.connect(self.download_completed)
        self.download_thread.start()
    
    def update_progress(self, progress: int, message: str):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def download_completed(self, success: bool, message: str, model_info: dict):
        """Appelé quand le téléchargement est terminé"""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("Téléchargement réussi!")
            
            # Sauvegarder les informations du modèle
            self.save_model_info(model_info)
            
            # Actualiser la liste des modèles téléchargés
            self.refresh_downloaded_models()
            
            # Émettre le signal
            self.model_downloaded.emit(model_info['name'], model_info)
            
            QMessageBox.information(self, "Succès", message)
        else:
            self.status_label.setText("Échec du téléchargement")
            QMessageBox.warning(self, "Erreur", message)
    
    def cancel_download(self):
        """Annule le téléchargement en cours"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
        
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Téléchargement annulé")
    
    def save_model_info(self, model_info: dict):
        """Sauvegarde les informations du modèle téléchargé"""
        try:
            models_file = Path("downloaded_nemo_models.json")
            
            if models_file.exists():
                with open(models_file, 'r', encoding='utf-8') as f:
                    models_data = json.load(f)
            else:
                models_data = {}
            
            models_data[model_info['name']] = model_info
            
            with open(models_file, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde info modèle: {e}")
    
    def load_downloaded_models(self):
        """Charge la liste des modèles téléchargés"""
        try:
            models_file = Path("downloaded_nemo_models.json")
            
            if models_file.exists():
                with open(models_file, 'r', encoding='utf-8') as f:
                    self.downloaded_models = json.load(f)
            else:
                self.downloaded_models = {}
            
            self.refresh_downloaded_models()
            
        except Exception as e:
            self.logger.error(f"Erreur chargement modèles téléchargés: {e}")
            self.downloaded_models = {}
    
    def refresh_downloaded_models(self):
        """Actualise la liste des modèles téléchargés"""
        self.downloaded_list.clear()
        
        for model_name, model_info in self.downloaded_models.items():
            item_text = f"{model_name.split('/')[-1]} ({model_info.get('type', 'Unknown')})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, model_name)
            self.downloaded_list.addItem(item)
        
        # Mettre à jour les informations
        self.update_info_text()
    
    def update_info_text(self):
        """Met à jour le texte d'informations"""
        total_models = len(self.downloaded_models)
        
        if total_models == 0:
            info_text = "Aucun modèle NeMo téléchargé."
        else:
            info_text = f"Modèles téléchargés: {total_models}\n"
            
            # Compter par type
            types_count = {}
            for model_info in self.downloaded_models.values():
                model_type = model_info.get('type', 'Unknown')
                types_count[model_type] = types_count.get(model_type, 0) + 1
            
            for model_type, count in types_count.items():
                info_text += f"- {model_type}: {count}\n"
        
        self.info_text.setText(info_text)
    
    def delete_selected_model(self):
        """Supprime le modèle sélectionné"""
        current_item = self.downloaded_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un modèle à supprimer.")
            return
        
        model_name = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer le modèle:\n{model_name}\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Supprimer des données
            if model_name in self.downloaded_models:
                del self.downloaded_models[model_name]
                self.save_downloaded_models()
                self.refresh_downloaded_models()
                
                QMessageBox.information(self, "Succès", "Modèle supprimé de la liste.")
    
    def test_selected_model(self):
        """Teste le modèle sélectionné"""
        current_item = self.downloaded_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un modèle à tester.")
            return
        
        model_name = current_item.data(Qt.UserRole)
        
        # Lancer un test simple
        QMessageBox.information(
            self,
            "Test du modèle",
            f"Test du modèle {model_name}...\n\n"
            "Cette fonctionnalité sera implémentée prochainement."
        )
    
    def save_downloaded_models(self):
        """Sauvegarde la liste des modèles téléchargés"""
        try:
            models_file = Path("downloaded_nemo_models.json")
            with open(models_file, 'w', encoding='utf-8') as f:
                json.dump(self.downloaded_models, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde modèles: {e}")
    
    def get_downloaded_models(self) -> Dict[str, dict]:
        """Retourne la liste des modèles téléchargés"""
        return self.downloaded_models.copy()