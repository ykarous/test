"""
Tests pour les modèles de données.
"""

import pytest
from ai_video_dubbing.models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment, 
    Interval, ModelType
)


class TestPipelineConfig:
    """Tests pour PipelineConfig."""
    
    def test_default_config(self):
        """Test de la configuration par défaut."""
        config = PipelineConfig()
        
        assert config.enable_source_separation is False
        assert config.asr_model == "whisper-large-v3"
        assert config.ocr_model == "qwen-vl"
        assert config.voice_cloning_model == "tortoise-tts"
        assert config.output_codec == "h264"
        assert config.output_bitrate == "5M"
        assert config.temp_directory == "./temp"
        assert config.max_memory_usage == 0.8
    
    def test_custom_config(self):
        """Test d'une configuration personnalisée."""
        config = PipelineConfig(
            enable_source_separation=True,
            asr_model="whisper-base",
            temp_directory="/tmp/custom"
        )
        
        assert config.enable_source_separation is True
        assert config.asr_model == "whisper-base"
        assert config.temp_directory == "/tmp/custom"


class TestInterval:
    """Tests pour Interval."""
    
    def test_duration_calculation(self):
        """Test du calcul de durée."""
        interval = Interval(start=1.5, end=5.2)
        
        assert interval.duration == 3.7
        assert interval.start == 1.5
        assert interval.end == 5.2


class TestDialogueSegment:
    """Tests pour DialogueSegment."""
    
    def test_dialogue_segment_creation(self):
        """Test de création d'un segment de dialogue."""
        segment = DialogueSegment(
            speaker_id="SPEAKER_01",
            start_time=10.5,
            end_time=15.2,
            original_text="Bonjour, comment allez-vous ?",
            audio_path="/path/to/audio.wav",
            confidence_score=0.95
        )
        
        assert segment.speaker_id == "SPEAKER_01"
        assert segment.start_time == 10.5
        assert segment.end_time == 15.2
        assert segment.original_text == "Bonjour, comment allez-vous ?"
        assert segment.audio_path == "/path/to/audio.wav"
        assert segment.confidence_score == 0.95


class TestModelType:
    """Tests pour ModelType enum."""
    
    def test_model_types(self):
        """Test des types de modèles."""
        assert ModelType.ASR.value == "asr"
        assert ModelType.OCR.value == "ocr"
        assert ModelType.DIARIZATION.value == "diarization"
        assert ModelType.VOICE_CLONING.value == "voice_cloning"
        assert ModelType.SOURCE_SEPARATION.value == "source_separation"