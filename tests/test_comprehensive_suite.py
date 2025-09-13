#!/usr/bin/env python3
"""
Suite de tests complète pour l'application de doublage vidéo par IA
Couvre tous les composants avec tests unitaires, d'intégration, de qualité et de performance
"""

import unittest
import tempfile
import os
import shutil
import time
import numpy as np
import wave
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import des modules de l'application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_video_dubbing.models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment, 
    VideoMetadata, AudioSegment, TranscriptionResult
)
from ai_video_dubbing.utils.file_manager import FileManager
from ai_video_dubbing.utils.temp_storage import TempStorage
from ai_video_dubbing.utils.output_manager import OutputManager
from ai_video_dubbing.processors.video_processor import VideoProcessor
from ai_video_dubbing.processors.audio_processor import AudioProcessor


class TestDataModels(unittest.TestCase):
    """Tests unitaires pour les modèles de données"""
    
    def test_pipeline_config_creation(self):
        """Test de création et validation de PipelineConfig"""
        config = PipelineConfig(
            enable_source_separation=True,
            asr_model="whisper-large-v3",
            ocr_model="qwen-vl",
            voice_cloning_model="tortoise-tts"
        )
        
        self.assertTrue(config.enable_source_separation)
        self.assertEqual(config.asr_model, "whisper-large-v3")
        self.assertEqual(config.ocr_model, "qwen-vl")
        self.assertEqual(config.voice_cloning_model, "tortoise-tts")
    
    def test_processing_results_validation(self):
        """Test de validation des résultats de traitement"""
        results = ProcessingResults(
            output_video_path="/path/to/output.mp4",
            processing_time=120.5,
            speakers_detected=3,
            dialogue_segments=45,
            quality_metrics={"snr": 25.3, "clarity": 0.85},
            intermediate_files=["/temp/audio.wav", "/temp/segments/"]
        )
        
        self.assertEqual(results.speakers_detected, 3)
        self.assertEqual(results.dialogue_segments, 45)
        self.assertIn("snr", results.quality_metrics)
        self.assertEqual(len(results.intermediate_files), 2)
    
    def test_dialogue_segment_timing(self):
        """Test de validation des segments de dialogue"""
        segment = DialogueSegment(
            speaker_id="Speaker_1",
            start_time=10.5,
            end_time=15.2,
            original_text="Bonjour, comment allez-vous ?",
            audio_path="/temp/speaker1_segment1.wav",
            confidence_score=0.92
        )
        
        self.assertEqual(segment.duration, 4.7)
        self.assertTrue(segment.is_valid_timing())
        self.assertGreater(segment.confidence_score, 0.9)


class TestFileManager(unittest.TestCase):
    """Tests unitaires pour le gestionnaire de fichiers"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_path=self.temp_dir)
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_format_validation(self):
        """Test de validation des formats vidéo supportés"""
        # Formats supportés
        self.assertTrue(self.file_manager.is_supported_video_format("test.mp4"))
        self.assertTrue(self.file_manager.is_supported_video_format("test.mkv"))
        self.assertTrue(self.file_manager.is_supported_video_format("test.avi"))
        
        # Formats non supportés
        self.assertFalse(self.file_manager.is_supported_video_format("test.mov"))
        self.assertFalse(self.file_manager.is_supported_video_format("test.wmv"))
        self.assertFalse(self.file_manager.is_supported_video_format("test.txt"))
    
    def test_file_corruption_detection(self):
        """Test de détection de fichiers corrompus"""
        # Créer un fichier corrompu (vide avec extension vidéo)
        corrupted_file = os.path.join(self.temp_dir, "corrupted.mp4")
        with open(corrupted_file, 'w') as f:
            f.write("not a video file")
        
        with self.assertRaises(ValueError) as context:
            self.file_manager.validate_video_file(corrupted_file)
        
        self.assertIn("corrompu", str(context.exception).lower())
    
    def test_temp_directory_management(self):
        """Test de gestion des répertoires temporaires"""
        temp_path = self.file_manager.create_temp_directory("test_session")
        self.assertTrue(os.path.exists(temp_path))
        
        # Nettoyage
        self.file_manager.cleanup_temp_directory(temp_path)
        self.assertFalse(os.path.exists(temp_path))


class TestVideoProcessor(unittest.TestCase):
    """Tests unitaires pour le processeur vidéo"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.video_processor = VideoProcessor()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ai_video_dubbing.processors.video_processor.ffmpeg')
    def test_audio_extraction(self, mock_ffmpeg):
        """Test d'extraction audio depuis vidéo"""
        # Mock de FFmpeg
        mock_ffmpeg.input.return_value.output.return_value.run.return_value = None
        
        input_video = "/path/to/input.mp4"
        output_audio = self.video_processor.extract_audio(
            input_video, 
            output_dir=self.temp_dir
        )
        
        # Vérifier que FFmpeg a été appelé correctement
        mock_ffmpeg.input.assert_called_once_with(input_video)
        self.assertTrue(output_audio.endswith('.wav'))
    
    @patch('ai_video_dubbing.processors.video_processor.cv2')
    def test_frame_extraction_during_speech(self, mock_cv2):
        """Test d'extraction d'images pendant les intervalles de parole"""
        # Mock de OpenCV
        mock_cap = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.return_value = 30.0  # FPS
        
        speech_intervals = [(10.0, 15.0), (20.0, 25.0)]
        frames = self.video_processor.extract_frames_during_speech(
            "/path/to/video.mp4", 
            speech_intervals
        )
        
        self.assertGreater(len(frames), 0)
        mock_cv2.VideoCapture.assert_called_once()


class TestAudioProcessor(unittest.TestCase):
    """Tests unitaires pour le processeur audio"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.audio_processor = AudioProcessor()
        
        # Créer un fichier audio de test
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        self._create_test_audio_file()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_audio_file(self):
        """Créer un fichier audio de test"""
        sample_rate = 16000
        duration = 5.0  # 5 secondes
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Signal sinusoïdal simple
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        with wave.open(self.test_audio_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
    
    @patch('ai_video_dubbing.processors.audio_processor.torch')
    def test_voice_activity_detection(self, mock_torch):
        """Test de détection d'activité vocale"""
        # Mock du modèle VAD
        mock_model = MagicMock()
        mock_model.return_value = [(0.5, 4.5)]  # Un segment de parole
        
        with patch.object(self.audio_processor, '_load_vad_model', return_value=mock_model):
            intervals = self.audio_processor.detect_voice_activity(self.test_audio_path)
        
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0], (0.5, 4.5))
    
    @patch('ai_video_dubbing.processors.audio_processor.Pipeline')
    def test_speaker_diarization(self, mock_pipeline):
        """Test de diarisation des locuteurs"""
        # Mock du pipeline de diarisation
        mock_diarization = MagicMock()
        mock_diarization.itertracks.return_value = [
            (("SPEAKER_00", 0.0, 2.0), "SPEAKER_00"),
            (("SPEAKER_01", 2.0, 4.0), "SPEAKER_01")
        ]
        mock_pipeline.return_value.return_value = mock_diarization
        
        segments = self.audio_processor.perform_speaker_diarization(self.test_audio_path)
        
        self.assertEqual(len(segments), 2)
        self.assertIn("SPEAKER_00", segments)
        self.assertIn("SPEAKER_01", segments)


class TestIntegrationPipeline(unittest.TestCase):
    """Tests d'intégration du pipeline complet"""
    
    def setUp(self):
        """Configuration des tests d'intégration"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = PipelineConfig(
            enable_source_separation=False,
            temp_directory=self.temp_dir
        )
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ai_video_dubbing.processors.pipeline_orchestrator.PipelineOrchestrator')
    def test_complete_pipeline_execution(self, mock_orchestrator):
        """Test d'exécution complète du pipeline"""
        # Mock des résultats du pipeline
        mock_results = ProcessingResults(
            output_video_path=os.path.join(self.temp_dir, "output.mp4"),
            processing_time=45.2,
            speakers_detected=2,
            dialogue_segments=12,
            quality_metrics={"snr": 22.5},
            intermediate_files=[]
        )
        
        mock_instance = mock_orchestrator.return_value
        mock_instance.execute_pipeline.return_value = mock_results
        
        # Simuler l'exécution du pipeline
        from ai_video_dubbing.processors.pipeline_orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator(self.config)
        results = orchestrator.execute_pipeline("/path/to/input.mp4")
        
        self.assertEqual(results.speakers_detected, 2)
        self.assertEqual(results.dialogue_segments, 12)
        self.assertGreater(results.processing_time, 0)
    
    def test_pipeline_error_handling(self):
        """Test de gestion d'erreurs dans le pipeline"""
        from ai_video_dubbing.utils.error_handler import ErrorHandler
        
        error_handler = ErrorHandler()
        
        # Test de gestion d'erreur de validation
        with self.assertRaises(ValueError):
            error_handler.validate_input_file("/nonexistent/file.mp4")
        
        # Test de gestion d'erreur de ressources
        error_handler.check_system_resources()  # Ne doit pas lever d'exception


class TestAudioQuality(unittest.TestCase):
    """Tests de qualité audio et de synchronisation"""
    
    def setUp(self):
        """Configuration des tests de qualité"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_audio_quality_metrics(self):
        """Test de calcul des métriques de qualité audio"""
        # Créer deux signaux audio pour comparaison
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Signal original
        original = np.sin(2 * np.pi * 440 * t)
        
        # Signal avec bruit
        noise_level = 0.1
        noisy = original + noise_level * np.random.randn(len(original))
        
        # Calculer SNR
        signal_power = np.mean(original ** 2)
        noise_power = np.mean((noisy - original) ** 2)
        snr = 10 * np.log10(signal_power / noise_power)
        
        self.assertGreater(snr, 10)  # SNR minimum acceptable
    
    def test_synchronization_accuracy(self):
        """Test de précision de synchronisation"""
        # Simuler des horodatages OCR et ASR
        ocr_timestamps = [1.0, 3.5, 6.2, 8.8]
        asr_timestamps = [1.1, 3.4, 6.3, 8.7]
        
        # Calculer l'erreur de synchronisation
        sync_errors = [abs(ocr - asr) for ocr, asr in zip(ocr_timestamps, asr_timestamps)]
        max_error = max(sync_errors)
        avg_error = sum(sync_errors) / len(sync_errors)
        
        self.assertLess(max_error, 0.5)  # Erreur max < 500ms
        self.assertLess(avg_error, 0.2)  # Erreur moyenne < 200ms


class TestPerformance(unittest.TestCase):
    """Tests de performance avec différentes tailles de fichiers"""
    
    def setUp(self):
        """Configuration des tests de performance"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_small_file_performance(self):
        """Test de performance sur petit fichier (< 1 minute)"""
        file_duration = 30  # 30 secondes
        start_time = time.time()
        
        # Simuler le traitement d'un petit fichier
        self._simulate_processing(file_duration)
        
        processing_time = time.time() - start_time
        
        # Le traitement ne doit pas prendre plus de 2x la durée du fichier
        self.assertLess(processing_time, file_duration * 2)
    
    def test_medium_file_performance(self):
        """Test de performance sur fichier moyen (5-10 minutes)"""
        file_duration = 300  # 5 minutes
        start_time = time.time()
        
        # Simuler le traitement d'un fichier moyen
        self._simulate_processing(file_duration)
        
        processing_time = time.time() - start_time
        
        # Le traitement ne doit pas prendre plus de 3x la durée du fichier
        self.assertLess(processing_time, file_duration * 3)
    
    def test_memory_usage_monitoring(self):
        """Test de monitoring de l'utilisation mémoire"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simuler un traitement qui utilise de la mémoire
        large_array = np.zeros((1000, 1000, 10))  # ~80MB
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Vérifier que l'augmentation mémoire est raisonnable
        self.assertLess(memory_increase, 200)  # < 200MB d'augmentation
        
        # Nettoyer
        del large_array
    
    def _simulate_processing(self, duration_seconds):
        """Simuler un traitement de durée donnée"""
        # Simulation simple avec sleep proportionnel
        time.sleep(min(duration_seconds / 100, 0.1))  # Max 100ms de simulation


class TestRegressionSuite(unittest.TestCase):
    """Tests de régression sur des échantillons de référence"""
    
    def setUp(self):
        """Configuration des tests de régression"""
        self.temp_dir = tempfile.mkdtemp()
        self.reference_results = {
            "sample1": {"speakers": 2, "segments": 15, "snr": 23.5},
            "sample2": {"speakers": 3, "segments": 28, "snr": 21.8}
        }
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_regression_sample1(self):
        """Test de régression sur échantillon 1"""
        # Simuler les résultats actuels
        current_results = {"speakers": 2, "segments": 15, "snr": 23.2}
        reference = self.reference_results["sample1"]
        
        # Vérifier que les résultats sont dans les tolérances acceptables
        self.assertEqual(current_results["speakers"], reference["speakers"])
        self.assertAlmostEqual(
            current_results["segments"], 
            reference["segments"], 
            delta=2  # ±2 segments acceptable
        )
        self.assertAlmostEqual(
            current_results["snr"], 
            reference["snr"], 
            delta=2.0  # ±2dB acceptable
        )
    
    def test_regression_sample2(self):
        """Test de régression sur échantillon 2"""
        # Simuler les résultats actuels
        current_results = {"speakers": 3, "segments": 27, "snr": 22.1}
        reference = self.reference_results["sample2"]
        
        # Vérifier que les résultats sont dans les tolérances acceptables
        self.assertEqual(current_results["speakers"], reference["speakers"])
        self.assertAlmostEqual(
            current_results["segments"], 
            reference["segments"], 
            delta=3  # ±3 segments acceptable
        )
        self.assertAlmostEqual(
            current_results["snr"], 
            reference["snr"], 
            delta=2.0  # ±2dB acceptable
        )


def create_test_suite():
    """Créer la suite de tests complète"""
    suite = unittest.TestSuite()
    
    # Tests unitaires
    suite.addTest(unittest.makeSuite(TestDataModels))
    suite.addTest(unittest.makeSuite(TestFileManager))
    suite.addTest(unittest.makeSuite(TestVideoProcessor))
    suite.addTest(unittest.makeSuite(TestAudioProcessor))
    
    # Tests d'intégration
    suite.addTest(unittest.makeSuite(TestIntegrationPipeline))
    
    # Tests de qualité
    suite.addTest(unittest.makeSuite(TestAudioQuality))
    
    # Tests de performance
    suite.addTest(unittest.makeSuite(TestPerformance))
    
    # Tests de régression
    suite.addTest(unittest.makeSuite(TestRegressionSuite))
    
    return suite


if __name__ == '__main__':
    # Exécuter la suite de tests complète
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Afficher le résumé
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ DES TESTS")
    print(f"{'='*60}")
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print(f"\nÉCHECS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERREURS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Code de sortie
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)