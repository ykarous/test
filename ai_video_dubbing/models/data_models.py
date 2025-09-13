"""
Modèles de données pour l'application de doublage vidéo par IA.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import numpy as np


class PipelineStage(Enum):
    """Étapes du pipeline de traitement."""
    INITIALIZATION = "initialization"
    VIDEO_PROCESSING = "video_processing"
    AUDIO_ANALYSIS = "audio_analysis"
    SOURCE_SEPARATION = "source_separation"
    TRANSCRIPTION = "transcription"
    OCR_EXTRACTION = "ocr_extraction"
    SYNCHRONIZATION = "synchronization"
    SPEAKER_SEGMENTATION = "speaker_segmentation"
    AUDIO_NORMALIZATION = "audio_normalization"
    VOICE_CLONING = "voice_cloning"
    AUDIO_MIXING = "audio_mixing"
    VIDEO_ASSEMBLY = "video_assembly"
    COMPLETED = "completed"


@dataclass
class ProgressInfo:
    """Informations de progression du pipeline."""
    stage: PipelineStage
    progress: float  # 0-100
    message: str
    timestamp: float


@dataclass
class PipelineConfig:
    """Configuration du pipeline de traitement."""
    enable_source_separation: bool = False
    enable_ocr: bool = True
    asr_model: str = "whisper-base"
    ocr_model: str = "paddleocr"
    voice_cloning_model: str = "tortoise-tts"
    target_language: str = "fr"
    output_codec: str = "h264"
    output_bitrate: str = "5M"
    temp_directory: str = "./temp"
    max_memory_usage: float = 0.8  # Pourcentage de RAM maximale à utiliser
    
    def is_valid(self) -> bool:
        """Valider la configuration."""
        # Vérifier que le bitrate est valide
        if not self.output_bitrate.endswith(('K', 'M', 'G')):
            return False
        
        # Vérifier que les modèles sont spécifiés
        if not all([self.asr_model, self.ocr_model, self.voice_cloning_model]):
            return False
            
        return True


@dataclass
class ProcessingResults:
    """Résultats du traitement complet."""
    output_video_path: str
    processing_time: float
    transcription_result: Optional[Any] = None
    speaker_segments: Optional[Any] = None
    ocr_results: List[Any] = field(default_factory=list)
    source_separation_result: Optional[Any] = None
    success: bool = True
    error_message: str = ""
    speakers_detected: int = 0
    dialogue_segments: int = 0
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    intermediate_files: List[str] = field(default_factory=list)
    
    @property
    def average_segment_duration(self) -> float:
        """Durée moyenne des segments."""
        if self.dialogue_segments == 0:
            return 0.0
        return self.processing_time / self.dialogue_segments
    
    @property
    def speakers_per_minute(self) -> float:
        """Nombre de locuteurs par minute."""
        if self.processing_time == 0:
            return 0.0
        return self.speakers_detected / (self.processing_time / 60)
    
    @property
    def overall_quality_score(self) -> float:
        """Score de qualité global."""
        if not self.quality_metrics:
            return 0.0
        return sum(self.quality_metrics.values()) / len(self.quality_metrics)


@dataclass
class DialogueSegment:
    """Segment de dialogue avec métadonnées."""
    speaker_id: str
    start_time: float
    end_time: float
    original_text: str
    audio_path: str
    confidence_score: float
    
    @property
    def duration(self) -> float:
        """Durée du segment."""
        return self.end_time - self.start_time
    
    @property
    def word_count(self) -> int:
        """Nombre de mots dans le segment."""
        return len(self.original_text.split())
    
    def is_valid_timing(self) -> bool:
        """Vérifier que les timings sont valides."""
        return self.start_time >= 0 and self.end_time > self.start_time
    
    def is_high_confidence(self) -> bool:
        """Vérifier si le segment a une confiance élevée."""
        return self.confidence_score > 0.8


@dataclass
class Interval:
    """Intervalle de temps avec début et fin."""
    start: float
    end: float
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Frame:
    """Image extraite de la vidéo avec métadonnées."""
    timestamp: float
    image_data: np.ndarray
    width: int
    height: int


@dataclass
class SpeakerSegments:
    """Résultats de la diarisation des locuteurs."""
    segments: List[DialogueSegment]
    speaker_count: int
    confidence_scores: Dict[str, float]


@dataclass
class SourceSeparationResult:
    """Résultats de la séparation de source audio."""
    vocals_path: str
    music_path: str
    effects_path: str
    separation_quality: float
    original_path: str = ""
    processing_time: float = 0.0


@dataclass
class WordTimestamp:
    """Horodatage d'un mot individuel."""
    word: str
    start: float
    end: float
    confidence: float


@dataclass
class TranscriptionSegment:
    """Segment de transcription avec horodatages."""
    text: str
    start: float
    end: float
    confidence: float
    word_timestamps: List[WordTimestamp] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    """Résultats de la transcription ASR."""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    confidence: float
    processing_time: float = 0.0
    model_name: str = ""
    word_count: int = 0
    
    @property
    def total_duration(self) -> float:
        """Durée totale de la transcription."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end - self.segments[0].start
    
    @property
    def segment_count(self) -> int:
        """Nombre de segments."""
        return len(self.segments)
    
    @property
    def words_per_minute(self) -> float:
        """Mots par minute."""
        if self.total_duration == 0:
            return 0.0
        return (self.word_count or len(self.text.split())) / (self.total_duration / 60)
    
    def is_reliable(self) -> bool:
        """Vérifier si la transcription est fiable."""
        return self.confidence > 0.8


@dataclass
class OCRResult:
    """Résultats de l'extraction OCR."""
    text: str
    timestamp: float
    confidence: float
    bounding_box: Optional[Dict[str, int]] = None


@dataclass
class AlignmentResult:
    """Résultats de l'alignement OCR/ASR."""
    aligned_segments: List[DialogueSegment]
    alignment_confidence: float
    corrections_made: int


@dataclass
class Subtitle:
    """Sous-titre avec horodatage."""
    text: str
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None



class ModelType(Enum):
    """Types de modèles IA supportés."""
    ASR = "asr"
    OCR = "ocr"
    DIARIZATION = "diarization"
    VOICE_CLONING = "voice_cloning"
    SOURCE_SEPARATION = "source_separation"
    NEMO_ASR = "nemo_asr"
    NEMO_OCR = "nemo_ocr"
    LM_STUDIO_ASR = "lm_studio_asr"
    LM_STUDIO_OCR = "lm_studio_ocr"


@dataclass
class VideoMetadata:
    """Métadonnées d'un fichier vidéo."""
    duration: float
    fps: float
    resolution: tuple  # (width, height)
    audio_channels: int
    audio_sample_rate: int
    file_size: int  # en bytes
    
    @property
    def aspect_ratio(self) -> float:
        """Ratio d'aspect de la vidéo."""
        return self.resolution[0] / self.resolution[1]
    
    @property
    def total_frames(self) -> int:
        """Nombre total d'images."""
        return int(self.duration * self.fps)
    
    @property
    def file_size_mb(self) -> int:
        """Taille du fichier en MB."""
        return self.file_size // (1024 * 1024)
    
    def is_hd_quality(self) -> bool:
        """Vérifier si c'est de la qualité HD."""
        return self.resolution[1] >= 720


@dataclass
class AudioSegment:
    """Segment audio avec données et métadonnées."""
    start_time: float
    end_time: float
    audio_data: np.ndarray
    sample_rate: int
    speaker_id: str
    
    @property
    def duration(self) -> float:
        """Durée du segment."""
        return self.end_time - self.start_time
    
    @property
    def sample_count(self) -> int:
        """Nombre d'échantillons."""
        return len(self.audio_data)
    
    @property
    def rms_energy(self) -> float:
        """Énergie RMS du signal."""
        return np.sqrt(np.mean(self.audio_data ** 2))
    
    @property
    def peak_amplitude(self) -> float:
        """Amplitude maximale."""
        return np.max(np.abs(self.audio_data))


# Exceptions personnalisées
class ValidationError(Exception):
    """Erreur de validation des données d'entrée."""
    pass


class ProcessingError(Exception):
    """Erreur lors du traitement."""
    pass


class ResourceError(Exception):
    """Erreur liée aux ressources système."""
    pass