#!/usr/bin/env python3
"""
Utilitaires média utilisant FFmpeg via le gestionnaire FFmpeg.
"""
import os
import json
import logging
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path

from .ffmpeg_manager import FFmpegManager

class MediaUtils:
    """Utilitaires pour le traitement média avec FFmpeg."""
    
    def __init__(self, ffmpeg_manager: Optional[FFmpegManager] = None):
        """Initialise les utilitaires média."""
        self.logger = logging.getLogger(__name__)
        self.ffmpeg_manager = ffmpeg_manager or FFmpegManager()
        
        if not self.ffmpeg_manager.is_available():
            self.logger.warning("FFmpeg not available - some features will be limited")
    
    def extract_audio(self, video_path: str, output_path: str, 
                     format: str = "wav", sample_rate: int = 44100) -> bool:
        """Extrait l'audio d'une vidéo."""
        try:
            if not self.ffmpeg_manager.is_available():
                raise RuntimeError("FFmpeg not available")
            
            args = [
                '-i', video_path,
                '-vn',  # Pas de vidéo
                '-acodec', 'pcm_s16le' if format == 'wav' else 'libmp3lame',
                '-ar', str(sample_rate),
                '-y',  # Écraser le fichier de sortie
                output_path
            ]
            
            result = self.ffmpeg_manager.run_ffmpeg_command(
                args, capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info(f"Audio extracted successfully: {output_path}")
                return True
            else:
                self.logger.error(f"Audio extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error extracting audio: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Obtient les informations d'une vidéo."""
        try:
            if not self.ffmpeg_manager.is_available():
                raise RuntimeError("FFmpeg not available")
            
            media_info = self.ffmpeg_manager.get_media_info(video_path)
            
            # Extraire les informations utiles
            info = {
                'duration': 0.0,
                'width': 0,
                'height': 0,
                'fps': 0.0,
                'video_codec': 'unknown',
                'audio_codec': 'unknown',
                'audio_sample_rate': 0,
                'file_size': 0
            }
            
            # Format général
            if 'format' in media_info:
                format_info = media_info['format']
                info['duration'] = float(format_info.get('duration', 0))
                info['file_size'] = int(format_info.get('size', 0))
            
            # Streams
            if 'streams' in media_info:
                for stream in media_info['streams']:
                    if stream.get('codec_type') == 'video':
                        info['width'] = stream.get('width', 0)
                        info['height'] = stream.get('height', 0)
                        info['video_codec'] = stream.get('codec_name', 'unknown')
                        
                        # FPS
                        fps_str = stream.get('r_frame_rate', '0/1')
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            if int(den) > 0:
                                info['fps'] = float(num) / float(den)
                                
                    elif stream.get('codec_type') == 'audio':
                        info['audio_codec'] = stream.get('codec_name', 'unknown')
                        info['audio_sample_rate'] = int(stream.get('sample_rate', 0))
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return {}
    
    def extract_frames(self, video_path: str, output_dir: str, 
                      fps: float = 1.0, format: str = "jpg") -> List[str]:
        """Extrait des frames d'une vidéo."""
        try:
            if not self.ffmpeg_manager.is_available():
                raise RuntimeError("FFmpeg not available")
            
            os.makedirs(output_dir, exist_ok=True)
            output_pattern = os.path.join(output_dir, f"frame_%06d.{format}")
            
            args = [
                '-i', video_path,
                '-vf', f'fps={fps}',
                '-y',
                output_pattern
            ]
            
            result = self.ffmpeg_manager.run_ffmpeg_command(
                args, capture_output=True, text=True, timeout=600
            )
            
            if result.returncode == 0:
                # Lister les fichiers créés
                frame_files = []
                for file in os.listdir(output_dir):
                    if file.startswith('frame_') and file.endswith(f'.{format}'):
                        frame_files.append(os.path.join(output_dir, file))
                frame_files.sort()
                
                self.logger.info(f"Extracted {len(frame_files)} frames")
                return frame_files
            else:
                self.logger.error(f"Frame extraction failed: {result.stderr}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error extracting frames: {e}")
            return []
    
    def convert_audio_format(self, input_path: str, output_path: str,
                           target_format: str = "wav", sample_rate: int = 44100) -> bool:
        """Convertit un fichier audio vers un autre format."""
        try:
            if not self.ffmpeg_manager.is_available():
                raise RuntimeError("FFmpeg not available")
            
            args = [
                '-i', input_path,
                '-ar', str(sample_rate),
                '-y',
                output_path
            ]
            
            # Ajouter le codec selon le format
            if target_format.lower() == 'wav':
                args.insert(-2, '-acodec')
                args.insert(-2, 'pcm_s16le')
            elif target_format.lower() == 'mp3':
                args.insert(-2, '-acodec')
                args.insert(-2, 'libmp3lame')
            
            result = self.ffmpeg_manager.run_ffmpeg_command(
                args, capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info(f"Audio converted successfully: {output_path}")
                return True
            else:
                self.logger.error(f"Audio conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error converting audio: {e}")
            return False
    
    def merge_audio_video(self, video_path: str, audio_path: str, 
                         output_path: str) -> bool:
        """Fusionne un fichier audio avec une vidéo."""
        try:
            if not self.ffmpeg_manager.is_available():
                raise RuntimeError("FFmpeg not available")
            
            args = [
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copier la vidéo sans réencodage
                '-c:a', 'aac',   # Encoder l'audio en AAC
                '-map', '0:v:0', # Première piste vidéo du premier fichier
                '-map', '1:a:0', # Première piste audio du second fichier
                '-y',
                output_path
            ]
            
            result = self.ffmpeg_manager.run_ffmpeg_command(
                args, capture_output=True, text=True, timeout=600
            )
            
            if result.returncode == 0:
                self.logger.info(f"Audio/video merged successfully: {output_path}")
                return True
            else:
                self.logger.error(f"Audio/video merge failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error merging audio/video: {e}")
            return False
    
    def is_available(self) -> bool:
        """Vérifie si les utilitaires média sont disponibles."""
        return self.ffmpeg_manager.is_available()
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Retourne les formats supportés."""
        if not self.ffmpeg_manager.is_available():
            return {'video': [], 'audio': []}
        
        return {
            'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'],
            'audio': ['wav', 'mp3', 'aac', 'flac', 'ogg', 'm4a']
        }