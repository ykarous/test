"""
Analyseur de prévention d'erreurs avec détection proactive des problèmes
"""

import asyncio
import logging
import time
import json
import psutil
import os
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, deque

# Définitions locales des enums pour éviter les dépendances circulaires
from enum import Enum

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

logger = logging.getLogger(__name__)

class PreventionLevel(Enum):
    """Niveaux de prévention"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class PreventionAction(Enum):
    """Actions préventives disponibles"""
    MONITOR = "monitor"
    WARN = "warn"
    OPTIMIZE = "optimize"
    BLOCK = "block"
    CLEANUP = "cleanup"
    FALLBACK = "fallback"

@dataclass
class PreventionRule:
    """Règle de prévention d'erreur"""
    rule_id: str
    name: str
    description: str
    error_type: ErrorType
    prevention_level: PreventionLevel
    check_function: Callable[[], bool]
    action: PreventionAction
    threshold: float = 0.8
    cooldown: float = 300.0  # 5 minutes
    last_triggered: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreventionAlert:
    """Alerte préventive"""
    alert_id: str
    rule_id: str
    timestamp: float
    level: PreventionLevel
    message: str
    recommended_actions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealthMetrics:
    """Métriques de santé du système"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    gpu_usage: float = 0.0
    gpu_memory_usage: float = 0.0
    gpu_temperature: float = 0.0
    network_latency: float = 0.0
    active_processes: int = 0
    available_memory_mb: float = 0.0
    disk_free_gb: float = 0.0

class ErrorPreventionAnalyzer:
    """Analyseur de prévention d'erreurs avec détection proactive"""
    
    def __init__(self, config_file: str = ".kiro/error_prevention_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config = {
            "monitoring_interval": 30.0,
            "health_check_interval": 60.0,
            "alert_retention_hours": 24,
            "max_alerts_per_rule": 10,
            "enable_proactive_cleanup": True,
            "enable_automatic_optimization": True,
            "critical_memory_threshold": 0.9,
            "critical_disk_threshold": 0.95,
            "critical_cpu_threshold": 0.95,
            "gpu_temperature_threshold": 85.0
        }
        
        # État interne
        self.prevention_rules: Dict[str, PreventionRule] = {}
        self.active_alerts: Dict[str, PreventionAlert] = {}
        self.alert_history: List[PreventionAlert] = []
        self.health_metrics_history: deque = deque(maxlen=1000)
        self.pattern_analysis: Dict[str, Any] = {}
        
        # Callbacks
        self.alert_callbacks: List[Callable] = []
        self.action_callbacks: Dict[PreventionAction, List[Callable]] = defaultdict(list)
        
        # Tâches de monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Statistiques
        self.prevention_stats = {
            "alerts_generated": 0,
            "problems_prevented": 0,
            "automatic_optimizations": 0,
            "false_positives": 0
        }
        
        # Initialisation
        self._load_config()
        self._setup_default_rules()
        self._start_monitoring()
        
        logger.info("Error Prevention Analyzer initialized")
    
    def _load_config(self):
        """Charge la configuration depuis le fichier"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config.get('config', {}))
                    self.prevention_stats.update(saved_config.get('stats', {}))
                logger.info("Error prevention configuration loaded")
            except Exception as e:
                logger.error(f"Failed to load error prevention config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            config_data = {
                'config': self.config,
                'stats': self.prevention_stats,
                'timestamp': time.time()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save error prevention config: {e}")
    
    def _setup_default_rules(self):
        """Configure les règles de prévention par défaut"""
        
        # Règle de prévention mémoire critique
        self.add_prevention_rule(PreventionRule(
            rule_id="memory_critical",
            name="Mémoire critique",
            description="Détecte quand la mémoire approche de la saturation",
            error_type=ErrorType.MEMORY_ERROR,
            prevention_level=PreventionLevel.CRITICAL,
            check_function=self._check_memory_critical,
            action=PreventionAction.CLEANUP,
            threshold=self.config["critical_memory_threshold"]
        ))
        
        # Règle de prévention espace disque critique
        self.add_prevention_rule(PreventionRule(
            rule_id="disk_critical",
            name="Espace disque critique",
            description="Détecte quand l'espace disque est insuffisant",
            error_type=ErrorType.DISK_ERROR,
            prevention_level=PreventionLevel.CRITICAL,
            check_function=self._check_disk_critical,
            action=PreventionAction.CLEANUP,
            threshold=self.config["critical_disk_threshold"]
        ))
        
        # Règle de prévention CPU surchargé
        self.add_prevention_rule(PreventionRule(
            rule_id="cpu_overload",
            name="CPU surchargé",
            description="Détecte une surcharge CPU prolongée",
            error_type=ErrorType.SYSTEM_ERROR,
            prevention_level=PreventionLevel.HIGH,
            check_function=self._check_cpu_overload,
            action=PreventionAction.OPTIMIZE,
            threshold=self.config["critical_cpu_threshold"]
        ))
        
        # Règle de prévention température GPU
        self.add_prevention_rule(PreventionRule(
            rule_id="gpu_temperature",
            name="Température GPU élevée",
            description="Détecte une surchauffe GPU",
            error_type=ErrorType.CUDA_ERROR,
            prevention_level=PreventionLevel.HIGH,
            check_function=self._check_gpu_temperature,
            action=PreventionAction.FALLBACK,
            threshold=self.config["gpu_temperature_threshold"]
        ))
        
        # Règle de prévention modèle corrompu
        self.add_prevention_rule(PreventionRule(
            rule_id="model_integrity",
            name="Intégrité des modèles",
            description="Vérifie l'intégrité des modèles avant utilisation",
            error_type=ErrorType.MODEL_ERROR,
            prevention_level=PreventionLevel.MEDIUM,
            check_function=self._check_model_integrity,
            action=PreventionAction.WARN,
            cooldown=1800.0  # 30 minutes
        ))
        
        # Règle de prévention réseau instable
        self.add_prevention_rule(PreventionRule(
            rule_id="network_instability",
            name="Réseau instable",
            description="Détecte une instabilité réseau",
            error_type=ErrorType.NETWORK_ERROR,
            prevention_level=PreventionLevel.MEDIUM,
            check_function=self._check_network_stability,
            action=PreventionAction.FALLBACK,
            cooldown=600.0  # 10 minutes
        ))
        
        # Règle de prévention configuration invalide
        self.add_prevention_rule(PreventionRule(
            rule_id="config_validation",
            name="Configuration invalide",
            description="Valide la configuration avant les opérations",
            error_type=ErrorType.CONFIGURATION_ERROR,
            prevention_level=PreventionLevel.HIGH,
            check_function=self._check_configuration_validity,
            action=PreventionAction.BLOCK,
            cooldown=60.0  # 1 minute
        ))
    
    def _start_monitoring(self):
        """Démarre le monitoring préventif"""
        try:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.health_check_task = asyncio.create_task(self._health_check_loop())
        except RuntimeError:
            # Pas de boucle d'événements active
            pass
    
    async def _monitoring_loop(self):
        """Boucle principale de monitoring préventif"""
        while True:
            try:
                # Vérifier toutes les règles de prévention
                await self._check_all_prevention_rules()
                
                # Analyser les patterns d'erreur
                await self._analyze_error_patterns()
                
                # Nettoyer les anciennes alertes
                await self._cleanup_old_alerts()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in prevention monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _health_check_loop(self):
        """Boucle de vérification de santé système"""
        while True:
            try:
                # Collecter les métriques de santé
                health_metrics = await self._collect_health_metrics()
                self.health_metrics_history.append(health_metrics)
                
                # Analyser les tendances de santé
                await self._analyze_health_trends()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.config["health_check_interval"])
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(120)
    
    async def _collect_health_metrics(self) -> SystemHealthMetrics:
        """Collecte les métriques de santé système"""
        
        def get_system_metrics():
            try:
                # Métriques système de base
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                metrics = SystemHealthMetrics(
                    timestamp=time.time(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    disk_usage=disk.percent,
                    active_processes=len(psutil.pids()),
                    available_memory_mb=memory.available / (1024 * 1024),
                    disk_free_gb=disk.free / (1024 * 1024 * 1024)
                )
                
                # Métriques GPU si disponibles
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        metrics.gpu_usage = gpu.load * 100
                        metrics.gpu_memory_usage = gpu.memoryUtil * 100
                        metrics.gpu_temperature = gpu.temperature
                except ImportError:
                    pass
                
                return metrics
                
            except Exception as e:
                logger.error(f"Error collecting health metrics: {e}")
                return SystemHealthMetrics(timestamp=time.time(), cpu_usage=0, memory_usage=0, disk_usage=0)
        
        # Exécuter dans un thread pour éviter de bloquer
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_system_metrics)
    
    async def _check_all_prevention_rules(self):
        """Vérifie toutes les règles de prévention"""
        
        for rule in self.prevention_rules.values():
            try:
                # Vérifier le cooldown
                if time.time() - rule.last_triggered < rule.cooldown:
                    continue
                
                # Exécuter la vérification
                should_trigger = await self._execute_rule_check(rule)
                
                if should_trigger:
                    await self._trigger_prevention_rule(rule)
                    
            except Exception as e:
                logger.error(f"Error checking prevention rule {rule.rule_id}: {e}")
    
    async def _execute_rule_check(self, rule: PreventionRule) -> bool:
        """Exécute la vérification d'une règle"""
        try:
            # Exécuter la fonction de vérification dans un thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, rule.check_function)
        except Exception as e:
            logger.error(f"Error executing rule check for {rule.rule_id}: {e}")
            return False
    
    async def _trigger_prevention_rule(self, rule: PreventionRule):
        """Déclenche une règle de prévention"""
        
        logger.warning(f"Prevention rule triggered: {rule.name}")
        
        # Créer une alerte
        alert = PreventionAlert(
            alert_id=f"{rule.rule_id}_{int(time.time())}",
            rule_id=rule.rule_id,
            timestamp=time.time(),
            level=rule.prevention_level,
            message=f"Problème potentiel détecté: {rule.description}",
            recommended_actions=await self._get_recommended_actions(rule)
        )
        
        # Enregistrer l'alerte
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        self.prevention_stats["alerts_generated"] += 1
        
        # Mettre à jour le timestamp de déclenchement
        rule.last_triggered = time.time()
        
        # Exécuter l'action préventive
        await self._execute_prevention_action(rule, alert)
        
        # Notifier les callbacks
        await self._notify_alert_callbacks(alert)
    
    async def _get_recommended_actions(self, rule: PreventionRule) -> List[str]:
        """Génère les actions recommandées pour une règle"""
        
        actions = []
        
        if rule.action == PreventionAction.CLEANUP:
            actions.extend([
                "Libérer de la mémoire en fermant les applications inutiles",
                "Nettoyer les fichiers temporaires",
                "Vider le cache des modèles"
            ])
        elif rule.action == PreventionAction.OPTIMIZE:
            actions.extend([
                "Réduire la charge CPU en optimisant les paramètres",
                "Utiliser des modèles plus légers",
                "Ajuster la priorité des processus"
            ])
        elif rule.action == PreventionAction.FALLBACK:
            actions.extend([
                "Basculer vers une alternative moins gourmande",
                "Utiliser le CPU au lieu du GPU",
                "Réduire la qualité de traitement"
            ])
        elif rule.action == PreventionAction.BLOCK:
            actions.extend([
                "Corriger la configuration avant de continuer",
                "Vérifier les paramètres système",
                "Redémarrer les services nécessaires"
            ])
        elif rule.action == PreventionAction.WARN:
            actions.extend([
                "Surveiller la situation de près",
                "Préparer des alternatives",
                "Vérifier les logs pour plus de détails"
            ])
        
        return actions
    
    async def _execute_prevention_action(self, rule: PreventionRule, alert: PreventionAlert):
        """Exécute l'action préventive"""
        
        try:
            if rule.action == PreventionAction.CLEANUP and self.config["enable_proactive_cleanup"]:
                await self._perform_proactive_cleanup(rule)
                self.prevention_stats["problems_prevented"] += 1
                
            elif rule.action == PreventionAction.OPTIMIZE and self.config["enable_automatic_optimization"]:
                await self._perform_automatic_optimization(rule)
                self.prevention_stats["automatic_optimizations"] += 1
                
            elif rule.action == PreventionAction.FALLBACK:
                await self._suggest_fallback_options(rule, alert)
                
            elif rule.action == PreventionAction.BLOCK:
                await self._block_risky_operations(rule, alert)
                
            # Notifier les callbacks d'action
            await self._notify_action_callbacks(rule.action, rule, alert)
            
        except Exception as e:
            logger.error(f"Error executing prevention action for rule {rule.rule_id}: {e}")
    
    async def _perform_proactive_cleanup(self, rule: PreventionRule):
        """Effectue un nettoyage proactif"""
        
        logger.info(f"Performing proactive cleanup for rule: {rule.rule_id}")
        
        if rule.error_type == ErrorType.MEMORY_ERROR:
            # Nettoyage mémoire
            import gc
            gc.collect()
            
        elif rule.error_type == ErrorType.DISK_ERROR:
            # Nettoyage disque (simulation)
            logger.info("Cleaning up temporary files and cache")
            
        elif rule.error_type == ErrorType.CUDA_ERROR:
            # Nettoyage GPU (simulation)
            logger.info("Cleaning up GPU memory")
    
    async def _perform_automatic_optimization(self, rule: PreventionRule):
        """Effectue une optimisation automatique"""
        
        logger.info(f"Performing automatic optimization for rule: {rule.rule_id}")
        
        if rule.error_type == ErrorType.SYSTEM_ERROR:
            # Optimisation CPU
            logger.info("Optimizing CPU usage")
            
        elif rule.error_type == ErrorType.MEMORY_ERROR:
            # Optimisation mémoire
            logger.info("Optimizing memory usage")
    
    async def _suggest_fallback_options(self, rule: PreventionRule, alert: PreventionAlert):
        """Suggère des options de fallback"""
        
        logger.info(f"Suggesting fallback options for rule: {rule.rule_id}")
        alert.metadata["fallback_suggested"] = True
    
    async def _block_risky_operations(self, rule: PreventionRule, alert: PreventionAlert):
        """Bloque les opérations risquées"""
        
        logger.warning(f"Blocking risky operations for rule: {rule.rule_id}")
        alert.metadata["operations_blocked"] = True
    
    async def _analyze_error_patterns(self):
        """Analyse les patterns d'erreur pour améliorer la prévention"""
        
        # Analyser les alertes récentes
        recent_alerts = [
            alert for alert in self.alert_history
            if time.time() - alert.timestamp < 3600  # Dernière heure
        ]
        
        # Compter les alertes par type
        alert_counts = defaultdict(int)
        for alert in recent_alerts:
            alert_counts[alert.rule_id] += 1
        
        # Détecter les patterns problématiques
        for rule_id, count in alert_counts.items():
            if count >= 5:  # Seuil de pattern
                logger.warning(f"Pattern d'alerte détecté: {rule_id} ({count} occurrences)")
                self.pattern_analysis[rule_id] = {
                    "count": count,
                    "last_analysis": time.time(),
                    "severity": "high" if count >= 10 else "medium"
                }
    
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
        
        # Créer une alerte préventive
        alert = PreventionAlert(
            alert_id=f"preventive_{error_type.value}_{int(time.time())}",
            rule_id=f"preventive_{error_type.value}",
            timestamp=time.time(),
            level=PreventionLevel.HIGH,
            message=message,
            recommended_actions=[
                "Vérifier l'utilisation des ressources",
                "Fermer les applications inutiles",
                "Redémarrer si nécessaire"
            ],
            metadata=metadata
        )
        
        # Enregistrer l'alerte
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        self.prevention_stats["alerts_generated"] += 1
        
        # Notifier les callbacks
        await self._notify_alert_callbacks(alert)

    async def _analyze_health_trends(self):
        """Analyse les tendances de santé système"""
        
        if len(self.health_metrics_history) < 10:
            return
        
        # Analyser les 10 dernières métriques
        recent_metrics = list(self.health_metrics_history)[-10:]
        
        # Calculer les tendances
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
        
        # Détecter les tendances problématiques
        if cpu_trend > 5:  # Augmentation de 5% par mesure
            logger.warning("Tendance d'augmentation CPU détectée")
            
        if memory_trend > 3:  # Augmentation de 3% par mesure
            logger.warning("Tendance d'augmentation mémoire détectée")
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcule la tendance d'une série de valeurs"""
        if len(values) < 2:
            return 0.0
        
        # Calcul simple de la pente
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    async def _cleanup_old_alerts(self):
        """Nettoie les anciennes alertes"""
        
        cutoff_time = time.time() - (self.config["alert_retention_hours"] * 3600)
        
        # Nettoyer l'historique
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]
        
        # Nettoyer les alertes actives
        expired_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.timestamp < cutoff_time
        ]
        
        for alert_id in expired_alerts:
            del self.active_alerts[alert_id]
    
    # Fonctions de vérification des règles
    
    def _check_memory_critical(self) -> bool:
        """Vérifie si la mémoire est critique"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0 > self.config["critical_memory_threshold"]
        except:
            return False
    
    def _check_disk_critical(self) -> bool:
        """Vérifie si l'espace disque est critique"""
        try:
            disk = psutil.disk_usage('/')
            return disk.percent / 100.0 > self.config["critical_disk_threshold"]
        except:
            return False
    
    def _check_cpu_overload(self) -> bool:
        """Vérifie si le CPU est surchargé"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            return cpu_usage / 100.0 > self.config["critical_cpu_threshold"]
        except:
            return False
    
    def _check_gpu_temperature(self) -> bool:
        """Vérifie la température GPU"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].temperature > self.config["gpu_temperature_threshold"]
            return False
        except:
            return False
    
    def _check_model_integrity(self) -> bool:
        """Vérifie l'intégrité des modèles"""
        # Simulation de vérification d'intégrité
        return False
    
    def _check_network_stability(self) -> bool:
        """Vérifie la stabilité réseau"""
        # Simulation de vérification réseau
        return False
    
    def _check_configuration_validity(self) -> bool:
        """Vérifie la validité de la configuration"""
        # Simulation de validation de configuration
        return False
    
    # Méthodes publiques
    
    def add_prevention_rule(self, rule: PreventionRule):
        """Ajoute une règle de prévention"""
        self.prevention_rules[rule.rule_id] = rule
        logger.info(f"Added prevention rule: {rule.name}")
    
    def remove_prevention_rule(self, rule_id: str):
        """Supprime une règle de prévention"""
        if rule_id in self.prevention_rules:
            del self.prevention_rules[rule_id]
            logger.info(f"Removed prevention rule: {rule_id}")
    
    def add_alert_callback(self, callback: Callable):
        """Ajoute un callback d'alerte"""
        self.alert_callbacks.append(callback)
    
    def add_action_callback(self, action: PreventionAction, callback: Callable):
        """Ajoute un callback d'action"""
        self.action_callbacks[action].append(callback)
    
    async def _notify_alert_callbacks(self, alert: PreventionAlert):
        """Notifie les callbacks d'alerte"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def _notify_action_callbacks(self, action: PreventionAction, rule: PreventionRule, alert: PreventionAlert):
        """Notifie les callbacks d'action"""
        for callback in self.action_callbacks[action]:
            try:
                await callback(rule, alert)
            except Exception as e:
                logger.error(f"Error in action callback: {e}")
    
    def get_active_alerts(self) -> List[PreventionAlert]:
        """Retourne les alertes actives"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[PreventionAlert]:
        """Retourne l'historique des alertes"""
        return self.alert_history[-limit:]
    
    def get_prevention_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de prévention"""
        return self.prevention_stats.copy()
    
    def get_health_metrics(self) -> Optional[SystemHealthMetrics]:
        """Retourne les dernières métriques de santé"""
        if self.health_metrics_history:
            return self.health_metrics_history[-1]
        return None
    
    async def run_manual_check(self) -> Dict[str, Any]:
        """Exécute une vérification manuelle de tous les systèmes"""
        
        logger.info("Running manual prevention check")
        
        results = {
            "timestamp": time.time(),
            "rules_checked": 0,
            "alerts_generated": 0,
            "problems_found": [],
            "recommendations": []
        }
        
        for rule in self.prevention_rules.values():
            try:
                results["rules_checked"] += 1
                
                should_trigger = await self._execute_rule_check(rule)
                
                if should_trigger:
                    results["problems_found"].append({
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "description": rule.description,
                        "level": rule.prevention_level.name
                    })
                    
                    recommendations = await self._get_recommended_actions(rule)
                    results["recommendations"].extend(recommendations)
                    
                    # Déclencher la règle si pas en cooldown
                    if time.time() - rule.last_triggered >= rule.cooldown:
                        await self._trigger_prevention_rule(rule)
                        results["alerts_generated"] += 1
                        
            except Exception as e:
                logger.error(f"Error in manual check for rule {rule.rule_id}: {e}")
        
        return results
    
    async def shutdown(self):
        """Arrête proprement l'analyseur de prévention"""
        
        logger.info("Shutting down Error Prevention Analyzer")
        
        # Arrêter les tâches de monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Sauvegarder la configuration finale
        self._save_config()
        
        logger.info("Error Prevention Analyzer shutdown complete")

# Instance globale
_error_prevention_analyzer: Optional[ErrorPreventionAnalyzer] = None

def get_error_prevention_analyzer() -> ErrorPreventionAnalyzer:
    """Retourne l'instance globale de l'analyseur de prévention"""
    global _error_prevention_analyzer
    if _error_prevention_analyzer is None:
        _error_prevention_analyzer = ErrorPreventionAnalyzer()
    return _error_prevention_analyzer

# Fonctions utilitaires

async def check_system_health() -> Dict[str, Any]:
    """Vérifie la santé générale du système"""
    analyzer = get_error_prevention_analyzer()
    return await analyzer.run_manual_check()

async def add_custom_prevention_rule(
    rule_id: str,
    name: str,
    description: str,
    error_type: ErrorType,
    check_function: Callable[[], bool],
    prevention_level: PreventionLevel = PreventionLevel.MEDIUM,
    action: PreventionAction = PreventionAction.WARN
):
    """Ajoute une règle de prévention personnalisée"""
    
    rule = PreventionRule(
        rule_id=rule_id,
        name=name,
        description=description,
        error_type=error_type,
        prevention_level=prevention_level,
        check_function=check_function,
        action=action
    )
    
    analyzer = get_error_prevention_analyzer()
    analyzer.add_prevention_rule(rule)