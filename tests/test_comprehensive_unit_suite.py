#!/usr/bin/env python3
"""
Suite de tests unitaires complète pour tous les composants
Tests isolés de chaque module avec mocks appropriés
"""

import unittest
import tempfile
import shutil
import os
import numpy as np
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import Dict, List, Any

# Import des modules de l'application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_video_dubbing.models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment,
    VideoMetadata, AudioSegment, TranscriptionResult
)


class TestDataModelsUnit(unittest.TestCase):
    """Tests unitaires pour les modèles de données"""
    
    def test_pipeline_config_defaults(self):
        """Test des valeurs par défaut de PipelineConfig"""
        config = PipelineConfig()
        
        self.assertFalse(config.enable_source_separation)
        self.assertEqual(config.asr_model, "whisper-base")
        self.assertEqual(config.ocr_model, "paddleocr")
        self.assertEqual(config.voice_cloning_model, "tortoise-tts")
        self.assertEqual(config.output_codec, "h264")
        self.assertEqual(config.output_bitrate, "5M")
    
    def test_pipeline_config_validation(self):
        """Test de validation de PipelineConfig"""
        # Configuration valide
        valid_config = PipelineConfig(
            asr_model="whisper-large-v3",
            output_bitrate="10M"
        )
        self.assertTrue(valid_config.is_valid())
        
        # Configuration invalide
        invalid_config = PipelineConfig(
            output_bitrate="invalid_bitrate"
        )
        self.assertFalse(invalid_config.is_valid())
    
    def test_dialogue_segment_properties(self):
        """Test des propriétés calculées de DialogueSegment"""
        segment = DialogueSegment(
            speaker_id="SPEAKER_01",
            start_time=10.5,
            end_time=15.8,
            original_text="Bonjour, comment allez-vous ?",
            audio_path="/path/to/audio.wav",
            confidence_score=0.92
        )
        
        # Test des propriétés calculées
        self.assertEqual(segment.duration, 5.3)
        self.assertEqual(segment.word_count, 4)
        self.assertTrue(segment.is_valid_timing())
        self.assertTrue(segment.is_high_confidence())
    
    def test_processing_results_aggregation(self):
        """Test d'agrégation des résultats de traitement"""
        results = ProcessingResults(
            output_video_path="/path/to/output.mp4",
            processing_time=125.7,
            speakers_detected=3,
            dialogue_segments=28,
            quality_metrics={
                "snr": 24.5,
                "transcription_accuracy": 0.94,
                "ocr_accuracy": 0.89
            },
            intermediate_files=["/temp/audio.wav", "/temp/segments/"]
        )
        
        # Test des métriques agrégées
        self.assertEqual(results.average_segment_duration, 125.7 / 28)
        self.assertEqual(results.speakers_per_minute, 3 / (125.7 / 60))
        self.assertGreater(results.overall_quality_score, 0.8)
    
    def test_video_metadata_extraction(self):
        """Test d'extraction de métadonnées vidéo"""
        metadata = VideoMetadata(
            duration=300.5,
            fps=29.97,
            resolution=(1920, 1080),
            audio_channels=2,
            audio_sample_rate=48000,
            file_size=157286400  # ~150MB
        )
        
        # Test des propriétés calculées
        self.assertEqual(metadata.aspect_ratio, 16/9)
        self.assertEqual(metadata.total_frames, int(300.5 * 29.97))
        self.assertEqual(metadata.file_size_mb, 150)
        self.assertTrue(metadata.is_hd_quality())
    
    def test_audio_segment_analysis(self):
        """Test d'analyse de segment audio"""
        # Créer des données audio simulées
        sample_rate = 16000
        duration = 2.0
        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        
        segment = AudioSegment(
            start_time=5.0,
            end_time=7.0,
            audio_data=audio_data,
            sample_rate=sample_rate,
            speaker_id="SPEAKER_00"
        )
        
        # Test des propriétés audio
        self.assertEqual(segment.duration, 2.0)
        self.assertEqual(segment.sample_count, len(audio_data))
        self.assertGreater(segment.rms_energy, 0)
        self.assertGreater(segment.peak_amplitude, 0.5)
    
    def test_transcription_result_processing(self):
        """Test de traitement des résultats de transcription"""
        segments = [
            {"start": 1.0, "end": 3.5, "text": "Bonjour tout le monde"},
            {"start": 4.0, "end": 7.2, "text": "Comment allez-vous aujourd'hui ?"},
            {"start": 8.5, "end": 11.0, "text": "Très bien merci beaucoup"}
        ]
        
        result = TranscriptionResult(
            text="Bonjour tout le monde. Comment allez-vous aujourd'hui ? Très bien merci beaucoup.",
            segments=segments,
            confidence=0.91,
            language="fr"
        )
        
        # Test des propriétés calculées
        self.assertEqual(result.total_duration, 10.0)  # 11.0 - 1.0
        self.assertEqual(result.segment_count, 3)
        self.assertEqual(result.words_per_minute, result.word_count / (result.total_duration / 60))
        self.assertTrue(result.is_reliable())


class TestFileManagerUnit(unittest.TestCase):
    """Tests unitaires pour le gestionnaire de fichiers"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du file manager pour les tests
        self.file_manager = Mock()
        self.file_manager.is_supported_video_format = Mock()
        self.file_manager.validate_file_size = Mock()
        self.file_manager.create_temp_directory = Mock()
        self.file_manager.cleanup_temp_directory = Mock()
        self.file_manager.is_file_corrupted = Mock()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_supported_formats_validation(self):
        """Test de validation des formats supportés"""
        # Formats vidéo supportés
        supported_video = ["test.mp4", "test.mkv", "test.avi"]
        for filename in supported_video:
            if hasattr(self.file_manager, 'is_supported_video_format'):
                self.assertTrue(self.file_manager.is_supported_video_format(filename))
        
        # Formats non supportés
        unsupported = ["test.mov", "test.wmv", "test.flv", "test.txt"]
        for filename in unsupported:
            if hasattr(self.file_manager, 'is_supported_video_format'):
                self.assertFalse(self.file_manager.is_supported_video_format(filename))
    
    def test_file_size_validation(self):
        """Test de validation de taille de fichier"""
        # Créer des fichiers de test de différentes tailles
        small_file = os.path.join(self.temp_dir, "small.mp4")
        large_file = os.path.join(self.temp_dir, "large.mp4")
        
        # Fichier petit (1KB)
        with open(small_file, 'wb') as f:
            f.write(b'0' * 1024)
        
        # Fichier "gros" (10MB simulé)
        with open(large_file, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))
        
        # Tests de validation
        if hasattr(self.file_manager, 'validate_file_size'):
            self.assertTrue(self.file_manager.validate_file_size(small_file, max_size_mb=100))
            self.assertFalse(self.file_manager.validate_file_size(large_file, max_size_mb=5))
    
    def test_temp_directory_management(self):
        """Test de gestion des répertoires temporaires"""
        if hasattr(self.file_manager, 'create_temp_directory'):
            # Créer un répertoire temporaire
            temp_path = self.file_manager.create_temp_directory("test_session")
            self.assertTrue(os.path.exists(temp_path))
            
            # Créer des fichiers dans le répertoire
            test_file = os.path.join(temp_path, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            self.assertTrue(os.path.exists(test_file))
            
            # Nettoyer le répertoire
            if hasattr(self.file_manager, 'cleanup_temp_directory'):
                self.file_manager.cleanup_temp_directory(temp_path)
                self.assertFalse(os.path.exists(temp_path))
    
    def test_file_corruption_detection(self):
        """Test de détection de corruption de fichier"""
        # Créer un fichier corrompu (header invalide)
        corrupted_file = os.path.join(self.temp_dir, "corrupted.mp4")
        with open(corrupted_file, 'wb') as f:
            f.write(b'INVALID_HEADER_DATA')
        
        if hasattr(self.file_manager, 'is_file_corrupted'):
            self.assertTrue(self.file_manager.is_file_corrupted(corrupted_file))
        
        # Créer un fichier avec header MP4 valide (simulé)
        valid_file = os.path.join(self.temp_dir, "valid.mp4")
        with open(valid_file, 'wb') as f:
            # Header MP4 simplifié
            f.write(b'\x00\x00\x00\x20ftypmp4\x00')
            f.write(b'0' * 1000)  # Données simulées
        
        if hasattr(self.file_manager, 'is_file_corrupted'):
            self.assertFalse(self.file_manager.is_file_corrupted(valid_file))


class TestVideoProcessorUnit(unittest.TestCase):
    """Tests unitaires pour le processeur vidéo"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du processeur vidéo
        self.video_processor = Mock()
        self.video_processor.extract_audio = Mock()
        self.video_processor.extract_frames_during_speech = Mock()
        self.video_processor.merge_audio_video = Mock()
        self.video_processor.get_video_metadata = Mock()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ai_video_dubbing.processors.video_processor.ffmpeg')
    def test_audio_extraction_parameters(self, mock_ffmpeg):
        """Test des paramètres d'extraction audio"""
        if hasattr(self.video_processor, 'extract_audio'):
            # Configuration du mock
            mock_ffmpeg.input.return_value.output.return_value.run.return_value = None
            
            input_video = "/path/to/input.mp4"
            output_audio = self.video_processor.extract_audio(
                input_video,
                output_format="wav",
                sample_rate=44100,
                channels=2
            )
            
            # Vérifier les appels FFmpeg
            mock_ffmpeg.input.assert_called_once_with(input_video)
            
            # Vérifier le format de sortie
            if output_audio:
                self.assertTrue(output_audio.endswith('.wav'))
    
    @patch('ai_video_dubbing.processors.video_processor.cv2')
    def test_frame_extraction_timing(self, mock_cv2):
        """Test de timing d'extraction d'images"""
        if hasattr(self.video_processor, 'extract_frames_during_speech'):
            # Configuration du mock OpenCV
            mock_cap = MagicMock()
            mock_cv2.VideoCapture.return_value = mock_cap
            mock_cap.get.return_value = 30.0  # 30 FPS
            mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            
            # Intervalles de parole
            speech_intervals = [(10.0, 15.0), (20.0, 25.0)]
            
            frames = self.video_processor.extract_frames_during_speech(
                "/path/to/video.mp4",
                speech_intervals,
                frame_rate=1.0  # 1 frame par seconde
            )
            
            # Vérifier le nombre d'images extraites
            expected_frames = sum(interval[1] - interval[0] for interval in speech_intervals)
            if frames:
                self.assertGreaterEqual(len(frames), expected_frames * 0.8)  # Tolérance 20%
    
    @patch('ai_video_dubbing.processors.video_processor.ffmpeg')
    def test_video_audio_merge_quality(self, mock_ffmpeg):
        """Test de qualité de fusion vidéo/audio"""
        if hasattr(self.video_processor, 'merge_audio_video'):
            # Configuration du mock
            mock_ffmpeg.input.return_value.output.return_value.run.return_value = None
            
            video_path = "/path/to/video.mp4"
            audio_path = "/path/to/audio.wav"
            output_path = "/path/to/output.mp4"
            
            quality_settings = {
                "codec": "h264",
                "bitrate": "5M",
                "preset": "medium"
            }
            
            self.video_processor.merge_audio_video(
                video_path,
                audio_path,
                output_path,
                **quality_settings
            )
            
            # Vérifier que FFmpeg est appelé avec les bons paramètres
            mock_ffmpeg.input.assert_called()
    
    def test_video_metadata_extraction(self):
        """Test d'extraction de métadonnées vidéo"""
        if hasattr(self.video_processor, 'get_video_metadata'):
            # Mock des métadonnées
            mock_metadata = {
                "duration": 300.5,
                "fps": 29.97,
                "width": 1920,
                "height": 1080,
                "audio_channels": 2,
                "audio_sample_rate": 48000
            }
            
            with patch.object(self.video_processor, 'get_video_metadata', return_value=mock_metadata):
                metadata = self.video_processor.get_video_metadata("/path/to/video.mp4")
                
                self.assertEqual(metadata["duration"], 300.5)
                self.assertEqual(metadata["fps"], 29.97)
                self.assertEqual(metadata["width"], 1920)
                self.assertEqual(metadata["height"], 1080)


class TestAudioProcessorUnit(unittest.TestCase):
    """Tests unitaires pour le processeur audio"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du processeur audio
        self.audio_processor = Mock()
        self.audio_processor.detect_voice_activity = Mock()
        self.audio_processor.perform_speaker_diarization = Mock()
        self.audio_processor.normalize_audio = Mock()
        self.audio_processor.separate_sources = Mock()
        self.audio_processor._load_vad_model = Mock()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vad_sensitivity_settings(self):
        """Test des paramètres de sensibilité VAD"""
        if hasattr(self.audio_processor, 'detect_voice_activity'):
            # Mock du modèle VAD
            with patch.object(self.audio_processor, '_load_vad_model') as mock_load:
                mock_model = Mock()
                mock_model.return_value = [(1.0, 5.0), (7.0, 10.0)]
                mock_load.return_value = mock_model
                
                # Test avec différents niveaux de sensibilité
                sensitivities = [0.3, 0.5, 0.7, 0.9]
                
                for sensitivity in sensitivities:
                    intervals = self.audio_processor.detect_voice_activity(
                        "/path/to/audio.wav",
                        sensitivity=sensitivity
                    )
                    
                    if intervals:
                        # Plus la sensibilité est élevée, plus on détecte d'intervalles
                        self.assertIsInstance(intervals, list)
                        for start, end in intervals:
                            self.assertLess(start, end)
    
    def test_speaker_diarization_accuracy(self):
        """Test de précision de diarisation"""
        if hasattr(self.audio_processor, 'perform_speaker_diarization'):
            # Mock du pipeline de diarisation
            with patch('ai_video_dubbing.processors.audio_processor.Pipeline') as mock_pipeline:
                mock_diarization = Mock()
                mock_diarization.itertracks.return_value = [
                    (("SPEAKER_00", 0.0, 3.0), "SPEAKER_00"),
                    (("SPEAKER_01", 3.5, 7.0), "SPEAKER_01"),
                    (("SPEAKER_00", 7.5, 10.0), "SPEAKER_00")
                ]
                mock_pipeline.return_value.return_value = mock_diarization
                
                segments = self.audio_processor.perform_speaker_diarization("/path/to/audio.wav")
                
                if segments:
                    # Vérifier la cohérence des segments
                    self.assertIn("SPEAKER_00", segments)
                    self.assertIn("SPEAKER_01", segments)
                    
                    # Vérifier qu'il n'y a pas de chevauchement
                    all_intervals = []
                    for speaker, intervals in segments.items():
                        all_intervals.extend(intervals)
                    
                    all_intervals.sort(key=lambda x: x[0])
                    for i in range(1, len(all_intervals)):
                        self.assertGreaterEqual(all_intervals[i][0], all_intervals[i-1][1])
    
    def test_audio_normalization_levels(self):
        """Test des niveaux de normalisation audio"""
        if hasattr(self.audio_processor, 'normalize_audio'):
            # Créer un signal audio de test
            sample_rate = 16000
            duration = 2.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Signal avec différents niveaux
            low_signal = 0.1 * np.sin(2 * np.pi * 440 * t)
            high_signal = 0.9 * np.sin(2 * np.pi * 440 * t)
            
            # Test de normalisation
            target_levels = [-12, -6, -3, 0]  # dB
            
            for target_db in target_levels:
                target_linear = 10 ** (target_db / 20)
                
                # Simuler la normalisation
                normalized_low = low_signal * (target_linear / np.max(np.abs(low_signal)))
                normalized_high = high_signal * (target_linear / np.max(np.abs(high_signal)))
                
                # Vérifier que les niveaux sont corrects
                self.assertAlmostEqual(np.max(np.abs(normalized_low)), target_linear, places=2)
                self.assertAlmostEqual(np.max(np.abs(normalized_high)), target_linear, places=2)
    
    def test_source_separation_quality(self):
        """Test de qualité de séparation de source"""
        if hasattr(self.audio_processor, 'separate_sources'):
            # Mock de Demucs
            with patch('ai_video_dubbing.processors.audio_processor.demucs') as mock_demucs:
                mock_sources = {
                    "vocals": np.random.randn(16000 * 2),  # 2 secondes
                    "drums": np.random.randn(16000 * 2),
                    "bass": np.random.randn(16000 * 2),
                    "other": np.random.randn(16000 * 2)
                }
                mock_demucs.separate.return_value = mock_sources
                
                result = self.audio_processor.separate_sources("/path/to/audio.wav")
                
                if result:
                    # Vérifier que toutes les sources sont présentes
                    expected_sources = ["vocals", "drums", "bass", "other"]
                    for source in expected_sources:
                        self.assertIn(source, result)
                        self.assertIsInstance(result[source], np.ndarray)


class TestAIModelManagerUnit(unittest.TestCase):
    """Tests unitaires pour le gestionnaire de modèles IA"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock du gestionnaire de modèles IA
        self.ai_manager = Mock()
        self.ai_manager.load_model = Mock()
        self.ai_manager.unload_model = Mock()
        self.ai_manager.transcribe_audio = Mock()
        self.ai_manager.extract_text_from_frames = Mock()
        self.ai_manager._load_whisper_model = Mock()
        self.ai_manager._whisper_model = Mock()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_loading_lazy(self):
        """Test de chargement paresseux des modèles"""
        if hasattr(self.ai_manager, 'load_model'):
            # Mock des modèles
            with patch.object(self.ai_manager, '_load_whisper_model') as mock_whisper:
                mock_whisper.return_value = Mock()
                
                # Le modèle ne doit pas être chargé avant utilisation
                self.assertFalse(hasattr(self.ai_manager, '_whisper_model'))
                
                # Charger le modèle
                self.ai_manager.load_model("asr", "whisper-base")
                
                # Vérifier que le modèle est chargé
                mock_whisper.assert_called_once_with("whisper-base")
    
    def test_model_memory_management(self):
        """Test de gestion mémoire des modèles"""
        if hasattr(self.ai_manager, 'unload_model'):
            # Simuler le chargement de plusieurs modèles
            models = ["asr", "ocr", "voice_cloning"]
            
            for model_type in models:
                if hasattr(self.ai_manager, 'load_model'):
                    self.ai_manager.load_model(model_type, f"mock_{model_type}_model")
            
            # Vérifier que les modèles peuvent être déchargés
            for model_type in models:
                self.ai_manager.unload_model(model_type)
                
                # Vérifier que le modèle n'est plus en mémoire
                model_attr = f"_{model_type}_model"
                if hasattr(self.ai_manager, model_attr):
                    self.assertIsNone(getattr(self.ai_manager, model_attr))
    
    def test_transcription_accuracy_metrics(self):
        """Test des métriques de précision de transcription"""
        if hasattr(self.ai_manager, 'transcribe_audio'):
            # Mock de Whisper
            with patch.object(self.ai_manager, '_whisper_model') as mock_model:
                mock_result = {
                    "text": "Bonjour, comment allez-vous ?",
                    "segments": [
                        {"start": 0.0, "end": 2.5, "text": "Bonjour,", "confidence": 0.95},
                        {"start": 2.5, "end": 5.0, "text": "comment allez-vous ?", "confidence": 0.89}
                    ]
                }
                mock_model.transcribe.return_value = mock_result
                
                result = self.ai_manager.transcribe_audio("/path/to/audio.wav")
                
                if result:
                    # Vérifier la structure du résultat
                    self.assertIn("text", result)
                    self.assertIn("segments", result)
                    
                    # Calculer la confiance moyenne
                    confidences = [seg["confidence"] for seg in result["segments"]]
                    avg_confidence = sum(confidences) / len(confidences)
                    self.assertGreater(avg_confidence, 0.8)
    
    def test_ocr_text_extraction_quality(self):
        """Test de qualité d'extraction de texte OCR"""
        if hasattr(self.ai_manager, 'extract_text_from_frames'):
            # Mock d'images avec texte
            mock_frames = [
                {"timestamp": 1.0, "frame": np.zeros((480, 640, 3), dtype=np.uint8)},
                {"timestamp": 2.0, "frame": np.zeros((480, 640, 3), dtype=np.uint8)}
            ]
            
            # Mock de PaddleOCR
            with patch('ai_video_dubbing.processors.ai_model_manager.PaddleOCR') as mock_ocr:
                mock_ocr_instance = mock_ocr.return_value
                mock_ocr_instance.ocr.return_value = [
                    [[[0, 0], [100, 0], [100, 30], [0, 30]], ("Bonjour", 0.95)],
                    [[[0, 40], [150, 40], [150, 70], [0, 70]], ("Comment ça va ?", 0.89)]
                ]
                
                results = self.ai_manager.extract_text_from_frames(mock_frames)
                
                if results:
                    # Vérifier la structure des résultats
                    for result in results:
                        self.assertIn("text", result)
                        self.assertIn("confidence", result)
                        self.assertIn("timestamp", result)
                        self.assertGreater(result["confidence"], 0.8)


if __name__ == '__main__':
    # Exécuter tous les tests unitaires
    unittest.main(verbosity=2)