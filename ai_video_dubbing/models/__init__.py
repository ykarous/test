"""
Modèles de données pour l'application de doublage vidéo par IA.
"""

from .data_models import (
    PipelineConfig,
    ProcessingResults,
    DialogueSegment,
    Interval,
    Frame,
    SpeakerSegments,
    SourceSeparationResult,
    TranscriptionResult,
    OCRResult,
    AlignmentResult,
    Subtitle,
    ProgressInfo,
    ModelType,
    ValidationError,
    ProcessingError,
    ResourceError
)

__all__ = [
    "PipelineConfig",
    "ProcessingResults", 
    "DialogueSegment",
    "Interval",
    "Frame",
    "SpeakerSegments",
    "SourceSeparationResult",
    "TranscriptionResult",
    "OCRResult",
    "AlignmentResult",
    "Subtitle",
    "ProgressInfo",
    "ModelType",
    "ValidationError",
    "ProcessingError",
    "ResourceError"
]