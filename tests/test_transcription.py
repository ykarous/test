"""
Tests pour la transcription ASR.
"""

import tempfile
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from ai_video_dubbing.processors.ai_model_manager import AIModelManager
from ai_video_dubbing.models.data_models import (
    ModelType, TranscriptionResult, TranscriptionSegment, WordTimestamp,
    ProcessingError, ValidationError
)


class TestTranscription:
    """Tests pour la transcription ASR."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        # Mock des dépendances
        with patch.multiple(
            'ai_video_dubbing.processors.ai_model_manager',
            _TORCH_AVAILABLE=True,
            _WHISPER_AVAILABLE=True,
            _TRANSFORMERS_AVAILABLE=True,
            _PADDLEOCR_AVAILABLE=True,
            _EASYOCR_AVAILABLE=True
        ):
            self.manager = AIModelManager()
    
    @patch('pathlib.Path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test de transcription avec fichier inexistant."""
        mock_exists.return_value = False
        
        try:
            self.manager.transcribe_audio("nonexistent.wav")
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "Audio file not found" in str(e)
    
    @patch('pathlib.Path.exists')
    @patch.object(AIModelManager, 'get_model')
    @patch.object(AIModelManager, '_transcribe_with_whisperx')
    @patch.object(AIModelManager, '_process_transcription_result')
    def test_transcribe_audio_success_whisperx(
        self, mock_process, mock_whisperx, mock_get_model, mock_exists
    ):
        """Test de transcription réussie avec WhisperX."""
        # Setup
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Mock des résultats WhisperX
        mock_whisperx_result = {
            "text": "Hello world",
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 2.0,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9},
                        {"word": "world", "start": 0.6, "end": 1.0, "probability": 0.8}
                    ]
                }
            ],
            "language": "en"
        }
        mock_whisperx.return_value = mock_whisperx_result
        
        # Mock du résultat traité
        expected_result = TranscriptionResult(
            text="Hello world",
            segments=[],
            language="en",
            confidence=0.85,
            processing_time=1.5,
            model_name="whisper-base",
            word_count=2
        )
        mock_process.return_value = expected_result
        
        # Test
        result = self.manager.transcribe_audio("test.wav")
        
        # Vérifications
        assert result == expected_result
        mock_get_model.assert_called_once_with(ModelType.ASR, "whisper-base")
        mock_whisperx.assert_called_once()
        mock_process.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch.object(AIModelManager, 'get_model')
    @patch.object(AIModelManager, '_transcribe_with_whisperx')
    @patch.object(AIModelManager, '_transcribe_with_whisper')
    @patch.object(AIModelManager, '_process_transcription_result')
    def test_transcribe_audio_fallback_to_whisper(
        self, mock_process, mock_whisper, mock_whisperx, mock_get_model, mock_exists
    ):
        """Test de transcription avec fallback vers Whisper standard."""
        # Setup
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # WhisperX échoue
        mock_whisperx.side_effect = Exception("WhisperX failed")
        
        # Whisper standard réussit
        mock_whisper_result = {
            "text": "Hello world",
            "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
            "language": "en"
        }
        mock_whisper.return_value = mock_whisper_result
        
        expected_result = TranscriptionResult(
            text="Hello world",
            segments=[],
            language="en",
            confidence=0.8,
            processing_time=1.0,
            model_name="whisper-base",
            word_count=2
        )
        mock_process.return_value = expected_result
        
        # Test
        result = self.manager.transcribe_audio("test.wav")
        
        # Vérifications
        assert result == expected_result
        mock_whisperx.assert_called_once()
        mock_whisper.assert_called_once()
    
    def test_transcribe_with_whisperx_import_error(self):
        """Test de WhisperX avec erreur d'import."""
        with patch('ai_video_dubbing.processors.ai_model_manager.whisperx', side_effect=ImportError):
            try:
                self.manager._transcribe_with_whisperx("test.wav", "whisper-base", {})
                assert False, "Devrait lever ProcessingError"
            except ProcessingError as e:
                assert "WhisperX not available" in str(e)
    
    @patch('ai_video_dubbing.processors.ai_model_manager.whisperx')
    def test_transcribe_with_whisperx_success(self, mock_whisperx):
        """Test de transcription WhisperX réussie."""
        # Mock du modèle WhisperX
        mock_model = MagicMock()
        mock_whisperx.load_model.return_value = mock_model
        
        # Mock de l'audio
        mock_audio = MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        # Mock des résultats de transcription
        mock_transcription_result = {
            "segments": [{"text": "Hello", "start": 0.0, "end": 1.0}],
            "language": "en"
        }
        mock_model.transcribe.return_value = mock_transcription_result
        
        # Mock du modèle d'alignement
        mock_align_model = MagicMock()
        mock_metadata = MagicMock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, mock_metadata)
        
        # Mock des résultats d'alignement
        mock_aligned_result = {
            "segments": [
                {
                    "text": "Hello",
                    "start": 0.0,
                    "end": 1.0,
                    "words": [{"word": "Hello", "start": 0.0, "end": 1.0, "probability": 0.9}]
                }
            ]
        }
        mock_whisperx.align.return_value = mock_aligned_result
        
        # Test
        options = {"language": "en", "word_timestamps": True}
        result = self.manager._transcribe_with_whisperx("test.wav", "whisper-base", options)
        
        # Vérifications
        assert result == mock_aligned_result
        mock_whisperx.load_model.assert_called_once()
        mock_whisperx.load_audio.assert_called_once_with("test.wav")
        mock_model.transcribe.assert_called_once()
        mock_whisperx.align.assert_called_once()
    
    def test_transcribe_with_whisper_success(self):
        """Test de transcription Whisper standard."""
        # Mock du modèle
        mock_model = MagicMock()
        mock_result = {
            "text": "Hello world",
            "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
            "language": "en"
        }
        mock_model.transcribe.return_value = mock_result
        
        # Test
        options = {"language": "en", "temperature": 0.0}
        result = self.manager._transcribe_with_whisper(mock_model, "test.wav", options)
        
        # Vérifications
        assert result == mock_result
        mock_model.transcribe.assert_called_once_with(
            "test.wav", 
            language="en", 
            temperature=0.0
        )
    
    def test_process_transcription_result(self):
        """Test de traitement des résultats de transcription."""
        # Données de test
        raw_result = {
            "text": "Hello world",
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 2.0,
                    "avg_logprob": -0.2,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9},
                        {"word": "world", "start": 0.6, "end": 1.0, "probability": 0.8}
                    ]
                }
            ],
            "language": "en"
        }
        
        # Test
        result = self.manager._process_transcription_result(
            raw_result, 1.5, "whisper-base"
        )
        
        # Vérifications
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.processing_time == 1.5
        assert result.model_name == "whisper-base"
        assert result.word_count == 2
        assert len(result.segments) == 1
        
        segment = result.segments[0]
        assert segment.text == "Hello world"
        assert segment.start == 0.0
        assert segment.end == 2.0
        assert len(segment.word_timestamps) == 2
        
        word1 = segment.word_timestamps[0]
        assert word1.word == "Hello"
        assert word1.start == 0.0
        assert word1.end == 0.5
        assert word1.confidence == 0.9
    
    def test_process_transcription_result_no_words(self):
        """Test de traitement sans horodatages de mots."""
        raw_result = {
            "text": "Hello world",
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 2.0,
                    "avg_logprob": -0.1
                }
            ],
            "language": "en"
        }
        
        result = self.manager._process_transcription_result(
            raw_result, 1.0, "whisper-base"
        )
        
        assert len(result.segments) == 1
        assert len(result.segments[0].word_timestamps) == 0
    
    @patch.object(AIModelManager, 'transcribe_audio')
    def test_transcribe_audio_segments(self, mock_transcribe):
        """Test de transcription de segments multiples."""
        # Mock des résultats
        results = [
            TranscriptionResult(
                text=f"Segment {i}",
                segments=[],
                language="en",
                confidence=0.8,
                processing_time=1.0,
                model_name="whisper-base",
                word_count=2
            )
            for i in range(3)
        ]
        
        mock_transcribe.side_effect = results
        
        # Test
        segments = ["seg1.wav", "seg2.wav", "seg3.wav"]
        transcription_results = self.manager.transcribe_audio_segments(segments)
        
        # Vérifications
        assert len(transcription_results) == 3
        assert mock_transcribe.call_count == 3
        
        for i, result in enumerate(transcription_results):
            assert result.text == f"Segment {i}"
    
    @patch.object(AIModelManager, 'transcribe_audio')
    def test_transcribe_audio_segments_with_error(self, mock_transcribe):
        """Test de transcription avec erreur sur un segment."""
        # Premier segment réussit, deuxième échoue
        mock_transcribe.side_effect = [
            TranscriptionResult(
                text="Success",
                segments=[],
                language="en",
                confidence=0.8,
                processing_time=1.0,
                model_name="whisper-base",
                word_count=1
            ),
            Exception("Transcription failed")
        ]
        
        # Test
        segments = ["seg1.wav", "seg2.wav"]
        results = self.manager.transcribe_audio_segments(segments)
        
        # Vérifications
        assert len(results) == 2
        assert results[0].text == "Success"
        assert results[1].text == ""  # Résultat vide pour l'erreur
        assert results[1].confidence == 0.0
    
    @patch('ai_video_dubbing.processors.ai_model_manager.whisper')
    def test_get_supported_languages(self, mock_whisper):
        """Test d'obtention des langues supportées."""
        # Mock des langues Whisper
        mock_whisper.tokenizer.LANGUAGES = {
            "en": "english",
            "fr": "french",
            "es": "spanish"
        }
        
        languages = self.manager.get_supported_languages()
        
        assert "en" in languages
        assert "fr" in languages
        assert "es" in languages
    
    def test_get_supported_languages_fallback(self):
        """Test d'obtention des langues avec fallback."""
        with patch('ai_video_dubbing.processors.ai_model_manager._WHISPER_AVAILABLE', False):
            languages = self.manager.get_supported_languages()
            assert languages == ["en"]
    
    @patch('pathlib.Path.exists')
    @patch.object(AIModelManager, 'get_model')
    @patch('ai_video_dubbing.processors.ai_model_manager.whisper')
    def test_detect_language(self, mock_whisper, mock_get_model, mock_exists):
        """Test de détection de langue."""
        # Setup
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Mock de l'audio et du mel spectrogram
        mock_audio = MagicMock()
        mock_whisper.load_audio.return_value = mock_audio
        mock_whisper.pad_or_trim.return_value = mock_audio
        
        mock_mel = MagicMock()
        mock_whisper.log_mel_spectrogram.return_value = mock_mel
        mock_mel.to.return_value = mock_mel
        
        # Mock de la détection de langue
        mock_model.detect_language.return_value = (None, {
            "en": 0.8,
            "fr": 0.15,
            "es": 0.05
        })
        
        # Test
        result = self.manager.detect_language("test.wav")
        
        # Vérifications
        assert result["en"] == 0.8
        assert result["fr"] == 0.15
        assert result["es"] == 0.05
        
        # Vérifier que les langues sont triées par probabilité
        languages = list(result.keys())
        assert languages[0] == "en"  # Plus haute probabilité en premier
    
    @patch('pathlib.Path.exists')
    def test_detect_language_file_not_found(self, mock_exists):
        """Test de détection de langue avec fichier inexistant."""
        mock_exists.return_value = False
        
        try:
            self.manager.detect_language("nonexistent.wav")
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "Audio file not found" in str(e)