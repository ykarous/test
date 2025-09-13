#!/usr/bin/env python3
"""
Test basique pour vérifier que les composants de test fonctionnent
"""

import unittest
import tempfile
import shutil
import os
import sys

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(__file__))

from ai_video_dubbing.models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment,
    VideoMetadata, AudioSegment, TranscriptionResult
)


class TestBasicFunctionality(unittest.TestCase):
    """Tests basiques pour vérifier le fonctionnement"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_config_creation(self):
        """Test de création de PipelineConfig"""
        config = PipelineConfig(
            enable_source_separation=True,
            asr_model="whisper-large-v3"
        )
        
        self.assertTrue(config.enable_source_separation)
        self.assertEqual(config.asr_model, "whisper-large-v3")
        self.assertTrue(config.is_valid())
    
    def test_pipeline_config_validation(self):
        """Test de validation de PipelineConfig"""
        # Configuration valide
        valid_config = PipelineConfig(output_bitrate="10M")
        self.assertTrue(valid_config.is_valid())
        
        # Configuration invalide
        invalid_config = PipelineConfig(output_bitrate="invalid")
        self.assertFalse(invalid_config.is_valid())
    
    def test_processing_results_properties(self):
        """Test des propriétés calculées de ProcessingResults"""
        results = ProcessingResults(
            output_video_path="/path/to/output.mp4",
            processing_time=120.0,
            speakers_detected=3,
            dialogue_segments=24,
            quality_metrics={"snr": 25.0, "accuracy": 0.95}
        )
        
        self.assertEqual(results.average_segment_duration, 5.0)  # 120/24
        self.assertEqual(results.speakers_per_minute, 1.5)  # 3/(120/60)
        self.assertEqual(results.overall_quality_score, 12.975)  # (25.0 + 0.95)/2
    
    def test_dialogue_segment_properties(self):
        """Test des propriétés de DialogueSegment"""
        segment = DialogueSegment(
            speaker_id="SPEAKER_01",
            start_time=10.5,
            end_time=15.8,
            original_text="Bonjour, comment allez-vous ?",
            audio_path="/path/to/audio.wav",
            confidence_score=0.92
        )
        
        self.assertAlmostEqual(segment.duration, 5.3, places=1)
        self.assertEqual(segment.word_count, 4)
        self.assertTrue(segment.is_valid_timing())
        self.assertTrue(segment.is_high_confidence())
    
    def test_video_metadata_properties(self):
        """Test des propriétés de VideoMetadata"""
        metadata = VideoMetadata(
            duration=300.5,
            fps=29.97,
            resolution=(1920, 1080),
            audio_channels=2,
            audio_sample_rate=48000,
            file_size=157286400  # ~150MB
        )
        
        self.assertAlmostEqual(metadata.aspect_ratio, 16/9, places=2)
        self.assertEqual(metadata.total_frames, int(300.5 * 29.97))
        self.assertEqual(metadata.file_size_mb, 150)
        self.assertTrue(metadata.is_hd_quality())
    
    def test_transcription_result_properties(self):
        """Test des propriétés de TranscriptionResult"""
        from ai_video_dubbing.models.data_models import TranscriptionSegment
        
        segments = [
            TranscriptionSegment(text="Bonjour", start=1.0, end=2.5, confidence=0.95),
            TranscriptionSegment(text="Comment allez-vous ?", start=3.0, end=5.5, confidence=0.89)
        ]
        
        result = TranscriptionResult(
            text="Bonjour. Comment allez-vous ?",
            segments=segments,
            language="fr",
            confidence=0.92,
            word_count=4
        )
        
        self.assertEqual(result.total_duration, 4.5)  # 5.5 - 1.0
        self.assertEqual(result.segment_count, 2)
        self.assertAlmostEqual(result.words_per_minute, 53.33, places=1)  # 4 / (4.5/60)
        self.assertTrue(result.is_reliable())


if __name__ == '__main__':
    # Exécuter les tests basiques
    unittest.main(verbosity=2)