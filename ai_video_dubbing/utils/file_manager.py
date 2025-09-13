"""
Gestionnaire de fichiers pour l'application de doublage vidéo par IA.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import json
import logging

from ..interfaces.base_interfaces import IFileManager
from ..models.data_models import ValidationError


class FileManager(IFileManager):
    """Gestionnaire de fichiers avec validation et gestion des temporaires."""
    
    # Formats vidéo supportés
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mkv', '.avi'}
    
    # Extensions audio supportées pour l'extraction
    SUPPORTED_AUDIO_FORMATS = {'.wav', '.flac', '.mp3', '.aac'}
    
    def __init__(self, temp_base_dir: str = None):
        """
        Initialise le gestionnaire de fichiers.
        
        Args:
            temp_base_dir: Répertoire de base pour les fichiers temporaires
        """
        self.temp_base_dir = temp_base_dir or "./temp"
        self.temp_directories: List[str] = []
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire temporaire de base s'il n'existe pas
        Path(self.temp_base_dir).mkdir(parents=True, exist_ok=True)
    
    def validate_video_file(self, file_path: str) -> bool:
        """
        Valide un fichier vidéo.
        
        Args:
            file_path: Chemin vers le fichier vidéo
            
        Returns:
            True si le fichier est valide
            
        Raises:
            ValidationError: Si le fichier n'est pas valide
        """
        file_path = Path(file_path)
        
        # Vérifier que le fichier existe
        if not file_path.exists():
            raise ValidationError(f"Le fichier {file_path} n'existe pas")
        
        # Vérifier l'extension
        if file_path.suffix.lower() not in self.SUPPORTED_VIDEO_FORMATS:
            supported = ', '.join(self.SUPPORTED_VIDEO_FORMATS)
            raise ValidationError(
                f"Format de fichier non supporté: {file_path.suffix}. "
                f"Formats supportés: {supported}"
            )
        
        # Vérifier que le fichier n'est pas vide
        if file_path.stat().st_size == 0:
            raise ValidationError(f"Le fichier {file_path} est vide")
        
        # Vérifier l'intégrité avec FFprobe
        if not self._check_video_integrity(str(file_path)):
            raise ValidationError(f"Le fichier {file_path} est corrompu ou non lisible")
        
        return True
    
    def _check_video_integrity(self, file_path: str) -> bool:
        """
        Vérifie l'intégrité d'un fichier vidéo avec FFprobe.
        
        Args:
            file_path: Chemin vers le fichier vidéo
            
        Returns:
            True si le fichier est intègre
        """
        try:
            # Utiliser FFprobe pour vérifier le fichier
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.warning(f"FFprobe failed for {file_path}: {result.stderr}")
                return False
            
            # Vérifier que nous avons des informations valides
            try:
                data = json.loads(result.stdout)
                
                # Vérifier qu'il y a au moins un stream vidéo
                video_streams = [
                    s for s in data.get('streams', [])
                    if s.get('codec_type') == 'video'
                ]
                
                if not video_streams:
                    self.logger.warning(f"No video streams found in {file_path}")
                    return False
                
                # Vérifier qu'il y a des informations de format
                format_info = data.get('format', {})
                if not format_info.get('duration'):
                    self.logger.warning(f"No duration information in {file_path}")
                    return False
                
                return True
                
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON from FFprobe for {file_path}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"FFprobe timeout for {file_path}")
            return False
        except FileNotFoundError:
            self.logger.error("FFprobe not found. Please install FFmpeg.")
            # En cas d'absence de FFmpeg, on fait une validation basique
            return self._basic_file_validation(file_path)
        except Exception as e:
            self.logger.warning(f"Error checking video integrity: {e}")
            return False
    
    def _basic_file_validation(self, file_path: str) -> bool:
        """
        Validation basique sans FFprobe.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            True si la validation basique passe
        """
        try:
            # Vérifier les premiers octets pour des signatures de fichiers connus
            with open(file_path, 'rb') as f:
                header = f.read(12)
            
            # Signatures de fichiers vidéo courants
            video_signatures = [
                b'\x00\x00\x00\x18ftypmp4',  # MP4
                b'\x00\x00\x00\x20ftypmp4',  # MP4 variant
                b'\x1a\x45\xdf\xa3',         # MKV/WebM
                b'RIFF',                     # AVI (commence par RIFF)
            ]
            
            for signature in video_signatures:
                if header.startswith(signature) or signature in header:
                    return True
            
            # Vérification spéciale pour AVI
            if header.startswith(b'RIFF') and b'AVI ' in header:
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Basic validation failed: {e}")
            return False
    
    def create_temp_directory(self) -> str:
        """
        Crée un répertoire temporaire unique.
        
        Returns:
            Chemin vers le répertoire temporaire créé
        """
        temp_dir = tempfile.mkdtemp(dir=self.temp_base_dir)
        self.temp_directories.append(temp_dir)
        self.logger.info(f"Created temporary directory: {temp_dir}")
        return temp_dir
    
    def cleanup_temp_files(self) -> None:
        """Nettoie tous les fichiers temporaires créés."""
        for temp_dir in self.temp_directories:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_dir}: {e}")
        
        self.temp_directories.clear()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtient les informations détaillées d'un fichier vidéo.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire avec les informations du fichier
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValidationError(f"Le fichier {file_path} n'existe pas")
        
        # Informations de base du fichier
        stat = file_path.stat()
        info = {
            'path': str(file_path.absolute()),
            'name': file_path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': file_path.suffix.lower(),
            'created': stat.st_ctime,
            'modified': stat.st_mtime
        }
        
        # Informations détaillées avec FFprobe si disponible
        try:
            media_info = self._get_media_info(str(file_path))
            info.update(media_info)
        except Exception as e:
            self.logger.warning(f"Could not get detailed media info: {e}")
            info['media_info_error'] = str(e)
        
        return info
    
    def _get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtient les informations média détaillées avec FFprobe.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire avec les informations média
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"FFprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        
        # Extraire les informations pertinentes
        format_info = data.get('format', {})
        streams = data.get('streams', [])
        
        video_streams = [s for s in streams if s.get('codec_type') == 'video']
        audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
        
        media_info = {
            'duration': float(format_info.get('duration', 0)),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'format_name': format_info.get('format_name', ''),
            'video_streams': len(video_streams),
            'audio_streams': len(audio_streams)
        }
        
        # Informations du premier stream vidéo
        if video_streams:
            video = video_streams[0]
            media_info.update({
                'video_codec': video.get('codec_name', ''),
                'width': int(video.get('width', 0)),
                'height': int(video.get('height', 0)),
                'fps': self._parse_fps(video.get('r_frame_rate', '0/1')),
                'video_bitrate': int(video.get('bit_rate', 0)) if video.get('bit_rate') else None
            })
        
        # Informations du premier stream audio
        if audio_streams:
            audio = audio_streams[0]
            media_info.update({
                'audio_codec': audio.get('codec_name', ''),
                'sample_rate': int(audio.get('sample_rate', 0)),
                'channels': int(audio.get('channels', 0)),
                'audio_bitrate': int(audio.get('bit_rate', 0)) if audio.get('bit_rate') else None
            })
        
        return media_info
    
    def _parse_fps(self, fps_string: str) -> float:
        """
        Parse une chaîne de FPS au format 'num/den'.
        
        Args:
            fps_string: Chaîne FPS (ex: '25/1', '30000/1001')
            
        Returns:
            FPS en tant que float
        """
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den)
            else:
                return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def ensure_directory_exists(self, directory: str) -> None:
        """
        S'assure qu'un répertoire existe.
        
        Args:
            directory: Chemin vers le répertoire
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_safe_filename(self, filename: str) -> str:
        """
        Génère un nom de fichier sûr en supprimant les caractères problématiques.
        
        Args:
            filename: Nom de fichier original
            
        Returns:
            Nom de fichier sécurisé
        """
        # Caractères à remplacer
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Supprimer les espaces en début/fin
        safe_filename = safe_filename.strip()
        
        # S'assurer que le nom n'est pas vide
        if not safe_filename:
            safe_filename = "unnamed_file"
        
        return safe_filename
    
    def copy_file(self, source: str, destination: str) -> None:
        """
        Copie un fichier avec gestion d'erreurs.
        
        Args:
            source: Fichier source
            destination: Fichier de destination
        """
        try:
            # S'assurer que le répertoire de destination existe
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            self.logger.info(f"File copied from {source} to {destination}")
            
        except Exception as e:
            raise ValidationError(f"Failed to copy file: {e}")
    
    def __del__(self):
        """Nettoyage automatique lors de la destruction de l'objet."""
        self.cleanup_temp_files()