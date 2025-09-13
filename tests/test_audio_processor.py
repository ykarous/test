"""
Tests pour le processeur audio.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from ai_video_dubbing.processors.audio_processor import AudioProcessor
from ai_video_dubbing.models.data_models import (
    Interval, SpeakerSegments, DialogueSegment, 
    ValidationError, ProcessingError
)


class TestAudioProcessor:
    """Tests pour AudioProcessor."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du temp_storage
        self.mock_temp_storage = MagicMock()
        
        # Créer le processeur avec mocks
        with patch('ai_video_dubbing.processors.audio_processor._PYANNOTE_AVAILABLE', False), \
             patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', True):
            self.processor = AudioProcessor(temp_storage=self.mock_temp_storage)
    
    def test_init_without_dependencies(self):
        """Test d'initialisation sans dépendances."""
        with patch('ai_video_dubbing.processors.audio_processor._PYANNOTE_AVAILABLE', False), \
             patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', False):
            processor = AudioProcessor()
            assert processor.vad_pipeline is None
            assert processor.diarization_pipeline is None
    
    @patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', True)
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('ai_video_dubbing.processors.audio_processor.np')
    @patch('pathlib.Path.exists')
    def test_detect_vad_fallback(self, mock_exists, mock_np, mock_librosa):
        """Test de détection VAD avec méthode de fallback."""
        # Setup
        mock_exists.return_value = True
        
        # Mock des données audio
        mock_y = np.array([0.1, 0.8, 0.9, 0.2, 0.1, 0.7, 0.8, 0.1])
        mock_sr = 44100
        mock_librosa.load.return_value = (mock_y, mock_sr)
        
        # Mock RMS
        mock_rms = np.array([0.1, 0.8, 0.9, 0.2, 0.1, 0.7, 0.8, 0.1])
        mock_librosa.feature.rms.return_value = [mock_rms]
        
        # Mock numpy functions
        mock_np.mean.return_value = 0.5
        mock_np.std.return_value = 0.3
        
        # Test
        intervals = self.processor._detect_vad_fallback("test_audio.wav")
        
        # Vérifications
        assert isinstance(intervals, list)
        mock_librosa.load.assert_called_once_with("test_audio.wav", sr=None)
        mock_librosa.feature.rms.assert_called_once()
    
    def test_detect_voice_activity_file_not_found(self):
        """Test de détection VAD avec fichier inexistant."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ValidationError, match="Audio file not found"):
                self.processor.detect_voice_activity("nonexistent.wav")
    
    def test_merge_close_intervals(self):
        """Test de fusion d'intervalles proches."""
        intervals = [
            Interval(start=1.0, end=2.0),
            Interval(start=2.2, end=3.0),  # Proche du précédent
            Interval(start=5.0, end=6.0),  # Éloigné
            Interval(start=6.1, end=7.0)   # Proche du précédent
        ]
        
        merged = self.processor._merge_close_intervals(intervals, gap_threshold=0.3)
        
        # Devrait fusionner les intervalles 1-2 et 4-5
        assert len(merged) == 2
        assert merged[0].start == 1.0
        assert merged[0].end == 3.0
        assert merged[1].start == 5.0
        assert merged[1].end == 7.0
    
    def test_merge_close_intervals_empty(self):
        """Test de fusion avec liste vide."""
        merged = self.processor._merge_close_intervals([])
        assert merged == []
    
    @patch('pathlib.Path.exists')
    def test_diarize_fallback(self, mock_exists):
        """Test de diarisation avec méthode de fallback."""
        mock_exists.return_value = True
        
        # Mock de la détection VAD
        mock_intervals = [
            Interval(start=1.0, end=3.0),
            Interval(start=5.0, end=7.0)
        ]
        
        with patch.object(self.processor, 'detect_voice_activity', return_value=mock_intervals):
            result = self.processor._diarize_fallback("test_audio.wav")
        
        # Vérifications
        assert isinstance(result, SpeakerSegments)
        assert result.speaker_count == 1
        assert len(result.segments) == 2
        assert result.segments[0].speaker_id == "SPEAKER_00"
        assert result.segments[0].start_time == 1.0
        assert result.segments[0].end_time == 3.0
        assert result.confidence_scores["SPEAKER_00"] == 0.8
    
    @patch('pathlib.Path.exists')
    def test_perform_speaker_diarization_file_not_found(self, mock_exists):
        """Test de diarisation avec fichier inexistant."""
        mock_exists.return_value = False
        
        with pytest.raises(ValidationError, match="Audio file not found"):
            self.processor.perform_speaker_diarization("nonexistent.wav")
    
    @patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', True)
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_get_audio_info_librosa(self, mock_stat, mock_exists, mock_librosa):
        """Test d'obtention d'informations audio avec librosa."""
        # Setup
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024000
        
        # Mock des données audio
        mock_y = np.array([0.1, -0.2, 0.8, -0.5, 0.3])
        mock_sr = 44100
        mock_librosa.load.return_value = (mock_y, mock_sr)
        
        # Mock des fonctions librosa
        mock_librosa.feature.zero_crossing_rate.return_value = [[0.1, 0.2, 0.15]]
        
        # Test
        info = self.processor.get_audio_info("test_audio.wav")
        
        # Vérifications
        assert info['sample_rate'] == 44100
        assert info['channels'] == 1
        assert info['samples'] == 5
        assert info['size_bytes'] == 1024000
        assert 'rms_energy' in info
        assert 'max_amplitude' in info
        assert 'zero_crossing_rate' in info
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_get_audio_info_ffprobe(self, mock_exists, mock_run):
        """Test d'obtention d'informations audio avec FFprobe."""
        mock_exists.return_value = True
        
        # Mock de la réponse FFprobe
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "pcm_s16le",
                    "sample_rate": "44100",
                    "channels": 2
                }
            ],
            "format": {
                "duration": "120.5",
                "bit_rate": "1411200",
                "format_name": "wav",
                "size": "21427200"
            }
        }
        '''
        mock_run.return_value = mock_result
        
        # Forcer l'utilisation de FFprobe
        with patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', False):
            processor = AudioProcessor()
            info = processor._get_audio_info_ffprobe("test_audio.wav")
        
        # Vérifications
        assert info['duration'] == 120.5
        assert info['sample_rate'] == 44100
        assert info['channels'] == 2
        assert info['format'] == 'wav'
        assert info['codec'] == 'pcm_s16le'
        assert info['bitrate'] == 1411200
        assert info['size_bytes'] == 21427200
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_with_ffmpeg(self, mock_exists, mock_run):
        """Test de conversion audio avec FFmpeg."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Test
        result = self.processor._convert_with_ffmpeg(
            "input.wav", 
            str(Path(self.temp_dir) / "output.wav"), 
            44100, 
            2
        )
        
        # Vérifications
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ffmpeg' in args
        assert '-i' in args
        assert 'input.wav' in args
        assert '-ar' in args
        assert '44100' in args
        assert '-ac' in args
        assert '2' in args
    
    @patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', True)
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('ai_video_dubbing.processors.audio_processor.sf')
    @patch('ai_video_dubbing.processors.audio_processor.np')
    @patch('pathlib.Path.exists')
    def test_convert_with_librosa_mono_to_stereo(self, mock_exists, mock_np, mock_sf, mock_librosa):
        """Test de conversion mono vers stéréo avec librosa."""
        mock_exists.return_value = True
        
        # Mock audio mono
        mock_y = np.array([0.1, 0.2, 0.3])
        mock_sr = 44100
        mock_librosa.load.return_value = (mock_y, mock_sr)
        
        # Mock numpy stack pour conversion stéréo
        mock_stereo = np.array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]])
        mock_np.stack.return_value = mock_stereo
        
        # Test
        result = self.processor._convert_with_librosa(
            "input.wav", 
            str(Path(self.temp_dir) / "output.wav"), 
            44100, 
            2  # Stéréo
        )
        
        # Vérifications
        mock_librosa.load.assert_called_once_with("input.wav", sr=44100, mono=False)
        mock_np.stack.assert_called_once()
        mock_sf.write.assert_called_once()
    
    @patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', True)
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('ai_video_dubbing.processors.audio_processor.sf')
    @patch('ai_video_dubbing.processors.audio_processor.np')
    @patch('pathlib.Path.exists')
    def test_convert_with_librosa_stereo_to_mono(self, mock_exists, mock_np, mock_sf, mock_librosa):
        """Test de conversion stéréo vers mono avec librosa."""
        mock_exists.return_value = True
        
        # Mock audio stéréo
        mock_y = np.array([[0.1, 0.2, 0.3], [0.15, 0.25, 0.35]])
        mock_sr = 44100
        mock_librosa.load.return_value = (mock_y, mock_sr)
        
        # Mock numpy mean pour conversion mono
        mock_mono = np.array([0.125, 0.225, 0.325])
        mock_np.mean.return_value = mock_mono
        
        # Test
        result = self.processor._convert_with_librosa(
            "input.wav", 
            str(Path(self.temp_dir) / "output.wav"), 
            44100, 
            1  # Mono
        )
        
        # Vérifications
        mock_librosa.load.assert_called_once_with("input.wav", sr=44100, mono=True)
        mock_sf.write.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_separate_sources_disabled(self, mock_exists):
        """Test de séparation de source désactivée."""
        mock_exists.return_value = True
        
        result = self.processor.separate_sources("test.wav", enable_separation=False)
        
        # Vérifications
        assert result.vocals_path == "test.wav"
        assert result.music_path == ""
        assert result.effects_path == ""
        assert result.original_path == "test.wav"
        assert result.separation_quality == 1.0
        assert result.processing_time == 0.0
    
    @patch('pathlib.Path.exists')
    def test_separate_sources_file_not_found(self, mock_exists):
        """Test de séparation avec fichier inexistant."""
        mock_exists.return_value = False
        
        with pytest.raises(ValidationError, match="Audio file not found"):
            self.processor.separate_sources("nonexistent.wav")
    
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('ai_video_dubbing.processors.audio_processor.sf')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_separate_sources_frequency_fallback(self, mock_mkdir, mock_exists, mock_sf, mock_librosa):
        """Test de séparation avec fallback fréquentiel."""
        # Setup
        mock_exists.return_value = True
        mock_mkdir.return_value = None
        
        # Mock de l'audio
        mock_y = np.random.random(16000)
        mock_sr = 16000
        mock_librosa.load.return_value = (mock_y, mock_sr)
        
        # Mock du temp_storage
        self.processor.temp_storage = MagicMock()
        self.processor.temp_storage.get_temp_path.return_value = "/tmp/separation"
        
        # Mock des méthodes internes
        with patch.object(self.processor, '_separate_with_demucs', return_value={}), \
             patch.object(self.processor, '_separate_with_frequency_filter') as mock_freq_sep:
            
            mock_freq_sep.return_value = {
                "vocals": "/tmp/separation/vocals.wav",
                "music": "/tmp/separation/music.wav"
            }
            
            # Test
            result = self.processor.separate_sources("test.wav", enable_separation=True)
            
            # Vérifications
            assert result.vocals_path == "/tmp/separation/vocals.wav"
            assert result.music_path == "/tmp/separation/music.wav"
            assert result.original_path == "test.wav"
            mock_freq_sep.assert_called_once()
    
    def test_apply_bandpass_filter(self):
        """Test du filtre passe-bande."""
        # Créer un signal de test
        sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        
        # Signal avec plusieurs fréquences
        signal = (np.sin(2 * np.pi * 440 * t) +  # 440 Hz (dans la bande)
                 np.sin(2 * np.pi * 100 * t) +   # 100 Hz (hors bande)
                 np.sin(2 * np.pi * 5000 * t))   # 5000 Hz (hors bande)
        
        # Appliquer le filtre
        filtered = self.processor._apply_bandpass_filter(signal, sr, 300, 3400)
        
        # Le signal filtré devrait être différent de l'original
        assert not np.array_equal(signal, filtered)
        assert len(filtered) == len(signal)
    
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('ai_video_dubbing.processors.audio_processor.sf')
    @patch('pathlib.Path.exists')
    def test_combine_audio_files(self, mock_exists, mock_sf, mock_librosa):
        """Test de combinaison de fichiers audio."""
        # Setup
        mock_exists.return_value = True
        
        # Mock des audios
        audio1 = np.random.random(1000)
        audio2 = np.random.random(1000)
        sr = 16000
        
        mock_librosa.load.side_effect = [(audio1, sr), (audio2, sr)]
        
        # Test
        self.processor._combine_audio_files(
            ["file1.wav", "file2.wav"], 
            "combined.wav"
        )
        
        # Vérifications
        assert mock_librosa.load.call_count == 2
        mock_sf.write.assert_called_once()
        
        # Vérifier que l'audio combiné a été calculé
        call_args = mock_sf.write.call_args[0]
        combined_audio = call_args[1]
        assert len(combined_audio) == 1000  # Longueur minimale
    
    @patch('ai_video_dubbing.processors.audio_processor.librosa')
    @patch('pathlib.Path.exists')
    def test_evaluate_separation_quality(self, mock_exists, mock_librosa):
        """Test d'évaluation de qualité de séparation."""
        # Setup
        mock_exists.return_value = True
        
        # Mock des audios
        original = np.random.random(1000)
        vocals = original * 0.8 + np.random.random(1000) * 0.2  # Vocals similaires à l'original
        sr = 16000
        
        mock_librosa.load.side_effect = [(original, sr), (vocals, sr)]
        
        # Test
        quality = self.processor._evaluate_separation_quality("original.wav", "vocals.wav")
        
        # Vérifications
        assert 0.0 <= quality <= 1.0
        assert mock_librosa.load.call_count == 2
    
    def test_evaluate_separation_quality_no_vocals(self):
        """Test d'évaluation avec fichier vocals inexistant."""
        quality = self.processor._evaluate_separation_quality("original.wav", "")
        assert quality == 0.0
        
        quality = self.processor._evaluate_separation_quality("original.wav", "nonexistent.wav")
        assert quality == 0.0
    
    def test_not_implemented_methods(self):
        """Test des méthodes non encore implémentées."""        
        with pytest.raises(NotImplementedError):
            mock_diarization = SpeakerSegments(segments=[], speaker_count=0, confidence_scores={})
            self.processor.segment_by_speaker("test.wav", mock_diarization)
        
        with pytest.raises(NotImplementedError):
            self.processor.normalize_audio("test.wav")
    
    @patch('pathlib.Path.exists')
    def test_convert_audio_format_file_not_found(self, mock_exists):
        """Test de conversion avec fichier inexistant."""
        mock_exists.return_value = False
        
        with pytest.raises(ValidationError, match="Input audio file not found"):
            self.processor.convert_audio_format("nonexistent.wav", "output.wav")
    
    @patch('ai_video_dubbing.processors.audio_processor._LIBROSA_AVAILABLE', False)
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_convert_audio_format_fallback_to_ffmpeg(self, mock_exists, mock_run):
        """Test de conversion avec fallback vers FFmpeg."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Créer un processeur sans librosa
        processor = AudioProcessor()
        
        # Test
        result = processor.convert_audio_format("input.wav", "output.wav")
        
        # Vérifications
        assert result == "output.wav"
        mock_run.assert_called_once()