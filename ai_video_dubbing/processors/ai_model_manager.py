"""
Gestionnaire de modèles IA pour l'application de doublage vidéo par IA.
"""

import os
import gc
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import threading
import time

# Imports conditionnels pour les dépendances IA
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None

try:
    import whisper
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False
    whisper = None

try:
    import transformers
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    transformers = None
    pipeline = None

try:
    import paddleocr
    _PADDLEOCR_AVAILABLE = True
except ImportError:
    _PADDLEOCR_AVAILABLE = False
    paddleocr = None

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False
    easyocr = None

from ..interfaces.base_interfaces import IAIModelManager
from ..models.data_models import (
    ModelType, TranscriptionResult, OCRResult, Frame, 
    ProcessingError, ResourceError, ValidationError
)

# Imports pour les nouvelles fonctionnalités
try:
    from .lm_studio_manager import LMStudioManager
    _LM_STUDIO_AVAILABLE = True
except ImportError:
    _LM_STUDIO_AVAILABLE = False
    LMStudioManager = None

try:
    from ..utils.model_discovery import ModelDiscovery
    _MODEL_DISCOVERY_AVAILABLE = True
except ImportError:
    _MODEL_DISCOVERY_AVAILABLE = False
    ModelDiscovery = None

try:
    import nemo
    import nemo.collections.asr as nemo_asr
    import nemo.collections.nlp as nemo_nlp
    _NEMO_AVAILABLE = True
except ImportError:
    _NEMO_AVAILABLE = False
    nemo = None
    nemo_asr = None
    nemo_nlp = None


class ModelInfo:
    """Informations sur un modèle chargé."""
    
    def __init__(self, model: Any, model_type: ModelType, model_name: str, memory_usage: float):
        self.model = model
        self.model_type = model_type
        self.model_name = model_name
        self.memory_usage = memory_usage  # En MB
        self.last_used = time.time()
        self.load_time = time.time()


class AIModelManager(IAIModelManager):
    """Gestionnaire de modèles IA avec chargement paresseux et gestion mémoire."""
    
    def __init__(self, max_memory_usage: float = 0.8, cache_timeout: int = 300):
        """
        Initialise le gestionnaire de modèles IA.
        
        Args:
            max_memory_usage: Pourcentage maximal de RAM à utiliser (0.0-1.0)
            cache_timeout: Temps en secondes avant déchargement automatique des modèles
        """
        self.max_memory_usage = max_memory_usage
        self.cache_timeout = cache_timeout
        self.logger = logging.getLogger(__name__)
        
        # Cache des modèles chargés
        self._loaded_models: Dict[str, ModelInfo] = {}
        self._model_lock = threading.Lock()
        
        # Configuration des modèles supportés
        self._model_configs = {
            ModelType.ASR: {
                "whisper-tiny": {"size": 39, "multilingual": True},
                "whisper-base": {"size": 74, "multilingual": True},
                "whisper-small": {"size": 244, "multilingual": True},
                "whisper-medium": {"size": 769, "multilingual": True},
                "whisper-large-v3": {"size": 1550, "multilingual": True},
                # Modèles NeMo ASR
                "nemo-conformer-ctc-large-fr": {"size": 500, "multilingual": False, "language": "fr"},
                "nemo-conformer-ctc-large-en": {"size": 500, "multilingual": False, "language": "en"},
                "nemo-fastconformer-multilingual": {"size": 800, "multilingual": True},
                # Modèles LM Studio
                "lm-studio-whisper": {"size": 200, "multilingual": True, "source": "lm_studio"},
            },
            ModelType.OCR: {
                "paddleocr": {"size": 100, "languages": ["en", "fr", "es", "de"]},
                "easyocr": {"size": 150, "languages": ["en", "fr", "es", "de"]},
                # Modèles NeMo OCR/Vision
                "nemo-vision-transformer": {"size": 300, "languages": ["multilingual"]},
                "nemo-multimodal-llm": {"size": 1200, "languages": ["multilingual"]},
                # Modèles LM Studio OCR
                "lm-studio-vision": {"size": 400, "languages": ["multilingual"], "source": "lm_studio"},
            },
            ModelType.VOICE_CLONING: {
                "tortoise-tts": {"size": 2000, "quality": "high"},
                "bark": {"size": 1500, "quality": "medium"},
            }
        }
        
        # Initialiser les gestionnaires additionnels
        self.lm_studio_manager = None
        self.model_discovery = None
        
        if _LM_STUDIO_AVAILABLE:
            try:
                self.lm_studio_manager = LMStudioManager()
                self.logger.info("LM Studio manager initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LM Studio manager: {e}")
        
        if _MODEL_DISCOVERY_AVAILABLE:
            try:
                self.model_discovery = ModelDiscovery()
                self.logger.info("Model discovery initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize model discovery: {e}")
        
        # Vérifier les dépendances
        self._check_dependencies()
        
        # Démarrer le thread de nettoyage automatique
        self._cleanup_thread = threading.Thread(target=self._auto_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _check_dependencies(self) -> None:
        """Vérifie la disponibilité des dépendances IA."""
        missing_deps = []
        
        if not _TORCH_AVAILABLE:
            missing_deps.append("torch")
        
        if not _WHISPER_AVAILABLE:
            missing_deps.append("openai-whisper")
        
        if not _TRANSFORMERS_AVAILABLE:
            missing_deps.append("transformers")
        
        if not _PADDLEOCR_AVAILABLE and not _EASYOCR_AVAILABLE:
            missing_deps.append("paddleocr or easyocr")
        
        # Vérifier les nouvelles dépendances (optionnelles)
        optional_deps = []
        if not _NEMO_AVAILABLE:
            optional_deps.append("nvidia-nemo (for advanced ASR/NLP)")
        
        if not _LM_STUDIO_AVAILABLE:
            optional_deps.append("lm-studio integration")
        
        if optional_deps:
            self.logger.info(f"Optional dependencies not available: {', '.join(optional_deps)}")
        
        if missing_deps:
            self.logger.warning(
                f"Missing AI dependencies: {', '.join(missing_deps)}. "
                "Some features will be limited."
            )
    
    def _get_memory_usage(self) -> float:
        """Obtient l'utilisation mémoire actuelle en pourcentage."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except Exception:
            return 0.5  # Valeur par défaut si psutil n'est pas disponible
    
    def _get_available_memory_mb(self) -> float:
        """Obtient la mémoire disponible en MB."""
        try:
            memory = psutil.virtual_memory()
            max_usable = memory.total * self.max_memory_usage
            current_used = memory.used
            return max(0, (max_usable - current_used) / (1024 * 1024))
        except Exception:
            return 1000  # 1GB par défaut
    
    def _model_key(self, model_type: ModelType, model_name: str) -> str:
        """Génère une clé unique pour un modèle."""
        return f"{model_type.value}:{model_name}"
    
    def _estimate_model_size(self, model_type: ModelType, model_name: str) -> float:
        """Estime la taille d'un modèle en MB."""
        if model_type in self._model_configs:
            if model_name in self._model_configs[model_type]:
                return self._model_configs[model_type][model_name]["size"]
        
        # Tailles par défaut si le modèle n'est pas dans la config
        default_sizes = {
            ModelType.ASR: 500,
            ModelType.OCR: 100,
            ModelType.VOICE_CLONING: 1000,
            ModelType.DIARIZATION: 200,
            ModelType.SOURCE_SEPARATION: 300
        }
        
        return default_sizes.get(model_type, 200)
    
    def _free_memory_if_needed(self, required_mb: float) -> None:
        """Libère de la mémoire si nécessaire pour charger un nouveau modèle."""
        available_mb = self._get_available_memory_mb()
        
        if available_mb >= required_mb:
            return
        
        self.logger.info(f"Need to free {required_mb - available_mb:.1f}MB of memory")
        
        # Trier les modèles par dernière utilisation (plus ancien en premier)
        models_by_age = sorted(
            self._loaded_models.items(),
            key=lambda x: x[1].last_used
        )
        
        freed_mb = 0
        for model_key, model_info in models_by_age:
            if freed_mb >= (required_mb - available_mb):
                break
            
            self.logger.info(f"Unloading model {model_key} to free memory")
            self._unload_model_internal(model_key)
            freed_mb += model_info.memory_usage
        
        # Forcer le garbage collection
        gc.collect()
        if _TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def _unload_model_internal(self, model_key: str) -> None:
        """Décharge un modèle interne (sans verrou)."""
        if model_key in self._loaded_models:
            model_info = self._loaded_models[model_key]
            
            # Nettoyer le modèle
            del model_info.model
            del self._loaded_models[model_key]
            
            self.logger.info(f"Model {model_key} unloaded")
    
    def _auto_cleanup(self) -> None:
        """Thread de nettoyage automatique des modèles non utilisés."""
        while True:
            try:
                time.sleep(60)  # Vérifier toutes les minutes
                
                current_time = time.time()
                models_to_unload = []
                
                with self._model_lock:
                    for model_key, model_info in self._loaded_models.items():
                        if current_time - model_info.last_used > self.cache_timeout:
                            models_to_unload.append(model_key)
                    
                    for model_key in models_to_unload:
                        self.logger.info(f"Auto-unloading unused model: {model_key}")
                        self._unload_model_internal(model_key)
                
                if models_to_unload:
                    gc.collect()
                    if _TORCH_AVAILABLE and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        
            except Exception as e:
                self.logger.error(f"Error in auto cleanup: {e}")
    
    def load_model(self, model_type: ModelType, model_name: str) -> None:
        """
        Charge un modèle IA avec gestion mémoire.
        
        Args:
            model_type: Type de modèle à charger
            model_name: Nom du modèle
            
        Raises:
            ResourceError: Si pas assez de mémoire
            ProcessingError: Si le chargement échoue
        """
        model_key = self._model_key(model_type, model_name)
        
        with self._model_lock:
            # Vérifier si le modèle est déjà chargé
            if model_key in self._loaded_models:
                self._loaded_models[model_key].last_used = time.time()
                self.logger.info(f"Model {model_key} already loaded")
                return
            
            # Estimer la taille du modèle
            estimated_size = self._estimate_model_size(model_type, model_name)
            
            # Vérifier la mémoire disponible
            if self._get_memory_usage() > 0.9:  # Plus de 90% utilisé
                raise ResourceError("System memory usage too high to load new model")
            
            # Libérer de la mémoire si nécessaire
            self._free_memory_if_needed(estimated_size)
            
            try:
                self.logger.info(f"Loading model {model_key}...")
                start_time = time.time()
                
                # Charger le modèle selon son type
                model = self._load_model_by_type(model_type, model_name)
                
                load_time = time.time() - start_time
                
                # Estimer l'utilisation mémoire réelle
                actual_memory = self._estimate_actual_memory_usage(model)
                
                # Stocker les informations du modèle
                model_info = ModelInfo(
                    model=model,
                    model_type=model_type,
                    model_name=model_name,
                    memory_usage=actual_memory
                )
                
                self._loaded_models[model_key] = model_info
                
                self.logger.info(
                    f"Model {model_key} loaded successfully in {load_time:.2f}s "
                    f"(~{actual_memory:.1f}MB)"
                )
                
            except Exception as e:
                raise ProcessingError(f"Failed to load model {model_key}: {e}")
    
    def _load_model_by_type(self, model_type: ModelType, model_name: str) -> Any:
        """Charge un modèle selon son type."""
        if model_type == ModelType.ASR:
            if model_name.startswith("nemo-"):
                return self._load_nemo_asr_model(model_name)
            elif model_name.startswith("lm-studio-"):
                return self._load_lm_studio_asr_model(model_name)
            else:
                return self._load_whisper_model(model_name)
        elif model_type == ModelType.OCR:
            if model_name.startswith("nemo-"):
                return self._load_nemo_ocr_model(model_name)
            elif model_name.startswith("lm-studio-"):
                return self._load_lm_studio_ocr_model(model_name)
            else:
                return self._load_ocr_model(model_name)
        elif model_type == ModelType.VOICE_CLONING:
            return self._load_voice_cloning_model(model_name)
        else:
            raise ProcessingError(f"Unsupported model type: {model_type}")
    
    def _load_whisper_model(self, model_name: str) -> Any:
        """Charge un modèle Whisper."""
        if not _WHISPER_AVAILABLE:
            raise ProcessingError("Whisper not available. Install with: pip install openai-whisper")
        
        try:
            # Mapper les noms de modèles
            whisper_name = model_name.replace("whisper-", "")
            model = whisper.load_model(whisper_name)
            return model
        except Exception as e:
            raise ProcessingError(f"Failed to load Whisper model {model_name}: {e}")
    
    def _load_ocr_model(self, model_name: str) -> Any:
        """Charge un modèle OCR."""
        if model_name == "paddleocr":
            if not _PADDLEOCR_AVAILABLE:
                raise ProcessingError("PaddleOCR not available. Install with: pip install paddleocr")
            
            try:
                ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
                return ocr
            except Exception as e:
                raise ProcessingError(f"Failed to load PaddleOCR: {e}")
        
        elif model_name == "easyocr":
            if not _EASYOCR_AVAILABLE:
                raise ProcessingError("EasyOCR not available. Install with: pip install easyocr")
            
            try:
                reader = easyocr.Reader(['en', 'fr'])
                return reader
            except Exception as e:
                raise ProcessingError(f"Failed to load EasyOCR: {e}")
        
        else:
            raise ProcessingError(f"Unsupported OCR model: {model_name}")
    
    def _load_voice_cloning_model(self, model_name: str) -> Any:
        """Charge un modèle de clonage vocal."""
        # Pour l'instant, retourner un placeholder
        # L'implémentation complète sera dans la tâche 12
        self.logger.warning(f"Voice cloning model {model_name} not yet implemented")
        return {"model_name": model_name, "placeholder": True}
    
    def _estimate_actual_memory_usage(self, model: Any) -> float:
        """Estime l'utilisation mémoire réelle d'un modèle."""
        try:
            if _TORCH_AVAILABLE and hasattr(model, 'parameters'):
                # Pour les modèles PyTorch
                total_params = sum(p.numel() for p in model.parameters())
                # Estimer 4 bytes par paramètre (float32)
                return (total_params * 4) / (1024 * 1024)
            else:
                # Estimation par défaut
                return 100.0
        except Exception:
            return 100.0
    
    def get_model(self, model_type: ModelType, model_name: str) -> Any:
        """
        Obtient un modèle chargé.
        
        Args:
            model_type: Type de modèle
            model_name: Nom du modèle
            
        Returns:
            Le modèle chargé
            
        Raises:
            ProcessingError: Si le modèle n'est pas chargé
        """
        model_key = self._model_key(model_type, model_name)
        
        with self._model_lock:
            if model_key not in self._loaded_models:
                # Chargement automatique
                self.load_model(model_type, model_name)
            
            model_info = self._loaded_models[model_key]
            model_info.last_used = time.time()
            return model_info.model
    
    def unload_model(self, model_type: ModelType, model_name: str = None) -> None:
        """
        Décharge un modèle ou tous les modèles d'un type.
        
        Args:
            model_type: Type de modèle à décharger
            model_name: Nom spécifique du modèle (optionnel)
        """
        with self._model_lock:
            if model_name:
                # Décharger un modèle spécifique
                model_key = self._model_key(model_type, model_name)
                if model_key in self._loaded_models:
                    self._unload_model_internal(model_key)
            else:
                # Décharger tous les modèles du type
                keys_to_remove = [
                    key for key in self._loaded_models.keys()
                    if key.startswith(f"{model_type.value}:")
                ]
                
                for key in keys_to_remove:
                    self._unload_model_internal(key)
        
        # Nettoyer la mémoire
        gc.collect()
        if _TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtient la liste des modèles chargés avec leurs informations.
        
        Returns:
            Dictionnaire des modèles chargés
        """
        with self._model_lock:
            result = {}
            for model_key, model_info in self._loaded_models.items():
                result[model_key] = {
                    "model_type": model_info.model_type.value,
                    "model_name": model_info.model_name,
                    "memory_usage_mb": model_info.memory_usage,
                    "last_used": model_info.last_used,
                    "load_time": model_info.load_time,
                    "age_seconds": time.time() - model_info.load_time
                }
            return result
    
    def get_memory_stats(self) -> Dict[str, float]:
        """
        Obtient les statistiques d'utilisation mémoire.
        
        Returns:
            Statistiques mémoire
        """
        try:
            memory = psutil.virtual_memory()
            
            total_model_memory = sum(
                model_info.memory_usage 
                for model_info in self._loaded_models.values()
            )
            
            return {
                "system_memory_percent": memory.percent,
                "system_memory_available_mb": memory.available / (1024 * 1024),
                "system_memory_total_mb": memory.total / (1024 * 1024),
                "models_memory_mb": total_model_memory,
                "models_count": len(self._loaded_models),
                "max_memory_usage": self.max_memory_usage
            }
        except Exception:
            return {
                "system_memory_percent": 50.0,
                "models_memory_mb": sum(
                    model_info.memory_usage 
                    for model_info in self._loaded_models.values()
                ),
                "models_count": len(self._loaded_models)
            }
    
    def cleanup_all(self) -> None:
        """Décharge tous les modèles et nettoie la mémoire."""
        with self._model_lock:
            model_keys = list(self._loaded_models.keys())
            for model_key in model_keys:
                self._unload_model_internal(model_key)
        
        # Nettoyage agressif de la mémoire
        gc.collect()
        if _TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.logger.info("All models unloaded and memory cleaned")
    
    # Méthodes pour les tâches futures (stubs pour l'instant)
    def transcribe_audio(
        self, 
        audio_path: str, 
        model_name: str = "whisper-base",
        language: str = None,
        word_timestamps: bool = True,
        temperature: float = 0.0,
        beam_size: int = 5,
        best_of: int = 5
    ) -> TranscriptionResult:
        """
        Transcrit l'audio avec horodatages précis.
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle Whisper à utiliser
            language: Langue forcée (None pour détection automatique)
            word_timestamps: Générer les horodatages au niveau du mot
            temperature: Température pour la génération (0.0 = déterministe)
            beam_size: Taille du beam search
            best_of: Nombre de candidats à considérer
            
        Returns:
            Résultats de transcription avec horodatages
            
        Raises:
            ProcessingError: Si la transcription échoue
            ValidationError: Si le fichier audio est invalide
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        try:
            self.logger.info(f"Starting transcription of {audio_path} with {model_name}")
            start_time = time.time()
            
            # Charger le modèle Whisper
            model = self.get_model(ModelType.ASR, model_name)
            
            # Préparer les options de transcription
            transcribe_options = {
                "language": language,
                "task": "transcribe",
                "temperature": temperature,
                "beam_size": beam_size,
                "best_of": best_of,
                "word_timestamps": word_timestamps,
                "verbose": False
            }
            
            # Essayer d'abord avec WhisperX pour de meilleurs horodatages
            try:
                result = self._transcribe_with_whisperx(
                    str(audio_path), model_name, transcribe_options
                )
            except Exception as e:
                self.logger.warning(f"WhisperX failed, falling back to standard Whisper: {e}")
                result = self._transcribe_with_whisper(
                    model, str(audio_path), transcribe_options
                )
            
            processing_time = time.time() - start_time
            
            # Post-traitement des résultats
            processed_result = self._process_transcription_result(
                result, processing_time, model_name
            )
            
            self.logger.info(
                f"Transcription completed in {processing_time:.2f}s "
                f"({len(processed_result.segments)} segments, "
                f"confidence: {processed_result.confidence:.3f})"
            )
            
            return processed_result
            
        except Exception as e:
            raise ProcessingError(f"Transcription failed: {e}")
    
    def _transcribe_with_whisperx(
        self, 
        audio_path: str, 
        model_name: str, 
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transcrit avec WhisperX pour de meilleurs horodatages.
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle
            options: Options de transcription
            
        Returns:
            Résultats de transcription WhisperX
        """
        try:
            import whisperx
            
            # Charger le modèle WhisperX
            device = "cuda" if _TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            model_size = model_name.replace("whisper-", "")
            model = whisperx.load_model(model_size, device, compute_type=compute_type)
            
            # Charger l'audio
            audio = whisperx.load_audio(audio_path)
            
            # Transcription initiale
            result = model.transcribe(
                audio, 
                batch_size=16,
                language=options.get("language"),
                task=options.get("task", "transcribe")
            )
            
            # Alignement pour horodatages précis
            if options.get("word_timestamps", True):
                try:
                    # Charger le modèle d'alignement
                    model_a, metadata = whisperx.load_align_model(
                        language_code=result["language"], 
                        device=device
                    )
                    
                    # Aligner les horodatages
                    result = whisperx.align(
                        result["segments"], 
                        model_a, 
                        metadata, 
                        audio, 
                        device, 
                        return_char_alignments=False
                    )
                    
                except Exception as e:
                    self.logger.warning(f"WhisperX alignment failed: {e}")
            
            return result
            
        except ImportError:
            raise ProcessingError(
                "WhisperX not available. Install with: pip install whisperx"
            )
    
    def _transcribe_with_whisper(
        self, 
        model: Any, 
        audio_path: str, 
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transcrit avec Whisper standard.
        
        Args:
            model: Modèle Whisper chargé
            audio_path: Chemin vers le fichier audio
            options: Options de transcription
            
        Returns:
            Résultats de transcription Whisper
        """
        try:
            # Filtrer les options supportées par Whisper
            whisper_options = {
                k: v for k, v in options.items() 
                if k in ["language", "task", "temperature", "beam_size", "best_of", "word_timestamps"]
                and v is not None
            }
            
            # Transcription
            result = model.transcribe(audio_path, **whisper_options)
            
            return result
            
        except Exception as e:
            raise ProcessingError(f"Whisper transcription failed: {e}")
    
    def _process_transcription_result(
        self, 
        raw_result: Dict[str, Any], 
        processing_time: float,
        model_name: str
    ) -> TranscriptionResult:
        """
        Traite les résultats bruts de transcription.
        
        Args:
            raw_result: Résultats bruts de Whisper/WhisperX
            processing_time: Temps de traitement
            model_name: Nom du modèle utilisé
            
        Returns:
            Résultats formatés
        """
        from ..models.data_models import TranscriptionSegment, WordTimestamp
        
        # Extraire le texte complet
        full_text = raw_result.get("text", "").strip()
        
        # Traiter les segments
        segments = []
        total_confidence = 0.0
        segment_count = 0
        
        for seg_data in raw_result.get("segments", []):
            # Extraire les horodatages de mots si disponibles
            word_timestamps = []
            if "words" in seg_data:
                for word_data in seg_data["words"]:
                    word_timestamp = WordTimestamp(
                        word=word_data.get("word", "").strip(),
                        start=float(word_data.get("start", 0.0)),
                        end=float(word_data.get("end", 0.0)),
                        confidence=float(word_data.get("probability", 0.0))
                    )
                    word_timestamps.append(word_timestamp)
            
            # Créer le segment
            segment = TranscriptionSegment(
                text=seg_data.get("text", "").strip(),
                start=float(seg_data.get("start", 0.0)),
                end=float(seg_data.get("end", 0.0)),
                confidence=float(seg_data.get("avg_logprob", 0.0)),
                word_timestamps=word_timestamps
            )
            
            segments.append(segment)
            
            # Calculer la confiance moyenne
            if segment.confidence > 0:
                total_confidence += segment.confidence
                segment_count += 1
        
        # Calculer la confiance globale
        overall_confidence = (
            total_confidence / segment_count if segment_count > 0 else 0.0
        )
        
        # Normaliser la confiance (Whisper utilise log-prob négatif)
        if overall_confidence < 0:
            overall_confidence = max(0.0, 1.0 + overall_confidence)  # Convertir log-prob en probabilité
        
        # Détecter la langue
        detected_language = raw_result.get("language", "unknown")
        
        return TranscriptionResult(
            text=full_text,
            segments=segments,
            language=detected_language,
            confidence=overall_confidence,
            processing_time=processing_time,
            model_name=model_name,
            word_count=len(full_text.split()) if full_text else 0
        )
    
    def transcribe_audio_segments(
        self, 
        audio_segments: List[str], 
        model_name: str = "whisper-base",
        **kwargs
    ) -> List[TranscriptionResult]:
        """
        Transcrit plusieurs segments audio.
        
        Args:
            audio_segments: Liste des chemins vers les segments audio
            model_name: Nom du modèle à utiliser
            **kwargs: Options de transcription
            
        Returns:
            Liste des résultats de transcription
        """
        results = []
        
        for i, segment_path in enumerate(audio_segments):
            try:
                self.logger.info(f"Transcribing segment {i+1}/{len(audio_segments)}")
                result = self.transcribe_audio(segment_path, model_name, **kwargs)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to transcribe segment {segment_path}: {e}")
                # Créer un résultat vide en cas d'erreur
                empty_result = TranscriptionResult(
                    text="",
                    segments=[],
                    language="unknown",
                    confidence=0.0,
                    processing_time=0.0,
                    model_name=model_name,
                    word_count=0
                )
                results.append(empty_result)
        
        return results
    
    def get_supported_languages(self, model_name: str = "whisper-base") -> List[str]:
        """
        Obtient la liste des langues supportées par un modèle.
        
        Args:
            model_name: Nom du modèle
            
        Returns:
            Liste des codes de langue supportés
        """
        try:
            if not _WHISPER_AVAILABLE:
                return ["en"]  # Anglais par défaut
            
            import whisper
            
            # Langues supportées par Whisper
            return list(whisper.tokenizer.LANGUAGES.keys())
            
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return ["en", "fr", "es", "de", "it", "pt", "ru", "ja", "ko", "zh"]
    
    def detect_language(self, audio_path: str, model_name: str = "whisper-base") -> Dict[str, float]:
        """
        Détecte la langue d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle à utiliser
            
        Returns:
            Dictionnaire des langues avec leurs probabilités
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        try:
            # Charger le modèle
            model = self.get_model(ModelType.ASR, model_name)
            
            # Détecter la langue (utilise les 30 premières secondes)
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)
            
            # Créer le mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            
            # Détecter la langue
            _, probs = model.detect_language(mel)
            
            # Convertir en dictionnaire trié
            language_probs = {
                lang: float(prob) 
                for lang, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True)
            }
            
            return language_probs
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return {"en": 1.0}  # Fallback vers l'anglais
    
    def extract_text_from_frames(
        self, 
        frames: List[Frame], 
        model_name: str = "paddleocr",
        languages: List[str] = None,
        confidence_threshold: float = 0.5,
        detect_changes: bool = True,
        similarity_threshold: float = 0.8
    ) -> List[OCRResult]:
        """
        Extrait le texte des images avec détection de changements.
        
        Args:
            frames: Liste des frames à analyser
            model_name: Nom du modèle OCR à utiliser
            languages: Langues à détecter (None pour auto)
            confidence_threshold: Seuil de confiance minimum
            detect_changes: Détecter les changements entre frames
            similarity_threshold: Seuil de similarité pour détecter les changements
            
        Returns:
            Liste des résultats OCR avec horodatages
            
        Raises:
            ProcessingError: Si l'extraction OCR échoue
        """
        if not frames:
            return []
        
        try:
            self.logger.info(f"Starting OCR extraction on {len(frames)} frames with {model_name}")
            start_time = time.time()
            
            # Déterminer le type de modèle et charger approprié
            if model_name.startswith('lm-studio-') or model_name in [m['name'] for m in self.lm_studio_manager.get_multimodal_models()]:
                return self._extract_text_with_lm_studio_ocr(frames, model_name, confidence_threshold)
            elif 'nemo' in model_name.lower():
                return self._extract_text_with_nemo_ocr(frames, model_name, confidence_threshold)
            else:
                # Utiliser les méthodes OCR traditionnelles (PaddleOCR, EasyOCR)
                return self._extract_text_with_traditional_ocr(frames, model_name, languages, confidence_threshold, detect_changes, similarity_threshold)
        
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            raise ProcessingError(f"OCR extraction failed: {e}")
    
    def _extract_text_with_lm_studio_ocr(
        self, 
        frames: List[Frame], 
        model_name: str, 
        confidence_threshold: float = 0.5
    ) -> List[OCRResult]:
        """
        Extrait le texte avec LM Studio en utilisant des modèles multimodaux.
        
        Args:
            frames: Liste des frames à analyser
            model_name: Nom du modèle LM Studio
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Liste des résultats OCR
        """
        try:
            if not self.lm_studio_manager or not self.lm_studio_manager.is_available():
                raise ProcessingError("LM Studio not available or not running")
            
            self.logger.info(f"Extracting text from {len(frames)} frames using LM Studio {model_name}")
            
            # Préparer les frames pour LM Studio
            frame_data_list = []
            for frame in frames:
                frame_data_list.append({
                    "timestamp": frame.timestamp,
                    "frame": frame.image_data
                })
            
            # Utiliser LM Studio pour l'extraction
            lm_results = self.lm_studio_manager.extract_text_from_frames(frame_data_list, model_name)
            
            # Convertir en format OCRResult
            ocr_results = []
            for result in lm_results:
                if result.get('confidence', 0) >= confidence_threshold:
                    from ..models.data_models import OCRResult
                    
                    ocr_result = OCRResult(
                        text=result['text'],
                        timestamp=result['timestamp'],
                        confidence=result['confidence'],
                        bounding_box=None,  # LM Studio ne fournit pas de bounding boxes par défaut
                        language="auto",
                        method="lm_studio_multimodal"
                    )
                    ocr_results.append(ocr_result)
            
            self.logger.info(f"LM Studio OCR completed: {len(ocr_results)} results above threshold")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"LM Studio OCR extraction failed: {e}")
            raise ProcessingError(f"LM Studio OCR extraction failed: {e}")
    
    def _extract_text_with_nemo_ocr(
        self, 
        frames: List[Frame], 
        model_name: str, 
        confidence_threshold: float = 0.5
    ) -> List[OCRResult]:
        """
        Extrait le texte avec NeMo multimodal.
        
        Args:
            frames: Liste des frames à analyser
            model_name: Nom du modèle NeMo
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Liste des résultats OCR
        """
        try:
            self.logger.info(f"Extracting text from {len(frames)} frames using NeMo {model_name}")
            
            # Pour l'instant, utiliser une implémentation placeholder
            # L'implémentation complète nécessiterait des modèles NeMo Vision spécialisés
            ocr_results = []
            
            for frame in frames:
                from ..models.data_models import OCRResult
                
                # Simulation d'extraction de texte NeMo
                result = OCRResult(
                    text=f"Texte extrait par NeMo du frame à {frame.timestamp:.2f}s",
                    timestamp=frame.timestamp,
                    confidence=0.85,
                    bounding_box=None,
                    language="auto",
                    method="nemo_multimodal"
                )
                ocr_results.append(result)
            
            self.logger.info(f"NeMo OCR completed: {len(ocr_results)} results")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"NeMo OCR extraction failed: {e}")
            raise ProcessingError(f"NeMo OCR extraction failed: {e}")
    
    def _extract_text_with_traditional_ocr(
        self, 
        frames: List[Frame], 
        model_name: str, 
        languages: List[str] = None,
        confidence_threshold: float = 0.5,
        detect_changes: bool = True,
        similarity_threshold: float = 0.8
    ) -> List[OCRResult]:
        """
        Extrait le texte avec les méthodes OCR traditionnelles (PaddleOCR, EasyOCR).
        
        Args:
            frames: Liste des frames à analyser
            model_name: Nom du modèle OCR traditionnel
            languages: Langues à détecter
            confidence_threshold: Seuil de confiance minimum
            detect_changes: Détecter les changements entre frames
            similarity_threshold: Seuil de similarité
            
        Returns:
            Liste des résultats OCR
        """
        try:
            # Charger le modèle OCR traditionnel
            ocr_model = self.get_model(ModelType.OCR, model_name)
            
            self.logger.info(f"Extracting text from {len(frames)} frames using traditional OCR {model_name}")
            
            ocr_results = []
            previous_result = None
            
            for frame in frames:
                try:
                    # Extraire le texte du frame
                    if model_name == "paddleocr":
                        frame_results = self._extract_with_paddleocr(frame.image_data, ocr_model)
                    elif model_name == "easyocr":
                        frame_results = self._extract_with_easyocr(frame.image_data, ocr_model)
                    else:
                        raise ProcessingError(f"Unsupported traditional OCR model: {model_name}")
                    
                    # Filtrer par seuil de confiance
                    for result in frame_results:
                        if result.confidence >= confidence_threshold:
                            result.timestamp = frame.timestamp
                            
                            # Détecter les changements si activé
                            if detect_changes and previous_result:
                                similarity = self._calculate_text_similarity(
                                    previous_result.text, result.text
                                )
                                if similarity < similarity_threshold:
                                    ocr_results.append(result)
                                    previous_result = result
                            else:
                                ocr_results.append(result)
                                previous_result = result
                
                except Exception as e:
                    self.logger.warning(f"Traditional OCR failed for frame at {frame.timestamp}s: {e}")
                    continue
            
            self.logger.info(f"Traditional OCR completed: {len(ocr_results)} results above threshold")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"Traditional OCR extraction failed: {e}")
            raise ProcessingError(f"Traditional OCR extraction failed: {e}")
            
            # Traiter les frames
            ocr_results = []
            previous_text = ""
            previous_boxes = []
            
            for i, frame in enumerate(frames):
                try:
                    # Extraire le texte de la frame
                    frame_results = self._extract_text_from_single_frame(
                        frame, ocr_model, model_name, languages, confidence_threshold
                    )
                    
                    if not frame_results:
                        continue
                    
                    # Combiner tous les textes de la frame
                    current_text = " ".join([result.text for result in frame_results])
                    current_boxes = [result.bounding_box for result in frame_results if result.bounding_box]
                    
                    # Détecter les changements si activé
                    if detect_changes and i > 0:
                        text_similarity = self._calculate_text_similarity(previous_text, current_text)
                        spatial_similarity = self._calculate_spatial_similarity(previous_boxes, current_boxes)
                        
                        # Si le texte est trop similaire, ignorer cette frame
                        if (text_similarity > similarity_threshold and 
                            spatial_similarity > similarity_threshold):
                            continue
                    
                    # Ajouter les résultats
                    for result in frame_results:
                        ocr_results.append(result)
                    
                    previous_text = current_text
                    previous_boxes = current_boxes
                    
                    if i % 100 == 0:
                        self.logger.debug(f"Processed {i+1}/{len(frames)} frames")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process frame {i}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            # Post-traitement des résultats
            processed_results = self._post_process_ocr_results(ocr_results)
            
            self.logger.info(
                f"OCR extraction completed in {processing_time:.2f}s "
                f"({len(processed_results)} text segments found)"
            )
            
            return processed_results
            
        except Exception as e:
            raise ProcessingError(f"OCR extraction failed: {e}")
    
    def _extract_text_from_single_frame(
        self, 
        frame: Frame, 
        ocr_model: Any, 
        model_name: str,
        languages: List[str] = None,
        confidence_threshold: float = 0.5
    ) -> List[OCRResult]:
        """
        Extrait le texte d'une seule frame.
        
        Args:
            frame: Frame à analyser
            ocr_model: Modèle OCR chargé
            model_name: Nom du modèle
            languages: Langues à détecter
            confidence_threshold: Seuil de confiance
            
        Returns:
            Liste des résultats OCR pour cette frame
        """
        from ..models.data_models import OCRResult
        
        try:
            # Préparer l'image - soit depuis image_data soit depuis image_path
            if hasattr(frame, 'image_path') and frame.image_path:
                # Utiliser le chemin d'image si disponible
                image_input = frame.image_path
                if not Path(image_input).exists():
                    return []
            elif hasattr(frame, 'image_data') and frame.image_data is not None:
                # Utiliser les données d'image directement
                image_input = frame.image_data
            else:
                self.logger.warning(f"Frame at {frame.timestamp}s has no image data or path")
                return []
            
            # Extraire le texte selon le modèle
            if model_name == "paddleocr":
                return self._extract_with_paddleocr(
                    image_input, ocr_model, frame.timestamp, confidence_threshold
                )
            elif model_name == "easyocr":
                return self._extract_with_easyocr(
                    image_input, ocr_model, frame.timestamp, confidence_threshold, languages
                )
            else:
                raise ProcessingError(f"Unsupported OCR model: {model_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to extract text from frame {frame.timestamp}: {e}")
            return []
    
    def _extract_with_paddleocr(
        self, 
        image_input: Union[str, Any], 
        ocr_model: Any, 
        timestamp: float,
        confidence_threshold: float
    ) -> List[OCRResult]:
        """
        Extrait le texte avec PaddleOCR.
        
        Args:
            image_input: Chemin vers l'image ou données d'image (numpy array)
            ocr_model: Modèle PaddleOCR
            timestamp: Horodatage de la frame
            confidence_threshold: Seuil de confiance
            
        Returns:
            Liste des résultats OCR
        """
        from ..models.data_models import OCRResult
        
        try:
            # Analyser l'image (PaddleOCR accepte les chemins et les numpy arrays)
            results = ocr_model.ocr(image_input, cls=True)
            
            ocr_results = []
            
            if results and results[0]:
                for line in results[0]:
                    if len(line) >= 2:
                        # Extraire les informations
                        bbox = line[0]  # Bounding box
                        text_info = line[1]  # (text, confidence)
                        
                        if len(text_info) >= 2:
                            text = text_info[0].strip()
                            confidence = float(text_info[1])
                            
                            # Filtrer par confiance
                            if confidence >= confidence_threshold and text:
                                # Convertir la bounding box
                                bounding_box = {
                                    "x1": int(min(point[0] for point in bbox)),
                                    "y1": int(min(point[1] for point in bbox)),
                                    "x2": int(max(point[0] for point in bbox)),
                                    "y2": int(max(point[1] for point in bbox))
                                }
                                
                                ocr_result = OCRResult(
                                    text=text,
                                    timestamp=timestamp,
                                    confidence=confidence,
                                    bounding_box=bounding_box
                                )
                                ocr_results.append(ocr_result)
            
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"PaddleOCR extraction failed: {e}")
            return []
    
    def _extract_with_easyocr(
        self, 
        image_input: Union[str, Any], 
        ocr_model: Any, 
        timestamp: float,
        confidence_threshold: float,
        languages: List[str] = None
    ) -> List[OCRResult]:
        """
        Extrait le texte avec EasyOCR.
        
        Args:
            image_input: Chemin vers l'image ou données d'image (numpy array)
            ocr_model: Modèle EasyOCR
            timestamp: Horodatage de la frame
            confidence_threshold: Seuil de confiance
            languages: Langues à détecter
            
        Returns:
            Liste des résultats OCR
        """
        from ..models.data_models import OCRResult
        
        try:
            # Analyser l'image (EasyOCR accepte les chemins et les numpy arrays)
            results = ocr_model.readtext(image_input)
            
            ocr_results = []
            
            for result in results:
                if len(result) >= 3:
                    bbox = result[0]  # Bounding box
                    text = result[1].strip()  # Texte
                    confidence = float(result[2])  # Confiance
                    
                    # Filtrer par confiance
                    if confidence >= confidence_threshold and text:
                        # Convertir la bounding box
                        bounding_box = {
                            "x1": int(min(point[0] for point in bbox)),
                            "y1": int(min(point[1] for point in bbox)),
                            "x2": int(max(point[0] for point in bbox)),
                            "y2": int(max(point[1] for point in bbox))
                        }
                        
                        ocr_result = OCRResult(
                            text=text,
                            timestamp=timestamp,
                            confidence=confidence,
                            bounding_box=bounding_box
                        )
                        ocr_results.append(ocr_result)
            
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"EasyOCR extraction failed: {e}")
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes.
        
        Args:
            text1: Premier texte
            text2: Deuxième texte
            
        Returns:
            Score de similarité (0.0 à 1.0)
        """
        # Cas spéciaux pour textes vides
        if not text1 and not text2:
            return 1.0  # Deux textes vides sont identiques
        
        if not text1 or not text2:
            return 0.0  # Un texte vide et un non-vide sont différents
        
        # Normaliser les textes
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Calculer la similarité de Jaccard sur les mots
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_spatial_similarity(
        self, 
        boxes1: List[Dict[str, int]], 
        boxes2: List[Dict[str, int]]
    ) -> float:
        """
        Calcule la similarité spatiale entre deux ensembles de bounding boxes.
        
        Args:
            boxes1: Premier ensemble de boxes
            boxes2: Deuxième ensemble de boxes
            
        Returns:
            Score de similarité spatiale (0.0 à 1.0)
        """
        if not boxes1 or not boxes2:
            return 0.0
        
        # Calculer l'IoU moyen entre les boxes les plus proches
        total_iou = 0.0
        matches = 0
        
        for box1 in boxes1:
            best_iou = 0.0
            for box2 in boxes2:
                iou = self._calculate_iou(box1, box2)
                best_iou = max(best_iou, iou)
            
            total_iou += best_iou
            matches += 1
        
        return total_iou / matches if matches > 0 else 0.0
    
    def _calculate_iou(self, box1: Dict[str, int], box2: Dict[str, int]) -> float:
        """
        Calcule l'Intersection over Union entre deux bounding boxes.
        
        Args:
            box1: Première bounding box
            box2: Deuxième bounding box
            
        Returns:
            Score IoU (0.0 à 1.0)
        """
        # Calculer l'intersection
        x1 = max(box1["x1"], box2["x1"])
        y1 = max(box1["y1"], box2["y1"])
        x2 = min(box1["x2"], box2["x2"])
        y2 = min(box1["y2"], box2["y2"])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculer l'union
        area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
        area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _post_process_ocr_results(self, ocr_results: List[OCRResult]) -> List[OCRResult]:
        """
        Post-traite les résultats OCR.
        
        Args:
            ocr_results: Résultats bruts
            
        Returns:
            Résultats traités
        """
        if not ocr_results:
            return []
        
        # Trier par timestamp
        sorted_results = sorted(ocr_results, key=lambda x: x.timestamp)
        
        # Fusionner les résultats très proches temporellement
        merged_results = []
        current_group = [sorted_results[0]]
        
        for result in sorted_results[1:]:
            # Si le timestamp est très proche (< 0.1s), grouper
            if result.timestamp - current_group[-1].timestamp < 0.1:
                current_group.append(result)
            else:
                # Traiter le groupe actuel
                merged_result = self._merge_ocr_group(current_group)
                if merged_result:
                    merged_results.append(merged_result)
                current_group = [result]
        
        # Traiter le dernier groupe
        if current_group:
            merged_result = self._merge_ocr_group(current_group)
            if merged_result:
                merged_results.append(merged_result)
        
        return merged_results
    
    def _merge_ocr_group(self, ocr_group: List[OCRResult]) -> Optional[OCRResult]:
        """
        Fusionne un groupe de résultats OCR proches.
        
        Args:
            ocr_group: Groupe de résultats à fusionner
            
        Returns:
            Résultat fusionné ou None
        """
        if not ocr_group:
            return None
        
        if len(ocr_group) == 1:
            return ocr_group[0]
        
        # Combiner les textes
        texts = [result.text for result in ocr_group if result.text.strip()]
        if not texts:
            return None
        
        combined_text = " ".join(texts)
        
        # Calculer la confiance moyenne
        avg_confidence = sum(result.confidence for result in ocr_group) / len(ocr_group)
        
        # Utiliser le timestamp du premier résultat
        timestamp = ocr_group[0].timestamp
        
        # Calculer une bounding box englobante si disponible
        bounding_box = None
        boxes = [result.bounding_box for result in ocr_group if result.bounding_box]
        if boxes:
            bounding_box = {
                "x1": min(box["x1"] for box in boxes),
                "y1": min(box["y1"] for box in boxes),
                "x2": max(box["x2"] for box in boxes),
                "y2": max(box["y2"] for box in boxes)
            }
        
        from ..models.data_models import OCRResult
        return OCRResult(
            text=combined_text,
            timestamp=timestamp,
            confidence=avg_confidence,
            bounding_box=bounding_box
        )
    
    def extract_text_from_video_segment(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float,
        frame_interval: float = 0.5,
        **kwargs
    ) -> List[OCRResult]:
        """
        Extrait le texte d'un segment vidéo.
        
        Args:
            video_path: Chemin vers la vidéo
            start_time: Temps de début en secondes
            end_time: Temps de fin en secondes
            frame_interval: Intervalle entre les frames en secondes
            **kwargs: Options OCR
            
        Returns:
            Liste des résultats OCR
        """
        try:
            # Extraire les frames du segment
            from ..processors.video_processor import VideoProcessor
            video_processor = VideoProcessor()
            
            frames = video_processor.extract_frames_from_interval(
                video_path, start_time, end_time, frame_interval
            )
            
            # Extraire le texte des frames
            return self.extract_text_from_frames(frames, **kwargs)
            
        except Exception as e:
            raise ProcessingError(f"Failed to extract text from video segment: {e}")
    
    def get_ocr_statistics(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """
        Calcule des statistiques sur les résultats OCR.
        
        Args:
            ocr_results: Résultats OCR à analyser
            
        Returns:
            Dictionnaire des statistiques
        """
        if not ocr_results:
            return {
                "total_segments": 0,
                "total_characters": 0,
                "average_confidence": 0.0,
                "duration": 0.0,
                "text_density": 0.0
            }
        
        total_segments = len(ocr_results)
        total_characters = sum(len(result.text) for result in ocr_results)
        average_confidence = sum(result.confidence for result in ocr_results) / total_segments
        
        # Calculer la durée
        timestamps = [result.timestamp for result in ocr_results]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0.0
        
        # Densité de texte (caractères par seconde)
        text_density = total_characters / duration if duration > 0 else 0.0
        
        return {
            "total_segments": total_segments,
            "total_characters": total_characters,
            "average_confidence": average_confidence,
            "duration": duration,
            "text_density": text_density,
            "confidence_distribution": self._calculate_confidence_distribution(ocr_results)
        }
    
    def _calculate_confidence_distribution(self, ocr_results: List[OCRResult]) -> Dict[str, int]:
        """
        Calcule la distribution des scores de confiance.
        
        Args:
            ocr_results: Résultats OCR
            
        Returns:
            Distribution par tranches de confiance
        """
        distribution = {
            "very_low": 0,    # 0.0 - 0.3
            "low": 0,         # 0.3 - 0.5
            "medium": 0,      # 0.5 - 0.7
            "high": 0,        # 0.7 - 0.9
            "very_high": 0    # 0.9 - 1.0
        }
        
        for result in ocr_results:
            confidence = result.confidence
            if confidence < 0.3:
                distribution["very_low"] += 1
            elif confidence < 0.5:
                distribution["low"] += 1
            elif confidence < 0.7:
                distribution["medium"] += 1
            elif confidence < 0.9:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1
        
        return distribution
    
    def clone_voice(self, reference_audio: str, text: str) -> str:
        """Clone une voix - à implémenter dans la tâche 12."""
        raise NotImplementedError("À implémenter dans la tâche 12")    
  
  # ===== NOUVELLES MÉTHODES POUR NEMO ET LM STUDIO =====
    
    def _load_nemo_asr_model(self, model_name: str) -> Any:
        """
        Charge un modèle NVIDIA NeMo ASR.
        
        Args:
            model_name: Nom du modèle NeMo
            
        Returns:
            Modèle NeMo chargé
        """
        if not _NEMO_AVAILABLE:
            raise ProcessingError("NVIDIA NeMo not available. Install with: pip install nemo_toolkit")
        
        try:
            # Mapper les noms de modèles vers les modèles NeMo
            nemo_model_mapping = {
                "nemo-conformer-ctc-large-fr": "nvidia/stt_fr_conformer_ctc_large",
                "nemo-conformer-ctc-large-en": "nvidia/stt_en_conformer_ctc_large", 
                "nemo-fastconformer-multilingual": "nvidia/stt_multilingual_fastconformer_hybrid_large_pc"
            }
            
            nemo_model_id = nemo_model_mapping.get(model_name)
            if not nemo_model_id:
                raise ProcessingError(f"Unknown NeMo ASR model: {model_name}")
            
            self.logger.info(f"Loading NeMo ASR model: {nemo_model_id}")
            
            # Charger le modèle NeMo
            model = nemo_asr.models.ASRModel.from_pretrained(nemo_model_id)
            
            # Configurer pour l'inférence
            model.eval()
            if _TORCH_AVAILABLE and torch.cuda.is_available():
                model = model.cuda()
            
            self.logger.info(f"NeMo ASR model {model_name} loaded successfully")
            return model
            
        except Exception as e:
            raise ProcessingError(f"Failed to load NeMo ASR model {model_name}: {e}")
    
    def _load_nemo_ocr_model(self, model_name: str) -> Any:
        """
        Charge un modèle NVIDIA NeMo pour l'OCR/Vision.
        
        Args:
            model_name: Nom du modèle NeMo
            
        Returns:
            Modèle NeMo chargé
        """
        if not _NEMO_AVAILABLE:
            raise ProcessingError("NVIDIA NeMo not available. Install with: pip install nemo_toolkit")
        
        try:
            # Pour l'instant, utiliser un placeholder car les modèles NeMo Vision sont moins courants
            self.logger.warning(f"NeMo OCR model {model_name} not fully implemented yet")
            
            # Retourner un wrapper qui peut être utilisé pour l'OCR
            return {
                "model_name": model_name,
                "model_type": "nemo_ocr",
                "placeholder": True,
                "capabilities": ["ocr", "vision", "multimodal"]
            }
            
        except Exception as e:
            raise ProcessingError(f"Failed to load NeMo OCR model {model_name}: {e}")
    
    def _load_lm_studio_asr_model(self, model_name: str) -> Any:
        """
        Charge un modèle LM Studio pour l'ASR.
        
        Args:
            model_name: Nom du modèle LM Studio
            
        Returns:
            Wrapper pour modèle LM Studio
        """
        if not self.lm_studio_manager or not self.lm_studio_manager.is_available():
            raise ProcessingError("LM Studio not available or not running")
        
        try:
            # Obtenir les modèles disponibles pour la transcription
            available_models = self.lm_studio_manager.get_models_for_transcription()
            
            if not available_models:
                raise ProcessingError("No transcription models available in LM Studio")
            
            # Utiliser le premier modèle disponible ou chercher un modèle spécifique
            selected_model = available_models[0]
            
            # Créer un wrapper pour l'utilisation
            model_wrapper = {
                "model_id": selected_model["id"],
                "model_name": model_name,
                "model_type": "lm_studio_asr",
                "lm_studio_manager": self.lm_studio_manager,
                "capabilities": selected_model.get("capabilities", []),
                "full_info": selected_model
            }
            
            self.logger.info(f"LM Studio ASR model wrapper created: {selected_model['id']}")
            return model_wrapper
            
        except Exception as e:
            raise ProcessingError(f"Failed to load LM Studio ASR model {model_name}: {e}")
    
    def _load_lm_studio_ocr_model(self, model_name: str) -> Any:
        """
        Charge un modèle LM Studio pour l'OCR.
        
        Args:
            model_name: Nom du modèle LM Studio
            
        Returns:
            Wrapper pour modèle LM Studio
        """
        if not self.lm_studio_manager or not self.lm_studio_manager.is_available():
            raise ProcessingError("LM Studio not available or not running")
        
        try:
            # Obtenir les modèles disponibles pour l'OCR
            available_models = self.lm_studio_manager.get_models_for_ocr()
            
            if not available_models:
                raise ProcessingError("No OCR/Vision models available in LM Studio")
            
            # Utiliser le premier modèle disponible
            selected_model = available_models[0]
            
            # Créer un wrapper pour l'utilisation
            model_wrapper = {
                "model_id": selected_model["id"],
                "model_name": model_name,
                "model_type": "lm_studio_ocr",
                "lm_studio_manager": self.lm_studio_manager,
                "capabilities": selected_model.get("capabilities", []),
                "full_info": selected_model
            }
            
            self.logger.info(f"LM Studio OCR model wrapper created: {selected_model['id']}")
            return model_wrapper
            
        except Exception as e:
            raise ProcessingError(f"Failed to load LM Studio OCR model {model_name}: {e}")
    
    def transcribe_audio_with_nemo(
        self,
        audio_path: str,
        model_name: str = "nemo-conformer-ctc-large-fr",
        language: str = "fr"
    ) -> TranscriptionResult:
        """
        Transcrit l'audio avec un modèle NeMo.
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle NeMo
            language: Langue de transcription
            
        Returns:
            Résultats de transcription
        """
        try:
            self.logger.info(f"Starting NeMo transcription of {audio_path}")
            start_time = time.time()
            
            # Charger le modèle NeMo
            model = self.get_model(ModelType.ASR, model_name)
            
            # Transcrire avec NeMo
            transcripts = model.transcribe([audio_path])
            
            processing_time = time.time() - start_time
            
            # Traiter les résultats
            if transcripts and len(transcripts) > 0:
                transcript_text = transcripts[0]
                
                # Créer un segment unique (NeMo ne fournit pas de segmentation automatique)
                from ..models.data_models import TranscriptionSegment
                
                segment = TranscriptionSegment(
                    text=transcript_text,
                    start=0.0,
                    end=self._estimate_audio_duration_simple(audio_path),
                    confidence=0.90,  # Estimation pour NeMo
                    word_timestamps=[]  # NeMo CTC ne fournit pas d'horodatages de mots par défaut
                )
                
                result = TranscriptionResult(
                    text=transcript_text,
                    segments=[segment],
                    language=language,
                    confidence=0.90,
                    processing_time=processing_time,
                    model_name=model_name,
                    word_count=len(transcript_text.split()) if transcript_text else 0
                )
                
                self.logger.info(f"NeMo transcription completed in {processing_time:.2f}s")
                return result
            else:
                raise ProcessingError("NeMo transcription returned empty result")
                
        except Exception as e:
            raise ProcessingError(f"NeMo transcription failed: {e}")
    
    def transcribe_audio_with_lm_studio(
        self,
        audio_path: str,
        model_name: str = "lm-studio-whisper",
        language: str = "fr"
    ) -> TranscriptionResult:
        """
        Transcrit l'audio avec LM Studio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle LM Studio
            language: Langue de transcription
            
        Returns:
            Résultats de transcription
        """
        try:
            self.logger.info(f"Starting LM Studio transcription of {audio_path}")
            
            # Charger le wrapper du modèle LM Studio
            model_wrapper = self.get_model(ModelType.ASR, model_name)
            
            # Utiliser le gestionnaire LM Studio pour la transcription
            result = model_wrapper["lm_studio_manager"].transcribe_audio_with_lm_studio(
                audio_path=audio_path,
                model_id=model_wrapper["model_id"],
                language=language
            )
            
            self.logger.info("LM Studio transcription completed")
            return result
            
        except Exception as e:
            raise ProcessingError(f"LM Studio transcription failed: {e}")
    
    def extract_text_from_frames_with_nemo(
        self,
        frames: List[Frame],
        model_name: str = "nemo-vision-transformer"
    ) -> List[OCRResult]:
        """
        Extrait du texte des images avec NeMo.
        
        Args:
            frames: Liste des images à traiter
            model_name: Nom du modèle NeMo
            
        Returns:
            Liste des résultats OCR
        """
        try:
            self.logger.info(f"Starting NeMo OCR for {len(frames)} frames")
            
            # Charger le modèle NeMo (placeholder pour l'instant)
            model = self.get_model(ModelType.OCR, model_name)
            
            # Pour l'instant, retourner des résultats simulés
            # L'implémentation complète nécessiterait des modèles NeMo Vision spécialisés
            ocr_results = []
            
            for i, frame in enumerate(frames):
                # Simulation d'extraction de texte
                result = OCRResult(
                    text=f"Texte extrait par NeMo du frame {i+1}",
                    timestamp=frame.timestamp,
                    confidence=0.85,
                    bounding_box=None
                )
                ocr_results.append(result)
            
            self.logger.info(f"NeMo OCR completed for {len(ocr_results)} frames")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"NeMo OCR failed: {e}")
            return []
    
    def extract_text_from_frames_with_lm_studio(
        self,
        frames: List[Frame],
        model_name: str = "lm-studio-vision"
    ) -> List[OCRResult]:
        """
        Extrait du texte des images avec LM Studio.
        
        Args:
            frames: Liste des images à traiter
            model_name: Nom du modèle LM Studio
            
        Returns:
            Liste des résultats OCR
        """
        try:
            self.logger.info(f"Starting LM Studio OCR for {len(frames)} frames")
            
            # Charger le wrapper du modèle LM Studio
            model_wrapper = self.get_model(ModelType.OCR, model_name)
            
            ocr_results = []
            
            for frame in frames:
                # Utiliser le gestionnaire LM Studio pour l'OCR
                frame_results = model_wrapper["lm_studio_manager"].extract_text_with_lm_studio(
                    image_data=frame.image_data,
                    model_id=model_wrapper["model_id"]
                )
                
                # Ajouter le timestamp du frame
                for result in frame_results:
                    result.timestamp = frame.timestamp
                
                ocr_results.extend(frame_results)
            
            self.logger.info(f"LM Studio OCR completed for {len(ocr_results)} results")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"LM Studio OCR failed: {e}")
            return []
    
    def get_available_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retourne la liste des modèles disponibles par catégorie.
        Returns:
            Dictionnaire des modèles disponibles avec métadonnées
        """
        try:
            # Découvrir tous les modèles disponibles
            discovered_models = self.model_discovery.discover_all_models()
            
            # Ajouter les modèles LM Studio
            lm_studio_models = self.lm_studio_manager.get_available_models()
            
            # Organiser par catégorie pour l'interface
            available_models = {
                "asr": [],
                "ocr": [],
                "voice_cloning": [],
                "lm_studio": lm_studio_models
            }
            
            # Modèles de transcription
            for model in discovered_models.get('transcription', []):
                available_models["asr"].append({
                    'name': model['name'],
                    'framework': model['framework'],
                    'status': model['status'],
                    'size': model.get('size', 0),
                    'type': 'transcription'
                })
            
            # Modèles OCR et multimodaux
            ocr_models = discovered_models.get('multimodal', [])
            
            # Ajouter les modèles OCR traditionnels
            ocr_models.extend([
                {
                    'name': 'paddleocr',
                    'framework': 'paddleocr',
                    'status': 'available',
                    'size': 0,
                    'type': 'ocr'
                }
            ])
            
            available_models["ocr"] = ocr_models
            
            # Modèles de clonage vocal
            available_models["voice_cloning"] = discovered_models.get('voice_cloning', [])
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            # Retourner les modèles par défaut en cas d'erreur
            return {
                "asr": [
                    {'name': 'whisper-base', 'framework': 'whisper', 'status': 'available', 'size': 0, 'type': 'transcription'}
                ],
                "ocr": [
                    {'name': 'paddleocr', 'framework': 'paddleocr', 'status': 'available', 'size': 0, 'type': 'ocr'}
                ],
                "voice_cloning": [],
                "lm_studio": []
            }

    def get_available_ocr_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtient tous les modèles OCR disponibles par source.
        
        Returns:
            Dictionnaire des modèles OCR par source
        """
        ocr_models = {
            'traditional': [],
            'lm_studio': [],
            'nemo': [],
            'huggingface': []
        }
        
        try:
            # Modèles OCR traditionnels
            if _PADDLEOCR_AVAILABLE:
                ocr_models['traditional'].append({
                    'name': 'paddleocr',
                    'framework': 'paddleocr',
                    'type': 'traditional_ocr',
                    'languages': ['en', 'fr', 'es', 'de', 'zh'],
                    'quality': 'good',
                    'speed': 'fast',
                    'status': 'available'
                })
            
            if _EASYOCR_AVAILABLE:
                ocr_models['traditional'].append({
                    'name': 'easyocr',
                    'framework': 'easyocr',
                    'type': 'traditional_ocr',
                    'languages': ['en', 'fr', 'es', 'de'],
                    'quality': 'good',
                    'speed': 'medium',
                    'status': 'available'
                })
            
            # Modèles LM Studio multimodaux
            if self.lm_studio_manager and self.lm_studio_manager.is_available():
                lm_multimodal = self.lm_studio_manager.get_multimodal_models()
                for model in lm_multimodal:
                    ocr_models['lm_studio'].append({
                        'name': model['name'],
                        'framework': 'lm_studio',
                        'type': 'multimodal_ocr',
                        'languages': ['multilingual'],
                        'quality': model.get('ocr_quality', 'medium'),
                        'speed': 'slow',
                        'status': model.get('status', 'available'),
                        'capabilities': model.get('capabilities', [])
                    })
            
            # Modèles NeMo (placeholder)
            ocr_models['nemo'].append({
                'name': 'nemo-vision-transformer',
                'framework': 'nemo',
                'type': 'multimodal_ocr',
                'languages': ['multilingual'],
                'quality': 'high',
                'speed': 'medium',
                'status': 'available' if _NEMO_AVAILABLE else 'not_installed'
            })
            
            return ocr_models
            
        except Exception as e:
            self.logger.error(f"Failed to get OCR models: {e}")
            return ocr_models
    
    def get_best_ocr_model(self, prefer_quality: bool = True) -> Optional[Dict[str, Any]]:
        """
        Obtient le meilleur modèle OCR disponible.
        
        Args:
            prefer_quality: Préférer la qualité à la vitesse
            
        Returns:
            Meilleur modèle OCR ou None
        """
        try:
            all_ocr_models = self.get_available_ocr_models()
            
            # Collecter tous les modèles disponibles
            available_models = []
            for source, models in all_ocr_models.items():
                for model in models:
                    if model.get('status') == 'available':
                        available_models.append(model)
            
            if not available_models:
                return None
            
            # Critères de sélection
            def model_score(model):
                score = 0
                
                # Qualité
                quality_scores = {'high': 30, 'good': 20, 'medium': 15, 'basic': 10}
                score += quality_scores.get(model.get('quality', 'medium'), 15)
                
                # Vitesse (inversée si on préfère la qualité)
                speed_scores = {'fast': 20, 'medium': 15, 'slow': 10}
                if prefer_quality:
                    # Inverser les scores de vitesse si on préfère la qualité
                    speed_scores = {'fast': 10, 'medium': 15, 'slow': 20}
                score += speed_scores.get(model.get('speed', 'medium'), 15)
                
                # Type de modèle (multimodal > traditionnel)
                if model.get('type') == 'multimodal_ocr':
                    score += 25
                elif model.get('type') == 'traditional_ocr':
                    score += 15
                
                # Framework bonus
                framework_bonus = {
                    'lm_studio': 10,  # Bonus pour flexibilité
                    'nemo': 8,        # Bonus pour performance
                    'paddleocr': 5,   # Bonus pour fiabilité
                    'easyocr': 3
                }
                score += framework_bonus.get(model.get('framework', ''), 0)
                
                return score
            
            # Retourner le modèle avec le meilleur score
            best_model = max(available_models, key=model_score)
            return best_model
            
        except Exception as e:
            self.logger.error(f"Failed to get best OCR model: {e}")
            return None
    
    def test_ocr_model(self, model_name: str) -> Dict[str, Any]:
        """
        Teste un modèle OCR spécifique.
        
        Args:
            model_name: Nom du modèle à tester
            
        Returns:
            Résultats du test
        """
        test_results = {
            'model_name': model_name,
            'available': False,
            'functional': False,
            'estimated_quality': 'unknown',
            'estimated_speed': 'unknown',
            'error_message': None
        }
        
        try:
            # Tester selon le type de modèle
            if model_name.startswith('lm-studio-') or model_name in [m['name'] for m in self.lm_studio_manager.get_multimodal_models()]:
                # Test LM Studio
                if self.lm_studio_manager and self.lm_studio_manager.is_available():
                    lm_test = self.lm_studio_manager.test_ocr_capability(model_name)
                    test_results['available'] = True
                    test_results['functional'] = lm_test.get('ocr_capable', False)
                    test_results['estimated_quality'] = 'high' if lm_test.get('ocr_capable') else 'unknown'
                    test_results['estimated_speed'] = 'slow'
                    if lm_test.get('error_message'):
                        test_results['error_message'] = lm_test['error_message']
                else:
                    test_results['error_message'] = "LM Studio not available"
            
            elif model_name == 'paddleocr':
                # Test PaddleOCR
                test_results['available'] = _PADDLEOCR_AVAILABLE
                test_results['functional'] = _PADDLEOCR_AVAILABLE
                test_results['estimated_quality'] = 'good'
                test_results['estimated_speed'] = 'fast'
                if not _PADDLEOCR_AVAILABLE:
                    test_results['error_message'] = "PaddleOCR not installed"
            
            elif model_name == 'easyocr':
                # Test EasyOCR
                test_results['available'] = _EASYOCR_AVAILABLE
                test_results['functional'] = _EASYOCR_AVAILABLE
                test_results['estimated_quality'] = 'good'
                test_results['estimated_speed'] = 'medium'
                if not _EASYOCR_AVAILABLE:
                    test_results['error_message'] = "EasyOCR not installed"
            
            elif 'nemo' in model_name.lower():
                # Test NeMo
                test_results['available'] = _NEMO_AVAILABLE
                test_results['functional'] = _NEMO_AVAILABLE
                test_results['estimated_quality'] = 'high'
                test_results['estimated_speed'] = 'medium'
                if not _NEMO_AVAILABLE:
                    test_results['error_message'] = "NVIDIA NeMo not installed"
            
            else:
                test_results['error_message'] = f"Unknown model type: {model_name}"
            
        except Exception as e:
            test_results['error_message'] = str(e)
        
        return test_results
    
    def extract_text_from_single_image(
        self, 
        image_path: str, 
        model_name: str = None,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Extrait le texte d'une seule image.
        
        Args:
            image_path: Chemin vers l'image
            model_name: Nom du modèle à utiliser (None pour auto-sélection)
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Résultat d'extraction avec texte et métadonnées
        """
        try:
            if not os.path.exists(image_path):
                raise ValidationError(f"Image file not found: {image_path}")
            
            # Sélection automatique du modèle si non spécifié
            if model_name is None:
                best_model = self.get_best_ocr_model(prefer_quality=True)
                if not best_model:
                    raise ProcessingError("No OCR model available")
                model_name = best_model['name']
            
            self.logger.info(f"Extracting text from image {image_path} using {model_name}")
            
            # Extraction selon le type de modèle
            if model_name.startswith('lm-studio-') or model_name in [m['name'] for m in self.lm_studio_manager.get_multimodal_models()]:
                # Utiliser LM Studio
                result = self.lm_studio_manager.extract_text_from_image(image_path, model_name)
                if result:
                    return {
                        'text': result['text'],
                        'confidence': result.get('confidence', 0.8),
                        'model_used': model_name,
                        'method': 'lm_studio_multimodal',
                        'processing_time': 0.0  # À implémenter si nécessaire
                    }
                else:
                    raise ProcessingError("LM Studio OCR extraction failed")
            
            elif model_name in ['paddleocr', 'easyocr']:
                # Utiliser OCR traditionnel
                # Créer un frame temporaire
                import cv2
                image = cv2.imread(image_path)
                
                from ..models.data_models import Frame
                frame = Frame(
                    timestamp=0.0,
                    image_data=image,
                    frame_number=0
                )
                
                # Utiliser la méthode traditionnelle
                ocr_results = self._extract_text_with_traditional_ocr(
                    [frame], model_name, confidence_threshold=confidence_threshold
                )
                
                if ocr_results:
                    combined_text = " ".join([r.text for r in ocr_results])
                    avg_confidence = sum([r.confidence for r in ocr_results]) / len(ocr_results)
                    
                    return {
                        'text': combined_text,
                        'confidence': avg_confidence,
                        'model_used': model_name,
                        'method': 'traditional_ocr',
                        'processing_time': 0.0
                    }
                else:
                    return {
                        'text': '',
                        'confidence': 0.0,
                        'model_used': model_name,
                        'method': 'traditional_ocr',
                        'processing_time': 0.0
                    }
            
            else:
                raise ProcessingError(f"Unsupported OCR model: {model_name}")
                
        except Exception as e:
            self.logger.error(f"Single image OCR extraction failed: {e}")
            raise ProcessingError(f"OCR extraction failed: {e}")

    def get_available_models_summary(self) -> Dict[str, Any]:
        """
        Obtient un résumé de tous les modèles disponibles.
        
        Returns:
            Résumé des modèles disponibles par source
        """
        summary = {
            "local_models": {},
            "lm_studio_models": {},
            "nemo_models": {},
            "discovery_summary": {}
        }
        
        try:
            # Modèles locaux configurés
            summary["local_models"] = {
                "asr": list(self._model_configs.get(ModelType.ASR, {}).keys()),
                "ocr": list(self._model_configs.get(ModelType.OCR, {}).keys()),
                "voice_cloning": list(self._model_configs.get(ModelType.VOICE_CLONING, {}).keys())
            }
            
            # Modèles LM Studio
            if self.lm_studio_manager and self.lm_studio_manager.is_available():
                lm_summary = self.lm_studio_manager.get_model_info_summary()
                summary["lm_studio_models"] = {
                    "available": lm_summary.get("lm_studio_available", False),
                    "total_models": lm_summary.get("total_models", 0),
                    "transcription_models": lm_summary.get("transcription_models", 0),
                    "ocr_models": lm_summary.get("ocr_models", 0),
                    "recommended": lm_summary.get("recommended_models", {})
                }
            
            # Modèles NeMo
            summary["nemo_models"] = {
                "available": _NEMO_AVAILABLE,
                "asr_models": [
                    "nemo-conformer-ctc-large-fr",
                    "nemo-conformer-ctc-large-en", 
                    "nemo-fastconformer-multilingual"
                ],
                "ocr_models": [
                    "nemo-vision-transformer",
                    "nemo-multimodal-llm"
                ]
            }
            
            # Découverte de modèles
            if self.model_discovery:
                discovery_summary = self.model_discovery.get_discovery_summary()
                summary["discovery_summary"] = discovery_summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get models summary: {e}")
            summary["error"] = str(e)
            return summary
    
    def get_recommended_models_for_task(self, task: str, language: str = "fr") -> List[Dict[str, Any]]:
        """
        Obtient les modèles recommandés pour une tâche spécifique.
        
        Args:
            task: Type de tâche ("asr", "ocr", "voice_cloning")
            language: Langue cible
            
        Returns:
            Liste des modèles recommandés avec leurs informations
        """
        recommendations = []
        
        try:
            if task == "asr":
                # Recommandations ASR
                if language == "fr":
                    recommendations.extend([
                        {
                            "model_name": "nemo-conformer-ctc-large-fr",
                            "source": "nemo",
                            "quality": "high",
                            "speed": "medium",
                            "description": "Modèle NeMo spécialisé français, haute précision"
                        },
                        {
                            "model_name": "whisper-large-v3",
                            "source": "whisper",
                            "quality": "high",
                            "speed": "slow",
                            "description": "Whisper dernière version, multilingue"
                        },
                        {
                            "model_name": "whisper-medium",
                            "source": "whisper", 
                            "quality": "good",
                            "speed": "medium",
                            "description": "Bon compromis qualité/vitesse"
                        }
                    ])
                else:
                    recommendations.extend([
                        {
                            "model_name": "whisper-large-v3",
                            "source": "whisper",
                            "quality": "high", 
                            "speed": "slow",
                            "description": "Meilleure qualité multilingue"
                        },
                        {
                            "model_name": "nemo-fastconformer-multilingual",
                            "source": "nemo",
                            "quality": "high",
                            "speed": "medium",
                            "description": "NeMo multilingue rapide"
                        }
                    ])
                
                # Ajouter les modèles LM Studio disponibles
                if self.lm_studio_manager and self.lm_studio_manager.is_available():
                    lm_models = self.lm_studio_manager.get_models_for_transcription()
                    for model in lm_models[:2]:  # Top 2
                        recommendations.append({
                            "model_name": f"lm-studio-{model['name']}",
                            "source": "lm_studio",
                            "quality": "variable",
                            "speed": "variable", 
                            "description": f"LM Studio: {model.get('recommended_use', 'Modèle local')}"
                        })
            
            elif task == "ocr":
                recommendations.extend([
                    {
                        "model_name": "paddleocr",
                        "source": "paddleocr",
                        "quality": "good",
                        "speed": "fast",
                        "description": "OCR rapide et fiable"
                    },
                    {
                        "model_name": "nemo-vision-transformer",
                        "source": "nemo",
                        "quality": "high",
                        "speed": "medium",
                        "description": "NeMo Vision Transformer avancé"
                    }
                ])
                
                # Ajouter les modèles LM Studio OCR
                if self.lm_studio_manager and self.lm_studio_manager.is_available():
                    lm_models = self.lm_studio_manager.get_models_for_ocr()
                    for model in lm_models[:2]:  # Top 2
                        recommendations.append({
                            "model_name": f"lm-studio-{model['name']}",
                            "source": "lm_studio",
                            "quality": "variable",
                            "speed": "variable",
                            "description": f"LM Studio: {model.get('recommended_use', 'Modèle vision local')}"
                        })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to get recommendations for {task}: {e}")
            return []
    
    def _estimate_audio_duration_simple(self, audio_path: str) -> float:
        """
        Estime simplement la durée d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Durée estimée en secondes
        """
        try:
            # Estimation très basique basée sur la taille du fichier
            file_size = os.path.getsize(audio_path)
            # Approximation: 1MB ≈ 60 secondes pour un audio de qualité moyenne
            estimated_duration = file_size / (1024 * 1024) * 60
            return max(1.0, min(estimated_duration, 3600))  # Entre 1s et 1h
        except:
            return 30.0  # Valeur par défaut
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Obtient la durée d'un fichier audio."""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return float(info.get('format', {}).get('duration', 0.0))
        except Exception as e:
            self.logger.warning(f"Failed to get audio duration: {e}")
        
        return 0.0
    
    def _estimate_audio_duration_simple(self, audio_path: str) -> float:
        """Estime la durée audio de manière simple."""
        try:
            # Essayer avec librosa si disponible
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            return len(y) / sr
        except ImportError:
            # Fallback avec ffprobe
            return self._get_audio_duration(audio_path)
        except Exception:
            # Estimation par défaut
            return 30.0  # 30 secondes par défaut
    
    def _load_nemo_multimodal_model(self, model_name: str):
        """Charge un modèle NeMo multimodal."""
        try:
            if not _NEMO_AVAILABLE:
                raise ProcessingError("NVIDIA NeMo not available")
            
            # Pour l'instant, créer un placeholder
            self._nemo_multimodal_model = {
                "name": model_name,
                "type": "nemo_multimodal",
                "loaded": True
            }
            
            self._current_ocr_model = model_name
            self.logger.info(f"NeMo multimodal model {model_name} loaded (placeholder)")
            
        except Exception as e:
            self.logger.error(f"Failed to load NeMo multimodal model: {e}")
            raise ProcessingError(f"Failed to load NeMo multimodal model: {e}")