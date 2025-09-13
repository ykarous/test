#!/usr/bin/env python3
"""
Panneau de configuration PyQt5 pour l'application de doublage vidéo par IA.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QSlider, QTextEdit, QFileDialog,
    QMessageBox, QProgressBar, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont

from .ffmpeg_config_widget import FFmpegConfigWidget
from .nemo_model_downloader import NemoModelDownloader
from ..models.data_models import PipelineConfig
from ..utils.config_manager import get_config_manager

class ConfigPanelQt(QWidget):
    """Panneau de configuration PyQt5 avec intégration FFmpeg."""
    
    config_changed = pyqtSignal(object)  # Signal émis quand la configuration change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("AI_Video_Dubbing", "Config")
        
        # Gestionnaire de configuration persistante
        self.config_manager = get_config_manager()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel("⚙️ Configuration du Pipeline")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Onglets de configuration
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Onglet Général
        general_tab = self.create_general_tab()
        self.tabs.addTab(general_tab, "Général")
        
        # Onglet Modèles IA
        models_tab = self.create_models_tab()
        self.tabs.addTab(models_tab, "Modèles IA")
        
        # Onglet Sortie
        output_tab = self.create_output_tab()
        self.tabs.addTab(output_tab, "Sortie")
        
        # Onglet FFmpeg
        ffmpeg_tab = self.create_ffmpeg_tab()
        self.tabs.addTab(ffmpeg_tab, "FFmpeg")
        
        # Onglet Système
        system_tab = self.create_system_tab()
        self.tabs.addTab(system_tab, "Système")
        
        # Onglet Configuration
        config_tab = self.create_config_management_tab()
        self.tabs.addTab(config_tab, "Configuration")
        
        # Onglet Téléchargement Modèles NeMo
        nemo_download_tab = self.create_nemo_download_tab()
        self.tabs.addTab(nemo_download_tab, "📥 Modèles NeMo")
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("🔄 Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_configuration)
        buttons_layout.addWidget(self.reset_btn)
        
        self.load_btn = QPushButton("📁 Charger")
        self.load_btn.clicked.connect(self.load_configuration_from_file)
        buttons_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 Sauvegarder")
        self.save_btn.clicked.connect(self.save_configuration_to_file)
        buttons_layout.addWidget(self.save_btn)
        
        buttons_layout.addStretch()
        
        self.apply_btn = QPushButton("✅ Appliquer")
        self.apply_btn.clicked.connect(self.apply_configuration)
        buttons_layout.addWidget(self.apply_btn)
        
        layout.addLayout(buttons_layout)
    
    def _load_default_settings(self):
        """Charge les paramètres par défaut."""
        try:
            default_config = PipelineConfig()
            self.load_config(default_config)
            self.logger.info("Default settings loaded")
        except Exception as e:
            self.logger.error(f"Failed to load default settings: {e}")
    
    def create_general_tab(self):
        """Crée l'onglet des options générales."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Options de traitement
        processing_group = QGroupBox("Options de traitement")
        processing_layout = QVBoxLayout(processing_group)
        
        self.source_separation_cb = QCheckBox("Activer la séparation de source audio")
        self.source_separation_cb.setToolTip("Sépare la voix de la musique et des effets sonores")
        processing_layout.addWidget(self.source_separation_cb)
        
        self.ocr_cb = QCheckBox("Activer l'extraction OCR des sous-titres")
        self.ocr_cb.setToolTip("Extrait le texte des sous-titres incrustés dans la vidéo")
        processing_layout.addWidget(self.ocr_cb)
        
        layout.addWidget(processing_group)
        
        # Langue cible
        language_group = QGroupBox("Langue")
        language_layout = QHBoxLayout(language_group)
        
        language_layout.addWidget(QLabel("Langue cible:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["fr", "en", "es", "de", "it", "pt"])
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        
        layout.addWidget(language_group)
        layout.addStretch()
        
        return tab
    
    def create_models_tab(self):
        """Crée l'onglet des modèles IA."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Modèles ASR
        asr_group = QGroupBox("Reconnaissance vocale (ASR)")
        asr_layout = QVBoxLayout(asr_group)
        
        asr_row = QHBoxLayout()
        asr_row.addWidget(QLabel("Modèle ASR:"))
        self.asr_combo = QComboBox()
        asr_options = [
            "whisper-tiny", "whisper-base", "whisper-small",
            "whisper-medium", "whisper-large-v3",
            "nemo-conformer-ctc-large-fr", "nemo-conformer-ctc-large-en",
            "nemo-fastconformer-multilingual", "lm-studio-whisper"
        ]
        self.asr_combo.addItems(asr_options)
        asr_row.addWidget(self.asr_combo)
        
        self.refresh_lm_btn = QPushButton("🔄 Actualiser LM Studio")
        self.refresh_lm_btn.clicked.connect(self.refresh_lm_studio_models)
        asr_row.addWidget(self.refresh_lm_btn)
        asr_row.addStretch()
        
        asr_layout.addLayout(asr_row)
        layout.addWidget(asr_group)
        
        # Modèles OCR
        ocr_group = QGroupBox("Reconnaissance optique (OCR)")
        ocr_layout = QHBoxLayout(ocr_group)
        
        ocr_layout.addWidget(QLabel("Modèle OCR:"))
        self.ocr_combo = QComboBox()
        ocr_options = [
            "paddleocr", "easyocr", "nemo-vision-transformer",
            "nemo-multimodal-llm", "lm-studio-vision"
        ]
        self.ocr_combo.addItems(ocr_options)
        ocr_layout.addWidget(self.ocr_combo)
        ocr_layout.addStretch()
        
        layout.addWidget(ocr_group)
        
        # Modèles de clonage vocal
        voice_group = QGroupBox("Clonage vocal")
        voice_layout = QHBoxLayout(voice_group)
        
        voice_layout.addWidget(QLabel("Modèle de clonage:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["tortoise-tts", "bark", "nemo-tts"])
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        
        layout.addWidget(voice_group)
        
        # Informations sur les modèles
        models_info_group = QGroupBox("Informations sur les modèles")
        models_info_layout = QVBoxLayout(models_info_group)
        
        self.models_status_text = QTextEdit()
        self.models_status_text.setMaximumHeight(150)
        self.models_status_text.setReadOnly(True)
        models_info_layout.addWidget(self.models_status_text)
        
        self.check_models_btn = QPushButton("🔍 Vérifier les modèles disponibles")
        self.check_models_btn.clicked.connect(self.check_available_models)
        models_info_layout.addWidget(self.check_models_btn)
        
        layout.addWidget(models_info_group)
        layout.addStretch()
        
        return tab
    
    def create_output_tab(self):
        """Crée l'onglet des options de sortie."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Codec vidéo
        codec_group = QGroupBox("Encodage vidéo")
        codec_layout = QVBoxLayout(codec_group)
        
        codec_row = QHBoxLayout()
        codec_row.addWidget(QLabel("Codec:"))
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["h264", "h265", "vp9", "av1"])
        codec_row.addWidget(self.codec_combo)
        codec_row.addStretch()
        codec_layout.addLayout(codec_row)
        
        bitrate_row = QHBoxLayout()
        bitrate_row.addWidget(QLabel("Débit:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["2M", "5M", "8M", "10M", "15M", "20M"])
        bitrate_row.addWidget(self.bitrate_combo)
        bitrate_row.addStretch()
        codec_layout.addLayout(bitrate_row)
        
        layout.addWidget(codec_group)
        layout.addStretch()
        
        return tab
    
    def create_ffmpeg_tab(self):
        """Crée l'onglet de configuration FFmpeg."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Widget de configuration FFmpeg
        self.ffmpeg_widget = FFmpegConfigWidget()
        self.ffmpeg_widget.ffmpeg_configured.connect(self.on_ffmpeg_configured)
        layout.addWidget(self.ffmpeg_widget)
        
        return tab
    
    def create_system_tab(self):
        """Crée l'onglet des options système."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Gestion mémoire
        memory_group = QGroupBox("Gestion mémoire")
        memory_layout = QVBoxLayout(memory_group)
        
        memory_row = QHBoxLayout()
        memory_row.addWidget(QLabel("Utilisation mémoire max:"))
        
        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(30)
        self.memory_slider.setMaximum(90)
        self.memory_slider.setValue(70)
        self.memory_slider.valueChanged.connect(self.update_memory_label)
        memory_row.addWidget(self.memory_slider)
        
        self.memory_label = QLabel("70%")
        memory_row.addWidget(self.memory_label)
        
        memory_layout.addLayout(memory_row)
        layout.addWidget(memory_group)
        
        # Répertoire temporaire
        temp_group = QGroupBox("Fichiers temporaires")
        temp_layout = QVBoxLayout(temp_group)
        
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("Répertoire:"))
        
        self.temp_path_edit = QLineEdit()
        self.temp_path_edit.setPlaceholderText("Répertoire temporaire par défaut")
        temp_row.addWidget(self.temp_path_edit)
        
        self.temp_browse_btn = QPushButton("📁 Parcourir")
        self.temp_browse_btn.clicked.connect(self.browse_temp_directory)
        temp_row.addWidget(self.temp_browse_btn)
        
        temp_layout.addLayout(temp_row)
        layout.addWidget(temp_group)
        
        layout.addStretch()
        
        return tab
    
    def create_config_management_tab(self):
        """Crée l'onglet de gestion de configuration."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Informations sur la configuration
        info_group = QGroupBox("Informations Configuration")
        info_layout = QVBoxLayout(info_group)
        
        self.config_info_text = QTextEdit()
        self.config_info_text.setMaximumHeight(150)
        self.config_info_text.setReadOnly(True)
        info_layout.addWidget(self.config_info_text)
        
        self.refresh_config_info_btn = QPushButton("🔄 Actualiser Infos")
        self.refresh_config_info_btn.clicked.connect(self.refresh_config_info)
        info_layout.addWidget(self.refresh_config_info_btn)
        
        layout.addWidget(info_group)
        
        # Configuration NeMo
        nemo_group = QGroupBox("Configuration NVIDIA NeMo")
        nemo_layout = QVBoxLayout(nemo_group)
        
        # Sélection dispositif
        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Dispositif de calcul:"))
        self.nemo_device_combo = QComboBox()
        self.nemo_device_combo.addItems(["auto", "gpu", "cpu"])
        device_row.addWidget(self.nemo_device_combo)
        
        self.force_cpu_cb = QCheckBox("Forcer CPU")
        device_row.addWidget(self.force_cpu_cb)
        device_row.addStretch()
        nemo_layout.addLayout(device_row)
        
        # Modèles NeMo
        models_row = QHBoxLayout()
        models_row.addWidget(QLabel("Modèle ASR:"))
        self.nemo_asr_combo = QComboBox()
        self.nemo_asr_combo.addItems([
            "stt_fr_conformer_ctc_large",
            "stt_en_conformer_ctc_large", 
            "stt_multilingual_fastconformer_hybrid_large_pc"
        ])
        models_row.addWidget(self.nemo_asr_combo)
        models_row.addStretch()
        nemo_layout.addLayout(models_row)
        
        layout.addWidget(nemo_group)
        
        # Actions de configuration
        actions_group = QGroupBox("Actions Configuration")
        actions_layout = QVBoxLayout(actions_group)
        
        # Sauvegarde manuelle
        save_row = QHBoxLayout()
        self.manual_save_btn = QPushButton("💾 Sauvegarder Maintenant")
        self.manual_save_btn.clicked.connect(self.manual_save_config)
        save_row.addWidget(self.manual_save_btn)
        
        self.backup_btn = QPushButton("📦 Créer Sauvegarde")
        self.backup_btn.clicked.connect(self.create_config_backup)
        save_row.addWidget(self.backup_btn)
        save_row.addStretch()
        actions_layout.addLayout(save_row)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        
        # Charger les infos au démarrage
        self.refresh_config_info()
        self.load_nemo_settings()
        
        return tab
    
    def on_ffmpeg_configured(self, success: bool):
        """Appelé quand FFmpeg est configuré."""
        if success:
            self.logger.info("FFmpeg configured successfully")
        else:
            self.logger.warning("FFmpeg configuration failed")
    
    def get_ffmpeg_manager(self):
        """Retourne le gestionnaire FFmpeg."""
        if hasattr(self, 'ffmpeg_widget'):
            return self.ffmpeg_widget.get_ffmpeg_manager()
        return None
    
    def refresh_lm_studio_models(self):
        """Actualise la liste des modèles LM Studio disponibles."""
        try:
            from ..processors.lm_studio_manager import LMStudioManager
            
            lm_manager = LMStudioManager()
            
            if not lm_manager.is_available():
                QMessageBox.information(
                    self,
                    "LM Studio",
                    "LM Studio n'est pas disponible ou n'est pas en cours d'exécution."
                )
                return
            
            # Obtenir les modèles disponibles
            available_models = lm_manager.get_available_models()
            
            if not available_models:
                QMessageBox.information(
                    self,
                    "LM Studio",
                    "Aucun modèle trouvé dans LM Studio."
                )
                return
            
            # Mettre à jour les listes déroulantes
            transcription_models = lm_manager.get_models_for_transcription()
            ocr_models = lm_manager.get_models_for_ocr()
            
            # Ajouter les nouveaux modèles
            for model in transcription_models:
                model_name = f"lm-studio-{model['name']}"
                if self.asr_combo.findText(model_name) == -1:
                    self.asr_combo.addItem(model_name)
            
            for model in ocr_models:
                model_name = f"lm-studio-{model['name']}"
                if self.ocr_combo.findText(model_name) == -1:
                    self.ocr_combo.addItem(model_name)
            
            QMessageBox.information(
                self,
                "LM Studio",
                f"Modèles LM Studio actualisés:\n"
                f"- {len(transcription_models)} modèles de transcription\n"
                f"- {len(ocr_models)} modèles OCR/Vision"
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de l'actualisation LM Studio: {e}"
            )
    
    def check_available_models(self):
        """Vérifie et affiche les modèles disponibles."""
        try:
            from ..processors.ai_model_manager import AIModelManager
            
            ai_manager = AIModelManager()
            models_summary = ai_manager.get_available_models_summary()
            
            # Construire le texte d'information
            info_lines = []
            info_lines.append("=== MODÈLES DISPONIBLES ===\n")
            
            # Modèles locaux
            local_models = models_summary.get("local_models", {})
            info_lines.append("📁 MODÈLES LOCAUX:")
            info_lines.append(f"  ASR: {len(local_models.get('asr', []))} modèles")
            info_lines.append(f"  OCR: {len(local_models.get('ocr', []))} modèles")
            info_lines.append(f"  Clonage vocal: {len(local_models.get('voice_cloning', []))} modèles")
            info_lines.append("")
            
            # Modèles LM Studio
            lm_models = models_summary.get("lm_studio_models", {})
            if lm_models.get("available", False):
                info_lines.append("🤖 LM STUDIO:")
                info_lines.append(f"  Total: {lm_models.get('total_models', 0)} modèles")
                info_lines.append(f"  Transcription: {lm_models.get('transcription_models', 0)} modèles")
                info_lines.append(f"  OCR: {lm_models.get('ocr_models', 0)} modèles")
            else:
                info_lines.append("🤖 LM STUDIO: Non disponible")
            info_lines.append("")
            
            # Modèles NeMo
            nemo_models = models_summary.get("nemo_models", {})
            if nemo_models.get("available", False):
                info_lines.append("🚀 NVIDIA NEMO:")
                info_lines.append(f"  ASR: {len(nemo_models.get('asr_models', []))} modèles")
                info_lines.append(f"  OCR: {len(nemo_models.get('ocr_models', []))} modèles")
            else:
                info_lines.append("🚀 NVIDIA NEMO: Non installé")
            
            # Afficher dans le widget de texte
            self.models_status_text.setText("\n".join(info_lines))
            
        except Exception as e:
            self.models_status_text.setText(f"Erreur lors de la vérification des modèles: {e}")
    
    def update_memory_label(self, value):
        """Met à jour le label de mémoire."""
        self.memory_label.setText(f"{value}%")
    
    def browse_temp_directory(self):
        """Ouvre le dialogue de sélection de répertoire temporaire."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le répertoire temporaire",
            self.temp_path_edit.text()
        )
        
        if directory:
            self.temp_path_edit.setText(directory)
    
    def get_current_config(self) -> PipelineConfig:
        """Retourne la configuration actuelle."""
        return PipelineConfig(
            enable_source_separation=self.source_separation_cb.isChecked(),
            enable_ocr=self.ocr_cb.isChecked(),
            asr_model=self.asr_combo.currentText(),
            ocr_model=self.ocr_combo.currentText(),
            voice_cloning_model=self.voice_combo.currentText(),
            target_language=self.language_combo.currentText(),
            output_codec=self.codec_combo.currentText(),
            output_bitrate=self.bitrate_combo.currentText(),
            temp_directory=self.temp_path_edit.text(),
            max_memory_usage=self.memory_slider.value() / 100.0
        )
    
    def load_config(self, config: PipelineConfig):
        """Charge une configuration dans l'interface."""
        self.source_separation_cb.setChecked(config.enable_source_separation)
        self.ocr_cb.setChecked(config.enable_ocr)
        
        # Sélectionner les éléments dans les combobox
        self.language_combo.setCurrentText(config.target_language)
        self.asr_combo.setCurrentText(config.asr_model)
        self.ocr_combo.setCurrentText(config.ocr_model)
        self.voice_combo.setCurrentText(config.voice_cloning_model)
        self.codec_combo.setCurrentText(config.output_codec)
        self.bitrate_combo.setCurrentText(config.output_bitrate)
        
        self.temp_path_edit.setText(config.temp_directory)
        self.memory_slider.setValue(int(config.max_memory_usage * 100))
    
    def load_settings(self):
        """Charge les paramètres sauvegardés depuis la configuration persistante."""
        try:
            # Charger la configuration du pipeline
            pipeline_config = self.config_manager.load_pipeline_config()
            
            # Charger les paramètres UI
            ui_settings = self.config_manager.load_ui_settings()
            
            # Appliquer la configuration du pipeline
            self.source_separation_cb.setChecked(pipeline_config.enable_source_separation)
            self.ocr_cb.setChecked(pipeline_config.enable_ocr)
            self.language_combo.setCurrentText(pipeline_config.target_language)
            self.asr_combo.setCurrentText(pipeline_config.asr_model)
            self.ocr_combo.setCurrentText(pipeline_config.ocr_model)
            self.voice_combo.setCurrentText(pipeline_config.voice_cloning_model)
            self.codec_combo.setCurrentText(pipeline_config.output_codec)
            self.bitrate_combo.setCurrentText(pipeline_config.output_bitrate)
            self.temp_path_edit.setText(pipeline_config.temp_directory)
            self.memory_slider.setValue(int(pipeline_config.max_memory_usage * 100))
            
            # Appliquer les paramètres UI spécifiques
            if ui_settings:
                # Restaurer la position des onglets, etc.
                current_tab = ui_settings.get("current_tab", 0)
                if hasattr(self, 'tabs'):
                    self.tabs.setCurrentIndex(current_tab)
            
            self.logger.info("Settings loaded from persistent configuration")
            
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
            # Fallback vers les paramètres par défaut
            self._load_default_settings()
    
    def save_settings(self):
        """Sauvegarde les paramètres actuels dans la configuration persistante."""
        try:
            # Sauvegarder la configuration du pipeline
            current_config = self.get_current_config()
            self.config_manager.save_pipeline_config(current_config)
            
            # Sauvegarder les paramètres UI
            ui_settings = {
                "current_tab": self.tabs.currentIndex() if hasattr(self, 'tabs') else 0,
                "window_geometry": self.geometry().getRect() if self.parent() else None,
                "last_temp_directory": self.temp_path_edit.text(),
                "memory_slider_position": self.memory_slider.value()
            }
            self.config_manager.save_ui_settings(ui_settings)
            
            # Sauvegarder les préférences de modèles
            model_preferences = {
                "preferred_asr": self.asr_combo.currentText(),
                "preferred_ocr": self.ocr_combo.currentText(),
                "preferred_voice": self.voice_combo.currentText(),
                "last_language": self.language_combo.currentText()
            }
            self.config_manager.save_model_preferences(model_preferences)
            
            self.logger.info("Settings saved to persistent configuration")
            
        except Exception as e:
            self.logger.warning(f"Failed to save settings: {e}")
    
    def apply_configuration(self):
        """Applique la configuration actuelle."""
        try:
            config = self.get_current_config()
            self.save_settings()
            
            # Sauvegarder aussi les paramètres NeMo
            if hasattr(self, 'nemo_device_combo'):
                self.save_nemo_settings()
            
            self.config_changed.emit(config)
            
            QMessageBox.information(
                self,
                "Configuration",
                "Configuration appliquée avec succès!\n"
                "Les paramètres sont maintenant sauvegardés de façon persistante."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de l'application de la configuration: {e}"
            )
    
    def save_configuration_to_file(self):
        """Sauvegarde la configuration actuelle dans un fichier JSON."""
        try:
            import json
            from pathlib import Path
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder la configuration",
                str(Path.home() / "config_doublage.json"),
                "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
            )
            
            if filename:
                # Obtenir la configuration actuelle
                current_config = self.get_current_config()
                
                # Convertir en dictionnaire pour la sérialisation JSON
                config_dict = {
                    "enable_source_separation": current_config.enable_source_separation,
                    "enable_ocr": current_config.enable_ocr,
                    "asr_model": current_config.asr_model,
                    "ocr_model": current_config.ocr_model,
                    "voice_cloning_model": current_config.voice_cloning_model,
                    "target_language": current_config.target_language,
                    "output_codec": current_config.output_codec,
                    "output_bitrate": current_config.output_bitrate,
                    "temp_directory": current_config.temp_directory,
                    "max_memory_usage": current_config.max_memory_usage
                }
                
                # Sauvegarder dans le fichier
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self,
                    "Sauvegarde réussie",
                    f"Configuration sauvegardée dans:\n{filename}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de sauvegarde",
                f"Impossible de sauvegarder la configuration:\n{str(e)}"
            )
    
    def load_configuration_from_file(self):
        """Charge une configuration depuis un fichier JSON."""
        try:
            import json
            from pathlib import Path
            
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Charger une configuration",
                str(Path.home()),
                "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
            )
            
            if filename:
                # Charger le fichier JSON
                with open(filename, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                # Créer un objet PipelineConfig avec les valeurs chargées
                loaded_config = PipelineConfig(
                    enable_source_separation=config_dict.get("enable_source_separation", False),
                    enable_ocr=config_dict.get("enable_ocr", False),
                    asr_model=config_dict.get("asr_model", "whisper-base"),
                    ocr_model=config_dict.get("ocr_model", "paddleocr"),
                    voice_cloning_model=config_dict.get("voice_cloning_model", "tortoise-tts"),
                    target_language=config_dict.get("target_language", "fr"),
                    output_codec=config_dict.get("output_codec", "h264"),
                    output_bitrate=config_dict.get("output_bitrate", "5M"),
                    temp_directory=config_dict.get("temp_directory", ""),
                    max_memory_usage=config_dict.get("max_memory_usage", 0.7)
                )
                
                # Charger la configuration dans l'interface
                self.load_config(loaded_config)
                
                QMessageBox.information(
                    self,
                    "Chargement réussi",
                    f"Configuration chargée depuis:\n{filename}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de chargement",
                f"Impossible de charger la configuration:\n{str(e)}"
            )
    
    def reset_configuration(self):
        """Remet la configuration par défaut."""
        reply = QMessageBox.question(
            self,
            "Réinitialiser Configuration",
            "Êtes-vous sûr de vouloir réinitialiser la configuration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            default_config = PipelineConfig()
            self.load_config(default_config)
            
            # Réinitialiser aussi FFmpeg
            if hasattr(self, 'ffmpeg_widget'):
                self.ffmpeg_widget.get_ffmpeg_manager().reset_configuration()
                self.ffmpeg_widget.update_status()
            
            QMessageBox.information(
                self,
                "Configuration",
                "Configuration réinitialisée!"
            )
    
    def refresh_config_info(self):
        """Actualise les informations de configuration."""
        try:
            summary = self.config_manager.get_config_summary()
            
            info_lines = []
            info_lines.append("=== INFORMATIONS CONFIGURATION ===\n")
            info_lines.append(f"📁 Répertoire: {summary.get('config_dir', 'N/A')}")
            info_lines.append("")
            
            info_lines.append("📄 Fichiers de configuration:")
            files_exist = summary.get('files_exist', {})
            for file_type, exists in files_exist.items():
                status = "✅" if exists else "❌"
                info_lines.append(f"  {status} {file_type}.json")
            
            info_lines.append("")
            info_lines.append("💾 Cache chargé:")
            cache_loaded = summary.get('cache_loaded', {})
            for cache_type, loaded in cache_loaded.items():
                status = "✅" if loaded else "❌"
                info_lines.append(f"  {status} {cache_type}")
            
            self.config_info_text.setText("\n".join(info_lines))
            
        except Exception as e:
            self.config_info_text.setText(f"Erreur lors du chargement des infos: {e}")
    
    def manual_save_config(self):
        """Sauvegarde manuelle de la configuration."""
        try:
            self.save_settings()
            QMessageBox.information(
                self,
                "Sauvegarde",
                "Configuration sauvegardée avec succès!"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de la sauvegarde: {e}"
            )
    
    def create_config_backup(self):
        """Crée une sauvegarde de la configuration."""
        try:
            success = self.config_manager.backup_configs()
            if success:
                QMessageBox.information(
                    self,
                    "Sauvegarde",
                    "Sauvegarde de configuration créée avec succès!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Erreur lors de la création de la sauvegarde"
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors de la sauvegarde: {e}"
            )
    
    def load_nemo_settings(self):
        """Charge les paramètres NeMo."""
        try:
            nemo_config = self.config_manager.load_nemo_config()
            
            # Appliquer les paramètres
            device_mode = nemo_config.get('device_mode', 'auto')
            self.nemo_device_combo.setCurrentText(device_mode)
            
            force_cpu = nemo_config.get('force_cpu', False)
            self.force_cpu_cb.setChecked(force_cpu)
            
            asr_model = nemo_config.get('asr_model', 'stt_fr_conformer_ctc_large')
            self.nemo_asr_combo.setCurrentText(asr_model)
            
        except Exception as e:
            self.logger.warning(f"Failed to load NeMo settings: {e}")
    
    def save_nemo_settings(self):
        """Sauvegarde les paramètres NeMo."""
        try:
            nemo_config = {
                'device_mode': self.nemo_device_combo.currentText(),
                'force_cpu': self.force_cpu_cb.isChecked(),
                'asr_model': self.nemo_asr_combo.currentText(),
                'processing_mode': 'integrated',
                'batch_size': 16,
                'gpu_memory_fraction': 0.8,
                'enable_mixed_precision': True,
                'fallback_to_whisper': True,
                'fallback_to_pyannote': True
            }
            
            self.config_manager.save_nemo_config(nemo_config)
            
        except Exception as e:
            self.logger.warning(f"Failed to save NeMo settings: {e}")
    
    def create_nemo_download_tab(self):
        """Crée l'onglet de téléchargement des modèles NeMo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Widget de téléchargement NeMo
        self.nemo_downloader = NemoModelDownloader()
        self.nemo_downloader.model_downloaded.connect(self.on_nemo_model_downloaded)
        layout.addWidget(self.nemo_downloader)
        
        return tab
    
    def on_nemo_model_downloaded(self, model_name: str, model_info: dict):
        """Appelé quand un modèle NeMo est téléchargé."""
        try:
            # Mettre à jour la liste des modèles ASR disponibles
            model_display_name = model_name.split('/')[-1]
            
            # Ajouter à la liste des modèles ASR si ce n'est pas déjà fait
            if self.asr_combo.findText(model_display_name) == -1:
                self.asr_combo.addItem(model_display_name)
            
            # Mettre à jour la liste des modèles NeMo dans l'onglet configuration
            if hasattr(self, 'nemo_asr_combo'):
                if self.nemo_asr_combo.findText(model_display_name) == -1:
                    self.nemo_asr_combo.addItem(model_display_name)
            
            # Actualiser les informations des modèles
            self.check_available_models()
            
            self.logger.info(f"Modèle NeMo ajouté aux options: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout du modèle téléchargé: {e}")