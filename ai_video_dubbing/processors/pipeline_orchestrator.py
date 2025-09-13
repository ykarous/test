"""
Orchestrateur de pipeline pour l'application de doublage vidéo par IA.
"""

import os
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from ..interfaces.base_interfaces import IPipelineOrchestrator
from ..models.data_models import (
    PipelineConfig, ProcessingResults, ProgressInfo, PipelineStage,
    ValidationError, ProcessingError, ResourceError
)
from ..utils.file_manager import FileManager
from ..utils.temp_storage import TempStorage
from ..utils.output_manager import OutputManager
from .video_processor import VideoProcessor
from .audio_processor import AudioProcessor
from .ai_model_manager import AIModelManager
from .sync_processor import SyncProcessor
from .speaker_segmentation import SpeakerSegmentationProcessor
from .audio_normalizer import AudioNormalizer
from .voice_cloner import VoiceCloner
from .audio_mixer import AudioMixer


class PipelineState(Enum):
    """États du pipeline."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ERROR = "error"


class PipelineOrchestrator(IPipelineOrchestrator):
    """Orchestrateur de pipeline avec gestion d'état et progression."""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialise l'orchestrateur de pipeline.
        
        Args:
            config: Configuration du pipeline
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # État du pipeline
        self.state = PipelineState.IDLE
        self.current_stage = PipelineStage.INITIALIZATION
        self.progress = 0.0
        self.error_message = ""
        
        # Callbacks et contrôle
        self.progress_callbacks: List[Callable[[ProgressInfo], None]] = []
        self.cancel_requested = False
        self.processing_thread: Optional[threading.Thread] = None    
    
        # Gestionnaires et processeurs
        self.file_manager = FileManager()
        self.temp_storage = TempStorage()
        self.output_manager = OutputManager()
        
        # Processeurs IA
        self.ai_model_manager = AIModelManager()
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor(temp_storage=self.temp_storage)
        self.sync_processor = SyncProcessor()
        self.speaker_segmentation = SpeakerSegmentationProcessor()
        self.audio_normalizer = AudioNormalizer()
        self.voice_cloner = VoiceCloner()
        self.audio_mixer = AudioMixer()
        
        # Résultats intermédiaires
        self.intermediate_results: Dict[str, Any] = {}
        
        self.logger.info("Pipeline orchestrator initialized")
    
    def execute_pipeline(self, video_path: str) -> ProcessingResults:
        """
        Exécute le pipeline complet de doublage vidéo.
        
        Args:
            video_path: Chemin vers le fichier vidéo d'entrée
            
        Returns:
            Résultats du traitement complet
            
        Raises:
            ValidationError: Si le fichier vidéo est invalide
            ProcessingError: Si le traitement échoue
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        
        try:
            self.logger.info(f"Starting pipeline execution for {video_path}")
            start_time = time.time()
            
            # Réinitialiser l'état
            self._reset_state()
            self.state = PipelineState.RUNNING
            
            # Étape 1: Validation et préparation
            self._update_progress(PipelineStage.INITIALIZATION, 0.0, "Initializing pipeline...")
            self._validate_input(str(video_path))
            
            # Étape 2: Extraction audio/vidéo
            self._update_progress(PipelineStage.VIDEO_PROCESSING, 5.0, "Extracting audio from video...")
            audio_path = self._extract_audio(str(video_path))
            
            # Étape 3: Analyse audio (VAD + Diarisation)
            self._update_progress(PipelineStage.AUDIO_ANALYSIS, 15.0, "Analyzing audio for speech...")
            speech_segments, speaker_segments = self._analyze_audio(audio_path)
            
            # Étape 4: Séparation de source (optionnelle)
            source_separation_result = None
            if self.config.enable_source_separation:
                self._update_progress(PipelineStage.SOURCE_SEPARATION, 25.0, "Separating audio sources...")
                source_separation_result = self._separate_audio_sources(audio_path)
                audio_path = source_separation_result.vocals_path  # Utiliser les voix séparées
            
            # Étape 5: Transcription ASR
            self._update_progress(PipelineStage.TRANSCRIPTION, 35.0, "Transcribing audio...")
            transcription_result = self._transcribe_audio(audio_path)
            
            # Étape 6: Extraction OCR (optionnelle)
            ocr_results = []
            if self.config.enable_ocr:
                self._update_progress(PipelineStage.OCR_EXTRACTION, 45.0, "Extracting subtitles from video...")
                ocr_results = self._extract_subtitles(str(video_path), speech_segments)
            
            # Étape 7: Synchronisation intelligente
            self._update_progress(PipelineStage.SYNCHRONIZATION, 55.0, "Synchronizing transcription and subtitles...")
            synchronized_segments = self._synchronize_content(transcription_result, ocr_results, speaker_segments)
            
            # Étape 8: Segmentation par locuteur
            self._update_progress(PipelineStage.SPEAKER_SEGMENTATION, 65.0, "Segmenting audio by speaker...")
            speaker_audio_segments = self._segment_by_speaker(audio_path, synchronized_segments)
            
            # Étape 9: Normalisation audio
            self._update_progress(PipelineStage.AUDIO_NORMALIZATION, 70.0, "Normalizing audio for voice cloning...")
            normalized_segments = self._normalize_audio_segments(speaker_audio_segments)
            
            # Étape 10: Clonage de voix
            self._update_progress(PipelineStage.VOICE_CLONING, 75.0, "Cloning voices...")
            cloned_audio_segments = self._clone_voices(normalized_segments, synchronized_segments)
            
            # Étape 11: Mixage audio final
            self._update_progress(PipelineStage.AUDIO_MIXING, 85.0, "Mixing final audio...")
            final_audio_path = self._mix_final_audio(cloned_audio_segments, source_separation_result)
            
            # Étape 12: Assemblage vidéo final
            self._update_progress(PipelineStage.VIDEO_ASSEMBLY, 95.0, "Assembling final video...")
            output_video_path = self._assemble_final_video(str(video_path), final_audio_path)
            
            # Finalisation
            processing_time = time.time() - start_time
            self._update_progress(PipelineStage.COMPLETED, 100.0, "Pipeline completed successfully!")
            
            # Créer les résultats finaux
            results = ProcessingResults(
                output_video_path=str(output_video_path),
                processing_time=processing_time,
                transcription_result=transcription_result,
                speaker_segments=speaker_segments,
                ocr_results=ocr_results,
                source_separation_result=source_separation_result,
                success=True,
                error_message=""
            )
            
            self.state = PipelineState.COMPLETED
            self.logger.info(f"Pipeline completed successfully in {processing_time:.2f}s")
            
            return results
            
        except Exception as e:
            self.state = PipelineState.ERROR
            self.error_message = str(e)
            self.logger.error(f"Pipeline execution failed: {e}")
            
            # Créer un résultat d'erreur
            error_results = ProcessingResults(
                output_video_path="",
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                transcription_result=None,
                speaker_segments=None,
                ocr_results=[],
                source_separation_result=None,
                success=False,
                error_message=str(e)
            )
            
            raise ProcessingError(f"Pipeline execution failed: {e}") from e
    
    def execute_pipeline_async(self, video_path: str) -> None:
        """
        Exécute le pipeline de manière asynchrone.
        
        Args:
            video_path: Chemin vers le fichier vidéo
        """
        if self.state == PipelineState.RUNNING:
            raise ProcessingError("Pipeline is already running")
        
        def run_pipeline():
            try:
                self.execute_pipeline(video_path)
            except Exception as e:
                self.logger.error(f"Async pipeline execution failed: {e}")
        
        self.processing_thread = threading.Thread(target=run_pipeline, daemon=True)
        self.processing_thread.start()
    
    def register_progress_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        Enregistre un callback de progression.
        
        Args:
            callback: Fonction appelée à chaque mise à jour de progression
        """
        self.progress_callbacks.append(callback)
    
    def cancel_processing(self) -> None:
        """Annule le traitement en cours."""
        if self.state == PipelineState.RUNNING:
            self.cancel_requested = True
            self.state = PipelineState.CANCELLED
            self.logger.info("Pipeline cancellation requested")
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Obtient l'état actuel du pipeline.
        
        Returns:
            Dictionnaire avec l'état actuel
        """
        return {
            "state": self.state.value,
            "current_stage": self.current_stage.value if self.current_stage else "unknown",
            "progress": self.progress,
            "error_message": self.error_message,
            "is_running": self.state == PipelineState.RUNNING,
            "can_cancel": self.state == PipelineState.RUNNING
        }
    
    def _reset_state(self) -> None:
        """Réinitialise l'état du pipeline."""
        self.state = PipelineState.IDLE
        self.current_stage = PipelineStage.INITIALIZATION
        self.progress = 0.0
        self.error_message = ""
        self.cancel_requested = False
        self.intermediate_results.clear()
    
    def _update_progress(self, stage: PipelineStage, progress: float, message: str) -> None:
        """
        Met à jour la progression et notifie les callbacks.
        
        Args:
            stage: Étape actuelle du pipeline
            progress: Pourcentage de progression (0-100)
            message: Message descriptif
        """
        # Vérifier si l'annulation a été demandée
        if self.cancel_requested:
            raise ProcessingError("Pipeline execution was cancelled")
        
        self.current_stage = stage
        self.progress = progress
        
        # Créer l'info de progression
        progress_info = ProgressInfo(
            stage=stage,
            progress=progress,
            message=message,
            timestamp=time.time()
        )
        
        # Notifier tous les callbacks
        for callback in self.progress_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
        
        self.logger.info(f"[{progress:.1f}%] {stage.value}: {message}")
    
    def _validate_input(self, video_path: str) -> None:
        """Valide le fichier vidéo d'entrée."""
        if not self.file_manager.validate_video_file(video_path):
            raise ValidationError(f"Invalid video file: {video_path}")
        
        self.logger.info(f"Video file validated: {video_path}")
    
    def _extract_audio(self, video_path: str) -> str:
        """Extrait l'audio de la vidéo."""
        try:
            audio_path = self.video_processor.extract_audio(video_path)
            
            self.intermediate_results["audio_path"] = audio_path
            return audio_path
            
        except Exception as e:
            raise ProcessingError(f"Audio extraction failed: {e}")
    
    def _analyze_audio(self, audio_path: str) -> tuple:
        """Analyse l'audio pour détecter la parole et les locuteurs."""
        try:
            # Détection d'activité vocale
            speech_intervals = self.audio_processor.detect_voice_activity(audio_path)
            
            # Diarisation des locuteurs
            speaker_segments = self.audio_processor.perform_speaker_diarization(audio_path)
            
            self.intermediate_results["speech_intervals"] = speech_intervals
            self.intermediate_results["speaker_segments"] = speaker_segments
            
            return speech_intervals, speaker_segments
            
        except Exception as e:
            raise ProcessingError(f"Audio analysis failed: {e}")
    
    def _separate_audio_sources(self, audio_path: str):
        """Sépare les sources audio."""
        try:
            result = self.audio_processor.separate_sources(
                audio_path, 
                enable_separation=True
            )
            
            self.intermediate_results["source_separation"] = result
            return result
            
        except Exception as e:
            raise ProcessingError(f"Source separation failed: {e}")
    
    def _transcribe_audio(self, audio_path: str):
        """Transcrit l'audio avec horodatages."""
        try:
            # Détecter si un modèle NeMo est configuré
            if self.config.asr_model.startswith("nemo-"):
                self.logger.info(f"Using NeMo transcription with model: {self.config.asr_model}")
                result = self.ai_model_manager.transcribe_audio_with_nemo(
                    audio_path,
                    model_name=self.config.asr_model,
                    language=self.config.target_language
                )
            else:
                self.logger.info(f"Using Whisper transcription with model: {self.config.asr_model}")
                result = self.ai_model_manager.transcribe_audio(
                    audio_path,
                    model_name=self.config.asr_model,
                    language=self.config.target_language,
                    word_timestamps=True
                )
            
            self.intermediate_results["transcription"] = result
            return result
            
        except Exception as e:
            raise ProcessingError(f"Audio transcription failed: {e}")
    
    def _extract_subtitles(self, video_path: str, speech_intervals: List) -> List:
        """Extrait les sous-titres de la vidéo."""
        try:
            # Extraire les frames pendant les intervalles de parole
            frames = self.video_processor.extract_frames_during_speech(
                video_path, 
                speech_intervals,
                frame_rate=1.0  # 1 frame par seconde
            )
            
            # Extraire le texte des frames
            ocr_results = self.ai_model_manager.extract_text_from_frames(
                frames,
                model_name=self.config.ocr_model,
                confidence_threshold=0.7
            )
            
            self.intermediate_results["ocr_results"] = ocr_results
            return ocr_results
            
        except Exception as e:
            raise ProcessingError(f"Subtitle extraction failed: {e}")
    
    def _synchronize_content(self, transcription, ocr_results, speaker_segments):
        """Synchronise la transcription avec les sous-titres et locuteurs."""
        try:
            result = self.sync_processor.synchronize_transcription_and_ocr(
                transcription,
                ocr_results,
                speaker_segments
            )
            
            self.intermediate_results["synchronized_segments"] = result
            return result
            
        except Exception as e:
            raise ProcessingError(f"Content synchronization failed: {e}")
    
    def _segment_by_speaker(self, audio_path: str, synchronized_segments) -> Dict:
        """Segmente l'audio par locuteur."""
        try:
            result = self.speaker_segmentation.segment_audio_by_speaker(
                audio_path,
                synchronized_segments
            )
            
            self.intermediate_results["speaker_audio_segments"] = result
            return result
            
        except Exception as e:
            raise ProcessingError(f"Speaker segmentation failed: {e}")
    
    def _normalize_audio_segments(self, speaker_segments: Dict) -> Dict:
        """Normalise les segments audio pour le clonage."""
        try:
            normalized_segments = {}
            
            for speaker_id, segments in speaker_segments.items():
                normalized_segments[speaker_id] = []
                
                for segment in segments:
                    normalized_path = self.audio_normalizer.normalize_audio(
                        segment["audio_path"],
                        target_lufs=-23.0,
                        normalize_volume=True
                    )
                    
                    normalized_segment = segment.copy()
                    normalized_segment["normalized_audio_path"] = normalized_path
                    normalized_segments[speaker_id].append(normalized_segment)
            
            self.intermediate_results["normalized_segments"] = normalized_segments
            return normalized_segments
            
        except Exception as e:
            raise ProcessingError(f"Audio normalization failed: {e}")
    
    def _clone_voices(self, normalized_segments: Dict, synchronized_segments) -> Dict:
        """Clone les voix pour chaque locuteur."""
        try:
            cloned_segments = {}
            
            for speaker_id, segments in normalized_segments.items():
                cloned_segments[speaker_id] = []
                
                # Utiliser le premier segment comme référence vocale
                if segments:
                    reference_audio = segments[0]["normalized_audio_path"]
                    
                    # Cloner chaque segment
                    for segment in segments:
                        # Trouver le texte correspondant dans les segments synchronisés
                        text_to_speak = self._find_text_for_segment(
                            segment, synchronized_segments, speaker_id
                        )
                        
                        if text_to_speak:
                            cloned_audio_path = self.voice_cloner.clone_voice(
                                reference_audio=reference_audio,
                                text=text_to_speak,
                                output_path=None  # Auto-généré
                            )
                            
                            cloned_segment = segment.copy()
                            cloned_segment["cloned_audio_path"] = cloned_audio_path
                            cloned_segment["text"] = text_to_speak
                            cloned_segments[speaker_id].append(cloned_segment)
            
            self.intermediate_results["cloned_segments"] = cloned_segments
            return cloned_segments
            
        except Exception as e:
            raise ProcessingError(f"Voice cloning failed: {e}")
    
    def _find_text_for_segment(self, segment: Dict, synchronized_segments, speaker_id: str) -> str:
        """Trouve le texte correspondant à un segment audio."""
        # Logique simplifiée - à améliorer selon les besoins
        start_time = segment.get("start_time", 0.0)
        end_time = segment.get("end_time", 0.0)
        
        # Chercher dans les segments synchronisés
        for sync_segment in synchronized_segments:
            if (sync_segment.speaker_id == speaker_id and
                abs(sync_segment.start_time - start_time) < 0.5):  # Tolérance de 0.5s
                return sync_segment.final_text or sync_segment.original_text
        
        return ""  # Texte par défaut si non trouvé
    
    def _mix_final_audio(self, cloned_segments: Dict, source_separation_result) -> str:
        """Mixe l'audio final avec les voix clonées."""
        try:
            # Collecter toutes les pistes audio clonées
            voice_tracks = []
            for speaker_segments in cloned_segments.values():
                for segment in speaker_segments:
                    if "cloned_audio_path" in segment:
                        voice_tracks.append(segment["cloned_audio_path"])
            
            # Déterminer les pistes de fond
            music_track = ""
            effects_track = ""
            
            if source_separation_result:
                music_track = source_separation_result.music_path
                effects_track = source_separation_result.effects_path
            
            # Mixer l'audio final
            final_audio_path = self.audio_mixer.mix_audio_tracks(
                voice_track=voice_tracks[0] if voice_tracks else "",
                music_track=music_track,
                effects_track=effects_track,
                output_path=None,  # Auto-généré
                voice_volume=1.0,
                music_volume=0.3,
                effects_volume=0.5
            )
            
            self.intermediate_results["final_audio_path"] = final_audio_path.output_path
            return final_audio_path.output_path
            
        except Exception as e:
            raise ProcessingError(f"Audio mixing failed: {e}")
    
    def _assemble_final_video(self, original_video_path: str, final_audio_path: str) -> str:
        """Assemble la vidéo finale avec le nouvel audio."""
        try:
            output_path = self.video_processor.merge_audio_video(
                video_path=original_video_path,
                audio_path=final_audio_path,
                output_path=None  # Auto-généré
            )
            
            self.intermediate_results["final_video_path"] = output_path
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Video assembly failed: {e}")
    
    def cleanup(self) -> None:
        """Nettoie les ressources et fichiers temporaires."""
        try:
            # Nettoyer les modèles IA
            self.ai_model_manager.cleanup_all()
            
            # Nettoyer les fichiers temporaires
            self.temp_storage.cleanup_all()
            
            self.logger.info("Pipeline cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    def __del__(self):
        """Destructeur pour nettoyer automatiquement."""
        try:
            self.cleanup()
        except:
            pass  # Ignorer les erreurs lors de la destruction