#!/usr/bin/env python3
"""
Gestionnaire de cache intelligent pour optimiser les performances.
"""

import os
import pickle
import hashlib
import time
import threading
from typing import Any, Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from .performance_optimizer import OptimizationConfig


@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées."""
    key: str
    data: Any
    timestamp: float
    access_count: int
    size_bytes: int
    ttl: Optional[float] = None  # Time to live en secondes


class InMemoryCache:
    """Cache en mémoire avec gestion LRU et TTL."""
    
    def __init__(self, max_size_mb: int = 500, max_entries: int = 1000):
        """
        Initialise le cache en mémoire.
        
        Args:
            max_size_mb: Taille maximale du cache en MB
            max_entries: Nombre maximum d'entrées
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.current_size = 0
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Statistiques
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Vérifier TTL
            if entry.ttl and time.time() - entry.timestamp > entry.ttl:
                self._remove_entry(key)
                self.misses += 1
                return None
            
            # Mettre à jour les statistiques d'accès
            entry.access_count += 1
            self.hits += 1
            
            return entry.data
    
    def put(self, key: str, data: Any, ttl: Optional[float] = None):
        """Ajoute une valeur au cache."""
        with self.lock:
            # Calculer la taille
            size_bytes = self._estimate_size(data)
            
            # Vérifier si on doit faire de la place
            if key not in self.cache:
                while (len(self.cache) >= self.max_entries or 
                       self.current_size + size_bytes > self.max_size_bytes):
                    if not self._evict_lru():
                        break
            
            # Créer l'entrée
            entry = CacheEntry(
                key=key,
                data=data,
                timestamp=time.time(),
                access_count=1,
                size_bytes=size_bytes,
                ttl=ttl
            )
            
            # Mettre à jour le cache
            if key in self.cache:
                self.current_size -= self.cache[key].size_bytes
            
            self.cache[key] = entry
            self.current_size += size_bytes
    
    def remove(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        with self.lock:
            return self._remove_entry(key)
    
    def clear(self):
        """Vide le cache."""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
            self.logger.info("Cache vidé")
    
    def _remove_entry(self, key: str) -> bool:
        """Supprime une entrée (méthode interne)."""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.current_size -= entry.size_bytes
            return True
        return False
    
    def _evict_lru(self) -> bool:
        """Évince l'entrée la moins récemment utilisée."""
        if not self.cache:
            return False
        
        # Trouver l'entrée LRU (combinaison timestamp et access_count)
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].access_count, self.cache[k].timestamp)
        )
        
        self._remove_entry(lru_key)
        self.evictions += 1
        return True
    
    def _estimate_size(self, data: Any) -> int:
        """Estime la taille d'un objet en bytes."""
        try:
            import sys
            return sys.getsizeof(data)
        except:
            # Estimation par défaut
            return 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self.cache),
                'size_mb': self.current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions
            }


class DiskCache:
    """Cache sur disque pour les données persistantes."""
    
    def __init__(self, cache_dir: str = "./cache", max_size_gb: float = 2.0):
        """
        Initialise le cache disque.
        
        Args:
            cache_dir: Répertoire de cache
            max_size_gb: Taille maximale en GB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Index des fichiers
        self.index_file = self.cache_dir / "cache_index.pkl"
        self.index: Dict[str, Dict] = self._load_index()
        
        # Statistiques
        self.hits = 0
        self.misses = 0
    
    def _load_index(self) -> Dict[str, Dict]:
        """Charge l'index du cache."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                self.logger.warning(f"Erreur chargement index cache: {e}")
        
        return {}
    
    def _save_index(self):
        """Sauvegarde l'index du cache."""
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.index, f)
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde index cache: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Retourne le chemin de fichier pour une clé."""
        # Hasher la clé pour éviter les problèmes de noms de fichiers
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache disque."""
        with self.lock:
            if key not in self.index:
                self.misses += 1
                return None
            
            entry_info = self.index[key]
            cache_path = self._get_cache_path(key)
            
            # Vérifier que le fichier existe
            if not cache_path.exists():
                del self.index[key]
                self._save_index()
                self.misses += 1
                return None
            
            # Vérifier TTL
            if entry_info.get('ttl') and time.time() - entry_info['timestamp'] > entry_info['ttl']:
                self.remove(key)
                self.misses += 1
                return None
            
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Mettre à jour les statistiques
                entry_info['access_count'] = entry_info.get('access_count', 0) + 1
                entry_info['last_access'] = time.time()
                self._save_index()
                
                self.hits += 1
                return data
                
            except Exception as e:
                self.logger.error(f"Erreur lecture cache {key}: {e}")
                self.remove(key)
                self.misses += 1
                return None
    
    def put(self, key: str, data: Any, ttl: Optional[float] = None):
        """Ajoute une valeur au cache disque."""
        with self.lock:
            cache_path = self._get_cache_path(key)
            
            try:
                # Sauvegarder les données
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                
                # Mettre à jour l'index
                file_size = cache_path.stat().st_size
                self.index[key] = {
                    'timestamp': time.time(),
                    'size': file_size,
                    'access_count': 1,
                    'last_access': time.time(),
                    'ttl': ttl
                }
                
                self._save_index()
                
                # Vérifier la taille totale et nettoyer si nécessaire
                self._cleanup_if_needed()
                
            except Exception as e:
                self.logger.error(f"Erreur écriture cache {key}: {e}")
    
    def remove(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        with self.lock:
            if key not in self.index:
                return False
            
            cache_path = self._get_cache_path(key)
            
            try:
                if cache_path.exists():
                    cache_path.unlink()
                
                del self.index[key]
                self._save_index()
                return True
                
            except Exception as e:
                self.logger.error(f"Erreur suppression cache {key}: {e}")
                return False
    
    def clear(self):
        """Vide le cache disque."""
        with self.lock:
            for key in list(self.index.keys()):
                self.remove(key)
            
            self.logger.info("Cache disque vidé")
    
    def _cleanup_if_needed(self):
        """Nettoie le cache si nécessaire."""
        total_size = sum(entry['size'] for entry in self.index.values())
        
        if total_size > self.max_size_bytes:
            # Trier par dernière utilisation
            sorted_keys = sorted(
                self.index.keys(),
                key=lambda k: (self.index[k].get('access_count', 0), self.index[k].get('last_access', 0))
            )
            
            # Supprimer les plus anciens
            for key in sorted_keys:
                if total_size <= self.max_size_bytes * 0.8:  # Garder 20% de marge
                    break
                
                entry_size = self.index[key]['size']
                if self.remove(key):
                    total_size -= entry_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache disque."""
        with self.lock:
            total_size = sum(entry['size'] for entry in self.index.values())
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self.index),
                'size_gb': total_size / (1024 * 1024 * 1024),
                'max_size_gb': self.max_size_bytes / (1024 * 1024 * 1024),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate
            }


class CacheManager:
    """Gestionnaire de cache multi-niveaux."""
    
    def __init__(self, config: OptimizationConfig = None):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            config: Configuration d'optimisation
        """
        self.config = config or OptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Caches
        self.memory_cache = InMemoryCache(max_size_mb=200, max_entries=500)
        self.disk_cache = DiskCache(max_size_gb=1.0)
        
        # Stratégies de cache par type de données
        self.cache_strategies = {
            'model_weights': {'memory': False, 'disk': True, 'ttl': 3600},  # 1h
            'audio_features': {'memory': True, 'disk': True, 'ttl': 1800},  # 30min
            'transcription': {'memory': True, 'disk': True, 'ttl': 7200},   # 2h
            'processed_audio': {'memory': False, 'disk': True, 'ttl': 1800}, # 30min
            'temp_results': {'memory': True, 'disk': False, 'ttl': 300}     # 5min
        }
    
    def get(self, key: str, data_type: str = 'default') -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de cache
            data_type: Type de données pour la stratégie
            
        Returns:
            Données cachées ou None
        """
        strategy = self.cache_strategies.get(data_type, {'memory': True, 'disk': True})
        
        # Essayer d'abord le cache mémoire
        if strategy.get('memory', True):
            data = self.memory_cache.get(key)
            if data is not None:
                return data
        
        # Puis le cache disque
        if strategy.get('disk', True):
            data = self.disk_cache.get(key)
            if data is not None:
                # Remettre en cache mémoire si approprié
                if strategy.get('memory', True):
                    self.memory_cache.put(key, data, strategy.get('ttl'))
                return data
        
        return None
    
    def put(self, key: str, data: Any, data_type: str = 'default'):
        """
        Ajoute une valeur au cache.
        
        Args:
            key: Clé de cache
            data: Données à cacher
            data_type: Type de données pour la stratégie
        """
        strategy = self.cache_strategies.get(data_type, {'memory': True, 'disk': True})
        ttl = strategy.get('ttl')
        
        # Cache mémoire
        if strategy.get('memory', True):
            self.memory_cache.put(key, data, ttl)
        
        # Cache disque
        if strategy.get('disk', True):
            self.disk_cache.put(key, data, ttl)
    
    def remove(self, key: str):
        """Supprime une entrée de tous les caches."""
        self.memory_cache.remove(key)
        self.disk_cache.remove(key)
    
    def clear(self, cache_type: str = 'all'):
        """
        Vide les caches.
        
        Args:
            cache_type: 'memory', 'disk' ou 'all'
        """
        if cache_type in ['memory', 'all']:
            self.memory_cache.clear()
        
        if cache_type in ['disk', 'all']:
            self.disk_cache.clear()
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """
        Génère une clé de cache à partir d'arguments.
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés
            
        Returns:
            Clé de cache unique
        """
        # Créer une représentation hashable
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def cached_function(self, data_type: str = 'default', ttl: Optional[float] = None):
        """
        Décorateur pour mettre en cache les résultats de fonction.
        
        Args:
            data_type: Type de données pour la stratégie
            ttl: Time to live personnalisé
            
        Returns:
            Décorateur
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Générer la clé de cache
                cache_key = f"{func.__name__}_{self.get_cache_key(*args, **kwargs)}"
                
                # Essayer de récupérer du cache
                result = self.get(cache_key, data_type)
                if result is not None:
                    return result
                
                # Exécuter la fonction
                result = func(*args, **kwargs)
                
                # Mettre en cache le résultat
                if ttl:
                    # Stratégie temporaire avec TTL personnalisé
                    temp_strategy = self.cache_strategies.get(data_type, {}).copy()
                    temp_strategy['ttl'] = ttl
                    self.cache_strategies[f"{data_type}_temp"] = temp_strategy
                    self.put(cache_key, result, f"{data_type}_temp")
                else:
                    self.put(cache_key, result, data_type)
                
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de tous les caches."""
        return {
            'memory_cache': self.memory_cache.get_stats(),
            'disk_cache': self.disk_cache.get_stats(),
            'strategies': self.cache_strategies
        }
    
    def cleanup(self):
        """Nettoie tous les caches."""
        self.clear()


# Instance globale du gestionnaire de cache
global_cache_manager = None


def get_cache_manager(config: OptimizationConfig = None) -> CacheManager:
    """Retourne l'instance globale du gestionnaire de cache."""
    global global_cache_manager
    
    if global_cache_manager is None:
        global_cache_manager = CacheManager(config)
    
    return global_cache_manager