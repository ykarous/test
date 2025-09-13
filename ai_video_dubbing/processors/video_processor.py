"""
Processeur vidéo pour l'application de doublage vidéo par IA.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import cv2
    import numpy as np
    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False
    cv2 = None
    np = None

from ..utils.ffmpeg_manager import FFmpegManager
from ..utils.media_utils import MediaUtils

from ..interfaces.base_interfaces import IVideoProcessor
from ..models.data_models import (
    Interval, Frame, ValidationError, ProcessingError
)


class VideoProcessor(IVideoProcessor):
    """Processeur vidéo utilisant FFmpeg pour l'extraction et la fusion."""
    
    def __init__(self, temp_storage=None, ffmpeg_manager=None):
        """
        Initialise le processeur vidéo.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
            ffmpeg_manager: Gestionnaire FFmpeg (optionnel)
        """
        self.temp_storage = temp_storage
        self.logger = logging.getLogger(__name__)
        
        # Initialiser le gestionnaire FFmpeg
        self.ffmpeg_manager = ffmpeg_manager or FFmpegManager()
        self.media_utils = MediaUtils(self.ffmpeg_manager)
        
        # Vérifier la disponibilité de FFmpeg (sans lever d'exception au démarrage)
        self._ffmpeg_available = self._check_ffmpeg_availability()
        
        # Vérifier la disponibilité d'OpenCV
        if not _OPENCV_AVAILABLE:
            self.logger.warning("OpenCV not available. Some features will be limited.")
    
    def _check_ffmpeg_availability(self) -> bool:
        """Vérifie que FFmpeg est disponible."""
        try:
            available = self.ffmpeg_manager.is_available()
            if not available:
                self.logger.warning(
                    "FFmpeg not available. Please configure FFmpeg in the application settings."
                )
            return available
        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg check timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking FFmpeg availability: {e}")
            return False
    
    def extract_audio(self, video_path: str) -> str:
        """
        Extrait l'audio d'un fichier vidéo.
        
        Args:
            video_path: Chemin vers le fichier vidéo
            
        Returns:
            Chemin vers le fichier audio extrait
        """
        if not self._ffmpeg_available:
            raise ProcessingError(
                "FFmpeg not available. Please configure FFmpeg in the application settings."
            )
            
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        
        # Déterminer le chemin de sortie
        if self.temp_storage:
            output_path = self.temp_storage.create_temp_file(
                suffix='.wav',
                prefix='extracted_audio_',
                category='audio'
            )
        else:
            output_path = str(video_path.parent / f"{video_path.stem}_audio.wav")
        
        # Commande FFmpeg pour extraction audio
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # Pas de vidéo
            '-acodec', 'pcm_s16le',  # Codec audio non compressé
            '-ar', '44100',  # Fréquence d'échantillonnage
            '-ac', '2',  # Stéréo
            '-y',  # Écraser le fichier de sortie
            output_path
        ]
        
        try:
            self.logger.info(f"Extracting audio from {video_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode != 0:
                error_msg = f"FFmpeg audio extraction failed: {result.stderr}"
                self.logger.error(error_msg)
                raise ProcessingError(error_msg)
            
            # Vérifier que le fichier a été créé
            if not Path(output_path).exists():
                raise ProcessingError("Audio file was not created")
            
            self.logger.info(f"Audio extracted successfully to {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise ProcessingError("Audio extraction timed out")
        except Exception as e:
            raise ProcessingError(f"Audio extraction failed: {e}")
    
    def extract_frames_during_speech(self, video_path: str, speech_intervals: List[Interval]) -> List[Frame]:
        """
        Extrait les images pendant les intervalles de parole.
        
        Args:
            video_path: Chemin vers le fichier vidéo
            speech_intervals: Intervalles de temps où il y a de la parole
            
        Returns:
            Liste des images extraites avec métadonnées
        """
        if not _OPENCV_AVAILABLE:
            raise ProcessingError("OpenCV is required for frame extraction. Please install opencv-python.")
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        
        if not speech_intervals:
            self.logger.warning("No speech intervals provided")
            return []
        
        frames = []
        
        try:
            # Ouvrir la vidéo avec OpenCV
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise ProcessingError(f"Could not open video file: {video_path}")
            
            # Obtenir les propriétés de la vidéo
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"Video properties: {fps} FPS, {total_frames} frames, {width}x{height}")
            
            # Extraire les images pour chaque intervalle de parole
            for interval in speech_intervals:
                interval_frames = self._extract_frames_for_interval(
                    cap, interval, fps, width, height
                )
                frames.extend(interval_frames)
            
            cap.release()
            
            self.logger.info(f"Extracted {len(frames)} frames during speech intervals")
            return frames
            
        except Exception as e:
            if 'cap' in locals():
                cap.release()
            raise ProcessingError(f"Frame extraction failed: {e}")
    
    def _extract_frames_for_interval(
        self, 
        cap, 
        interval: Interval, 
        fps: float,
        width: int,
        height: int
    ) -> List[Frame]:
        """Extrait les images pour un intervalle spécifique."""
        frames = []
        
        # Calculer les numéros de frames
        start_frame = int(interval.start * fps)
        end_frame = int(interval.end * fps)
        
        # Échantillonner les frames (max 1 frame par seconde pour l'OCR)
        sample_rate = max(1, int(fps))  # Une frame par seconde
        
        for frame_num in range(start_frame, end_frame, sample_rate):
            # Aller à la frame spécifique
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            ret, frame_data = cap.read()
            if not ret:
                continue
            
            # Calculer le timestamp
            timestamp = frame_num / fps
            
            # Créer l'objet Frame
            frame = Frame(
                timestamp=timestamp,
                image_data=frame_data,
                width=width,
                height=height
            )
            
            frames.append(frame)
        
        return frames
    
    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str) -> None:
        """
        Fusionne l'audio et la vidéo.
        
        Args:
            video_path: Chemin vers le fichier vidéo
            audio_path: Chemin vers le fichier audio
            output_path: Chemin de sortie
        """
        if not self._ffmpeg_available:
            raise ProcessingError(
                "FFmpeg not available. Please configure FFmpeg in the application settings."
            )
            
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_path = Path(output_path)
        
        # Vérifier que les fichiers d'entrée existent
        if not video_path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        # S'assurer que le répertoire de sortie existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Commande FFmpeg pour fusion
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',  # Copier le stream vidéo sans réencodage
            '-c:a', 'aac',   # Encoder l'audio en AAC
            '-map', '0:v:0',  # Prendre la vidéo du premier fichier
            '-map', '1:a:0',  # Prendre l'audio du deuxième fichier
            '-shortest',      # Arrêter quand le plus court se termine
            '-y',            # Écraser le fichier de sortie
            str(output_path)
        ]
        
        try:
            self.logger.info(f"Merging video {video_path} with audio {audio_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            
            if result.returncode != 0:
                error_msg = f"FFmpeg merge failed: {result.stderr}"
                self.logger.error(error_msg)
                raise ProcessingError(error_msg)
            
            # Vérifier que le fichier a été créé
            if not output_path.exists():
                raise ProcessingError("Merged video file was not created")
            
            self.logger.info(f"Video merged successfully to {output_path}")
            
        except subprocess.TimeoutExpired:
            raise ProcessingError("Video merge timed out")
        except Exception as e:
            raise ProcessingError(f"Video merge failed: {e}")
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse une chaîne de FPS au format 'num/den'."""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den)
            else:
                return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0