"""Actions de gestion avancées pour les modèles avec notifications"""
import asyncio
import time
import logging
import shutil
import hashlib
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types d'actions disponibles"""
    DOWNLOAD = "download"
    DELETE = "delete"
    VALIDATE = "validate"
    UPDATE = "update"
    BACKUP = "backup"
    RESTORE = "restore"
    OPTIMIZE = "optimize"
    REPAIR = "repair"
    CLEANUP = "cleanup"

class ActionStatus(Enum):
    """Statuts d'exécution des actions"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class NotificationType(Enum):
    """Types de notifications"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    UPDATE_AVAILABLE = "update_available"
    DISK_SPACE_LOW = "disk_space_low"
    MODEL_CORRUPTED = "model_corrupted"

@dataclass
class ActionProgress:
    """Progression d'une action"""
    action_id: str
    action_type: ActionType
    status: ActionStatus
    progress_percent: float = 0.0
    current_step: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Durée de l'action"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def is_finished(self) -> bool:
        """Vérifie si l'action est terminée"""
        return self.status in [ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.CANCELLED]

@dataclass
class ModelNotification:
    """Notification liée aux modèles"""
    notification_id: str
    notification_type: NotificationType
    title: str
    message: str
    model_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    read: bool = False
    priority: int = 1  # 1=low, 2=medium, 3=high

@dataclass
class DownloadConfig:
    """Configuration de téléchargement"""
    url: str
    destination: str
    chunk_size: int = 8192
    timeout: int = 300
    max_retries: int = 3
    verify_checksum: bool = True
    expected_checksum: Optional[str] = None
    resume_download: bool = True
    headers: Dict[str, str] = field(default_factory=dict)

class ModelActionManager:
    """Gestionnaire d'actions avancées pour les modèles avec notifications"""
    
    def __init__(self, models_dir: str, backup_dir: str = ".kiro/model_backups"):
        self.models_dir = Path(models_dir)
        self.backup_dir = Path(backup_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Actions en cours
        self.active_actions: Dict[str, ActionProgress] = {}
        self.action_history: List[ActionProgress] = []
        self.action_lock = asyncio.Lock()
        
        # Système de notifications
        self.notifications: List[ModelNotification] = []
        self.notification_callbacks: List[Callable[[ModelNotification], None]] = []
        
        # Callbacks pour les événements
        self.progress_callbacks: List[Callable[[ActionProgress], None]] = []
        self.completion_callbacks: List[Callable[[str, bool], None]] = []
        
        # Configuration
        self.config = {
            "max_concurrent_actions": 3,
            "default_chunk_size": 8192,
            "default_timeout": 300,
            "auto_cleanup_history": True,
            "max_history_size": 100,
            "disk_space_threshold": 1024 * 1024 * 1024,  # 1GB
            "auto_repair_enabled": True,
            "notification_retention_days": 7
        }
        
        # Démarrer les tâches de surveillance
        self._monitoring_task = None
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Démarre les tâches de surveillance en arrière-plan"""
        if self._monitoring_task is None:
            try:
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            except RuntimeError:
                # Pas de boucle d'événements active, on démarre plus tard
                pass
    
    async def _monitoring_loop(self):
        """Boucle de surveillance pour les notifications automatiques"""
        while True:
            try:
                # Vérifier l'espace disque
                await self._check_disk_space()
                
                # Vérifier les modèles corrompus
                await self._check_model_integrity()
                
                # Vérifier les mises à jour disponibles
                await self._check_model_updates()
                
                # Nettoyer les anciennes notifications
                await self._cleanup_old_notifications()
                
                # Attendre 5 minutes avant la prochaine vérification
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    async def _check_disk_space(self):
        """Vérifie l'espace disque disponible"""
        try:
            disk_usage = shutil.disk_usage(self.models_dir)
            free_space = disk_usage.free
            
            if free_space < self.config["disk_space_threshold"]:
                # Créer une notification d'espace disque faible
                notification = ModelNotification(
                    notification_id=f"disk_space_{int(time.time())}",
                    notification_type=NotificationType.DISK_SPACE_LOW,
                    title="Espace disque faible",
                    message=f"Il ne reste que {self._format_bytes(free_space)} d'espace libre",
                    actions=["cleanup_old_models", "move_to_external_storage"],
                    priority=2,
                    metadata={"free_space": free_space, "threshold": self.config["disk_space_threshold"]}
                )
                
                await self._add_notification(notification)
                
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
    
    async def _check_model_integrity(self):
        """Vérifie l'intégrité des modèles"""
        try:
            for model_file in self.models_dir.rglob("*.bin"):
                if await self._is_model_corrupted(model_file):
                    notification = ModelNotification(
                        notification_id=f"corrupted_{model_file.stem}_{int(time.time())}",
                        notification_type=NotificationType.MODEL_CORRUPTED,
                        title="Modèle corrompu détecté",
                        message=f"Le modèle {model_file.name} semble être corrompu",
                        model_id=model_file.stem,
                        actions=["repair_model", "redownload_model", "delete_model"],
                        priority=3,
                        metadata={"file_path": str(model_file)}
                    )
                    
                    await self._add_notification(notification)
                    
        except Exception as e:
            logger.error(f"Error checking model integrity: {e}")
    
    async def _check_model_updates(self):
        """Vérifie les mises à jour disponibles pour les modèles"""
        try:
            # Simuler la vérification des mises à jour
            for model_file in self.models_dir.rglob("*.bin"):
                # Simuler une mise à jour disponible (1 chance sur 20)
                if hash(str(model_file)) % 20 == 0:
                    notification = ModelNotification(
                        notification_id=f"update_{model_file.stem}_{int(time.time())}",
                        notification_type=NotificationType.UPDATE_AVAILABLE,
                        title="Mise à jour disponible",
                        message=f"Une nouvelle version du modèle {model_file.name} est disponible",
                        model_id=model_file.stem,
                        actions=["download_update", "view_changelog"],
                        priority=1,
                        metadata={"current_version": "1.0", "new_version": "1.1"}
                    )
                    
                    await self._add_notification(notification)
                    
        except Exception as e:
            logger.error(f"Error checking model updates: {e}")
    
    async def _add_notification(self, notification: ModelNotification):
        """Ajoute une nouvelle notification"""
        # Vérifier si une notification similaire existe déjà
        existing = next(
            (n for n in self.notifications 
             if n.notification_type == notification.notification_type 
             and n.model_id == notification.model_id 
             and not n.read),
            None
        )
        
        if not existing:
            self.notifications.append(notification)
            
            # Notifier les callbacks
            for callback in self.notification_callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
            
            logger.info(f"New notification: {notification.title}")
    
    async def _cleanup_old_notifications(self):
        """Nettoie les anciennes notifications"""
        cutoff_time = time.time() - (self.config["notification_retention_days"] * 24 * 3600)
        
        self.notifications = [
            n for n in self.notifications 
            if n.timestamp > cutoff_time or not n.read
        ]
    
    async def _is_model_corrupted(self, model_path: Path) -> bool:
        """Vérifie si un modèle est corrompu"""
        try:
            # Vérifications basiques
            if not model_path.exists() or model_path.stat().st_size == 0:
                return True
            
            # Test de lecture des premiers bytes
            with open(model_path, 'rb') as f:
                header = f.read(1024)
                if len(header) < 100:  # Fichier trop petit
                    return True
            
            return False
            
        except Exception:
            return True 
   
    async def validate_model(self, model_id: str, file_path: str, 
                           expected_checksum: Optional[str] = None) -> str:
        """Valide l'intégrité d'un modèle"""
        
        action_id = f"validate_{model_id}_{int(time.time())}"
        
        progress = ActionProgress(
            action_id=action_id,
            action_type=ActionType.VALIDATE,
            status=ActionStatus.RUNNING,
            current_step="Démarrage de la validation",
            metadata={"model_id": model_id, "file_path": file_path}
        )
        
        async with self.action_lock:
            self.active_actions[action_id] = progress
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                raise Exception(f"Fichier non trouvé: {file_path}")
            
            # Vérifier la taille du fichier
            await self._update_progress(progress, 20, "Vérification de la taille")
            file_size = file_path_obj.stat().st_size
            
            if file_size == 0:
                raise Exception("Fichier vide")
            
            # Calculer le checksum
            await self._update_progress(progress, 40, "Calcul du checksum")
            actual_checksum = await self._calculate_file_checksum(file_path_obj)
            
            # Vérifier le checksum si fourni
            if expected_checksum:
                await self._update_progress(progress, 80, "Vérification du checksum")
                
                if actual_checksum != expected_checksum:
                    raise Exception(f"Checksum invalide: attendu {expected_checksum}, obtenu {actual_checksum}")
            
            # Test de lecture basique
            await self._update_progress(progress, 90, "Test de lecture")
            
            try:
                with open(file_path_obj, 'rb') as f:
                    f.read(1024)  # Lire les premiers 1KB
            except Exception as e:
                raise Exception(f"Erreur de lecture: {str(e)}")
            
            progress.status = ActionStatus.COMPLETED
            progress.end_time = time.time()
            progress.metadata["checksum"] = actual_checksum
            progress.metadata["file_size"] = file_size
            await self._update_progress(progress, 100, "Validation réussie")
            
            logger.info(f"Model {model_id} validated successfully")
            return action_id
            
        except Exception as e:
            progress.status = ActionStatus.FAILED
            progress.error_message = str(e)
            progress.end_time = time.time()
            await self._update_progress(progress, progress.progress_percent, f"Erreur: {str(e)}")
            
            logger.error(f"Validation failed for {model_id}: {e}")
            raise
        
        finally:
            await self._move_to_history(action_id)
    
    async def download_model(self, model_id: str, download_config: DownloadConfig,
                           progress_callback: Optional[Callable] = None) -> str:
        """Télécharge un modèle avec gestion avancée (simulation)"""
        
        action_id = f"download_{model_id}_{int(time.time())}"
        
        # Créer le suivi de progression
        progress = ActionProgress(
            action_id=action_id,
            action_type=ActionType.DOWNLOAD,
            status=ActionStatus.PENDING,
            current_step="Initialisation du téléchargement",
            metadata={
                "model_id": model_id,
                "url": download_config.url,
                "destination": download_config.destination
            }
        )
        
        async with self.action_lock:
            self.active_actions[action_id] = progress
        
        try:
            # Simulation d'un téléchargement
            progress.status = ActionStatus.RUNNING
            await self._update_progress(progress, 10, "Démarrage du téléchargement")
            
            # Simuler la progression
            for i in range(10, 100, 10):
                await asyncio.sleep(0.01)  # Petite pause pour la simulation
                await self._update_progress(progress, i, f"Téléchargement en cours... {i}%")
                
                if progress_callback:
                    await progress_callback(action_id, i, i * 1024, 100 * 1024)
            
            # Simuler une erreur pour les URLs fictives
            if "example.com" in download_config.url:
                raise Exception("URL fictive - téléchargement simulé échoué")
            
            progress.status = ActionStatus.COMPLETED
            progress.end_time = time.time()
            await self._update_progress(progress, 100, "Téléchargement terminé")
            
            logger.info(f"Model {model_id} download simulated successfully")
            return action_id
            
        except Exception as e:
            progress.status = ActionStatus.FAILED
            progress.error_message = str(e)
            progress.end_time = time.time()
            await self._update_progress(progress, progress.progress_percent, f"Erreur: {str(e)}")
            
            logger.error(f"Download failed for {model_id}: {e}")
            raise
        
        finally:
            await self._move_to_history(action_id)
    
    async def delete_model_intelligent(self, model_id: str, file_path: str) -> str:
        """Suppression intelligente avec suggestions basées sur l'usage"""
        
        action_id = f"delete_intelligent_{model_id}_{int(time.time())}"
        
        progress = ActionProgress(
            action_id=action_id,
            action_type=ActionType.DELETE,
            status=ActionStatus.RUNNING,
            current_step="Analyse de l'usage du modèle",
            metadata={"model_id": model_id, "file_path": file_path}
        )
        
        async with self.action_lock:
            self.active_actions[action_id] = progress
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                raise Exception(f"Fichier non trouvé: {file_path}")
            
            # Analyser l'usage du modèle
            await self._update_progress(progress, 20, "Analyse de l'usage")
            usage_stats = await self._analyze_model_usage(model_id)
            
            # Créer des suggestions basées sur l'usage
            suggestions = []
            if usage_stats["last_used_days"] < 7:
                suggestions.append("Modèle utilisé récemment - considérer garder")
            elif usage_stats["usage_frequency"] > 0.5:
                suggestions.append("Modèle fréquemment utilisé - recommandé de garder")
            else:
                suggestions.append("Modèle peu utilisé - suppression recommandée")
            
            # Créer une sauvegarde automatique
            await self._update_progress(progress, 40, "Création de la sauvegarde")
            backup_path = await self._create_automatic_backup(file_path_obj, model_id)
            
            # Supprimer le fichier
            await self._update_progress(progress, 70, "Suppression du fichier")
            file_path_obj.unlink()
            
            # Nettoyer les répertoires vides
            await self._update_progress(progress, 90, "Nettoyage des répertoires")
            await self._cleanup_empty_dirs(file_path_obj.parent)
            
            progress.status = ActionStatus.COMPLETED
            progress.end_time = time.time()
            progress.metadata.update({
                "usage_stats": usage_stats,
                "suggestions": suggestions,
                "backup_path": str(backup_path)
            })
            await self._update_progress(progress, 100, "Suppression intelligente terminée")
            
            # Notification avec suggestions
            notification = ModelNotification(
                notification_id=f"delete_success_{model_id}_{int(time.time())}",
                notification_type=NotificationType.SUCCESS,
                title="Modèle supprimé",
                message=f"Le modèle {model_id} a été supprimé. Sauvegarde créée.",
                model_id=model_id,
                actions=["restore_from_backup", "view_usage_stats"],
                priority=1,
                metadata={"backup_path": str(backup_path), "suggestions": suggestions}
            )
            await self._add_notification(notification)
            
            logger.info(f"Model {model_id} deleted intelligently")
            return action_id
            
        except Exception as e:
            progress.status = ActionStatus.FAILED
            progress.error_message = str(e)
            progress.end_time = time.time()
            await self._update_progress(progress, progress.progress_percent, f"Erreur: {str(e)}")
            
            logger.error(f"Intelligent delete failed for {model_id}: {e}")
            raise
        
        finally:
            await self._move_to_history(action_id)
    
    async def repair_model_automatic(self, model_id: str, file_path: str) -> str:
        """Réparation automatique des modèles endommagés"""
        
        action_id = f"repair_{model_id}_{int(time.time())}"
        
        progress = ActionProgress(
            action_id=action_id,
            action_type=ActionType.REPAIR,
            status=ActionStatus.RUNNING,
            current_step="Diagnostic du modèle",
            metadata={"model_id": model_id, "file_path": file_path}
        )
        
        async with self.action_lock:
            self.active_actions[action_id] = progress
        
        try:
            file_path_obj = Path(file_path)
            
            # Diagnostic approfondi
            await self._update_progress(progress, 20, "Diagnostic approfondi")
            diagnostic = await self._diagnose_model_corruption(file_path_obj)
            
            repair_success = False
            
            if diagnostic["corruption_type"] == "truncated":
                # Tentative de réparation par re-téléchargement partiel
                await self._update_progress(progress, 40, "Réparation par re-téléchargement")
                repair_success = await self._repair_by_partial_redownload(file_path_obj, diagnostic)
                
            elif diagnostic["corruption_type"] == "header_damaged":
                # Tentative de réparation d'en-tête
                await self._update_progress(progress, 40, "Réparation de l'en-tête")
                repair_success = await self._repair_header(file_path_obj, diagnostic)
                
            elif diagnostic["corruption_type"] == "checksum_mismatch":
                # Re-téléchargement complet
                await self._update_progress(progress, 40, "Re-téléchargement complet")
                repair_success = await self._repair_by_full_redownload(file_path_obj, model_id)
            
            if repair_success:
                # Vérification post-réparation
                await self._update_progress(progress, 80, "Vérification de la réparation")
                
                if not await self._is_model_corrupted(file_path_obj):
                    progress.status = ActionStatus.COMPLETED
                    progress.end_time = time.time()
                    await self._update_progress(progress, 100, "Réparation réussie")
                    
                    # Notification de succès
                    notification = ModelNotification(
                        notification_id=f"repair_success_{model_id}_{int(time.time())}",
                        notification_type=NotificationType.SUCCESS,
                        title="Modèle réparé",
                        message=f"Le modèle {model_id} a été réparé avec succès",
                        model_id=model_id,
                        priority=1,
                        metadata={"repair_method": diagnostic["corruption_type"]}
                    )
                    await self._add_notification(notification)
                    
                else:
                    raise Exception("La réparation a échoué - le modèle est toujours corrompu")
            else:
                raise Exception(f"Impossible de réparer le type de corruption: {diagnostic['corruption_type']}")
            
            logger.info(f"Model {model_id} repaired successfully")
            return action_id
            
        except Exception as e:
            progress.status = ActionStatus.FAILED
            progress.error_message = str(e)
            progress.end_time = time.time()
            await self._update_progress(progress, progress.progress_percent, f"Erreur: {str(e)}")
            
            # Notification d'échec avec suggestions
            notification = ModelNotification(
                notification_id=f"repair_failed_{model_id}_{int(time.time())}",
                notification_type=NotificationType.ERROR,
                title="Échec de la réparation",
                message=f"Impossible de réparer le modèle {model_id}: {str(e)}",
                model_id=model_id,
                actions=["redownload_model", "delete_corrupted_model", "contact_support"],
                priority=3
            )
            await self._add_notification(notification)
            
            logger.error(f"Repair failed for {model_id}: {e}")
            raise
        
        finally:
            await self._move_to_history(action_id)    
  
  # Méthodes utilitaires
    
    async def _update_progress(self, progress: ActionProgress, percent: float, step: str):
        """Met à jour la progression d'une action"""
        progress.progress_percent = percent
        progress.current_step = step
        
        # Notifier les callbacks
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    async def _move_to_history(self, action_id: str):
        """Déplace une action vers l'historique"""
        async with self.action_lock:
            if action_id in self.active_actions:
                action = self.active_actions.pop(action_id)
                self.action_history.append(action)
                
                # Limiter la taille de l'historique
                if len(self.action_history) > self.config["max_history_size"]:
                    self.action_history = self.action_history[-self.config["max_history_size"]:]
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calcule le checksum SHA256 d'un fichier"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _analyze_model_usage(self, model_id: str) -> Dict[str, Any]:
        """Analyse l'usage d'un modèle spécifique"""
        # Simulation - dans une vraie implémentation, cela lirait les logs d'usage
        return {
            "last_used_days": hash(model_id) % 60,  # 0-59 jours
            "usage_frequency": (hash(model_id) % 100) / 100,  # 0-1
            "total_usage_time": hash(model_id) % 3600,  # 0-3600 secondes
            "file_path": str(self.models_dir / f"{model_id}.bin")
        }
    
    async def _create_automatic_backup(self, file_path: Path, model_id: str) -> Path:
        """Crée une sauvegarde automatique d'un modèle"""
        backup_dir = self.backup_dir / f"auto_backup_{model_id}_{int(time.time())}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / file_path.name
        shutil.copy2(file_path, backup_file)
        
        # Créer les métadonnées
        metadata = {
            "original_path": str(file_path),
            "backup_time": time.time(),
            "model_id": model_id,
            "file_size": file_path.stat().st_size,
            "checksum": await self._calculate_file_checksum(file_path)
        }
        
        metadata_file = backup_dir / "backup_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return backup_file
    
    async def _cleanup_empty_dirs(self, directory: Path):
        """Nettoie les répertoires vides"""
        try:
            if directory.exists() and directory.is_dir():
                # Vérifier si le répertoire est vide
                if not any(directory.iterdir()):
                    directory.rmdir()
                    # Récursion pour nettoyer le parent si nécessaire
                    await self._cleanup_empty_dirs(directory.parent)
        except Exception as e:
            logger.debug(f"Could not remove directory {directory}: {e}")
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Formate une taille en bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    # Méthodes de diagnostic et réparation
    
    async def _diagnose_model_corruption(self, file_path: Path) -> Dict[str, Any]:
        """Diagnostic approfondi de la corruption d'un modèle"""
        diagnostic = {
            "corruption_type": "unknown",
            "severity": "low",
            "repairable": False,
            "details": {}
        }
        
        try:
            file_size = file_path.stat().st_size
            
            if file_size == 0:
                diagnostic.update({
                    "corruption_type": "empty_file",
                    "severity": "high",
                    "repairable": True
                })
                return diagnostic
            
            # Lire l'en-tête du fichier
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
                if len(header) < 100:
                    diagnostic.update({
                        "corruption_type": "truncated",
                        "severity": "high",
                        "repairable": True,
                        "details": {"actual_size": file_size, "expected_min_size": 1024}
                    })
                elif not self._is_valid_model_header(header):
                    diagnostic.update({
                        "corruption_type": "header_damaged",
                        "severity": "medium",
                        "repairable": True
                    })
                else:
                    diagnostic.update({
                        "corruption_type": "checksum_mismatch",
                        "severity": "low",
                        "repairable": True
                    })
        
        except Exception as e:
            diagnostic.update({
                "corruption_type": "read_error",
                "severity": "high",
                "repairable": False,
                "details": {"error": str(e)}
            })
        
        return diagnostic
    
    def _is_valid_model_header(self, header: bytes) -> bool:
        """Vérifie si l'en-tête d'un modèle est valide"""
        # Vérifications basiques pour différents formats de modèles
        magic_numbers = [
            b'GGML',  # GGML format
            b'GGUF',  # GGUF format
            b'PK\x03\x04',  # ZIP format (pour les modèles PyTorch)
            b'\x80\x02',  # Pickle format
        ]
        
        return any(header.startswith(magic) for magic in magic_numbers)
    
    async def _repair_by_partial_redownload(self, file_path: Path, diagnostic: Dict) -> bool:
        """Répare un fichier tronqué par re-téléchargement partiel"""
        # Simulation - dans une vraie implémentation, cela utiliserait l'URL originale
        logger.info(f"Simulating partial redownload repair for {file_path}")
        return True
    
    async def _repair_header(self, file_path: Path, diagnostic: Dict) -> bool:
        """Répare l'en-tête d'un fichier endommagé"""
        # Simulation - dans une vraie implémentation, cela tenterait de reconstruire l'en-tête
        logger.info(f"Simulating header repair for {file_path}")
        return True
    
    async def _repair_by_full_redownload(self, file_path: Path, model_id: str) -> bool:
        """Répare par re-téléchargement complet"""
        # Simulation - dans une vraie implémentation, cela re-téléchargerait le modèle
        logger.info(f"Simulating full redownload repair for {model_id}")
        return True
    
    # API publique pour les notifications
    
    def get_notifications(self, unread_only: bool = False) -> List[ModelNotification]:
        """Récupère les notifications"""
        if unread_only:
            return [n for n in self.notifications if not n.read]
        return self.notifications.copy()
    
    def mark_notification_read(self, notification_id: str):
        """Marque une notification comme lue"""
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.read = True
                break
    
    def add_notification_callback(self, callback: Callable[[ModelNotification], None]):
        """Ajoute un callback pour les nouvelles notifications"""
        self.notification_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable[[ActionProgress], None]):
        """Ajoute un callback pour les mises à jour de progression"""
        self.progress_callbacks.append(callback)
    
    def get_active_actions(self) -> List[ActionProgress]:
        """Récupère les actions en cours"""
        return list(self.active_actions.values())
    
    def get_action_history(self, limit: int = 50) -> List[ActionProgress]:
        """Récupère l'historique des actions"""
        return self.action_history[-limit:]
    
    async def cancel_action(self, action_id: str) -> bool:
        """Annule une action en cours"""
        async with self.action_lock:
            if action_id in self.active_actions:
                action = self.active_actions[action_id]
                action.status = ActionStatus.CANCELLED
                action.end_time = time.time()
                await self._move_to_history(action_id)
                return True
        return False
    
    async def close(self):
        """Ferme le gestionnaire et nettoie les ressources"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass