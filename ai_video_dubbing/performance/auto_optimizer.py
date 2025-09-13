"""
Optimisateur automatique pour cache et mémoire avec prédiction d'usage
"""

import asyncio
import logging
import time
import json
import gc
import os
import hashlib
import zlib
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import psutil

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """Types d'optimisation disponibles"""
    MEMORY_CLEANUP = "memory_cleanup"
    CACHE_COMPRESSION = "cache_compression"
    CACHE_PREDICTION = "cache_prediction"
    MODEL_VALIDATION = "model_validation"
    DISK_CLEANUP = "disk_cleanup"
    PRIORITY_ADJUSTMENT = "priority_adjustment"

class OptimizationPriority(Enum):
    """Priorités d'optimisation"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées"""
    key: str
    data: Any
    size_bytes: int
    created_time: float
    last_accessed: float
    access_count: int = 0
    compression_ratio: float = 1.0
    is_compressed: bool = False
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationRule:
    """Règle d'optimisation"""
    rule_id: str
    name: str
    description: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    trigger_condition: Callable[[], bool]
    optimization_action: Callable
    cooldown_seconds: float = 300.0
    last_executed: float = 0.0
    execution_count: int = 0
    success_rate: float = 1.0

@dataclass
class OptimizationResult:
    """Résultat d'une optimisation"""
    rule_id: str
    success: bool
    execution_time: float
    memory_saved_mb: float = 0.0
    disk_saved_mb: float = 0.0
    performance_improvement: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """Métriques système pour l'optimisation"""
    timestamp: float
    memory_usage_percent: float
    memory_available_mb: float
    cpu_usage_percent: float
    disk_usage_percent: float
    cache_size_mb: float
    active_processes: int
    gpu_memory_usage_percent: float = 0.0

class IntelligentCacheManager:
    """Gestionnaire de cache intelligent avec compression et prédiction"""
    
    def __init__(self, max_size_mb: int = 1024, cache_dir: str = ".kiro/cache"):
        self.max_size_mb = max_size_mb
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache en mémoire
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "decompressions": 0
        }
        
        # Prédiction d'usage
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.prediction_model: Dict[str, float] = {}
        
        # Configuration
        self.compression_threshold_mb = 10  # Compresser si > 10MB
        self.max_access_history = 100
        self.prediction_window_hours = 24
        
        logger.info(f"Intelligent Cache Manager initialized (max: {max_size_mb}MB)")
    
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une entrée du cache"""
        
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            entry.last_accessed = time.time()
            entry.access_count += 1
            
            # Enregistrer le pattern d'accès
            self._record_access_pattern(key)
            
            # Décompresser si nécessaire
            if entry.is_compressed:
                data = await self._decompress_data(entry.data)
                self.cache_stats["decompressions"] += 1
                return data
            
            self.cache_stats["hits"] += 1
            return entry.data
        
        # Essayer de charger depuis le disque
        disk_data = await self._load_from_disk(key)
        if disk_data is not None:
            await self.set(key, disk_data)
            return disk_data
        
        self.cache_stats["misses"] += 1
        return None
    
    async def set(self, key: str, data: Any, priority: int = 1) -> bool:
        """Stocke une entrée dans le cache"""
        
        try:
            # Calculer la taille
            data_size = self._calculate_size(data)
            
            # Vérifier si on doit compresser
            should_compress = data_size > self.compression_threshold_mb * 1024 * 1024
            
            if should_compress:
                compressed_data = await self._compress_data(data)
                compression_ratio = len(compressed_data) / data_size if data_size > 0 else 1.0
                actual_data = compressed_data
                actual_size = len(compressed_data)
                self.cache_stats["compressions"] += 1
            else:
                actual_data = data
                actual_size = data_size
                compression_ratio = 1.0
            
            # Créer l'entrée
            entry = CacheEntry(
                key=key,
                data=actual_data,
                size_bytes=actual_size,
                created_time=time.time(),
                last_accessed=time.time(),
                access_count=1,
                compression_ratio=compression_ratio,
                is_compressed=should_compress,
                priority=priority
            )
            
            # Vérifier l'espace disponible
            await self._ensure_space_available(actual_size)
            
            # Stocker en mémoire
            self.memory_cache[key] = entry
            
            # Sauvegarder sur disque si important
            if priority >= 3:
                await self._save_to_disk(key, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache entry {key}: {e}")
            return False
    
    async def _ensure_space_available(self, required_bytes: int):
        """S'assure qu'il y a assez d'espace dans le cache"""
        
        current_size = sum(entry.size_bytes for entry in self.memory_cache.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024
        
        if current_size + required_bytes <= max_size_bytes:
            return
        
        # Calculer l'espace à libérer
        space_to_free = (current_size + required_bytes) - max_size_bytes
        
        # Trier les entrées par priorité d'éviction
        entries_by_priority = sorted(
            self.memory_cache.items(),
            key=lambda x: self._calculate_eviction_score(x[1])
        )
        
        freed_space = 0
        for key, entry in entries_by_priority:
            if freed_space >= space_to_free:
                break
            
            # Sauvegarder sur disque si priorité élevée
            if entry.priority >= 2:
                await self._save_to_disk(key, entry.data)
            
            freed_space += entry.size_bytes
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1
    
    def _calculate_eviction_score(self, entry: CacheEntry) -> float:
        """Calcule le score d'éviction (plus bas = évincé en premier)"""
        
        age_hours = (time.time() - entry.last_accessed) / 3600
        access_frequency = entry.access_count / max(age_hours, 0.1)
        
        # Prédire la probabilité d'accès futur
        future_access_prob = self._predict_future_access(entry.key)
        
        # Score combiné (plus bas = plus susceptible d'être évincé)
        score = (entry.priority * 100) + (access_frequency * 10) + (future_access_prob * 50) - age_hours
        
        return score
    
    def _predict_future_access(self, key: str) -> float:
        """Prédit la probabilité d'accès futur"""
        
        if key not in self.access_patterns:
            return 0.1  # Probabilité par défaut
        
        # Analyser les patterns d'accès récents
        recent_accesses = self.access_patterns[key][-10:]  # 10 derniers accès
        
        if len(recent_accesses) < 2:
            return 0.1
        
        # Calculer l'intervalle moyen entre les accès
        intervals = [recent_accesses[i] - recent_accesses[i-1] for i in range(1, len(recent_accesses))]
        avg_interval = sum(intervals) / len(intervals)
        
        # Temps depuis le dernier accès
        time_since_last = time.time() - recent_accesses[-1]
        
        # Probabilité basée sur l'intervalle moyen
        if avg_interval > 0:
            probability = max(0.0, 1.0 - (time_since_last / avg_interval))
        else:
            probability = 0.5
        
        return min(1.0, probability)
    
    def _record_access_pattern(self, key: str):
        """Enregistre un pattern d'accès"""
        
        current_time = time.time()
        self.access_patterns[key].append(current_time)
        
        # Limiter l'historique
        if len(self.access_patterns[key]) > self.max_access_history:
            self.access_patterns[key] = self.access_patterns[key][-self.max_access_history:]
    
    async def _compress_data(self, data: Any) -> bytes:
        """Compresse les données"""
        
        try:
            # Sérialiser les données
            if isinstance(data, (str, bytes)):
                serialized = data.encode() if isinstance(data, str) else data
            else:
                serialized = json.dumps(data, default=str).encode()
            
            # Compresser avec zlib
            compressed = zlib.compress(serialized, level=6)
            return compressed
            
        except Exception as e:
            logger.error(f"Error compressing data: {e}")
            return data
    
    async def _decompress_data(self, compressed_data: bytes) -> Any:
        """Décompresse les données"""
        
        try:
            # Décompresser
            decompressed = zlib.decompress(compressed_data)
            
            # Essayer de désérialiser JSON
            try:
                return json.loads(decompressed.decode())
            except:
                return decompressed.decode()
                
        except Exception as e:
            logger.error(f"Error decompressing data: {e}")
            return compressed_data
    
    def _calculate_size(self, data: Any) -> int:
        """Calcule la taille approximative des données"""
        
        try:
            if isinstance(data, (str, bytes)):
                return len(data.encode() if isinstance(data, str) else data)
            else:
                return len(json.dumps(data, default=str).encode())
        except:
            return 1024  # Taille par défaut
    
    async def _save_to_disk(self, key: str, data: Any):
        """Sauvegarde sur disque"""
        
        try:
            file_path = self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
            
            with open(file_path, 'wb') as f:
                if isinstance(data, bytes):
                    f.write(data)
                else:
                    f.write(json.dumps(data, default=str).encode())
                    
        except Exception as e:
            logger.error(f"Error saving to disk: {e}")
    
    async def _load_from_disk(self, key: str) -> Optional[Any]:
        """Charge depuis le disque"""
        
        try:
            file_path = self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Essayer de désérialiser JSON
            try:
                return json.loads(data.decode())
            except:
                return data
                
        except Exception as e:
            logger.error(f"Error loading from disk: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        
        total_size = sum(entry.size_bytes for entry in self.memory_cache.values())
        
        return {
            "entries": len(self.memory_cache),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "usage_percent": (total_size / (self.max_size_mb * 1024 * 1024)) * 100,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": self.cache_stats["hits"] / max(self.cache_stats["hits"] + self.cache_stats["misses"], 1),
            "evictions": self.cache_stats["evictions"],
            "compressions": self.cache_stats["compressions"],
            "decompressions": self.cache_stats["decompressions"]
        }
    
    async def cleanup_expired_entries(self, max_age_hours: float = 24):
        """Nettoie les entrées expirées"""
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.last_accessed < cutoff_time and entry.priority < 3
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        return len(expired_keys)

class AutoOptimizer:
    """Optimisateur automatique pour cache et mémoire"""
    
    def __init__(self, cache_manager: Optional[IntelligentCacheManager] = None):
        self.cache_manager = cache_manager or IntelligentCacheManager()
        
        # Configuration
        self.config = {
            "optimization_interval": 300.0,  # 5 minutes
            "memory_threshold_percent": 80.0,
            "disk_threshold_percent": 90.0,
            "cache_cleanup_interval": 3600.0,  # 1 heure
            "model_validation_interval": 7200.0,  # 2 heures
            "enable_automatic_optimization": True,
            "enable_predictive_caching": True
        }
        
        # État interne
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.optimization_history: List[OptimizationResult] = []
        self.system_metrics_history: deque = deque(maxlen=100)
        
        # Tâches de monitoring
        self.optimization_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Statistiques
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "memory_saved_mb": 0.0,
            "disk_saved_mb": 0.0,
            "performance_improvements": 0
        }
        
        # Initialisation
        self._setup_default_rules()
        self._start_optimization_loop()
        
        logger.info("Auto Optimizer initialized")
    
    def _setup_default_rules(self):
        """Configure les règles d'optimisation par défaut"""
        
        # Règle de nettoyage mémoire
        self.add_optimization_rule(OptimizationRule(
            rule_id="memory_cleanup",
            name="Nettoyage mémoire automatique",
            description="Libère la mémoire quand l'usage dépasse le seuil",
            optimization_type=OptimizationType.MEMORY_CLEANUP,
            priority=OptimizationPriority.HIGH,
            trigger_condition=self._check_memory_threshold,
            optimization_action=self._perform_memory_cleanup,
            cooldown_seconds=300.0
        ))
        
        # Règle de compression de cache
        self.add_optimization_rule(OptimizationRule(
            rule_id="cache_compression",
            name="Compression du cache",
            description="Compresse les entrées de cache volumineuses",
            optimization_type=OptimizationType.CACHE_COMPRESSION,
            priority=OptimizationPriority.MEDIUM,
            trigger_condition=self._check_cache_size,
            optimization_action=self._perform_cache_compression,
            cooldown_seconds=600.0
        ))
        
        # Règle de nettoyage de cache
        self.add_optimization_rule(OptimizationRule(
            rule_id="cache_cleanup",
            name="Nettoyage du cache",
            description="Supprime les entrées de cache anciennes ou inutilisées",
            optimization_type=OptimizationType.CACHE_PREDICTION,
            priority=OptimizationPriority.MEDIUM,
            trigger_condition=self._check_cache_cleanup_needed,
            optimization_action=self._perform_cache_cleanup,
            cooldown_seconds=1800.0
        ))
        
        # Règle de validation des modèles
        self.add_optimization_rule(OptimizationRule(
            rule_id="model_validation",
            name="Validation des modèles",
            description="Vérifie l'intégrité des modèles en cache",
            optimization_type=OptimizationType.MODEL_VALIDATION,
            priority=OptimizationPriority.LOW,
            trigger_condition=self._check_model_validation_needed,
            optimization_action=self._perform_model_validation,
            cooldown_seconds=7200.0
        ))
        
        # Règle de nettoyage disque
        self.add_optimization_rule(OptimizationRule(
            rule_id="disk_cleanup",
            name="Nettoyage disque",
            description="Nettoie les fichiers temporaires et logs anciens",
            optimization_type=OptimizationType.DISK_CLEANUP,
            priority=OptimizationPriority.HIGH,
            trigger_condition=self._check_disk_threshold,
            optimization_action=self._perform_disk_cleanup,
            cooldown_seconds=1800.0
        ))
    
    def _start_optimization_loop(self):
        """Démarre la boucle d'optimisation"""
        
        try:
            self.optimization_task = asyncio.create_task(self._optimization_loop())
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        except RuntimeError:
            # Pas de boucle d'événements active
            pass
    
    async def _optimization_loop(self):
        """Boucle principale d'optimisation"""
        
        while True:
            try:
                if self.config["enable_automatic_optimization"]:
                    await self._run_optimization_cycle()
                
                await asyncio.sleep(self.config["optimization_interval"])
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Boucle de monitoring système"""
        
        while True:
            try:
                # Collecter les métriques système
                metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                await asyncio.sleep(60)  # Collecter toutes les minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collecte les métriques système"""
        
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            cache_stats = self.cache_manager.get_cache_stats()
            
            return SystemMetrics(
                timestamp=time.time(),
                memory_usage_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                cpu_usage_percent=cpu_percent,
                disk_usage_percent=disk.percent,
                cache_size_mb=cache_stats["total_size_mb"],
                active_processes=len(psutil.pids())
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                memory_usage_percent=0,
                memory_available_mb=0,
                cpu_usage_percent=0,
                disk_usage_percent=0,
                cache_size_mb=0,
                active_processes=0
            )
    
    async def _run_optimization_cycle(self):
        """Exécute un cycle d'optimisation"""
        
        logger.debug("Running optimization cycle")
        
        # Trier les règles par priorité
        rules_by_priority = sorted(
            self.optimization_rules.values(),
            key=lambda r: r.priority.value,
            reverse=True
        )
        
        for rule in rules_by_priority:
            try:
                # Vérifier le cooldown
                if time.time() - rule.last_executed < rule.cooldown_seconds:
                    continue
                
                # Vérifier la condition de déclenchement
                if await self._check_rule_condition(rule):
                    result = await self._execute_optimization_rule(rule)
                    
                    if result:
                        self.optimization_history.append(result)
                        self._update_optimization_stats(result)
                        
                        # Limiter l'historique
                        if len(self.optimization_history) > 1000:
                            self.optimization_history = self.optimization_history[-1000:]
                
            except Exception as e:
                logger.error(f"Error executing optimization rule {rule.rule_id}: {e}")
    
    async def _check_rule_condition(self, rule: OptimizationRule) -> bool:
        """Vérifie la condition de déclenchement d'une règle"""
        
        try:
            return rule.trigger_condition()
        except Exception as e:
            logger.error(f"Error checking rule condition {rule.rule_id}: {e}")
            return False
    
    async def _execute_optimization_rule(self, rule: OptimizationRule) -> Optional[OptimizationResult]:
        """Exécute une règle d'optimisation"""
        
        logger.info(f"Executing optimization rule: {rule.name}")
        
        start_time = time.time()
        
        try:
            # Exécuter l'action d'optimisation
            result_data = await rule.optimization_action()
            
            execution_time = time.time() - start_time
            
            # Mettre à jour les statistiques de la règle
            rule.last_executed = time.time()
            rule.execution_count += 1
            
            # Créer le résultat
            result = OptimizationResult(
                rule_id=rule.rule_id,
                success=True,
                execution_time=execution_time,
                **result_data
            )
            
            # Mettre à jour le taux de succès
            rule.success_rate = (rule.success_rate * (rule.execution_count - 1) + 1.0) / rule.execution_count
            
            logger.info(f"Optimization rule {rule.rule_id} completed successfully")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Mettre à jour les statistiques d'échec
            rule.last_executed = time.time()
            rule.execution_count += 1
            rule.success_rate = (rule.success_rate * (rule.execution_count - 1)) / rule.execution_count
            
            logger.error(f"Optimization rule {rule.rule_id} failed: {e}")
            
            return OptimizationResult(
                rule_id=rule.rule_id,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _update_optimization_stats(self, result: OptimizationResult):
        """Met à jour les statistiques d'optimisation"""
        
        self.optimization_stats["total_optimizations"] += 1
        
        if result.success:
            self.optimization_stats["successful_optimizations"] += 1
            self.optimization_stats["memory_saved_mb"] += result.memory_saved_mb
            self.optimization_stats["disk_saved_mb"] += result.disk_saved_mb
            
            if result.performance_improvement > 0:
                self.optimization_stats["performance_improvements"] += 1
    
    # Conditions de déclenchement
    
    def _check_memory_threshold(self) -> bool:
        """Vérifie si le seuil mémoire est dépassé"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent > self.config["memory_threshold_percent"]
        except:
            return False
    
    def _check_disk_threshold(self) -> bool:
        """Vérifie si le seuil disque est dépassé"""
        try:
            disk = psutil.disk_usage('/')
            return disk.percent > self.config["disk_threshold_percent"]
        except:
            return False
    
    def _check_cache_size(self) -> bool:
        """Vérifie si le cache est trop volumineux"""
        cache_stats = self.cache_manager.get_cache_stats()
        return cache_stats["usage_percent"] > 80
    
    def _check_cache_cleanup_needed(self) -> bool:
        """Vérifie si un nettoyage de cache est nécessaire"""
        cache_stats = self.cache_manager.get_cache_stats()
        return cache_stats["entries"] > 1000 or cache_stats["usage_percent"] > 70
    
    def _check_model_validation_needed(self) -> bool:
        """Vérifie si une validation des modèles est nécessaire"""
        # Vérifier périodiquement (toutes les 2 heures)
        return True  # Simplifié pour la démo
    
    # Actions d'optimisation
    
    async def _perform_memory_cleanup(self) -> Dict[str, Any]:
        """Effectue un nettoyage mémoire"""
        
        memory_before = psutil.virtual_memory().used
        
        # Force garbage collection
        gc.collect()
        
        # Nettoyer le cache si nécessaire
        if self.cache_manager.get_cache_stats()["usage_percent"] > 50:
            expired_count = await self.cache_manager.cleanup_expired_entries(max_age_hours=12)
            logger.info(f"Cleaned up {expired_count} expired cache entries")
        
        memory_after = psutil.virtual_memory().used
        memory_saved = max(0, memory_before - memory_after) / (1024 * 1024)
        
        return {
            "memory_saved_mb": memory_saved,
            "metadata": {"expired_entries_cleaned": expired_count if 'expired_count' in locals() else 0}
        }
    
    async def _perform_cache_compression(self) -> Dict[str, Any]:
        """Effectue une compression du cache"""
        
        compressed_count = 0
        space_saved = 0
        
        # Identifier les entrées non compressées volumineuses
        for key, entry in self.cache_manager.memory_cache.items():
            if not entry.is_compressed and entry.size_bytes > 1024 * 1024:  # > 1MB
                try:
                    # Compresser l'entrée
                    compressed_data = await self.cache_manager._compress_data(entry.data)
                    
                    if len(compressed_data) < entry.size_bytes:
                        space_saved += entry.size_bytes - len(compressed_data)
                        entry.data = compressed_data
                        entry.size_bytes = len(compressed_data)
                        entry.is_compressed = True
                        entry.compression_ratio = len(compressed_data) / entry.size_bytes
                        compressed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error compressing cache entry {key}: {e}")
        
        return {
            "memory_saved_mb": space_saved / (1024 * 1024),
            "metadata": {"entries_compressed": compressed_count}
        }
    
    async def _perform_cache_cleanup(self) -> Dict[str, Any]:
        """Effectue un nettoyage du cache"""
        
        initial_entries = len(self.cache_manager.memory_cache)
        initial_size = sum(entry.size_bytes for entry in self.cache_manager.memory_cache.values())
        
        # Nettoyer les entrées expirées
        expired_count = await self.cache_manager.cleanup_expired_entries(max_age_hours=6)
        
        # Nettoyer les entrées peu utilisées
        low_usage_keys = [
            key for key, entry in self.cache_manager.memory_cache.items()
            if entry.access_count < 2 and (time.time() - entry.created_time) > 3600
        ]
        
        for key in low_usage_keys[:10]:  # Limiter à 10 suppressions
            del self.cache_manager.memory_cache[key]
        
        final_entries = len(self.cache_manager.memory_cache)
        final_size = sum(entry.size_bytes for entry in self.cache_manager.memory_cache.values())
        
        entries_removed = initial_entries - final_entries
        space_saved = (initial_size - final_size) / (1024 * 1024)
        
        return {
            "memory_saved_mb": space_saved,
            "metadata": {
                "entries_removed": entries_removed,
                "expired_entries": expired_count,
                "low_usage_entries": len(low_usage_keys)
            }
        }
    
    async def _perform_model_validation(self) -> Dict[str, Any]:
        """Effectue une validation des modèles"""
        
        validated_count = 0
        corrupted_count = 0
        
        # Simuler la validation des modèles
        # Dans une vraie implémentation, cela vérifierait l'intégrité des fichiers
        
        model_keys = [key for key in self.cache_manager.memory_cache.keys() if 'model' in key.lower()]
        
        for key in model_keys:
            validated_count += 1
            # Simulation de validation
            await asyncio.sleep(0.01)  # Simuler le temps de validation
        
        return {
            "metadata": {
                "models_validated": validated_count,
                "corrupted_models": corrupted_count
            }
        }
    
    async def _perform_disk_cleanup(self) -> Dict[str, Any]:
        """Effectue un nettoyage disque"""
        
        space_saved = 0
        files_removed = 0
        
        # Nettoyer les fichiers temporaires
        temp_dirs = [Path(".kiro/temp"), Path("temp"), Path("/tmp")]
        
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                try:
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file() and (time.time() - file_path.stat().st_mtime) > 86400:  # > 24h
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            space_saved += file_size
                            files_removed += 1
                except Exception as e:
                    logger.error(f"Error cleaning temp directory {temp_dir}: {e}")
        
        return {
            "disk_saved_mb": space_saved / (1024 * 1024),
            "metadata": {"files_removed": files_removed}
        }
    
    # Méthodes publiques
    
    def add_optimization_rule(self, rule: OptimizationRule):
        """Ajoute une règle d'optimisation"""
        self.optimization_rules[rule.rule_id] = rule
        logger.info(f"Added optimization rule: {rule.name}")
    
    def remove_optimization_rule(self, rule_id: str):
        """Supprime une règle d'optimisation"""
        if rule_id in self.optimization_rules:
            del self.optimization_rules[rule_id]
            logger.info(f"Removed optimization rule: {rule_id}")
    
    async def run_manual_optimization(self) -> Dict[str, Any]:
        """Exécute une optimisation manuelle"""
        
        logger.info("Running manual optimization")
        
        results = []
        
        for rule in self.optimization_rules.values():
            if await self._check_rule_condition(rule):
                result = await self._execute_optimization_rule(rule)
                if result:
                    results.append(result)
                    self._update_optimization_stats(result)
        
        return {
            "timestamp": time.time(),
            "rules_executed": len(results),
            "successful_optimizations": sum(1 for r in results if r.success),
            "total_memory_saved_mb": sum(r.memory_saved_mb for r in results),
            "total_disk_saved_mb": sum(r.disk_saved_mb for r in results),
            "results": [
                {
                    "rule_id": r.rule_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "memory_saved_mb": r.memory_saved_mb,
                    "disk_saved_mb": r.disk_saved_mb
                }
                for r in results
            ]
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'optimisation"""
        
        cache_stats = self.cache_manager.get_cache_stats()
        
        return {
            "optimization_stats": self.optimization_stats.copy(),
            "cache_stats": cache_stats,
            "active_rules": len(self.optimization_rules),
            "recent_optimizations": len([
                r for r in self.optimization_history
                if time.time() - r.metadata.get("timestamp", 0) < 3600
            ]),
            "system_metrics": self.system_metrics_history[-1].__dict__ if self.system_metrics_history else {}
        }
    
    def get_optimization_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne l'historique des optimisations"""
        
        return [
            {
                "rule_id": r.rule_id,
                "success": r.success,
                "execution_time": r.execution_time,
                "memory_saved_mb": r.memory_saved_mb,
                "disk_saved_mb": r.disk_saved_mb,
                "error_message": r.error_message
            }
            for r in self.optimization_history[-limit:]
        ]
    
    async def shutdown(self):
        """Arrête proprement l'optimisateur"""
        
        logger.info("Shutting down Auto Optimizer")
        
        # Arrêter les tâches
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto Optimizer shutdown complete")

# Instance globale
_auto_optimizer: Optional[AutoOptimizer] = None

def get_auto_optimizer() -> AutoOptimizer:
    """Retourne l'instance globale de l'optimisateur"""
    global _auto_optimizer
    if _auto_optimizer is None:
        _auto_optimizer = AutoOptimizer()
    return _auto_optimizer

# Fonctions utilitaires

async def optimize_system() -> Dict[str, Any]:
    """Optimise le système manuellement"""
    optimizer = get_auto_optimizer()
    return await optimizer.run_manual_optimization()

async def get_system_optimization_stats() -> Dict[str, Any]:
    """Retourne les statistiques d'optimisation du système"""
    optimizer = get_auto_optimizer()
    return optimizer.get_optimization_stats()