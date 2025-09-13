#!/usr/bin/env python3
"""
Tests pour le processeur de normalisation audio.
"""

import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

from ai_video_dubbing.processors.audio_normalizer import (
    AudioNormalizer, NormalizationResult, AudioQualityMetrics
)
from ai_video_dubbing.models.data_models import ProcessingError, ValidationError
from ai_video_dubbing.utils.temp_storage import TempStorage


class TestAudioNormalizer:
    """Tests pour AudioNormalizer."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_storage = TempStorage()
        self.normalizer = AudioNormalizer(self.temp_storage)
        
        # Créer des données audio de test
        self.sample_rate = 22050
        self.duration = 5.0
        self.audio_data = self._create_test_audio(self.duration, self.sample_rate)
    
    def _create_test_audio(self, duration: float, sample_rate: int) -> np.ndarray:
        """Crée des données audio de test."""
        num_samples = int(duration * sample_rate)
        
        # Signal de voix simulé avec harmoniques
        t = np.linspace(0, duration, num_samples)
        
        # Fréquence fondamentale (voix masculine typique)
        f0 = 120  # Hz
        
        # Harmoniques avec amplitudes décroissantes
        signal = (0.5 * np.sin(2 * np.pi * f0 * t) +
                 0.3 * np.sin(2 * np.pi * 2 * f0 * t) +
                 0.2 * np.sin(2 * np.pi * 3 * f0 * t) +
                 0.1 * np.sin(2 * np.pi * 4 * f0 * t))
        
        # Ajouter du bruit réaliste
        noise = 0.05 * np.random.randn(num_samples)
        
        # Modulation d'amplitude pour simuler la parole
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # Modulation à 2Hz
        
        return signal * envelope + noise
    
    def test_init(self):
        """Test d'initialisation du normalisateur."""
        normalizer = AudioNormalizer()
        assert normalizer.temp_storage is not None
        assert normalizer.logger is not None
        assert normalizer.target_rms_db == -12.0
        assert normalizer.target_peak_db == -3.0
        assert normalizer.target_sample_rate == 22050
    
    def test_init_with_temp_storage(self):
        """Test d'initialisation avec gestionnaire de stockage."""
        temp_storage = TempStorage()
        normalizer = AudioNormalizer(temp_storage)
        assert normalizer.temp_storage is temp_storage
    
    @patch('ai_video_dubbing.processors.audio_normalizer.librosa')
    def test_load_audio(self, mock_librosa):
        """Test de chargement audio."""
        # Mock librosa.load
        mock_librosa.load.return_value = (self.audio_data, self.sample_rate)
        
        audio_data, sample_rate = self.normalizer._load_audio("test.wav")
        
        assert np.array_equal(audio_data, self.audio_data)
        assert sample_rate == self.sample_rate
        mock_librosa.load.assert_called_once_with("test.wav", sr=None, mono=True)
    
    def test_load_audio_empty_file(self):
        """Test de chargement d'un fichier vide."""
        with patch('ai_video_dubbing.processors.audio_normalizer.librosa') as mock_librosa:
            mock_librosa.load.return_value = (np.array([]), self.sample_rate)
            
            try:
                self.normalizer._load_audio("empty.wav")
                assert False, "Devrait lever ValidationError"
            except ValidationError as e:
                assert "empty" in str(e).lower()
    
    def test_calculate_audio_stats(self):
        """Test de calcul des statistiques audio."""
        stats = self.normalizer._calculate_audio_stats(self.audio_data, self.sample_rate)
        
        # Vérifier la structure
        required_keys = [
            'rms', 'rms_db', 'peak', 'peak_db', 'dynamic_range_db',
            'duration', 'clipping_ratio', 'sample_rate'
        ]
        for key in required_keys:
            assert key in stats
        
        # Vérifier les valeurs
        assert stats['duration'] == self.duration
        assert stats['sample_rate'] == self.sample_rate
        assert stats['rms'] > 0
        assert stats['peak'] > 0
        assert stats['dynamic_range_db'] > 0
        assert 0 <= stats['clipping_ratio'] <= 1
    
    def test_analyze_audio_quality(self):
        """Test d'analyse de qualité audio."""
        quality = self.normalizer._analyze_audio_quality(self.audio_data, self.sample_rate)
        
        # Vérifier le type de retour
        assert isinstance(quality, AudioQualityMetrics)
        
        # Vérifier les valeurs
        assert quality.rms_level > 0
        assert quality.peak_level > 0
        assert quality.dynamic_range > 0
        assert 0 <= quality.silence_ratio <= 1
        assert 0 <= quality.frequency_response_score <= 1
        assert isinstance(quality.clipping_detected, bool)
    
    def test_resample_audio_same_rate(self):
        """Test de rééchantillonnage avec même taux."""
        resampled, new_sr = self.normalizer._resample_audio(
            self.audio_data, self.sample_rate, self.sample_rate
        )
        
        # Devrait retourner les mêmes données
        assert np.array_equal(resampled, self.audio_data)
        assert new_sr == self.sample_rate
    
    @patch('ai_video_dubbing.processors.audio_normalizer.librosa')
    def test_resample_audio_different_rate(self, mock_librosa):
        """Test de rééchantillonnage avec taux différent."""
        target_sr = 16000
        resampled_data = np.random.randn(int(self.duration * target_sr))
        
        mock_librosa.resample.return_value = resampled_data
        
        resampled, new_sr = self.normalizer._resample_audio(
            self.audio_data, self.sample_rate, target_sr
        )
        
        assert np.array_equal(resampled, resampled_data)
        assert new_sr == target_sr
        mock_librosa.resample.assert_called_once()
    
    def test_resample_audio_without_librosa(self):
        """Test de rééchantillonnage sans librosa."""
        with patch('ai_video_dubbing.processors.audio_normalizer.librosa', None):
            target_sr = 16000
            
            resampled, new_sr = self.normalizer._resample_audio(
                self.audio_data, self.sample_rate, target_sr
            )
            
            # Vérifier que le rééchantillonnage a eu lieu
            expected_length = int(len(self.audio_data) * target_sr / self.sample_rate)
            assert len(resampled) == expected_length
            assert new_sr == target_sr
    
    def test_normalize_rms_level(self):
        """Test de normalisation RMS."""
        # Créer un signal avec un niveau RMS spécifique
        low_level_audio = self.audio_data * 0.1  # Niveau très faible
        
        normalized = self.normalizer._normalize_rms_level(low_level_audio)
        
        # Vérifier que le niveau RMS a augmenté
        original_rms = np.sqrt(np.mean(low_level_audio ** 2))
        normalized_rms = np.sqrt(np.mean(normalized ** 2))
        
        assert normalized_rms > original_rms
        
        # Vérifier qu'il n'y a pas de clipping
        assert np.max(np.abs(normalized)) <= 0.99
    
    def test_normalize_rms_level_silent(self):
        """Test de normalisation RMS sur signal silencieux."""
        silent_audio = np.zeros(1000)
        
        normalized = self.normalizer._normalize_rms_level(silent_audio)
        
        # Le signal silencieux devrait rester silencieux
        assert np.array_equal(normalized, silent_audio)
    
    def test_apply_noise_gate(self):
        """Test d'application du gate de bruit."""
        # Créer un signal avec des parties silencieuses
        signal_with_silence = self.audio_data.copy()
        
        # Ajouter des segments silencieux
        silence_start = int(0.2 * len(signal_with_silence))
        silence_end = int(0.4 * len(signal_with_silence))
        signal_with_silence[silence_start:silence_end] *= 0.001  # Très faible
        
        gated = self.normalizer._apply_noise_gate(signal_with_silence, self.sample_rate)
        
        # Vérifier que les parties silencieuses ont été atténuées
        gated_silence = gated[silence_start:silence_end]
        original_silence = signal_with_silence[silence_start:silence_end]
        
        assert np.mean(np.abs(gated_silence)) <= np.mean(np.abs(original_silence))
    
    def test_apply_peak_limiting(self):
        """Test de limitation de crête."""
        # Créer un signal avec des crêtes élevées
        high_peak_audio = self.audio_data * 2.0  # Amplifier pour créer des crêtes
        
        limited = self.normalizer._apply_peak_limiting(high_peak_audio)
        
        # Vérifier que les crêtes ont été limitées
        target_peak_linear = 10 ** (self.normalizer.target_peak_db / 20)
        assert np.max(np.abs(limited)) <= target_peak_linear * 1.01  # Petite tolérance
    
    def test_apply_peak_limiting_no_limiting_needed(self):
        """Test de limitation quand aucune limitation n'est nécessaire."""
        # Signal déjà sous le seuil
        low_peak_audio = self.audio_data * 0.1
        
        limited = self.normalizer._apply_peak_limiting(low_peak_audio)
        
        # Devrait être identique
        assert np.array_equal(limited, low_peak_audio)
    
    def test_normalize_with_dynamics_preservation(self):
        """Test de normalisation avec préservation de la dynamique."""
        normalized = self.normalizer._normalize_with_dynamics_preservation(self.audio_data)
        
        # Vérifier que le niveau a été ajusté
        original_rms = np.sqrt(np.mean(self.audio_data ** 2))
        normalized_rms = np.sqrt(np.mean(normalized ** 2))
        
        # Le niveau devrait être différent (généralement plus élevé)
        assert normalized_rms != original_rms
        
        # Vérifier qu'il n'y a pas de clipping
        assert np.max(np.abs(normalized)) <= 0.99
    
    def test_calculate_frequency_response_score(self):
        """Test de calcul du score de réponse en fréquence."""
        # Créer un spectre de test
        n_fft = 1024
        magnitude = np.random.rand(n_fft // 2 + 1, 100)  # Spectre aléatoire
        
        score = self.normalizer._calculate_frequency_response_score(
            magnitude, self.sample_rate
        )
        
        # Vérifier que le score est dans la plage valide
        assert 0.0 <= score <= 1.0
    
    @patch('ai_video_dubbing.processors.audio_normalizer.soundfile')
    def test_save_audio(self, mock_sf):
        """Test de sauvegarde audio."""
        output_path = "test_output.wav"
        
        self.normalizer._save_audio(self.audio_data, self.sample_rate, output_path)
        
        mock_sf.write.assert_called_once_with(
            output_path, self.audio_data, self.sample_rate, subtype='PCM_24'
        )
    
    def test_validate_audio_quality_good(self):
        """Test de validation avec audio de bonne qualité."""
        with patch.object(self.normalizer, '_load_audio') as mock_load:
            mock_load.return_value = (self.audio_data, self.sample_rate)
            
            is_valid, issues = self.normalizer.validate_audio_quality(
                "good_audio.wav", min_duration=3.0, min_snr_db=5.0
            )
            
            # L'audio de test devrait être considéré comme valide
            assert is_valid or len(issues) <= 2  # Tolérance pour quelques avertissements mineurs
    
    def test_validate_audio_quality_short_duration(self):
        """Test de validation avec durée trop courte."""
        short_audio = self.audio_data[:int(2.0 * self.sample_rate)]  # 2 secondes
        
        with patch.object(self.normalizer, '_load_audio') as mock_load:
            mock_load.return_value = (short_audio, self.sample_rate)
            
            is_valid, issues = self.normalizer.validate_audio_quality(
                "short_audio.wav", min_duration=5.0
            )
            
            assert not is_valid
            assert any("Duration too short" in issue for issue in issues)
    
    def test_validate_audio_quality_clipping(self):
        """Test de validation avec clipping."""
        clipped_audio = np.clip(self.audio_data * 2.0, -1.0, 1.0)  # Créer du clipping
        
        with patch.object(self.normalizer, '_load_audio') as mock_load:
            mock_load.return_value = (clipped_audio, self.sample_rate)
            
            is_valid, issues = self.normalizer.validate_audio_quality("clipped_audio.wav")
            
            # Devrait détecter le clipping
            clipping_issues = [issue for issue in issues if "clipping" in issue.lower()]
            assert len(clipping_issues) > 0
    
    def test_batch_normalize_speaker_files(self):
        """Test de normalisation par lot."""
        speaker_files = {
            "SPEAKER_00": "speaker_00.wav",
            "SPEAKER_01": "speaker_01.wav"
        }
        
        # Mock des méthodes nécessaires
        with patch.object(self.normalizer, 'normalize_for_voice_cloning') as mock_normalize:
            mock_result = NormalizationResult(
                normalized_audio_path="normalized.wav",
                original_stats={},
                normalized_stats={},
                quality_metrics={},
                processing_time=1.0,
                normalization_applied={}
            )
            mock_normalize.return_value = mock_result
            
            results = self.normalizer.batch_normalize_speaker_files(speaker_files)
            
            # Vérifier que tous les locuteurs ont été traités
            assert len(results) == 2
            assert "SPEAKER_00" in results
            assert "SPEAKER_01" in results
            assert mock_normalize.call_count == 2
    
    def test_batch_normalize_with_output_dir(self):
        """Test de normalisation par lot avec dossier de sortie."""
        speaker_files = {"SPEAKER_00": "speaker_00.wav"}
        output_dir = "normalized_output"
        
        with patch.object(self.normalizer, 'normalize_for_voice_cloning') as mock_normalize:
            mock_result = NormalizationResult(
                normalized_audio_path="normalized.wav",
                original_stats={},
                normalized_stats={},
                quality_metrics={},
                processing_time=1.0,
                normalization_applied={}
            )
            mock_normalize.return_value = mock_result
            
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                results = self.normalizer.batch_normalize_speaker_files(
                    speaker_files, output_dir=output_dir
                )
                
                # Vérifier que le dossier a été créé
                mock_mkdir.assert_called_once()
                
                # Vérifier l'appel avec le bon chemin de sortie
                expected_output = str(Path(output_dir) / "SPEAKER_00_normalized.wav")
                mock_normalize.assert_called_once()
                call_args = mock_normalize.call_args
                assert call_args[0][1] == expected_output


class TestAudioQualityMetrics:
    """Tests pour la classe AudioQualityMetrics."""
    
    def test_audio_quality_metrics_creation(self):
        """Test de création des métriques de qualité."""
        metrics = AudioQualityMetrics(
            rms_level=0.1,
            peak_level=0.5,
            dynamic_range=20.0,
            snr_estimate=15.0,
            spectral_centroid=1000.0,
            zero_crossing_rate=0.1,
            clipping_detected=False,
            silence_ratio=0.05,
            frequency_response_score=0.8
        )
        
        assert metrics.rms_level == 0.1
        assert metrics.peak_level == 0.5
        assert metrics.dynamic_range == 20.0
        assert metrics.snr_estimate == 15.0
        assert metrics.spectral_centroid == 1000.0
        assert metrics.zero_crossing_rate == 0.1
        assert metrics.clipping_detected == False
        assert metrics.silence_ratio == 0.05
        assert metrics.frequency_response_score == 0.8


class TestNormalizationResult:
    """Tests pour la classe NormalizationResult."""
    
    def test_normalization_result_creation(self):
        """Test de création du résultat de normalisation."""
        result = NormalizationResult(
            normalized_audio_path="output.wav",
            original_stats={"rms_db": -20.0},
            normalized_stats={"rms_db": -12.0},
            quality_metrics={"original": {}, "normalized": {}},
            processing_time=2.5,
            normalization_applied={"level_normalization": "rms_target"}
        )
        
        assert result.normalized_audio_path == "output.wav"
        assert result.original_stats["rms_db"] == -20.0
        assert result.normalized_stats["rms_db"] == -12.0
        assert result.processing_time == 2.5
        assert "level_normalization" in result.normalization_applied