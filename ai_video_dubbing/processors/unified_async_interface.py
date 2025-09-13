"""
Interface unifiée pour les opérations asynchrones avec progression
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Types d'opérations supportées"""
    TRANSCRIPTION = "transcription"
    MODEL_DOWNLOAD = "model_download"
    MODEL_VALIDATION = "model_validation"
    CACHE_OPERATION = "cache_operation"
    DIAGNOSTIC = "diagnostic"
    OPTIMIZATION = "optimization"
    CLEANUP = "cleanup"

class OperationStatus(Enum):
    """Statuts d'opération"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OperationProgress:
    """Informations de progression d'une opération"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    progress_percent: float = 0.0
    current_step: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    estimated_duration: float = 0.0
    
    # Métriques détaillées
    bytes_processed: int = 0
    total_bytes: int = 0
    items_processed: int = 0
    total_items: int = 0
    
    # Messages et erreurs
    current_message: str = ""
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def elapsed_time(self) -> float:
        """Temps écoulé depuis le début"""
        return time.time() - self.start_time
    
    @property
    def remaining_time(self) -> float:
        """Temps restant estimé"""
        if self.progress_percent > 0:
            elapsed = self.elapsed_time
            total_estimated = elapsed / (self.progress_percent / 100)
            return max(0, total_estimated - elapsed)
        return self.estimated_duration
    
    @property
    def processing_speed(self) -> float:
        """Vitesse de traitement (bytes/sec ou items/sec)"""
        elapsed = self.elapsed_time
        if elapsed > 0:
            if self.total_bytes > 0:
                return self.bytes_processed / elapsed
            elif self.total_items > 0:
                return self.items_processed / elapsed
        return 0.0
    
    def update(self, **kwargs):
        """Met à jour les informations de progression"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

@dataclass
class OperationResult:
    """Résultat d'une opération"""
    operation_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class UnifiedAsyncInterface:
    """Interface unifiée pour toutes les opérations asynchrones avec progression"""
    
    def __init__(self):
        self.active_operations: Dict[str, OperationProgress] = {}
        self.operation_history: List[OperationProgress] = []
        self.operation_lock = asyncio.Lock()
        
        # Callbacks pour les événements
        self.progress_callbacks: List[Callable[[OperationProgress], None]] = []
        self.completion_callbacks: List[Callable[[OperationResult], None]] = []
        self.status_change_callbacks: List[Callable[[str, OperationStatus], None]] = []
        
        # Configuration
        self.config = {
            "max_concurrent_operations": 5,
            "max_history_size": 100,
            "default_timeout": 300,
            "progress_update_interval": 1.0
        }
        
        # Tâches de surveillance
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("Unified Async Interface initialized")
    
    async def start_operation(
        self,
        operation_type: OperationType,
        operation_func: Callable,
        operation_id: Optional[str] = None,
        estimated_duration: float = 0.0,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Démarre une nouvelle opération asynchrone
        
        Args:
            operation_type: Type d'opération
            operation_func: Fonction à exécuter
            operation_id: ID personnalisé (généré automatiquement si None)
            estimated_duration: Durée estimée en secondes
            timeout: Timeout personnalisé
            metadata: Métadonnées additionnelles
            progress_callback: Callback de progression spécifique
            
        Returns:
            ID de l'opération
        """
        
        if operation_id is None:
            operation_id = f"{operation_type.value}_{int(time.time() * 1000)}"
        
        # Vérifier les limites de concurrence
        if len(self.active_operations) >= self.config["max_concurrent_operations"]:
            raise RuntimeError("Maximum concurrent operations reached")
        
        # Créer l'objet de progression
        progress = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.INITIALIZING,
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )
        
        async with self.operation_lock:
            self.active_operations[operation_id] = progress
        
        # Démarrer la tâche d'exécution
        execution_task = asyncio.create_task(
            self._execute_operation(
                progress, operation_func, timeout or self.config["default_timeout"], progress_callback
            )
        )
        
        # Démarrer la surveillance de progression
        monitoring_task = asyncio.create_task(
            self._monitor_operation_progress(operation_id)
        )
        
        self._monitoring_tasks[operation_id] = monitoring_task
        
        logger.info(f"Started operation {operation_id} ({operation_type.value})")
        return operation_id
    
    async def _execute_operation(
        self,
        progress: OperationProgress,
        operation_func: Callable,
        timeout: float,
        progress_callback: Optional[Callable]
    ):
        """Exécute une opération avec gestion des erreurs et timeout"""
        
        operation_id = progress.operation_id
        
        try:
            # Marquer comme en cours
            progress.status = OperationStatus.RUNNING
            progress.current_step = "Démarrage de l'opération"
            await self._notify_status_change(operation_id, OperationStatus.RUNNING)
            
            # Créer un wrapper de callback de progression
            async def progress_wrapper(**kwargs):
                progress.update(**kwargs)
                await self._notify_progress_update(progress)
                if progress_callback:
                    await progress_callback(progress)
            
            # Exécuter avec timeout
            result = await asyncio.wait_for(
                operation_func(progress_wrapper),
                timeout=timeout
            )
            
            # Marquer comme terminé
            progress.status = OperationStatus.COMPLETED
            progress.end_time = time.time()
            progress.progress_percent = 100.0
            progress.current_step = "Opération terminée"
            
            # Créer le résultat
            operation_result = OperationResult(
                operation_id=operation_id,
                success=True,
                result=result,
                duration=progress.elapsed_time,
                metadata=progress.metadata
            )
            
            await self._complete_operation(operation_id, operation_result)
            
        except asyncio.TimeoutError:
            error_msg = f"Operation {operation_id} timed out after {timeout}s"
            logger.error(error_msg)
            
            progress.status = OperationStatus.FAILED
            progress.error_message = error_msg
            progress.end_time = time.time()
            
            operation_result = OperationResult(
                operation_id=operation_id,
                success=False,
                error=error_msg,
                duration=progress.elapsed_time
            )
            
            await self._complete_operation(operation_id, operation_result)
            
        except asyncio.CancelledError:
            logger.info(f"Operation {operation_id} was cancelled")
            
            progress.status = OperationStatus.CANCELLED
            progress.end_time = time.time()
            progress.current_step = "Opération annulée"
            
            operation_result = OperationResult(
                operation_id=operation_id,
                success=False,
                error="Operation cancelled",
                duration=progress.elapsed_time
            )
            
            await self._complete_operation(operation_id, operation_result)
            
        except Exception as e:
            error_msg = f"Operation {operation_id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            progress.status = OperationStatus.FAILED
            progress.error_message = error_msg
            progress.end_time = time.time()
            
            operation_result = OperationResult(
                operation_id=operation_id,
                success=False,
                error=error_msg,
                duration=progress.elapsed_time
            )
            
            await self._complete_operation(operation_id, operation_result)
    
    async def _monitor_operation_progress(self, operation_id: str):
        """Surveille la progression d'une opération"""
        
        while operation_id in self.active_operations:
            try:
                progress = self.active_operations[operation_id]
                
                if progress.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                    break
                
                # Notifier les callbacks de progression
                await self._notify_progress_update(progress)
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.config["progress_update_interval"])
                
            except Exception as e:
                logger.error(f"Error monitoring operation {operation_id}: {e}")
                break
        
        # Nettoyer la tâche de surveillance
        if operation_id in self._monitoring_tasks:
            del self._monitoring_tasks[operation_id]
    
    async def _complete_operation(self, operation_id: str, result: OperationResult):
        """Finalise une opération"""
        
        async with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations.pop(operation_id)
                
                # Ajouter à l'historique
                self.operation_history.append(progress)
                
                # Limiter la taille de l'historique
                if len(self.operation_history) > self.config["max_history_size"]:
                    self.operation_history = self.operation_history[-self.config["max_history_size"]:]
        
        # Notifier les callbacks de completion
        await self._notify_completion(result)
        
        # Notifier le changement de statut
        await self._notify_status_change(operation_id, result.success and OperationStatus.COMPLETED or OperationStatus.FAILED)
        
        logger.info(f"Operation {operation_id} completed: {'success' if result.success else 'failed'}")
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Annule une opération en cours"""
        
        if operation_id not in self.active_operations:
            return False
        
        # Annuler la tâche de surveillance
        if operation_id in self._monitoring_tasks:
            self._monitoring_tasks[operation_id].cancel()
        
        # Marquer comme annulé
        progress = self.active_operations[operation_id]
        progress.status = OperationStatus.CANCELLED
        progress.end_time = time.time()
        
        logger.info(f"Cancelled operation {operation_id}")
        return True
    
    async def pause_operation(self, operation_id: str) -> bool:
        """Met en pause une opération (si supporté)"""
        
        if operation_id not in self.active_operations:
            return False
        
        progress = self.active_operations[operation_id]
        if progress.status == OperationStatus.RUNNING:
            progress.status = OperationStatus.PAUSED
            await self._notify_status_change(operation_id, OperationStatus.PAUSED)
            logger.info(f"Paused operation {operation_id}")
            return True
        
        return False
    
    async def resume_operation(self, operation_id: str) -> bool:
        """Reprend une opération en pause"""
        
        if operation_id not in self.active_operations:
            return False
        
        progress = self.active_operations[operation_id]
        if progress.status == OperationStatus.PAUSED:
            progress.status = OperationStatus.RUNNING
            await self._notify_status_change(operation_id, OperationStatus.RUNNING)
            logger.info(f"Resumed operation {operation_id}")
            return True
        
        return False
    
    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Obtient les informations de progression d'une opération"""
        return self.active_operations.get(operation_id)
    
    def list_active_operations(self) -> List[OperationProgress]:
        """Liste toutes les opérations actives"""
        return list(self.active_operations.values())
    
    def get_operation_history(self, limit: int = 50) -> List[OperationProgress]:
        """Obtient l'historique des opérations"""
        return self.operation_history[-limit:]
    
    def get_operations_by_type(self, operation_type: OperationType) -> List[OperationProgress]:
        """Obtient les opérations par type"""
        active = [op for op in self.active_operations.values() if op.operation_type == operation_type]
        history = [op for op in self.operation_history if op.operation_type == operation_type]
        return active + history
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des opérations"""
        
        all_operations = list(self.active_operations.values()) + self.operation_history
        
        stats = {
            "total_operations": len(all_operations),
            "active_operations": len(self.active_operations),
            "completed_operations": len([op for op in all_operations if op.status == OperationStatus.COMPLETED]),
            "failed_operations": len([op for op in all_operations if op.status == OperationStatus.FAILED]),
            "cancelled_operations": len([op for op in all_operations if op.status == OperationStatus.CANCELLED]),
            "by_type": {},
            "average_duration": 0.0
        }
        
        # Statistiques par type
        for op_type in OperationType:
            ops_of_type = [op for op in all_operations if op.operation_type == op_type]
            stats["by_type"][op_type.value] = len(ops_of_type)
        
        # Durée moyenne des opérations terminées
        completed_ops = [op for op in all_operations if op.end_time is not None]
        if completed_ops:
            total_duration = sum(op.end_time - op.start_time for op in completed_ops)
            stats["average_duration"] = total_duration / len(completed_ops)
        
        return stats
    
    # Méthodes de callback
    
    def add_progress_callback(self, callback: Callable[[OperationProgress], None]):
        """Ajoute un callback de progression"""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[OperationResult], None]):
        """Ajoute un callback de completion"""
        self.completion_callbacks.append(callback)
    
    def add_status_change_callback(self, callback: Callable[[str, OperationStatus], None]):
        """Ajoute un callback de changement de statut"""
        self.status_change_callbacks.append(callback)
    
    async def _notify_progress_update(self, progress: OperationProgress):
        """Notifie les callbacks de progression"""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    async def _notify_completion(self, result: OperationResult):
        """Notifie les callbacks de completion"""
        for callback in self.completion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
    
    async def _notify_status_change(self, operation_id: str, status: OperationStatus):
        """Notifie les callbacks de changement de statut"""
        for callback in self.status_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(operation_id, status)
                else:
                    callback(operation_id, status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")
    
    async def cancel_all_operations(self) -> int:
        """Annule toutes les opérations actives"""
        
        operation_ids = list(self.active_operations.keys())
        cancelled_count = 0
        
        for operation_id in operation_ids:
            if await self.cancel_operation(operation_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} operations")
        return cancelled_count
    
    async def shutdown(self):
        """Arrêt propre de l'interface"""
        
        logger.info("Shutting down Unified Async Interface...")
        
        # Annuler toutes les opérations
        await self.cancel_all_operations()
        
        # Annuler toutes les tâches de surveillance
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Attendre que toutes les tâches se terminent
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        self._monitoring_tasks.clear()
        
        logger.info("Unified Async Interface shutdown completed")


# Instance globale
unified_async_interface = UnifiedAsyncInterface()