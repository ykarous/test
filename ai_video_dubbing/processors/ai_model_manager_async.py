"""
Extension asynchrone pour AIModelManager avec optimisations de performance
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from .ai_model_manager import AIModelManager
from ..performance.async_controller import AsyncNeMoController
from ..models.data_models import TranscriptionResult, ModelType, ProcessingError

logger = logging.getLogger(__name__)


class AsyncAIModelManager(AIModelManager):
    """Extension asynchrone d'AIModelManager avec contrôleur de performance"""
    
    def __init__(self, max_memory_usage: float = 0.8, cache_timeout: int = 300):
        super().__init__(max_memory_usage, cache_timeout)
        self.async_controller = AsyncNeMoController()
        
        # Configuration des timeouts par opération
        self.operation_timeouts = {
            "model_loading": 120,  # 2 minutes
            "transcription": 600,  # 10 minutes
            "download": 300,       # 5 minutes
        }
    
    async def transcribe_audio_async(
        self,
        audio_path: str,
        model_name: str = "whisper-base",
        language: str = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcription asynchrone avec gestion des timeouts et progression
        
        Args:
            audio_path: Chemin vers le fichier audio
            model_name: Nom du modèle à utiliser
            language: Langue (optionnel)
            progress_callback: Callback pour les mises à jour de progression
            **kwargs: Arguments additionnels pour la transcription
            
        Returns:
            Résultats de transcription
            
        Raises:
            TimeoutError: Si l'opération dépasse le timeout
            ProcessingError: Si la transcription échoue
        """
        
        async def transcription_operation():
            """Opération de transcription wrappée"""
            try:
                # Charger le modèle de manière asynchrone
                await self._load_model_async(ModelType.ASR, model_name, progress_callback)
                
                # Effectuer la transcription
                if model_name.startswith("nemo-"):
                    return await self._transcribe_with_nemo_async(
                        audio_path, model_name, language, **kwargs
                    )
                else:
                    return await self._transcribe_with_whisper_async(
                        audio_path, model_name, language, **kwargs
                    )
                    
            except Exception as e:
                logger.error(f"Transcription operation failed: {e}")
                raise ProcessingError(f"Transcription failed: {e}")
        
        # Exécuter avec le contrôleur asynchrone
        return await self.async_controller.execute_with_timeout(
            transcription_operation,
            operation_type="transcription",
            timeout=self.operation_timeouts["transcription"],
            progress_callback=progress_callback
        )
    
    async def _load_model_async(
        self,
        model_type: ModelType,
        model_name: str,
        progress_callback: Optional[Callable] = None
    ):
        """
        Chargement asynchrone de modèle avec progression
        
        Args:
            model_type: Type de modèle
            model_name: Nom du modèle
            progress_callback: Callback de progression
        """
        
        async def loading_operation():
            """Opération de chargement wrappée"""
            try:
                # Vérifier si le modèle est déjà chargé
                model_key = self._model_key(model_type, model_name)
                if model_key in self._loaded_models:
                    logger.info(f"Model {model_key} already loaded")
                    return
                
                # Charger le modèle (synchrone pour l'instant)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    self.load_model, 
                    model_type, 
                    model_name
                )
                
            except Exception as e:
                logger.error(f"Model loading failed: {e}")
                raise ProcessingError(f"Failed to load model {model_name}: {e}")
        
        # Exécuter avec timeout
        await self.async_controller.execute_with_timeout(
            loading_operation,
            operation_type="model_loading",
            timeout=self.operation_timeouts["model_loading"],
            progress_callback=progress_callback
        )
    
    async def _transcribe_with_whisper_async(
        self,
        audio_path: str,
        model_name: str,
        language: str = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcription Whisper asynchrone
        
        Args:
            audio_path: Chemin audio
            model_name: Nom du modèle Whisper
            language: Langue
            **kwargs: Arguments additionnels
            
        Returns:
            Résultats de transcription
        """
        try:
            # Exécuter la transcription synchrone dans un executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.transcribe_audio,
                audio_path,
                model_name,
                language,
                kwargs.get('word_timestamps', True),
                kwargs.get('temperature', 0.0),
                kwargs.get('beam_size', 5),
                kwargs.get('best_of', 5)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Whisper async transcription failed: {e}")
            raise ProcessingError(f"Whisper transcription failed: {e}")
    
    async def _transcribe_with_nemo_async(
        self,
        audio_path: str,
        model_name: str,
        language: str = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcription NeMo asynchrone
        
        Args:
            audio_path: Chemin audio
            model_name: Nom du modèle NeMo
            language: Langue
            **kwargs: Arguments additionnels
            
        Returns:
            Résultats de transcription
        """
        try:
            # Pour l'instant, utiliser la méthode existante si disponible
            if hasattr(self, 'transcribe_audio_with_nemo'):
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.transcribe_audio_with_nemo,
                    audio_path,
                    model_name,
                    language
                )
                return result
            else:
                # Fallback vers Whisper
                logger.warning(f"NeMo transcription not available, falling back to Whisper")
                return await self._transcribe_with_whisper_async(
                    audio_path, "whisper-base", language, **kwargs
                )
                
        except Exception as e:
            logger.error(f"NeMo async transcription failed: {e}")
            # Fallback vers Whisper en cas d'erreur
            logger.info("Falling back to Whisper due to NeMo error")
            return await self._transcribe_with_whisper_async(
                audio_path, "whisper-base", language, **kwargs
            )
    
    async def transcribe_with_performance_optimization(
        self,
        audio_path: str,
        preferred_model: str = None,
        language: str = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcription avec optimisation automatique des performances
        
        Args:
            audio_path: Chemin vers le fichier audio
            preferred_model: Modèle préféré (optionnel)
            language: Langue (optionnel)
            progress_callback: Callback de progression
            **kwargs: Arguments additionnels
            
        Returns:
            Résultats de transcription optimisés
        """
        
        # Déterminer le meilleur modèle selon les ressources
        if preferred_model is None:
            preferred_model = self._select_optimal_model(audio_path)
        
        # Chaîne de fallback
        fallback_models = [
            preferred_model,
            "whisper-base",  # Fallback léger
            "whisper-tiny"   # Fallback ultra-léger
        ]
        
        last_error = None
        
        for model_name in fallback_models:
            try:
                logger.info(f"Attempting transcription with {model_name}")
                
                result = await self.transcribe_audio_async(
                    audio_path=audio_path,
                    model_name=model_name,
                    language=language,
                    progress_callback=progress_callback,
                    **kwargs
                )
                
                logger.info(f"Transcription successful with {model_name}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Transcription failed with {model_name}: {e}")
                
                # Si ce n'est pas le dernier modèle, continuer
                if model_name != fallback_models[-1]:
                    logger.info(f"Trying fallback model...")
                    continue
        
        # Tous les modèles ont échoué
        raise ProcessingError(f"All transcription models failed. Last error: {last_error}")
    
    def _select_optimal_model(self, audio_path: str) -> str:
        """
        Sélectionne le modèle optimal selon les ressources et le fichier audio
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Nom du modèle optimal
        """
        try:
            # Analyser le fichier audio
            audio_info = self._analyze_audio_file(audio_path)
            
            # Obtenir les stats mémoire
            memory_stats = self.get_memory_stats()
            available_memory = memory_stats.get("system_memory_available_mb", 1000)
            
            # Sélection basée sur la mémoire disponible et la durée audio
            if available_memory > 4000 and audio_info["duration"] < 300:  # 4GB+ et <5min
                if hasattr(self, '_nemo_available') and self._nemo_available:
                    return "nemo-conformer-ctc-large-fr"
                else:
                    return "whisper-large-v3"
            elif available_memory > 2000:  # 2GB+
                return "whisper-medium"
            elif available_memory > 1000:  # 1GB+
                return "whisper-base"
            else:
                return "whisper-tiny"
                
        except Exception as e:
            logger.warning(f"Model selection failed, using default: {e}")
            return "whisper-base"
    
    def _analyze_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier audio pour optimiser le traitement
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Informations sur le fichier audio
        """
        try:
            import librosa
            
            # Charger les métadonnées sans charger tout l'audio
            duration = librosa.get_duration(filename=audio_path)
            
            return {
                "duration": duration,
                "file_size": Path(audio_path).stat().st_size,
                "estimated_complexity": "medium"  # Placeholder
            }
            
        except Exception as e:
            logger.warning(f"Audio analysis failed: {e}")
            return {
                "duration": 60,  # Estimation par défaut
                "file_size": 1024 * 1024,  # 1MB par défaut
                "estimated_complexity": "medium"
            }
    
    async def cancel_transcription(self, task_id: str = None) -> bool:
        """
        Annule une transcription en cours
        
        Args:
            task_id: ID de la tâche à annuler (None pour toutes)
            
        Returns:
            True si l'annulation a réussi
        """
        if task_id:
            return await self.async_controller.cancel_operation(task_id)
        else:
            cancelled_count = await self.async_controller.cancel_all_operations()
            return cancelled_count > 0
    
    def get_active_transcriptions(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtient les transcriptions actives
        
        Returns:
            Dictionnaire des transcriptions en cours
        """
        return self.async_controller.get_active_operations()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtient les statistiques de performance complètes
        
        Returns:
            Statistiques de performance
        """
        base_stats = self.get_memory_stats()
        async_stats = self.async_controller.get_performance_stats()
        
        return {
            **base_stats,
            "async_operations": async_stats,
            "operation_timeouts": self.operation_timeouts
        }


# Instance globale pour l'application
async_ai_manager = AsyncAIModelManager()