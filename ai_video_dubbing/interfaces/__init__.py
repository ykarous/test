"""
Interfaces de base pour l'application de doublage vidéo par IA.
"""

from .base_interfaces import (
    IVideoProcessor,
    IAudioProcessor,
    IAIModelManager,
    IPipelineOrchestrator,
    IFileManager,
    IErrorHandler
)

__all__ = [
    "IVideoProcessor",
    "IAudioProcessor", 
    "IAIModelManager",
    "IPipelineOrchestrator",
    "IFileManager",
    "IErrorHandler"
]