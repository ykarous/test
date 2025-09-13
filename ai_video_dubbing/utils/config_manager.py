#!/usr/bin/env python3
"""
Gestionnaire de configuration persistante pour l'application de doublage vidéo par IA.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict
import threading

from ..models.data_models import PipelineConfig

class ConfigManager:
    """Gestionnaire de configuration avec sauvegarde automatique."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_dir: Répertoire de configuration (par défaut: ~/.ai_video_dubbing)
        """
        self.logger = logging.getLogger(__name__)
        
        # Définir le répertoire de configuration
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Utiliser le répertoire utilisateur
            home_dir = Path.home()
            self.config_dir = home_dir / ".ai_video_dubbing"
        
        # Créer le répertoire s'il n'existe pas
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichiers de configuration
        self.main_config_file = self.config_dir / "config.json"
        self.models_config_file = self.config_dir / "models.json"
        self.ui_config_file = self.config_dir / "ui_settings.json"
        self.lm_studio_config_file = self.config_dir / "lm_studio.json"
        self.nemo_config_file = self.config_dir / "nemo.json"
        
        # Cache de configuration
        self._config_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        
        # Charger la configuration existante
        self._load_all_configs()
        
        self.logger.info(f"Configuration manager initialized: {self.config_dir}")
    
    def _load_all_configs(self):
        """Charge toutes les configurations au démarrage."""
        config_files = {
            'main': self.main_config_file,
            'models': self.models_config_file,
            'ui': self.ui_config_file,
            'lm_studio': self.lm_studio_config_file,
            'nemo': self.nemo_config_file
        }
        
        for config_name, config_file in config_files.items():
            try:
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self._config_cache[config_name] = json.load(f)
                    self.logger.debug(f"Loaded {config_name} config from {config_file}")
                else:
                    self._config_cache[config_name] = {}
                    self.logger.debug(f"No existing {config_name} config, using defaults")
            except Exception as e:
                self.logger.error(f"Error loading {config_name} config: {e}")
                self._config_cache[config_name] = {}
    
    def save_pipeline_config(self, config: PipelineConfig) -> bool:
        """
        Sauvegarde la configuration du pipeline.
        
        Args:
            config: Configuration du pipeline à sauvegarder
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            with self._cache_lock:
                # Convertir en dictionnaire
                config_dict = asdict(config)
                
                # Sauvegarder dans le cache
                self._config_cache['main'] = config_dict
                
                # Sauvegarder sur disque
                with open(self.main_config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                self.logger.info("Pipeline configuration saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving pipeline config: {e}")
            return False
    
    def load_pipeline_config(self) -> PipelineConfig:
        """
        Charge la configuration du pipeline.
        
        Returns:
            Configuration du pipeline (ou défaut si erreur)
        """
        try:
            with self._cache_lock:
                config_dict = self._config_cache.get('main', {})
                
                if config_dict:
                    # Créer PipelineConfig depuis le dictionnaire
                    return PipelineConfig(**config_dict)
                else:
                    # Retourner configuration par défaut
                    default_config = PipelineConfig()
                    self.logger.info("Using default pipeline configuration")
                    return default_config
                    
        except Exception as e:
            self.logger.error(f"Error loading pipeline config: {e}")
            return PipelineConfig()  # Configuration par défaut
    
    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Sauvegarde les paramètres d'interface utilisateur.
        
        Args:
            settings: Paramètres UI à sauvegarder
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            with self._cache_lock:
                self._config_cache['ui'] = settings
                
                with open(self.ui_config_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("UI settings saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving UI settings: {e}")
            return False
    
    def load_ui_settings(self) -> Dict[str, Any]:
        """
        Charge les paramètres d'interface utilisateur.
        
        Returns:
            Paramètres UI (ou dictionnaire vide si erreur)
        """
        try:
            with self._cache_lock:
                return self._config_cache.get('ui', {}).copy()
        except Exception as e:
            self.logger.error(f"Error loading UI settings: {e}")
            return {}
    
    def save_model_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Sauvegarde les préférences de modèles.
        
        Args:
            preferences: Préférences de modèles
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            with self._cache_lock:
                self._config_cache['models'] = preferences
                
                with open(self.models_config_file, 'w', encoding='utf-8') as f:
                    json.dump(preferences, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("Model preferences saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving model preferences: {e}")
            return False
    
    def load_model_preferences(self) -> Dict[str, Any]:
        """
        Charge les préférences de modèles.
        
        Returns:
            Préférences de modèles
        """
        try:
            with self._cache_lock:
                return self._config_cache.get('models', {}).copy()
        except Exception as e:
            self.logger.error(f"Error loading model preferences: {e}")
            return {}
    
    def save_lm_studio_config(self, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde la configuration LM Studio.
        
        Args:
            config: Configuration LM Studio
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            with self._cache_lock:
                self._config_cache['lm_studio'] = config
                
                with open(self.lm_studio_config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("LM Studio config saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving LM Studio config: {e}")
            return False
    
    def load_lm_studio_config(self) -> Dict[str, Any]:
        """
        Charge la configuration LM Studio.
        
        Returns:
            Configuration LM Studio
        """
        try:
            with self._cache_lock:
                return self._config_cache.get('lm_studio', {
                    'base_url': 'http://localhost:1234',
                    'preferred_ocr_model': None,
                    'preferred_transcription_model': None,
                    'manual_models': [],
                    'cache_duration': 300,
                    'auto_refresh': True
                }).copy()
        except Exception as e:
            self.logger.error(f"Error loading LM Studio config: {e}")
            return {}
    
    def save_nemo_config(self, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde la configuration NeMo.
        
        Args:
            config: Configuration NeMo
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            with self._cache_lock:
                self._config_cache['nemo'] = config
                
                with open(self.nemo_config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self.logger.debug("NeMo config saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving NeMo config: {e}")
            return False
    
    def load_nemo_config(self) -> Dict[str, Any]:
        """
        Charge la configuration NeMo.
        
        Returns:
            Configuration NeMo
        """
        try:
            with self._cache_lock:
                return self._config_cache.get('nemo', {
                    'device_mode': 'auto',
                    'force_cpu': False,
                    'asr_model': 'stt_fr_conformer_ctc_large',
                    'diarization_model': 'titanet_large',
                    'processing_mode': 'integrated',
                    'batch_size': 16,
                    'gpu_memory_fraction': 0.8,
                    'enable_mixed_precision': True,
                    'fallback_to_whisper': True,
                    'fallback_to_pyannote': True
                }).copy()
        except Exception as e:
            self.logger.error(f"Error loading NeMo config: {e}")
            return {}
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Obtient un résumé de toutes les configurations.
        
        Returns:
            Résumé des configurations
        """
        try:
            with self._cache_lock:
                summary = {
                    'config_dir': str(self.config_dir),
                    'files_exist': {
                        'main': self.main_config_file.exists(),
                        'models': self.models_config_file.exists(),
                        'ui': self.ui_config_file.exists(),
                        'lm_studio': self.lm_studio_config_file.exists(),
                        'nemo': self.nemo_config_file.exists()
                    },
                    'cache_loaded': {
                        'main': bool(self._config_cache.get('main')),
                        'models': bool(self._config_cache.get('models')),
                        'ui': bool(self._config_cache.get('ui')),
                        'lm_studio': bool(self._config_cache.get('lm_studio')),
                        'nemo': bool(self._config_cache.get('nemo'))
                    }
                }
                return summary
        except Exception as e:
            self.logger.error(f"Error getting config summary: {e}")
            return {}
    
    def reset_all_configs(self) -> bool:
        """
        Remet toutes les configurations par défaut.
        
        Returns:
            True si réinitialisation réussie
        """
        try:
            with self._cache_lock:
                # Vider le cache
                self._config_cache.clear()
                
                # Supprimer les fichiers de configuration
                config_files = [
                    self.main_config_file,
                    self.models_config_file,
                    self.ui_config_file,
                    self.lm_studio_config_file,
                    self.nemo_config_file
                ]
                
                for config_file in config_files:
                    if config_file.exists():
                        config_file.unlink()
                
                # Recharger les configurations par défaut
                self._load_all_configs()
                
                self.logger.info("All configurations reset to defaults")
                return True
                
        except Exception as e:
            self.logger.error(f"Error resetting configs: {e}")
            return False
    
    def backup_configs(self, backup_dir: Optional[str] = None) -> bool:
        """
        Crée une sauvegarde de toutes les configurations.
        
        Args:
            backup_dir: Répertoire de sauvegarde (par défaut: config_dir/backups)
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            import shutil
            from datetime import datetime
            
            if backup_dir:
                backup_path = Path(backup_dir)
            else:
                backup_path = self.config_dir / "backups"
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Nom de sauvegarde avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"
            backup_full_path = backup_path / backup_name
            
            # Copier tout le répertoire de configuration
            shutil.copytree(self.config_dir, backup_full_path, 
                          ignore=shutil.ignore_patterns('backups'))
            
            self.logger.info(f"Configuration backup created: {backup_full_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating config backup: {e}")
            return False


# Instance globale du gestionnaire de configuration
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """
    Obtient l'instance globale du gestionnaire de configuration.
    
    Returns:
        Instance du gestionnaire de configuration
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager