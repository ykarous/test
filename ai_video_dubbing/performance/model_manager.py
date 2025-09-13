"""
Gestionnaire de modèles légers avec recommandations intelligentes
"""

import logging
import time
import psutil
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Informations détaillées sur un modèle"""
    name: str
    category: str  # "ultra_light", "light", "medium", "heavy"
    size_mb: int
    download_time_estimate: int  # secondes
    quality: str  # "basic", "good", "very_good", "excellent"
    languages: List[str]
    device_compatibility: List[str]  # ["cpu", "gpu", "auto"]
    memory_requirement_mb: int
    description: str
    model_type: str  # "asr", "diarization", "ocr"
    source: str = "huggingface"  # "huggingface", "nvidia", "local"
    
@dataclass
class ModelRecommendation:
    """Recommandation de modèle avec justification"""
    model_name: str
    category: str
    estimated_download_time: int
    quality_level: str
    reason: str
    confidence: float  # 0.0 à 1.0
    alternatives: List[str]

@dataclass
class SystemResources:
    """Informations sur les ressources système"""
    available_memory_mb: float
    total_memory_mb: float
    memory_usage_percent: float
    cpu_count: int
    gpu_available: bool
    gpu_memory_mb: float
    disk_space_gb: float
    connection_speed_mbps: float

class LightweightModelManager:
    """Gestionnaire de modèles avec priorité aux modèles légers"""
    
    def __init__(self, cache_manager=None):
        self.model_catalog = self._initialize_model_catalog()
        self.system_resources = None
        self.connection_speed_cache = None
        self.connection_speed_timestamp = 0
        
        # Intégration du cache manager
        if cache_manager is None:
            try:
                from .cache_manager import ModelCacheManager
                self.cache_manager = ModelCacheManager()
            except ImportError:
                # Fallback vers le cache simple
                from .simple_cache import SimpleCacheManager
                self.cache_manager = SimpleCacheManager()
        else:
            self.cache_manager = cache_manager
        
    def _initialize_model_catalog(self) -> Dict[str, ModelInfo]:
        """Initialise le catalogue de modèles avec métadonnées complètes"""
        catalog = {}
        
        # Modèles ASR ultra-légers
        catalog["stt_en_conformer_ctc_small"] = ModelInfo(
            name="stt_en_conformer_ctc_small",
            category="ultra_light",
            size_mb=49,
            download_time_estimate=30,
            quality="good",
            languages=["en"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=200,
            description="Modèle NeMo Conformer CTC compact pour l'anglais",
            model_type="asr",
            source="nvidia"
        )
        
        catalog["whisper-tiny"] = ModelInfo(
            name="whisper-tiny",
            category="ultra_light",
            size_mb=39,
            download_time_estimate=25,
            quality="basic",
            languages=["multilingual"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=150,
            description="Modèle Whisper le plus compact, multilingue",
            model_type="asr",
            source="openai"
        )
        
        # Modèles ASR légers
        catalog["whisper-base"] = ModelInfo(
            name="whisper-base",
            category="light",
            size_mb=74,
            download_time_estimate=45,
            quality="good",
            languages=["multilingual"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=300,
            description="Modèle Whisper équilibré qualité/performance",
            model_type="asr",
            source="openai"
        )
        
        catalog["stt_fr_conformer_ctc_large"] = ModelInfo(
            name="stt_fr_conformer_ctc_large",
            category="light",
            size_mb=120,
            download_time_estimate=75,
            quality="very_good",
            languages=["fr"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=400,
            description="Modèle NeMo optimisé pour le français",
            model_type="asr",
            source="nvidia"
        )
        
        # Modèles ASR moyens
        catalog["whisper-small"] = ModelInfo(
            name="whisper-small",
            category="medium",
            size_mb=244,
            download_time_estimate=120,
            quality="very_good",
            languages=["multilingual"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=800,
            description="Modèle Whisper avec bonne précision",
            model_type="asr",
            source="openai"
        )
        
        catalog["stt_multilingual_fastconformer_hybrid_large_pc"] = ModelInfo(
            name="stt_multilingual_fastconformer_hybrid_large_pc",
            category="medium",
            size_mb=300,
            download_time_estimate=180,
            quality="very_good",
            languages=["multilingual"],
            device_compatibility=["gpu", "auto"],
            memory_requirement_mb=1000,
            description="Modèle NeMo FastConformer multilingue",
            model_type="asr",
            source="nvidia"
        )
        
        # Modèles ASR lourds
        catalog["whisper-medium"] = ModelInfo(
            name="whisper-medium",
            category="heavy",
            size_mb=769,
            download_time_estimate=300,
            quality="excellent",
            languages=["multilingual"],
            device_compatibility=["gpu", "auto"],
            memory_requirement_mb=2000,
            description="Modèle Whisper haute précision",
            model_type="asr",
            source="openai"
        )
        
        catalog["whisper-large-v3"] = ModelInfo(
            name="whisper-large-v3",
            category="heavy",
            size_mb=1550,
            download_time_estimate=600,
            quality="excellent",
            languages=["multilingual"],
            device_compatibility=["gpu", "auto"],
            memory_requirement_mb=4000,
            description="Modèle Whisper le plus précis",
            model_type="asr",
            source="openai"
        )
        
        catalog["nemo-fastconformer-multilingual"] = ModelInfo(
            name="nemo-fastconformer-multilingual",
            category="heavy",
            size_mb=1200,
            download_time_estimate=480,
            quality="excellent",
            languages=["multilingual"],
            device_compatibility=["gpu", "auto"],
            memory_requirement_mb=3500,
            description="Modèle NeMo FastConformer haute performance",
            model_type="asr",
            source="nvidia"
        )
        
        # Modèles de diarisation
        catalog["titanet_large"] = ModelInfo(
            name="titanet_large",
            category="medium",
            size_mb=200,
            download_time_estimate=90,
            quality="very_good",
            languages=["multilingual"],
            device_compatibility=["cpu", "gpu", "auto"],
            memory_requirement_mb=600,
            description="Modèle NeMo TitaNet pour diarisation",
            model_type="diarization",
            source="nvidia"
        )
        
        return catalog
    
    def get_system_resources(self) -> SystemResources:
        """Obtient les informations sur les ressources système"""
        if self.system_resources is None:
            self.system_resources = self._detect_system_resources()
        return self.system_resources
    
    def _detect_system_resources(self) -> SystemResources:
        """Détecte les ressources système disponibles"""
        try:
            # Mémoire système
            memory = psutil.virtual_memory()
            available_memory_mb = memory.available / (1024 * 1024)
            total_memory_mb = memory.total / (1024 * 1024)
            memory_usage_percent = memory.percent
            
            # CPU
            cpu_count = psutil.cpu_count()
            
            # GPU (tentative de détection)
            gpu_available = False
            gpu_memory_mb = 0
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_memory_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            except ImportError:
                pass
            
            # Espace disque
            disk_usage = psutil.disk_usage('.')
            disk_space_gb = disk_usage.free / (1024 * 1024 * 1024)
            
            # Vitesse de connexion (estimation)
            connection_speed_mbps = self._estimate_connection_speed()
            
            return SystemResources(
                available_memory_mb=available_memory_mb,
                total_memory_mb=total_memory_mb,
                memory_usage_percent=memory_usage_percent,
                cpu_count=cpu_count,
                gpu_available=gpu_available,
                gpu_memory_mb=gpu_memory_mb,
                disk_space_gb=disk_space_gb,
                connection_speed_mbps=connection_speed_mbps
            )
            
        except Exception as e:
            logger.warning(f"Could not detect system resources: {e}")
            # Valeurs par défaut conservatrices
            return SystemResources(
                available_memory_mb=2000,
                total_memory_mb=8000,
                memory_usage_percent=50.0,
                cpu_count=4,
                gpu_available=False,
                gpu_memory_mb=0,
                disk_space_gb=10.0,
                connection_speed_mbps=10.0
            )
    
    def _estimate_connection_speed(self) -> float:
        """Estime la vitesse de connexion internet"""
        # Cache de 5 minutes
        current_time = time.time()
        if (self.connection_speed_cache is not None and 
            current_time - self.connection_speed_timestamp < 300):
            return self.connection_speed_cache
        
        try:
            # Test simple avec un petit fichier
            start_time = time.time()
            response = requests.get(
                "https://httpbin.org/bytes/1024",  # 1KB
                timeout=5
            )
            download_time = time.time() - start_time
            
            if download_time > 0:
                # Calculer la vitesse en Mbps
                bytes_downloaded = len(response.content)
                speed_mbps = (bytes_downloaded * 8) / (download_time * 1024 * 1024)
                
                # Extrapoler pour une estimation plus réaliste
                estimated_speed = min(speed_mbps * 100, 100.0)  # Cap à 100 Mbps
                
                self.connection_speed_cache = estimated_speed
                self.connection_speed_timestamp = current_time
                
                return estimated_speed
            
        except Exception as e:
            logger.warning(f"Could not estimate connection speed: {e}")
        
        # Valeur par défaut
        default_speed = 10.0  # 10 Mbps
        self.connection_speed_cache = default_speed
        self.connection_speed_timestamp = current_time
        return default_speed
    
    def get_recommended_model(self, 
                            model_type: str = "asr",
                            language: str = None,
                            quality_preference: str = "balanced",
                            device_preference: str = "auto") -> ModelRecommendation:
        """
        Recommande le meilleur modèle selon les contraintes système
        
        Args:
            model_type: Type de modèle ("asr", "diarization", "ocr")
            language: Langue préférée (None pour multilingue)
            quality_preference: "speed", "balanced", "quality"
            device_preference: "cpu", "gpu", "auto"
            
        Returns:
            Recommandation de modèle avec justification
        """
        resources = self.get_system_resources()
        
        # Filtrer les modèles par type
        candidates = [
            model for model in self.model_catalog.values()
            if model.model_type == model_type
        ]
        
        # Filtrer par compatibilité de dispositif
        if device_preference != "auto":
            candidates = [
                model for model in candidates
                if device_preference in model.device_compatibility
            ]
        
        # Filtrer par langue si spécifiée
        if language:
            candidates = [
                model for model in candidates
                if language in model.languages or "multilingual" in model.languages
            ]
        
        # Filtrer par ressources disponibles
        candidates = [
            model for model in candidates
            if model.memory_requirement_mb <= resources.available_memory_mb
            and model.size_mb <= (resources.disk_space_gb * 1024 * 0.1)  # Max 10% de l'espace disque
        ]
        
        if not candidates:
            # Fallback vers le modèle le plus léger disponible
            all_models = list(self.model_catalog.values())
            all_models.sort(key=lambda m: m.size_mb)
            fallback_model = all_models[0]
            
            return ModelRecommendation(
                model_name=fallback_model.name,
                category=fallback_model.category,
                estimated_download_time=fallback_model.download_time_estimate,
                quality_level=fallback_model.quality,
                reason="Fallback: ressources système limitées",
                confidence=0.3,
                alternatives=[]
            )
        
        # Scorer les modèles selon les préférences
        scored_models = []
        for model in candidates:
            score = self._score_model(model, resources, quality_preference, device_preference)
            scored_models.append((model, score))
        
        # Trier par score décroissant
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        best_model, best_score = scored_models[0]
        
        # Générer les alternatives
        alternatives = [model.name for model, _ in scored_models[1:4]]  # Top 3 alternatives
        
        # Générer la raison
        reason = self._generate_recommendation_reason(best_model, resources, quality_preference)
        
        return ModelRecommendation(
            model_name=best_model.name,
            category=best_model.category,
            estimated_download_time=self._adjust_download_time(
                best_model.download_time_estimate, 
                resources.connection_speed_mbps
            ),
            quality_level=best_model.quality,
            reason=reason,
            confidence=min(best_score / 100.0, 1.0),
            alternatives=alternatives
        )
    
    def _score_model(self, 
                    model: ModelInfo, 
                    resources: SystemResources,
                    quality_preference: str,
                    device_preference: str) -> float:
        """Score un modèle selon les critères et ressources"""
        score = 0.0
        
        # Score de base selon la catégorie et préférence qualité
        category_scores = {
            "ultra_light": {"speed": 100, "balanced": 80, "quality": 40},
            "light": {"speed": 80, "balanced": 100, "quality": 70},
            "medium": {"speed": 60, "balanced": 90, "quality": 90},
            "heavy": {"speed": 30, "balanced": 70, "quality": 100}
        }
        
        base_score = category_scores.get(model.category, {}).get(quality_preference, 50)
        score += base_score
        
        # Bonus pour compatibilité GPU si disponible
        if resources.gpu_available and "gpu" in model.device_compatibility:
            score += 20
        
        # Bonus pour compatibilité CPU si GPU non disponible
        if not resources.gpu_available and "cpu" in model.device_compatibility:
            score += 15
        
        # Pénalité pour utilisation mémoire élevée
        memory_ratio = model.memory_requirement_mb / resources.available_memory_mb
        if memory_ratio > 0.8:
            score -= 30
        elif memory_ratio > 0.6:
            score -= 15
        elif memory_ratio < 0.3:
            score += 10
        
        # Bonus pour temps de téléchargement rapide
        if model.download_time_estimate < 60:
            score += 15
        elif model.download_time_estimate > 300:
            score -= 10
        
        # Bonus pour modèles multilingues si pas de langue spécifiée
        if "multilingual" in model.languages:
            score += 5
        
        return score
    
    def _adjust_download_time(self, base_time: int, connection_speed_mbps: float) -> int:
        """Ajuste le temps de téléchargement selon la vitesse de connexion"""
        # Temps de base calculé pour ~10 Mbps
        base_speed_mbps = 10.0
        speed_ratio = base_speed_mbps / max(connection_speed_mbps, 1.0)
        
        adjusted_time = int(base_time * speed_ratio)
        return max(adjusted_time, 10)  # Minimum 10 secondes
    
    def _generate_recommendation_reason(self, 
                                      model: ModelInfo, 
                                      resources: SystemResources,
                                      quality_preference: str) -> str:
        """Génère une explication pour la recommandation"""
        reasons = []
        
        # Raison principale selon la catégorie
        if model.category == "ultra_light":
            reasons.append("modèle ultra-léger pour démarrage rapide")
        elif model.category == "light":
            reasons.append("bon équilibre performance/qualité")
        elif model.category == "medium":
            reasons.append("qualité élevée avec ressources suffisantes")
        elif model.category == "heavy":
            reasons.append("qualité maximale avec ressources importantes")
        
        # Raisons spécifiques aux ressources
        if resources.available_memory_mb < 2000:
            reasons.append("optimisé pour mémoire limitée")
        elif resources.available_memory_mb > 8000:
            reasons.append("profite de la mémoire abondante")
        
        if resources.gpu_available and "gpu" in model.device_compatibility:
            reasons.append("optimisé GPU disponible")
        elif not resources.gpu_available:
            reasons.append("compatible CPU uniquement")
        
        if resources.connection_speed_mbps < 5:
            reasons.append("téléchargement rapide avec connexion lente")
        
        return ", ".join(reasons)
    
    def get_models_by_category(self, category: str) -> List[ModelInfo]:
        """Obtient tous les modèles d'une catégorie"""
        return [
            model for model in self.model_catalog.values()
            if model.category == category
        ]
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Obtient les informations détaillées d'un modèle"""
        return self.model_catalog.get(model_name)
    
    def get_available_models(self, 
                           model_type: str = None,
                           max_size_mb: int = None,
                           device_compatibility: str = None) -> List[ModelInfo]:
        """
        Obtient la liste des modèles disponibles avec filtres
        
        Args:
            model_type: Type de modèle à filtrer
            max_size_mb: Taille maximale en MB
            device_compatibility: Compatibilité de dispositif requise
            
        Returns:
            Liste des modèles correspondants
        """
        models = list(self.model_catalog.values())
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        if max_size_mb:
            models = [m for m in models if m.size_mb <= max_size_mb]
        
        if device_compatibility:
            models = [m for m in models if device_compatibility in m.device_compatibility]
        
        # Trier par taille (plus léger en premier)
        models.sort(key=lambda m: m.size_mb)
        
        return models
    
    def refresh_system_resources(self):
        """Force la mise à jour des informations système"""
        self.system_resources = None
        self.connection_speed_cache = None
        self.connection_speed_timestamp = 0
    
    async def ensure_model_available(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """
        S'assure qu'un modèle est disponible, le télécharge si nécessaire
        
        Returns:
            Tuple (is_available, file_path)
        """
        try:
            # Vérifier si le modèle est en cache et valide
            # Adapter selon le type de cache manager
            if hasattr(self.cache_manager, 'is_model_cached'):
                # Cache simple (synchrone)
                if self.cache_manager.is_model_cached(model_name):
                    file_path = self.cache_manager.get_model_path(model_name)
                    logger.info(f"Modèle {model_name} trouvé en cache: {file_path}")
                    return True, file_path
            else:
                # Cache avancé (asynchrone)
                if await self.cache_manager.is_model_cached(model_name):
                    if await self.cache_manager.validate_model(model_name):
                        file_path = self.cache_manager.get_model_path(model_name)
                        logger.info(f"Modèle {model_name} trouvé en cache: {file_path}")
                        return True, file_path
                    else:
                        # Modèle corrompu, le supprimer
                        logger.warning(f"Modèle {model_name} corrompu, suppression du cache")
                        await self.cache_manager.remove_model(model_name)
            
            # Le modèle n'est pas disponible ou est corrompu
            logger.info(f"Modèle {model_name} non disponible en cache")
            return False, None
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du modèle {model_name}: {e}")
            return False, None
    
    async def get_cached_models_info(self) -> List[Dict[str, Any]]:
        """Obtient les informations des modèles en cache"""
        try:
            # Adapter selon le type de cache manager
            if hasattr(self.cache_manager, 'list_cached_models'):
                cached_models = self.cache_manager.list_cached_models()
            else:
                cached_models = []
            
            # Enrichir avec les informations du catalogue
            for cached_model in cached_models:
                model_name = cached_model['name']
                if model_name in self.model_catalog:
                    model_info = self.model_catalog[model_name]
                    cached_model.update({
                        'category': model_info.category,
                        'quality': model_info.quality,
                        'languages': model_info.languages,
                        'model_type': model_info.model_type,
                        'description': model_info.description
                    })
                else:
                    # Modèle non reconnu dans le catalogue
                    cached_model.update({
                        'category': 'unknown',
                        'quality': 'unknown',
                        'languages': ['unknown'],
                        'model_type': 'unknown',
                        'description': 'Modèle non reconnu'
                    })
            
            return cached_models
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modèles en cache: {e}")
            return []
    
    async def remove_cached_model(self, model_name: str) -> bool:
        """Supprime un modèle du cache"""
        try:
            # Adapter selon le type de cache manager
            if hasattr(self.cache_manager, 'remove_model') and not asyncio.iscoroutinefunction(self.cache_manager.remove_model):
                # Cache simple (synchrone)
                success = self.cache_manager.remove_model(model_name)
            else:
                # Cache avancé (asynchrone)
                success = await self.cache_manager.remove_model(model_name)
            
            if success:
                logger.info(f"Modèle {model_name} supprimé du cache")
            return success
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du modèle {model_name}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques du cache"""
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            return {
                'total_models': cache_stats.total_models,
                'total_size_mb': cache_stats.total_size_mb,
                'available_space_mb': cache_stats.available_space_mb,
                'cache_hit_rate': cache_stats.cache_hit_rate,
                'last_cleanup': cache_stats.last_cleanup
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques du cache: {e}")
            return {
                'total_models': 0,
                'total_size_mb': 0.0,
                'available_space_mb': 0.0,
                'cache_hit_rate': 0.0,
                'last_cleanup': 0.0
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques de performance du gestionnaire"""
        resources = self.get_system_resources()
        cache_stats = self.get_cache_stats()
        
        return {
            "total_models": len(self.model_catalog),
            "models_by_category": {
                category: len([m for m in self.model_catalog.values() if m.category == category])
                for category in ["ultra_light", "light", "medium", "heavy"]
            },
            "models_by_type": {
                model_type: len([m for m in self.model_catalog.values() if m.model_type == model_type])
                for model_type in ["asr", "diarization", "ocr"]
            },
            "system_resources": {
                "available_memory_mb": resources.available_memory_mb,
                "gpu_available": resources.gpu_available,
                "connection_speed_mbps": resources.connection_speed_mbps,
                "disk_space_gb": resources.disk_space_gb
            },
            "cache_stats": cache_stats
        }


# Instance globale
lightweight_model_manager = LightweightModelManager()