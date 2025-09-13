"""
Gestionnaire de cache simple pour test
"""

import os
import json
import hashlib
import shutil
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

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

@dataclass
class CacheStats:
    """Statistiques du cache"""
    total_models: int
    total_size_mb: float
    available_space_mb: float
    cache_hit_rate: float = 0.0
    last_cleanup: float = 0.0

class SimpleCacheManager:
    """Gestionnaire de cache simple pour les modèles"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ai_video_dubbing" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.lock = threading.RLock()
        
        # Charger l'index du cache
        self.cache_index: Dict[str, CacheEntry] = self._load_cache_index()
    
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
    
    def is_model_cached(self, model_name: str) -> bool:
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
    
    def add_model_to_cache(self, model_name: str, file_path: str) -> bool:
        """Ajoute un modèle au cache"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"Fichier modèle introuvable: {file_path}")
                return False
            
            # Calculer les métadonnées
            file_size = file_path_obj.stat().st_size
            
            # Calculer le checksum
            hash_sha256 = hashlib.sha256()
            with open(file_path_obj, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            checksum = hash_sha256.hexdigest()
            
            # Créer l'entrée de cache
            cache_entry = CacheEntry(
                model_name=model_name,
                file_path=str(file_path_obj.absolute()),
                file_size=file_size,
                checksum=checksum,
                download_date=time.time(),
                last_accessed=time.time(),
                access_count=1,
                is_validated=True
            )
            
            with self.lock:
                self.cache_index[model_name] = cache_entry
                self._save_cache_index()
            
            logger.info(f"Modèle {model_name} ajouté au cache ({file_size / 1024 / 1024:.1f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du modèle {model_name} au cache: {e}")
            return False
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """Retourne le chemin d'un modèle en cache"""
        with self.lock:
            if model_name in self.cache_index:
                return self.cache_index[model_name].file_path
            return None
    
    def get_cache_stats(self) -> CacheStats:
        """Retourne les statistiques du cache"""
        with self.lock:
            total_size = sum(entry.file_size for entry in self.cache_index.values())
            available_space = shutil.disk_usage(self.cache_dir).free
            
            return CacheStats(
                total_models=len(self.cache_index),
                total_size_mb=total_size / 1024 / 1024,
                available_space_mb=available_space / 1024 / 1024,
                cache_hit_rate=0.0,
                last_cleanup=0.0
            )
    
    def remove_model(self, model_name: str) -> bool:
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
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du modèle {model_name}: {e}")
            return False
    
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