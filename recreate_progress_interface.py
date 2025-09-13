#!/usr/bin/env python3
"""
Script pour recréer le fichier progress_interface.py avec OperationType
"""

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
    operation_type: str
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

class RealTimeProgressInterface:
    """Interface de progression temps réel pour les opérations longues"""
    
    def __init__(self, ui_update_interval: float = 0.5):
        self.ui_update_interval = ui_update_interval
        self.active_operations: Dict[str, OperationProgress] = {}
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
                            operation_type: str,
                            operation_id: Optional[str] = None,
                            estimated_duration: float = 0.0,
                            metadata: Optional[Dict[str, Any]] = None) -> ProgressTracker:
        """
        Démarre le suivi d'une nouvelle opération
        """
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        # Créer l'objet de progression
        progress = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.STARTING,
            details=metadata or {}
        )
        
        # Enregistrer l'opération
        with self.operation_lock:
            self.active_operations[operation_id] = progress
            self.global_stats["total_operations"] += 1
        
        # Créer le tracker
        tracker = ProgressTracker(progress, self._update_progress_callback)
        
        logger.info(f"Started tracking operation {operation_id} ({operation_type})")
        return tracker
    
    async def _update_progress_callback(self, progress: OperationProgress):
        """Callback appelé lors des mises à jour de progression"""
        # Mettre à jour le statut si nécessaire
        if progress.progress_percent > 0 and progress.status == OperationStatus.STARTING:
            progress.status = OperationStatus.IN_PROGRESS
    
    async def complete_operation(self, operation_id: str, success: bool = True, message: str = ""):
        """Marque une opération comme terminée"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
                progress.progress_percent = 100.0 if success else progress.progress_percent
                if message:
                    progress.status_message = message
    
    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Obtient les informations de progression d'une opération"""
        with self.operation_lock:
            return self.active_operations.get(operation_id)
    
    def list_active_operations(self) -> List[Dict[str, Any]]:
        """Liste toutes les opérations actives"""
        with self.operation_lock:
            operations = []
            for progress in self.active_operations.values():
                operations.append({
                    "operation_id": progress.operation_id,
                    "operation_type": progress.operation_type,
                    "status": progress.status.value,
                    "progress_percent": progress.progress_percent,
                    "elapsed_time": progress.elapsed_time,
                    "eta_seconds": progress.eta_seconds,
                    "current_task": progress.current_task
                })
            return operations

# Instance globale
real_time_progress_interface = RealTimeProgressInterface()
'''

# Supprimer l'ancien fichier et créer le nouveau
import os
if os.path.exists('ai_video_dubbing/performance/progress_interface.py'):
    os.remove('ai_video_dubbing/performance/progress_interface.py')

# Écrire le nouveau fichier
with open('ai_video_dubbing/performance/progress_interface.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fichier progress_interface.py recréé avec OperationType")