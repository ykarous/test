#!/usr/bin/env python3
"""
Script pour créer un fichier progress_interface.py simple et fonctionnel
"""

import os

# Contenu du fichier
content = '''"""
Interface de progression temps réel pour les opérations longues
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import uuid

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Statuts possibles d'une opération"""
    PENDING = "pending"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OperationProgress:
    """Informations de progression d'une opération"""
    operation_id: str
    operation_type: str
    status: OperationStatus = OperationStatus.PENDING
    start_time: float = field(default_factory=time.time)
    progress_percent: float = 0.0
    current_step: str = ""
    elapsed_time: float = 0.0
    current_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_progress(self, **kwargs):
        """Met à jour les informations de progression"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.elapsed_time = time.time() - self.start_time
    
    def complete(self, success: bool = True):
        """Marque l'opération comme terminée"""
        self.elapsed_time = time.time() - self.start_time
        self.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
        self.progress_percent = 100.0 if success else self.progress_percent

class ProgressTracker:
    """Tracker pour une opération spécifique"""
    
    def __init__(self, progress: OperationProgress, update_callback: Callable):
        self.progress = progress
        self.update_callback = update_callback
        self._cancelled = False
    
    async def update(self, **kwargs):
        """Met à jour la progression"""
        if not self._cancelled:
            self.progress.update_progress(**kwargs)
            if self.update_callback:
                await self.update_callback(self.progress.operation_id, **kwargs)
    
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
                            estimated_duration: float = 0.0,
                            operation_id: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> ProgressTracker:
        """Démarre le suivi d'une nouvelle opération"""
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        progress = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.STARTING,
            metadata=metadata or {}
        )
        
        with self.operation_lock:
            self.active_operations[operation_id] = progress
            self.global_stats["total_operations"] += 1
        
        tracker = ProgressTracker(progress, self._update_progress)
        logger.info(f"Started tracking operation {operation_id} ({operation_type})")
        return tracker
    
    async def _update_progress(self, operation_id: str, **kwargs):
        """Met à jour les informations de progression d'une opération"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.update_progress(**kwargs)
                if progress.progress_percent > 0 and progress.status == OperationStatus.STARTING:
                    progress.status = OperationStatus.IN_PROGRESS
    
    async def complete_operation(self, operation_id: str, success: bool = True, message: str = ""):
        """Marque une opération comme terminée"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.complete(success)
                if message:
                    progress.current_message = message
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Annule une opération en cours"""
        with self.operation_lock:
            if operation_id in self.active_operations:
                progress = self.active_operations[operation_id]
                progress.status = OperationStatus.CANCELLED
                progress.current_message = "Opération annulée par l'utilisateur"
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
                operations.append({
                    "operation_id": progress.operation_id,
                    "operation_type": progress.operation_type,
                    "status": progress.status.value,
                    "progress_percent": progress.progress_percent,
                    "elapsed_time": progress.elapsed_time,
                    "current_message": progress.current_message
                })
            return operations
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques globales"""
        with self.operation_lock:
            return self.global_stats.copy()
    
    def add_ui_callback(self, callback: Callable):
        """Ajoute un callback pour les mises à jour UI"""
        self.ui_callbacks.append(callback)
    
    def add_notification_callback(self, callback: Callable):
        """Ajoute un callback pour les notifications"""
        self.notification_callbacks.append(callback)
    
    async def shutdown(self):
        """Arrête proprement l'interface de progression"""
        operation_ids = list(self.active_operations.keys())
        for operation_id in operation_ids:
            await self.cancel_operation(operation_id)
        logger.info("Progress interface shutdown complete")

# Instance globale
real_time_progress_interface = RealTimeProgressInterface()
'''

# Supprimer l'ancien fichier s'il existe
file_path = 'ai_video_dubbing/performance/progress_interface.py'
if os.path.exists(file_path):
    os.remove(file_path)

# Créer le nouveau fichier
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fichier créé: {file_path}")
print(f"Taille: {len(content)} caractères")

# Vérifier que le fichier a été créé correctement
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        written_content = f.read()
    print(f"Vérification - Taille lue: {len(written_content)} caractères")
    if 'RealTimeProgressInterface' in written_content:
        print("✅ Classe RealTimeProgressInterface trouvée")
    else:
        print("❌ Classe RealTimeProgressInterface non trouvée")
else:
    print("❌ Fichier non créé")