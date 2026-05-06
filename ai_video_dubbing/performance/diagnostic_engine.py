"""
Moteur de diagnostic avancé pour l'optimisation des performances
"""
import asyncio
import time
import logging
import psutil
import platform
import subprocess
import json
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class DiagnosticSeverity(Enum):
    """Niveaux de sévérité des problèmes diagnostiqués"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComponentStatus(Enum):
    """Statuts possibles des composants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class DiagnosticIssue:
    """Problème diagnostiqué"""
    component: str
    issue_type: str
    severity: DiagnosticSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    fix_commands: List[str] = field(default_factory=list)

@dataclass
class ComponentDiagnostic:
    """Diagnostic d'un composant"""
    component_name: str
    status: ComponentStatus
    health_score: float  # 0-100
    issues: List[DiagnosticIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class SystemDiagnosticReport:
    """Rapport de diagnostic complet du système"""
    timestamp: float
    overall_health_score: float
    system_info: Dict[str, Any]
    component_diagnostics: Dict[str, ComponentDiagnostic] = field(default_factory=dict)
    critical_issues: List[DiagnosticIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    performance_bottlenecks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_health_score": self.overall_health_score,
            "system_info": self.system_info,
            "component_diagnostics": {
                name: diag.to_dict() for name, diag in self.component_diagnostics.items()
            },
            "critical_issues": [issue.to_dict() for issue in self.critical_issues],
            "recommendations": self.recommendations,
            "performance_bottlenecks": self.performance_bottlenecks
        }

class DiagnosticEngine:
    """Moteur de diagnostic avancé"""
    
    def __init__(self, config_dir: str = ".kiro/diagnostics"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Composants à diagnostiquer
        self.components = {
            "system": self._diagnose_system,
            "gpu": self._diagnose_gpu,
            "memory": self._diagnose_memory,
            "storage": self._diagnose_storage,
            "network": self._diagnose_network,
            "python_env": self._diagnose_python_environment,
            "cuda": self._diagnose_cuda,
            "models": self._diagnose_models,
            "cache": self._diagnose_cache,
            "performance": self._diagnose_performance
        }
        
        # Seuils de performance
        self.thresholds = {
            "memory_usage_warning": 80.0,
            "memory_usage_critical": 95.0,
            "disk_usage_warning": 85.0,
            "disk_usage_critical": 95.0,
            "cpu_usage_warning": 80.0,
            "cpu_usage_critical": 95.0,
            "gpu_memory_warning": 85.0,
            "gpu_memory_critical": 95.0,
            "network_speed_warning": 1000000,  # 1MB/s
            "network_speed_critical": 100000,  # 100KB/s
        }
        
        # Historique des diagnostics
        self.diagnostic_history: List[SystemDiagnosticReport] = []
        self.max_history_size = 50
    
    async def run_full_diagnostic(self) -> SystemDiagnosticReport:
        """Exécute un diagnostic complet du système"""
        
        logger.info("Starting full system diagnostic...")
        start_time = time.time()
        
        # Collecter les informations système de base
        system_info = await self._collect_system_info()
        
        # Diagnostiquer chaque composant
        component_diagnostics = {}
        for component_name, diagnostic_func in self.components.items():
            try:
                logger.debug(f"Diagnosing component: {component_name}")
                component_diag = await diagnostic_func()
                component_diagnostics[component_name] = component_diag
            except Exception as e:
                logger.warning(f"Failed to diagnose {component_name}: {e}")
                component_diagnostics[component_name] = ComponentDiagnostic(
                    component_name=component_name,
                    status=ComponentStatus.UNKNOWN,
                    health_score=0.0,
                    issues=[DiagnosticIssue(
                        component=component_name,
                        issue_type="diagnostic_error",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Failed to diagnose component: {str(e)}"
                    )]
                )
        
        # Calculer le score de santé global
        overall_health_score = self._calculate_overall_health_score(component_diagnostics)
        
        # Identifier les problèmes critiques
        critical_issues = []
        for component_diag in component_diagnostics.values():
            critical_issues.extend([
                issue for issue in component_diag.issues 
                if issue.severity == DiagnosticSeverity.CRITICAL
            ])
        
        # Générer des recommandations globales
        recommendations = self._generate_global_recommendations(component_diagnostics)
        
        # Identifier les goulots d'étranglement
        bottlenecks = self._identify_performance_bottlenecks(component_diagnostics)
        
        # Créer le rapport
        report = SystemDiagnosticReport(
            timestamp=time.time(),
            overall_health_score=overall_health_score,
            system_info=system_info,
            component_diagnostics=component_diagnostics,
            critical_issues=critical_issues,
            recommendations=recommendations,
            performance_bottlenecks=bottlenecks
        )
        
        # Sauvegarder dans l'historique
        self._save_to_history(report)
        
        duration = time.time() - start_time
        logger.info(f"Full diagnostic completed in {duration:.2f}s - Health score: {overall_health_score:.1f}%")
        
        return report
    
    async def _collect_system_info(self) -> Dict[str, Any]:
        """Collecte les informations système de base"""
        
        try:
            # Informations système
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "boot_time": psutil.boot_time(),
                "uptime": time.time() - psutil.boot_time()
            }
            
            # Informations mémoire
            memory = psutil.virtual_memory()
            system_info.update({
                "total_memory": memory.total,
                "available_memory": memory.available,
                "memory_percent": memory.percent
            })
            
            # Informations disque
            disk = psutil.disk_usage('/')
            system_info.update({
                "total_disk": disk.total,
                "free_disk": disk.free,
                "disk_percent": (disk.used / disk.total) * 100
            })
            
            return system_info
            
        except Exception as e:
            logger.warning(f"Failed to collect system info: {e}")
            return {"error": str(e)}
    
    async def _diagnose_system(self) -> ComponentDiagnostic:
        """Diagnostic du système général"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics["cpu_usage"] = cpu_percent
            
            if cpu_percent > self.thresholds["cpu_usage_critical"]:
                issues.append(DiagnosticIssue(
                    component="system",
                    issue_type="high_cpu_usage",
                    severity=DiagnosticSeverity.CRITICAL,
                    message=f"CPU usage très élevé: {cpu_percent:.1f}%",
                    details={"cpu_percent": cpu_percent},
                    recommendations=[
                        "Fermer les applications non nécessaires",
                        "Vérifier les processus en arrière-plan",
                        "Redémarrer le système si nécessaire"
                    ]
                ))
            elif cpu_percent > self.thresholds["cpu_usage_warning"]:
                issues.append(DiagnosticIssue(
                    component="system",
                    issue_type="moderate_cpu_usage",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"CPU usage modérément élevé: {cpu_percent:.1f}%",
                    details={"cpu_percent": cpu_percent},
                    recommendations=["Surveiller l'utilisation CPU"]
                ))
            
            # Température CPU (si disponible)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    cpu_temps = []
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            cpu_temps.extend([entry.current for entry in entries])
                    
                    if cpu_temps:
                        avg_temp = sum(cpu_temps) / len(cpu_temps)
                        metrics["cpu_temperature"] = avg_temp
                        
                        if avg_temp > 85:
                            issues.append(DiagnosticIssue(
                                component="system",
                                issue_type="high_cpu_temperature",
                                severity=DiagnosticSeverity.WARNING,
                                message=f"Température CPU élevée: {avg_temp:.1f}°C",
                                details={"temperature": avg_temp},
                                recommendations=[
                                    "Vérifier la ventilation",
                                    "Nettoyer les ventilateurs",
                                    "Réduire la charge CPU"
                                ]
                            ))
            except:
                pass  # Température non disponible sur tous les systèmes
            
            # Processus consommateurs
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['cpu_percent'] > 5.0:  # Plus de 5% CPU
                        processes.append(proc.info)
                except:
                    continue
            
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            metrics["top_processes"] = processes[:5]
            
            # Score de santé
            health_score = 100.0
            if cpu_percent > self.thresholds["cpu_usage_warning"]:
                health_score -= min(30, (cpu_percent - self.thresholds["cpu_usage_warning"]) * 2)
            
            status = ComponentStatus.HEALTHY
            if issues:
                critical_issues = [i for i in issues if i.severity == DiagnosticSeverity.CRITICAL]
                if critical_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="system",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"System diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="system",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="system",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Diagnostic system failed: {str(e)}"
                )]
            )
    
    async def _diagnose_gpu(self) -> ComponentDiagnostic:
        """Diagnostic du GPU"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Vérifier CUDA
            cuda_available = False
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    cuda_available = True
                    gpu_info = result.stdout.strip().split('\n')[0].split(', ')
                    
                    metrics.update({
                        "gpu_name": gpu_info[0],
                        "gpu_memory_total": int(gpu_info[1]),
                        "gpu_memory_used": int(gpu_info[2]),
                        "gpu_temperature": float(gpu_info[3]),
                        "gpu_utilization": float(gpu_info[4])
                    })
                    
                    # Vérifier l'utilisation mémoire GPU
                    memory_percent = (int(gpu_info[2]) / int(gpu_info[1])) * 100
                    metrics["gpu_memory_percent"] = memory_percent
                    
                    if memory_percent > self.thresholds["gpu_memory_critical"]:
                        issues.append(DiagnosticIssue(
                            component="gpu",
                            issue_type="high_gpu_memory",
                            severity=DiagnosticSeverity.CRITICAL,
                            message=f"Mémoire GPU critique: {memory_percent:.1f}%",
                            details={"memory_percent": memory_percent},
                            recommendations=[
                                "Fermer les applications utilisant le GPU",
                                "Utiliser des modèles plus légers",
                                "Redémarrer l'application"
                            ]
                        ))
                    elif memory_percent > self.thresholds["gpu_memory_warning"]:
                        issues.append(DiagnosticIssue(
                            component="gpu",
                            issue_type="moderate_gpu_memory",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Mémoire GPU élevée: {memory_percent:.1f}%",
                            details={"memory_percent": memory_percent},
                            recommendations=["Surveiller l'utilisation mémoire GPU"]
                        ))
                    
                    # Vérifier la température
                    temp = float(gpu_info[3])
                    if temp > 85:
                        issues.append(DiagnosticIssue(
                            component="gpu",
                            issue_type="high_gpu_temperature",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Température GPU élevée: {temp}°C",
                            details={"temperature": temp},
                            recommendations=[
                                "Vérifier la ventilation GPU",
                                "Réduire la charge GPU",
                                "Nettoyer le système de refroidissement"
                            ]
                        ))
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            if not cuda_available:
                issues.append(DiagnosticIssue(
                    component="gpu",
                    issue_type="no_gpu_detected",
                    severity=DiagnosticSeverity.WARNING,
                    message="Aucun GPU NVIDIA détecté ou nvidia-smi non disponible",
                    recommendations=[
                        "Installer les pilotes NVIDIA",
                        "Vérifier la connexion GPU",
                        "Utiliser le mode CPU comme alternative"
                    ]
                ))
                metrics["cuda_available"] = False
            else:
                metrics["cuda_available"] = True
            
            # Score de santé
            health_score = 100.0
            if not cuda_available:
                health_score = 60.0  # Pas critique mais pas optimal
            elif "gpu_memory_percent" in metrics:
                memory_percent = metrics["gpu_memory_percent"]
                if memory_percent > self.thresholds["gpu_memory_warning"]:
                    health_score -= min(40, (memory_percent - self.thresholds["gpu_memory_warning"]) * 3)
            
            status = ComponentStatus.HEALTHY
            if issues:
                critical_issues = [i for i in issues if i.severity == DiagnosticSeverity.CRITICAL]
                if critical_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="gpu",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"GPU diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="gpu",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="gpu",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"GPU diagnostic failed: {str(e)}"
                )]
            )
    
    async def _diagnose_memory(self) -> ComponentDiagnostic:
        """Diagnostic de la mémoire"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics.update({
                "total_memory": memory.total,
                "available_memory": memory.available,
                "used_memory": memory.used,
                "memory_percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent
            })
            
            # Vérifier l'utilisation mémoire
            if memory.percent > self.thresholds["memory_usage_critical"]:
                issues.append(DiagnosticIssue(
                    component="memory",
                    issue_type="critical_memory_usage",
                    severity=DiagnosticSeverity.CRITICAL,
                    message=f"Utilisation mémoire critique: {memory.percent:.1f}%",
                    details={"memory_percent": memory.percent, "available_gb": memory.available / (1024**3)},
                    recommendations=[
                        "Fermer les applications non nécessaires",
                        "Redémarrer l'application",
                        "Ajouter plus de RAM si possible"
                    ]
                ))
            elif memory.percent > self.thresholds["memory_usage_warning"]:
                issues.append(DiagnosticIssue(
                    component="memory",
                    issue_type="high_memory_usage",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Utilisation mémoire élevée: {memory.percent:.1f}%",
                    details={"memory_percent": memory.percent, "available_gb": memory.available / (1024**3)},
                    recommendations=["Surveiller l'utilisation mémoire"]
                ))
            
            # Vérifier l'utilisation du swap
            if swap.percent > 50:
                issues.append(DiagnosticIssue(
                    component="memory",
                    issue_type="high_swap_usage",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Utilisation swap élevée: {swap.percent:.1f}%",
                    details={"swap_percent": swap.percent},
                    recommendations=[
                        "Libérer de la mémoire RAM",
                        "Fermer des applications",
                        "Redémarrer le système"
                    ]
                ))
            
            # Vérifier la mémoire disponible absolue
            available_gb = memory.available / (1024**3)
            if available_gb < 1.0:  # Moins de 1GB disponible
                issues.append(DiagnosticIssue(
                    component="memory",
                    issue_type="low_available_memory",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Mémoire disponible très faible: {available_gb:.1f}GB",
                    details={"available_gb": available_gb},
                    recommendations=[
                        "Fermer immédiatement des applications",
                        "Utiliser des modèles plus légers",
                        "Redémarrer l'application"
                    ]
                ))
            
            # Score de santé
            health_score = 100.0
            if memory.percent > self.thresholds["memory_usage_warning"]:
                health_score -= min(50, (memory.percent - self.thresholds["memory_usage_warning"]) * 3)
            if swap.percent > 25:
                health_score -= min(20, swap.percent)
            
            status = ComponentStatus.HEALTHY
            if issues:
                critical_issues = [i for i in issues if i.severity in [DiagnosticSeverity.CRITICAL, DiagnosticSeverity.ERROR]]
                if critical_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="memory",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Memory diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="memory",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="memory",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Memory diagnostic failed: {str(e)}"
                )]
            )

    async def _diagnose_storage(self) -> ComponentDiagnostic:
        """Diagnostic du stockage"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Diagnostic du disque principal
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            metrics.update({
                "total_disk": disk.total,
                "used_disk": disk.used,
                "free_disk": disk.free,
                "disk_percent": disk_percent
            })
            
            # Vérifier l'espace disque
            if disk_percent > self.thresholds["disk_usage_critical"]:
                issues.append(DiagnosticIssue(
                    component="storage",
                    issue_type="critical_disk_usage",
                    severity=DiagnosticSeverity.CRITICAL,
                    message=f"Espace disque critique: {disk_percent:.1f}%",
                    details={"disk_percent": disk_percent, "free_gb": disk.free / (1024**3)},
                    recommendations=[
                        "Supprimer des fichiers non nécessaires",
                        "Nettoyer le cache des modèles",
                        "Déplacer des fichiers vers un autre disque"
                    ]
                ))
            elif disk_percent > self.thresholds["disk_usage_warning"]:
                issues.append(DiagnosticIssue(
                    component="storage",
                    issue_type="high_disk_usage",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Espace disque élevé: {disk_percent:.1f}%",
                    details={"disk_percent": disk_percent, "free_gb": disk.free / (1024**3)},
                    recommendations=["Surveiller l'espace disque"]
                ))
            
            # Vérifier l'espace libre absolu
            free_gb = disk.free / (1024**3)
            if free_gb < 5.0:  # Moins de 5GB libre
                issues.append(DiagnosticIssue(
                    component="storage",
                    issue_type="low_free_space",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Espace libre très faible: {free_gb:.1f}GB",
                    details={"free_gb": free_gb},
                    recommendations=[
                        "Libérer de l'espace immédiatement",
                        "Supprimer les modèles non utilisés",
                        "Nettoyer les fichiers temporaires"
                    ]
                ))
            
            # Vérifier les performances I/O (si possible)
            try:
                io_counters = psutil.disk_io_counters()
                if io_counters:
                    metrics.update({
                        "read_bytes": io_counters.read_bytes,
                        "write_bytes": io_counters.write_bytes,
                        "read_time": io_counters.read_time,
                        "write_time": io_counters.write_time
                    })
            except:
                pass
            
            # Score de santé
            health_score = 100.0
            if disk_percent > self.thresholds["disk_usage_warning"]:
                health_score -= min(40, (disk_percent - self.thresholds["disk_usage_warning"]) * 4)
            if free_gb < 10:
                health_score -= min(30, (10 - free_gb) * 3)
            
            status = ComponentStatus.HEALTHY
            if issues:
                critical_issues = [i for i in issues if i.severity in [DiagnosticSeverity.CRITICAL, DiagnosticSeverity.ERROR]]
                if critical_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="storage",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Storage diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="storage",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="storage",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Storage diagnostic failed: {str(e)}"
                )]
            )    async
 def _diagnose_network(self) -> ComponentDiagnostic:
        """Diagnostic du réseau"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Test de connectivité basique
            import socket
            
            # Test de résolution DNS
            try:
                socket.gethostbyname('google.com')
                metrics["dns_resolution"] = True
            except:
                issues.append(DiagnosticIssue(
                    component="network",
                    issue_type="dns_resolution_failed",
                    severity=DiagnosticSeverity.ERROR,
                    message="Résolution DNS échouée",
                    recommendations=[
                        "Vérifier la connexion internet",
                        "Changer les serveurs DNS",
                        "Redémarrer la connexion réseau"
                    ]
                ))
                metrics["dns_resolution"] = False
            
            # Test de connectivité HTTP
            try:
                import urllib.request
                start_time = time.time()
                response = urllib.request.urlopen('http://httpbin.org/get', timeout=10)
                response_time = time.time() - start_time
                
                metrics["http_connectivity"] = True
                metrics["http_response_time"] = response_time
                
                if response_time > 5.0:
                    issues.append(DiagnosticIssue(
                        component="network",
                        issue_type="slow_network",
                        severity=DiagnosticSeverity.WARNING,
                        message=f"Connexion réseau lente: {response_time:.2f}s",
                        details={"response_time": response_time},
                        recommendations=[
                            "Vérifier la qualité de la connexion",
                            "Utiliser une connexion plus rapide",
                            "Télécharger les modèles à un moment optimal"
                        ]
                    ))
                
            except Exception as e:
                issues.append(DiagnosticIssue(
                    component="network",
                    issue_type="http_connectivity_failed",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Connectivité HTTP échouée: {str(e)}",
                    recommendations=[
                        "Vérifier la connexion internet",
                        "Vérifier les paramètres proxy",
                        "Vérifier le pare-feu"
                    ]
                ))
                metrics["http_connectivity"] = False
            
            # Statistiques réseau
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    metrics.update({
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv,
                        "errin": net_io.errin,
                        "errout": net_io.errout,
                        "dropin": net_io.dropin,
                        "dropout": net_io.dropout
                    })
                    
                    # Vérifier les erreurs réseau
                    total_errors = net_io.errin + net_io.errout
                    total_drops = net_io.dropin + net_io.dropout
                    
                    if total_errors > 100:
                        issues.append(DiagnosticIssue(
                            component="network",
                            issue_type="network_errors",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Erreurs réseau détectées: {total_errors}",
                            details={"total_errors": total_errors},
                            recommendations=[
                                "Vérifier la qualité de la connexion",
                                "Redémarrer l'interface réseau",
                                "Vérifier les câbles réseau"
                            ]
                        ))
                    
                    if total_drops > 50:
                        issues.append(DiagnosticIssue(
                            component="network",
                            issue_type="packet_drops",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Paquets perdus détectés: {total_drops}",
                            details={"total_drops": total_drops},
                            recommendations=[
                                "Vérifier la stabilité de la connexion",
                                "Réduire la charge réseau",
                                "Utiliser une connexion filaire"
                            ]
                        ))
            except:
                pass
            
            # Score de santé
            health_score = 100.0
            if not metrics.get("dns_resolution", True):
                health_score -= 40
            if not metrics.get("http_connectivity", True):
                health_score -= 30
            if metrics.get("http_response_time", 0) > 3.0:
                health_score -= 20
            
            status = ComponentStatus.HEALTHY
            if issues:
                error_issues = [i for i in issues if i.severity == DiagnosticSeverity.ERROR]
                if error_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="network",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Network diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="network",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="network",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Network diagnostic failed: {str(e)}"
                )]
            )
    
    async def _diagnose_python_environment(self) -> ComponentDiagnostic:
        """Diagnostic de l'environnement Python"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            import sys
            import pkg_resources
            
            metrics.update({
                "python_version": sys.version,
                "python_executable": sys.executable,
                "python_path": sys.path[:3]  # Premiers éléments du path
            })
            
            # Vérifier les packages critiques
            critical_packages = {
                "torch": "PyTorch pour l'IA",
                "numpy": "Calculs numériques",
                "psutil": "Monitoring système"
            }
            
            installed_packages = {}
            missing_packages = []
            
            for package, description in critical_packages.items():
                try:
                    version = pkg_resources.get_distribution(package).version
                    installed_packages[package] = version
                except pkg_resources.DistributionNotFound:
                    missing_packages.append(package)
                    issues.append(DiagnosticIssue(
                        component="python_env",
                        issue_type="missing_package",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Package critique manquant: {package} ({description})",
                        details={"package": package, "description": description},
                        recommendations=[f"Installer {package}: pip install {package}"]
                    ))
            
            metrics["installed_packages"] = installed_packages
            metrics["missing_packages"] = missing_packages
            
            # Vérifier la version Python
            python_version = sys.version_info
            if python_version < (3, 8):
                issues.append(DiagnosticIssue(
                    component="python_env",
                    issue_type="old_python_version",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Version Python ancienne: {python_version.major}.{python_version.minor}",
                    details={"version": f"{python_version.major}.{python_version.minor}.{python_version.micro}"},
                    recommendations=[
                        "Mettre à jour vers Python 3.8+",
                        "Vérifier la compatibilité des packages"
                    ]
                ))
            
            # Vérifier l'environnement virtuel
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            metrics["virtual_environment"] = in_venv
            
            if not in_venv:
                issues.append(DiagnosticIssue(
                    component="python_env",
                    issue_type="no_virtual_environment",
                    severity=DiagnosticSeverity.INFO,
                    message="Aucun environnement virtuel détecté",
                    recommendations=[
                        "Utiliser un environnement virtuel",
                        "Créer avec: python -m venv mon_env"
                    ]
                ))
            
            # Score de santé
            health_score = 100.0
            health_score -= len(missing_packages) * 20  # -20 par package manquant
            if python_version < (3, 8):
                health_score -= 15
            if not in_venv:
                health_score -= 5
            
            status = ComponentStatus.HEALTHY
            if issues:
                error_issues = [i for i in issues if i.severity == DiagnosticSeverity.ERROR]
                if error_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="python_env",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Python environment diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="python_env",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="python_env",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Python environment diagnostic failed: {str(e)}"
                )]
            )
    
    async def _diagnose_cuda(self) -> ComponentDiagnostic:
        """Diagnostic de CUDA"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Vérifier PyTorch CUDA
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                metrics["pytorch_cuda_available"] = cuda_available
                
                if cuda_available:
                    metrics.update({
                        "cuda_device_count": torch.cuda.device_count(),
                        "cuda_current_device": torch.cuda.current_device(),
                        "cuda_device_name": torch.cuda.get_device_name(),
                        "cuda_version": torch.version.cuda
                    })
                    
                    # Test de mémoire CUDA
                    try:
                        memory_allocated = torch.cuda.memory_allocated()
                        memory_reserved = torch.cuda.memory_reserved()
                        memory_total = torch.cuda.get_device_properties(0).total_memory
                        
                        metrics.update({
                            "cuda_memory_allocated": memory_allocated,
                            "cuda_memory_reserved": memory_reserved,
                            "cuda_memory_total": memory_total,
                            "cuda_memory_free": memory_total - memory_reserved
                        })
                        
                        memory_usage_percent = (memory_reserved / memory_total) * 100
                        if memory_usage_percent > 90:
                            issues.append(DiagnosticIssue(
                                component="cuda",
                                issue_type="high_cuda_memory",
                                severity=DiagnosticSeverity.WARNING,
                                message=f"Mémoire CUDA élevée: {memory_usage_percent:.1f}%",
                                details={"memory_percent": memory_usage_percent},
                                recommendations=[
                                    "Libérer la mémoire CUDA",
                                    "Utiliser torch.cuda.empty_cache()",
                                    "Réduire la taille des modèles"
                                ]
                            ))
                        
                    except Exception as e:
                        issues.append(DiagnosticIssue(
                            component="cuda",
                            issue_type="cuda_memory_check_failed",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Vérification mémoire CUDA échouée: {str(e)}"
                        ))
                    
                    # Test simple CUDA
                    try:
                        test_tensor = torch.randn(100, 100).cuda()
                        result = torch.matmul(test_tensor, test_tensor)
                        del test_tensor, result
                        torch.cuda.empty_cache()
                        metrics["cuda_test_passed"] = True
                    except Exception as e:
                        issues.append(DiagnosticIssue(
                            component="cuda",
                            issue_type="cuda_test_failed",
                            severity=DiagnosticSeverity.ERROR,
                            message=f"Test CUDA échoué: {str(e)}",
                            recommendations=[
                                "Redémarrer l'application",
                                "Vérifier les pilotes NVIDIA",
                                "Utiliser le mode CPU"
                            ]
                        ))
                        metrics["cuda_test_passed"] = False
                
                else:
                    issues.append(DiagnosticIssue(
                        component="cuda",
                        issue_type="cuda_not_available",
                        severity=DiagnosticSeverity.WARNING,
                        message="CUDA non disponible dans PyTorch",
                        recommendations=[
                            "Installer PyTorch avec support CUDA",
                            "Vérifier les pilotes NVIDIA",
                            "Utiliser le mode CPU comme alternative"
                        ]
                    ))
                
            except ImportError:
                issues.append(DiagnosticIssue(
                    component="cuda",
                    issue_type="pytorch_not_installed",
                    severity=DiagnosticSeverity.ERROR,
                    message="PyTorch non installé",
                    recommendations=["Installer PyTorch: pip install torch"]
                ))
                metrics["pytorch_installed"] = False
            
            # Score de santé
            health_score = 100.0
            if not metrics.get("pytorch_cuda_available", False):
                health_score = 60.0  # Pas critique mais pas optimal
            if not metrics.get("cuda_test_passed", True):
                health_score -= 30
            
            status = ComponentStatus.HEALTHY
            if issues:
                error_issues = [i for i in issues if i.severity == DiagnosticSeverity.ERROR]
                if error_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="cuda",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"CUDA diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="cuda",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="cuda",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"CUDA diagnostic failed: {str(e)}"
                )]
            ) 
   async def _diagnose_models(self) -> ComponentDiagnostic:
        """Diagnostic des modèles"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Vérifier les répertoires de modèles
            model_dirs = [
                Path.home() / ".cache" / "huggingface",
                Path.home() / ".cache" / "torch",
                Path("models"),
                Path("ai_video_dubbing") / "models"
            ]
            
            total_model_size = 0
            model_count = 0
            accessible_dirs = []
            
            for model_dir in model_dirs:
                if model_dir.exists():
                    accessible_dirs.append(str(model_dir))
                    try:
                        for file_path in model_dir.rglob("*"):
                            if file_path.is_file():
                                total_model_size += file_path.stat().st_size
                                model_count += 1
                    except PermissionError:
                        issues.append(DiagnosticIssue(
                            component="models",
                            issue_type="model_dir_permission",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Permissions insuffisantes pour {model_dir}",
                            recommendations=["Vérifier les permissions du répertoire"]
                        ))
            
            metrics.update({
                "model_directories": accessible_dirs,
                "total_model_size": total_model_size,
                "model_file_count": model_count,
                "total_model_size_gb": total_model_size / (1024**3)
            })
            
            # Vérifier l'espace utilisé par les modèles
            model_size_gb = total_model_size / (1024**3)
            if model_size_gb > 50:  # Plus de 50GB
                issues.append(DiagnosticIssue(
                    component="models",
                    issue_type="large_model_cache",
                    severity=DiagnosticSeverity.INFO,
                    message=f"Cache de modèles volumineux: {model_size_gb:.1f}GB",
                    details={"size_gb": model_size_gb},
                    recommendations=[
                        "Nettoyer les modèles non utilisés",
                        "Utiliser des modèles plus légers",
                        "Configurer un nettoyage automatique"
                    ]
                ))
            
            # Vérifier les modèles spécifiques (si disponibles)
            try:
                from .model_manager import ModelManager
                model_manager = ModelManager()
                
                # Vérifier les modèles recommandés
                recommended_models = ["whisper-tiny", "whisper-base", "nemo-asr-light"]
                available_models = []
                missing_models = []
                
                for model_name in recommended_models:
                    # Simulation de vérification (à adapter selon l'implémentation réelle)
                    model_available = True  # Placeholder
                    if model_available:
                        available_models.append(model_name)
                    else:
                        missing_models.append(model_name)
                
                metrics.update({
                    "available_models": available_models,
                    "missing_models": missing_models
                })
                
                if len(missing_models) > len(available_models):
                    issues.append(DiagnosticIssue(
                        component="models",
                        issue_type="few_models_available",
                        severity=DiagnosticSeverity.WARNING,
                        message=f"Peu de modèles disponibles: {len(available_models)}/{len(recommended_models)}",
                        details={"available": len(available_models), "total": len(recommended_models)},
                        recommendations=[
                            "Télécharger des modèles de base",
                            "Vérifier la connexion internet",
                            "Utiliser le gestionnaire de modèles"
                        ]
                    ))
                
            except ImportError:
                issues.append(DiagnosticIssue(
                    component="models",
                    issue_type="model_manager_unavailable",
                    severity=DiagnosticSeverity.INFO,
                    message="Gestionnaire de modèles non disponible",
                    recommendations=["Vérifier l'installation du gestionnaire de modèles"]
                ))
            
            # Score de santé
            health_score = 100.0
            if model_count == 0:
                health_score = 30.0  # Pas de modèles
            elif len(accessible_dirs) == 0:
                health_score = 20.0  # Pas d'accès aux répertoires
            
            status = ComponentStatus.HEALTHY
            if issues:
                warning_issues = [i for i in issues if i.severity == DiagnosticSeverity.WARNING]
                if warning_issues:
                    status = ComponentStatus.DEGRADED
            
            if model_count == 0:
                status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="models",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Models diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="models",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="models",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Models diagnostic failed: {str(e)}"
                )]
            )    as
ync def _diagnose_cache(self) -> ComponentDiagnostic:
        """Diagnostic du système de cache"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Vérifier les répertoires de cache
            cache_dirs = [
                Path(".kiro/cache"),
                Path("cache"),
                Path.home() / ".cache" / "ai_video_dubbing"
            ]
            
            total_cache_size = 0
            cache_file_count = 0
            accessible_cache_dirs = []
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    accessible_cache_dirs.append(str(cache_dir))
                    try:
                        for file_path in cache_dir.rglob("*"):
                            if file_path.is_file():
                                total_cache_size += file_path.stat().st_size
                                cache_file_count += 1
                    except PermissionError:
                        issues.append(DiagnosticIssue(
                            component="cache",
                            issue_type="cache_dir_permission",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Permissions insuffisantes pour {cache_dir}",
                            recommendations=["Vérifier les permissions du répertoire cache"]
                        ))
            
            metrics.update({
                "cache_directories": accessible_cache_dirs,
                "total_cache_size": total_cache_size,
                "cache_file_count": cache_file_count,
                "total_cache_size_gb": total_cache_size / (1024**3)
            })
            
            # Vérifier la taille du cache
            cache_size_gb = total_cache_size / (1024**3)
            if cache_size_gb > 20:  # Plus de 20GB
                issues.append(DiagnosticIssue(
                    component="cache",
                    issue_type="large_cache_size",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Cache volumineux: {cache_size_gb:.1f}GB",
                    details={"size_gb": cache_size_gb},
                    recommendations=[
                        "Nettoyer le cache ancien",
                        "Configurer un nettoyage automatique",
                        "Réduire la durée de rétention du cache"
                    ]
                ))
            
            # Vérifier l'âge des fichiers de cache
            old_files = 0
            recent_files = 0
            current_time = time.time()
            
            for cache_dir in accessible_cache_dirs:
                cache_path = Path(cache_dir)
                if cache_path.exists():
                    for file_path in cache_path.rglob("*"):
                        if file_path.is_file():
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > 7 * 24 * 3600:  # Plus de 7 jours
                                old_files += 1
                            else:
                                recent_files += 1
            
            metrics.update({
                "old_cache_files": old_files,
                "recent_cache_files": recent_files
            })
            
            if old_files > recent_files * 2:  # Beaucoup de vieux fichiers
                issues.append(DiagnosticIssue(
                    component="cache",
                    issue_type="many_old_cache_files",
                    severity=DiagnosticSeverity.INFO,
                    message=f"Nombreux fichiers de cache anciens: {old_files}",
                    details={"old_files": old_files, "recent_files": recent_files},
                    recommendations=[
                        "Nettoyer les fichiers de cache anciens",
                        "Activer le nettoyage automatique"
                    ]
                ))
            
            # Tester l'accès en écriture au cache
            try:
                test_cache_dir = Path(".kiro/cache")
                test_cache_dir.mkdir(parents=True, exist_ok=True)
                test_file = test_cache_dir / "diagnostic_test.tmp"
                
                with open(test_file, 'w') as f:
                    f.write("test")
                
                test_file.unlink()  # Supprimer le fichier de test
                metrics["cache_write_access"] = True
                
            except Exception as e:
                issues.append(DiagnosticIssue(
                    component="cache",
                    issue_type="cache_write_failed",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Impossible d'écrire dans le cache: {str(e)}",
                    recommendations=[
                        "Vérifier les permissions du répertoire",
                        "Vérifier l'espace disque disponible",
                        "Créer le répertoire de cache manuellement"
                    ]
                ))
                metrics["cache_write_access"] = False
            
            # Score de santé
            health_score = 100.0
            if not metrics.get("cache_write_access", True):
                health_score -= 40
            if cache_size_gb > 30:
                health_score -= 20
            if old_files > 1000:
                health_score -= 10
            
            status = ComponentStatus.HEALTHY
            if issues:
                error_issues = [i for i in issues if i.severity == DiagnosticSeverity.ERROR]
                if error_issues:
                    status = ComponentStatus.FAILED
                else:
                    status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="cache",
                status=status,
                health_score=max(0, health_score),
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Cache diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="cache",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="cache",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Cache diagnostic failed: {str(e)}"
                )]
            )    async de
f _diagnose_performance(self) -> ComponentDiagnostic:
        """Diagnostic des performances générales"""
        
        issues = []
        metrics = {}
        recommendations = []
        
        try:
            # Test de performance CPU
            start_time = time.time()
            # Test simple de calcul
            result = sum(i * i for i in range(100000))
            cpu_test_time = time.time() - start_time
            
            metrics["cpu_test_time"] = cpu_test_time
            metrics["cpu_test_result"] = result
            
            if cpu_test_time > 0.1:  # Plus de 100ms pour un test simple
                issues.append(DiagnosticIssue(
                    component="performance",
                    issue_type="slow_cpu_performance",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Performance CPU lente: {cpu_test_time:.3f}s",
                    details={"test_time": cpu_test_time},
                    recommendations=[
                        "Fermer les applications consommatrices",
                        "Vérifier la température CPU",
                        "Redémarrer le système"
                    ]
                ))
            
            # Test de performance mémoire
            start_time = time.time()
            # Allocation et libération de mémoire
            test_data = [i for i in range(1000000)]
            del test_data
            memory_test_time = time.time() - start_time
            
            metrics["memory_test_time"] = memory_test_time
            
            if memory_test_time > 0.5:  # Plus de 500ms
                issues.append(DiagnosticIssue(
                    component="performance",
                    issue_type="slow_memory_performance",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Performance mémoire lente: {memory_test_time:.3f}s",
                    details={"test_time": memory_test_time},
                    recommendations=[
                        "Vérifier l'utilisation mémoire",
                        "Fermer des applications",
                        "Ajouter plus de RAM"
                    ]
                ))
            
            # Test de performance disque
            start_time = time.time()
            test_file = Path(".kiro/perf_test.tmp")
            test_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Écriture
                with open(test_file, 'w') as f:
                    f.write("x" * 1000000)  # 1MB
                
                # Lecture
                with open(test_file, 'r') as f:
                    content = f.read()
                
                disk_test_time = time.time() - start_time
                test_file.unlink()  # Nettoyer
                
                metrics["disk_test_time"] = disk_test_time
                
                if disk_test_time > 2.0:  # Plus de 2 secondes
                    issues.append(DiagnosticIssue(
                        component="performance",
                        issue_type="slow_disk_performance",
                        severity=DiagnosticSeverity.WARNING,
                        message=f"Performance disque lente: {disk_test_time:.3f}s",
                        details={"test_time": disk_test_time},
                        recommendations=[
                            "Vérifier l'espace disque",
                            "Défragmenter le disque",
                            "Utiliser un SSD"
                        ]
                    ))
                
            except Exception as e:
                issues.append(DiagnosticIssue(
                    component="performance",
                    issue_type="disk_test_failed",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Test disque échoué: {str(e)}",
                    recommendations=["Vérifier les permissions et l'espace disque"]
                ))
            
            # Évaluation globale des performances
            performance_score = 100.0
            if cpu_test_time > 0.05:
                performance_score -= min(30, (cpu_test_time - 0.05) * 300)
            if memory_test_time > 0.2:
                performance_score -= min(25, (memory_test_time - 0.2) * 50)
            if metrics.get("disk_test_time", 0) > 1.0:
                performance_score -= min(25, (metrics["disk_test_time"] - 1.0) * 12.5)
            
            metrics["performance_score"] = performance_score
            
            if performance_score < 60:
                issues.append(DiagnosticIssue(
                    component="performance",
                    issue_type="overall_poor_performance",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Performance générale dégradée: {performance_score:.1f}/100",
                    details={"score": performance_score},
                    recommendations=[
                        "Optimiser les ressources système",
                        "Fermer les applications non nécessaires",
                        "Redémarrer le système",
                        "Vérifier les mises à jour système"
                    ]
                ))
            
            # Score de santé basé sur les performances
            health_score = max(0, performance_score)
            
            status = ComponentStatus.HEALTHY
            if performance_score < 40:
                status = ComponentStatus.FAILED
            elif performance_score < 70:
                status = ComponentStatus.DEGRADED
            
            return ComponentDiagnostic(
                component_name="performance",
                status=status,
                health_score=health_score,
                issues=issues,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Performance diagnostic failed: {e}")
            return ComponentDiagnostic(
                component_name="performance",
                status=ComponentStatus.UNKNOWN,
                health_score=0.0,
                issues=[DiagnosticIssue(
                    component="performance",
                    issue_type="diagnostic_error",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Performance diagnostic failed: {str(e)}"
                )]
            )    d
ef _calculate_overall_health_score(self, component_diagnostics: Dict[str, ComponentDiagnostic]) -> float:
        """Calcule le score de santé global"""
        
        if not component_diagnostics:
            return 0.0
        
        # Pondération des composants
        component_weights = {
            "system": 0.15,
            "memory": 0.15,
            "gpu": 0.12,
            "storage": 0.12,
            "network": 0.10,
            "python_env": 0.10,
            "cuda": 0.08,
            "models": 0.08,
            "cache": 0.05,
            "performance": 0.05
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for component_name, diagnostic in component_diagnostics.items():
            weight = component_weights.get(component_name, 0.05)  # Poids par défaut
            total_score += diagnostic.health_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_global_recommendations(self, component_diagnostics: Dict[str, ComponentDiagnostic]) -> List[str]:
        """Génère des recommandations globales"""
        
        recommendations = []
        
        # Analyser les problèmes critiques
        critical_components = []
        degraded_components = []
        
        for component_name, diagnostic in component_diagnostics.items():
            if diagnostic.status == ComponentStatus.FAILED:
                critical_components.append(component_name)
            elif diagnostic.status == ComponentStatus.DEGRADED:
                degraded_components.append(component_name)
        
        # Recommandations basées sur les composants critiques
        if "memory" in critical_components:
            recommendations.append("🚨 Priorité critique: Libérer de la mémoire immédiatement")
        
        if "storage" in critical_components:
            recommendations.append("🚨 Priorité critique: Libérer de l'espace disque")
        
        if "gpu" in critical_components:
            recommendations.append("🚨 Priorité critique: Résoudre les problèmes GPU")
        
        if "network" in critical_components:
            recommendations.append("🚨 Priorité critique: Vérifier la connexion réseau")
        
        # Recommandations générales
        if len(critical_components) > 2:
            recommendations.append("⚠️ Redémarrage du système recommandé")
        
        if len(degraded_components) > 3:
            recommendations.append("🔧 Maintenance système recommandée")
        
        # Recommandations d'optimisation
        if "performance" in degraded_components:
            recommendations.append("⚡ Optimiser les performances système")
        
        if "cache" in degraded_components:
            recommendations.append("🗄️ Nettoyer et optimiser le cache")
        
        if "models" in degraded_components:
            recommendations.append("📦 Gérer et optimiser les modèles")
        
        return recommendations
    
    def _identify_performance_bottlenecks(self, component_diagnostics: Dict[str, ComponentDiagnostic]) -> List[str]:
        """Identifie les goulots d'étranglement de performance"""
        
        bottlenecks = []
        
        for component_name, diagnostic in component_diagnostics.items():
            if diagnostic.health_score < 60:
                # Analyser les métriques pour identifier les goulots
                metrics = diagnostic.metrics
                
                if component_name == "memory" and metrics.get("memory_percent", 0) > 85:
                    bottlenecks.append(f"Mémoire RAM saturée ({metrics.get('memory_percent', 0):.1f}%)")
                
                if component_name == "gpu" and metrics.get("gpu_memory_percent", 0) > 85:
                    bottlenecks.append(f"Mémoire GPU saturée ({metrics.get('gpu_memory_percent', 0):.1f}%)")
                
                if component_name == "storage" and metrics.get("disk_percent", 0) > 90:
                    bottlenecks.append(f"Espace disque critique ({metrics.get('disk_percent', 0):.1f}%)")
                
                if component_name == "system" and metrics.get("cpu_usage", 0) > 90:
                    bottlenecks.append(f"CPU surchargé ({metrics.get('cpu_usage', 0):.1f}%)")
                
                if component_name == "network" and not metrics.get("http_connectivity", True):
                    bottlenecks.append("Connectivité réseau défaillante")
                
                if component_name == "performance":
                    if metrics.get("cpu_test_time", 0) > 0.1:
                        bottlenecks.append("Performance CPU dégradée")
                    if metrics.get("disk_test_time", 0) > 2.0:
                        bottlenecks.append("Performance disque lente")
        
        return bottlenecks
    
    def _save_to_history(self, report: SystemDiagnosticReport):
        """Sauvegarde le rapport dans l'historique"""
        
        self.diagnostic_history.append(report)
        
        # Limiter la taille de l'historique
        if len(self.diagnostic_history) > self.max_history_size:
            self.diagnostic_history = self.diagnostic_history[-self.max_history_size:]
        
        # Sauvegarder sur disque
        try:
            history_file = self.config_dir / "diagnostic_history.json"
            with open(history_file, 'w') as f:
                json.dump([report.to_dict() for report in self.diagnostic_history[-10:]], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save diagnostic history: {e}")
    
    def get_diagnostic_history(self, limit: int = 10) -> List[SystemDiagnosticReport]:
        """Retourne l'historique des diagnostics"""
        return self.diagnostic_history[-limit:] if limit else self.diagnostic_history
    
    def get_component_trend(self, component_name: str, metric_name: str, limit: int = 10) -> List[Tuple[float, float]]:
        """Retourne la tendance d'une métrique pour un composant"""
        
        trend_data = []
        
        for report in self.diagnostic_history[-limit:]:
            if component_name in report.component_diagnostics:
                component_diag = report.component_diagnostics[component_name]
                if metric_name in component_diag.metrics:
                    trend_data.append((report.timestamp, component_diag.metrics[metric_name]))
        
        return trend_data
    
    async def quick_health_check(self) -> Dict[str, Any]:
        """Vérification rapide de santé (composants critiques seulement)"""
        
        logger.info("Running quick health check...")
        
        quick_components = ["system", "memory", "storage", "gpu"]
        results = {}
        
        for component_name in quick_components:
            if component_name in self.components:
                try:
                    diagnostic = await self.components[component_name]()
                    results[component_name] = {
                        "status": diagnostic.status.value,
                        "health_score": diagnostic.health_score,
                        "critical_issues": len([i for i in diagnostic.issues if i.severity == DiagnosticSeverity.CRITICAL])
                    }
                except Exception as e:
                    results[component_name] = {
                        "status": "error",
                        "health_score": 0.0,
                        "error": str(e)
                    }
        
        # Score global rapide
        health_scores = [r.get("health_score", 0) for r in results.values() if isinstance(r.get("health_score"), (int, float))]
        overall_score = sum(health_scores) / len(health_scores) if health_scores else 0.0
        
        return {
            "overall_health_score": overall_score,
            "components": results,
            "timestamp": time.time()
        }

# Instance globale pour faciliter l'utilisation
diagnostic_engine = DiagnosticEngine()
