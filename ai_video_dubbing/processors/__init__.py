"""
Processeurs pour le traitement vidéo et audio.
"""

# Import conditionnel pour éviter les erreurs de dépendances manquantes
try:
    from .video_processor import VideoProcessor
    _VIDEO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: VideoProcessor not available: {e}")
    VideoProcessor = None
    _VIDEO_PROCESSOR_AVAILABLE = False

try:
    from .audio_processor import AudioProcessor
    _AUDIO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AudioProcessor not available: {e}")
    AudioProcessor = None
    _AUDIO_PROCESSOR_AVAILABLE = False

try:
    from .ai_model_manager import AIModelManager
    _AI_MODEL_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AIModelManager not available: {e}")
    AIModelManager = None
    _AI_MODEL_MANAGER_AVAILABLE = False

try:
    from .sync_processor import SyncProcessor
    _SYNC_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SyncProcessor not available: {e}")
    SyncProcessor = None
    _SYNC_PROCESSOR_AVAILABLE = False

try:
    from .speaker_segmentation import SpeakerSegmentationProcessor
    _SPEAKER_SEGMENTATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SpeakerSegmentationProcessor not available: {e}")
    SpeakerSegmentationProcessor = None
    _SPEAKER_SEGMENTATION_AVAILABLE = False

try:
    from .audio_normalizer import AudioNormalizer
    _AUDIO_NORMALIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AudioNormalizer not available: {e}")
    AudioNormalizer = None
    _AUDIO_NORMALIZER_AVAILABLE = False

try:
    from .voice_cloner import VoiceCloner
    _VOICE_CLONER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: VoiceCloner not available: {e}")
    VoiceCloner = None
    _VOICE_CLONER_AVAILABLE = False

__all__ = [
    "VideoProcessor",
    "AudioProcessor",
    "AIModelManager",
    "SyncProcessor",
    "SpeakerSegmentationProcessor",
    "AudioNormalizer",
    "VoiceCloner"
]