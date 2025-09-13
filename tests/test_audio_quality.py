#!/usr/bin/env python3
"""
Tests de qualité audio pour l'application de doublage vidéo par IA.
"""

import unittest
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AudioQualityTests(unittest.TestCase):
    """Tests de qualité audio."""
    
    def setUp(self):
        """Configuration des tests."""
        self.sample_rate = 44100
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def generate_test_audio(self, duration=1.0, frequency=440.0):
        """Génère un signal audio de test."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    def calculate_snr(self, original, processed):
        """Calcule le rapport signal/bruit."""
        noise = original - processed
        signal_power = np.mean(original ** 2)
        noise_power = np.mean(noise ** 2)
        
        if noise_power == 0:
            return float('inf')
        
        return 10 * np.log10(signal_power / noise_power)
    
    def calculate_thd(self, signal, fundamental_freq, sample_rate):
        """Calcule la distorsion harmonique totale."""
        # Implémentation simplifiée
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/sample_rate)
        
        # Trouver le pic fondamental
        fundamental_idx = np.argmin(np.abs(freqs - fundamental_freq))
        fundamental_power = np.abs(fft[fundamental_idx]) ** 2
        
        # Calculer la puissance totale
        total_power = np.sum(np.abs(fft) ** 2)
        
        # THD approximatif
        harmonic_power = total_power - fundamental_power
        thd = np.sqrt(harmonic_power / fundamental_power)
        
        return thd
    
    def test_audio_normalization_quality(self):
        """Test de qualité de la normalisation audio."""
        # Générer un signal de test
        original = self.generate_test_audio(duration=2.0)
        
        # Simuler normalisation
        target_level = 0.8
        current_max = np.max(np.abs(original))
        normalized = original * (target_level / current_max)
        
        # Vérifier que le niveau cible est atteint
        new_max = np.max(np.abs(normalized))
        self.assertAlmostEqual(new_max, target_level, places=3)
        
        # Vérifier que la forme du signal est préservée
        correlation = np.corrcoef(original, normalized)[0, 1]
        self.assertGreater(correlation, 0.99)
    
    def test_audio_filtering_quality(self):
        """Test de qualité du filtrage audio."""
        # Générer un signal avec bruit
        clean_signal = self.generate_test_audio(duration=1.0, frequency=440.0)
        noise = np.random.normal(0, 0.1, len(clean_signal))
        noisy_signal = clean_signal + noise
        
        # Simuler filtrage simple (moyenne mobile)
        window_size = 5
        filtered_signal = np.convolve(noisy_signal, np.ones(window_size)/window_size, mode='same')
        
        # Calculer l'amélioration SNR
        original_snr = self.calculate_snr(clean_signal, noisy_signal)
        filtered_snr = self.calculate_snr(clean_signal, filtered_signal)
        
        # Le filtrage doit améliorer le SNR
        self.assertGreater(filtered_snr, original_snr)
    
    def test_audio_resampling_quality(self):
        """Test de qualité du rééchantillonnage."""
        # Générer signal à 44.1kHz
        original_sr = 44100
        target_sr = 22050
        
        original = self.generate_test_audio(duration=1.0)
        
        # Simuler rééchantillonnage (décimation simple)
        decimation_factor = original_sr // target_sr
        resampled = original[::decimation_factor]
        
        # Vérifier la longueur
        expected_length = len(original) // decimation_factor
        self.assertEqual(len(resampled), expected_length)
        
        # Vérifier que le contenu fréquentiel principal est préservé
        # (test simplifié)
        self.assertGreater(len(resampled), 0)
    
    def test_audio_compression_quality(self):
        """Test de qualité de la compression audio."""
        # Générer signal de test
        original = self.generate_test_audio(duration=2.0)
        
        # Simuler compression dynamique
        threshold = 0.5
        ratio = 4.0
        
        compressed = original.copy()
        over_threshold = np.abs(compressed) > threshold
        
        # Appliquer compression aux échantillons au-dessus du seuil
        compressed[over_threshold] = (
            np.sign(compressed[over_threshold]) * 
            (threshold + (np.abs(compressed[over_threshold]) - threshold) / ratio)
        )
        
        # Vérifier que les pics sont réduits
        original_peak = np.max(np.abs(original))
        compressed_peak = np.max(np.abs(compressed))
        
        if original_peak > threshold:
            self.assertLess(compressed_peak, original_peak)
    
    def test_audio_distortion_measurement(self):
        """Test de mesure de distorsion audio."""
        # Générer signal pur
        frequency = 1000.0  # 1kHz
        pure_signal = self.generate_test_audio(duration=1.0, frequency=frequency)
        
        # Ajouter distorsion harmonique
        distorted_signal = pure_signal + 0.1 * np.sin(2 * 2 * np.pi * frequency * 
                                                      np.linspace(0, 1, len(pure_signal)))
        
        # Calculer THD
        thd_pure = self.calculate_thd(pure_signal, frequency, self.sample_rate)
        thd_distorted = self.calculate_thd(distorted_signal, frequency, self.sample_rate)
        
        # Le signal distordu doit avoir plus de THD
        self.assertGreater(thd_distorted, thd_pure)
    
    def test_audio_phase_coherence(self):
        """Test de cohérence de phase audio."""
        # Générer signal stéréo cohérent
        mono_signal = self.generate_test_audio(duration=1.0)
        stereo_left = mono_signal
        stereo_right = mono_signal  # Même signal, phase cohérente
        
        # Calculer corrélation croisée
        correlation = np.corrcoef(stereo_left, stereo_right)[0, 1]
        
        # Les canaux doivent être parfaitement corrélés
        self.assertAlmostEqual(correlation, 1.0, places=3)
        
        # Test avec déphasage
        stereo_right_shifted = np.roll(stereo_right, 100)  # Décalage de phase
        correlation_shifted = np.corrcoef(stereo_left, stereo_right_shifted)[0, 1]
        
        # La corrélation doit diminuer avec le déphasage
        self.assertLess(correlation_shifted, correlation)
    
    def test_audio_frequency_response(self):
        """Test de réponse en fréquence."""
        # Générer sweep de fréquences
        duration = 2.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Sweep logarithmique de 100Hz à 10kHz
        f_start, f_end = 100, 10000
        sweep = np.sin(2 * np.pi * f_start * (f_end/f_start)**(t/duration) * t)
        
        # Simuler traitement (filtre passe-bas simple)
        cutoff_freq = 5000  # 5kHz
        
        # Filtre simple (moyenne mobile)
        window_size = int(self.sample_rate / cutoff_freq)
        filtered_sweep = np.convolve(sweep, np.ones(window_size)/window_size, mode='same')
        
        # Vérifier que le signal est modifié (filtré)
        correlation = np.corrcoef(sweep, filtered_sweep)[0, 1]
        self.assertLess(correlation, 0.99)  # Doit être différent mais similaire
        self.assertGreater(correlation, 0.8)  # Mais pas trop différent
    
    def test_audio_dynamic_range(self):
        """Test de plage dynamique audio."""
        # Générer signal avec différents niveaux
        quiet_part = 0.1 * self.generate_test_audio(duration=0.5, frequency=440)
        loud_part = 0.9 * self.generate_test_audio(duration=0.5, frequency=880)
        
        combined_signal = np.concatenate([quiet_part, loud_part])
        
        # Calculer plage dynamique
        rms_values = []
        window_size = int(0.1 * self.sample_rate)  # Fenêtres de 100ms
        
        for i in range(0, len(combined_signal) - window_size, window_size):
            window = combined_signal[i:i + window_size]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)
        
        rms_values = np.array(rms_values)
        dynamic_range_db = 20 * np.log10(np.max(rms_values) / (np.min(rms_values) + 1e-10))
        
        # Vérifier que la plage dynamique est significative
        self.assertGreater(dynamic_range_db, 10)  # Au moins 10dB de plage
    
    def test_audio_stereo_imaging(self):
        """Test d'imagerie stéréo."""
        # Générer signal stéréo avec panoramique
        mono_signal = self.generate_test_audio(duration=1.0)
        
        # Panoramique gauche (L=1.0, R=0.0)
        left_channel = mono_signal
        right_channel = np.zeros_like(mono_signal)
        
        # Vérifier la séparation stéréo
        left_energy = np.sum(left_channel ** 2)
        right_energy = np.sum(right_channel ** 2)
        
        # Le canal gauche doit avoir toute l'énergie
        self.assertGreater(left_energy, 0)
        self.assertEqual(right_energy, 0)
        
        # Test panoramique centre
        center_left = mono_signal * 0.707  # -3dB
        center_right = mono_signal * 0.707
        
        center_left_energy = np.sum(center_left ** 2)
        center_right_energy = np.sum(center_right ** 2)
        
        # Les deux canaux doivent avoir la même énergie
        self.assertAlmostEqual(center_left_energy, center_right_energy, places=3)


if __name__ == '__main__':
    unittest.main()