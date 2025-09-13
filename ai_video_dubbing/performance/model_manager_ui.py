"""
Interface de gestion des modèles avec visualisation et actions
"""
import asyncio
import time
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Statuts possibles des modèles"""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    CORRUPTED = "corrupted"
    MISSING = "missing"
    VALIDATING = "validating"
    UPDATING = "updating"

class ModelType(Enum):
    """Types de modèles supportés"""
    NEMO_ASR = "nemo_asr"
    WHISPER = "whisper"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

@dataclass
class ModelInfo:
    """Informations sur un modèle"""
    model_id: str
    name: str
    model_type: ModelType
    status: ModelStatus
    file_path: Optional[str] = None
    file_size: int = 0
    download_date: Optional[float] = None
    last_used: Optional[float] = None
    usage_count: int = 0
    version: str = "1.0"
    description: str = ""
    language: str = "multi"
    quality_score: float = 0.0
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "model_type": self.model_type.value,
            "status": self.status.value,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "download_date": self.download_date,
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "version": self.version,
            "description": self.description,
            "language": self.language,
            "quality_score": self.quality_score,
            "download_url": self.download_url,
            "checksum": self.checksum,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Crée depuis un dictionnaire"""
        return cls(
            model_id=data["model_id"],
            name=data["name"],
            model_type=ModelType(data["model_type"]),
            status=ModelStatus(data["status"]),
            file_path=data.get("file_path"),
            file_size=data.get("file_size", 0),
            download_date=data.get("download_date"),
            last_used=data.get("last_used"),
            usage_count=data.get("usage_count", 0),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            language=data.get("language", "multi"),
            quality_score=data.get("quality_score", 0.0),
            download_url=data.get("download_url"),
            checksum=data.get("checksum"),
            metadata=data.get("metadata", {})
        )

@dataclass
class DiskUsageInfo:
    """Informations d'utilisation disque"""
    total_space: int
    used_space: int
    free_space: int
    models_space: int
    cache_space: int
    
    @property
    def usage_percent(self) -> float:
        """Pourcentage d'utilisation"""
        return (self.used_space / self.total_space) * 100 if self.total_space > 0 else 0.0
    
    @property
    def models_percent(self) -> float:
        """Pourcentage utilisé par les modèles"""
        return (self.models_space / self.total_space) * 100 if self.total_space > 0 else 0.0

class ModelManagerUI:
    """Interface de gestion des modèles"""
    
    def __init__(self, models_dir: str = "models", cache_dir: str = ".kiro/models_cache"):
        self.models_dir = Path(models_dir)
        self.cache_dir = Path(cache_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Stockage des modèles
        self.models: Dict[str, ModelInfo] = {}
        
        # Callbacks pour les événements
        self.event_callbacks: Dict[str, List[Callable]] = {
            "model_added": [],
            "model_removed": [],
            "model_updated": [],
            "download_progress": [],
            "validation_complete": [],
            "error_occurred": []
        }
        
        # Configuration
        self.config = {
            "auto_validate": True,
            "auto_cleanup": True,
            "max_cache_size": 10 * 1024**3,  # 10GB
            "validation_interval": 24 * 3600,  # 24 heures
            "supported_extensions": [".pt", ".pth", ".onnx", ".bin", ".safetensors"]
        }
        
        # Modèles prédéfinis disponibles
        self.available_models = {
            "whisper-tiny": {
                "name": "Whisper Tiny",
                "type": ModelType.WHISPER,
                "size": 39 * 1024**2,  # 39MB
                "description": "Modèle Whisper ultra-léger et rapide",
                "language": "multi",
                "quality_score": 7.0,
                "url": "https://huggingface.co/openai/whisper-tiny"
            },
            "whisper-base": {
                "name": "Whisper Base", 
                "type": ModelType.WHISPER,
                "size": 142 * 1024**2,  # 142MB
                "description": "Modèle Whisper équilibré",
                "language": "multi",
                "quality_score": 8.0,
                "url": "https://huggingface.co/openai/whisper-base"
            },
            "whisper-small": {
                "name": "Whisper Small",
                "type": ModelType.WHISPER,
                "size": 488 * 1024**2,  # 488MB
                "description": "Modèle Whisper de bonne qualité",
                "language": "multi", 
                "quality_score": 8.5,
                "url": "https://huggingface.co/openai/whisper-small"
            },
            "nemo-asr-conformer-ctc-large": {
                "name": "NeMo ASR Conformer Large",
                "type": ModelType.NEMO_ASR,
                "size": 1200 * 1024**2,  # 1.2GB
                "description": "Modèle NeMo haute qualité",
                "language": "en",
                "quality_score": 9.2,
                "url": "https://huggingface.co/nvidia/stt_en_conformer_ctc_large"
            },
            "nemo-asr-conformer-ctc-medium": {
                "name": "NeMo ASR Conformer Medium",
                "type": ModelType.NEMO_ASR,
                "size": 600 * 1024**2,  # 600MB
                "description": "Modèle NeMo équilibré",
                "language": "en",
                "quality_score": 8.8,
                "url": "https://huggingface.co/nvidia/stt_en_conformer_ctc_medium"
            }
        }
        
        # Charger les modèles existants
        self._load_models_from_disk()
    
    async def scan_models(self) -> List[ModelInfo]:
        """Scanne le répertoire des modèles pour détecter les nouveaux modèles"""
        
        logger.info("Scanning models directory...")
        discovered_models = []
        
        # Scanner le répertoire des modèles
        for file_path in self.models_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in self.config["supported_extensions"]:
                model_id = self._generate_model_id(file_path)
                
                if model_id not in self.models:
                    # Nouveau modèle découvert
                    model_info = await self._analyze_model_file(file_path)
                    if model_info:
                        self.models[model_id] = model_info
                        discovered_models.append(model_info)
                        
                        await self._emit_event("model_added", {
                            "model_id": model_id,
                            "model_info": model_info.to_dict()
                        })
        
        # Vérifier les modèles existants
        models_to_remove = []
        for model_id, model_info in self.models.items():
            if model_info.file_path and not Path(model_info.file_path).exists():
                models_to_remove.append(model_id)
        
        # Supprimer les modèles manquants
        for model_id in models_to_remove:
            model_info = self.models[model_id]
            model_info.status = ModelStatus.MISSING
            await self._emit_event("model_updated", {
                "model_id": model_id,
                "status": "missing"
            })
        
        logger.info(f"Discovered {len(discovered_models)} new models")
        return discovered_models
    
    async def _analyze_model_file(self, file_path: Path) -> Optional[ModelInfo]:
        """Analyse un fichier de modèle pour extraire les informations"""
        
        try:
            # Informations de base du fichier
            stat = file_path.stat()
            file_size = stat.st_size
            
            # Générer un ID unique
            model_id = self._generate_model_id(file_path)
            
            # Déterminer le type de modèle basé sur le nom/chemin
            model_type = self._detect_model_type(file_path)
            
            # Nom du modèle basé sur le nom de fichier
            model_name = file_path.stem
            
            # Calculer le checksum
            checksum = await self._calculate_checksum(file_path)
            
            model_info = ModelInfo(
                model_id=model_id,
                name=model_name,
                model_type=model_type,
                status=ModelStatus.AVAILABLE,
                file_path=str(file_path),
                file_size=file_size,
                download_date=stat.st_ctime,
                checksum=checksum,
                description=f"Modèle {model_type.value} découvert automatiquement"
            )
            
            return model_info
            
        except Exception as e:
            logger.warning(f"Failed to analyze model file {file_path}: {e}")
            return None
    
    def _generate_model_id(self, file_path: Path) -> str:
        """Génère un ID unique pour un modèle"""
        # Utiliser le chemin relatif et la taille pour générer un ID stable
        relative_path = file_path.relative_to(self.models_dir)
        id_string = f"{relative_path}_{file_path.stat().st_size}"
        return hashlib.md5(id_string.encode()).hexdigest()[:16]
    
    def _detect_model_type(self, file_path: Path) -> ModelType:
        """Détecte le type de modèle basé sur le nom/chemin"""
        
        path_str = str(file_path).lower()
        
        if "whisper" in path_str:
            return ModelType.WHISPER
        elif "nemo" in path_str or "conformer" in path_str:
            return ModelType.NEMO_ASR
        else:
            return ModelType.UNKNOWN
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calcule le checksum MD5 d'un fichier"""
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Lire par chunks pour les gros fichiers
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def get_models_list(self, filter_type: Optional[ModelType] = None, 
                       filter_status: Optional[ModelStatus] = None) -> List[ModelInfo]:
        """Obtient la liste des modèles avec filtres optionnels"""
        
        models = list(self.models.values())
        
        if filter_type:
            models = [m for m in models if m.model_type == filter_type]
        
        if filter_status:
            models = [m for m in models if m.status == filter_status]
        
        # Trier par date d'utilisation récente, puis par nom
        models.sort(key=lambda m: (m.last_used or 0, m.name), reverse=True)
        
        return models
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Obtient les informations d'un modèle spécifique"""
        return self.models.get(model_id)
    
    async def validate_model(self, model_id: str) -> bool:
        """Valide l'intégrité d'un modèle"""
        
        model_info = self.models.get(model_id)
        if not model_info:
            return False
        
        if not model_info.file_path or not Path(model_info.file_path).exists():
            model_info.status = ModelStatus.MISSING
            await self._emit_event("model_updated", {
                "model_id": model_id,
                "status": "missing"
            })
            return False
        
        # Marquer comme en cours de validation
        model_info.status = ModelStatus.VALIDATING
        await self._emit_event("model_updated", {
            "model_id": model_id,
            "status": "validating"
        })
        
        try:
            # Vérifier le checksum si disponible
            if model_info.checksum:
                current_checksum = await self._calculate_checksum(Path(model_info.file_path))
                if current_checksum != model_info.checksum:
                    model_info.status = ModelStatus.CORRUPTED
                    await self._emit_event("model_updated", {
                        "model_id": model_id,
                        "status": "corrupted"
                    })
                    return False
            
            # Validation basique du fichier
            file_path = Path(model_info.file_path)
            if file_path.stat().st_size != model_info.file_size:
                model_info.status = ModelStatus.CORRUPTED
                await self._emit_event("model_updated", {
                    "model_id": model_id,
                    "status": "corrupted"
                })
                return False
            
            # Modèle valide
            model_info.status = ModelStatus.AVAILABLE
            await self._emit_event("validation_complete", {
                "model_id": model_id,
                "valid": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Model validation failed for {model_id}: {e}")
            model_info.status = ModelStatus.CORRUPTED
            await self._emit_event("error_occurred", {
                "model_id": model_id,
                "error": str(e)
            })
            return False
    
    async def delete_model(self, model_id: str, delete_file: bool = True) -> bool:
        """Supprime un modèle"""
        
        model_info = self.models.get(model_id)
        if not model_info:
            return False
        
        try:
            # Supprimer le fichier si demandé
            if delete_file and model_info.file_path:
                file_path = Path(model_info.file_path)
                if file_path.exists():
                    file_path.unlink()
            
            # Supprimer de la liste
            del self.models[model_id]
            
            await self._emit_event("model_removed", {
                "model_id": model_id,
                "model_name": model_info.name
            })
            
            logger.info(f"Deleted model {model_info.name} ({model_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            await self._emit_event("error_occurred", {
                "model_id": model_id,
                "error": str(e)
            })
            return False
    
    async def download_model(self, model_key: str, progress_callback: Optional[Callable] = None) -> bool:
        """Télécharge un modèle depuis la liste des modèles disponibles"""
        
        if model_key not in self.available_models:
            logger.error(f"Model {model_key} not found in available models")
            return False
        
        model_spec = self.available_models[model_key]
        
        # Créer l'info du modèle
        model_id = f"downloaded_{model_key}"
        model_info = ModelInfo(
            model_id=model_id,
            name=model_spec["name"],
            model_type=model_spec["type"],
            status=ModelStatus.DOWNLOADING,
            file_size=model_spec["size"],
            description=model_spec["description"],
            language=model_spec["language"],
            quality_score=model_spec["quality_score"],
            download_url=model_spec["url"],
            download_date=time.time()
        )
        
        self.models[model_id] = model_info
        
        await self._emit_event("model_added", {
            "model_id": model_id,
            "model_info": model_info.to_dict()
        })
        
        try:
            # Simuler le téléchargement (dans une vraie implémentation, utiliser le download_manager)
            download_path = self.models_dir / f"{model_key}.pt"
            
            # Simulation du téléchargement avec progression
            total_size = model_spec["size"]
            downloaded = 0
            chunk_size = total_size // 20  # 20 étapes
            
            # Créer un fichier factice pour la simulation
            with open(download_path, 'wb') as f:
                while downloaded < total_size:
                    chunk = min(chunk_size, total_size - downloaded)
                    f.write(b'0' * chunk)
                    downloaded += chunk
                    
                    # Callback de progression
                    progress = (downloaded / total_size) * 100
                    if progress_callback:
                        await progress_callback(model_id, progress, downloaded, total_size)
                    
                    await self._emit_event("download_progress", {
                        "model_id": model_id,
                        "progress": progress,
                        "downloaded": downloaded,
                        "total": total_size
                    })
                    
                    # Petite pause pour simuler le téléchargement
                    await asyncio.sleep(0.1)
            
            # Finaliser le modèle
            model_info.file_path = str(download_path)
            model_info.status = ModelStatus.AVAILABLE
            model_info.checksum = await self._calculate_checksum(download_path)
            
            await self._emit_event("model_updated", {
                "model_id": model_id,
                "status": "available"
            })
            
            logger.info(f"Successfully downloaded model {model_spec['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download model {model_key}: {e}")
            model_info.status = ModelStatus.CORRUPTED
            await self._emit_event("error_occurred", {
                "model_id": model_id,
                "error": str(e)
            })
            return False
    
    def get_disk_usage(self) -> DiskUsageInfo:
        """Obtient les informations d'utilisation disque"""
        
        try:
            import shutil
            
            # Espace disque total
            total, used, free = shutil.disk_usage(self.models_dir)
            
            # Calculer l'espace utilisé par les modèles
            models_space = 0
            for model_info in self.models.values():
                if model_info.file_path and Path(model_info.file_path).exists():
                    models_space += model_info.file_size
            
            # Calculer l'espace utilisé par le cache
            cache_space = 0
            if self.cache_dir.exists():
                for file_path in self.cache_dir.rglob("*"):
                    if file_path.is_file():
                        cache_space += file_path.stat().st_size
            
            return DiskUsageInfo(
                total_space=total,
                used_space=used,
                free_space=free,
                models_space=models_space,
                cache_space=cache_space
            )
            
        except Exception as e:
            logger.warning(f"Failed to get disk usage: {e}")
            return DiskUsageInfo(0, 0, 0, 0, 0)
    
    def get_models_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des modèles"""
        
        stats = {
            "total_models": len(self.models),
            "by_type": {},
            "by_status": {},
            "total_size": 0,
            "most_used": None,
            "recently_added": [],
            "available_for_download": len(self.available_models)
        }
        
        # Statistiques par type
        for model_type in ModelType:
            stats["by_type"][model_type.value] = len([
                m for m in self.models.values() if m.model_type == model_type
            ])
        
        # Statistiques par statut
        for status in ModelStatus:
            stats["by_status"][status.value] = len([
                m for m in self.models.values() if m.status == status
            ])
        
        # Taille totale et modèle le plus utilisé
        most_used_count = 0
        for model_info in self.models.values():
            stats["total_size"] += model_info.file_size
            
            if model_info.usage_count > most_used_count:
                most_used_count = model_info.usage_count
                stats["most_used"] = {
                    "model_id": model_info.model_id,
                    "name": model_info.name,
                    "usage_count": model_info.usage_count
                }
        
        # Modèles récemment ajoutés (dernières 24h)
        recent_threshold = time.time() - 24 * 3600
        stats["recently_added"] = [
            {
                "model_id": m.model_id,
                "name": m.name,
                "download_date": m.download_date
            }
            for m in self.models.values()
            if m.download_date and m.download_date > recent_threshold
        ]
        
        return stats
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Obtient la liste des modèles disponibles au téléchargement"""
        
        available = {}
        
        for model_key, model_spec in self.available_models.items():
            # Vérifier si déjà téléchargé
            already_downloaded = any(
                model_key in model_info.model_id or model_key in model_info.name.lower()
                for model_info in self.models.values()
                if model_info.status == ModelStatus.AVAILABLE
            )
            
            available[model_key] = {
                **model_spec,
                "already_downloaded": already_downloaded,
                "size_mb": model_spec["size"] / (1024**2),
                "size_formatted": self._format_file_size(model_spec["size"])
            }
        
        return available
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formate une taille de fichier"""
        
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.1f} MB"
        else:
            return f"{size_bytes / (1024**3):.1f} GB"
    
    async def record_model_usage(self, model_id: str):
        """Enregistre l'utilisation d'un modèle"""
        
        model_info = self.models.get(model_id)
        if model_info:
            model_info.usage_count += 1
            model_info.last_used = time.time()
            
            await self._emit_event("model_updated", {
                "model_id": model_id,
                "usage_count": model_info.usage_count,
                "last_used": model_info.last_used
            })
    
    def get_model_recommendations(self, system_info: Dict[str, Any]) -> List[str]:
        """Obtient des recommandations de modèles basées sur les ressources système"""
        
        recommendations = []
        
        # Analyser les ressources disponibles
        memory_gb = system_info.get("available_memory", 0) / (1024**3)
        has_gpu = system_info.get("cuda_available", False)
        disk_free_gb = system_info.get("free_disk", 0) / (1024**3)
        
        # Recommandations basées sur la mémoire
        if memory_gb < 4:
            recommendations.extend(["whisper-tiny"])
        elif memory_gb < 8:
            recommendations.extend(["whisper-tiny", "whisper-base"])
        else:
            recommendations.extend(["whisper-base", "whisper-small"])
        
        # Recommandations basées sur le GPU
        if has_gpu and memory_gb > 8:
            recommendations.extend(["nemo-asr-conformer-ctc-medium"])
            if memory_gb > 16:
                recommendations.extend(["nemo-asr-conformer-ctc-large"])
        
        # Filtrer selon l'espace disque disponible
        filtered_recommendations = []
        for model_key in recommendations:
            if model_key in self.available_models:
                model_size_gb = self.available_models[model_key]["size"] / (1024**3)
                if model_size_gb < disk_free_gb * 0.8:  # Garder 20% d'espace libre
                    filtered_recommendations.append(model_key)
        
        return list(set(filtered_recommendations))  # Supprimer les doublons
    
    async def cleanup_unused_models(self, days_threshold: int = 30) -> List[str]:
        """Nettoie les modèles non utilisés depuis X jours"""
        
        threshold_time = time.time() - (days_threshold * 24 * 3600)
        models_to_cleanup = []
        
        for model_id, model_info in self.models.items():
            # Modèles jamais utilisés ou non utilisés depuis longtemps
            if (not model_info.last_used or model_info.last_used < threshold_time) and model_info.usage_count == 0:
                models_to_cleanup.append(model_id)
        
        # Supprimer les modèles identifiés
        cleaned_models = []
        for model_id in models_to_cleanup:
            model_name = self.models[model_id].name
            if await self.delete_model(model_id, delete_file=True):
                cleaned_models.append(model_name)
        
        if cleaned_models:
            logger.info(f"Cleaned up {len(cleaned_models)} unused models")
        
        return cleaned_models
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Ajoute un callback d'événement"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Supprime un callback d'événement"""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Émet un événement vers les callbacks"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.warning(f"Event callback error for {event_type}: {e}")
    
    def _load_models_from_disk(self):
        """Charge les modèles depuis le fichier de configuration"""
        
        config_file = self.cache_dir / "models_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    models_data = json.load(f)
                
                for model_data in models_data:
                    model_info = ModelInfo.from_dict(model_data)
                    self.models[model_info.model_id] = model_info
                
                logger.info(f"Loaded {len(self.models)} models from configuration")
                
            except Exception as e:
                logger.warning(f"Failed to load models configuration: {e}")
    
    async def save_models_config(self):
        """Sauvegarde la configuration des modèles"""
        
        config_file = self.cache_dir / "models_config.json"
        
        try:
            models_data = [model_info.to_dict() for model_info in self.models.values()]
            
            with open(config_file, 'w') as f:
                json.dump(models_data, f, indent=2)
            
            logger.debug("Saved models configuration")
            
        except Exception as e:
            logger.warning(f"Failed to save models configuration: {e}")
    
    def get_model_visualization_data(self) -> Dict[str, Any]:
        """Obtient les données pour la visualisation des modèles"""
        
        disk_usage = self.get_disk_usage()
        stats = self.get_models_statistics()
        
        # Données pour les graphiques
        visualization_data = {
            "disk_usage": {
                "total_gb": disk_usage.total_space / (1024**3),
                "used_gb": disk_usage.used_space / (1024**3),
                "free_gb": disk_usage.free_space / (1024**3),
                "models_gb": disk_usage.models_space / (1024**3),
                "cache_gb": disk_usage.cache_space / (1024**3),
                "usage_percent": disk_usage.usage_percent,
                "models_percent": disk_usage.models_percent
            },
            "models_by_type": [
                {"type": model_type, "count": count}
                for model_type, count in stats["by_type"].items()
                if count > 0
            ],
            "models_by_status": [
                {"status": status, "count": count}
                for status, count in stats["by_status"].items()
                if count > 0
            ],
            "models_timeline": [
                {
                    "name": model_info.name,
                    "download_date": model_info.download_date,
                    "size_mb": model_info.file_size / (1024**2),
                    "usage_count": model_info.usage_count
                }
                for model_info in self.models.values()
                if model_info.download_date
            ],
            "top_models": sorted([
                {
                    "name": model_info.name,
                    "usage_count": model_info.usage_count,
                    "size_mb": model_info.file_size / (1024**2),
                    "quality_score": model_info.quality_score
                }
                for model_info in self.models.values()
            ], key=lambda x: x["usage_count"], reverse=True)[:5]
        }
        
        return visualization_data

# Instance globale pour faciliter l'utilisation
model_manager_ui = ModelManagerUI()