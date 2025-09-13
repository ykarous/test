#!/usr/bin/env python3
"""
Tests pour le processeur de segmentation audio par locuteur.
"""

import tempfile
import numpy as np
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import os

from ai_video_dubbing.processors.speaker_segmentation import (
    SpeakerSegmentationProcessor, SegmentationResult, AudioSegment
)
from ai_video_dubbing.models.data_models import (
    DialogueSegment, SpeakerSegments, ProcessingError, ValidationError
)
from ai_video_dubbing.utils.temp_storage import TempStorage


class TestSpeakerSegmentationProcessor:
    """Tests pour SpeakerSegmentationProcessor."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_storage = TempStorage()
        self.processor = SpeakerSegmentationProcessor(self.temp_storage)
        
        # Créer des segments de test
        self.speaker_segments = SpeakerSegments(
            segments=[
                DialogueSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=3.0,
                    original_text="Hello world",
                    audio_path="",
                    confidence_score=0.9
                ),
                DialogueSegment(
                    speaker_id="SPEAKER_01",
                    start_time=4.0,
                    end_time=6.0,
                    original_text="This is a test",
                    audio_path="",
                    confidence_score=0.8
                ),
                DialogueSegment(
                    speaker_id="SPEAKER_00",
                    start_time=7.0,
                    end_time=9.0,
                    original_text="Another segment",
                    audio_path="",
                    confidence_score=0.85
                )
            ],
            speaker_count=2,
            confidence_scores={"SPEAKER_00": 0.875, "SPEAKER_01": 0.8}
        )
        
        # Créer des données audio de test
        self.sample_rate = 16000
        self.audio_duration = 10.0
        self.audio_data = self._create_test_audio(self.audio_duration, self.sample_rate)
    
    def _create_test_audio(self, duration: float, sample_rate: int) -> np.ndarray:
        """Crée des données audio de test."""
        num_samples = int(duration * sample_rate)
        
        # Générer un signal sinusoïdal avec du bruit
        t = np.linspace(0, duration, num_samples)
        frequency = 440  # La note A4
        signal = 0.3 * np.sin(2 * np.pi * frequency * t)
        noise = 0.1 * np.random.randn(num_samples)
        
        return signal + noise
    
    def test_init(self):
        """Test d'initialisation du processeur."""
        processor = SpeakerSegmentationProcessor()
        assert processor.temp_storage is not None
        assert processor.logger is not None
        assert processor.min_segment_duration == 0.5
        assert processor.max_gap_duration == 0.2
        assert processor.fade_duration == 0.05
    
    def test_init_with_temp_storage(self):
        """Test d'initialisation avec gestionnaire de stockage."""
        temp_storage = TempStorage()
        processor = SpeakerSegmentationProcessor(temp_storage)
        assert processor.temp_storage is temp_storage
    
    @patch('ai_video_dubbing.processors.speaker_segmentation.librosa')
    def test_load_audio(self, mock_librosa):
        """Test de chargement audio."""
        # Mock librosa.load
        mock_librosa.load.return_value = (self.audio_data, self.sample_rate)
        
        audio_data, sample_rate = self.processor._load_audio("test.wav")
        
        assert np.array_equal(audio_data, self.audio_data)
        assert sample_rate == self.sample_rate
        mock_librosa.load.assert_called_once_with("test.wav", sr=None, mono=True)
    
    def test_load_audio_missing_librosa(self):
        """Test de chargement audio sans librosa."""
        with patch('ai_video_dubbing.processors.speaker_segmentation.librosa', None):
            try:
                self.processor._load_audio("test.wav")
                assert False, "Devrait lever ProcessingError"
            except ProcessingError as e:
                assert "librosa is required" in str(e)
    
    def test_extract_speaker_segments(self):
        """Test d'extraction des segments par locuteur."""
        segments = self.processor._extract_speaker_segments(
            self.audio_data, self.sample_rate, self.speaker_segments
        )
        
        # Vérifier la structure
        assert "SPEAKER_00" in segments
        assert "SPEAKER_01" in segments
        assert len(segments["SPEAKER_00"]) == 2  # Deux segments pour SPEAKER_00
        assert len(segments["SPEAKER_01"]) == 1  # Un segment pour SPEAKER_01
        
        # Vérifier les propriétés des segments
        speaker_00_segments = segments["SPEAKER_00"]
        assert speaker_00_segments[0].speaker_id == "SPEAKER_00"
        assert speaker_00_segments[0].start_time == 1.0
        assert speaker_00_segments[0].end_time == 3.0
        assert len(speaker_00_segments[0].audio_data) > 0
    
    def test_extract_speaker_segments_short_duration(self):
        """Test avec segments trop courts."""
        # Créer des segments très courts
        short_segments = SpeakerSegments(
            segments=[
                DialogueSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=1.1,  # Seulement 0.1s
                    original_text="Short",
                    audio_path="",
                    confidence_score=0.9
                )
            ],
            speaker_count=1,
            confidence_scores={"SPEAKER_00": 0.9}
        )
        
        segments = self.processor._extract_speaker_segments(
            self.audio_data, self.sample_rate, short_segments
        )
        
        # Le segment court devrait être ignoré
        assert len(segments) == 0 or len(segments.get("SPEAKER_00", [])) == 0
    
    def test_apply_fade(self):
        """Test d'application du fade."""
        # Créer un signal de test
        test_signal = np.ones(1000)  # Signal constant
        
        faded_signal = self.processor._apply_fade(test_signal, self.sample_rate)
        
        # Vérifier que le fade a été appliqué
        fade_samples = int(self.processor.fade_duration * self.sample_rate)
        
        # Le début devrait commencer à 0 et augmenter
        assert faded_signal[0] == 0.0
        assert faded_signal[fade_samples - 1] < 1.0
        
        # La fin devrait diminuer vers 0
        assert faded_signal[-1] == 0.0
        assert faded_signal[-fade_samples] < 1.0
    
    def test_apply_fade_short_signal(self):
        """Test de fade sur un signal trop court."""
        short_signal = np.ones(10)  # Signal très court
        
        faded_signal = self.processor._apply_fade(short_signal, self.sample_rate)
        
        # Le signal devrait être inchangé
        assert np.array_equal(faded_signal, short_signal)
    
    def test_validate_segment_quality(self):
        """Test de validation de qualité des segments."""
        # Créer des segments de test
        segments = {
            "SPEAKER_00": [
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=3.0,
                    audio_data=np.random.randn(32000) * 0.5,
                    sample_rate=16000,
                    confidence_score=0.9,
                    segment_index=0
                )
            ],
            "SPEAKER_01": [
                AudioSegment(
                    speaker_id="SPEAKER_01",
                    start_time=4.0,
                    end_time=6.0,
                    audio_data=np.random.randn(32000) * 0.1,  # Niveau plus faible
                    sample_rate=16000,
                    confidence_score=0.3,  # Confiance faible
                    segment_index=1
                )
            ]
        }
        
        quality_metrics = self.processor._validate_segment_quality(segments)
        
        # Vérifier la structure des métriques
        assert "total_speakers" in quality_metrics
        assert "total_segments" in quality_metrics
        assert "speaker_statistics" in quality_metrics
        assert "quality_warnings" in quality_metrics
        
        assert quality_metrics["total_speakers"] == 2
        assert quality_metrics["total_segments"] == 2
        
        # Vérifier les statistiques par locuteur
        speaker_00_stats = quality_metrics["speaker_statistics"]["SPEAKER_00"]
        assert speaker_00_stats["segment_count"] == 1
        assert speaker_00_stats["total_duration"] == 2.0
        assert speaker_00_stats["average_confidence"] == 0.9
        
        # Vérifier les avertissements de qualité
        warnings = quality_metrics["quality_warnings"]
        assert any("Low confidence for speaker SPEAKER_01" in w for w in warnings)
    
    def test_concatenate_segments_with_gaps(self):
        """Test de concaténation avec silences."""
        segments = [
            AudioSegment(
                speaker_id="SPEAKER_00",
                start_time=1.0,
                end_time=2.0,
                audio_data=np.ones(16000),  # 1 seconde à 16kHz
                sample_rate=16000,
                confidence_score=0.9,
                segment_index=0
            ),
            AudioSegment(
                speaker_id="SPEAKER_00",
                start_time=3.0,  # Gap de 1 seconde
                end_time=4.0,
                audio_data=np.ones(16000),  # 1 seconde à 16kHz
                sample_rate=16000,
                confidence_score=0.9,
                segment_index=1
            )
        ]
        
        concatenated = self.processor._concatenate_segments_with_gaps(segments, 16000)
        
        # Vérifier la longueur (2 segments + silence limité)
        expected_length = 2 * 16000 + int(self.processor.max_gap_duration * 16000)
        assert len(concatenated) == expected_length
    
    def test_normalize_audio(self):
        """Test de normalisation audio."""
        # Créer un signal avec un niveau spécifique
        test_signal = np.random.randn(1000) * 0.1  # Niveau faible
        
        normalized = self.processor._normalize_audio(test_signal)
        
        # Vérifier que le niveau RMS a augmenté
        original_rms = np.sqrt(np.mean(test_signal ** 2))
        normalized_rms = np.sqrt(np.mean(normalized ** 2))
        
        assert normalized_rms > original_rms
        assert normalized_rms <= 0.95  # Pas de saturation
    
    def test_normalize_audio_empty(self):
        """Test de normalisation sur signal vide."""
        empty_signal = np.array([])
        normalized = self.processor._normalize_audio(empty_signal)
        assert len(normalized) == 0
    
    def test_normalize_audio_silent(self):
        """Test de normalisation sur signal silencieux."""
        silent_signal = np.zeros(1000)
        normalized = self.processor._normalize_audio(silent_signal)
        assert np.array_equal(normalized, silent_signal)
    
    @patch('ai_video_dubbing.processors.speaker_segmentation.sf')
    def test_save_audio_wav(self, mock_sf):
        """Test de sauvegarde audio WAV."""
        audio_data = np.random.randn(1000)
        sample_rate = 16000
        output_path = "test.wav"
        
        self.processor._save_audio(audio_data, sample_rate, output_path, "wav")
        
        mock_sf.write.assert_called_once_with(
            output_path, audio_data, sample_rate, subtype='PCM_16'
        )
    
    def test_save_audio_missing_soundfile(self):
        """Test de sauvegarde sans soundfile."""
        with patch('ai_video_dubbing.processors.speaker_segmentation.sf', None):
            try:
                self.processor._save_audio(np.array([]), 16000, "test.wav", "wav")
                assert False, "Devrait lever ProcessingError"
            except ProcessingError as e:
                assert "soundfile is required" in str(e)
    
    def test_create_segment_mapping(self):
        """Test de création du mapping des segments."""
        mapping = self.processor._create_segment_mapping(self.speaker_segments)
        
        assert "SPEAKER_00" in mapping
        assert "SPEAKER_01" in mapping
        assert len(mapping["SPEAKER_00"]) == 2
        assert len(mapping["SPEAKER_01"]) == 1
        
        # Vérifier l'ordre chronologique
        speaker_00_segments = mapping["SPEAKER_00"]
        assert speaker_00_segments[0].start_time < speaker_00_segments[1].start_time
    
    def test_calculate_duration_statistics(self):
        """Test de calcul des statistiques de durée."""
        segments = {
            "SPEAKER_00": [
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=3.0,
                    audio_data=np.array([]),
                    sample_rate=16000,
                    confidence_score=0.9,
                    segment_index=0
                ),
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=7.0,
                    end_time=9.0,
                    audio_data=np.array([]),
                    sample_rate=16000,
                    confidence_score=0.85,
                    segment_index=1
                )
            ]
        }
        
        stats = self.processor._calculate_duration_statistics(segments)
        
        assert "SPEAKER_00" in stats
        assert stats["SPEAKER_00"] == 4.0  # (3-1) + (9-7) = 4 secondes
    
    def test_segment_audio_by_speaker_no_segments(self):
        """Test avec aucun segment."""
        empty_segments = SpeakerSegments(
            segments=[],
            speaker_count=0,
            confidence_scores={}
        )
        
        try:
            self.processor.segment_audio_by_speaker("test.wav", empty_segments)
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "No speaker segments provided" in str(e)
    
    def test_segment_audio_by_speaker_missing_file(self):
        """Test avec fichier audio manquant."""
        try:
            self.processor.segment_audio_by_speaker(
                "nonexistent.wav", self.speaker_segments
            )
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "Audio file not found" in str(e)
    
    def test_extract_speaker_samples(self):
        """Test d'extraction d'échantillons par locuteur."""
        segments = {
            "SPEAKER_00": [
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=4.0,  # 3 secondes
                    audio_data=np.random.randn(48000),
                    sample_rate=16000,
                    confidence_score=0.9,
                    segment_index=0
                ),
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=7.0,
                    end_time=10.0,  # 3 secondes
                    audio_data=np.random.randn(48000),
                    sample_rate=16000,
                    confidence_score=0.8,
                    segment_index=1
                )
            ]
        }
        
        with patch.object(self.processor, '_save_audio') as mock_save:
            samples = self.processor.extract_speaker_samples(
                segments, sample_duration=5.0, min_quality_threshold=0.7
            )
        
        assert "SPEAKER_00" in samples
        assert len(samples["SPEAKER_00"]) == 2  # Deux échantillons
        assert mock_save.call_count == 2
    
    def test_extract_speaker_samples_low_quality(self):
        """Test d'extraction avec segments de faible qualité."""
        segments = {
            "SPEAKER_00": [
                AudioSegment(
                    speaker_id="SPEAKER_00",
                    start_time=1.0,
                    end_time=4.0,
                    audio_data=np.random.randn(48000),
                    sample_rate=16000,
                    confidence_score=0.5,  # Confiance trop faible
                    segment_index=0
                )
            ]
        }
        
        samples = self.processor.extract_speaker_samples(
            segments, sample_duration=5.0, min_quality_threshold=0.7
        )
        
        # Aucun échantillon ne devrait être extrait
        assert len(samples) == 0 or len(samples.get("SPEAKER_00", [])) == 0