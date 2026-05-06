#!/usr/bin/env python3
"""
Tests pour le processeur de synchronisation temporelle.
"""

import tempfile
import numpy as np
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from ai_video_dubbing.processors.sync_processor import SyncProcessor, SyncResult, AlignmentPoint
from ai_video_dubbing.models.data_models import (
    TranscriptionResult, TranscriptionSegment, OCRResult, DialogueSegment,
    SpeakerSegments, WordTimestamp, ProcessingError, ValidationError
)


class TestSyncProcessor:
    """Tests pour SyncProcessor."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.processor = SyncProcessor()
        
        # Créer des données de test
        self.asr_segments = [
            TranscriptionSegment(
                text="Hello world",
                start=1.0,
                end=3.0,
                confidence=0.9,
                word_timestamps=[]
            ),
            TranscriptionSegment(
                text="This is a test",
                start=4.0,
                end=6.0,
                confidence=0.8,
                word_timestamps=[]
            )
        ]
        
        self.asr_result = TranscriptionResult(
            text="Hello world This is a test",
            segments=self.asr_segments,
            language="en",
            confidence=0.85,
            processing_time=1.0,
            model_name="whisper-base",
            word_count=6
        )
        
        self.ocr_results = [
            OCRResult(
                text="Hello world",
                timestamp=1.2,
                confidence=0.95,
                bounding_box={"x1": 100, "y1": 50, "x2": 200, "y2": 100}
            )
        ]

    def test_init(self):
        """Test d'initialisation du processeur."""
        processor = SyncProcessor()
        assert processor.temp_storage is None
        assert processor.logger is not None
    
    def test_synchronize_asr_ocr_no_asr_segments(self):
        """Test avec résultats ASR vides."""
        empty_asr = TranscriptionResult(
            text="",
            segments=[],
            language="en",
            confidence=0.0,
            processing_time=0.0,
            model_name="whisper-base",
            word_count=0
        )
        
        try:
            self.processor.synchronize_asr_ocr(empty_asr, self.ocr_results)
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "no segments" in str(e).lower()
    
    def test_synchronize_asr_ocr_no_ocr_results(self):
        """Test avec résultats OCR vides."""
        result = self.processor.synchronize_asr_ocr(self.asr_result, [])
        
        # Devrait retourner un résultat basé uniquement sur l'ASR
        assert result.alignment_method == "asr_only"
        assert len(result.synchronized_segments) == len(self.asr_result.segments)
        assert result.confidence_score == self.asr_result.confidence
    
    def test_calculate_text_similarity(self):
        """Test de calcul de similarité textuelle."""
        # Textes identiques
        similarity = self.processor._calculate_text_similarity("hello world", "hello world")
        assert similarity == 1.0
        
        # Textes différents
        similarity = self.processor._calculate_text_similarity("hello", "goodbye")
        assert similarity == 0.0
        
        # Textes partiellement similaires
        similarity = self.processor._calculate_text_similarity("hello world", "hello there")
        assert 0.0 < similarity < 1.0
        
        # Textes vides
        similarity = self.processor._calculate_text_similarity("", "")
        assert similarity == 1.0
    
    def test_seconds_to_srt_time(self):
        """Test de conversion vers format SRT."""
        # Test avec différentes valeurs
        assert self.processor._seconds_to_srt_time(0.0) == "00:00:00,000"
        assert self.processor._seconds_to_srt_time(1.5) == "00:00:01,500"
        assert self.processor._seconds_to_srt_time(61.25) == "00:01:01,250"
        assert self.processor._seconds_to_srt_time(3661.123) == "01:01:01,123"
