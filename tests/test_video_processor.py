"""
Tests pour le processeur vidéo.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from ai_video_dubbing.processors.video_processor import VideoProcessor
from ai_video_dubbing.models.data_models import (
    Interval, Frame, ValidationError, ProcessingError
)


class TestVideoProcessor:
    """Tests pour VideoProcessor."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du temp_storage
        self.mock_temp_storage = MagicMock()
        self.mock_temp_storage.create_temp_file.return_value = str(
            Path(self.temp_dir) / "test_audio.wav"
        )
        
        # Créer le processeur avec mock de FFmpeg
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ffmpeg version 4.4.0"
            mock_run.return_value = mock_result
            
            self.processor = VideoProcessor(temp_storage=self.mock_temp_storage)
    
    def test_init_without_ffmpeg(self):
        """Test d'initialisation sans FFmpeg."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with pytest.raises(ProcessingError, match="FFmpeg not found"):
                VideoProcessor()
    
    def test_init_ffmpeg_not_working(self):
        """Test d'initialisation avec FFmpeg non fonctionnel."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            with pytest.raises(ProcessingError, match="not working properly"):
                VideoProcessor()
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_extract_audio_success(self, mock_exists, mock_run):
        """Test d'extraction audio réussie."""
        # Setup
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Créer le fichier de sortie simulé
        output_file = Path(self.temp_dir) / "test_audio.wav"
        output_file.touch()
        
        # Test
        result = self.processor.extract_audio("test_video.mp4")
        
        # Vérifications
        assert result == str(output_file)
        mock_run.assert_called_once()
        
        # Vérifier les arguments FFmpeg
        args = mock_run.call_args[0][0]
        assert 'ffmpeg' in args
        assert '-i' in args
        assert 'test_video.mp4' in args
        assert '-vn' in args  # Pas de vidéo
        assert '-acodec' in args
        assert 'pcm_s16le' in args
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_extract_audio_file_not_found(self, mock_exists, mock_run):
        """Test d'extraction audio avec fichier inexistant."""
        mock_exists.return_value = False
        
        with pytest.raises(ValidationError, match="Video file not found"):
            self.processor.extract_audio("nonexistent.mp4")
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_extract_audio_ffmpeg_failure(self, mock_exists, mock_run):
        """Test d'extraction audio avec échec FFmpeg."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "FFmpeg error"
        mock_run.return_value = mock_result
        
        with pytest.raises(ProcessingError, match="FFmpeg audio extraction failed"):
            self.processor.extract_audio("test_video.mp4")
    
    @patch('cv2.VideoCapture')
    @patch('pathlib.Path.exists')
    def test_extract_frames_during_speech_success(self, mock_exists, mock_cap_class):
        """Test d'extraction d'images pendant la parole."""
        # Setup
        mock_exists.return_value = True
        
        # Mock de VideoCapture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 25.0,    # FPS
            7: 1000,    # Total frames
            3: 1920,    # Width
            4: 1080     # Height
        }.get(prop, 0)
        
        # Mock de lecture de frame
        mock_frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame_data)
        
        mock_cap_class.return_value = mock_cap
        
        # Intervalles de test
        intervals = [
            Interval(start=1.0, end=3.0),
            Interval(start=5.0, end=7.0)
        ]
        
        # Test
        frames = self.processor.extract_frames_during_speech("test_video.mp4", intervals)
        
        # Vérifications
        assert len(frames) > 0
        assert all(isinstance(frame, Frame) for frame in frames)
        assert all(frame.width == 1920 for frame in frames)
        assert all(frame.height == 1080 for frame in frames)
        
        mock_cap.release.assert_called_once()
    
    @patch('cv2.VideoCapture')
    @patch('pathlib.Path.exists')
    def test_extract_frames_video_not_opened(self, mock_exists, mock_cap_class):
        """Test d'extraction d'images avec vidéo non ouverte."""
        mock_exists.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_class.return_value = mock_cap
        
        intervals = [Interval(start=1.0, end=3.0)]
        
        with pytest.raises(ProcessingError, match="Could not open video file"):
            self.processor.extract_frames_during_speech("test_video.mp4", intervals)
    
    def test_extract_frames_no_intervals(self):
        """Test d'extraction d'images sans intervalles."""
        with patch('pathlib.Path.exists', return_value=True):
            frames = self.processor.extract_frames_during_speech("test_video.mp4", [])
            assert frames == []
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_merge_audio_video_success(self, mock_exists, mock_run):
        """Test de fusion audio/vidéo réussie."""
        # Setup
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Créer le fichier de sortie simulé
        output_file = Path(self.temp_dir) / "output.mp4"
        output_file.touch()
        
        # Test
        self.processor.merge_audio_video(
            "video.mp4", 
            "audio.wav", 
            str(output_file)
        )
        
        # Vérifications
        mock_run.assert_called_once()
        
        # Vérifier les arguments FFmpeg
        args = mock_run.call_args[0][0]
        assert 'ffmpeg' in args
        assert '-i' in args
        assert 'video.mp4' in args
        assert 'audio.wav' in args
        assert '-c:v' in args
        assert 'copy' in args
        assert '-c:a' in args
        assert 'aac' in args
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_merge_audio_video_missing_files(self, mock_exists, mock_run):
        """Test de fusion avec fichiers manquants."""
        mock_exists.side_effect = lambda path: str(path) != "missing_video.mp4"
        
        with pytest.raises(ValidationError, match="Video file not found"):
            self.processor.merge_audio_video(
                "missing_video.mp4", 
                "audio.wav", 
                "output.mp4"
            )
    
    @patch('subprocess.run')
    def test_get_video_info_success(self, mock_run):
        """Test d'obtention d'informations vidéo."""
        # Mock de la réponse FFprobe
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "25/1",
                    "bit_rate": "5000000"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "44100",
                    "channels": 2,
                    "bit_rate": "128000"
                }
            ],
            "format": {
                "duration": "120.5",
                "bit_rate": "5128000",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "size": "77312000"
            }
        }
        '''
        mock_run.return_value = mock_result
        
        with patch('pathlib.Path.exists', return_value=True):
            info = self.processor.get_video_info("test_video.mp4")
        
        # Vérifications
        assert info['duration'] == 120.5
        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['fps'] == 25.0
        assert info['video_codec'] == 'h264'
        assert info['audio_codec'] == 'aac'
        assert info['sample_rate'] == 44100
        assert info['channels'] == 2
    
    def test_parse_fps(self):
        """Test du parsing de FPS."""
        assert self.processor._parse_fps('25/1') == 25.0
        assert self.processor._parse_fps('30000/1001') == pytest.approx(29.97, rel=1e-2)
        assert self.processor._parse_fps('60') == 60.0
        assert self.processor._parse_fps('invalid') == 0.0
        assert self.processor._parse_fps('25/0') == 0.0
    
    @patch('cv2.VideoCapture')
    @patch('pathlib.Path.exists')
    def test_extract_frame_at_timestamp(self, mock_exists, mock_cap_class):
        """Test d'extraction d'image à un timestamp."""
        mock_exists.return_value = True
        
        # Mock de VideoCapture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 25.0,    # FPS
            3: 1920,    # Width
            4: 1080     # Height
        }.get(prop, 0)
        
        mock_frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame_data)
        
        mock_cap_class.return_value = mock_cap
        
        # Test
        frame = self.processor.extract_frame_at_timestamp("test_video.mp4", 2.5)
        
        # Vérifications
        assert frame is not None
        assert isinstance(frame, Frame)
        assert frame.timestamp == 2.5
        assert frame.width == 1920
        assert frame.height == 1080
        
        # Vérifier que la position a été définie correctement
        mock_cap.set.assert_called_with(1, 62)  # 2.5 * 25 = 62.5 -> 62
        mock_cap.release.assert_called_once()
    
    @patch('cv2.VideoWriter')
    def test_create_video_from_frames(self, mock_writer_class):
        """Test de création de vidéo à partir d'images."""
        # Mock du writer
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer
        
        # Créer des frames de test
        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frames = [
            Frame(timestamp=0.0, image_data=frame_data, width=640, height=480),
            Frame(timestamp=0.04, image_data=frame_data, width=640, height=480),
            Frame(timestamp=0.08, image_data=frame_data, width=640, height=480)
        ]
        
        output_path = Path(self.temp_dir) / "output_video.mp4"
        
        # Test
        self.processor.create_video_from_frames(frames, str(output_path), fps=25.0)
        
        # Vérifications
        mock_writer_class.assert_called_once()
        assert mock_writer.write.call_count == 3
        mock_writer.release.assert_called_once()
    
    def test_create_video_from_frames_no_frames(self):
        """Test de création de vidéo sans images."""
        with pytest.raises(ValidationError, match="No frames provided"):
            self.processor.create_video_from_frames([], "output.mp4")
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_resize_video(self, mock_exists, mock_run):
        """Test de redimensionnement de vidéo."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Test
        self.processor.resize_video(
            "input.mp4", 
            str(Path(self.temp_dir) / "resized.mp4"), 
            1280, 
            720
        )
        
        # Vérifications
        mock_run.assert_called_once()
        
        # Vérifier les arguments FFmpeg
        args = mock_run.call_args[0][0]
        assert 'ffmpeg' in args
        assert '-vf' in args
        assert 'scale=1280:720' in args