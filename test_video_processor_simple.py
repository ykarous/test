#!/usr/bin/env python3
"""
Script de test simple pour le processeur vidéo.
"""

import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_video_dubbing.processors.video_processor import VideoProcessor
from ai_video_dubbing.models.data_models import Interval, Frame
from ai_video_dubbing.utils.temp_storage import TempStorage


def test_video_processor_basic():
    """Test basique du processeur vidéo."""
    print("=== Test VideoProcessor ===")
    
    # Mock FFmpeg pour les tests
    with patch('subprocess.run') as mock_run:
        # Mock de vérification FFmpeg
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ffmpeg version 4.4.0"
        mock_run.return_value = mock_result
        
        try:
            processor = VideoProcessor()
            print("✅ Test 1 réussi: VideoProcessor initialisé")
        except Exception as e:
            print(f"❌ Test 1 échoué: {e}")
            return
    
    # Test de parsing FPS
    fps_tests = [
        ("25/1", 25.0),
        ("30000/1001", 29.97),
        ("60", 60.0),
        ("invalid", 0.0)
    ]
    
    for fps_str, expected in fps_tests:
        result = processor._parse_fps(fps_str)
        if abs(result - expected) < 0.1:
            print(f"✅ Test FPS réussi: {fps_str} -> {result}")
        else:
            print(f"❌ Test FPS échoué: {fps_str} -> {result} (attendu: {expected})")
    
    # Test avec TempStorage
    with TempStorage() as storage:
        processor_with_storage = VideoProcessor(temp_storage=storage)
        
        # Simuler l'extraction audio
        with patch('subprocess.run') as mock_run, \
             patch('pathlib.Path.exists', return_value=True):
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            # Créer un fichier de sortie simulé
            temp_file = storage.create_temp_file(suffix='.wav', category='audio')
            Path(temp_file).touch()
            
            try:
                result = processor_with_storage.extract_audio("fake_video.mp4")
                print(f"✅ Test extraction audio réussi: {result}")
            except Exception as e:
                print(f"❌ Test extraction audio échoué: {e}")
    
    # Test de création de frames
    frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
    frames = [
        Frame(timestamp=0.0, image_data=frame_data, width=640, height=480),
        Frame(timestamp=1.0, image_data=frame_data, width=640, height=480)
    ]
    
    with patch('cv2.VideoWriter') as mock_writer_class:
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test_output.mp4"
                processor.create_video_from_frames(frames, str(output_path))
                print("✅ Test création vidéo à partir de frames réussi")
        except Exception as e:
            print(f"❌ Test création vidéo échoué: {e}")
    
    print("=== Tests VideoProcessor terminés ===")


def test_video_info_parsing():
    """Test du parsing d'informations vidéo."""
    print("\n=== Test parsing informations vidéo ===")
    
    # Mock FFmpeg check
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ffmpeg version 4.4.0"
        mock_run.return_value = mock_result
        
        processor = VideoProcessor()
    
    # Mock de get_video_info
    with patch('subprocess.run') as mock_run, \
         patch('pathlib.Path.exists', return_value=True):
        
        # Simuler une réponse FFprobe
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
                    "r_frame_rate": "25/1"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "44100",
                    "channels": 2
                }
            ],
            "format": {
                "duration": "120.5",
                "bit_rate": "5000000",
                "format_name": "mp4"
            }
        }
        '''
        mock_run.return_value = mock_result
        
        try:
            info = processor.get_video_info("fake_video.mp4")
            
            expected_fields = [
                ('duration', 120.5),
                ('width', 1920),
                ('height', 1080),
                ('fps', 25.0),
                ('video_codec', 'h264'),
                ('audio_codec', 'aac')
            ]
            
            for field, expected_value in expected_fields:
                if field in info and info[field] == expected_value:
                    print(f"✅ Champ {field}: {info[field]}")
                else:
                    print(f"❌ Champ {field}: {info.get(field)} (attendu: {expected_value})")
            
        except Exception as e:
            print(f"❌ Test parsing info échoué: {e}")


if __name__ == "__main__":
    test_video_processor_basic()
    test_video_info_parsing()
    print("\n=== Tous les tests terminés ===")