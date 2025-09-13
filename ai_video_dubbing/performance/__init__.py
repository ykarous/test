"""
Module de performance et optimisation pour NeMo
"""

from .async_controller import AsyncNeMoController

# Import conditionnel des autres modules (seront créés dans les prochaines tâches)
try:
    from .model_manager import LightweightModelManager
except ImportError:
    LightweightModelManager = None

try:
    from .download_manager import IntelligentDownloadManager
except ImportError:
    IntelligentDownloadManager = None

try:
    from .fallback_system import IntelligentFallbackSystem
except ImportError:
    IntelligentFallbackSystem = None

try:
    from .progress_interface import RealTimeProgressInterface
except ImportError:
    RealTimeProgressInterface = None

__all__ = [
    'AsyncNeMoController',
    'LightweightModelManager', 
    'IntelligentDownloadManager',
    'IntelligentFallbackSystem',
    'RealTimeProgressInterface'
]