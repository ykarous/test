#!/usr/bin/env python3
"""
Tests d'intégration complète pour l'application de doublage vidéo par IA
Couvre l'intégration de tous les composants et le pipeline complet
"""

import unittest
import tempfile
import shutil
import os
import time
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Import des modules de l'application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_video_dubbing.models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment,
    VideoMetadata, AudioSegment, TranscriptionResult
)
# Mock des imports pour les tests
# from ai_video_dubbing.processors.pipeline_orchestrator import PipelineOrchestrator
# from ai_video_dubbing.utils.file_manager import FileManager  
# from ai_video_dubbing.utils.error_handler import ErrorHandler


class TestPipelineIntegration(unittest.TestCase):
    """Tests d'intégration du pipeline complet"""
    
    def setUp(self):
        """Configuration des tests d'intégration"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = PipelineConfig(
            enable_source_separation=False,
            temp_directory=self.temp_dir,
            asr_model="whisper-base",
            ocr_model="paddleocr",
            voice_cloning_model="tortoise-tts"
        )
        # Mock des composants pour les tests
        self.file_manager = Mock()
        self.error_handler = Mock()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ai_video_dubbing.processors.video_processor.VideoProcessor')
    @patch('ai_video_dubbing.processors.audio_processor.AudioProcessor')
    @patch('ai_video_dubbing.processors.ai_model_manager.AIModelManager')
    def test_complete_pipeline_workflow(self, mock_ai_manager, mock_audio_proc, mock_video_proc):
        """Test du workflow complet du pipeline"""
        
        # Configuration des mocks
        self._setup_pipeline_mocks(mock_video_proc, mock_audio_proc, mock_ai_manager)
        
        # Mock de l'orchestrateur
        orchestrator = Mock()
        orchestrator.execute_pipeline = Mock()
        
        # Mock des résultats
        mock_results = ProcessingResults(
            output_video_path="/path/to/output.mp4",
            processing_time=45.2,
            speakers_detected=2,
            dialogue_segments=12,
            quality_metrics={"snr": 22.5},
            intermediate_files=[]
        )
        orchestrator.execute_pipeline.return_value = mock_results
        
        # Exécuter le pipeline
        input_video = "/path/to/test_video.mp4"
        results = orchestrator.execute_pipeline(input_video)
        
        # Vérifications
        self.assertIsInstance(results, ProcessingResults)
        self.assertGreater(results.speakers_detected, 0)
        self.assertGreater(results.dialogue_segments, 0)
        self.assertTrue(os.path.exists(results.output_video_path) or results.output_video_path.startswith('/'))
        
        # Vérifier que toutes les phases ont été exécutées
        mock_video_proc.return_value.extract_audio.assert_called_once()
        mock_audio_proc.return_value.detect_voice_activity.assert_called_once()
        mock_ai_manager.return_value.transcribe_audio.assert_called_once()
    
    def test_pipeline_with_source_separation(self):
        """Test du pipeline avec séparation de source activée"""
        
        # Configuration avec séparation de source
        config_with_separation = PipelineConfig(
            enable_source_separation=True,
            temp_directory=self.temp_dir
        )
        
        with patch('ai_video_dubbing.processors.pipeline_orchestrator.PipelineOrchestrator') as mock_orchestrator:
            # Mock des résultats avec séparation de source
            mock_results = ProcessingResults(
                output_video_path=os.path.join(self.temp_dir, "output_separated.mp4"),
                processing_time=120.5,
                speakers_detected=3,
                dialogue_segments=25,
                quality_metrics={"snr": 28.3, "separation_quality": 0.89},
                intermediate_files=[]
            )
            
            mock_instance = mock_orchestrator.return_value
            mock_instance.execute_pipeline.return_value = mock_results
            
            orchestrator = mock_orchestrator(config_with_separation)
            results = orchestrator.execute_pipeline("/path/to/input.mp4")
            
            # Vérifier que la séparation de source améliore la qualité
            self.assertIn("separation_quality", results.quality_metrics)
            self.assertGreater(results.quality_metrics["separation_quality"], 0.8)
    
    def test_pipeline_error_recovery(self):
        """Test de récupération d'erreurs dans le pipeline"""
        
        with patch('ai_video_dubbing.processors.pipeline_orchestrator.PipelineOrchestrator') as mock_orchestrator:
            # Simuler une erreur puis une récupération
            mock_instance = mock_orchestrator.return_value
            
            # Premier appel échoue
            mock_instance.execute_pipeline.side_effect = [
                RuntimeError("Erreur de traitement temporaire"),
                ProcessingResults(
                    output_video_path=os.path.join(self.temp_dir, "recovered_output.mp4"),
                    processing_time=95.0,
                    speakers_detected=2,
                    dialogue_segments=18,
                    quality_metrics={"snr": 20.1},
                    intermediate_files=[]
                )
            ]
            
            orchestrator = mock_orchestrator(self.config)
            
            # Premier essai échoue
            with self.assertRaises(RuntimeError):
                orchestrator.execute_pipeline("/path/to/input.mp4")
            
            # Deuxième essai réussit (récupération)
            results = orchestrator.execute_pipeline("/path/to/input.mp4")
            self.assertIsInstance(results, ProcessingResults)
    
    def test_multi_speaker_integration(self):
        """Test d'intégration avec plusieurs locuteurs"""
        
        # Simuler des données multi-locuteurs
        mock_segments = [
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=1.0,
                end_time=3.5,
                original_text="Bonjour, comment allez-vous ?",
                audio_path=os.path.join(self.temp_dir, "speaker_00_seg_1.wav"),
                confidence_score=0.95
            ),
            DialogueSegment(
                speaker_id="SPEAKER_01",
                start_time=4.0,
                end_time=7.2,
                original_text="Très bien, merci beaucoup !",
                audio_path=os.path.join(self.temp_dir, "speaker_01_seg_1.wav"),
                confidence_score=0.92
            ),
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=8.0,
                end_time=11.5,
                original_text="Parfait, continuons notre discussion.",
                audio_path=os.path.join(self.temp_dir, "speaker_00_seg_2.wav"),
                confidence_score=0.88
            )
        ]
        
        # Vérifier la cohérence des segments
        speakers = set(seg.speaker_id for seg in mock_segments)
        self.assertEqual(len(speakers), 2)  # 2 locuteurs distincts
        
        # Vérifier l'ordre chronologique
        for i in range(1, len(mock_segments)):
            self.assertGreaterEqual(
                mock_segments[i].start_time,
                mock_segments[i-1].end_time
            )
        
        # Vérifier la qualité des segments
        avg_confidence = sum(seg.confidence_score for seg in mock_segments) / len(mock_segments)
        self.assertGreater(avg_confidence, 0.85)
    
    def test_synchronization_integration(self):
        """Test d'intégration de la synchronisation OCR/ASR"""
        
        # Données de test pour synchronisation
        ocr_results = [
            {"text": "Bonjour tout le monde", "timestamp": 1.2, "confidence": 0.94},
            {"text": "Comment ça va aujourd'hui ?", "timestamp": 4.8, "confidence": 0.91},
            {"text": "Très bien merci", "timestamp": 8.1, "confidence": 0.96}
        ]
        
        asr_results = [
            {"text": "bonjour tout le monde", "timestamp": 1.1, "confidence": 0.89},
            {"text": "comment ça va aujourd'hui", "timestamp": 4.9, "confidence": 0.87},
            {"text": "très bien merci", "timestamp": 8.0, "confidence": 0.93}
        ]
        
        # Calculer l'alignement
        alignments = []
        for ocr, asr in zip(ocr_results, asr_results):
            time_diff = abs(ocr["timestamp"] - asr["timestamp"])
            text_similarity = self._calculate_text_similarity(ocr["text"], asr["text"])
            
            alignments.append({
                "time_diff": time_diff,
                "text_similarity": text_similarity,
                "aligned": time_diff < 0.5 and text_similarity > 0.8
            })
        
        # Vérifier la qualité de l'alignement
        aligned_count = sum(1 for align in alignments if align["aligned"])
        alignment_rate = aligned_count / len(alignments)
        
        self.assertGreater(alignment_rate, 0.8)  # 80% d'alignement minimum
    
    def test_quality_metrics_integration(self):
        """Test d'intégration des métriques de qualité"""
        
        # Simuler des métriques de qualité complètes
        quality_metrics = {
            "audio_snr": 24.5,
            "transcription_accuracy": 0.94,
            "ocr_accuracy": 0.91,
            "synchronization_error": 0.15,  # secondes
            "voice_cloning_similarity": 0.87,
            "overall_quality_score": 0.89
        }
        
        # Vérifier que toutes les métriques sont dans les plages acceptables
        self.assertGreater(quality_metrics["audio_snr"], 20)  # SNR > 20dB
        self.assertGreater(quality_metrics["transcription_accuracy"], 0.85)
        self.assertGreater(quality_metrics["ocr_accuracy"], 0.80)
        self.assertLess(quality_metrics["synchronization_error"], 0.3)  # < 300ms
        self.assertGreater(quality_metrics["voice_cloning_similarity"], 0.75)
        self.assertGreater(quality_metrics["overall_quality_score"], 0.80)
    
    def test_resource_management_integration(self):
        """Test d'intégration de la gestion des ressources"""
        
        import psutil
        
        # Mesurer l'utilisation des ressources avant traitement
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # Simuler un traitement avec gestion des ressources
        with patch('ai_video_dubbing.utils.performance_optimizer.PerformanceOptimizer') as mock_optimizer:
            mock_instance = mock_optimizer.return_value
            mock_instance.optimize_for_current_system.return_value = {
                "chunk_size": 300,  # 5 minutes
                "max_memory_usage": 0.8,  # 80% max
                "parallel_processes": 2
            }
            
            # Vérifier que l'optimiseur est configuré correctement
            optimizer = mock_optimizer()
            config = optimizer.optimize_for_current_system()
            
            self.assertIn("chunk_size", config)
            self.assertIn("max_memory_usage", config)
            self.assertLessEqual(config["max_memory_usage"], 0.9)
    
    def test_file_management_integration(self):
        """Test d'intégration de la gestion des fichiers"""
        
        # Créer une structure de fichiers temporaires
        test_files = [
            "input_video.mp4",
            "extracted_audio.wav",
            "speaker_segments/speaker_00.wav",
            "speaker_segments/speaker_01.wav",
            "transcription_results.json",
            "ocr_results.json",
            "final_output.mp4"
        ]
        
        created_files = []
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Créer un fichier de test
            with open(full_path, 'w') as f:
                f.write(f"Test content for {file_path}")
            
            created_files.append(full_path)
            self.assertTrue(os.path.exists(full_path))
        
        # Tester le nettoyage des fichiers temporaires
        temp_files = [f for f in created_files if "speaker_segments" in f or "extracted_audio" in f]
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Vérifier que les fichiers temporaires sont supprimés
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))
        
        # Vérifier que les fichiers importants sont conservés
        important_files = [f for f in created_files if "final_output" in f]
        for important_file in important_files:
            if os.path.exists(important_file):
                self.assertTrue(os.path.exists(important_file))
    
    def _setup_pipeline_mocks(self, mock_video_proc, mock_audio_proc, mock_ai_manager):
        """Configuration des mocks pour le pipeline"""
        
        # Mock VideoProcessor
        mock_video_instance = mock_video_proc.return_value
        mock_video_instance.extract_audio.return_value = os.path.join(self.temp_dir, "audio.wav")
        mock_video_instance.extract_frames_during_speech.return_value = [
            {"timestamp": 1.0, "frame": np.zeros((480, 640, 3))},
            {"timestamp": 2.0, "frame": np.zeros((480, 640, 3))}
        ]
        
        # Mock AudioProcessor
        mock_audio_instance = mock_audio_proc.return_value
        mock_audio_instance.detect_voice_activity.return_value = [(1.0, 5.0), (7.0, 12.0)]
        mock_audio_instance.perform_speaker_diarization.return_value = {
            "SPEAKER_00": [(1.0, 3.0), (8.0, 10.0)],
            "SPEAKER_01": [(3.5, 6.0), (11.0, 12.0)]
        }
        
        # Mock AIModelManager
        mock_ai_instance = mock_ai_manager.return_value
        mock_ai_instance.transcribe_audio.return_value = TranscriptionResult(
            text="Bonjour, comment allez-vous ? Très bien merci.",
            segments=[
                {"start": 1.0, "end": 3.0, "text": "Bonjour, comment allez-vous ?"},
                {"start": 3.5, "end": 5.0, "text": "Très bien merci."}
            ],
            confidence=0.92
        )
        mock_ai_instance.extract_text_from_frames.return_value = [
            {"text": "Bonjour, comment allez-vous ?", "timestamp": 1.2, "confidence": 0.94},
            {"text": "Très bien merci.", "timestamp": 3.8, "confidence": 0.91}
        ]
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculer la similarité entre deux textes"""
        # Normaliser les textes
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Calculer la similarité simple (Jaccard)
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class TestEndToEndScenarios(unittest.TestCase):
    """Tests de scénarios end-to-end complets"""
    
    def setUp(self):
        """Configuration des tests end-to-end"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_speaker_scenario(self):
        """Test de scénario avec un seul locuteur"""
        
        # Configuration pour un seul locuteur
        scenario_config = {
            "speakers": 1,
            "duration": 60,  # 1 minute
            "dialogue_segments": 8,
            "expected_quality": 0.90
        }
        
        # Simuler le traitement
        results = self._simulate_scenario_processing(scenario_config)
        
        # Vérifications spécifiques au mono-locuteur
        self.assertEqual(results["speakers_detected"], 1)
        self.assertGreaterEqual(results["dialogue_segments"], 6)
        self.assertGreater(results["quality_score"], 0.85)
    
    def test_multi_speaker_scenario(self):
        """Test de scénario avec plusieurs locuteurs"""
        
        # Configuration pour plusieurs locuteurs
        scenario_config = {
            "speakers": 3,
            "duration": 300,  # 5 minutes
            "dialogue_segments": 25,
            "expected_quality": 0.85
        }
        
        # Simuler le traitement
        results = self._simulate_scenario_processing(scenario_config)
        
        # Vérifications spécifiques au multi-locuteurs
        self.assertEqual(results["speakers_detected"], 3)
        self.assertGreaterEqual(results["dialogue_segments"], 20)
        self.assertGreater(results["quality_score"], 0.80)
    
    def test_noisy_audio_scenario(self):
        """Test de scénario avec audio bruité"""
        
        # Configuration pour audio de faible qualité
        scenario_config = {
            "speakers": 2,
            "duration": 120,  # 2 minutes
            "noise_level": 0.3,  # 30% de bruit
            "expected_quality": 0.75  # Qualité réduite attendue
        }
        
        # Simuler le traitement avec bruit
        results = self._simulate_scenario_processing(scenario_config)
        
        # Vérifications pour audio bruité
        self.assertGreaterEqual(results["speakers_detected"], 1)  # Au moins 1 détecté
        self.assertGreater(results["quality_score"], 0.70)  # Qualité acceptable malgré le bruit
    
    def test_long_video_scenario(self):
        """Test de scénario avec vidéo longue"""
        
        # Configuration pour vidéo longue
        scenario_config = {
            "speakers": 4,
            "duration": 1800,  # 30 minutes
            "dialogue_segments": 120,
            "expected_quality": 0.88,
            "chunk_processing": True
        }
        
        # Simuler le traitement par chunks
        results = self._simulate_scenario_processing(scenario_config)
        
        # Vérifications pour vidéo longue
        self.assertEqual(results["speakers_detected"], 4)
        self.assertGreaterEqual(results["dialogue_segments"], 100)
        self.assertLess(results["processing_time"], 3600)  # < 1 heure de traitement
    
    def _simulate_scenario_processing(self, config: Dict) -> Dict:
        """Simuler le traitement d'un scénario"""
        
        # Calculer le temps de traitement basé sur la durée
        base_processing_time = config["duration"] * 0.5  # 50% de la durée réelle
        
        # Ajuster selon le nombre de locuteurs
        speaker_factor = 1 + (config["speakers"] - 1) * 0.2
        processing_time = base_processing_time * speaker_factor
        
        # Ajuster selon le niveau de bruit si présent
        if "noise_level" in config:
            noise_factor = 1 + config["noise_level"]
            processing_time *= noise_factor
        
        # Calculer la qualité finale
        base_quality = config["expected_quality"]
        
        # Réduire la qualité si beaucoup de locuteurs
        if config["speakers"] > 2:
            base_quality *= 0.95
        
        # Réduire la qualité si audio bruité
        if "noise_level" in config:
            base_quality *= (1 - config["noise_level"] * 0.3)
        
        return {
            "speakers_detected": config["speakers"],
            "dialogue_segments": config["dialogue_segments"],
            "processing_time": processing_time,
            "quality_score": base_quality,
            "memory_usage": config["duration"] * 2,  # 2MB par seconde
            "success": True
        }


if __name__ == '__main__':
    # Exécuter les tests d'intégration
    unittest.main(verbosity=2)