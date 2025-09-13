"""Système de notifications avancées pour la gestion des modèles"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from .model_actions import ModelNotification, NotificationType

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """Priorités des notifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class NotificationCategory(Enum):
    """Catégories de notifications"""
    SYSTEM = "system"
    MODEL_MANAGEMENT = "model_management"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UPDATE = "update"
    ERROR = "error"

@dataclass
class NotificationRule:
    """Règle de notification"""
    rule_id: str
    name: str
    description: str
    condition: str  # Expression à évaluer
    notification_template: Dict[str, Any]
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes par défaut
    last_triggered: float = 0
    trigger_count: int = 0

@dataclass
class NotificationChannel:
    """Canal de notification"""
    channel_id: str
    name: str
    channel_type: str  # "ui", "email", "webhook", "file"
    config: Dict[str, Any]
    enabled: bool = True
    priority_filter: Set[NotificationPriority] = field(default_factory=lambda: {NotificationPriority.MEDIUM, NotificationPriority.HIGH, NotificationPriority.CRITICAL})

class SmartNotificationManager:
    """Gestionnaire de notifications intelligent avec règles et filtres"""
    
    def __init__(self, config_file: str = ".kiro/notifications_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Stockage des notifications
        self.notifications: List[ModelNotification] = []
        self.notification_rules: Dict[str, NotificationRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        
        # Callbacks et handlers
        self.notification_handlers: Dict[str, Callable] = {}
        self.global_callbacks: List[Callable[[ModelNotification], None]] = []
        
        # Configuration
        self.config = {
            "max_notifications": 1000,
            "auto_cleanup_days": 30,
            "batch_notifications": True,
            "batch_interval_seconds": 60,
            "enable_smart_grouping": True,
            "enable_priority_escalation": True
        }
        
        # État interne
        self.notification_lock = asyncio.Lock()
        self.pending_batch: List[ModelNotification] = []
        self.batch_task: Optional[asyncio.Task] = None
        
        # Charger la configuration
        self._load_config()
        self._setup_default_rules()
        self._setup_default_channels()
        
        # Démarrer les tâches de traitement
        self._start_background_tasks()
    
    def _load_config(self):
        """Charge la configuration depuis le fichier"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config.get('config', {}))
                    
                    # Charger les règles
                    for rule_data in saved_config.get('rules', []):
                        rule = NotificationRule(**rule_data)
                        self.notification_rules[rule.rule_id] = rule
                    
                    # Charger les canaux
                    for channel_data in saved_config.get('channels', []):
                        channel_data['priority_filter'] = {
                            NotificationPriority(p) for p in channel_data.get('priority_filter', [2, 3, 4])
                        }
                        channel = NotificationChannel(**channel_data)
                        self.notification_channels[channel.channel_id] = channel
                        
            except Exception as e:
                logger.error(f"Error loading notification config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration dans le fichier"""
        try:
            config_data = {
                'config': self.config,
                'rules': [
                    {
                        'rule_id': rule.rule_id,
                        'name': rule.name,
                        'description': rule.description,
                        'condition': rule.condition,
                        'notification_template': rule.notification_template,
                        'enabled': rule.enabled,
                        'cooldown_seconds': rule.cooldown_seconds,
                        'last_triggered': rule.last_triggered,
                        'trigger_count': rule.trigger_count
                    }
                    for rule in self.notification_rules.values()
                ],
                'channels': [
                    {
                        'channel_id': channel.channel_id,
                        'name': channel.name,
                        'channel_type': channel.channel_type,
                        'config': channel.config,
                        'enabled': channel.enabled,
                        'priority_filter': [p.value for p in channel.priority_filter]
                    }
                    for channel in self.notification_channels.values()
                ]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving notification config: {e}")
    
    def _setup_default_rules(self):
        """Configure les règles de notification par défaut"""
        
        default_rules = [
            NotificationRule(
                rule_id="disk_space_critical",
                name="Espace disque critique",
                description="Alerte quand l'espace disque est très faible",
                condition="free_space < 500MB",
                notification_template={
                    "type": NotificationType.DISK_SPACE_LOW,
                    "title": "Espace disque critique",
                    "message": "Moins de 500MB d'espace libre disponible",
                    "priority": NotificationPriority.CRITICAL.value,
                    "actions": ["cleanup_models", "move_to_external", "expand_storage"]
                },
                cooldown_seconds=1800  # 30 minutes
            ),
            
            NotificationRule(
                rule_id="model_corruption_detected",
                name="Modèle corrompu détecté",
                description="Alerte quand un modèle corrompu est détecté",
                condition="corruption_detected == True",
                notification_template={
                    "type": NotificationType.MODEL_CORRUPTED,
                    "title": "Modèle corrompu détecté",
                    "message": "Un modèle corrompu a été détecté et nécessite une attention",
                    "priority": NotificationPriority.HIGH.value,
                    "actions": ["repair_model", "redownload_model", "quarantine_model"]
                },
                cooldown_seconds=600  # 10 minutes
            ),
            
            NotificationRule(
                rule_id="multiple_download_failures",
                name="Échecs de téléchargement multiples",
                description="Alerte après plusieurs échecs de téléchargement",
                condition="download_failures >= 3",
                notification_template={
                    "type": NotificationType.ERROR,
                    "title": "Échecs de téléchargement répétés",
                    "message": "Plusieurs téléchargements ont échoué récemment",
                    "priority": NotificationPriority.MEDIUM.value,
                    "actions": ["check_connection", "check_storage", "retry_downloads"]
                },
                cooldown_seconds=3600  # 1 heure
            ),
            
            NotificationRule(
                rule_id="model_update_available",
                name="Mise à jour de modèle disponible",
                description="Notification quand une mise à jour est disponible",
                condition="update_available == True",
                notification_template={
                    "type": NotificationType.UPDATE_AVAILABLE,
                    "title": "Mise à jour disponible",
                    "message": "Une nouvelle version d'un modèle est disponible",
                    "priority": NotificationPriority.LOW.value,
                    "actions": ["download_update", "view_changelog", "schedule_update"]
                },
                cooldown_seconds=86400  # 24 heures
            )
        ]
        
        for rule in default_rules:
            if rule.rule_id not in self.notification_rules:
                self.notification_rules[rule.rule_id] = rule
    
    def _setup_default_channels(self):
        """Configure les canaux de notification par défaut"""
        
        default_channels = [
            NotificationChannel(
                channel_id="ui_notifications",
                name="Interface utilisateur",
                channel_type="ui",
                config={"show_toast": True, "show_in_panel": True},
                enabled=True,
                priority_filter={NotificationPriority.LOW, NotificationPriority.MEDIUM, NotificationPriority.HIGH, NotificationPriority.CRITICAL}
            ),
            
            NotificationChannel(
                channel_id="log_file",
                name="Fichier de log",
                channel_type="file",
                config={"file_path": ".kiro/logs/notifications.log", "format": "json"},
                enabled=True,
                priority_filter={NotificationPriority.MEDIUM, NotificationPriority.HIGH, NotificationPriority.CRITICAL}
            ),
            
            NotificationChannel(
                channel_id="critical_alerts",
                name="Alertes critiques",
                channel_type="ui",
                config={"modal_popup": True, "require_acknowledgment": True},
                enabled=True,
                priority_filter={NotificationPriority.CRITICAL}
            )
        ]
        
        for channel in default_channels:
            if channel.channel_id not in self.notification_channels:
                self.notification_channels[channel.channel_id] = channel
    
    def _start_background_tasks(self):
        """Démarre les tâches de traitement en arrière-plan"""
        try:
            if self.config["batch_notifications"]:
                self.batch_task = asyncio.create_task(self._batch_processing_loop())
        except RuntimeError:
            # Pas de boucle d'événements active
            pass
    
    async def _batch_processing_loop(self):
        """Boucle de traitement par lots des notifications"""
        while True:
            try:
                await asyncio.sleep(self.config["batch_interval_seconds"])
                
                if self.pending_batch:
                    async with self.notification_lock:
                        batch_to_process = self.pending_batch.copy()
                        self.pending_batch.clear()
                    
                    await self._process_notification_batch(batch_to_process)
                
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    async def _process_notification_batch(self, notifications: List[ModelNotification]):
        """Traite un lot de notifications"""
        
        if self.config["enable_smart_grouping"]:
            grouped_notifications = self._group_similar_notifications(notifications)
        else:
            grouped_notifications = {"ungrouped": notifications}
        
        for group_name, group_notifications in grouped_notifications.items():
            if len(group_notifications) > 1:
                # Créer une notification groupée
                summary_notification = self._create_summary_notification(group_name, group_notifications)
                await self._send_notification(summary_notification)
            else:
                # Envoyer la notification individuelle
                await self._send_notification(group_notifications[0])
    
    def _group_similar_notifications(self, notifications: List[ModelNotification]) -> Dict[str, List[ModelNotification]]:
        """Groupe les notifications similaires"""
        groups = {}
        
        for notification in notifications:
            # Grouper par type et modèle
            group_key = f"{notification.notification_type.value}_{notification.model_id or 'system'}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(notification)
        
        return groups
    
    def _create_summary_notification(self, group_name: str, notifications: List[ModelNotification]) -> ModelNotification:
        """Crée une notification de résumé pour un groupe"""
        
        first_notification = notifications[0]
        count = len(notifications)
        
        return ModelNotification(
            notification_id=f"summary_{group_name}_{int(time.time())}",
            notification_type=first_notification.notification_type,
            title=f"{first_notification.title} ({count} éléments)",
            message=f"{count} notifications similaires: {first_notification.message}",
            model_id=first_notification.model_id,
            actions=first_notification.actions,
            priority=max(n.priority for n in notifications),
            metadata={
                "is_summary": True,
                "grouped_notifications": [n.notification_id for n in notifications],
                "group_count": count
            }
        )
    
    async def add_notification(self, notification: ModelNotification):
        """Ajoute une nouvelle notification au système"""
        
        # Vérifier les règles de déduplication
        if await self._should_deduplicate(notification):
            logger.debug(f"Notification deduplicated: {notification.title}")
            return
        
        # Appliquer l'escalade de priorité si activée
        if self.config["enable_priority_escalation"]:
            notification = await self._apply_priority_escalation(notification)
        
        async with self.notification_lock:
            self.notifications.append(notification)
            
            # Limiter le nombre de notifications
            if len(self.notifications) > self.config["max_notifications"]:
                self.notifications = self.notifications[-self.config["max_notifications"]:]
        
        # Traitement immédiat ou par lot
        if self.config["batch_notifications"] and notification.priority < NotificationPriority.CRITICAL.value:
            self.pending_batch.append(notification)
        else:
            await self._send_notification(notification)
        
        # Déclencher les callbacks globaux
        for callback in self.global_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error in global notification callback: {e}")
    
    async def _should_deduplicate(self, notification: ModelNotification) -> bool:
        """Vérifie si une notification doit être dédupliquée"""
        
        # Chercher des notifications similaires récentes (dernières 5 minutes)
        cutoff_time = time.time() - 300
        
        for existing in self.notifications:
            if (existing.timestamp > cutoff_time and
                existing.notification_type == notification.notification_type and
                existing.model_id == notification.model_id and
                existing.title == notification.title):
                return True
        
        return False
    
    async def _apply_priority_escalation(self, notification: ModelNotification) -> ModelNotification:
        """Applique l'escalade de priorité basée sur l'historique"""
        
        # Compter les notifications similaires récentes
        similar_count = 0
        cutoff_time = time.time() - 3600  # Dernière heure
        
        for existing in self.notifications:
            if (existing.timestamp > cutoff_time and
                existing.notification_type == notification.notification_type and
                existing.model_id == notification.model_id):
                similar_count += 1
        
        # Escalader la priorité si nécessaire
        if similar_count >= 5 and notification.priority < NotificationPriority.HIGH.value:
            notification.priority = NotificationPriority.HIGH.value
            notification.message += f" (Escaladé - {similar_count} occurrences récentes)"
        elif similar_count >= 10 and notification.priority < NotificationPriority.CRITICAL.value:
            notification.priority = NotificationPriority.CRITICAL.value
            notification.message += f" (Critique - {similar_count} occurrences récentes)"
        
        return notification
    
    async def _send_notification(self, notification: ModelNotification):
        """Envoie une notification via tous les canaux appropriés"""
        
        notification_priority = NotificationPriority(notification.priority)
        
        for channel in self.notification_channels.values():
            if (channel.enabled and 
                notification_priority in channel.priority_filter):
                
                try:
                    await self._send_to_channel(notification, channel)
                except Exception as e:
                    logger.error(f"Error sending notification to channel {channel.channel_id}: {e}")
    
    async def _send_to_channel(self, notification: ModelNotification, channel: NotificationChannel):
        """Envoie une notification à un canal spécifique"""
        
        if channel.channel_type == "ui":
            await self._send_to_ui_channel(notification, channel)
        elif channel.channel_type == "file":
            await self._send_to_file_channel(notification, channel)
        elif channel.channel_type == "webhook":
            await self._send_to_webhook_channel(notification, channel)
        else:
            logger.warning(f"Unknown channel type: {channel.channel_type}")
    
    async def _send_to_ui_channel(self, notification: ModelNotification, channel: NotificationChannel):
        """Envoie une notification au canal UI"""
        
        # Appeler les handlers UI enregistrés
        if "ui" in self.notification_handlers:
            await self.notification_handlers["ui"](notification, channel.config)
        else:
            # Log par défaut si pas de handler UI
            logger.info(f"UI Notification: {notification.title} - {notification.message}")
    
    async def _send_to_file_channel(self, notification: ModelNotification, channel: NotificationChannel):
        """Envoie une notification au canal fichier"""
        
        log_file = Path(channel.config.get("file_path", ".kiro/logs/notifications.log"))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": notification.timestamp,
            "id": notification.notification_id,
            "type": notification.notification_type.value,
            "title": notification.title,
            "message": notification.message,
            "model_id": notification.model_id,
            "priority": notification.priority,
            "actions": notification.actions,
            "metadata": notification.metadata
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    async def _send_to_webhook_channel(self, notification: ModelNotification, channel: NotificationChannel):
        """Envoie une notification au canal webhook"""
        
        # Implémentation webhook (nécessiterait aiohttp)
        webhook_url = channel.config.get("url")
        if webhook_url:
            logger.info(f"Would send webhook to {webhook_url}: {notification.title}")
    
    # API publique
    
    def register_notification_handler(self, channel_type: str, handler: Callable):
        """Enregistre un handler pour un type de canal"""
        self.notification_handlers[channel_type] = handler
    
    def add_global_callback(self, callback: Callable[[ModelNotification], None]):
        """Ajoute un callback global pour toutes les notifications"""
        self.global_callbacks.append(callback)
    
    def get_notifications(self, 
                         unread_only: bool = False,
                         priority_filter: Optional[List[NotificationPriority]] = None,
                         type_filter: Optional[List[NotificationType]] = None,
                         limit: int = 100) -> List[ModelNotification]:
        """Récupère les notifications avec filtres"""
        
        notifications = self.notifications.copy()
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        if priority_filter:
            priority_values = [p.value for p in priority_filter]
            notifications = [n for n in notifications if n.priority in priority_values]
        
        if type_filter:
            notifications = [n for n in notifications if n.notification_type in type_filter]
        
        # Trier par priorité puis par timestamp (plus récentes d'abord)
        notifications.sort(key=lambda n: (-n.priority, -n.timestamp))
        
        return notifications[:limit]
    
    def mark_notification_read(self, notification_id: str):
        """Marque une notification comme lue"""
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.read = True
                break
    
    def mark_all_read(self, notification_type: Optional[NotificationType] = None):
        """Marque toutes les notifications comme lues"""
        for notification in self.notifications:
            if notification_type is None or notification.notification_type == notification_type:
                notification.read = True
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques des notifications"""
        
        total = len(self.notifications)
        unread = len([n for n in self.notifications if not n.read])
        
        by_type = {}
        by_priority = {}
        
        for notification in self.notifications:
            # Par type
            type_key = notification.notification_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # Par priorité
            priority_key = f"priority_{notification.priority}"
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        
        return {
            "total": total,
            "unread": unread,
            "by_type": by_type,
            "by_priority": by_priority,
            "active_rules": len([r for r in self.notification_rules.values() if r.enabled]),
            "active_channels": len([c for c in self.notification_channels.values() if c.enabled])
        }
    
    async def cleanup_old_notifications(self):
        """Nettoie les anciennes notifications"""
        cutoff_time = time.time() - (self.config["auto_cleanup_days"] * 24 * 3600)
        
        async with self.notification_lock:
            self.notifications = [
                n for n in self.notifications 
                if n.timestamp > cutoff_time or not n.read
            ]
    
    async def close(self):
        """Ferme le gestionnaire et sauvegarde la configuration"""
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        self._save_config()
        logger.info("Smart notification manager closed")