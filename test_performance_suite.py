"""
Suite de tests de performance complète pour l'optimisation NeMo
"""

import asyncio
import time
import logging
import json
import tempfile
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Métrique de performance"""
    name: str
    value: float
    unit: str
    description: str
    baseline: Optional[float] = None
    target: Optional[float] = None
    
    @property
    def improvement_percent(self) -> Optional[float]:
        """Calcule le pourcentage d'amélioration par rapport à la baseline"""
        if self.baseline and self.baseline > 0:
            return ((self.value - self.baseline) / self.baseline) * 100
        return None
    
    @property
    def meets_target(self) -> Optional[bool]:
        """Vérifie si la métrique atteint la cible"""
        if self.target is None:
            return None
        return self.value >= self.target

@dataclass
class PerformanceTestResult:
    """Résultat d'un test de performance"""
    test_name: str
    duration: float
    success: bool
    metrics: List[PerformanceMetric] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceTestSuite:
    """Suite de tests de performance"""
    
    def __init__(self):
        self.results: List[PerformanceTestResult] = []
        self.baselines: Dict[str, float] = {}
        self.targets: Dict[str, float] = {}
        
        # Charger les baselines et targets
        self._load_performance_baselines()
    
    def _load_performance_baselines(self):
        """Charge les baselines et targets de performance"""
        
        # Baselines (performances avant optimisation)
        self.baselines = {
            "cache_hit_rate": 0.60,  # 60% de hit rate
            "memory_usage_mb": 2048,  # 2GB d'usage mémoire
            "download_speed_mbps": 10,  # 10 Mbps
            "model_load_time_s": 30,  # 30 secondes
            "transcription_speed_ratio": 0.5,  # 0.5x temps réel
            "error_recovery_time_s": 5,  # 5 secondes
            "optimization_frequency_per_hour": 2,  # 2 optimisations par heure
            "disk_usage_mb": 5120,  # 5GB d'usage disque
            "concurrent_operations": 2,  # 2 opérations simultanées
            "system_responsiveness_ms": 500  # 500ms de réponse
        }
        
        # Targets (objectifs après optimisation)
        self.targets = {
            "cache_hit_rate": 0.85,  # 85% de hit rate
            "memory_usage_mb": 1536,  # 1.5GB d'usage mémoire
            "download_speed_mbps": 25,  # 25 Mbps
            "model_load_time_s": 15,  # 15 secondes
            "transcription_speed_ratio": 1.0,  # 1x temps réel
            "error_recovery_time_s": 2,  # 2 secondes
            "optimization_frequency_per_hour": 6,  # 6 optimisations par heure
            "disk_usage_mb": 3072,  # 3GB d'usage disque
            "concurrent_operations": 8,  # 8 opérations simultanées
            "system_responsiveness_ms": 200  # 200ms de réponse
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests de performance"""
        
        print("🚀 Démarrage de la suite de tests de performance\n")
        
        start_time = time.time()
        
        # Tests de performance par composant
        test_methods = [
            self.test_cache_performance,
            self.test_memory_optimization,
            self.test_network_performance,
            self.test_error_recovery_performance,
            self.test_auto_optimization_performance,
            self.test_concurrent_operations,
            self.test_system_responsiveness,
            self.test_integration_performance
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test failed: {test_method.__name__}: {e}")
                self.results.append(PerformanceTestResult(
                    test_name=test_method.__name__,
                    duration=0,
                    success=False,
                    error_message=str(e)
                ))
        
        total_duration = time.time() - start_time
        
        # Générer le rapport
        report = self._generate_performance_report(total_duration)
        
        print(f"\n⏱️ Suite de tests terminée en {total_duration:.2f}s")
        
        return report
    
    async def test_cache_performance(self):
        """Test de performance du cache"""
        
        print("=== Test de Performance du Cache ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.auto_optimizer import IntelligentCacheManager
            
            cache = IntelligentCacheManager(max_size_mb=50)
            
            # Test de performance d'écriture
            write_times = []
            for i in range(100):
                key = f"test_key_{i}"
                data = f"test_data_{i}" * 1000  # ~10KB par entrée
                
                write_start = time.time()
                await cache.set(key, data)
                write_times.append(time.time() - write_start)
            
            # Test de performance de lecture
            read_times = []
            hits = 0
            for i in range(100):
                key = f"test_key_{i}"
                
                read_start = time.time()
                result = await cache.get(key)
                read_times.append(time.time() - read_start)
                
                if result is not None:
                    hits += 1
            
            # Calculer les métriques
            avg_write_time = statistics.mean(write_times) * 1000  # en ms
            avg_read_time = statistics.mean(read_times) * 1000  # en ms
            hit_rate = hits / 100
            
            cache_stats = cache.get_cache_stats()
            
            metrics = [
                PerformanceMetric(
                    name="cache_hit_rate",
                    value=hit_rate,
                    unit="ratio",
                    description="Taux de hit du cache",
                    baseline=self.baselines.get("cache_hit_rate"),
                    target=self.targets.get("cache_hit_rate")
                ),
                PerformanceMetric(
                    name="cache_write_time",
                    value=avg_write_time,
                    unit="ms",
                    description="Temps moyen d'écriture en cache"
                ),
                PerformanceMetric(
                    name="cache_read_time",
                    value=avg_read_time,
                    unit="ms",
                    description="Temps moyen de lecture du cache"
                ),
                PerformanceMetric(
                    name="cache_memory_usage",
                    value=cache_stats["total_size_mb"],
                    unit="MB",
                    description="Utilisation mémoire du cache"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="cache_performance",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={"cache_stats": cache_stats}
            ))
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Hit rate: {hit_rate:.2%}")
            print(f"   Temps d'écriture: {avg_write_time:.2f}ms")
            print(f"   Temps de lecture: {avg_read_time:.2f}ms")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="cache_performance",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_memory_optimization(self):
        """Test de performance de l'optimisation mémoire"""
        
        print("\n=== Test de Performance de l'Optimisation Mémoire ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.auto_optimizer import AutoOptimizer
            import psutil
            
            # Mesurer la mémoire avant
            memory_before = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            optimizer = AutoOptimizer()
            
            # Remplir le cache pour simuler l'usage mémoire
            cache_manager = optimizer.cache_manager
            for i in range(50):
                key = f"memory_test_{i}"
                data = "x" * (1024 * 200)  # 200KB par entrée
                await cache_manager.set(key, data)
            
            memory_after_fill = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            # Exécuter l'optimisation
            optimization_start = time.time()
            result = await optimizer.run_manual_optimization()
            optimization_time = time.time() - optimization_start
            
            # Mesurer la mémoire après optimisation
            memory_after_opt = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            # Calculer les métriques
            memory_saved = memory_after_fill - memory_after_opt
            memory_usage = memory_after_opt
            
            metrics = [
                PerformanceMetric(
                    name="memory_usage_mb",
                    value=memory_usage,
                    unit="MB",
                    description="Utilisation mémoire après optimisation",
                    baseline=self.baselines.get("memory_usage_mb"),
                    target=self.targets.get("memory_usage_mb")
                ),
                PerformanceMetric(
                    name="memory_saved_mb",
                    value=memory_saved,
                    unit="MB",
                    description="Mémoire économisée par l'optimisation"
                ),
                PerformanceMetric(
                    name="optimization_time",
                    value=optimization_time,
                    unit="s",
                    description="Temps d'exécution de l'optimisation"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="memory_optimization",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={"optimization_result": result}
            ))
            
            await optimizer.shutdown()
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Mémoire utilisée: {memory_usage:.1f} MB")
            print(f"   Mémoire économisée: {memory_saved:.1f} MB")
            print(f"   Temps d'optimisation: {optimization_time:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="memory_optimization",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_network_performance(self):
        """Test de performance réseau"""
        
        print("\n=== Test de Performance Réseau ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.network_optimizer import NetworkOptimizer
            
            optimizer = NetworkOptimizer()
            
            # Test de vitesse de téléchargement
            test_url = "https://httpbin.org/json"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                file_path = temp_path / "network_test.json"
                
                download_start = time.time()
                task = await optimizer.download_with_segments(test_url, file_path)
                download_time = time.time() - download_start
                
                # Calculer la vitesse
                if download_time > 0 and task.total_size > 0:
                    speed_mbps = (task.total_size * 8) / (download_time * 1024 * 1024)
                else:
                    speed_mbps = 0
                
                # Test de performance des serveurs
                server_test_start = time.time()
                server_results = await optimizer.test_all_servers()
                server_test_time = time.time() - server_test_start
                
                # Calculer la latence moyenne
                latencies = []
                for result in server_results.values():
                    if result.get('success') and 'latency_ms' in result:
                        latencies.append(result['latency_ms'])
                
                avg_latency = statistics.mean(latencies) if latencies else 0
                
                metrics = [
                    PerformanceMetric(
                        name="download_speed_mbps",
                        value=speed_mbps,
                        unit="Mbps",
                        description="Vitesse de téléchargement",
                        baseline=self.baselines.get("download_speed_mbps"),
                        target=self.targets.get("download_speed_mbps")
                    ),
                    PerformanceMetric(
                        name="server_test_time",
                        value=server_test_time,
                        unit="s",
                        description="Temps de test des serveurs"
                    ),
                    PerformanceMetric(
                        name="average_latency",
                        value=avg_latency,
                        unit="ms",
                        description="Latence moyenne des serveurs"
                    )
                ]
                
                duration = time.time() - start_time
                
                self.results.append(PerformanceTestResult(
                    test_name="network_performance",
                    duration=duration,
                    success=True,
                    metrics=metrics,
                    metadata={
                        "download_task": {
                            "size": task.total_size,
                            "segments": len(task.segments),
                            "status": task.status
                        },
                        "server_results": server_results
                    }
                ))
                
                await optimizer.shutdown()
                
                print(f"   ✅ Test terminé en {duration:.2f}s")
                print(f"   Vitesse de téléchargement: {speed_mbps:.2f} Mbps")
                print(f"   Latence moyenne: {avg_latency:.1f} ms")
                print(f"   Serveurs testés: {len(server_results)}")
        
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="network_performance",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_error_recovery_performance(self):
        """Test de performance de la récupération d'erreurs"""
        
        print("\n=== Test de Performance de la Récupération d'Erreurs ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.error_recovery_manager import (
                get_error_recovery_manager,
                create_error_context,
                ErrorType,
                ErrorSeverity
            )
            
            manager = get_error_recovery_manager()
            
            # Test de temps de récupération
            recovery_times = []
            successful_recoveries = 0
            
            for i in range(10):
                error_context = create_error_context(
                    error_type=ErrorType.MEMORY_ERROR,
                    error_message=f"Test error {i}",
                    component="performance_test",
                    severity=ErrorSeverity.MEDIUM
                )
                
                recovery_start = time.time()
                result = await manager.handle_error(error_context)
                recovery_time = time.time() - recovery_start
                
                recovery_times.append(recovery_time)
                
                if result and result.success:
                    successful_recoveries += 1
            
            # Calculer les métriques
            avg_recovery_time = statistics.mean(recovery_times)
            recovery_success_rate = successful_recoveries / 10
            
            metrics = [
                PerformanceMetric(
                    name="error_recovery_time_s",
                    value=avg_recovery_time,
                    unit="s",
                    description="Temps moyen de récupération d'erreur",
                    baseline=self.baselines.get("error_recovery_time_s"),
                    target=self.targets.get("error_recovery_time_s")
                ),
                PerformanceMetric(
                    name="recovery_success_rate",
                    value=recovery_success_rate,
                    unit="ratio",
                    description="Taux de succès de récupération"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="error_recovery_performance",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={
                    "recovery_times": recovery_times,
                    "successful_recoveries": successful_recoveries
                }
            ))
            
            await manager.shutdown()
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Temps de récupération moyen: {avg_recovery_time:.2f}s")
            print(f"   Taux de succès: {recovery_success_rate:.1%}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="error_recovery_performance",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_auto_optimization_performance(self):
        """Test de performance de l'optimisation automatique"""
        
        print("\n=== Test de Performance de l'Optimisation Automatique ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
            
            optimizer = get_auto_optimizer()
            
            # Mesurer la fréquence d'optimisation
            optimization_times = []
            
            for i in range(5):
                opt_start = time.time()
                result = await optimizer.run_manual_optimization()
                opt_time = time.time() - opt_start
                optimization_times.append(opt_time)
                
                # Petite pause entre les optimisations
                await asyncio.sleep(0.1)
            
            # Calculer les métriques
            avg_optimization_time = statistics.mean(optimization_times)
            optimizations_per_hour = 3600 / avg_optimization_time if avg_optimization_time > 0 else 0
            
            stats = optimizer.get_optimization_stats()
            
            metrics = [
                PerformanceMetric(
                    name="optimization_frequency_per_hour",
                    value=optimizations_per_hour,
                    unit="ops/hour",
                    description="Fréquence d'optimisation par heure",
                    baseline=self.baselines.get("optimization_frequency_per_hour"),
                    target=self.targets.get("optimization_frequency_per_hour")
                ),
                PerformanceMetric(
                    name="avg_optimization_time",
                    value=avg_optimization_time,
                    unit="s",
                    description="Temps moyen d'optimisation"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="auto_optimization_performance",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={
                    "optimization_stats": stats,
                    "optimization_times": optimization_times
                }
            ))
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Temps d'optimisation moyen: {avg_optimization_time:.3f}s")
            print(f"   Fréquence théorique: {optimizations_per_hour:.1f} opt/heure")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="auto_optimization_performance",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_concurrent_operations(self):
        """Test de performance des opérations concurrentes"""
        
        print("\n=== Test de Performance des Opérations Concurrentes ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.auto_optimizer import IntelligentCacheManager
            
            # Test de concurrence sur le cache
            cache = IntelligentCacheManager(max_size_mb=100)
            
            async def concurrent_cache_operation(operation_id: int):
                """Opération de cache concurrente"""
                for i in range(20):
                    key = f"concurrent_{operation_id}_{i}"
                    data = f"data_{operation_id}_{i}" * 100
                    
                    # Écriture
                    await cache.set(key, data)
                    
                    # Lecture
                    result = await cache.get(key)
                    
                    if result is None:
                        raise Exception(f"Failed to retrieve {key}")
            
            # Lancer plusieurs opérations concurrentes
            concurrent_start = time.time()
            
            tasks = [concurrent_cache_operation(i) for i in range(8)]
            await asyncio.gather(*tasks)
            
            concurrent_time = time.time() - concurrent_start
            
            # Vérifier les statistiques du cache
            cache_stats = cache.get_cache_stats()
            
            metrics = [
                PerformanceMetric(
                    name="concurrent_operations",
                    value=8,
                    unit="ops",
                    description="Nombre d'opérations concurrentes",
                    baseline=self.baselines.get("concurrent_operations"),
                    target=self.targets.get("concurrent_operations")
                ),
                PerformanceMetric(
                    name="concurrent_execution_time",
                    value=concurrent_time,
                    unit="s",
                    description="Temps d'exécution concurrente"
                ),
                PerformanceMetric(
                    name="cache_hit_rate_concurrent",
                    value=cache_stats["hit_rate"],
                    unit="ratio",
                    description="Taux de hit en mode concurrent"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="concurrent_operations",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={"cache_stats": cache_stats}
            ))
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Opérations concurrentes: 8")
            print(f"   Temps d'exécution: {concurrent_time:.2f}s")
            print(f"   Hit rate concurrent: {cache_stats['hit_rate']:.2%}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="concurrent_operations",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_system_responsiveness(self):
        """Test de réactivité du système"""
        
        print("\n=== Test de Réactivité du Système ===")
        
        start_time = time.time()
        
        try:
            from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
            
            analyzer = get_error_prevention_analyzer()
            
            # Test de temps de réponse
            response_times = []
            
            for i in range(20):
                response_start = time.time()
                
                # Opération de vérification système
                health_metrics = analyzer.get_health_metrics()
                active_alerts = analyzer.get_active_alerts()
                stats = analyzer.get_prevention_stats()
                
                response_time = (time.time() - response_start) * 1000  # en ms
                response_times.append(response_time)
            
            # Calculer les métriques de réactivité
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            metrics = [
                PerformanceMetric(
                    name="system_responsiveness_ms",
                    value=avg_response_time,
                    unit="ms",
                    description="Temps de réponse moyen du système",
                    baseline=self.baselines.get("system_responsiveness_ms"),
                    target=self.targets.get("system_responsiveness_ms")
                ),
                PerformanceMetric(
                    name="max_response_time",
                    value=max_response_time,
                    unit="ms",
                    description="Temps de réponse maximum"
                ),
                PerformanceMetric(
                    name="min_response_time",
                    value=min_response_time,
                    unit="ms",
                    description="Temps de réponse minimum"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="system_responsiveness",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={
                    "response_times": response_times,
                    "health_metrics": health_metrics.__dict__ if health_metrics else None
                }
            ))
            
            await analyzer.shutdown()
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Temps de réponse moyen: {avg_response_time:.1f}ms")
            print(f"   Temps de réponse min/max: {min_response_time:.1f}/{max_response_time:.1f}ms")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="system_responsiveness",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    async def test_integration_performance(self):
        """Test de performance d'intégration"""
        
        print("\n=== Test de Performance d'Intégration ===")
        
        start_time = time.time()
        
        try:
            # Test d'intégration de tous les composants
            from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
            from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
            from ai_video_dubbing.performance.network_optimizer import get_network_optimizer
            
            # Initialiser tous les composants
            auto_optimizer = get_auto_optimizer()
            prevention_analyzer = get_error_prevention_analyzer()
            network_optimizer = get_network_optimizer()
            
            # Test d'intégration : optimisation complète
            integration_start = time.time()
            
            # 1. Vérification préventive
            prevention_check = await prevention_analyzer.run_manual_check()
            
            # 2. Optimisation automatique
            optimization_result = await auto_optimizer.run_manual_optimization()
            
            # 3. Test réseau
            network_stats = network_optimizer.get_network_stats()
            
            integration_time = time.time() - integration_start
            
            # Calculer les métriques d'intégration
            total_components = 3
            successful_components = 0
            
            if prevention_check["rules_checked"] > 0:
                successful_components += 1
            if optimization_result["rules_executed"] > 0:
                successful_components += 1
            if network_stats["server_count"] > 0:
                successful_components += 1
            
            integration_success_rate = successful_components / total_components
            
            metrics = [
                PerformanceMetric(
                    name="integration_time",
                    value=integration_time,
                    unit="s",
                    description="Temps d'intégration complète"
                ),
                PerformanceMetric(
                    name="integration_success_rate",
                    value=integration_success_rate,
                    unit="ratio",
                    description="Taux de succès d'intégration"
                ),
                PerformanceMetric(
                    name="components_active",
                    value=successful_components,
                    unit="count",
                    description="Nombre de composants actifs"
                )
            ]
            
            duration = time.time() - start_time
            
            self.results.append(PerformanceTestResult(
                test_name="integration_performance",
                duration=duration,
                success=True,
                metrics=metrics,
                metadata={
                    "prevention_check": prevention_check,
                    "optimization_result": optimization_result,
                    "network_stats": network_stats
                }
            ))
            
            # Arrêter tous les composants
            await auto_optimizer.shutdown()
            await prevention_analyzer.shutdown()
            await network_optimizer.shutdown()
            
            print(f"   ✅ Test terminé en {duration:.2f}s")
            print(f"   Temps d'intégration: {integration_time:.2f}s")
            print(f"   Composants actifs: {successful_components}/{total_components}")
            print(f"   Taux de succès: {integration_success_rate:.1%}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(PerformanceTestResult(
                test_name="integration_performance",
                duration=duration,
                success=False,
                error_message=str(e)
            ))
            print(f"   ❌ Test échoué: {e}")
    
    def _generate_performance_report(self, total_duration: float) -> Dict[str, Any]:
        """Génère un rapport de performance complet"""
        
        print("\n" + "="*60)
        print("📊 RAPPORT DE PERFORMANCE COMPLET")
        print("="*60)
        
        # Statistiques générales
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        print(f"\n📈 Statistiques Générales:")
        print(f"   Tests exécutés: {total_tests}")
        print(f"   Tests réussis: {successful_tests}")
        print(f"   Tests échoués: {failed_tests}")
        print(f"   Taux de succès: {(successful_tests/total_tests)*100:.1f}%")
        print(f"   Durée totale: {total_duration:.2f}s")
        
        # Analyse des métriques
        all_metrics = []
        for result in self.results:
            all_metrics.extend(result.metrics)
        
        print(f"\n🎯 Analyse des Métriques ({len(all_metrics)} métriques):")
        
        # Grouper par nom de métrique
        metrics_by_name = {}
        for metric in all_metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)
        
        # Analyser chaque métrique
        performance_summary = {}
        
        for metric_name, metrics in metrics_by_name.items():
            if not metrics:
                continue
            
            # Prendre la première métrique pour les infos de base
            first_metric = metrics[0]
            
            # Calculer les statistiques
            values = [m.value for m in metrics]
            avg_value = statistics.mean(values) if values else 0
            
            # Vérifier les améliorations et cibles
            improvement = first_metric.improvement_percent
            meets_target = first_metric.meets_target
            
            performance_summary[metric_name] = {
                "value": avg_value,
                "unit": first_metric.unit,
                "description": first_metric.description,
                "improvement_percent": improvement,
                "meets_target": meets_target,
                "baseline": first_metric.baseline,
                "target": first_metric.target
            }
            
            # Affichage
            status = ""
            if meets_target is True:
                status = "🎯 CIBLE ATTEINTE"
            elif meets_target is False:
                status = "⚠️ CIBLE NON ATTEINTE"
            
            improvement_text = ""
            if improvement is not None:
                if improvement > 0:
                    improvement_text = f"📈 +{improvement:.1f}%"
                else:
                    improvement_text = f"📉 {improvement:.1f}%"
            
            print(f"   • {first_metric.description}:")
            print(f"     Valeur: {avg_value:.2f} {first_metric.unit}")
            if improvement_text:
                print(f"     Amélioration: {improvement_text}")
            if status:
                print(f"     Statut: {status}")
        
        # Tests échoués
        if failed_tests > 0:
            print(f"\n❌ Tests Échoués ({failed_tests}):")
            for result in self.results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.error_message}")
        
        # Recommandations
        print(f"\n💡 Recommandations:")
        
        recommendations = []
        
        # Analyser les métriques pour des recommandations
        for metric_name, summary in performance_summary.items():
            if summary["meets_target"] is False:
                recommendations.append(
                    f"Améliorer {summary['description']} "
                    f"(actuel: {summary['value']:.2f}, cible: {summary['target']:.2f})"
                )
        
        if not recommendations:
            recommendations.append("Toutes les métriques de performance sont dans les objectifs ✅")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Créer le rapport final
        report = {
            "timestamp": time.time(),
            "total_duration": total_duration,
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests/total_tests) if total_tests > 0 else 0
            },
            "performance_metrics": performance_summary,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "duration": r.duration,
                    "success": r.success,
                    "error_message": r.error_message,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "unit": m.unit,
                            "description": m.description,
                            "improvement_percent": m.improvement_percent,
                            "meets_target": m.meets_target
                        }
                        for m in r.metrics
                    ]
                }
                for r in self.results
            ],
            "recommendations": recommendations
        }
        
        # Sauvegarder le rapport
        self._save_performance_report(report)
        
        return report
    
    def _save_performance_report(self, report: Dict[str, Any]):
        """Sauvegarde le rapport de performance"""
        
        try:
            report_dir = Path(".kiro/performance_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"performance_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n💾 Rapport sauvegardé: {report_file}")
            
        except Exception as e:
            print(f"\n⚠️ Erreur lors de la sauvegarde du rapport: {e}")

async def main():
    """Fonction principale"""
    
    suite = PerformanceTestSuite()
    report = await suite.run_all_tests()
    
    # Afficher un résumé final
    print(f"\n🏁 Suite de tests terminée!")
    print(f"   Tests réussis: {report['test_summary']['successful_tests']}/{report['test_summary']['total_tests']}")
    print(f"   Durée totale: {report['total_duration']:.2f}s")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())