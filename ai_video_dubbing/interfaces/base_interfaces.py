"""
Interfaces de base pour tous les composants principaux.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional, Any
from ..models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment, Interval,
    Frame, SpeakerSegments, SourceSeparationResult, TranscriptionResult,
    OCRResult, AlignmentResult, Subtitle, ProgressInfo, ModelType,
    ValidationError, ProcessingError, ResourceError
)


class IVideoProcessor(ABC):
    """Interface pour le processeur vidéo."""
    
    @abstractmethod
    def extract_audio(self, video_path: str) -> str:
        """Extrait l'audio d'un fichier vidéo."""
        pass
    
    @abstractmethod
    def extract_frames_during_speech(self, video_path: str, speech_intervals: List[Interval]) -> List[Frame]:
        """Extrait les images pendant les intervalles de parole."""
        pass
    
    @abstractmethod
    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str) -> None:
        """Fusionne l'audio et la vidéo."""
        pass


class IAudioProcessor(ABC):
    """Interface pour le processeur audio."""
    
    @abstractmethod
    def detect_voice_activity(self, audio_path: str) -> List[Interval]:
        """Détecte l'activité vocale."""
        pass
    
    @abstractmethod
    def perform_speaker_diarization(self, audio_path: str) -> SpeakerSegments:
        """Effectue la diarisation des locuteurs."""
        pass
    
    @abstractmethod
    def separate_sources(self, audio_path: str) -> SourceSeparationResult:
        """Sépare les sources audio."""
        pass
    
    @abstractmethod
    def segment_by_speaker(self, audio_path: str, diarization: SpeakerSegments) -> Dict[str, str]:
        """Segmente l'audio par locuteur."""
        pass
    
    @abstractmethod
    def normalize_audio(self, audio_path: str) -> str:
        """Normalise l'audio."""
        pass


class IAIModelManager(ABC):
    """Interface pour le gestionnaire de modèles IA."""
    
    @abstractmethod
    def load_model(self, model_type: ModelType, model_name: str) -> None:
        """Charge un modèle IA."""
        pass
    
    @abstractmethod
    def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """Transcrit l'audio."""
        pass
    
    @abstractmethod
    def extract_text_from_frames(self, frames: List[Frame]) -> List[OCRResult]:
        """Extrait le texte des images."""
        pass
    
    @abstractmethod
    def clone_voice(self, reference_audio: str, text: str) -> str:
        """Clone une voix."""
        pass
    
    @abstractmethod
    def unload_model(self, model_type: ModelType) -> None:
        """Décharge un modèle."""
        pass


class IPipelineOrchestrator(ABC):
    """Interface pour l'orchestrateur de pipeline."""
    
    @abstractmethod
    def __init__(self, config: PipelineConfig):
        """Initialise l'orchestrateur."""
        pass
    
    @abstractmethod
    def execute_pipeline(self, video_path: str) -> ProcessingResults:
        """Exécute le pipeline complet."""
        pass
    
    @abstractmethod
    def register_progress_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """Enregistre un callback de progression."""
        pass
    
    @abstractmethod
    def cancel_processing(self) -> None:
        """Annule le traitement."""
        pass


class IFileManager(ABC):
    """Interface pour le gestionnaire de fichiers."""
    
    @abstractmethod
    def validate_video_file(self, file_path: str) -> bool:
        """Valide un fichier vidéo."""
        pass
    
    @abstractmethod
    def create_temp_directory(self) -> str:
        """Crée un répertoire temporaire."""
        pass
    
    @abstractmethod
    def cleanup_temp_files(self) -> None:
        """Nettoie les fichiers temporaires."""
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtient les informations d'un fichier."""
        pass


class IErrorHandler(ABC):
    """Interface pour le gestionnaire d'erreurs."""
    
    @abstractmethod
    def handle_validation_error(self, error: ValidationError) -> None:
        """Gère les erreurs de validation."""
        pass
    
    @abstractmethod
    def handle_processing_error(self, error: ProcessingError) -> bool:
        """Gère les erreurs de traitement. Retourne True si récupération possible."""
        pass
    
    @abstractmethod
    def handle_resource_error(self, error: ResourceError) -> None:
        """Gère les erreurs de ressources."""
        pass
    
    @abstractmethod
    def suggest_fallback_options(self, error: Any) -> List[str]:
        """Suggère des options de fallback."""
        pass