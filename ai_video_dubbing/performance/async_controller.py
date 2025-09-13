"""
Contrôleur asynchrone pour éviter les blocages lors des opérations NeMo
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, Callable, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    """Informations sur une tâche en cours"""
    task_id: str
    operation_type: str
    start_time: float
    timeout: int
    progress_callback: Optional[Callable] = None
    cancelled: bool = False

class TimeoutManager:
    """Gestionnaire des timeouts avec suggestions de fallback"""
    
    def __init__(self):
        self.timeout_history: Dict[str, int] = {}
        
    def get_recommended_timeout(self, operation_type: str) -> int:
        """Recommande un timeout basé sur l'historique"""
        base_timeouts = {
            "download": 300,  # 5 minutes
            "model_loading": 120,  # 2 minutes
            "transcription": 600,  # 10 minutes
        }
        
        base_timeout = base_timeouts.get(operation_type, 300)
        
        # Ajuster basé sur l'historique
        if operation_type in self.timeout_history:
            historical_timeout = self.timeout_history[operation_type]
            return max(base_timeout, int(historical_timeout * 1.2))
        
        return base_timeout
    
    def record_completion_time(self, operation_type: str, duration: float):
        """Enregistre le temps de completion pour améliorer les estimations"""
        self.timeout_history[operation_type] = duration

class AsyncNeMoController:
    """Contrôleur asynchrone pour les opérations NeMo"""
    
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_info: Dict[str, TaskInfo] = {}
        self.timeout_manager = TimeoutManager()
        self.cleanup_lock = asyncio.Lock()
        
    async def execute_with_timeout(self, 
                                 operation: Callable,
                                 operation_type: str = "generic",
                                 timeout: Optional[int] = None,
                                 progress_callback: Optional[Callable] = None,
                                 **kwargs) -> Any:
        """
        Exécute une opération avec timeout et callback de progression
        
        Args:
            operation: Fonction à exécuter
            operation_type: Type d'opération pour les métriques
            timeout: Timeout en secondes (auto si None)
            progress_callback: Callback pour les mises à jour de progression
            **kwargs: Arguments pour l'opération
            
        Returns:
            Résultat de l'opération
            
        Raises:
            TimeoutError: Si l'opération dépasse le timeout
            asyncio.CancelledError: Si l'opération est annulée
        """
        task_id = str(uuid.uuid4())
        
        if timeout is None:
            timeout = self.timeout_manager.get_recommended_timeout(operation_type)
        
        task_info = TaskInfo(
            task_id=task_id,
            operation_type=operation_type,
            start_time=time.time(),
            timeout=timeout,
            progress_callback=progress_callback
        )
        
        self.task_info[task_id] = task_info
        
        try:
            logger.info(f"Starting {operation_type} operation {task_id} with timeout {timeout}s")
            
            # Créer la tâche asynchrone
            if asyncio.iscoroutinefunction(operation):
                task = asyncio.create_task(operation(**kwargs))
            else:
                # Wrapper pour les fonctions synchrones
                task = asyncio.create_task(self._run_sync_in_executor(operation, **kwargs))
            
            self.active_tasks[task_id] = task
            
            # Démarrer le monitoring de progression si callback fourni
            if progress_callback:
                asyncio.create_task(self._monitor_progress(task_id))
            
            # Attendre avec timeout
            try:
                result = await asyncio.wait_for(task, timeout=timeout)
                
                # Enregistrer le temps de completion
                duration = time.time() - task_info.start_time
                self.timeout_manager.record_completion_time(operation_type, duration)
                
                logger.info(f"Operation {task_id} completed successfully in {duration:.2f}s")
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Operation {task_id} timed out after {timeout}s")
                await self._handle_timeout(task_id)
                raise TimeoutError(f"Operation {operation_type} timed out after {timeout}s")
                
        except asyncio.CancelledError:
            logger.info(f"Operation {task_id} was cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Operation {task_id} failed: {e}")
            raise
            
        finally:
            await self._cleanup_task(task_id)
    
    async def cancel_operation(self, task_id: str) -> bool:
        """
        Annule une opération en cours
        
        Args:
            task_id: ID de la tâche à annuler
            
        Returns:
            True si l'annulation a réussi
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found for cancellation")
            return False
        
        task_info = self.task_info.get(task_id)
        if task_info:
            task_info.cancelled = True
        
        task = self.active_tasks[task_id]
        task.cancel()
        
        # Nettoyer les téléchargements partiels si applicable
        await self._cleanup_partial_downloads(task_id)
        
        logger.info(f"Task {task_id} cancelled successfully")
        return True
    
    async def cancel_all_operations(self) -> int:
        """
        Annule toutes les opérations en cours
        
        Returns:
            Nombre d'opérations annulées
        """
        task_ids = list(self.active_tasks.keys())
        cancelled_count = 0
        
        for task_id in task_ids:
            if await self.cancel_operation(task_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} operations")
        return cancelled_count
    
    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne les informations sur les opérations actives
        
        Returns:
            Dictionnaire des opérations actives avec leurs infos
        """
        active_ops = {}
        
        for task_id, task_info in self.task_info.items():
            if task_id in self.active_tasks:
                elapsed = time.time() - task_info.start_time
                active_ops[task_id] = {
                    "operation_type": task_info.operation_type,
                    "elapsed_time": elapsed,
                    "timeout": task_info.timeout,
                    "progress": elapsed / task_info.timeout * 100,
                    "cancelled": task_info.cancelled
                }
        
        return active_ops
    
    async def _run_sync_in_executor(self, func: Callable, **kwargs) -> Any:
        """Exécute une fonction synchrone dans un executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(**kwargs))
    
    async def _monitor_progress(self, task_id: str):
        """Monitore la progression d'une tâche"""
        task_info = self.task_info.get(task_id)
        if not task_info or not task_info.progress_callback:
            return
        
        try:
            while task_id in self.active_tasks and not task_info.cancelled:
                elapsed = time.time() - task_info.start_time
                progress_percent = min((elapsed / task_info.timeout) * 100, 99)
                
                # Appeler le callback de progression
                try:
                    if asyncio.iscoroutinefunction(task_info.progress_callback):
                        await task_info.progress_callback(task_id, progress_percent, elapsed)
                    else:
                        task_info.progress_callback(task_id, progress_percent, elapsed)
                except Exception as e:
                    logger.error(f"Progress callback error for task {task_id}: {e}")
                
                await asyncio.sleep(1.0)  # Mise à jour chaque seconde
                
        except Exception as e:
            logger.error(f"Progress monitoring error for task {task_id}: {e}")
    
    async def _handle_timeout(self, task_id: str):
        """Gère les timeouts avec suggestions de fallback"""
        task_info = self.task_info.get(task_id)
        if not task_info:
            return
        
        # Annuler la tâche
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
        
        # Nettoyer les ressources
        await self._cleanup_partial_downloads(task_id)
        
        # Log pour diagnostic
        logger.warning(f"Timeout handled for {task_info.operation_type} operation {task_id}")
    
    async def _cleanup_partial_downloads(self, task_id: str):
        """Nettoie les téléchargements partiels"""
        task_info = self.task_info.get(task_id)
        if not task_info or task_info.operation_type != "download":
            return
        
        try:
            # Chercher les fichiers partiels (.part, .tmp)
            temp_patterns = [
                f"*{task_id}*.part",
                f"*{task_id}*.tmp",
                f"temp_download_{task_id}*"
            ]
            
            for pattern in temp_patterns:
                for temp_file in Path(".").glob(pattern):
                    try:
                        temp_file.unlink()
                        logger.info(f"Cleaned up partial download: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Could not clean up {temp_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up partial downloads for {task_id}: {e}")
    
    async def _cleanup_task(self, task_id: str):
        """Nettoie les ressources d'une tâche terminée"""
        async with self.cleanup_lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            if task_id in self.task_info:
                del self.task_info[task_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        return {
            "active_tasks": len(self.active_tasks),
            "timeout_history": dict(self.timeout_manager.timeout_history),
            "total_tasks_processed": len(self.timeout_manager.timeout_history)
        }

# Instance globale pour l'application
async_controller = AsyncNeMoController()