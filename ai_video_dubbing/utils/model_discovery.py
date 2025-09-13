#!/usr/bin/env python3
"""
Utilitaire de découverte automatique des modèles IA locaux.
Détecte les modèles disponibles pour Whisper, NVIDIA NeMo, LM Studio, etc.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import glob

class ModelDiscovery:
    """Découvreur automatique de modèles IA locaux."""
    
    def __init__(self):
        """Initialise le découvreur de modèles."""
        self.logger = logging.getLogger(__name__)
        
        # Chemins de recherche par défaut
        self.search_paths = {
            'whisper': [
                os.path.expanduser("~/.cache/whisper"),
                os.path.expanduser("~/.cache/huggingface/transformers"),
                "./models/whisper"
            ],
            'nemo': [
                os.path.expanduser("~/.cache/torch/NeMo"),
                os.path.expanduser("~/.nemo"),
                "./models/nemo"
            ],
            'lm_studio': [
                os.path.expanduser("~/.cache/lm-studio/models"),
                os.path.expanduser("~/LM Studio/models"),
                "C:/Users/{}/AppData/Local/LM Studio/models".format(os.getenv('USERNAME', '')),
                "/Applications/LM Studio.app/Contents/Resources/models"
            ],
            'huggingface': [
                os.path.expanduser("~/.cache/huggingface/transformers"),
                os.path.expanduser("~/.cache/huggingface/hub")
            ]
        }
        self.logger.info("Model discovery initialized")
    
    def discover_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Découvre tous les modèles disponibles localement.
        Returns:
            Dictionnaire organisé par type de modèle
        """
        discovered_models = {
            'transcription': [],
            'ocr': [],
            'multimodal': [],
            'voice_cloning': [],
            'language': []
        }
        
        try:
            # Découvrir les modèles Whisper
            whisper_models = self.discover_whisper_models()
            discovered_models['transcription'].extend(whisper_models)
            
            # Découvrir les modèles NeMo
            nemo_models = self.discover_nemo_models()
            discovered_models['transcription'].extend([m for m in nemo_models if m['task'] == 'asr'])
            discovered_models['voice_cloning'].extend([m for m in nemo_models if m['task'] == 'tts'])
            
            # Découvrir les modèles LM Studio
            lm_studio_models = self.discover_lm_studio_models()
            for model in lm_studio_models:
                model_type = model.get('type', 'language')
                if model_type in discovered_models:
                    discovered_models[model_type].append(model)
                else:
                    discovered_models['language'].append(model)
            
            # Découvrir les modèles Hugging Face
            hf_models = self.discover_huggingface_models()
            for model in hf_models:
                model_type = self._classify_hf_model(model)
                discovered_models[model_type].append(model)
            
            # Statistiques
            total_models = sum(len(models) for models in discovered_models.values())
            self.logger.info(f"Discovered {total_models} models across all categories")
            return discovered_models
            
        except Exception as e:
            self.logger.error(f"Model discovery failed: {e}")
            return discovered_models
    
    def discover_whisper_models(self) -> List[Dict[str, Any]]:
        """Découvre les modèles Whisper disponibles."""
        models = []
        try:
            # Modèles Whisper standard
            standard_models = [
                "tiny", "tiny.en", "base", "base.en", 
                "small", "small.en", "medium", "medium.en",
                "large", "large-v1", "large-v2", "large-v3"
            ]
            
            for model_name in standard_models:
                model_info = {
                    'name': f"whisper-{model_name}",
                    'type': 'transcription',
                    'framework': 'whisper',
                    'size': self._estimate_whisper_size(model_name),
                    'languages': ['multilingual'] if not model_name.endswith('.en') else ['english'],
                    'status': 'available',
                    'source': 'openai'
                }
                
                # Vérifier si le modèle est déjà téléchargé
                if self._is_whisper_model_downloaded(model_name):
                    model_info['status'] = 'downloaded'
                    model_info['path'] = self._get_whisper_model_path(model_name)
                
                models.append(model_info)
            
            self.logger.info(f"Found {len(models)} Whisper models")
            return models
            
        except Exception as e:
            self.logger.warning(f"Whisper model discovery failed: {e}")
            return []
    
    def discover_nemo_models(self) -> List[Dict[str, Any]]:
        """Découvre les modèles NVIDIA NeMo disponibles."""
        models = []
        try:
            # Modèles NeMo pré-entraînés connus
            known_models = {
                'asr': [
                    'stt_en_conformer_ctc_large',
                    'stt_en_conformer_transducer_xlarge',
                    'stt_multilingual_conformer_ctc_large',
                    'stt_fr_conformer_ctc_large'
                ],
                'tts': [
                    'tts_en_fastpitch',
                    'tts_en_hifigan',
                    'tts_fr_fastpitch',
                    'tts_multilingual_fastpitch'
                ]
            }
            
            for task, model_names in known_models.items():
                for model_name in model_names:
                    model_info = {
                        'name': model_name,
                        'type': 'transcription' if task == 'asr' else 'voice_cloning',
                        'framework': 'nemo',
                        'task': task,
                        'status': 'available',
                        'source': 'nvidia'
                    }
                    
                    # Vérifier si le modèle est téléchargé
                    if self._is_nemo_model_downloaded(model_name):
                        model_info['status'] = 'downloaded'
                        model_info['path'] = self._get_nemo_model_path(model_name)
                    
                    models.append(model_info)
            
            self.logger.info(f"Found {len(models)} NeMo models")
            return models
            
        except Exception as e:
            self.logger.warning(f"NeMo model discovery failed: {e}")
            return []
    
    def discover_lm_studio_models(self) -> List[Dict[str, Any]]:
        """Découvre les modèles LM Studio disponibles."""
        models = []
        try:
            # Importer le gestionnaire LM Studio
            from ..processors.lm_studio_manager import LMStudioManager
            lm_manager = LMStudioManager()
            lm_models = lm_manager.get_available_models()
            
            for model in lm_models:
                model_info = {
                    'name': model['name'],
                    'type': model.get('type', 'language'),
                    'framework': 'lm_studio',
                    'size': model.get('size', 0),
                    'status': model.get('status', 'available'),
                    'source': model.get('source', 'local')
                }
                if 'path' in model:
                    model_info['path'] = model['path']
                models.append(model_info)
            
            self.logger.info(f"Found {len(models)} LM Studio models")
            return models
            
        except Exception as e:
            self.logger.warning(f"LM Studio model discovery failed: {e}")
            return []
    
    def discover_huggingface_models(self) -> List[Dict[str, Any]]:
        """Découvre les modèles Hugging Face téléchargés localement."""
        models = []
        try:
            for search_path in self.search_paths['huggingface']:
                if os.path.exists(search_path):
                    hf_models = self._scan_huggingface_directory(search_path)
                    models.extend(hf_models)
            
            self.logger.info(f"Found {len(models)} Hugging Face models")
            return models
            
        except Exception as e:
            self.logger.warning(f"Hugging Face model discovery failed: {e}")
            return []
    
    def get_recommended_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtient les modèles recommandés pour chaque tâche.
        Returns:
            Dictionnaire des modèles recommandés par tâche
        """
        all_models = self.discover_all_models()
        recommendations = {}
        
        # Transcription - Recommander Whisper base ou large selon disponibilité
        transcription_models = all_models.get('transcription', [])
        whisper_models = [m for m in transcription_models if m['framework'] == 'whisper']
        if whisper_models:
            # Préférer large-v3, puis medium, puis base
            for preferred in ['whisper-large-v3', 'whisper-medium', 'whisper-base']:
                matching = [m for m in whisper_models if m['name'] == preferred]
                if matching:
                    recommendations['transcription'] = matching[0]
                    break
        
        # OCR/Multimodal - Recommander les modèles multimodaux disponibles
        multimodal_models = all_models.get('multimodal', [])
        if multimodal_models:
            # Préférer les modèles LLaVA ou Qwen-VL
            for preferred_pattern in ['llava', 'qwen-vl', 'cogvlm']:
                matching = [m for m in multimodal_models if preferred_pattern in m['name'].lower()]
                if matching:
                    recommendations['ocr'] = matching[0]
                    break
        
        # Clonage vocal - Recommander NeMo TTS si disponible
        voice_models = all_models.get('voice_cloning', [])
        nemo_tts = [m for m in voice_models if m['framework'] == 'nemo']
        if nemo_tts:
            recommendations['voice_cloning'] = nemo_tts[0]
        
        return recommendations
    
    def _is_whisper_model_downloaded(self, model_name: str) -> bool:
        """Vérifie si un modèle Whisper est téléchargé."""
        try:
            import whisper
            model_path = whisper._MODELS[model_name]
            cache_dir = os.path.expanduser("~/.cache/whisper")
            model_file = os.path.join(cache_dir, os.path.basename(model_path))
            return os.path.exists(model_file)
        except:
            return False
    
    def _get_whisper_model_path(self, model_name: str) -> Optional[str]:
        """Obtient le chemin d'un modèle Whisper téléchargé."""
        try:
            import whisper
            model_path = whisper._MODELS[model_name]
            cache_dir = os.path.expanduser("~/.cache/whisper")
            model_file = os.path.join(cache_dir, os.path.basename(model_path))
            return model_file if os.path.exists(model_file) else None
        except:
            return None
    
    def _estimate_whisper_size(self, model_name: str) -> int:
        """Estime la taille d'un modèle Whisper."""
        size_map = {
            'tiny': 39 * 1024 * 1024,      # ~39MB
            'base': 74 * 1024 * 1024,      # ~74MB
            'small': 244 * 1024 * 1024,    # ~244MB
            'medium': 769 * 1024 * 1024,   # ~769MB
            'large': 1550 * 1024 * 1024,   # ~1.55GB
        }
        base_name = model_name.replace('.en', '')
        return size_map.get(base_name, 100 * 1024 * 1024)  # Default 100MB
    
    def _is_nemo_model_downloaded(self, model_name: str) -> bool:
        """Vérifie si un modèle NeMo est téléchargé."""
        try:
            for search_path in self.search_paths['nemo']:
                if os.path.exists(search_path):
                    model_files = glob.glob(os.path.join(search_path, f"*{model_name}*"))
                    if model_files:
                        return True
            return False
        except:
            return False
    
    def _get_nemo_model_path(self, model_name: str) -> Optional[str]:
        """Obtient le chemin d'un modèle NeMo téléchargé."""
        try:
            for search_path in self.search_paths['nemo']:
                if os.path.exists(search_path):
                    model_files = glob.glob(os.path.join(search_path, f"*{model_name}*"))
                    if model_files:
                        return model_files[0]
            return None
        except:
            return None
    
    def _scan_huggingface_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scanne un répertoire pour les modèles Hugging Face."""
        models = []
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    config_path = os.path.join(item_path, "config.json")
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                            model_info = {
                                'name': item,
                                'type': 'language',
                                'framework': 'huggingface',
                                'path': item_path,
                                'size': self._get_directory_size(item_path),
                                'status': 'downloaded',
                                'source': 'huggingface',
                                'config': config
                            }
                            models.append(model_info)
                        except Exception as e:
                            self.logger.debug(f"Error reading config for {item}: {e}")
        except Exception as e:
            self.logger.debug(f"Error scanning HuggingFace directory {directory}: {e}")
        return models
    
    def _classify_hf_model(self, model: Dict[str, Any]) -> str:
        """Classifie un modèle Hugging Face selon son type."""
        config = model.get('config', {})
        model_name = model.get('name', '').lower()
        
        # Vérifier le type d'architecture
        architectures = config.get('architectures', [])
        
        # Modèles de vision/multimodaux
        if any(arch in str(architectures) for arch in ['Vision', 'CLIP', 'BLIP', 'LLaVA']):
            return 'multimodal'
        
        # Modèles de transcription
        if any(keyword in model_name for keyword in ['whisper', 'wav2vec', 'speech']):
            return 'transcription'
        
        # Modèles de synthèse vocale
        if any(keyword in model_name for keyword in ['tts', 'tacotron', 'fastspeech']):
            return 'voice_cloning'
        
        # Par défaut, modèle de langage
        return 'language'
    
    def _get_directory_size(self, directory: str) -> int:
        """Calcule la taille totale d'un répertoire."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size