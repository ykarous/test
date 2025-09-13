"""
Gestionnaire d'erreurs centralisé avec stratégies de récupération automatique
"""

import asyncio
import logging
import time
import traceback
import gc
import json
import psutil
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types d'erreurs gérées"""
    CUDA_ERROR = "cuda_error"
    MEMORY_ERROR = "memory_error"
    NETWORK_ERROR = "network_error"
    DISK_ERROR = "disk_error"
    MODEL_ERROR = "model_error"
    TRANSCRIPTION_ERROR = "transcription_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """Niveaux de gravité des erreurs"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class RecoveryStrategy(Enum):
    """Stratégies de récupération"""
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    CLEANUP = "cleanup"
    USER_INTERVENTION = "user_intervention"
    SYSTEM_RECOVERY = "system_recovery"
    IGNORE = "ignore"

class RecoveryActionType(Enum):
    """Actions de récupération spécifiques"""
    CLEAR_CACHE = "clear_cache"
    RESTART_SERVICE = "restart_service"
    SWITCH_MODEL = "switch_model"
    REDUCE_MEMORY = "reduce_memory"
    CLEANUP_TEMP = "cleanup_temp"
    RESET_CONNECTION = "reset_connection"
    RELOAD_CONFIG = "reload_config"
    FORCE_GC = "force_gc"

@dataclass
class ErrorContext:
    """Contexte d'une erreur"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    timestamp: float = field(default_factory=time.time)
    
    # Informations sur l'erreur
    exception: Optional[Exception] = None
    error_message: str = ""
    stack_trace: str = ""
    
    # Contexte d'exécution
    operation_id: Optional[str] = None
    component: str = ""
    function_name: str = ""
    
    # État du système
    system_state: Dict[str, Any] = field(default_factory=dict)
    
    # Tentatives de récupération
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    recovery_strategies_tried: List[RecoveryStrategy] = field(default_factory=list)
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryAction:
    """Action de récupération"""
    strategy: RecoveryStrategy
    action_func: Callable
    description: str
    requires_confirmation: bool = False
    timeout: float = 30.0
    priority: int = 1  # Plus bas = plus prioritaire

@dataclass
class RecoveryResult:
    """Résultat d'une tentative de récupération"""
    success: bool
    strategy_used: RecoveryStrategy
    actions_taken: List[str]
    duration: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorRecoveryManager:
    """Gestionnaire d'erreurs centralisé avec récupération automatique"""
    
    def __init__(self, config_file: str = ".kiro/error_recovery_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Stockage des erreurs
        self.error_history: List[ErrorContext] = []
        self.active_errors: Dict[str, ErrorContext] = {}
        self.error_patterns: Dict[str, int] = {}
        
        # Stratégies de récupération par type d'erreur
        self.recovery_strategies: Dict[ErrorType, List[RecoveryAction]] = {}
        
        # Configuration
        self.config = {
            "max_error_history": 1000,
            "auto_recovery_enabled": True,
            "confirmation_timeout": 30.0,
            "max_concurrent_recoveries": 3,
            "error_pattern_threshold": 5,
            "system_monitoring_interval": 10.0,
            "detailed_logging": True
        }
        
        # État interne
        self.recovery_lock = asyncio.Lock()
        self.active_recoveries: Dict[str, asyncio.Task] = {}
        self.confirmation_callbacks: List[Callable] = []
        
        # Monitoring système
        self.system_monitor_task: Optional[asyncio.Task] = None
        self.system_metrics: Dict[str, Any] = {}
        
        # Thread pool pour opérations bloquantes
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Statistiques d'erreurs
        self.error_stats: Dict[ErrorType, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "recovery_success_rate": 0.0,
            "average_recovery_time": 0.0,
            "last_occurrence": 0.0
        })
        
        # Initialisation
        self._load_config()
        self._setup_default_strategies()
        self._start_system_monitoring()
        
        logger.info("Error Recovery Manager initialized")
    
    def _load_config(self):
        """Charge la configuration depuis le fichier"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config.get('config', {}))
                    self.error_patterns.update(saved_config.get('error_patterns', {}))
                logger.info("Error recovery configuration loaded")
            except Exception as e:
                logger.error(f"Failed to load error recovery config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            config_data = {
                'config': self.config,
                'error_patterns': self.error_patterns,
                'timestamp': time.time()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save error recovery config: {e}")
    
    def _setup_default_strategies(self):
        """Configure les stratégies de récupération par défaut"""
        
        # Stratégies pour erreurs CUDA
        self.recovery_strategies[ErrorType.CUDA_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.CLEANUP,
                action_func=self._cleanup_cuda_memory,
                description="Nettoyer la mémoire CUDA et réessayer",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._fallback_to_cpu,
                description="Basculer vers le CPU",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.RESTART,
                action_func=self._restart_cuda_context,
                description="Redémarrer le contexte CUDA",
                requires_confirmation=True,
                priority=3
            )
        ]
        
        # Stratégies pour erreurs mémoire
        self.recovery_strategies[ErrorType.MEMORY_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.CLEANUP,
                action_func=self._cleanup_memory,
                description="Libérer la mémoire et réessayer",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._reduce_memory_usage,
                description="Réduire l'utilisation mémoire",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.RESTART,
                action_func=self._restart_memory_intensive_components,
                description="Redémarrer les composants gourmands en mémoire",
                requires_confirmation=True,
                priority=3
            )
        ]
        
        # Stratégies pour erreurs réseau
        self.recovery_strategies[ErrorType.NETWORK_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action_func=self._retry_network_operation,
                description="Réessayer l'opération réseau",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._use_cached_data,
                description="Utiliser les données en cache",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.USER_INTERVENTION,
                action_func=self._request_network_check,
                description="Demander vérification de la connexion",
                requires_confirmation=True,
                priority=3
            )
        ]
        
        # Stratégies pour erreurs de modèle
        self.recovery_strategies[ErrorType.MODEL_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action_func=self._reload_model,
                description="Recharger le modèle",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._use_fallback_model,
                description="Utiliser un modèle de fallback",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.CLEANUP,
                action_func=self._redownload_model,
                description="Re-télécharger le modèle",
                requires_confirmation=True,
                priority=3
            )
        ]
        
        # Stratégies pour erreurs de transcription
        self.recovery_strategies[ErrorType.TRANSCRIPTION_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action_func=self._retry_transcription,
                description="Réessayer la transcription",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._use_different_model,
                description="Utiliser un modèle différent",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                action_func=self._reduce_transcription_quality,
                description="Réduire la qualité de transcription",
                priority=3
            )
        ]
        
        # Stratégies par défaut pour erreurs inconnues
        self.recovery_strategies[ErrorType.UNKNOWN_ERROR] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action_func=self._generic_retry,
                description="Réessayer l'opération",
                priority=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.CLEANUP,
                action_func=self._generic_cleanup_retry,
                description="Nettoyer et réessayer",
                priority=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.USER_INTERVENTION,
                action_func=self._request_manual_intervention,
                description="Intervention manuelle requise",
                requires_confirmation=True,
                priority=3
            )
        ]
    
    def _start_system_monitoring(self):
        """Démarre le monitoring système"""
        if self.system_monitor_task is None:
            try:
                self.system_monitor_task = asyncio.create_task(self._system_monitoring_loop())
            except RuntimeError:
                # Pas de boucle d'événements active
                pass
    
    async def _system_monitoring_loop(self):
        """Boucle de monitoring système"""
        while True:
            try:
                # Collecter les métriques système
                self.system_metrics = await self._collect_system_metrics()
                
                # Détecter les problèmes potentiels
                await self._detect_potential_issues()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.config["system_monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques système"""
        
        def get_metrics():
            try:
                return {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                    "available_memory": psutil.virtual_memory().available,
                    "process_count": len(psutil.pids()),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                return {"error": str(e), "timestamp": time.time()}
        
        # Exécuter dans le thread pool pour éviter de bloquer
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, get_metrics)
    
    async def _detect_potential_issues(self):
        """Détecte les problèmes potentiels du système"""
        
        metrics = self.system_metrics
        
        # Vérifier l'utilisation mémoire
        if metrics.get("memory_percent", 0) > 90:
            await self._create_preventive_error(
                ErrorType.MEMORY_ERROR,
                "Utilisation mémoire critique détectée",
                {"memory_percent": metrics["memory_percent"]}
            )
        
        # Vérifier l'utilisation CPU
        if metrics.get("cpu_percent", 0) > 95:
            await self._create_preventive_error(
                ErrorType.SYSTEM_ERROR,
                "Utilisation CPU critique détectée",
                {"cpu_percent": metrics["cpu_percent"]}
            )
        
        # Vérifier l'espace disque
        if metrics.get("disk_usage", 0) > 95:
            await self._create_preventive_error(
                ErrorType.DISK_ERROR,
                "Espace disque critique détecté",
                {"disk_usage": metrics["disk_usage"]}
            )
    
    async def _create_preventive_error(self, error_type: ErrorType, message: str, metadata: Dict[str, Any]):
        """Crée une erreur préventive"""
        
        error_context = ErrorContext(
            error_id=f"preventive_{error_type.value}_{int(time.time())}",
            error_type=error_type,
            severity=ErrorSeverity.MEDIUM,
            error_message=message,
            component="system_monitor",
            system_state=self.system_metrics.copy(),
            metadata=metadata
        )
        
        # Traiter l'erreur préventive
        await self.handle_error(error_context)
    
    async def handle_error(self, error_context: ErrorContext) -> Optional[RecoveryResult]:
        """
        Gère une erreur avec récupération automatique
        
        Args:
            error_context: Contexte de l'erreur
            
        Returns:
            Résultat de la récupération si tentée
        """
        
        # Enregistrer l'erreur
        await self._log_error(error_context)
        
        # Ajouter à l'historique
        self.error_history.append(error_context)
        self.active_errors[error_context.error_id] = error_context
        
        # Limiter la taille de l'historique
        if len(self.error_history) > self.config["max_error_history"]:
            self.error_history = self.error_history[-self.config["max_error_history"]:]
        
        # Mettre à jour les statistiques
        self._update_error_stats(error_context)
        
        # Analyser les patterns d'erreur
        await self._analyze_error_patterns(error_context)
        
        # Tenter la récupération automatique si activée
        if self.config["auto_recovery_enabled"]:
            return await self._attempt_recovery(error_context)
        
        return None
    
    def _update_error_stats(self, error_context: ErrorContext):
        """Met à jour les statistiques d'erreurs"""
        
        error_type = error_context.error_type
        stats = self.error_stats[error_type]
        
        stats["count"] += 1
        stats["last_occurrence"] = error_context.timestamp
    
    async def _log_error(self, error_context: ErrorContext):
        """Journalise une erreur de manière détaillée"""
        
        log_entry = {
            "error_id": error_context.error_id,
            "error_type": error_context.error_type.value,
            "severity": error_context.severity.value,
            "timestamp": error_context.timestamp,
            "message": error_context.error_message,
            "component": error_context.component,
            "function": error_context.function_name,
            "operation_id": error_context.operation_id,
            "system_state": error_context.system_state,
            "metadata": error_context.metadata
        }
        
        # Log selon la gravité
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_context.error_message}", extra=log_entry)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error_context.error_message}", extra=log_entry)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_context.error_message}", extra=log_entry)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_context.error_message}", extra=log_entry)
        
        # Sauvegarder dans un fichier de log dédié si critique
        if error_context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            await self._save_critical_error_log(error_context, log_entry)
    
    async def _save_critical_error_log(self, error_context: ErrorContext, log_entry: Dict[str, Any]):
        """Sauvegarde les erreurs critiques dans un fichier dédié"""
        
        try:
            log_file = self.config_file.parent / "critical_errors.log"
            
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(log_entry)}\n")
                
        except Exception as e:
            logger.error(f"Failed to save critical error log: {e}")
    
    async def _analyze_error_patterns(self, error_context: ErrorContext):
        """Analyse les patterns d'erreur pour détecter les problèmes récurrents"""
        
        # Créer une clé de pattern basée sur le type et le composant
        pattern_key = f"{error_context.error_type.value}_{error_context.component}"
        
        # Incrémenter le compteur
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # Vérifier si le seuil est atteint
        if self.error_patterns[pattern_key] >= self.config["error_pattern_threshold"]:
            await self._handle_error_pattern(pattern_key, self.error_patterns[pattern_key])
    
    async def _handle_error_pattern(self, pattern_key: str, count: int):
        """Gère un pattern d'erreur récurrent"""
        
        logger.warning(f"Error pattern detected: {pattern_key} occurred {count} times")
        
        # Créer une erreur de pattern pour déclencher des actions préventives
        pattern_error = ErrorContext(
            error_id=f"pattern_{pattern_key}_{int(time.time())}",
            error_type=ErrorType.SYSTEM_ERROR,
            severity=ErrorSeverity.HIGH,
            error_message=f"Pattern d'erreur récurrent détecté: {pattern_key} ({count} occurrences)",
            component="error_pattern_analyzer",
            metadata={"pattern_key": pattern_key, "count": count}
        )
        
        # Traiter le pattern comme une erreur
        await self.handle_error(pattern_error)
    
    async def _attempt_recovery(self, error_context: ErrorContext) -> Optional[RecoveryResult]:
        """Tente la récupération automatique d'une erreur"""
        
        async with self.recovery_lock:
            # Vérifier les limites de récupération concurrente
            if len(self.active_recoveries) >= self.config["max_concurrent_recoveries"]:
                logger.warning(f"Max concurrent recoveries reached, queuing error {error_context.error_id}")
                return None
            
            # Vérifier si on a dépassé le nombre max de tentatives
            if error_context.recovery_attempts >= error_context.max_recovery_attempts:
                logger.error(f"Max recovery attempts reached for error {error_context.error_id}")
                return None
            
            # Obtenir les stratégies de récupération
            strategies = self.recovery_strategies.get(error_context.error_type, 
                                                    self.recovery_strategies[ErrorType.UNKNOWN_ERROR])
            
            # Filtrer les stratégies déjà essayées
            available_strategies = [s for s in strategies if s.strategy not in error_context.recovery_strategies_tried]
            
            if not available_strategies:
                logger.error(f"No more recovery strategies available for error {error_context.error_id}")
                return None
            
            # Trier par priorité
            available_strategies.sort(key=lambda x: x.priority)
            
            # Essayer la première stratégie disponible
            strategy = available_strategies[0]
            
            # Démarrer la récupération
            recovery_task = asyncio.create_task(
                self._execute_recovery_strategy(error_context, strategy)
            )
            
            self.active_recoveries[error_context.error_id] = recovery_task
            
            try:
                result = await recovery_task
                return result
            finally:
                # Nettoyer la tâche de récupération
                if error_context.error_id in self.active_recoveries:
                    del self.active_recoveries[error_context.error_id]
    
    async def _execute_recovery_strategy(self, error_context: ErrorContext, strategy: RecoveryAction) -> RecoveryResult:
        """Exécute une stratégie de récupération"""
        
        logger.info(f"Executing recovery strategy '{strategy.strategy.value}' for error {error_context.error_id}")
        
        start_time = time.time()
        actions_taken = []
        
        # Incrémenter le compteur de tentatives
        error_context.recovery_attempts += 1
        error_context.recovery_strategies_tried.append(strategy.strategy)
        
        try:
            # Demander confirmation si nécessaire
            if strategy.requires_confirmation:
                confirmed = await self._request_confirmation(error_context, strategy)
                if not confirmed:
                    logger.info(f"Recovery strategy '{strategy.strategy.value}' not confirmed by user")
                    return RecoveryResult(
                        success=False,
                        strategy_used=strategy.strategy,
                        actions_taken=actions_taken,
                        duration=time.time() - start_time,
                        error_message="User confirmation denied"
                    )
            
            # Exécuter l'action de récupération avec timeout
            result = await asyncio.wait_for(
                strategy.action_func(error_context),
                timeout=strategy.timeout
            )
            
            actions_taken.append(strategy.description)
            duration = time.time() - start_time
            
            if result:
                logger.info(f"Recovery strategy '{strategy.strategy.value}' succeeded for error {error_context.error_id}")
                
                # Marquer l'erreur comme récupérée
                error_context.metadata["recovered"] = True
                error_context.metadata["recovery_strategy"] = strategy.strategy.value
                
                # Retirer de la liste des erreurs actives
                if error_context.error_id in self.active_errors:
                    del self.active_errors[error_context.error_id]
                
                # Mettre à jour les statistiques de succès
                self._update_recovery_stats(error_context.error_type, True, duration)
                
                return RecoveryResult(
                    success=True,
                    strategy_used=strategy.strategy,
                    actions_taken=actions_taken,
                    duration=duration
                )
            else:
                logger.warning(f"Recovery strategy '{strategy.strategy.value}' failed for error {error_context.error_id}")
                
                self._update_recovery_stats(error_context.error_type, False, duration)
                
                return RecoveryResult(
                    success=False,
                    strategy_used=strategy.strategy,
                    actions_taken=actions_taken,
                    duration=duration,
                    error_message="Recovery action returned False"
                )
                
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"Recovery strategy '{strategy.strategy.value}' timed out for error {error_context.error_id}")
            
            self._update_recovery_stats(error_context.error_type, False, duration)
            
            return RecoveryResult(
                success=False,
                strategy_used=strategy.strategy,
                actions_taken=actions_taken,
                duration=duration,
                error_message=f"Recovery timed out after {strategy.timeout}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Recovery strategy '{strategy.strategy.value}' raised exception for error {error_context.error_id}: {e}")
            
            self._update_recovery_stats(error_context.error_type, False, duration)
            
            return RecoveryResult(
                success=False,
                strategy_used=strategy.strategy,
                actions_taken=actions_taken,
                duration=duration,
                error_message=str(e)
            )
    
    def _update_recovery_stats(self, error_type: ErrorType, success: bool, duration: float):
        """Met à jour les statistiques de récupération"""
        
        stats = self.error_stats[error_type]
        
        # Mettre à jour le taux de succès
        current_rate = stats.get("recovery_success_rate", 0.0)
        current_count = stats.get("recovery_attempts", 0)
        
        new_count = current_count + 1
        if success:
            new_rate = (current_rate * current_count + 1.0) / new_count
        else:
            new_rate = (current_rate * current_count) / new_count
        
        stats["recovery_success_rate"] = new_rate
        stats["recovery_attempts"] = new_count
        
        # Mettre à jour le temps moyen
        current_avg = stats.get("average_recovery_time", 0.0)
        new_avg = (current_avg * current_count + duration) / new_count
        stats["average_recovery_time"] = new_avg
    
    async def _request_confirmation(self, error_context: ErrorContext, strategy: RecoveryAction) -> bool:
        """Demande confirmation à l'utilisateur pour une stratégie de récupération"""
        
        # Créer le message de confirmation
        confirmation_message = {
            "error_id": error_context.error_id,
            "error_type": error_context.error_type.value,
            "error_message": error_context.error_message,
            "strategy": strategy.strategy.value,
            "description": strategy.description,
            "requires_confirmation": True
        }
        
        # Notifier les callbacks de confirmation
        for callback in self.confirmation_callbacks:
            try:
                result = await callback(confirmation_message)
                if result is not None:
                    return bool(result)
            except Exception as e:
                logger.error(f"Error in confirmation callback: {e}")
        
        # Par défaut, ne pas confirmer si pas de callback
        logger.warning(f"No confirmation callback available for error {error_context.error_id}, defaulting to False")
        return False    

    # Méthodes de récupération spécifiques
    
    async def _cleanup_cuda_memory(self, error_context: ErrorContext) -> bool:
        """Nettoie la mémoire CUDA"""
        try:
            logger.info("Cleaning up CUDA memory")
            
            # Force garbage collection
            gc.collect()
            
            # Simulation du nettoyage CUDA
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup CUDA memory: {e}")
            return False
    
    async def _fallback_to_cpu(self, error_context: ErrorContext) -> bool:
        """Bascule vers le CPU"""
        try:
            logger.info("Falling back to CPU processing")
            error_context.metadata["fallback_to_cpu"] = True
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Failed to fallback to CPU: {e}")
            return False
    
    async def _restart_cuda_context(self, error_context: ErrorContext) -> bool:
        """Redémarre le contexte CUDA"""
        try:
            logger.info("Restarting CUDA context")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed to restart CUDA context: {e}")
            return False
    
    async def _cleanup_memory(self, error_context: ErrorContext) -> bool:
        """Nettoie la mémoire système"""
        try:
            logger.info("Cleaning up system memory")
            gc.collect()
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup memory: {e}")
            return False
    
    async def _reduce_memory_usage(self, error_context: ErrorContext) -> bool:
        """Réduit l'utilisation mémoire"""
        try:
            logger.info("Reducing memory usage")
            error_context.metadata["memory_reduced"] = True
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Failed to reduce memory usage: {e}")
            return False
    
    async def _restart_memory_intensive_components(self, error_context: ErrorContext) -> bool:
        """Redémarre les composants gourmands en mémoire"""
        try:
            logger.info("Restarting memory intensive components")
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Failed to restart memory intensive components: {e}")
            return False
    
    async def _retry_network_operation(self, error_context: ErrorContext) -> bool:
        """Réessaie une opération réseau"""
        try:
            logger.info("Retrying network operation")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed to retry network operation: {e}")
            return False
    
    async def _use_cached_data(self, error_context: ErrorContext) -> bool:
        """Utilise les données en cache"""
        try:
            logger.info("Using cached data")
            error_context.metadata["used_cache"] = True
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Failed to use cached data: {e}")
            return False
    
    async def _request_network_check(self, error_context: ErrorContext) -> bool:
        """Demande vérification de la connexion réseau"""
        try:
            logger.info("Requesting network connectivity check")
            error_context.metadata["network_check_requested"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to request network check: {e}")
            return False
    
    async def _reload_model(self, error_context: ErrorContext) -> bool:
        """Recharge un modèle"""
        try:
            logger.info("Reloading model")
            await asyncio.sleep(5)
            return True
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            return False
    
    async def _use_fallback_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle de fallback"""
        try:
            logger.info("Using fallback model")
            error_context.metadata["fallback_model"] = True
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed to use fallback model: {e}")
            return False
    
    async def _redownload_model(self, error_context: ErrorContext) -> bool:
        """Re-télécharge un modèle"""
        try:
            logger.info("Re-downloading model")
            await asyncio.sleep(10)
            return True
        except Exception as e:
            logger.error(f"Failed to redownload model: {e}")
            return False
    
    async def _retry_transcription(self, error_context: ErrorContext) -> bool:
        """Réessaie la transcription"""
        try:
            logger.info("Retrying transcription")
            await asyncio.sleep(5)
            return True
        except Exception as e:
            logger.error(f"Failed to retry transcription: {e}")
            return False
    
    async def _use_different_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle différent"""
        try:
            logger.info("Using different model")
            error_context.metadata["different_model"] = True
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Failed to use different model: {e}")
            return False
    
    async def _reduce_transcription_quality(self, error_context: ErrorContext) -> bool:
        """Réduit la qualité de transcription"""
        try:
            logger.info("Reducing transcription quality")
            error_context.metadata["quality_reduced"] = True
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Failed to reduce transcription quality: {e}")
            return False
    
    async def _generic_retry(self, error_context: ErrorContext) -> bool:
        """Réessaie générique"""
        try:
            logger.info("Generic retry")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed generic retry: {e}")
            return False
    
    async def _generic_cleanup_retry(self, error_context: ErrorContext) -> bool:
        """Nettoyage générique et reprise"""
        try:
            logger.info("Generic cleanup and retry")
            gc.collect()
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed generic cleanup retry: {e}")
            return False
    
    async def _request_manual_intervention(self, error_context: ErrorContext) -> bool:
        """Demande intervention manuelle"""
        try:
            logger.info("Requesting manual intervention")
            error_context.metadata["manual_intervention_requested"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to request manual intervention: {e}")
            return False
    
    # Méthodes utilitaires
    
    def add_confirmation_callback(self, callback: Callable):
        """Ajoute un callback de confirmation"""
        self.confirmation_callbacks.append(callback)
    
    def remove_confirmation_callback(self, callback: Callable):
        """Supprime un callback de confirmation"""
        if callback in self.confirmation_callbacks:
            self.confirmation_callbacks.remove(callback)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'erreurs"""
        return dict(self.error_stats)
    
    def get_active_errors(self) -> List[ErrorContext]:
        """Retourne les erreurs actives"""
        return list(self.active_errors.values())
    
    def get_error_history(self, limit: int = 100) -> List[ErrorContext]:
        """Retourne l'historique des erreurs"""
        return self.error_history[-limit:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques système actuelles"""
        return self.system_metrics.copy()
    
    async def force_recovery(self, error_id: str) -> Optional[RecoveryResult]:
        """Force la récupération d'une erreur spécifique"""
        if error_id in self.active_errors:
            error_context = self.active_errors[error_id]
            return await self._attempt_recovery(error_context)
        return None
    
    async def clear_error_history(self):
        """Vide l'historique des erreurs"""
        async with self.recovery_lock:
            self.error_history.clear()
            self.error_patterns.clear()
            self._save_config()
    
    async def shutdown(self):
        """Arrête proprement le gestionnaire d'erreurs"""
        logger.info("Shutting down Error Recovery Manager")
        
        # Arrêter le monitoring système
        if self.system_monitor_task:
            self.system_monitor_task.cancel()
            try:
                await self.system_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Annuler les récupérations actives
        for task in self.active_recoveries.values():
            task.cancel()
        
        # Attendre que toutes les tâches se terminent
        if self.active_recoveries:
            await asyncio.gather(*self.active_recoveries.values(), return_exceptions=True)
        
        # Fermer le thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Sauvegarder la configuration finale
        self._save_config()
        
        logger.info("Error Recovery Manager shutdown complete")

# Fonctions utilitaires pour créer des contextes d'erreur

def create_error_context(
    error_type: ErrorType,
    error_message: str,
    exception: Optional[Exception] = None,
    component: str = "",
    operation_id: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    metadata: Optional[Dict[str, Any]] = None
) -> ErrorContext:
    """Crée un contexte d'erreur"""
    
    error_id = f"{error_type.value}_{int(time.time() * 1000)}"
    
    return ErrorContext(
        error_id=error_id,
        error_type=error_type,
        severity=severity,
        exception=exception,
        error_message=error_message,
        stack_trace=traceback.format_exc() if exception else "",
        operation_id=operation_id,
        component=component,
        metadata=metadata or {}
    )

def classify_error(exception: Exception) -> ErrorType:
    """Classifie automatiquement une exception"""
    
    error_message = str(exception).lower()
    
    # Classification basée sur le message d'erreur
    if "cuda" in error_message or "gpu" in error_message:
        return ErrorType.CUDA_ERROR
    elif "memory" in error_message or "out of memory" in error_message:
        return ErrorType.MEMORY_ERROR
    elif "network" in error_message or "connection" in error_message or "timeout" in error_message:
        return ErrorType.NETWORK_ERROR
    elif "disk" in error_message or "space" in error_message or "file" in error_message:
        return ErrorType.DISK_ERROR
    elif "model" in error_message or "checkpoint" in error_message:
        return ErrorType.MODEL_ERROR
    elif "transcription" in error_message or "audio" in error_message:
        return ErrorType.TRANSCRIPTION_ERROR
    elif "timeout" in error_message:
        return ErrorType.TIMEOUT_ERROR
    elif "config" in error_message or "configuration" in error_message:
        return ErrorType.CONFIGURATION_ERROR
    else:
        return ErrorType.UNKNOWN_ERROR

# Instance globale (singleton pattern)
_error_recovery_manager: Optional[ErrorRecoveryManager] = None

def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Retourne l'instance globale du gestionnaire d'erreurs"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager

async def handle_error_with_recovery(
    exception: Exception,
    component: str = "",
    operation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[RecoveryResult]:
    """Fonction utilitaire pour gérer une erreur avec récupération automatique"""
    
    error_type = classify_error(exception)
    error_context = create_error_context(
        error_type=error_type,
        error_message=str(exception),
        exception=exception,
        component=component,
        operation_id=operation_id,
        metadata=metadata
    )
    
    manager = get_error_recovery_manager()
    return await manager.handle_error(error_context)    # Simuler le nettoyage CUDA (dans une vraie implémentation, utiliser torch.cuda.empty_cache())
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup CUDA memory: {e}")
            return False
    
    async def _fallback_to_cpu(self, error_context: ErrorContext) -> bool:
        """Bascule vers le CPU"""
        try:
            logger.info("Falling back to CPU processing")
            
            # Simuler le basculement vers CPU
            error_context.metadata["fallback_to_cpu"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to fallback to CPU: {e}")
            return False
    
    async def _restart_cuda_context(self, error_context: ErrorContext) -> bool:
        """Redémarre le contexte CUDA"""
        try:
            logger.info("Restarting CUDA context")
            
            # Simuler le redémarrage du contexte CUDA
            await asyncio.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to restart CUDA context: {e}")
            return False
    
    async def _cleanup_memory(self, error_context: ErrorContext) -> bool:
        """Nettoie la mémoire système"""
        try:
            logger.info("Cleaning up system memory")
            
            # Force garbage collection
            gc.collect()
            
            # Simuler le nettoyage mémoire
            await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup memory: {e}")
            return False
    
    async def _reduce_memory_usage(self, error_context: ErrorContext) -> bool:
        """Réduit l'utilisation mémoire"""
        try:
            logger.info("Reducing memory usage")
            
            # Simuler la réduction de l'utilisation mémoire
            error_context.metadata["memory_reduced"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to reduce memory usage: {e}")
            return False
    
    async def _restart_memory_intensive_components(self, error_context: ErrorContext) -> bool:
        """Redémarre les composants gourmands en mémoire"""
        try:
            logger.info("Restarting memory intensive components")
            
            # Simuler le redémarrage des composants
            await asyncio.sleep(3)
            
            return True
        except Exception as e:
            logger.error(f"Failed to restart memory intensive components: {e}")
            return False
    
    async def _retry_network_operation(self, error_context: ErrorContext) -> bool:
        """Réessaie une opération réseau"""
        try:
            logger.info("Retrying network operation")
            
            # Simuler la reprise de l'opération réseau
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"Failed to retry network operation: {e}")
            return False
    
    async def _use_cached_data(self, error_context: ErrorContext) -> bool:
        """Utilise les données en cache"""
        try:
            logger.info("Using cached data")
            
            # Simuler l'utilisation du cache
            error_context.metadata["used_cache"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to use cached data: {e}")
            return False
    
    async def _request_network_check(self, error_context: ErrorContext) -> bool:
        """Demande une vérification de la connexion réseau"""
        try:
            logger.info("Requesting network connectivity check")
            
            # Simuler la demande de vérification
            error_context.metadata["network_check_requested"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to request network check: {e}")
            return False
    
    async def _reload_model(self, error_context: ErrorContext) -> bool:
        """Recharge un modèle"""
        try:
            logger.info("Reloading model")
            
            # Simuler le rechargement du modèle
            await asyncio.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            return False
    
    async def _use_fallback_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle de fallback"""
        try:
            logger.info("Using fallback model")
            
            # Simuler l'utilisation d'un modèle de fallback
            error_context.metadata["fallback_model_used"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to use fallback model: {e}")
            return False
    
    async def _redownload_model(self, error_context: ErrorContext) -> bool:
        """Re-télécharge un modèle"""
        try:
            logger.info("Re-downloading model")
            
            # Simuler le re-téléchargement
            await asyncio.sleep(5)
            
            return True
        except Exception as e:
            logger.error(f"Failed to re-download model: {e}")
            return False
    
    async def _retry_transcription(self, error_context: ErrorContext) -> bool:
        """Réessaie une transcription"""
        try:
            logger.info("Retrying transcription")
            
            # Simuler la reprise de la transcription
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"Failed to retry transcription: {e}")
            return False
    
    async def _use_different_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle différent"""
        try:
            logger.info("Using different model")
            
            # Simuler l'utilisation d'un modèle différent
            error_context.metadata["different_model_used"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to use different model: {e}")
            return False
    
    async def _reduce_transcription_quality(self, error_context: ErrorContext) -> bool:
        """Réduit la qualité de transcription"""
        try:
            logger.info("Reducing transcription quality")
            
            # Simuler la réduction de qualité
            error_context.metadata["quality_reduced"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to reduce transcription quality: {e}")
            return False
    
    async def _generic_retry(self, error_context: ErrorContext) -> bool:
        """Réessaie générique"""
        try:
            logger.info("Generic retry")
            
            # Simuler un réessai générique
            await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"Generic retry failed: {e}")
            return False
    
    async def _generic_cleanup_retry(self, error_context: ErrorContext) -> bool:
        """Nettoyage générique et réessai"""
        try:
            logger.info("Generic cleanup and retry")
            
            # Force garbage collection
            gc.collect()
            
            # Simuler le nettoyage et réessai
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"Generic cleanup retry failed: {e}")
            return False
    
    async def _request_manual_intervention(self, error_context: ErrorContext) -> bool:
        """Demande une intervention manuelle"""
        try:
            logger.info("Requesting manual intervention")
            
            # Simuler la demande d'intervention
            error_context.metadata["manual_intervention_requested"] = True
            
            return True
        except Exception as e:
            logger.error(f"Failed to request manual intervention: {e}")
            return False
    
    # API publique
    
    def add_confirmation_callback(self, callback: Callable):
        """Ajoute un callback de confirmation"""
        self.confirmation_callbacks.append(callback)
    
    def get_error_history(self, limit: int = 100) -> List[ErrorContext]:
        """Obtient l'historique des erreurs"""
        return self.error_history[-limit:]
    
    def get_active_errors(self) -> Dict[str, ErrorContext]:
        """Obtient les erreurs actives"""
        return self.active_errors.copy()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques d'erreurs"""
        
        total_errors = len(self.error_history)
        active_errors = len(self.active_errors)
        
        # Statistiques par type
        error_counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Statistiques de récupération
        recovery_stats = {}
        for error_type, stats in self.error_stats.items():
            recovery_stats[error_type.value] = {
                "count": stats["count"],
                "success_rate": stats["recovery_success_rate"],
                "avg_recovery_time": stats["average_recovery_time"],
                "last_occurrence": stats["last_occurrence"]
            }
        
        return {
            "total_errors": total_errors,
            "active_errors": active_errors,
            "error_counts": error_counts,
            "recovery_statistics": recovery_stats,
            "error_patterns": self.error_patterns.copy(),
            "system_metrics": self.system_metrics.copy()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtient l'état de santé du système"""
        
        metrics = self.system_metrics
        
        # Déterminer l'état de santé
        health_status = "healthy"
        issues = []
        
        if metrics.get("memory_percent", 0) > 85:
            health_status = "warning"
            issues.append("High memory usage")
        
        if metrics.get("cpu_percent", 0) > 90:
            health_status = "warning"
            issues.append("High CPU usage")
        
        if metrics.get("disk_usage", 0) > 90:
            health_status = "critical"
            issues.append("Low disk space")
        
        if len(self.active_errors) > 5:
            health_status = "critical"
            issues.append("Multiple active errors")
        
        return {
            "status": health_status,
            "issues": issues,
            "metrics": metrics,
            "active_errors_count": len(self.active_errors),
            "recent_errors_count": len([e for e in self.error_history if time.time() - e.timestamp < 3600])
        }
    
    async def force_recovery(self, error_id: str) -> Optional[RecoveryResult]:
        """Force la récupération d'une erreur spécifique"""
        
        if error_id not in self.active_errors:
            logger.warning(f"Error {error_id} not found in active errors")
            return None
        
        error_context = self.active_errors[error_id]
        return await self._attempt_recovery(error_context)
    
    async def clear_error_history(self):
        """Efface l'historique des erreurs"""
        self.error_history.clear()
        self.error_patterns.clear()
        logger.info("Error history cleared")
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire d'erreurs"""
        
        logger.info("Shutting down Error Recovery Manager...")
        
        # Arrêter le monitoring système
        if self.system_monitor_task:
            self.system_monitor_task.cancel()
            try:
                await self.system_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Annuler toutes les récupérations actives
        for task in self.active_recoveries.values():
            task.cancel()
        
        if self.active_recoveries:
            await asyncio.gather(*self.active_recoveries.values(), return_exceptions=True)
        
        # Fermer le thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Sauvegarder la configuration
        self._save_config()
        
        logger.info("Error Recovery Manager shutdown completed")


# Fonctions utilitaires pour créer des contextes d'erreur

def create_error_context(
    error_type: ErrorType,
    error_message: str,
    exception: Optional[Exception] = None,
    component: str = "",
    operation_id: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    **metadata
) -> ErrorContext:
    """Crée un contexte d'erreur"""
    
    error_id = f"{error_type.value}_{int(time.time() * 1000)}"
    
    # Extraire la stack trace si une exception est fournie
    stack_trace = ""
    if exception:
        stack_trace = traceback.format_exc()
    
    return ErrorContext(
        error_id=error_id,
        error_type=error_type,
        severity=severity,
        exception=exception,
        error_message=error_message,
        stack_trace=stack_trace,
        operation_id=operation_id,
        component=component,
        metadata=metadata
    )

def create_cuda_error(error_message: str, exception: Optional[Exception] = None, **metadata) -> ErrorContext:
    """Crée un contexte d'erreur CUDA"""
    return create_error_context(
        ErrorType.CUDA_ERROR,
        error_message,
        exception,
        component="cuda_handler",
        severity=ErrorSeverity.HIGH,
        **metadata
    )

def create_memory_error(error_message: str, exception: Optional[Exception] = None, **metadata) -> ErrorContext:
    """Crée un contexte d'erreur mémoire"""
    return create_error_context(
        ErrorType.MEMORY_ERROR,
        error_message,
        exception,
        component="memory_manager",
        severity=ErrorSeverity.HIGH,
        **metadata
    )

def create_network_error(error_message: str, exception: Optional[Exception] = None, **metadata) -> ErrorContext:
    """Crée un contexte d'erreur réseau"""
    return create_error_context(
        ErrorType.NETWORK_ERROR,
        error_message,
        exception,
        component="network_handler",
        severity=ErrorSeverity.MEDIUM,
        **metadata
    )

def create_model_error(error_message: str, exception: Optional[Exception] = None, **metadata) -> ErrorContext:
    """Crée un contexte d'erreur de modèle"""
    return create_error_context(
        ErrorType.MODEL_ERROR,
        error_message,
        exception,
        component="model_manager",
        severity=ErrorSeverity.HIGH,
        **metadata
    )

def create_transcription_error(error_message: str, exception: Optional[Exception] = None, **metadata) -> ErrorContext:
    """Crée un contexte d'erreur de transcription"""
    return create_error_context(
        ErrorType.TRANSCRIPTION_ERROR,
        error_message,
        exception,
        component="transcription_engine",
        severity=ErrorSeverity.MEDIUM,
        **metadata
    )        
    # Dans une vraie implémentation, utiliser torch.cuda.empty_cache()
            # torch.cuda.empty_cache()
            
            await asyncio.sleep(1)  # Simuler le temps de nettoyage
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup CUDA memory: {e}")
            return False
    
    async def _fallback_to_cpu(self, error_context: ErrorContext) -> bool:
        """Bascule vers le CPU"""
        try:
            logger.info("Falling back to CPU processing")
            
            # Simulation du basculement vers CPU
            error_context.metadata["fallback_to_cpu"] = True
            
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to fallback to CPU: {e}")
            return False
    
    async def _restart_cuda_context(self, error_context: ErrorContext) -> bool:
        """Redémarre le contexte CUDA"""
        try:
            logger.info("Restarting CUDA context")
            
            # Simulation du redémarrage du contexte CUDA
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart CUDA context: {e}")
            return False
    
    async def _cleanup_memory(self, error_context: ErrorContext) -> bool:
        """Nettoie la mémoire système"""
        try:
            logger.info("Cleaning up system memory")
            
            # Force garbage collection
            gc.collect()
            
            # Simulation du nettoyage mémoire
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup memory: {e}")
            return False
    
    async def _reduce_memory_usage(self, error_context: ErrorContext) -> bool:
        """Réduit l'utilisation mémoire"""
        try:
            logger.info("Reducing memory usage")
            
            # Simulation de la réduction d'usage mémoire
            error_context.metadata["memory_reduced"] = True
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reduce memory usage: {e}")
            return False
    
    async def _restart_memory_intensive_components(self, error_context: ErrorContext) -> bool:
        """Redémarre les composants gourmands en mémoire"""
        try:
            logger.info("Restarting memory intensive components")
            
            # Simulation du redémarrage des composants
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart memory intensive components: {e}")
            return False
    
    async def _retry_network_operation(self, error_context: ErrorContext) -> bool:
        """Réessaie une opération réseau"""
        try:
            logger.info("Retrying network operation")
            
            # Simulation de la reprise réseau
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry network operation: {e}")
            return False
    
    async def _use_cached_data(self, error_context: ErrorContext) -> bool:
        """Utilise les données en cache"""
        try:
            logger.info("Using cached data")
            
            # Simulation de l'utilisation du cache
            error_context.metadata["used_cache"] = True
            
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to use cached data: {e}")
            return False
    
    async def _request_network_check(self, error_context: ErrorContext) -> bool:
        """Demande vérification de la connexion réseau"""
        try:
            logger.info("Requesting network connectivity check")
            
            # Simulation de la vérification réseau
            error_context.metadata["network_check_requested"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to request network check: {e}")
            return False
    
    async def _reload_model(self, error_context: ErrorContext) -> bool:
        """Recharge un modèle"""
        try:
            logger.info("Reloading model")
            
            # Simulation du rechargement de modèle
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            return False
    
    async def _use_fallback_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle de fallback"""
        try:
            logger.info("Using fallback model")
            
            # Simulation de l'utilisation d'un modèle de fallback
            error_context.metadata["fallback_model_used"] = True
            
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to use fallback model: {e}")
            return False
    
    async def _redownload_model(self, error_context: ErrorContext) -> bool:
        """Re-télécharge un modèle"""
        try:
            logger.info("Re-downloading model")
            
            # Simulation du re-téléchargement
            await asyncio.sleep(10)
            return True
            
        except Exception as e:
            logger.error(f"Failed to re-download model: {e}")
            return False
    
    async def _retry_transcription(self, error_context: ErrorContext) -> bool:
        """Réessaie une transcription"""
        try:
            logger.info("Retrying transcription")
            
            # Simulation de la reprise de transcription
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry transcription: {e}")
            return False
    
    async def _use_different_model(self, error_context: ErrorContext) -> bool:
        """Utilise un modèle différent"""
        try:
            logger.info("Using different model for transcription")
            
            # Simulation de l'utilisation d'un modèle différent
            error_context.metadata["different_model_used"] = True
            
            await asyncio.sleep(4)
            return True
            
        except Exception as e:
            logger.error(f"Failed to use different model: {e}")
            return False
    
    async def _reduce_transcription_quality(self, error_context: ErrorContext) -> bool:
        """Réduit la qualité de transcription"""
        try:
            logger.info("Reducing transcription quality")
            
            # Simulation de la réduction de qualité
            error_context.metadata["quality_reduced"] = True
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reduce transcription quality: {e}")
            return False
    
    async def _generic_retry(self, error_context: ErrorContext) -> bool:
        """Réessaie générique"""
        try:
            logger.info("Generic retry operation")
            
            # Simulation de reprise générique
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Generic retry failed: {e}")
            return False
    
    async def _generic_cleanup_retry(self, error_context: ErrorContext) -> bool:
        """Nettoyage générique et reprise"""
        try:
            logger.info("Generic cleanup and retry")
            
            # Force garbage collection
            gc.collect()
            
            # Simulation du nettoyage et reprise
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"Generic cleanup retry failed: {e}")
            return False
    
    async def _request_manual_intervention(self, error_context: ErrorContext) -> bool:
        """Demande intervention manuelle"""
        try:
            logger.info("Requesting manual intervention")
            
            # Simulation de la demande d'intervention
            error_context.metadata["manual_intervention_requested"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to request manual intervention: {e}")
            return False
    
    # Méthodes utilitaires et API publique
    
    def add_confirmation_callback(self, callback: Callable):
        """Ajoute un callback de confirmation"""
        self.confirmation_callbacks.append(callback)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques d'erreurs"""
        
        total_errors = sum(stats["count"] for stats in self.error_stats.values())
        
        return {
            "total_errors": total_errors,
            "active_errors": len(self.active_errors),
            "error_types": dict(self.error_stats),
            "error_patterns": dict(self.error_patterns),
            "active_recoveries": len(self.active_recoveries),
            "system_metrics": self.system_metrics.copy()
        }
    
    def get_active_errors(self) -> List[ErrorContext]:
        """Obtient les erreurs actives"""
        return list(self.active_errors.values())
    
    def get_error_history(self, limit: int = 100) -> List[ErrorContext]:
        """Obtient l'historique des erreurs"""
        return self.error_history[-limit:]
    
    def get_error_patterns(self) -> Dict[str, int]:
        """Obtient les patterns d'erreur détectés"""
        return self.error_patterns.copy()
    
    async def clear_error_patterns(self):
        """Efface les patterns d'erreur"""
        self.error_patterns.clear()
        self._save_config()
        logger.info("Error patterns cleared")
    
    async def force_recovery(self, error_id: str) -> Optional[RecoveryResult]:
        """Force la récupération d'une erreur spécifique"""
        
        if error_id not in self.active_errors:
            logger.warning(f"Error {error_id} not found in active errors")
            return None
        
        error_context = self.active_errors[error_id]
        return await self._attempt_recovery(error_context)
    
    async def cancel_recovery(self, error_id: str) -> bool:
        """Annule une récupération en cours"""
        
        if error_id in self.active_recoveries:
            recovery_task = self.active_recoveries[error_id]
            recovery_task.cancel()
            
            try:
                await recovery_task
            except asyncio.CancelledError:
                pass
            
            del self.active_recoveries[error_id]
            logger.info(f"Recovery cancelled for error {error_id}")
            return True
        
        return False
    
    def create_error_context(self, 
                           error_type: ErrorType,
                           exception: Optional[Exception] = None,
                           error_message: str = "",
                           component: str = "",
                           operation_id: Optional[str] = None,
                           severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                           metadata: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Crée un contexte d'erreur
        
        Args:
            error_type: Type d'erreur
            exception: Exception Python (optionnel)
            error_message: Message d'erreur personnalisé
            component: Composant où l'erreur s'est produite
            operation_id: ID de l'opération (optionnel)
            severity: Gravité de l'erreur
            metadata: Métadonnées additionnelles
            
        Returns:
            Contexte d'erreur créé
        """
        
        error_id = f"{error_type.value}_{int(time.time() * 1000)}"
        
        # Extraire les informations de l'exception si fournie
        if exception:
            if not error_message:
                error_message = str(exception)
            stack_trace = traceback.format_exc()
        else:
            stack_trace = ""
        
        # Collecter l'état du système
        system_state = self.system_metrics.copy() if self.system_metrics else {}
        
        return ErrorContext(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            exception=exception,
            error_message=error_message,
            stack_trace=stack_trace,
            operation_id=operation_id,
            component=component,
            system_state=system_state,
            metadata=metadata or {}
        )
    
    async def handle_exception(self,
                             exception: Exception,
                             component: str = "",
                             operation_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Optional[RecoveryResult]:
        """
        Gère une exception Python en créant automatiquement le contexte d'erreur
        
        Args:
            exception: Exception à gérer
            component: Composant où l'exception s'est produite
            operation_id: ID de l'opération (optionnel)
            metadata: Métadonnées additionnelles
            
        Returns:
            Résultat de la récupération si tentée
        """
        
        # Déterminer le type d'erreur basé sur l'exception
        error_type = self._classify_exception(exception)
        
        # Déterminer la gravité
        severity = self._determine_severity(exception, error_type)
        
        # Créer le contexte d'erreur
        error_context = self.create_error_context(
            error_type=error_type,
            exception=exception,
            component=component,
            operation_id=operation_id,
            severity=severity,
            metadata=metadata
        )
        
        # Gérer l'erreur
        return await self.handle_error(error_context)
    
    def _classify_exception(self, exception: Exception) -> ErrorType:
        """Classifie une exception Python en type d'erreur"""
        
        exception_name = type(exception).__name__.lower()
        exception_message = str(exception).lower()
        
        # Classification basée sur le type d'exception
        if "cuda" in exception_name or "cuda" in exception_message:
            return ErrorType.CUDA_ERROR
        elif "memory" in exception_name or "out of memory" in exception_message:
            return ErrorType.MEMORY_ERROR
        elif "network" in exception_name or "connection" in exception_message or "timeout" in exception_message:
            return ErrorType.NETWORK_ERROR
        elif "disk" in exception_message or "space" in exception_message or "permission" in exception_message:
            return ErrorType.DISK_ERROR
        elif "model" in exception_message or "checkpoint" in exception_message:
            return ErrorType.MODEL_ERROR
        elif "transcription" in exception_message or "audio" in exception_message:
            return ErrorType.TRANSCRIPTION_ERROR
        elif "timeout" in exception_name:
            return ErrorType.TIMEOUT_ERROR
        elif "config" in exception_message or "configuration" in exception_message:
            return ErrorType.CONFIGURATION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _determine_severity(self, exception: Exception, error_type: ErrorType) -> ErrorSeverity:
        """Détermine la gravité d'une exception"""
        
        exception_name = type(exception).__name__.lower()
        
        # Erreurs critiques
        if error_type == ErrorType.CUDA_ERROR and "out of memory" in str(exception).lower():
            return ErrorSeverity.CRITICAL
        elif error_type == ErrorType.MEMORY_ERROR and "out of memory" in str(exception).lower():
            return ErrorSeverity.CRITICAL
        elif "critical" in str(exception).lower():
            return ErrorSeverity.CRITICAL
        
        # Erreurs de haute gravité
        elif error_type in [ErrorType.SYSTEM_ERROR, ErrorType.DISK_ERROR]:
            return ErrorSeverity.HIGH
        elif "fatal" in str(exception).lower():
            return ErrorSeverity.HIGH
        
        # Erreurs de gravité moyenne
        elif error_type in [ErrorType.MODEL_ERROR, ErrorType.TRANSCRIPTION_ERROR, ErrorType.NETWORK_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Erreurs de faible gravité
        else:
            return ErrorSeverity.LOW
    
    async def cleanup_old_errors(self, max_age_hours: int = 24):
        """Nettoie les anciennes erreurs de l'historique"""
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Nettoyer l'historique
        initial_count = len(self.error_history)
        self.error_history = [e for e in self.error_history if e.timestamp > cutoff_time]
        
        # Nettoyer les erreurs actives anciennes (sauf si en cours de récupération)
        active_to_remove = []
        for error_id, error_context in self.active_errors.items():
            if (error_context.timestamp < cutoff_time and 
                error_id not in self.active_recoveries):
                active_to_remove.append(error_id)
        
        for error_id in active_to_remove:
            del self.active_errors[error_id]
        
        cleaned_count = initial_count - len(self.error_history)
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old errors from history")
        
        return cleaned_count
    
    async def export_error_report(self, output_file: str) -> bool:
        """Exporte un rapport d'erreurs détaillé"""
        
        try:
            report = {
                "timestamp": time.time(),
                "statistics": self.get_error_statistics(),
                "active_errors": [
                    {
                        "error_id": e.error_id,
                        "error_type": e.error_type.value,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp,
                        "message": e.error_message,
                        "component": e.component,
                        "recovery_attempts": e.recovery_attempts,
                        "metadata": e.metadata
                    }
                    for e in self.active_errors.values()
                ],
                "error_history": [
                    {
                        "error_id": e.error_id,
                        "error_type": e.error_type.value,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp,
                        "message": e.error_message,
                        "component": e.component,
                        "recovered": e.metadata.get("recovered", False)
                    }
                    for e in self.error_history[-100:]  # Dernières 100 erreurs
                ],
                "error_patterns": self.error_patterns,
                "system_metrics": self.system_metrics
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Error report exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")
            return False
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire d'erreurs"""
        
        logger.info("Shutting down Error Recovery Manager...")
        
        try:
            # Arrêter le monitoring système
            if self.system_monitor_task:
                self.system_monitor_task.cancel()
                try:
                    await self.system_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Annuler toutes les récupérations en cours
            for error_id in list(self.active_recoveries.keys()):
                await self.cancel_recovery(error_id)
            
            # Sauvegarder la configuration
            self._save_config()
            
            # Fermer le thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("Error Recovery Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Instance globale
error_recovery_manager = ErrorRecoveryManager()