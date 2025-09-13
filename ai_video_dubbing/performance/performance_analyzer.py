"""
Analyseur de performance avec historique et détection de tendances
"""
import asyncio
import time
import logging
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    """Direction de la tendance"""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    """Niveaux d'alerte"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """Métrique de performance"""
    timestamp: float
    component: str
    metric_name: str
    value: Union[float, int, bool]
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrendAnalysis:
    """Analyse de tendance"""
    metric_name: str
    component: str
    direction: TrendDirection
    change_rate: float  # Pourcentage de changement
    confidence: float  # 0-1
    time_period: float  # Période analysée en secondes
    current_value: Union[float, int]
    previous_value: Union[float, int]
    recommendation: str = ""

@dataclass
class PerformanceAlert:
    """Alerte de performance"""
    timestamp: float
    component: str
    metric_name: str
    level: AlertLevel
    message: str
    current_value: Union[float, int]
    threshold_value: Union[float, int]
    trend_analysis: Optional[TrendAnalysis] = None
    recommendations: List[str] = field(default_factory=list)

@dataclass
class OptimalConfiguration:
    """Configuration optimale identifiée"""
    component: str
    configuration: Dict[str, Any]
    performance_score: float
    conditions: Dict[str, Any]  # Conditions système lors de cette performance
    timestamp: float
    usage_count: int = 1
    success_rate: float = 1.0

class PerformanceAnalyzer:
    """Analyseur de performance avec historique et tendances"""
    
    def __init__(self, config_dir: str = ".kiro/performance_analysis"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Stockage des métriques
        self.metrics_history: List[PerformanceMetric] = []
        self.max_history_size = 10000
        
        # Alertes et analyses
        self.active_alerts: List[PerformanceAlert] = []
        self.trend_analyses: Dict[str, TrendAnalysis] = {}
        self.optimal_configurations: Dict[str, List[OptimalConfiguration]] = {}
        
        # Configuration des seuils
        self.thresholds = {
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "memory_percent": {"warning": 85.0, "critical": 95.0},
            "disk_percent": {"warning": 90.0, "critical": 98.0},
            "gpu_memory_percent": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 5.0, "critical": 10.0},
            "error_rate": {"warning": 0.05, "critical": 0.15}
        }
        
        # Configuration de l'analyse
        self.analysis_config = {
            "trend_analysis_window": 3600,  # 1 heure
            "min_data_points": 5,
            "confidence_threshold": 0.7,
            "alert_cooldown": 300,  # 5 minutes
            "auto_cleanup_age": 7 * 24 * 3600  # 7 jours
        }
        
        # Charger les données existantes
        self._load_historical_data()
    
    async def record_metric(self, component: str, metric_name: str, 
                          value: Union[float, int, bool], unit: str = "",
                          metadata: Optional[Dict[str, Any]] = None):
        """Enregistre une métrique de performance"""
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            component=component,
            metric_name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        
        self.metrics_history.append(metric)
        
        # Limiter la taille de l'historique
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # Analyser les tendances et alertes
        await self._analyze_metric(metric)
        
        logger.debug(f"Recorded metric: {component}.{metric_name} = {value} {unit}")
    
    async def _analyze_metric(self, metric: PerformanceMetric):
        """Analyse une métrique pour détecter les tendances et alertes"""
        
        # Vérifier les seuils d'alerte
        await self._check_alert_thresholds(metric)
        
        # Analyser les tendances
        await self._analyze_trend(metric)
    
    async def _check_alert_thresholds(self, metric: PerformanceMetric):
        """Vérifie si une métrique dépasse les seuils d'alerte"""
        
        if not isinstance(metric.value, (int, float)):
            return
        
        metric_key = metric.metric_name
        if metric_key not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric_key]
        current_time = time.time()
        
        # Vérifier le cooldown des alertes
        recent_alerts = [
            alert for alert in self.active_alerts
            if (alert.component == metric.component and 
                alert.metric_name == metric.metric_name and
                current_time - alert.timestamp < self.analysis_config["alert_cooldown"])
        ]
        
        if recent_alerts:
            return  # Cooldown actif
        
        alert_level = None
        threshold_value = None
        
        if metric.value >= thresholds["critical"]:
            alert_level = AlertLevel.CRITICAL
            threshold_value = thresholds["critical"]
        elif metric.value >= thresholds["warning"]:
            alert_level = AlertLevel.WARNING
            threshold_value = thresholds["warning"]
        
        if alert_level:
            # Obtenir l'analyse de tendance si disponible
            trend_key = f"{metric.component}.{metric.metric_name}"
            trend_analysis = self.trend_analyses.get(trend_key)
            
            # Générer le message d'alerte
            message = self._generate_alert_message(metric, alert_level, threshold_value)
            
            # Générer les recommandations
            recommendations = self._generate_alert_recommendations(metric, alert_level, trend_analysis)
            
            alert = PerformanceAlert(
                timestamp=current_time,
                component=metric.component,
                metric_name=metric.metric_name,
                level=alert_level,
                message=message,
                current_value=metric.value,
                threshold_value=threshold_value,
                trend_analysis=trend_analysis,
                recommendations=recommendations
            )
            
            self.active_alerts.append(alert)
            logger.warning(f"Performance alert: {message}")
    
    async def _analyze_trend(self, metric: PerformanceMetric):
        """Analyse la tendance d'une métrique"""
        
        if not isinstance(metric.value, (int, float)):
            return
        
        # Obtenir l'historique récent de cette métrique
        recent_metrics = self._get_recent_metrics(
            metric.component, 
            metric.metric_name,
            self.analysis_config["trend_analysis_window"]
        )
        
        if len(recent_metrics) < self.analysis_config["min_data_points"]:
            return  # Pas assez de données
        
        # Calculer la tendance
        trend_analysis = self._calculate_trend(recent_metrics)
        
        if trend_analysis and trend_analysis.confidence >= self.analysis_config["confidence_threshold"]:
            trend_key = f"{metric.component}.{metric.metric_name}"
            self.trend_analyses[trend_key] = trend_analysis
            
            # Générer des recommandations basées sur la tendance
            if trend_analysis.direction == TrendDirection.DEGRADING:
                trend_analysis.recommendation = self._generate_trend_recommendation(trend_analysis)
    
    def _get_recent_metrics(self, component: str, metric_name: str, time_window: float) -> List[PerformanceMetric]:
        """Obtient les métriques récentes pour un composant et une métrique"""
        
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        return [
            metric for metric in self.metrics_history
            if (metric.component == component and 
                metric.metric_name == metric_name and
                metric.timestamp >= cutoff_time and
                isinstance(metric.value, (int, float)))
        ]
    
    def _calculate_trend(self, metrics: List[PerformanceMetric]) -> Optional[TrendAnalysis]:
        """Calcule la tendance à partir d'une série de métriques"""
        
        if len(metrics) < 2:
            return None
        
        # Trier par timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Extraire les valeurs et timestamps
        values = [float(m.value) for m in sorted_metrics]
        timestamps = [m.timestamp for m in sorted_metrics]
        
        # Calculer la régression linéaire simple
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(t * v for t, v in zip(timestamps, values))
        sum_x2 = sum(t * t for t in timestamps)
        
        # Éviter la division par zéro
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return None
        
        # Coefficient de régression (pente)
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculer le coefficient de corrélation
        mean_x = sum_x / n
        mean_y = sum_y / n
        
        numerator = sum((t - mean_x) * (v - mean_y) for t, v in zip(timestamps, values))
        denom_x = sum((t - mean_x) ** 2 for t in timestamps)
        denom_y = sum((v - mean_y) ** 2 for v in values)
        
        if denom_x * denom_y <= 0:
            return None
        
        correlation = numerator / (denom_x * denom_y) ** 0.5
        confidence = abs(correlation)
        
        # Déterminer la direction de la tendance
        if abs(slope) < 0.001:  # Seuil de stabilité
            direction = TrendDirection.STABLE
        elif slope > 0:
            # Pour certaines métriques, une augmentation est une dégradation
            if sorted_metrics[0].metric_name in ["cpu_usage", "memory_percent", "error_rate", "response_time"]:
                direction = TrendDirection.DEGRADING
            else:
                direction = TrendDirection.IMPROVING
        else:
            if sorted_metrics[0].metric_name in ["cpu_usage", "memory_percent", "error_rate", "response_time"]:
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DEGRADING
        
        # Calculer le taux de changement
        time_span = timestamps[-1] - timestamps[0]
        if time_span > 0:
            change_rate = (slope * time_span / mean_y) * 100  # Pourcentage
        else:
            change_rate = 0.0
        
        return TrendAnalysis(
            metric_name=sorted_metrics[0].metric_name,
            component=sorted_metrics[0].component,
            direction=direction,
            change_rate=change_rate,
            confidence=confidence,
            time_period=time_span,
            current_value=values[-1],
            previous_value=values[0]
        )
    
    def _generate_alert_message(self, metric: PerformanceMetric, level: AlertLevel, threshold: float) -> str:
        """Génère un message d'alerte"""
        
        level_text = {
            AlertLevel.INFO: "Information",
            AlertLevel.WARNING: "Attention",
            AlertLevel.CRITICAL: "Critique"
        }[level]
        
        return f"{level_text}: {metric.component}.{metric.metric_name} = {metric.value}{metric.unit} (seuil: {threshold}{metric.unit})"
    
    def _generate_alert_recommendations(self, metric: PerformanceMetric, level: AlertLevel, 
                                      trend: Optional[TrendAnalysis]) -> List[str]:
        """Génère des recommandations pour une alerte"""
        
        recommendations = []
        
        # Recommandations spécifiques par métrique
        metric_recommendations = {
            "cpu_usage": [
                "Fermer les applications non nécessaires",
                "Vérifier les processus en arrière-plan",
                "Redémarrer le système si nécessaire"
            ],
            "memory_percent": [
                "Libérer de la mémoire",
                "Fermer des applications",
                "Redémarrer l'application"
            ],
            "disk_percent": [
                "Supprimer des fichiers non nécessaires",
                "Nettoyer le cache",
                "Déplacer des fichiers vers un autre disque"
            ],
            "gpu_memory_percent": [
                "Libérer la mémoire GPU",
                "Utiliser des modèles plus légers",
                "Redémarrer l'application"
            ]
        }
        
        if metric.metric_name in metric_recommendations:
            recommendations.extend(metric_recommendations[metric.metric_name])
        
        # Recommandations basées sur la tendance
        if trend and trend.direction == TrendDirection.DEGRADING:
            recommendations.append(f"Tendance dégradante détectée ({trend.change_rate:.1f}% de changement)")
            recommendations.append("Surveillance accrue recommandée")
        
        # Recommandations basées sur le niveau
        if level == AlertLevel.CRITICAL:
            recommendations.insert(0, "Action immédiate requise")
        
        return recommendations
    
    def _generate_trend_recommendation(self, trend: TrendAnalysis) -> str:
        """Génère une recommandation basée sur la tendance"""
        
        if trend.direction == TrendDirection.DEGRADING:
            return f"Performance en dégradation ({trend.change_rate:.1f}% sur {trend.time_period/3600:.1f}h) - Investigation recommandée"
        elif trend.direction == TrendDirection.IMPROVING:
            return f"Performance en amélioration ({trend.change_rate:.1f}% sur {trend.time_period/3600:.1f}h)"
        else:
            return "Performance stable"
    
    async def learn_optimal_configuration(self, component: str, configuration: Dict[str, Any],
                                         performance_score: float, system_conditions: Dict[str, Any]):
        """Apprend une configuration optimale"""
        
        if component not in self.optimal_configurations:
            self.optimal_configurations[component] = []
        
        # Chercher une configuration similaire existante
        existing_config = None
        for config in self.optimal_configurations[component]:
            if self._configurations_similar(config.configuration, configuration):
                existing_config = config
                break
        
        if existing_config:
            # Mettre à jour la configuration existante
            existing_config.usage_count += 1
            # Moyenne pondérée du score de performance
            total_weight = existing_config.usage_count
            existing_config.performance_score = (
                (existing_config.performance_score * (total_weight - 1) + performance_score) / total_weight
            )
            existing_config.timestamp = time.time()
        else:
            # Créer une nouvelle configuration optimale
            optimal_config = OptimalConfiguration(
                component=component,
                configuration=configuration.copy(),
                performance_score=performance_score,
                conditions=system_conditions.copy(),
                timestamp=time.time()
            )
            
            self.optimal_configurations[component].append(optimal_config)
            
            # Limiter le nombre de configurations stockées
            if len(self.optimal_configurations[component]) > 10:
                # Garder les meilleures configurations
                self.optimal_configurations[component].sort(
                    key=lambda c: c.performance_score, reverse=True
                )
                self.optimal_configurations[component] = self.optimal_configurations[component][:10]
        
        logger.info(f"Learned optimal configuration for {component}: score {performance_score:.2f}")
    
    def _configurations_similar(self, config1: Dict[str, Any], config2: Dict[str, Any], 
                              threshold: float = 0.8) -> bool:
        """Vérifie si deux configurations sont similaires"""
        
        if not config1 or not config2:
            return False
        
        # Comparer les clés communes
        common_keys = set(config1.keys()) & set(config2.keys())
        if not common_keys:
            return False
        
        matches = 0
        for key in common_keys:
            if config1[key] == config2[key]:
                matches += 1
        
        similarity = matches / len(common_keys)
        return similarity >= threshold
    
    async def get_optimal_configuration(self, component: str, 
                                      current_conditions: Dict[str, Any]) -> Optional[OptimalConfiguration]:
        """Obtient la configuration optimale pour les conditions actuelles"""
        
        if component not in self.optimal_configurations:
            return None
        
        configurations = self.optimal_configurations[component]
        if not configurations:
            return None
        
        # Trouver la configuration la plus adaptée aux conditions actuelles
        best_config = None
        best_score = 0.0
        
        for config in configurations:
            # Calculer la compatibilité avec les conditions actuelles
            compatibility = self._calculate_condition_compatibility(
                config.conditions, current_conditions
            )
            
            # Score combiné : performance * compatibilité * usage
            combined_score = (
                config.performance_score * 
                compatibility * 
                min(1.0, config.usage_count / 10.0)  # Normaliser l'usage
            )
            
            if combined_score > best_score:
                best_score = combined_score
                best_config = config
        
        return best_config
    
    def _calculate_condition_compatibility(self, stored_conditions: Dict[str, Any], 
                                         current_conditions: Dict[str, Any]) -> float:
        """Calcule la compatibilité entre les conditions stockées et actuelles"""
        
        if not stored_conditions or not current_conditions:
            return 0.5  # Score neutre
        
        compatibility_scores = []
        
        # Comparer les conditions numériques avec tolérance
        numeric_conditions = ["memory_percent", "cpu_usage", "disk_percent", "gpu_memory_percent"]
        
        for condition in numeric_conditions:
            if condition in stored_conditions and condition in current_conditions:
                stored_val = stored_conditions[condition]
                current_val = current_conditions[condition]
                
                if isinstance(stored_val, (int, float)) and isinstance(current_val, (int, float)):
                    # Calculer la différence relative
                    if stored_val > 0:
                        diff = abs(current_val - stored_val) / stored_val
                        score = max(0.0, 1.0 - diff)  # Score inversement proportionnel à la différence
                        compatibility_scores.append(score)
        
        # Comparer les conditions booléennes
        boolean_conditions = ["cuda_available", "gpu_available"]
        
        for condition in boolean_conditions:
            if condition in stored_conditions and condition in current_conditions:
                if stored_conditions[condition] == current_conditions[condition]:
                    compatibility_scores.append(1.0)
                else:
                    compatibility_scores.append(0.0)
        
        if not compatibility_scores:
            return 0.5
        
        return sum(compatibility_scores) / len(compatibility_scores)
    
    async def detect_performance_degradation(self, component: str, 
                                           time_window: float = 3600) -> List[TrendAnalysis]:
        """Détecte les dégradations de performance"""
        
        degradations = []
        
        # Analyser toutes les métriques du composant
        metric_names = set()
        for metric in self.metrics_history:
            if metric.component == component:
                metric_names.add(metric.metric_name)
        
        for metric_name in metric_names:
            recent_metrics = self._get_recent_metrics(component, metric_name, time_window)
            
            if len(recent_metrics) >= self.analysis_config["min_data_points"]:
                trend = self._calculate_trend(recent_metrics)
                
                if (trend and 
                    trend.direction == TrendDirection.DEGRADING and
                    trend.confidence >= self.analysis_config["confidence_threshold"]):
                    degradations.append(trend)
        
        return degradations
    
    async def generate_performance_report(self, time_window: float = 24 * 3600) -> Dict[str, Any]:
        """Génère un rapport de performance"""
        
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # Filtrer les métriques dans la fenêtre de temps
        recent_metrics = [
            metric for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        # Grouper par composant
        components = {}
        for metric in recent_metrics:
            if metric.component not in components:
                components[metric.component] = {}
            
            if metric.metric_name not in components[metric.component]:
                components[metric.component][metric.metric_name] = []
            
            components[metric.component][metric.metric_name].append(metric)
        
        # Analyser chaque composant
        report = {
            "timestamp": current_time,
            "time_window_hours": time_window / 3600,
            "components": {},
            "overall_trends": [],
            "active_alerts": len(self.active_alerts),
            "recommendations": []
        }
        
        for component_name, metrics_by_name in components.items():
            component_report = {
                "metrics": {},
                "trends": [],
                "alerts": []
            }
            
            for metric_name, metric_list in metrics_by_name.items():
                if not metric_list:
                    continue
                
                # Statistiques de base
                numeric_values = [
                    float(m.value) for m in metric_list 
                    if isinstance(m.value, (int, float))
                ]
                
                if numeric_values:
                    component_report["metrics"][metric_name] = {
                        "count": len(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "mean": statistics.mean(numeric_values),
                        "median": statistics.median(numeric_values),
                        "current": numeric_values[-1] if numeric_values else None
                    }
                    
                    if len(numeric_values) > 1:
                        component_report["metrics"][metric_name]["std_dev"] = statistics.stdev(numeric_values)
                
                # Analyse de tendance
                if len(metric_list) >= self.analysis_config["min_data_points"]:
                    trend = self._calculate_trend(metric_list)
                    if trend and trend.confidence >= 0.5:  # Seuil plus bas pour le rapport
                        component_report["trends"].append({
                            "metric": metric_name,
                            "direction": trend.direction.value,
                            "change_rate": trend.change_rate,
                            "confidence": trend.confidence,
                            "recommendation": trend.recommendation
                        })
            
            # Alertes pour ce composant
            component_alerts = [
                alert for alert in self.active_alerts
                if alert.component == component_name and
                current_time - alert.timestamp < time_window
            ]
            
            component_report["alerts"] = [
                {
                    "metric": alert.metric_name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "recommendations": alert.recommendations
                }
                for alert in component_alerts
            ]
            
            report["components"][component_name] = component_report
        
        # Tendances globales
        all_trends = []
        for component_report in report["components"].values():
            all_trends.extend(component_report["trends"])
        
        # Trier par importance (dégradations d'abord, puis par confiance)
        all_trends.sort(key=lambda t: (
            0 if t["direction"] == "degrading" else 1,
            -t["confidence"]
        ))
        
        report["overall_trends"] = all_trends[:10]  # Top 10
        
        # Recommandations globales
        recommendations = set()
        
        # Recommandations basées sur les alertes
        for alert in self.active_alerts:
            if current_time - alert.timestamp < time_window:
                recommendations.update(alert.recommendations)
        
        # Recommandations basées sur les tendances
        degrading_trends = [t for t in all_trends if t["direction"] == "degrading"]
        if len(degrading_trends) > 3:
            recommendations.add("Plusieurs métriques en dégradation - Investigation approfondie recommandée")
        
        report["recommendations"] = list(recommendations)[:10]  # Max 10
        
        return report
    
    def get_component_statistics(self, component: str, metric_name: str, 
                               time_window: float = 24 * 3600) -> Dict[str, Any]:
        """Obtient les statistiques détaillées pour une métrique"""
        
        recent_metrics = self._get_recent_metrics(component, metric_name, time_window)
        
        if not recent_metrics:
            return {"error": "No data available"}
        
        numeric_values = [
            float(m.value) for m in recent_metrics 
            if isinstance(m.value, (int, float))
        ]
        
        if not numeric_values:
            return {"error": "No numeric data available"}
        
        stats = {
            "component": component,
            "metric_name": metric_name,
            "time_window_hours": time_window / 3600,
            "data_points": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
            "current": numeric_values[-1],
            "first": numeric_values[0]
        }
        
        if len(numeric_values) > 1:
            stats["std_dev"] = statistics.stdev(numeric_values)
            stats["variance"] = statistics.variance(numeric_values)
            
            # Percentiles
            sorted_values = sorted(numeric_values)
            n = len(sorted_values)
            stats["percentile_25"] = sorted_values[int(n * 0.25)]
            stats["percentile_75"] = sorted_values[int(n * 0.75)]
            stats["percentile_95"] = sorted_values[int(n * 0.95)]
        
        # Analyse de tendance
        trend = self._calculate_trend(recent_metrics)
        if trend:
            stats["trend"] = {
                "direction": trend.direction.value,
                "change_rate": trend.change_rate,
                "confidence": trend.confidence,
                "recommendation": trend.recommendation
            }
        
        return stats
    
    def _load_historical_data(self):
        """Charge les données historiques depuis le disque"""
        
        try:
            # Charger les métriques
            metrics_file = self.config_dir / "metrics_history.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    
                for metric_data in metrics_data[-1000:]:  # Charger les 1000 dernières
                    metric = PerformanceMetric(
                        timestamp=metric_data["timestamp"],
                        component=metric_data["component"],
                        metric_name=metric_data["metric_name"],
                        value=metric_data["value"],
                        unit=metric_data.get("unit", ""),
                        metadata=metric_data.get("metadata", {})
                    )
                    self.metrics_history.append(metric)
            
            # Charger les configurations optimales
            configs_file = self.config_dir / "optimal_configurations.json"
            if configs_file.exists():
                with open(configs_file, 'r') as f:
                    configs_data = json.load(f)
                    
                for component, configs in configs_data.items():
                    self.optimal_configurations[component] = []
                    for config_data in configs:
                        config = OptimalConfiguration(
                            component=component,
                            configuration=config_data["configuration"],
                            performance_score=config_data["performance_score"],
                            conditions=config_data["conditions"],
                            timestamp=config_data["timestamp"],
                            usage_count=config_data.get("usage_count", 1),
                            success_rate=config_data.get("success_rate", 1.0)
                        )
                        self.optimal_configurations[component].append(config)
            
            logger.info(f"Loaded {len(self.metrics_history)} historical metrics")
            
        except Exception as e:
            logger.warning(f"Failed to load historical data: {e}")
    
    async def save_historical_data(self):
        """Sauvegarde les données historiques sur le disque"""
        
        try:
            # Sauvegarder les métriques (dernières 1000)
            metrics_file = self.config_dir / "metrics_history.json"
            metrics_data = []
            
            for metric in self.metrics_history[-1000:]:
                metrics_data.append({
                    "timestamp": metric.timestamp,
                    "component": metric.component,
                    "metric_name": metric.metric_name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "metadata": metric.metadata
                })
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Sauvegarder les configurations optimales
            configs_file = self.config_dir / "optimal_configurations.json"
            configs_data = {}
            
            for component, configs in self.optimal_configurations.items():
                configs_data[component] = []
                for config in configs:
                    configs_data[component].append({
                        "configuration": config.configuration,
                        "performance_score": config.performance_score,
                        "conditions": config.conditions,
                        "timestamp": config.timestamp,
                        "usage_count": config.usage_count,
                        "success_rate": config.success_rate
                    })
            
            with open(configs_file, 'w') as f:
                json.dump(configs_data, f, indent=2)
            
            logger.debug("Saved historical performance data")
            
        except Exception as e:
            logger.warning(f"Failed to save historical data: {e}")
    
    async def cleanup_old_data(self):
        """Nettoie les anciennes données"""
        
        current_time = time.time()
        cutoff_time = current_time - self.analysis_config["auto_cleanup_age"]
        
        # Nettoyer les métriques anciennes
        initial_count = len(self.metrics_history)
        self.metrics_history = [
            metric for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        cleaned_metrics = initial_count - len(self.metrics_history)
        
        # Nettoyer les alertes anciennes
        initial_alerts = len(self.active_alerts)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if current_time - alert.timestamp < 24 * 3600  # Garder 24h d'alertes
        ]
        
        cleaned_alerts = initial_alerts - len(self.active_alerts)
        
        if cleaned_metrics > 0 or cleaned_alerts > 0:
            logger.info(f"Cleaned up {cleaned_metrics} old metrics and {cleaned_alerts} old alerts")
    
    def get_active_alerts(self, component: Optional[str] = None, 
                         level: Optional[AlertLevel] = None) -> List[PerformanceAlert]:
        """Obtient les alertes actives avec filtres optionnels"""
        
        alerts = self.active_alerts
        
        if component:
            alerts = [alert for alert in alerts if alert.component == component]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        # Trier par timestamp (plus récentes d'abord)
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_trend_analysis(self, component: Optional[str] = None) -> Dict[str, TrendAnalysis]:
        """Obtient les analyses de tendance"""
        
        if component:
            return {
                key: trend for key, trend in self.trend_analyses.items()
                if trend.component == component
            }
        
        return self.trend_analyses.copy()

# Instance globale pour faciliter l'utilisation
performance_analyzer = PerformanceAnalyzer()