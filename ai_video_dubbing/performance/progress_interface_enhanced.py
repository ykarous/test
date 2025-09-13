"""
Interface de progression temps réel améliorée avec messages contextuels
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import uuid

from .contextual_messages import (
    ContextualMessageGenerator, ProgressContext, OperationType, 
    MessageType, ContextualMessage
)

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Statuts possibles d'une opération"""
    PENDING = "pending"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class EnhancedProgressUpdate:
    """Mise à jour de progression améliorée avec messages contextuels"""
    operation_id: str
    operation_type: OperationType
    progress_percent: float
    current_step: str
    status: OperationStatus
    start_time: float
    last_update_time: float
    estimated_duration: Optional[float] = None
    
    # Métriques spécifiques
    download_speed: Optional[float] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    model_name: Optional[str] = None
    language: Optional[str] = None
    quality_preference: Optional[str] = None
    gpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    
    # Erreurs et solutions
    error_message: Optional[str] = None
    suggested_solutions: List[str] = field(default_factory=list)
    
    # Messages contextuels
    contextual_message: Optional[ContextualMessage] = None
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnhancedOperationProgress:
    """Progression d'opération améliorée"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    progress_percent: float = 0.0
    current_step: str = ""
    start_time: float = field(default_factory=time.time)
    estimated_duration: Optional[float] = None
    
    # Métriques spécifiques
    download_speed: Optional[float] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    model_name: Optional[str] = None
    language: Optional[str] = None
    quality_preference: Optional[str] = None
    gpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    
    # Erreurs
    error_message: Optional[str] = None
    suggested_solutions: List[str] = field(default_factory=list)
    
    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_progress_update(self) -> EnhancedProgressUpdate:
        """Convertit en mise à jour de progression"""
        return EnhancedProgressUpdate(
            operation_id=self.operation_id,
            operation_type=self.operation_type,
            progress_percent=self.progress_percent,
            current_step=self.current_step,
            status=self.status,
            start_time=self.start_time,
            last_update_time=time.time(),
            estimated_duration=self.estimated_duration,
            download_speed=self.download_speed,
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            model_name=self.model_name,
            language=self.language,
            quality_preference=self.quality_preference,
            gpu_usage=self.gpu_usage,
            memory_usage=self.memory_usage,
            cache_hit_rate=self.cache_hit_rate,
            error_message=self.error_message,
            suggested_solutions=self.suggested_solutions.copy(),
            metadata=self.metadata.copy()
        )
    
    def update_progress(self, **kwargs):
        """Met à jour les champs de progression"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class EnhancedProgressTracker:
    """Tracker de progression amélioré avec messages contextuels"""
    
    def __init__(self, progress: EnhancedOperationProgress, 
                 update_callback: Callable, message_generator: ContextualMessageGenerator):
        self.progress = progress
        self.update_callback = update_callback
        self.message_generator = message_generator
        self._cancelled = False
    
    async def update(self, **kwargs):
        """Met à jour la progression avec génération de message contextuel"""
        if self._cancelled:
            return
        
        # Mettre à jour la progression
        self.progress.update_progress(**kwargs)
        
        # Créer le contexte pour le générateur de messages
        context = ProgressContext(
            operation_type=self.progress.operation_type,
            operation_id=self.progress.operation_id,
            progress_percent=self.progress.progress_percent,
            current_step=self.progress.current_step,
            start_time=self.progress.start_time,
            estimated_duration=self.progress.estimated_duration,
            download_speed=self.progress.download_speed,
            downloaded_bytes=self.progress.downloaded_bytes,
            total_bytes=self.progress.total_bytes,
            model_name=self.progress.model_name,
            language=self.progress.language,
            quality_preference=self.progress.quality_preference,
            gpu_usage=self.progress.gpu_usage,
            memory_usage=self.progress.memory_usage,
            cache_hit_rate=self.progress.cache_hit_rate,
            error_message=self.progress.error_message,
            suggested_solutions=self.progress.suggested_solutions,
            metadata=self.progress.metadata
        )
        
        # Générer le message contextuel
        contextual_message = self.message_generator.create_progress_message(context)
        
        # Créer la mise à jour complète
        progress_update = self.progress.to_progress_update()
        progress_update.contextual_message = contextual_message
        
        # Appeler le callback
        if self.update_callback:
            await self.update_callback(progress_update)
    
    def cancel(self):
        """Annule le suivi"""
        self._cancelled = True
        self.progress.status = OperationStatus.CANCELLED
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

class EnhancedRealTimeProgressInterface:
    """Interface de progression temps réel améliorée avec messages contextuels"""
    
    def __init__(self, ui_update_interval: float = 0.5):
        self.ui_update_interval = ui_update_interval
        self.active_operations: Dict[str, EnhancedOperationProgress] = {}
        self.operation_trackers: Dict[str, EnhancedProgressTracker] = {}
        self.operation_lock = asyncio.Lock()
        
        # Générateur de messages contextuels
        self.message_generator = ContextualMessageGenerator()
        
        # Callbacks pour les mises à jour
        self.progress_callbacks: List[Callable[[EnhancedProgressUpdate], None]] = []
        self.completion_callbacks: List[Callable[[str, bool], None]] = []
        self.error_callbacks: List[Callable[[str, str], None]] = []
        
        # Tâche de mise à jour UI
        self.ui_update_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Statistiques
        self.total_operations = 0
        self.completed_operations = 0
        self.failed_operations = 0
        self.cancelled_operations = 0
    
    async def start(self):
        """Démarre l'interface de progression"""
        if self.is_running:
            return
        
        self.is_running = True
        self.ui_update_task = asyncio.create_task(self._ui_update_loop())
        logger.info("Enhanced progress interface started")
    
    async def stop(self):
        """Arrête l'interface de progression"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.ui_update_task:
            self.ui_update_task.cancel()
            try:
                await self.ui_update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Enhanced progress interface stopped")
    
    async def track_operation(self, operation_type: OperationType, 
                            operation_id: Optional[str] = None,
                            estimated_duration: Optional[float] = None,
                            **kwargs) -> EnhancedProgressTracker:
        """Démarre le suivi d'une nouvelle opération"""
        
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        async with self.operation_lock:
            # Créer la progression d'opération
            progress = EnhancedOperationProgress(
                operation_id=operation_id,
                operation_type=operation_type,
                estimated_duration=estimated_duration,
                status=OperationStatus.STARTING
            )
            
            # Mettre à jour avec les paramètres fournis
            progress.update_progress(**kwargs)
            
            # Créer le tracker
            tracker = EnhancedProgressTracker(
                progress=progress,
                update_callback=self._on_progress_update,
                message_generator=self.message_generator
            )
            
            # Enregistrer
            self.active_operations[operation_id] = progress
            self.operation_trackers[operation_id] = tracker
            self.total_operations += 1
            
            # Démarrer l'interface si nécessaire
            if not self.is_running:
                await self.start()
            
            logger.debug(f"Started tracking operation {operation_id} ({operation_type.value})")
            
            return tracker
    
    async def complete_operation(self, operation_id: str, success: bool = True, 
                               error_message: Optional[str] = None):
        """Marque une opération comme terminée"""
        
        async with self.operation_lock:
            if operation_id not in self.active_operations:
                logger.warning(f"Operation {operation_id} not found")
                return
            
            progress = self.active_operations[operation_id]
            tracker = self.operation_trackers.get(operation_id)
            
            if success:
                progress.status = OperationStatus.COMPLETED
                progress.progress_percent = 100.0
                self.completed_operations += 1
            else:
                progress.status = OperationStatus.FAILED
                if error_message:
                    progress.error_message = error_message
                self.failed_operations += 1
            
            # Dernière mise à jour avec message contextuel
            if tracker:
                await tracker.update()
            
            # Notifier les callbacks de completion
            for callback in self.completion_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(operation_id, success)
                    else:
                        callback(operation_id, success)
                except Exception as e:
                    logger.warning(f"Completion callback error: {e}")
            
            # Notifier les callbacks d'erreur si nécessaire
            if not success and error_message:
                for callback in self.error_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(operation_id, error_message)
                        else:
                            callback(operation_id, error_message)
                    except Exception as e:
                        logger.warning(f"Error callback error: {e}")
            
            logger.debug(f"Completed operation {operation_id} (success: {success})")
    
    async def cancel_operation(self, operation_id: str):
        """Annule une opération"""
        
        async with self.operation_lock:
            if operation_id not in self.active_operations:
                logger.warning(f"Operation {operation_id} not found")
                return
            
            progress = self.active_operations[operation_id]
            tracker = self.operation_trackers.get(operation_id)
            
            progress.status = OperationStatus.CANCELLED
            self.cancelled_operations += 1
            
            if tracker:
                tracker.cancel()
                await tracker.update(current_step="Opération annulée")
            
            logger.debug(f"Cancelled operation {operation_id}")
    
    async def _on_progress_update(self, progress_update: EnhancedProgressUpdate):
        """Gestionnaire interne des mises à jour de progression"""
        
        # Notifier tous les callbacks de progression
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress_update)
                else:
                    callback(progress_update)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    async def _ui_update_loop(self):
        """Boucle de mise à jour de l'interface utilisateur"""
        
        while self.is_running:
            try:
                await asyncio.sleep(self.ui_update_interval)
                
                # Nettoyer les opérations terminées anciennes
                await self._cleanup_old_operations()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"UI update loop error: {e}")
    
    async def _cleanup_old_operations(self, max_age: float = 300.0):
        """Nettoie les opérations terminées anciennes"""
        
        current_time = time.time()
        to_remove = []
        
        async with self.operation_lock:
            for operation_id, progress in self.active_operations.items():
                if (progress.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED] and
                    current_time - progress.start_time > max_age):
                    to_remove.append(operation_id)
            
            for operation_id in to_remove:
                del self.active_operations[operation_id]
                if operation_id in self.operation_trackers:
                    del self.operation_trackers[operation_id]
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old operations")
    
    def add_progress_callback(self, callback: Callable[[EnhancedProgressUpdate], None]):
        """Ajoute un callback de progression"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[EnhancedProgressUpdate], None]):
        """Supprime un callback de progression"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def add_completion_callback(self, callback: Callable[[str, bool], None]):
        """Ajoute un callback de completion"""
        self.completion_callbacks.append(callback)
    
    def remove_completion_callback(self, callback: Callable[[str, bool], None]):
        """Supprime un callback de completion"""
        if callback in self.completion_callbacks:
            self.completion_callbacks.remove(callback)
    
    def add_error_callback(self, callback: Callable[[str, str], None]):
        """Ajoute un callback d'erreur"""
        self.error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[str, str], None]):
        """Supprime un callback d'erreur"""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
    
    def get_operation_status(self, operation_id: str) -> Optional[EnhancedOperationProgress]:
        """Retourne le statut d'une opération"""
        return self.active_operations.get(operation_id)
    
    def get_all_operations(self) -> Dict[str, EnhancedOperationProgress]:
        """Retourne toutes les opérations actives"""
        return self.active_operations.copy()
    
    def get_active_operations_count(self) -> int:
        """Retourne le nombre d'opérations actives"""
        active_count = 0
        for progress in self.active_operations.values():
            if progress.status in [OperationStatus.STARTING, OperationStatus.IN_PROGRESS]:
                active_count += 1
        return active_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'interface"""
        return {
            "total_operations": self.total_operations,
            "completed_operations": self.completed_operations,
            "failed_operations": self.failed_operations,
            "cancelled_operations": self.cancelled_operations,
            "active_operations": self.get_active_operations_count(),
            "success_rate": self.completed_operations / max(self.total_operations, 1),
            "is_running": self.is_running
        }
    
    async def shutdown(self):
        """Arrêt propre de l'interface"""
        logger.info("Shutting down enhanced progress interface...")
        
        # Annuler toutes les opérations actives
        operation_ids = list(self.active_operations.keys())
        for operation_id in operation_ids:
            progress = self.active_operations[operation_id]
            if progress.status in [OperationStatus.STARTING, OperationStatus.IN_PROGRESS]:
                await self.cancel_operation(operation_id)
        
        # Arrêter l'interface
        await self.stop()
        
        logger.info("Enhanced progress interface shutdown complete")

# Instance globale pour faciliter l'utilisation
enhanced_progress_interface = EnhancedRealTimeProgressInterface()