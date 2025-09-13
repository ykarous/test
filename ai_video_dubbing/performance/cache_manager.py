"""
Gestionnaire de cache intelligent pour les modèles avec validation d'intégrité
"""

import os
import json
import hashlib
import shutil
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import threading
import aiofiles

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrée de cache pour un modèle"""
    model_name: str
    file_path: str
    file_size: int
    checksum: str
    download_date: float
    last_accessed: float
    access_count: int
    is_validated: bool = False
    validation_date: Optional[float] = None

@dataclass
class CacheStats:
    """Statistiques du cache"""
    total_models: int
    total_size_mb: float
    available_space_mb: float
    cache_hit_rate: float
    last_cleanup: float

class ModelCacheManager:
    """Gestionnaire de cache intelligent pour les modèles NeMo"""
    
    def __init__(self, cache_dir: str = None, max_cache_size_gb: float = 5.0):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ai_video_dubbing" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.lock = threading.RLock()
        
        # Charger l'index du cache
        self.cache_index: Dict[str, CacheEntry] = self._load_cache_index()
        
        # Statistiques
        self.stats = CacheStats(0, 0.0, 0.0, 0.0, 0.0)
        self._update_stats()
    
    def _load_cache_index(self) -> Dict[str, CacheEntry]:
        """Charge l'index du cache depuis le disque"""
        if not self.cache_index_file.exists():
            return {}
        
        try:
            with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    name: CacheEntry(**entry_data) 
                    for name, entry_data in data.items()
                }
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de l'index du cache: {e}")
            return {}
    
    def _save_cache_index(self):
        """Sauvegarde l'index du cache sur le disque"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                data = {
                    name: asdict(entry) 
                    for name, entry in self.cache_index.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'index du cache: {e}")
    
    async def is_model_cached(self, model_name: str) -> bool:
        """Vérifie si un modèle est en cache"""
        with self.lock:
            if model_name not in self.cache_index:
                return False
            
            entry = self.cache_index[model_name]
            file_path = Path(entry.file_path)
            
            # Vérifier que le fichier existe
            if not file_path.exists():
                logger.warning(f"Modèle {model_name} dans l'index mais fichier manquant")
                del self.cache_index[model_name]
                self._save_cache_index()
                return False
            
            return True
    
    async def validate_model(self, model_name: str) -> bool:
        """Valide l'intégrité d'un modèle en cache"""
        if not await self.is_model_cached(model_name):
            return False
        
        with self.lock:
            entry = self.cache_index[model_name]
            file_path = Path(entry.file_path)
            
            try:
                # Vérifier la taille du fichier
                actual_size = file_path.stat().st_size
                if actual_size != entry.file_size:
                    logger.warning(f"Taille incorrecte pour {model_name}: {actual_size} vs {entry.file_size}")
                    return False
                
                # Vérifier le checksum si pas déjà validé récemment
                if not entry.is_validated or (time.time() - (entry.validation_date or 0)) > 86400:  # 24h
                    logger.info(f"Validation du checksum pour {model_name}...")
                    actual_checksum = await self._calculate_file_checksum(file_path)
                    
                    if actual_checksum != entry.checksum:
                        logger.error(f"Checksum incorrect pour {model_name}")
                        return False
                    
                    # Marquer comme validé
                    entry.is_validated = True
                    entry.validation_date = time.time()
                    self._save_cache_index()
                
                # Mettre à jour les statistiques d'accès
                entry.last_accessed = time.time()
                entry.access_count += 1
                self._save_cache_index()
                
                return True
                
            except Exception as e:
                logger.error(f"Erreur lors de la validation de {model_name}: {e}")
                return False
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calcule le checksum SHA256 d'un fichier de manière asynchrone"""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def add_model_to_cache(self, model_name: str, file_path: str, 
                               expected_checksum: Optional[str] = None) -> bool:
        """Ajoute un modèle au cache avec validation"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"Fichier modèle introuvable: {file_path}")
                return False
            
            # Calculer les métadonnées
            file_size = file_path_obj.stat().st_size
            checksum = await self._calculate_file_checksum(file_path_obj)
            
            # Vérifier le checksum si fourni
            if expected_checksum and checksum != expected_checksum:
                logger.error(f"Checksum incorrect pour {model_name}")
                return False
            
            # Créer l'entrée de cache
            cache_entry = CacheEntry(
                model_name=model_name,
                file_path=str(file_path_obj.absolute()),
                file_size=file_size,
                checksum=checksum,
                download_date=time.time(),
                last_accessed=time.time(),
                access_count=1,
                is_validated=True,
                validation_date=time.time()
            )
            
            with self.lock:
                self.cache_index[model_name] = cache_entry
                self._save_cache_index()
                self._update_stats()
            
            logger.info(f"Modèle {model_name} ajouté au cache ({file_size / 1024 / 1024:.1f} MB)")
            
            # Vérifier si nettoyage nécessaire
            await self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du modèle {model_name} au cache: {e}")
            return False
    
    async def remove_model(self, model_name: str) -> bool:
        """Supprime un modèle du cache"""
        try:
            with self.lock:
                if model_name not in self.cache_index:
                    return False
                
                entry = self.cache_index[model_name]
                file_path = Path(entry.file_path)
                
                # Supprimer le fichier
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Fichier supprimé: {file_path}")
                
                # Supprimer de l'index
                del self.cache_index[model_name]
                self._save_cache_index()
                self._update_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du modèle {model_name}: {e}")
            return False
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """Retourne le chemin d'un modèle en cache"""
        with self.lock:
            if model_name in self.cache_index:
                return self.cache_index[model_name].file_path
            return None
    
    def get_cache_stats(self) -> CacheStats:
        """Retourne les statistiques du cache"""
        self._update_stats()
        return self.stats
    
    def _update_stats(self):
        """Met à jour les statistiques du cache"""
        with self.lock:
            total_size = sum(entry.file_size for entry in self.cache_index.values())
            available_space = shutil.disk_usage(self.cache_dir).free
            
            self.stats = CacheStats(
                total_models=len(self.cache_index),
                total_size_mb=total_size / 1024 / 1024,
                available_space_mb=available_space / 1024 / 1024,
                cache_hit_rate=0.0,  # À implémenter avec des métriques d'usage
                last_cleanup=getattr(self, '_last_cleanup', 0.0)
            )
    
    async def _cleanup_if_needed(self):
        """Nettoie le cache si nécessaire"""
        current_size = sum(entry.file_size for entry in self.cache_index.values())
        
        if current_size > self.max_cache_size:
            logger.info("Nettoyage du cache nécessaire...")
            await self._cleanup_cache()
    
    async def _cleanup_cache(self):
        """Nettoie le cache en supprimant les modèles les moins utilisés"""
        with self.lock:
            # Trier par score d'utilisation (accès récent + fréquence)
            models_by_usage = []
            current_time = time.time()
            
            for name, entry in self.cache_index.items():
                # Score basé sur la fréquence et la récence d'accès
                recency_score = 1.0 / (1.0 + (current_time - entry.last_accessed) / 86400)  # Décroissance sur 24h
                frequency_score = min(entry.access_count / 10.0, 1.0)  # Normalisé sur 10 accès
                usage_score = (recency_score + frequency_score) / 2.0
                
                models_by_usage.append((usage_score, name, entry))
            
            # Trier par score croissant (les moins utilisés en premier)
            models_by_usage.sort(key=lambda x: x[0])
            
            # Supprimer les modèles jusqu'à atteindre 80% de la limite
            target_size = self.max_cache_size * 0.8
            current_size = sum(entry.file_size for entry in self.cache_index.values())
            
            for usage_score, model_name, entry in models_by_usage:
                if current_size <= target_size:
                    break
                
                logger.info(f"Suppression du modèle peu utilisé: {model_name} (score: {usage_score:.2f})")
                await self.remove_model(model_name)
                current_size -= entry.file_size
            
            self._last_cleanup = time.time()
            logger.info(f"Nettoyage terminé. Taille du cache: {current_size / 1024 / 1024:.1f} MB")
    
    def list_cached_models(self) -> List[Dict[str, Any]]:
        """Liste tous les modèles en cache avec leurs métadonnées"""
        with self.lock:
            models = []
            for name, entry in self.cache_index.items():
                models.append({
                    'name': name,
                    'size_mb': entry.file_size / 1024 / 1024,
                    'download_date': entry.download_date,
                    'last_accessed': entry.last_accessed,
                    'access_count': entry.access_count,
                    'is_validated': entry.is_validated,
                    'file_path': entry.file_path
                })
            
            # Trier par date d'accès décroissante
            models.sort(key=lambda x: x['last_accessed'], reverse=True)
            return models