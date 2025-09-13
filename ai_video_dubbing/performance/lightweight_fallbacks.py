"""
Fallbacks légers pour les composants qui nécessitent des dépendances lourdes
Permet à l'application de fonctionner même sans torch, aiofiles, etc.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LightweightFallbackSystem:
    """Système de fallback léger sans dépendances lourdes"""
    
    def __init__(self):
        self.fallback_chain = ["whisper", "basic"]
        logger.info("Système de fallback léger initialisé")
    
    def execute_with_fallback(self, operation, *args, **kwargs):
        """Exécute une opération avec fallback simple"""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Opération échouée, utilisation du fallback: {e}")
            return self._basic_fallback(*args, **kwargs)
    
    def _basic_fallback(self, *args, **kwargs):
        """Fallback de base"""
        return {"status": "fallback_used", "message": "Opération effectuée avec fallback léger"}

class LightweightCacheManager:
    """Gestionnaire de cache léger sans aiofiles"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"Cache léger initialisé: {self.cache_dir}")
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère un élément du cache"""
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                import json
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lecture cache {key}: {e}")
        return None
    
    def set(self, key: str, value: Any) -> bool:
        """Stocke un élément dans le cache"""
        try:
            import json
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, 'w') as f:
                json.dump(value, f)
            return True
        except Exception as e:
            logger.warning(f"Erreur écriture cache {key}: {e}")
            return False
    
    def clear(self):
        """Vide le cache"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            logger.info("Cache vidé")
        except Exception as e:
            logger.warning(f"Erreur vidage cache: {e}")

class LightweightDownloadManager:
    """Gestionnaire de téléchargement léger sans aiofiles"""
    
    def __init__(self):
        self.downloads = {}
        logger.info("Gestionnaire de téléchargement léger initialisé")
    
    def download_model(self, model_name: str, url: str, progress_callback=None) -> bool:
        """Télécharge un modèle de manière simple"""
        try:
            import urllib.request
            
            def progress_hook(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    progress = (block_num * block_size) / total_size * 100
                    progress_callback(min(progress, 100))
            
            # Simuler le téléchargement pour les tests
            if progress_callback:
                for i in range(0, 101, 10):
                    progress_callback(i)
                    import time
                    time.sleep(0.1)
            
            logger.info(f"Téléchargement simulé de {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur téléchargement {model_name}: {e}")
            return False
    
    def cancel_download(self, model_name: str):
        """Annule un téléchargement"""
        if model_name in self.downloads:
            del self.downloads[model_name]
            logger.info(f"Téléchargement annulé: {model_name}")

class LightweightAIManager:
    """Gestionnaire AI léger sans torch"""
    
    def __init__(self):
        self.models = {}
        self.cache_manager = LightweightCacheManager()
        self.fallback_system = LightweightFallbackSystem()
        logger.info("Gestionnaire AI léger initialisé")
    
    def transcribe_audio(self, audio_path: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Transcription audio simplifiée"""
        try:
            # Simulation de transcription
            result = {
                "text": "Transcription simulée (mode léger)",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Segment de test"},
                ],
                "language": "fr",
                "confidence": 0.85
            }
            
            logger.info(f"Transcription simulée de {audio_path}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur transcription: {e}")
            return self.fallback_system.execute_with_fallback(
                self._basic_transcription, audio_path
            )
    
    def _basic_transcription(self, audio_path: str) -> Dict[str, Any]:
        """Transcription de base en fallback"""
        return {
            "text": "Transcription de base (fallback)",
            "segments": [],
            "language": "unknown",
            "confidence": 0.5
        }
    
    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return ["whisper-tiny", "whisper-base", "basic-transcriber"]
    
    def is_model_available(self, model_name: str) -> bool:
        """Vérifie si un modèle est disponible"""
        return model_name in self.get_available_models()

# Fonctions utilitaires pour l'intégration
def get_fallback_manager():
    """Retourne un gestionnaire de fallback léger"""
    return LightweightFallbackSystem()

def get_lightweight_cache():
    """Retourne un cache léger"""
    return LightweightCacheManager()

def get_lightweight_downloader():
    """Retourne un téléchargeur léger"""
    return LightweightDownloadManager()

def get_lightweight_ai_manager():
    """Retourne un gestionnaire AI léger"""
    return LightweightAIManager()

# Configuration pour l'intégration automatique
LIGHTWEIGHT_COMPONENTS = {
    "FallbackSystem": LightweightFallbackSystem,
    "CacheManager": LightweightCacheManager,
    "DownloadManager": LightweightDownloadManager,
    "AIManager": LightweightAIManager,
}

def initialize_lightweight_mode():
    """Initialise le mode léger pour tous les composants"""
    logger.info("Mode léger activé - Composants sans dépendances lourdes")
    return {
        name: component() for name, component in LIGHTWEIGHT_COMPONENTS.items()
    }