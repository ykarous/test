"""
AIModelManager amélioré avec intégration complète des optimisations de performance
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Imports des composants de performance
from ..performance.async_controller import AsyncNeMoController
from ..performance.fallback_system import IntelligentFallbackSystem
from ..performance.model_manager import LightweightModelManager
from ..performance.download_manager import IntelligentDownloadManager
from ..performance.cache_manager import ModelCacheManager
from ..performance.progress_interface import RealTimeProgressInterface
from ..performance.diagnostic_engine import DiagnosticEngine
from ..performance.model_actions import ModelActionManager
from ..performance.model_notifications import SmartNotificationManager
from ..performance.auto_optimizer import AutoOptimizer

# Imports existants
from .ai_model_manager_async import AsyncAIModelManager

logger = logging.getLogger(__name__)

class TranscriptionMode(Enum):
    """Modes de transcription disponibles"""
    FAST = "fast"           # Privilégie la vitesse
    BALANCED = "balanced"   # Équilibre vitesse/qualité
    QUALITY = "quality"     # Privilégie la qualité
    ADAPTIVE = "adaptive"   # S'adapte automatiquement

@dataclass
class TranscriptionConfig:
    """Configuration pour une transcription"""
    mode: TranscriptionMode = TranscriptionMode.BALANCED
    preferred_model: Optional[str] = None
    language: Optional[str] = None
    enable_fallback: bool = True
    enable_caching: bool = True
    max_duration: Optional[int] = None  # Durée max en secondes
    quality_threshold: float = 0.8      # Seuil de qualité minimum
    timeout: Optional[int] = None       # Timeout personnalisé

class EnhancedAIModelManager(AsyncAIModelManager):
    """AIModelManager avec intégration complète des optimisations de performance"""
    
    def __init__(self, 
                 models_dir: str = ".kiro/models",
                 cache_dir: str = ".kiro/cache",
                 config_dir: str = ".kiro/config",
                 max_memory_usage: float = 0.8,
                 cache_timeout: int = 300):
        
        super().__init__(max_memory_usage, cache_timeout)
        
        # Répertoires de configuration
        self.models_dir = Path(models_dir)
        self.cache_dir = Path(cache_dir)
        self.config_dir = Path(config_dir)
        
        # Créer les répertoires nécessaires
        for directory in [self.models_dir, self.cache_dir, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialiser les composants de performance
        self._initialize_performance_components()
        
        # Configuration des modes de transcription
        self._setup_transcription_modes()
        
        # Statistiques et métriques
        self.performance_metrics = {
            "total_transcriptions": 0,
            "successful_transcriptions": 0,
            "failed_transcriptions": 0,
            "fallback_usage": 0,
            "cache_hits": 0,
            "average_processing_time": 0.0,
            "models_downloaded": 0,
            "errors_recovered": 0
        }
        
        # État interne
        self._initialized = False
        self._shutdown = False
        
        logger.info("Enhanced AI Model Manager initialized")
    
    def _initialize_performance_components(self):
        """Initialise tous les composants de performance"""
        
        # Contrôleur asynchrone (déjà initialisé par la classe parent)
        # self.async_controller = AsyncNeMoController()
        
        # Système de fallback intelligent
        self.fallback_system = IntelligentFallbackSystem()
        
        # Gestionnaire de modèles légers
        self.model_manager = LightweightModelManager(str(self.models_dir))
        
        # Gestionnaire de téléchargement intelligent
        self.download_manager = IntelligentDownloadManager(str(self.models_dir))
        
        # Gestionnaire de cache
        from ..performance.cache_manager import ModelCacheManager
        self.cache_manager = ModelCacheManager(str(self.cache_dir))
        
        # Interface de progression temps réel
        self.progress_interface = RealTimeProgressInterface()
        
        # Moteur de diagnostic
        self.diagnostic_engine = DiagnosticEngine()
        
        # Gestionnaire d'actions sur les modèles
        self.action_manager = ModelActionManager(str(self.models_dir))
        
        # Gestionnaire de notifications intelligent
        self.notification_manager = SmartNotificationManager(
            str(self.config_dir / "notifications_config.json")
        )
        
        # Optimiseur automatique
        self.auto_optimizer = AutoOptimizer()
        
        # Connecter les callbacks entre composants
        self._setup_component_callbacks()
    
    def _setup_component_callbacks(self):
        """Configure les callbacks entre les différents composants"""
        
        # Callbacks de progression
        def progress_callback(operation_id: str, **kwargs):
            # Propager les mises à jour de progression
            pass
        
        self.progress_interface.add_ui_callback(progress_callback)
        
        # Callbacks de notifications
        def notification_callback(notification):
            logger.info(f"Notification: {notification.title}")
        
        self.notification_manager.add_global_callback(notification_callback)
        
        # Callbacks d'actions sur les modèles
        def action_progress_callback(progress):
            logger.debug(f"Action progress: {progress.current_step} ({progress.progress_percent:.1f}%)")
        
        self.action_manager.add_progress_callback(action_progress_callback)
    
    def _setup_transcription_modes(self):
        """Configure les modes de transcription"""
        
        self.transcription_modes = {
            TranscriptionMode.FAST: {
                "preferred_models": ["whisper-tiny", "whisper-base"],
                "quality_threshold": 0.6,
                "timeout_multiplier": 0.5,
                "enable_optimizations": True
            },
            
            TranscriptionMode.BALANCED: {
                "preferred_models": ["whisper-base", "whisper-medium"],
                "quality_threshold": 0.8,
                "timeout_multiplier": 1.0,
                "enable_optimizations": True
            },
            
            TranscriptionMode.QUALITY: {
                "preferred_models": ["whisper-large-v3", "nemo-conformer-ctc-large"],
                "quality_threshold": 0.9,
                "timeout_multiplier": 2.0,
                "enable_optimizations": False
            },
            
            TranscriptionMode.ADAPTIVE: {
                "preferred_models": [],  # Sera déterminé dynamiquement
                "quality_threshold": 0.8,
                "timeout_multiplier": 1.0,
                "enable_optimizations": True
            }
        }
    
    async def initialize_async(self):
        """Initialisation asynchrone complète"""
        
        if self._initialized:
            return
        
        logger.info("Starting async initialization...")
        
        try:
            # Initialiser le diagnostic système
            await self.diagnostic_engine.run_full_diagnostic()
            
            # Optimiser la configuration initiale
            optimization_result = await self.auto_optimizer.optimize_system_configuration()
            logger.info(f"System optimization completed: {optimization_result}")
            
            # Vérifier les modèles disponibles
            await self.model_manager.refresh_model_catalog()
            
            # Initialiser le cache
            await self.cache_manager.initialize()
            
            self._initialized = True
            logger.info("Enhanced AI Model Manager fully initialized")
            
        except Exception as e:
            logger.error(f"Async initialization failed: {e}")
            raise
    
    async def transcribe_with_performance_optimization(
        self,
        audio_path: str,
        config: Optional[TranscriptionConfig] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcription avec optimisation complète des performances
        
        Args:
            audio_path: Chemin vers le fichier audio
            config: Configuration de transcription
            progress_callback: Callback de progression
            **kwargs: Arguments additionnels
            
        Returns:
            Résultats de transcription avec métriques
        """
        
        if not self._initialized:
            await self.initialize_async()
        
        # Configuration par défaut
        if config is None:
            config = TranscriptionConfig()
        
        # Créer un tracker de progression
        tracker = await self.progress_interface.track_operation(
            operation_type="transcription",
            estimated_duration=self._estimate_transcription_duration(audio_path),
            metadata={"audio_path": audio_path, "mode": config.mode.value}
        )
        
        start_time = time.time()
        
        try:
            # Étape 1: Vérifier le cache
            await tracker.update(progress_percent=5, current_step="Vérification du cache")
            
            if config.enable_caching:
                cached_result = await self.cache_manager.get_cached_transcription(audio_path)
                if cached_result:
                    self.performance_metrics["cache_hits"] += 1
                    await tracker.update(progress_percent=100, current_step="Résultat trouvé en cache")
                    await self.progress_interface.complete_operation(tracker.progress.operation_id, True)
                    return self._format_transcription_result(cached_result, from_cache=True)
            
            # Étape 2: Sélection du modèle optimal
            await tracker.update(progress_percent=10, current_step="Sélection du modèle optimal")
            
            optimal_model = await self._select_optimal_model_enhanced(audio_path, config)
            logger.info(f"Selected optimal model: {optimal_model}")
            
            # Étape 3: Vérifier et télécharger le modèle si nécessaire
            await tracker.update(progress_percent=20, current_step="Vérification du modèle")
            
            model_available = await self.model_manager.ensure_model_available(optimal_model)
            if not model_available:
                await tracker.update(progress_percent=25, current_step="Téléchargement du modèle")
                await self._download_model_with_progress(optimal_model, tracker)
            
            # Étape 4: Transcription avec fallback
            await tracker.update(progress_percent=40, current_step="Démarrage de la transcription")
            
            if config.enable_fallback:
                result = await self._transcribe_with_fallback(
                    audio_path, optimal_model, config, tracker, progress_callback
                )
            else:
                result = await self._transcribe_single_model(
                    audio_path, optimal_model, config, tracker, progress_callback
                )
            
            # Étape 5: Post-traitement et cache
            await tracker.update(progress_percent=90, current_step="Post-traitement")
            
            processed_result = await self._post_process_transcription(result, config)
            
            # Sauvegarder en cache si activé
            if config.enable_caching:
                await self.cache_manager.cache_transcription_result(audio_path, processed_result)
            
            # Finaliser
            processing_time = time.time() - start_time
            await tracker.update(progress_percent=100, current_step="Transcription terminée")
            await self.progress_interface.complete_operation(tracker.progress.operation_id, True)
            
            # Mettre à jour les métriques
            self._update_performance_metrics(True, processing_time)
            
            return self._format_transcription_result(processed_result, processing_time=processing_time)
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            
            # Mettre à jour les métriques d'erreur
            processing_time = time.time() - start_time
            self._update_performance_metrics(False, processing_time)
            
            # Marquer l'opération comme échouée
            await self.progress_interface.complete_operation(tracker.progress.operation_id, False, str(e))
            
            # Créer une notification d'erreur
            from ..performance.model_actions import ModelNotification, NotificationType
            error_notification = ModelNotification(
                notification_id=f"transcription_error_{int(time.time())}",
                notification_type=NotificationType.ERROR,
                title="Échec de transcription",
                message=f"La transcription de {Path(audio_path).name} a échoué: {str(e)}",
                actions=["retry_transcription", "check_audio_file", "contact_support"],
                priority=2
            )
            await self.notification_manager.add_notification(error_notification)
            
            raise
    
    async def _select_optimal_model_enhanced(
        self, 
        audio_path: str, 
        config: TranscriptionConfig
    ) -> str:
        """Sélection de modèle améliorée avec tous les critères"""
        
        # Si un modèle préféré est spécifié
        if config.preferred_model:
            return config.preferred_model
        
        # Mode adaptatif - analyse complète
        if config.mode == TranscriptionMode.ADAPTIVE:
            return await self._adaptive_model_selection(audio_path, config)
        
        # Sélection basée sur le mode
        mode_config = self.transcription_modes[config.mode]
        preferred_models = mode_config["preferred_models"]
        
        if not preferred_models:
            return await self._adaptive_model_selection(audio_path, config)
        
        # Vérifier la disponibilité des modèles préférés
        for model in preferred_models:
            if await self.model_manager.is_model_available(model):
                return model
        
        # Fallback vers le premier modèle de la liste
        return preferred_models[0]
    
    async def _adaptive_model_selection(
        self, 
        audio_path: str, 
        config: TranscriptionConfig
    ) -> str:
        """Sélection adaptative basée sur l'analyse complète"""
        
        # Analyser le fichier audio
        audio_analysis = self._analyze_audio_file(audio_path)
        
        # Obtenir les ressources système
        system_resources = await self.diagnostic_engine.get_system_resources()
        
        # Obtenir les recommandations du gestionnaire de modèles
        recommended_model = await self.model_manager.get_recommended_model(
            audio_duration=audio_analysis["duration"],
            available_memory=system_resources.get("memory_available_mb", 1000),
            cpu_cores=system_resources.get("cpu_cores", 2),
            has_gpu=system_resources.get("has_gpu", False)
        )
        
        return recommended_model
    
    async def _transcribe_with_fallback(
        self,
        audio_path: str,
        primary_model: str,
        config: TranscriptionConfig,
        tracker,
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Transcription avec système de fallback intelligent"""
        
        # Configurer la chaîne de fallback
        fallback_chain = [primary_model]
        
        # Ajouter des modèles de fallback selon le mode
        mode_config = self.transcription_modes[config.mode]
        for model in mode_config["preferred_models"]:
            if model != primary_model and model not in fallback_chain:
                fallback_chain.append(model)
        
        # Ajouter des fallbacks universels
        universal_fallbacks = ["whisper-base", "whisper-tiny"]
        for model in universal_fallbacks:
            if model not in fallback_chain:
                fallback_chain.append(model)
        
        # Exécuter avec le système de fallback
        result = await self.fallback_system.execute_with_fallback(
            operation_name="transcription",
            primary_method=lambda: self._transcribe_single_model(
                audio_path, primary_model, config, tracker, progress_callback
            ),
            fallback_methods=[
                lambda model=model: self._transcribe_single_model(
                    audio_path, model, config, tracker, progress_callback
                )
                for model in fallback_chain[1:]
            ],
            quality_check=lambda result: self._check_transcription_quality(result, config),
            progress_callback=progress_callback
        )
        
        if result["used_fallback"]:
            self.performance_metrics["fallback_usage"] += 1
        
        return result
    
    async def _transcribe_single_model(
        self,
        audio_path: str,
        model_name: str,
        config: TranscriptionConfig,
        tracker,
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Transcription avec un seul modèle"""
        
        # Calculer le timeout
        base_timeout = self.operation_timeouts.get("transcription", 600)
        mode_config = self.transcription_modes[config.mode]
        timeout = int(base_timeout * mode_config["timeout_multiplier"])
        
        if config.timeout:
            timeout = config.timeout
        
        # Préparer les arguments de transcription
        transcription_args = {
            "audio_path": audio_path,
            "model_name": model_name,
            "language": config.language,
            "progress_callback": progress_callback
        }
        
        # Exécuter la transcription avec le contrôleur asynchrone
        result = await self.async_controller.execute_with_timeout(
            lambda: super().transcribe_audio_async(**transcription_args),
            operation_type="transcription",
            timeout=timeout,
            progress_callback=progress_callback
        )
        
        return {
            "result": result,
            "model_used": model_name,
            "processing_time": getattr(result, 'processing_time', 0),
            "used_fallback": False
        }
    
    def _check_transcription_quality(
        self, 
        result: Dict[str, Any], 
        config: TranscriptionConfig
    ) -> bool:
        """Vérifie la qualité d'une transcription"""
        
        if "result" not in result:
            return False
        
        transcription_result = result["result"]
        
        # Vérifications basiques
        if not hasattr(transcription_result, 'text') or not transcription_result.text.strip():
            return False
        
        # Vérification du seuil de confiance si disponible
        if hasattr(transcription_result, 'confidence'):
            return transcription_result.confidence >= config.quality_threshold
        
        # Si pas de métrique de confiance, considérer comme valide
        return True
    
    async def _post_process_transcription(
        self, 
        result: Dict[str, Any], 
        config: TranscriptionConfig
    ) -> Dict[str, Any]:
        """Post-traitement des résultats de transcription"""
        
        # Ajouter des métadonnées
        result["transcription_mode"] = config.mode.value
        result["timestamp"] = time.time()
        
        # Optimisations post-traitement si activées
        mode_config = self.transcription_modes[config.mode]
        if mode_config.get("enable_optimizations", False):
            # Appliquer des optimisations (nettoyage du texte, etc.)
            result = await self._apply_post_processing_optimizations(result)
        
        return result
    
    async def _apply_post_processing_optimizations(
        self, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Applique des optimisations de post-traitement"""
        
        # Placeholder pour les optimisations futures
        # - Nettoyage du texte
        # - Correction orthographique
        # - Formatage intelligent
        
        return result
    
    def _estimate_transcription_duration(self, audio_path: str) -> float:
        """Estime la durée de transcription"""
        
        try:
            audio_info = self._analyze_audio_file(audio_path)
            duration = audio_info["duration"]
            
            # Estimation basée sur la durée audio (ratio approximatif)
            # Généralement 1:4 à 1:10 selon le modèle et les ressources
            return duration * 6  # Estimation moyenne
            
        except Exception:
            return 60  # Estimation par défaut
    
    async def _download_model_with_progress(
        self, 
        model_name: str, 
        tracker
    ):
        """Télécharge un modèle avec suivi de progression"""
        
        def download_progress(downloaded: int, total: int):
            if total > 0:
                progress = 25 + (downloaded / total) * 15  # 25-40%
                tracker.update(
                    progress_percent=progress,
                    current_step=f"Téléchargement {model_name}: {downloaded}/{total} bytes"
                )
        
        await self.download_manager.download_model(
            model_name, 
            progress_callback=download_progress
        )
        
        self.performance_metrics["models_downloaded"] += 1
    
    def _format_transcription_result(
        self, 
        result: Dict[str, Any], 
        from_cache: bool = False,
        processing_time: float = 0
    ) -> Dict[str, Any]:
        """Formate le résultat final de transcription"""
        
        return {
            "transcription": result,
            "metadata": {
                "from_cache": from_cache,
                "processing_time": processing_time,
                "timestamp": time.time()
            },
            "performance_metrics": self.get_performance_summary()
        }
    
    def _update_performance_metrics(self, success: bool, processing_time: float):
        """Met à jour les métriques de performance"""
        
        self.performance_metrics["total_transcriptions"] += 1
        
        if success:
            self.performance_metrics["successful_transcriptions"] += 1
        else:
            self.performance_metrics["failed_transcriptions"] += 1
        
        # Mettre à jour le temps moyen
        total = self.performance_metrics["total_transcriptions"]
        current_avg = self.performance_metrics["average_processing_time"]
        self.performance_metrics["average_processing_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtient un résumé des performances"""
        
        return {
            "metrics": self.performance_metrics.copy(),
            "system_resources": self.diagnostic_engine.get_current_resources(),
            "active_operations": len(self.progress_interface.list_active_operations()),
            "cache_stats": self.cache_manager.get_cache_stats(),
            "model_stats": self.model_manager.get_model_stats()
        }
    
    async def run_performance_diagnostic(self) -> Dict[str, Any]:
        """Exécute un diagnostic complet des performances"""
        
        diagnostic_result = await self.diagnostic_engine.run_full_diagnostic()
        
        return {
            "diagnostic": diagnostic_result,
            "recommendations": await self.auto_optimizer.get_optimization_recommendations(),
            "performance_summary": self.get_performance_summary()
        }
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Optimise automatiquement le système"""
        
        optimization_result = await self.auto_optimizer.optimize_system_configuration()
        
        # Appliquer les optimisations recommandées
        if optimization_result.get("cache_optimization"):
            await self.cache_manager.optimize_cache_settings()
        
        if optimization_result.get("model_optimization"):
            await self.model_manager.optimize_model_selection()
        
        return optimization_result
    
    async def cleanup_resources(self):
        """Nettoie les ressources et optimise l'utilisation mémoire"""
        
        # Nettoyer le cache
        await self.cache_manager.cleanup_expired_cache()
        
        # Nettoyer les modèles non utilisés
        await self.model_manager.cleanup_unused_models()
        
        # Nettoyer les notifications anciennes
        await self.notification_manager.cleanup_old_notifications()
        
        # Forcer le garbage collection
        import gc
        gc.collect()
        
        logger.info("Resource cleanup completed")
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire"""
        
        if self._shutdown:
            return
        
        self._shutdown = True
        logger.info("Shutting down Enhanced AI Model Manager...")
        
        try:
            # Annuler toutes les opérations en cours
            await self.async_controller.cancel_all_operations()
            
            # Fermer tous les composants
            await self.progress_interface.shutdown()
            await self.notification_manager.close()
            await self.action_manager.close()
            await self.cache_manager.close()
            
            # Nettoyer les ressources
            await self.cleanup_resources()
            
            logger.info("Enhanced AI Model Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Instance globale améliorée
enhanced_ai_manager = EnhancedAIModelManager()