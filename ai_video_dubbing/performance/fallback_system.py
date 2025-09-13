"""
Système de fallback intelligent pour la transcription audio
"""
import asyncio
import logging
import time
import psutil
import torch
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import traceback

from .progress_interface import RealTimeProgressInterface, OperationStatus

logger = logging.getLogger(__name__)

class FallbackReason(Enum):
    """Raisons de basculement vers un fallback"""
    CUDA_ERROR = "cuda_error"
    MEMORY_ERROR = "memory_error"
    TIMEOUT = "timeout"
    MODEL_LOAD_ERROR = "model_load_error"
    TRANSCRIPTION_ERROR = "transcription_error"
    PERFORMANCE_ISSUE = "performance_issue"
    MANUAL_OVERRIDE = "manual_override"

class ModelType(Enum):
    """Types de modèles disponibles"""
    NEMO_GPU = "nemo_gpu"
    NEMO_CPU = "nemo_cpu"
    NEMO_LIGHT = "nemo_light"
    WHISPER_GPU = "whisper_gpu"
    WHISPER_CPU = "whisper_cpu"
    WHISPER_TINY = "whisper_tiny"

@dataclass
class FallbackConfig:
    """Configuration d'un fallback"""
    model_type: ModelType
    model_name: str
    device: str = "auto"
    max_memory_mb: int = 2048
    timeout_seconds: int = 300
    quality_score: float = 1.0  # 0.0 à 1.0
    speed_score: float = 1.0    # 0.0 à 1.0
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    def meets_requirements(self, system_info: Dict[str, Any]) -> bool:
        """Vérifie si la configuration peut fonctionner avec le système actuel"""
        # Vérifier la mémoire disponible
        available_memory = system_info.get("available_memory_mb", 0)
        if available_memory < self.max_memory_mb:
            return False
        
        # Vérifier CUDA si nécessaire
        if self.device == "cuda" or "gpu" in self.model_type.value:
            if not system_info.get("cuda_available", False):
                return False
        
        # Vérifications spécifiques aux requirements
        for req_key, req_value in self.requirements.items():
            if req_key not in system_info:
                return False
            if system_info[req_key] < req_value:
                return False
        
        return True

@dataclass
class FallbackAttempt:
    """Informations sur une tentative de fallback"""
    config: FallbackConfig
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    reason: Optional[FallbackReason] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Durée de la tentative"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

class IntelligentFallbackSystem:
    """Système de fallback intelligent avec chaîne de fallbacks automatique"""
    
    def __init__(self, progress_interface: Optional[RealTimeProgressInterface] = None):
        self.progress_interface = progress_interface
        
        # Configuration des fallbacks par ordre de préférence
        self.fallback_chain = self._create_default_fallback_chain()
        
        # Historique des tentatives
        self.attempt_history: List[FallbackAttempt] = []
        
        # Cache des informations système
        self._system_info_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 60.0  # 1 minute
        
        # Callbacks de notification
        self.notification_callbacks: List[Callable] = []
        
        # Statistiques
        self.stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "fallback_usage": {},
            "common_errors": {},
            "average_fallback_time": 0.0
        }
    
    def _create_default_fallback_chain(self) -> List[FallbackConfig]:
        """Crée la chaîne de fallback par défaut"""
        return [
            # 1. NeMo GPU (meilleure qualité)
            FallbackConfig(
                model_type=ModelType.NEMO_GPU,
                model_name="stt_en_conformer_ctc_large",
                device="cuda",
                max_memory_mb=4096,
                timeout_seconds=300,
                quality_score=1.0,
                speed_score=0.9,
                requirements={"cuda_memory_mb": 2048}
            ),
            
            # 2. NeMo Light GPU (bon compromis)
            FallbackConfig(
                model_type=ModelType.NEMO_LIGHT,
                model_name="stt_en_conformer_ctc_medium",
                device="cuda",
                max_memory_mb=2048,
                timeout_seconds=240,
                quality_score=0.85,
                speed_score=0.95,
                requirements={"cuda_memory_mb": 1024}
            ),
            
            # 3. Whisper GPU (alternative robuste)
            FallbackConfig(
                model_type=ModelType.WHISPER_GPU,
                model_name="whisper-base",
                device="cuda",
                max_memory_mb=1536,
                timeout_seconds=180,
                quality_score=0.8,
                speed_score=0.8,
                requirements={"cuda_memory_mb": 512}
            ),
            
            # 4. NeMo CPU (fallback CPU)
            FallbackConfig(
                model_type=ModelType.NEMO_CPU,
                model_name="stt_en_conformer_ctc_medium",
                device="cpu",
                max_memory_mb=3072,
                timeout_seconds=600,
                quality_score=0.85,
                speed_score=0.3,
                requirements={"cpu_cores": 2}
            ),
            
            # 5. Whisper CPU (fallback universel)
            FallbackConfig(
                model_type=ModelType.WHISPER_CPU,
                model_name="whisper-base",
                device="cpu",
                max_memory_mb=2048,
                timeout_seconds=480,
                quality_score=0.8,
                speed_score=0.4,
                requirements={}
            ),
            
            # 6. Whisper Tiny (dernier recours)
            FallbackConfig(
                model_type=ModelType.WHISPER_TINY,
                model_name="whisper-tiny",
                device="cpu",
                max_memory_mb=512,
                timeout_seconds=300,
                quality_score=0.6,
                speed_score=0.7,
                requirements={}
            )
        ]
    
    async def execute_with_fallback(self, 
                                  audio_file: str,
                                  transcription_func: Callable,
                                  max_attempts: Optional[int] = None,
                                  preferred_config: Optional[FallbackConfig] = None) -> Tuple[bool, Optional[str], Optional[FallbackConfig]]:
        """
        Exécute la transcription avec fallback automatique
        
        Args:
            audio_file: Chemin vers le fichier audio
            transcription_func: Fonction de transcription à appeler
            max_attempts: Nombre maximum de tentatives (None = toutes)
            preferred_config: Configuration préférée à essayer en premier
            
        Returns:
            Tuple (success, result, used_config)
        """
        operation_id = f"fallback_{int(time.time())}"
        
        # Démarrer le suivi de progression
        progress_tracker = None
        if self.progress_interface:
            progress_tracker = await self.progress_interface.track_operation(
                operation_type="transcription_with_fallback",
                operation_id=operation_id,
                metadata={"audio_file": audio_file}
            )
        
        try:
            # Obtenir les informations système
            system_info = await self._get_system_info()
            
            # Déterminer la chaîne de fallback à utiliser
            fallback_chain = self._get_optimal_fallback_chain(system_info, preferred_config)
            
            if max_attempts:
                fallback_chain = fallback_chain[:max_attempts]
            
            logger.info(f"Starting fallback chain with {len(fallback_chain)} configurations")
            
            # Essayer chaque configuration
            for i, config in enumerate(fallback_chain):
                if progress_tracker:
                    await progress_tracker.update(
                        progress_percent=(i / len(fallback_chain)) * 100,
                        current_step=f"Tentative {i+1}/{len(fallback_chain)}",
                        current_message=f"Essai avec {config.model_type.value}"
                    )
                
                # Vérifier si la configuration est compatible
                if not config.meets_requirements(system_info):
                    logger.info(f"Skipping {config.model_type.value} - requirements not met")
                    continue
                
                # Essayer cette configuration
                success, result, attempt = await self._try_configuration(
                    config, audio_file, transcription_func, progress_tracker
                )
                
                self.attempt_history.append(attempt)
                self._update_stats(attempt)
                
                if success:
                    logger.info(f"Transcription successful with {config.model_type.value}")
                    
                    # Notifier le succès
                    await self._notify_fallback_success(config, attempt, i + 1)
                    
                    if progress_tracker:
                        await self.progress_interface.complete_operation(operation_id, success=True)
                    
                    return True, result, config
                else:
                    logger.warning(f"Transcription failed with {config.model_type.value}: {attempt.error}")
                    
                    # Notifier l'échec et continuer
                    await self._notify_fallback_failure(config, attempt, i + 1, len(fallback_chain))
            
            # Tous les fallbacks ont échoué
            logger.error("All fallback configurations failed")
            
            if progress_tracker:
                await self.progress_interface.complete_operation(operation_id, success=False)
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"Fallback system error: {e}")
            if progress_tracker:
                await self.progress_interface.complete_operation(operation_id, success=False)
            return False, None, None
    
    async def _try_configuration(self, 
                                config: FallbackConfig,
                                audio_file: str,
                                transcription_func: Callable,
                                progress_tracker: Optional[Any] = None) -> Tuple[bool, Optional[str], FallbackAttempt]:
        """Essaie une configuration spécifique"""
        
        attempt = FallbackAttempt(
            config=config,
            start_time=time.time()
        )
        
        try:
            # Mettre à jour la progression
            if progress_tracker:
                await progress_tracker.update(
                    current_message=f"Chargement du modèle {config.model_name}..."
                )
            
            # Appeler la fonction de transcription avec timeout
            result = await asyncio.wait_for(
                transcription_func(audio_file, config),
                timeout=config.timeout_seconds
            )
            
            # Succès
            attempt.end_time = time.time()
            attempt.success = True
            attempt.performance_metrics = {
                "duration": attempt.duration,
                "quality_score": config.quality_score,
                "speed_score": config.speed_score
            }
            
            return True, result, attempt
            
        except asyncio.TimeoutError:
            attempt.end_time = time.time()
            attempt.error = f"Timeout after {config.timeout_seconds}s"
            attempt.reason = FallbackReason.TIMEOUT
            return False, None, attempt
            
        except torch.cuda.OutOfMemoryError:
            attempt.end_time = time.time()
            attempt.error = "CUDA out of memory"
            attempt.reason = FallbackReason.CUDA_ERROR
            return False, None, attempt
            
        except MemoryError:
            attempt.end_time = time.time()
            attempt.error = "System out of memory"
            attempt.reason = FallbackReason.MEMORY_ERROR
            return False, None, attempt
            
        except Exception as e:
            attempt.end_time = time.time()
            attempt.error = str(e)
            attempt.reason = FallbackReason.TRANSCRIPTION_ERROR
            return False, None, attempt
    
    def _get_optimal_fallback_chain(self, 
                                  system_info: Dict[str, Any],
                                  preferred_config: Optional[FallbackConfig] = None) -> List[FallbackConfig]:
        """Détermine la chaîne de fallback optimale selon le système"""
        
        # Filtrer les configurations compatibles
        compatible_configs = [
            config for config in self.fallback_chain
            if config.meets_requirements(system_info)
        ]
        
        # Trier par score de performance (qualité * vitesse)
        compatible_configs.sort(
            key=lambda c: c.quality_score * c.speed_score,
            reverse=True
        )
        
        # Ajouter la configuration préférée en premier si fournie
        if preferred_config and preferred_config.meets_requirements(system_info):
            if preferred_config in compatible_configs:
                compatible_configs.remove(preferred_config)
            compatible_configs.insert(0, preferred_config)
        
        return compatible_configs
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Obtient les informations système avec cache"""
        
        current_time = time.time()
        
        # Utiliser le cache si valide
        if (self._system_info_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._system_info_cache
        
        # Collecter les informations système
        system_info = {
            "available_memory_mb": psutil.virtual_memory().available // (1024 * 1024),
            "total_memory_mb": psutil.virtual_memory().total // (1024 * 1024),
            "cpu_cores": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "cuda_available": torch.cuda.is_available(),
        }
        
        # Informations CUDA si disponible
        if system_info["cuda_available"]:
            try:
                system_info["cuda_memory_mb"] = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
                system_info["cuda_memory_free_mb"] = (torch.cuda.get_device_properties(0).total_memory - 
                                                    torch.cuda.memory_allocated(0)) // (1024 * 1024)
            except Exception as e:
                logger.warning(f"Failed to get CUDA info: {e}")
                system_info["cuda_memory_mb"] = 0
                system_info["cuda_memory_free_mb"] = 0
        else:
            system_info["cuda_memory_mb"] = 0
            system_info["cuda_memory_free_mb"] = 0
        
        # Mettre en cache
        self._system_info_cache = system_info
        self._cache_timestamp = current_time
        
        return system_info
    
    async def _notify_fallback_success(self, config: FallbackConfig, attempt: FallbackAttempt, attempt_number: int):
        """Notifie le succès d'un fallback"""
        message = f"Transcription réussie avec {config.model_type.value} (tentative {attempt_number})"
        
        if attempt_number > 1:
            message += f" après {attempt_number-1} échec(s)"
        
        notification_data = {
            "type": "fallback_success",
            "config": config,
            "attempt": attempt,
            "attempt_number": attempt_number,
            "message": message
        }
        
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification_data)
                else:
                    callback(notification_data)
            except Exception as e:
                logger.warning(f"Notification callback error: {e}")
    
    async def _notify_fallback_failure(self, config: FallbackConfig, attempt: FallbackAttempt, 
                                     attempt_number: int, total_attempts: int):
        """Notifie l'échec d'un fallback"""
        message = f"Échec avec {config.model_type.value} (tentative {attempt_number}/{total_attempts}): {attempt.error}"
        
        notification_data = {
            "type": "fallback_failure",
            "config": config,
            "attempt": attempt,
            "attempt_number": attempt_number,
            "total_attempts": total_attempts,
            "message": message
        }
        
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification_data)
                else:
                    callback(notification_data)
            except Exception as e:
                logger.warning(f"Notification callback error: {e}")
    
    def _update_stats(self, attempt: FallbackAttempt):
        """Met à jour les statistiques"""
        self.stats["total_attempts"] += 1
        
        if attempt.success:
            self.stats["successful_attempts"] += 1
        
        # Statistiques par type de modèle
        model_type = attempt.config.model_type.value
        if model_type not in self.stats["fallback_usage"]:
            self.stats["fallback_usage"][model_type] = {"attempts": 0, "successes": 0}
        
        self.stats["fallback_usage"][model_type]["attempts"] += 1
        if attempt.success:
            self.stats["fallback_usage"][model_type]["successes"] += 1
        
        # Erreurs communes
        if attempt.error:
            error_key = attempt.reason.value if attempt.reason else "unknown"
            self.stats["common_errors"][error_key] = self.stats["common_errors"].get(error_key, 0) + 1
        
        # Temps moyen de fallback
        if self.stats["total_attempts"] > 0:
            total_time = sum(a.duration for a in self.attempt_history)
            self.stats["average_fallback_time"] = total_time / self.stats["total_attempts"]
    
    # Méthodes spécifiques pour chaque type de modèle
    async def try_nemo_light(self, audio_file: str) -> Tuple[bool, Optional[str]]:
        """Essaie spécifiquement NeMo Light"""
        config = next((c for c in self.fallback_chain if c.model_type == ModelType.NEMO_LIGHT), None)
        if not config:
            return False, None
        
        # Fonction de transcription simulée pour NeMo Light
        async def nemo_light_transcription(audio_file: str, config: FallbackConfig) -> str:
            # Simulation - remplacer par l'appel réel à NeMo
            await asyncio.sleep(0.1)  # Simulation du temps de traitement
            return f"Transcription NeMo Light de {audio_file}"
        
        success, result, _ = await self._try_configuration(config, audio_file, nemo_light_transcription)
        return success, result
    
    async def try_nemo_cpu(self, audio_file: str) -> Tuple[bool, Optional[str]]:
        """Essaie spécifiquement NeMo CPU"""
        config = next((c for c in self.fallback_chain if c.model_type == ModelType.NEMO_CPU), None)
        if not config:
            return False, None
        
        async def nemo_cpu_transcription(audio_file: str, config: FallbackConfig) -> str:
            await asyncio.sleep(0.2)  # Simulation plus lente pour CPU
            return f"Transcription NeMo CPU de {audio_file}"
        
        success, result, _ = await self._try_configuration(config, audio_file, nemo_cpu_transcription)
        return success, result
    
    async def try_whisper(self, audio_file: str, model_size: str = "base") -> Tuple[bool, Optional[str]]:
        """Essaie spécifiquement Whisper"""
        model_type = ModelType.WHISPER_GPU if torch.cuda.is_available() else ModelType.WHISPER_CPU
        if model_size == "tiny":
            model_type = ModelType.WHISPER_TINY
        
        config = next((c for c in self.fallback_chain if c.model_type == model_type), None)
        if not config:
            return False, None
        
        async def whisper_transcription(audio_file: str, config: FallbackConfig) -> str:
            await asyncio.sleep(0.15)
            return f"Transcription Whisper {model_size} de {audio_file}"
        
        success, result, _ = await self._try_configuration(config, audio_file, whisper_transcription)
        return success, result
    
    def add_notification_callback(self, callback: Callable):
        """Ajoute un callback de notification"""
        self.notification_callbacks.append(callback)
    
    def remove_notification_callback(self, callback: Callable):
        """Supprime un callback de notification"""
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système de fallback"""
        return self.stats.copy()
    
    def get_attempt_history(self) -> List[FallbackAttempt]:
        """Retourne l'historique des tentatives"""
        return self.attempt_history.copy()
    
    async def get_recommended_config(self) -> Optional[FallbackConfig]:
        """Retourne la configuration recommandée selon le système actuel"""
        try:
            system_info = await self._get_system_info()
            optimal_chain = self._get_optimal_fallback_chain(system_info)
            return optimal_chain[0] if optimal_chain else None
        except Exception as e:
            logger.error(f"Failed to get recommended config: {e}")
            return None
    
    def clear_history(self):
        """Efface l'historique des tentatives"""
        self.attempt_history.clear()
        self.stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "fallback_usage": {},
            "common_errors": {},
            "average_fallback_time": 0.0
        }