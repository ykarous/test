#!/usr/bin/env python3
import os

# Supprimer l'ancien fichier s'il existe
if os.path.exists('ai_video_dubbing/performance/progress_interface.py'):
    os.remove('ai_video_dubbing/performance/progress_interface.py')

# Contenu du fichier final avec toutes les corrections
content = '''"""
Interface de progression temps réel pour les opérations longues
"""

import asyncio
import time
import logging
import threading
import uuid
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Statuts possibles d'une opération"""
    PENDING = "pending"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OperationType(Enum):
    """Types d'opérations supportées"""
    DOWNLOAD = "download"
    MODEL_LOADING = "model_loading"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    AUDIO_PROCESSING = "audio_processing"

@dataclass
class OperationProgress:
    """Informations de progression d'une opération"""
    operation_id: str
    operation_type: Any  # Peut être OperationType ou str
    status: OperationStatus = OperationStatus.PENDING
    progress_percent: float = 0.0
    current_step: int = 0
    total_steps: int = 1
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    elapsed_time: float = 0.0
    eta_seconds: float = 0.0
    current_task: str = ""
    throughput: float = 0.0
    status_message: str = ""
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def update_progress(self, **kwargs):
        """Met à jour les informations de progression"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.last_update = time.time()
        self.elapsed_time = self.last_update - self.start_time
        
        # Calcul de l'ETA basé sur le pourcentage de progression
        if self.progress_percent > 0 and self.elapsed_time > 0:
            total_estimated = self.elapsed_time / (self.progress_percent / 100)
            self.eta_seconds = max(0, total_estimated - self.elapsed_time)

class ProgressTracker:
    """Tracker pour une opération spécifique"""
    
    def __init__(self, progress: OperationProgress, update_callback: Optional[Callable] = None):
        self.progress = progress
        self.update_callback = update_callback
        self._cancelled = False
    
    async def update(self, **kwargs):
        """Met à jour la progression"""
        if not self._cancelled:
            self.progress.update_progress(**kwargs)
            if self.update_callback:
                await self.update_callback(self.progress)
    
    def cancel(self):
        """Annule le suivi"""
        self._cancelled = True
        self.progress.status = OperationStatus.CANCELLED
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
    
    async def complete(self, message: str = ""):
        """Marque l'opération comme terminée"""
        self.progress.status = OperationStatus.COMPLETED
        self.progress.progress_percent = 100.0
        if message:
            self.progress.status_message = message
        if self.update_callback:
            await self.update_callback(self.progress)
    
    async def set_error(self, message: str = ""):
        """Marque l'opération comme échouée"""
        self.progress.status = OperationStatus.FAILED
        if message:
            self.progress.error_message = message
            self.progress.status_message = message
        if self.update_callback:
            await self.update_callback(self.progress)

class RealTimeProgressInterface:
    """Interface de progression temps réel pour les opérations longues"""
    
    def __init__(self, ui_update_interval: float = 0.5, update_interval: Optional[float] = None):
        # Support pour les deux noms de paramètres
        if update_interval is not None:
            self.ui_update_interval = update_interval
        else:
            self.ui_update_interval = ui_update_interval
            
        self.active_operations: Dict[str, OperationProgress] = {}
        self.active_trackers: Dict[str, ProgressTracker] = {}  # Garder les références aux trackers
        self.operation_lock = threading.RLock()
        self.ui_callbacks: List[Callable] = []
        self.notification_callbacks: List[Callable] = []
        self.update_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistiques globales
        self.global_stats = {
            "total_operations": 0,
            "completed_operations": 0,
            "failed_operations": 0,
            "cancelled_operations": 0,
            "average_duration": 0.0
        }
    
    async def track_operation(self, 
                            operation_type,
                            operation_id: Optional[str] = None,
                            estimated_duration: float = 0.0,
                            metadata: Optional[Dict[str, Any]] = None,
                            total_steps: Optional[int] = None,
                            initial_task: Optional[str] = None) -> ProgressTracker:
        """
        Démarre le suivi d'une nouvelle opération
        """
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        # Créer l'objet de progression
        progress = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,  # Garder l'enum original
            status=OperationStatus.STARTING,
            details=metadata or {}
        )
        
        # Appliquer les paramètres optionnels
        if total_steps is not None:
            progress.total_steps = total_steps
        if initial_task is not None:
            progress.current_task = initial_task
        
        # Créer le tracker
        tracker = ProgressTracker(progress, self._update_progress_callback)
        
        # Enregistrer l'opération et le tracker
        with self.operation_lock:
            self.active_operations[operation_id] = progress
            self.active_trackers[operation_id] = tracker
            self.global_stats["total_operations"] += 1
        
        # Convertir pour le log
        operation_type_str = operation_type.value if hasattr(operation_type, 'value') else str(operation_type)
        logger.info(f"Started tracking operation {operation_id} ({operation_type_str})")
        return tracker
    
    async def _update_progress_callback(self, progress: OperationProgress):
        """Callback appelé lors des mises à jour de progression"""
        # Mettre à jour le statut si nécessaire
        if progress.progress_percent > 0 and progress.status == OperationStatus.STARTING:
            progress.status = OperationStatus.IN_PROGRESS
        
        # Appeler les callbacks UI
        await self._send_ui_updates(progress)
    
    async def _send_ui_updates(self, progress: OperationProgress):
        """Envoie les mises à jour aux callbacks UI"""
        update_data = {
            "operation_id": progress.operation_id,
            "operation_type": progress.operation_type.value if hasattr(progress.operation_type, 'value') else str(progress.operation_type),
            "status": progress.status.value,
            "progress_percent": progress.progress_percent,
            "current_step": progress.current_step,
            "total_steps": progress.total_steps,
            "current_task": progress.current_task,
            "elapsed_time": progress.elapsed_time,
            "eta_seconds": progress.eta_seconds,
            "throughput": progress.throughput,
            "status_message": progress.status_message
        }
        
        # Envoyer aux callbacks UI
        for callback in self.ui_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback("progress_update", update_data)
                else:
                    callback("progress_update", update_data)
            except Exception as e:
                logger.warning(f"Error in UI callback: {e}")
    
    async def complete_operation(self, operation_id: str, success: bool = True, message: str = ""):
        """Marque une opération comme terminée"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
                progress.progress_percent = 100.0 if success else progress.progress_percent
                if message:
                    progress.status_message = message
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Annule une opération en cours"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.status = OperationStatus.CANCELLED
                progress.status_message = "Opération annulée par l'utilisateur"
                
                # Marquer le tracker comme annulé aussi
                if operation_id in self.active_trackers:
                    tracker = self.active_trackers[operation_id]
                    tracker.cancel()
                
                return True
        return False
    
    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Obtient les informations de progression d'une opération"""
        with self.operation_lock:
            return self.active_operations.get(operation_id)
    
    def list_active_operations(self) -> List[Dict[str, Any]]:
        """Liste toutes les opérations actives"""
        with self.operation_lock:
            operations = []
            for progress in self.active_operations.values():
                # Convertir operation_type pour l'affichage
                operation_type_str = progress.operation_type.value if hasattr(progress.operation_type, 'value') else str(progress.operation_type)
                operations.append({
                    "operation_id": progress.operation_id,
                    "operation_type": operation_type_str,
                    "status": progress.status.value,
                    "progress_percent": progress.progress_percent,
                    "elapsed_time": progress.elapsed_time,
                    "eta_seconds": progress.eta_seconds,
                    "current_task": progress.current_task
                })
            return operations
    
    def add_ui_callback(self, callback: Callable):
        """Ajoute un callback pour les mises à jour UI"""
        self.ui_callbacks.append(callback)
    
    def add_notification_callback(self, callback: Callable):
        """Ajoute un callback pour les notifications"""
        self.notification_callbacks.append(callback)
    
    async def cancel_all_operations(self):
        """Annule toutes les opérations actives"""
        operation_ids = list(self.active_operations.keys())
        for operation_id in operation_ids:
            await self.cancel_operation(operation_id)
    
    async def stop(self):
        """Arrête l'interface de progression"""
        await self.cancel_all_operations()
        # Nettoyer les tâches de mise à jour
        if self.update_tasks:
            for task in self.update_tasks.values():
                if not task.done():
                    task.cancel()
            self.update_tasks.clear()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtient un résumé des statistiques"""
        with self.operation_lock:
            active_count = len(self.active_operations)
            return {
                **self.global_stats,
                "active_operations": active_count,
                "total_active_and_completed": self.global_stats["total_operations"]
            }
    
    def create_progress_message(self, operation_data: Dict[str, Any]) -> str:
        """Crée un message de progression formaté"""
        op_type = operation_data.get("operation_type", "Unknown")
        progress = operation_data.get("progress_percent", 0)
        status = operation_data.get("status", "unknown")
        eta = operation_data.get("eta_seconds", 0)
        
        if status == "completed":
            return f"{op_type}: ✅ Terminé (100%)"
        elif status == "failed":
            return f"{op_type}: ❌ Échoué ({progress:.1f}%)"
        elif status == "cancelled":
            return f"{op_type}: 🛑 Annulé ({progress:.1f}%)"
        else:
            eta_str = f" - ETA: {eta:.1f}s" if eta > 0 else ""
            return f"{op_type}: 🔄 En cours ({progress:.1f}%){eta_str}"

# Instance globale
real_time_progress_interface = RealTimeProgressInterface()
'''

# Écrire le fichier avec l'encodage correct
with open('ai_video_dubbing/performance/progress_interface.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fichier progress_interface.py final créé avec toutes les corrections")
print(f"Taille: {len(content)} caractères")