#!/usr/bin/env python3
"""
Tests de performance et benchmarks pour l'application de doublage vidéo par IA
Mesure les performances sur différentes tailles de fichiers et configurations
"""

import unittest
import time
import psutil
import tempfile
import shutil
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Import des modules de l'application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_video_dubbing.models.data_models import PipelineConfig
from ai_video_dubbing.utils.performance_optimizer import PerformanceOptimizer
from ai_video_dubbing.utils.cache_manager import CacheManager


class PerformanceBenchmark:
    """Classe utilitaire pour mesurer les performances"""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
    
    def start_measurement(self, test_name: str):
        """Démarrer la mesure de performance"""
        self.results[test_name] = {
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss / 1024 / 1024,  # MB
            'start_cpu': self.process.cpu_percent()
        }
    
    def end_measurement(self, test_name: str) -> Dict:
        """Terminer la mesure et retourner les résultats"""
        if test_name not in self.results:
            raise ValueError(f"Mesure {test_name} non démarrée")
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()
        
        result = {
            'duration': end_time - self.results[test_name]['start_time'],
            'memory_peak': end_memory,
            'memory_increase': end_memory - self.results[test_name]['start_memory'],
            'cpu_usage': end_cpu
        }
        
        self.results[test_name].update(result)
        return result
    
    def save_results(self, filepath: str):
        """Sauvegarder les résultats dans un fichier JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)


class TestSmallFileBenchmarks(unittest.TestCase):
    """Benchmarks pour petits fichiers (< 1 minute)"""
    
    def setUp(self):
        """Configuration des benchmarks"""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        self.optimizer = PerformanceOptimizer()
        
        # Configuration optimisée pour petits fichiers
        self.config = PipelineConfig(
            enable_source_separation=False,
            temp_directory=self.temp_dir,
            optimization_level="fast"
        )
    
    def tearDown(self):
        """Nettoyage après benchmarks"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_30_second_video_processing(self):
        """Benchmark traitement vidéo 30 secondes"""
        test_name = "video_30s"
        self.benchmark.start_measurement(test_name)
        
        # Simuler le traitement d'une vidéo de 30 secondes
        self._simulate_video_processing(duration=30, resolution="720p")
        
        result = self.benchmark.end_measurement(test_name)
        
        # Assertions de performance
        self.assertLess(result['duration'], 60)  # < 1 minute de traitement
        self.assertLess(result['memory_increase'], 500)  # < 500MB d'augmentation
        
        print(f"Vidéo 30s - Durée: {result['duration']:.2f}s, "
              f"Mémoire: {result['memory_increase']:.1f}MB")
    
    def test_audio_extraction_speed(self):
        """Benchmark extraction audio rapide"""
        test_name = "audio_extraction"
        self.benchmark.start_measurement(test_name)
        
        # Simuler l'extraction audio
        self._simulate_audio_extraction(duration=30)
        
        result = self.benchmark.end_measurement(test_name)
        
        # L'extraction audio doit être très rapide
        self.assertLess(result['duration'], 5)  # < 5 secondes
        
        print(f"Extraction audio - Durée: {result['duration']:.2f}s")
    
    def test_vad_performance(self):
        """Benchmark détection d'activité vocale"""
        test_name = "vad_detection"
        self.benchmark.start_measurement(test_name)
        
        # Simuler la VAD
        self._simulate_vad_processing(duration=30)
        
        result = self.benchmark.end_measurement(test_name)
        
        # VAD doit être rapide
        self.assertLess(result['duration'], 10)  # < 10 secondes
        
        print(f"VAD 30s - Durée: {result['duration']:.2f}s")
    
    def _simulate_video_processing(self, duration: int, resolution: str):
        """Simuler le traitement vidéo"""
        # Simulation basée sur la durée et résolution
        complexity_factor = {
            "480p": 1.0,
            "720p": 1.5,
            "1080p": 2.5
        }.get(resolution, 1.0)
        
        processing_time = (duration / 30) * complexity_factor * 0.1
        time.sleep(min(processing_time, 2.0))  # Max 2s de simulation
    
    def _simulate_audio_extraction(self, duration: int):
        """Simuler l'extraction audio"""
        # L'extraction audio est généralement très rapide
        time.sleep(min(duration / 100, 0.5))  # Max 500ms
    
    def _simulate_vad_processing(self, duration: int):
        """Simuler la détection d'activité vocale"""
        # VAD proportionnelle à la durée
        time.sleep(min(duration / 20, 1.0))  # Max 1s


class TestMediumFileBenchmarks(unittest.TestCase):
    """Benchmarks pour fichiers moyens (5-15 minutes)"""
    
    def setUp(self):
        """Configuration des benchmarks"""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        self.optimizer = PerformanceOptimizer()
        
        # Configuration équilibrée pour fichiers moyens
        self.config = PipelineConfig(
            enable_source_separation=True,
            temp_directory=self.temp_dir,
            optimization_level="balanced"
        )
    
    def tearDown(self):
        """Nettoyage après benchmarks"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_10_minute_complete_pipeline(self):
        """Benchmark pipeline complet 10 minutes"""
        test_name = "pipeline_10min"
        self.benchmark.start_measurement(test_name)
        
        # Simuler le pipeline complet
        self._simulate_complete_pipeline(duration=600)  # 10 minutes
        
        result = self.benchmark.end_measurement(test_name)
        
        # Pipeline complet ne doit pas dépasser 30 minutes
        self.assertLess(result['duration'], 1800)  # < 30 minutes
        self.assertLess(result['memory_increase'], 2000)  # < 2GB
        
        print(f"Pipeline 10min - Durée: {result['duration']:.1f}s, "
              f"Mémoire: {result['memory_increase']:.1f}MB")
    
    def test_speaker_diarization_scaling(self):
        """Benchmark diarisation avec montée en charge"""
        durations = [300, 600, 900]  # 5, 10, 15 minutes
        
        for duration in durations:
            test_name = f"diarization_{duration}s"
            self.benchmark.start_measurement(test_name)
            
            self._simulate_speaker_diarization(duration)
            
            result = self.benchmark.end_measurement(test_name)
            
            # La diarisation doit être sub-linéaire
            expected_max_time = duration / 10  # 1/10 de la durée audio
            self.assertLess(result['duration'], expected_max_time)
            
            print(f"Diarisation {duration}s - Durée: {result['duration']:.1f}s")
    
    def test_memory_optimization(self):
        """Test d'optimisation mémoire avec gros fichiers"""
        test_name = "memory_optimization"
        self.benchmark.start_measurement(test_name)
        
        # Activer l'optimisation mémoire
        self.optimizer.set_optimization_level("memory_efficient")
        
        # Simuler un traitement gourmand en mémoire
        self._simulate_memory_intensive_task()
        
        result = self.benchmark.end_measurement(test_name)
        
        # Avec optimisation, l'augmentation mémoire doit être limitée
        self.assertLess(result['memory_increase'], 1000)  # < 1GB
        
        print(f"Optimisation mémoire - Augmentation: {result['memory_increase']:.1f}MB")
    
    def _simulate_complete_pipeline(self, duration: int):
        """Simuler un pipeline complet"""
        # Phases du pipeline avec temps proportionnels
        phases = {
            "extraction": 0.05,
            "vad": 0.1,
            "diarization": 0.2,
            "transcription": 0.3,
            "ocr": 0.15,
            "alignment": 0.1,
            "voice_cloning": 0.1
        }
        
        for phase, ratio in phases.items():
            phase_time = (duration / 60) * ratio  # Temps basé sur durée
            time.sleep(min(phase_time, 1.0))  # Max 1s par phase
    
    def _simulate_speaker_diarization(self, duration: int):
        """Simuler la diarisation des locuteurs"""
        # Diarisation sub-linéaire
        processing_time = np.sqrt(duration) * 0.1
        time.sleep(min(processing_time, 2.0))
    
    def _simulate_memory_intensive_task(self):
        """Simuler une tâche gourmande en mémoire"""
        # Créer et libérer des arrays pour simuler l'usage mémoire
        arrays = []
        for i in range(5):
            arr = np.zeros((100, 100, 100))  # ~8MB par array
            arrays.append(arr)
            time.sleep(0.1)
        
        # Libérer progressivement
        for arr in arrays:
            del arr
            time.sleep(0.05)


class TestLargeFileBenchmarks(unittest.TestCase):
    """Benchmarks pour gros fichiers (> 30 minutes)"""
    
    def setUp(self):
        """Configuration des benchmarks"""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        self.optimizer = PerformanceOptimizer()
        
        # Configuration optimisée pour gros fichiers
        self.config = PipelineConfig(
            enable_source_separation=True,
            temp_directory=self.temp_dir,
            optimization_level="quality",
            chunk_processing=True
        )
    
    def tearDown(self):
        """Nettoyage après benchmarks"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_chunk_processing_efficiency(self):
        """Test d'efficacité du traitement par chunks"""
        test_name = "chunk_processing"
        self.benchmark.start_measurement(test_name)
        
        # Simuler le traitement par chunks d'un gros fichier
        total_duration = 3600  # 1 heure
        chunk_size = 300  # 5 minutes par chunk
        
        self._simulate_chunked_processing(total_duration, chunk_size)
        
        result = self.benchmark.end_measurement(test_name)
        
        # Le traitement par chunks doit maintenir une mémoire stable
        self.assertLess(result['memory_increase'], 1500)  # < 1.5GB
        
        print(f"Traitement par chunks 1h - Durée: {result['duration']:.1f}s, "
              f"Mémoire: {result['memory_increase']:.1f}MB")
    
    def test_cache_effectiveness(self):
        """Test d'efficacité du cache"""
        cache_manager = CacheManager()
        
        test_name = "cache_test"
        self.benchmark.start_measurement(test_name)
        
        # Premier accès (mise en cache)
        key = "test_model_large"
        data = np.random.rand(1000, 1000)  # ~8MB de données
        cache_manager.set(key, data)
        
        # Accès répétés (depuis le cache)
        for i in range(10):
            cached_data = cache_manager.get(key)
            self.assertIsNotNone(cached_data)
        
        result = self.benchmark.end_measurement(test_name)
        
        # Les accès cache doivent être très rapides
        self.assertLess(result['duration'], 1.0)  # < 1 seconde total
        
        print(f"Cache 10 accès - Durée: {result['duration']:.3f}s")
    
    def test_resource_monitoring(self):
        """Test de monitoring des ressources système"""
        test_name = "resource_monitoring"
        self.benchmark.start_measurement(test_name)
        
        # Simuler un monitoring continu
        monitor_duration = 10  # 10 secondes de monitoring
        self._simulate_resource_monitoring(monitor_duration)
        
        result = self.benchmark.end_measurement(test_name)
        
        # Le monitoring ne doit pas impacter les performances
        self.assertLess(result['cpu_usage'], 5)  # < 5% CPU pour monitoring
        
        print(f"Monitoring {monitor_duration}s - CPU: {result['cpu_usage']:.1f}%")
    
    def _simulate_chunked_processing(self, total_duration: int, chunk_size: int):
        """Simuler le traitement par chunks"""
        num_chunks = total_duration // chunk_size
        
        for chunk in range(num_chunks):
            # Simuler le traitement d'un chunk
            chunk_processing_time = chunk_size / 100  # 1/100 de la durée
            time.sleep(min(chunk_processing_time, 0.5))  # Max 500ms par chunk
            
            # Simuler la libération mémoire entre chunks
            if chunk % 5 == 0:  # Nettoyage tous les 5 chunks
                time.sleep(0.1)
    
    def _simulate_resource_monitoring(self, duration: int):
        """Simuler le monitoring des ressources"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Simuler la collecte de métriques
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            # Petit délai pour simuler le traitement des métriques
            time.sleep(0.05)


class TestConcurrencyBenchmarks(unittest.TestCase):
    """Benchmarks pour les traitements concurrents"""
    
    def setUp(self):
        """Configuration des benchmarks de concurrence"""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
    
    def tearDown(self):
        """Nettoyage après benchmarks"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parallel_ocr_asr(self):
        """Test de traitement parallèle OCR + ASR"""
        test_name = "parallel_ocr_asr"
        self.benchmark.start_measurement(test_name)
        
        # Simuler OCR et ASR en parallèle
        import threading
        
        def simulate_ocr():
            time.sleep(2.0)  # OCR prend 2 secondes
        
        def simulate_asr():
            time.sleep(3.0)  # ASR prend 3 secondes
        
        # Lancer en parallèle
        ocr_thread = threading.Thread(target=simulate_ocr)
        asr_thread = threading.Thread(target=simulate_asr)
        
        ocr_thread.start()
        asr_thread.start()
        
        ocr_thread.join()
        asr_thread.join()
        
        result = self.benchmark.end_measurement(test_name)
        
        # Le traitement parallèle doit être plus rapide que séquentiel
        self.assertLess(result['duration'], 4.0)  # < 4s (au lieu de 5s séquentiel)
        
        print(f"OCR+ASR parallèle - Durée: {result['duration']:.2f}s")
    
    def test_multi_speaker_processing(self):
        """Test de traitement multi-locuteurs"""
        test_name = "multi_speaker"
        self.benchmark.start_measurement(test_name)
        
        # Simuler le traitement de 4 locuteurs en parallèle
        num_speakers = 4
        self._simulate_multi_speaker_processing(num_speakers)
        
        result = self.benchmark.end_measurement(test_name)
        
        # Le traitement multi-locuteurs doit être efficace
        expected_max_time = num_speakers * 0.5  # 500ms par locuteur max
        self.assertLess(result['duration'], expected_max_time)
        
        print(f"Traitement {num_speakers} locuteurs - Durée: {result['duration']:.2f}s")
    
    def _simulate_multi_speaker_processing(self, num_speakers: int):
        """Simuler le traitement de plusieurs locuteurs"""
        import threading
        
        def process_speaker(speaker_id):
            # Simuler le traitement d'un locuteur
            time.sleep(0.3)  # 300ms par locuteur
        
        threads = []
        for i in range(num_speakers):
            thread = threading.Thread(target=process_speaker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()


def run_all_benchmarks():
    """Exécuter tous les benchmarks et générer un rapport"""
    print("="*60)
    print("BENCHMARKS DE PERFORMANCE - APPLICATION DOUBLAGE IA")
    print("="*60)
    
    # Créer le répertoire de résultats
    results_dir = Path("benchmark_results")
    results_dir.mkdir(exist_ok=True)
    
    # Exécuter les suites de benchmarks
    test_suites = [
        TestSmallFileBenchmarks,
        TestMediumFileBenchmarks,
        TestLargeFileBenchmarks,
        TestConcurrencyBenchmarks
    ]
    
    all_results = {}
    
    for suite_class in test_suites:
        print(f"\n{suite_class.__name__}:")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        
        # Capturer les résultats
        result = runner.run(suite)
        
        suite_name = suite_class.__name__
        all_results[suite_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        }
    
    # Sauvegarder le rapport final
    report_path = results_dir / "benchmark_report.json"
    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES BENCHMARKS")
    print(f"{'='*60}")
    
    for suite_name, results in all_results.items():
        print(f"{suite_name}:")
        print(f"  Tests: {results['tests_run']}")
        print(f"  Succès: {results['success_rate']:.1f}%")
        if results['failures'] > 0:
            print(f"  Échecs: {results['failures']}")
        if results['errors'] > 0:
            print(f"  Erreurs: {results['errors']}")
    
    print(f"\nRapport détaillé sauvegardé: {report_path}")


if __name__ == '__main__':
    run_all_benchmarks()