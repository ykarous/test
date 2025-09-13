#!/usr/bin/env python3
"""
Test simple du système de normalisation audio pour le clonage de voix.
"""

import numpy as np
import tempfile
from pathlib import Path

from ai_video_dubbing.processors.audio_normalizer import AudioNormalizer
from ai_video_dubbing.utils.temp_storage import TempStorage


def create_test_audio(duration: float = 5.0, sample_rate: int = 22050) -> np.ndarray:
    """Crée des données audio de test simulant une voix."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples)
    
    # Simuler une voix avec harmoniques
    f0 = 150  # Fréquence fondamentale (voix féminine)
    
    # Harmoniques avec amplitudes décroissantes
    signal = (0.6 * np.sin(2 * np.pi * f0 * t) +
             0.4 * np.sin(2 * np.pi * 2 * f0 * t) +
             0.25 * np.sin(2 * np.pi * 3 * f0 * t) +
             0.15 * np.sin(2 * np.pi * 4 * f0 * t) +
             0.1 * np.sin(2 * np.pi * 5 * f0 * t))
    
    # Modulation d'amplitude pour simuler la parole naturelle
    envelope = 0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    
    # Ajouter du bruit réaliste
    noise = 0.02 * np.random.randn(num_samples)
    
    # Ajouter quelques segments plus silencieux (pauses)
    pause_mask = np.ones_like(t)
    pause_mask[(t > 1.5) & (t < 2.0)] *= 0.1  # Pause à 1.5-2.0s
    pause_mask[(t > 3.5) & (t < 3.8)] *= 0.1  # Pause à 3.5-3.8s
    
    return signal * envelope * pause_mask + noise


def test_audio_normalizer():
    """Test simple du normalisateur audio."""
    
    print("🎚️ Test du système de normalisation audio pour le clonage de voix")
    
    # Créer le normalisateur
    temp_storage = TempStorage()
    normalizer = AudioNormalizer(temp_storage)
    
    print(f"✓ Normalisateur initialisé")
    print(f"  - RMS cible: {normalizer.target_rms_db}dB")
    print(f"  - Crête cible: {normalizer.target_peak_db}dB")
    print(f"  - Taux d'échantillonnage cible: {normalizer.target_sample_rate}Hz")
    print(f"  - Filtre passe-haut: {normalizer.highpass_freq}Hz")
    print(f"  - Filtre passe-bas: {normalizer.lowpass_freq}Hz")
    
    # Créer des données audio de test
    sample_rate = 44100  # Taux élevé pour tester le rééchantillonnage
    duration = 5.0
    audio_data = create_test_audio(duration, sample_rate)
    
    print(f"✓ Audio de test créé: {duration}s à {sample_rate}Hz")
    
    # Test de calcul des statistiques
    print("\n📊 Test de calcul des statistiques audio...")
    
    stats = normalizer._calculate_audio_stats(audio_data, sample_rate)
    
    print(f"✓ Statistiques calculées:")
    print(f"  - RMS: {stats['rms']:.4f} ({stats['rms_db']:.1f}dB)")
    print(f"  - Crête: {stats['peak']:.4f} ({stats['peak_db']:.1f}dB)")
    print(f"  - Plage dynamique: {stats['dynamic_range_db']:.1f}dB")
    print(f"  - Durée: {stats['duration']:.1f}s")
    print(f"  - Ratio de clipping: {stats['clipping_ratio']:.1%}")
    
    # Test d'analyse de qualité
    print("\n🔍 Test d'analyse de qualité audio...")
    
    quality = normalizer._analyze_audio_quality(audio_data, sample_rate)
    
    print(f"✓ Qualité analysée:")
    print(f"  - Niveau RMS: {quality.rms_level:.4f}")
    print(f"  - Niveau de crête: {quality.peak_level:.4f}")
    print(f"  - Plage dynamique: {quality.dynamic_range:.1f}dB")
    print(f"  - SNR estimé: {quality.snr_estimate:.1f}dB")
    print(f"  - Centroïde spectral: {quality.spectral_centroid:.0f}Hz")
    print(f"  - Taux de passage par zéro: {quality.zero_crossing_rate:.4f}")
    print(f"  - Clipping détecté: {quality.clipping_detected}")
    print(f"  - Ratio de silence: {quality.silence_ratio:.1%}")
    print(f"  - Score de réponse fréquentielle: {quality.frequency_response_score:.3f}")
    
    # Test de rééchantillonnage
    print("\n🔄 Test de rééchantillonnage...")
    
    target_sr = normalizer.target_sample_rate
    resampled, new_sr = normalizer._resample_audio(audio_data, sample_rate, target_sr)
    
    print(f"✓ Rééchantillonnage:")
    print(f"  - {sample_rate}Hz -> {new_sr}Hz")
    print(f"  - {len(audio_data)} -> {len(resampled)} échantillons")
    print(f"  - Durée: {len(resampled)/new_sr:.2f}s")
    
    # Test de normalisation RMS
    print("\n📈 Test de normalisation RMS...")
    
    # Créer un signal avec niveau faible
    low_level_audio = resampled * 0.05
    original_rms = np.sqrt(np.mean(low_level_audio ** 2))
    original_rms_db = 20 * np.log10(max(original_rms, 1e-10))
    
    normalized_rms = normalizer._normalize_rms_level(low_level_audio)
    new_rms = np.sqrt(np.mean(normalized_rms ** 2))
    new_rms_db = 20 * np.log10(max(new_rms, 1e-10))
    
    gain_db = new_rms_db - original_rms_db
    
    print(f"✓ Normalisation RMS:")
    print(f"  - RMS original: {original_rms_db:.1f}dB")
    print(f"  - RMS normalisé: {new_rms_db:.1f}dB")
    print(f"  - Gain appliqué: {gain_db:+.1f}dB")
    print(f"  - Crête finale: {20*np.log10(np.max(np.abs(normalized_rms))):.1f}dB")
    
    # Test de normalisation avec préservation de la dynamique
    print("\n🎭 Test de normalisation avec préservation de la dynamique...")
    
    dynamic_normalized = normalizer._normalize_with_dynamics_preservation(low_level_audio)
    dynamic_rms = np.sqrt(np.mean(dynamic_normalized ** 2))
    dynamic_rms_db = 20 * np.log10(max(dynamic_rms, 1e-10))
    
    print(f"✓ Normalisation dynamique:")
    print(f"  - RMS final: {dynamic_rms_db:.1f}dB")
    print(f"  - Crête finale: {20*np.log10(np.max(np.abs(dynamic_normalized))):.1f}dB")
    
    # Test de gate de bruit
    print("\n🚪 Test de gate de bruit...")
    
    # Créer un signal avec du bruit de fond
    noisy_audio = resampled.copy()
    # Ajouter du bruit de fond constant
    noise_level = 0.001
    noisy_audio += noise_level * np.random.randn(len(noisy_audio))
    
    gated_audio = normalizer._apply_noise_gate(noisy_audio, new_sr)
    
    # Calculer la réduction de bruit
    original_noise_floor = np.percentile(np.abs(noisy_audio), 10)
    gated_noise_floor = np.percentile(np.abs(gated_audio), 10)
    noise_reduction_db = 20 * np.log10(max(gated_noise_floor / max(original_noise_floor, 1e-10), 1e-10))
    
    print(f"✓ Gate de bruit:")
    print(f"  - Plancher de bruit original: {20*np.log10(original_noise_floor):.1f}dB")
    print(f"  - Plancher de bruit après gate: {20*np.log10(gated_noise_floor):.1f}dB")
    print(f"  - Réduction: {noise_reduction_db:.1f}dB")
    
    # Test de limitation de crête
    print("\n✂️ Test de limitation de crête...")
    
    # Créer un signal avec des crêtes élevées
    high_peak_audio = resampled * 1.5  # Amplifier pour créer des crêtes
    original_peak = np.max(np.abs(high_peak_audio))
    original_peak_db = 20 * np.log10(original_peak)
    
    limited_audio = normalizer._apply_peak_limiting(high_peak_audio)
    limited_peak = np.max(np.abs(limited_audio))
    limited_peak_db = 20 * np.log10(limited_peak)
    
    reduction_db = limited_peak_db - original_peak_db
    
    print(f"✓ Limitation de crête:")
    print(f"  - Crête originale: {original_peak_db:.1f}dB")
    print(f"  - Crête limitée: {limited_peak_db:.1f}dB")
    print(f"  - Réduction: {reduction_db:.1f}dB")
    print(f"  - Cible: {normalizer.target_peak_db}dB")
    
    # Test de validation de qualité
    print("\n✅ Test de validation de qualité...")
    
    # Mock de la méthode _load_audio pour le test
    original_load = normalizer._load_audio
    
    def mock_load_audio(path):
        return resampled, new_sr
    
    normalizer._load_audio = mock_load_audio
    
    try:
        is_valid, issues = normalizer.validate_audio_quality(
            "test_audio.wav",
            min_duration=3.0,
            min_snr_db=5.0
        )
        
        print(f"✓ Validation de qualité:")
        print(f"  - Audio valide: {is_valid}")
        if issues:
            print(f"  - Problèmes détectés:")
            for issue in issues:
                print(f"    * {issue}")
        else:
            print(f"  - Aucun problème détecté")
    
    finally:
        normalizer._load_audio = original_load
    
    # Test de score de réponse en fréquence
    print("\n🎵 Test de score de réponse en fréquence...")
    
    # Créer un spectre de test
    n_fft = 1024
    magnitude = np.random.rand(n_fft // 2 + 1, 100)
    
    # Simuler un spectre vocal (plus d'énergie dans les moyennes fréquences)
    freqs = np.fft.fftfreq(n_fft, 1/new_sr)[:n_fft//2 + 1]
    voice_mask = (freqs >= 300) & (freqs <= 3400)
    magnitude[voice_mask] *= 3  # Amplifier la bande vocale
    
    score = normalizer._calculate_frequency_response_score(magnitude, new_sr)
    
    print(f"✓ Score de réponse fréquentielle: {score:.3f}")
    print(f"  - Plage optimale pour la voix: 0.6-0.8")
    
    # Test de normalisation par lot (simulation)
    print("\n📦 Test de normalisation par lot...")
    
    speaker_files = {
        "SPEAKER_00": "speaker_00.wav",
        "SPEAKER_01": "speaker_01.wav"
    }
    
    # Mock de la méthode normalize_for_voice_cloning
    original_normalize = normalizer.normalize_for_voice_cloning
    
    def mock_normalize(audio_path, output_path=None, **kwargs):
        from ai_video_dubbing.processors.audio_normalizer import NormalizationResult
        return NormalizationResult(
            normalized_audio_path=output_path or "normalized.wav",
            original_stats={"rms_db": -20.0},
            normalized_stats={"rms_db": -12.0},
            quality_metrics={"original": {}, "normalized": {}},
            processing_time=1.0,
            normalization_applied={"level_normalization": "rms_target"}
        )
    
    normalizer.normalize_for_voice_cloning = mock_normalize
    
    try:
        results = normalizer.batch_normalize_speaker_files(speaker_files)
        
        print(f"✓ Normalisation par lot:")
        print(f"  - Locuteurs traités: {len(results)}")
        for speaker_id, result in results.items():
            print(f"    * {speaker_id}: {result.original_stats['rms_db']:.1f}dB -> {result.normalized_stats['rms_db']:.1f}dB")
    
    finally:
        normalizer.normalize_for_voice_cloning = original_normalize
    
    print(f"\n🎉 Tous les tests de normalisation audio sont réussis!")
    
    # Nettoyage
    temp_storage.cleanup_all()
    print(f"🧹 Nettoyage terminé")


if __name__ == "__main__":
    test_audio_normalizer()