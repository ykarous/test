#!/usr/bin/env python3
"""
Processeur de normalisation audio pour le clonage de voix.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import warnings

from ..models.data_models import ProcessingError, ValidationError
from ..utils.temp_storage import TempStorage


@dataclass
class NormalizationResult:
    """Résultat de la normalisation audio."""
    normalized_audio_path: str
    original_stats: Dict[str, float]
    normalized_stats: Dict[str, float]
    quality_metrics: Dict[str, Any]
    processing_time: float
    normalization_applied: Dict[str, Any]


@dataclass
class AudioQualityMetrics:
    """Métriques de qualité audio."""
    rms_level: float
    peak_level: float
    dynamic_range: float
    snr_estimate: float
    spectral_centroid: float
    zero_crossing_rate: float
    clipping_detected: bool
    silence_ratio: float
    frequency_response_score: float


class AudioNormalizer:
    """Processeur de normalisation audio optimisé pour le clonage de voix."""
    
    def __init__(self, temp_storage: Optional[TempStorage] = None):
        """
        Initialise le normalisateur audio.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage or TempStorage()
        self.logger = logging.getLogger(__name__)
        
        # Configuration optimale pour le clonage de voix
        self.target_rms_db = -12.0  # Niveau RMS cible en dB
        self.target_peak_db = -3.0  # Niveau de crête maximal en dB
        self.min_dynamic_range_db = 20.0  # Plage dynamique minimale
        self.target_sample_rate = 22050  # Taux d'échantillonnage optimal
        self.highpass_freq = 80.0  # Filtre passe-haut pour éliminer les basses fréquences
        self.lowpass_freq = 8000.0  # Filtre passe-bas pour éliminer les hautes fréquences
        self.noise_gate_threshold_db = -40.0  # Seuil de gate de bruit
        self.max_gain_db = 20.0  # Gain maximal autorisé
        
    def normalize_for_voice_cloning(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        preserve_dynamics: bool = True,
        apply_noise_reduction: bool = True,
        apply_eq: bool = True
    ) -> NormalizationResult:
        """
        Normalise l'audio pour optimiser le clonage de voix.
        
        Args:
            audio_path: Chemin vers le fichier audio d'entrée
            output_path: Chemin de sortie (optionnel)
            preserve_dynamics: Préserver la dynamique naturelle
            apply_noise_reduction: Appliquer la réduction de bruit
            apply_eq: Appliquer l'égalisation
            
        Returns:
            Résultats de la normalisation
            
        Raises:
            ProcessingError: Si la normalisation échoue
        """
        if not Path(audio_path).exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        try:
            import time
            start_time = time.time()
            
            self.logger.info(f"Starting voice cloning normalization for {audio_path}")
            
            # Charger l'audio
            audio_data, sample_rate = self._load_audio(audio_path)
            original_stats = self._calculate_audio_stats(audio_data, sample_rate)
            
            # Analyser la qualité initiale
            quality_metrics = self._analyze_audio_quality(audio_data, sample_rate)
            
            # Pipeline de normalisation
            normalized_audio = audio_data.copy()
            normalization_steps = {}
            
            # 1. Rééchantillonnage si nécessaire
            if sample_rate != self.target_sample_rate:
                normalized_audio, new_sample_rate = self._resample_audio(
                    normalized_audio, sample_rate, self.target_sample_rate
                )
                sample_rate = new_sample_rate
                normalization_steps["resampling"] = {
                    "original_sr": sample_rate,
                    "target_sr": self.target_sample_rate
                }
            
            # 2. Filtrage passe-haut/passe-bas
            if apply_eq:
                normalized_audio = self._apply_frequency_filtering(
                    normalized_audio, sample_rate
                )
                normalization_steps["frequency_filtering"] = {
                    "highpass_freq": self.highpass_freq,
                    "lowpass_freq": self.lowpass_freq
                }
            
            # 3. Réduction de bruit
            if apply_noise_reduction:
                normalized_audio = self._apply_noise_reduction(
                    normalized_audio, sample_rate
                )
                normalization_steps["noise_reduction"] = True
            
            # 4. Gate de bruit
            normalized_audio = self._apply_noise_gate(
                normalized_audio, sample_rate
            )
            normalization_steps["noise_gate"] = {
                "threshold_db": self.noise_gate_threshold_db
            }
            
            # 5. Normalisation de niveau
            if preserve_dynamics:
                normalized_audio = self._normalize_with_dynamics_preservation(
                    normalized_audio
                )
                normalization_steps["level_normalization"] = "dynamic_preservation"
            else:
                normalized_audio = self._normalize_rms_level(normalized_audio)
                normalization_steps["level_normalization"] = "rms_target"
            
            # 6. Limitation de crête
            normalized_audio = self._apply_peak_limiting(normalized_audio)
            normalization_steps["peak_limiting"] = {
                "target_peak_db": self.target_peak_db
            }
            
            # 7. Validation finale
            final_stats = self._calculate_audio_stats(normalized_audio, sample_rate)
            final_quality = self._analyze_audio_quality(normalized_audio, sample_rate)
            
            # Sauvegarder le résultat
            if output_path is None:
                output_path = self.temp_storage.get_temp_path("normalized_audio.wav")
            
            self._save_audio(normalized_audio, sample_rate, output_path)
            
            processing_time = time.time() - start_time
            
            result = NormalizationResult(
                normalized_audio_path=output_path,
                original_stats=original_stats,
                normalized_stats=final_stats,
                quality_metrics={
                    "original": quality_metrics,
                    "normalized": final_quality
                },
                processing_time=processing_time,
                normalization_applied=normalization_steps
            )
            
            self.logger.info(
                f"Normalization completed in {processing_time:.2f}s "
                f"(RMS: {original_stats['rms_db']:.1f}dB -> {final_stats['rms_db']:.1f}dB)"
            )
            
            return result
            
        except Exception as e:
            raise ProcessingError(f"Audio normalization failed: {e}")
    
    def _load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Charge le fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Tuple (données audio, taux d'échantillonnage)
        """
        try:
            import librosa
            
            # Charger en mono avec le taux d'échantillonnage original
            audio_data, sample_rate = librosa.load(
                audio_path, 
                sr=None,  # Conserver le taux original
                mono=True
            )
            
            if len(audio_data) == 0:
                raise ValidationError("Audio file is empty")
            
            self.logger.info(
                f"Loaded audio: {len(audio_data)/sample_rate:.2f}s at {sample_rate}Hz"
            )
            
            return audio_data, sample_rate
            
        except ImportError:
            raise ProcessingError("librosa is required for audio processing")
        except Exception as e:
            raise ProcessingError(f"Failed to load audio: {e}")
    
    def _calculate_audio_stats(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """
        Calcule les statistiques audio de base.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Dictionnaire des statistiques
        """
        # Niveaux RMS et de crête
        rms = np.sqrt(np.mean(audio_data ** 2))
        peak = np.max(np.abs(audio_data))
        
        # Conversion en dB (avec protection contre log(0))
        rms_db = 20 * np.log10(max(rms, 1e-10))
        peak_db = 20 * np.log10(max(peak, 1e-10))
        
        # Plage dynamique
        dynamic_range_db = peak_db - rms_db
        
        # Durée
        duration = len(audio_data) / sample_rate
        
        # Détection de clipping
        clipping_threshold = 0.99
        clipped_samples = np.sum(np.abs(audio_data) > clipping_threshold)
        clipping_ratio = clipped_samples / len(audio_data)
        
        return {
            "rms": rms,
            "rms_db": rms_db,
            "peak": peak,
            "peak_db": peak_db,
            "dynamic_range_db": dynamic_range_db,
            "duration": duration,
            "clipping_ratio": clipping_ratio,
            "sample_rate": sample_rate
        }
    
    def _analyze_audio_quality(self, audio_data: np.ndarray, sample_rate: int) -> AudioQualityMetrics:
        """
        Analyse la qualité audio en détail.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Métriques de qualité détaillées
        """
        try:
            import librosa
            
            # Niveaux de base
            rms = np.sqrt(np.mean(audio_data ** 2))
            peak = np.max(np.abs(audio_data))
            
            # Plage dynamique
            dynamic_range = 20 * np.log10(max(peak, 1e-10)) - 20 * np.log10(max(rms, 1e-10))
            
            # Estimation du SNR (Signal-to-Noise Ratio)
            # Utiliser les 10% les plus silencieux comme estimation du bruit
            sorted_abs = np.sort(np.abs(audio_data))
            noise_floor = np.mean(sorted_abs[:int(0.1 * len(sorted_abs))])
            signal_level = rms
            snr = 20 * np.log10(max(signal_level / max(noise_floor, 1e-10), 1e-10))
            
            # Centroïde spectral (brillance)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(
                y=audio_data, sr=sample_rate
            ))
            
            # Taux de passage par zéro (indicateur de contenu haute fréquence)
            zero_crossings = librosa.feature.zero_crossing_rate(audio_data)
            zcr = np.mean(zero_crossings)
            
            # Détection de clipping
            clipping_detected = np.any(np.abs(audio_data) > 0.99)
            
            # Ratio de silence
            silence_threshold = 0.01 * rms  # 1% du niveau RMS
            silence_samples = np.sum(np.abs(audio_data) < silence_threshold)
            silence_ratio = silence_samples / len(audio_data)
            
            # Score de réponse en fréquence (basé sur la distribution spectrale)
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            freq_response_score = self._calculate_frequency_response_score(
                magnitude, sample_rate
            )
            
            return AudioQualityMetrics(
                rms_level=rms,
                peak_level=peak,
                dynamic_range=dynamic_range,
                snr_estimate=snr,
                spectral_centroid=spectral_centroid,
                zero_crossing_rate=zcr,
                clipping_detected=clipping_detected,
                silence_ratio=silence_ratio,
                frequency_response_score=freq_response_score
            )
            
        except ImportError:
            # Version simplifiée sans librosa
            rms = np.sqrt(np.mean(audio_data ** 2))
            peak = np.max(np.abs(audio_data))
            dynamic_range = 20 * np.log10(max(peak / max(rms, 1e-10), 1e-10))
            
            return AudioQualityMetrics(
                rms_level=rms,
                peak_level=peak,
                dynamic_range=dynamic_range,
                snr_estimate=0.0,
                spectral_centroid=0.0,
                zero_crossing_rate=0.0,
                clipping_detected=np.any(np.abs(audio_data) > 0.99),
                silence_ratio=0.0,
                frequency_response_score=0.5
            )
    
    def _calculate_frequency_response_score(
        self, 
        magnitude: np.ndarray, 
        sample_rate: int
    ) -> float:
        """
        Calcule un score de qualité de la réponse en fréquence.
        
        Args:
            magnitude: Magnitude du spectre
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Score de 0.0 à 1.0 (1.0 = optimal pour la voix)
        """
        # Fréquences importantes pour la voix humaine (300-3400 Hz)
        freqs = np.fft.fftfreq(magnitude.shape[0] * 2, 1/sample_rate)[:magnitude.shape[0]]
        
        # Indices pour les bandes de fréquences importantes
        voice_band_mask = (freqs >= 300) & (freqs <= 3400)
        low_freq_mask = freqs < 300
        high_freq_mask = freqs > 3400
        
        if not np.any(voice_band_mask):
            return 0.5  # Score neutre si impossible à calculer
        
        # Énergie dans chaque bande
        voice_energy = np.mean(magnitude[voice_band_mask])
        low_energy = np.mean(magnitude[low_freq_mask]) if np.any(low_freq_mask) else 0
        high_energy = np.mean(magnitude[high_freq_mask]) if np.any(high_freq_mask) else 0
        
        # Score basé sur la concentration d'énergie dans la bande vocale
        total_energy = voice_energy + low_energy + high_energy
        if total_energy > 0:
            voice_ratio = voice_energy / total_energy
            # Score optimal autour de 0.6-0.8 pour la voix
            score = 1.0 - abs(voice_ratio - 0.7) / 0.7
            return max(0.0, min(1.0, score))
        
        return 0.5
    
    def _resample_audio(
        self, 
        audio_data: np.ndarray, 
        original_sr: int, 
        target_sr: int
    ) -> Tuple[np.ndarray, int]:
        """
        Rééchantillonne l'audio au taux cible.
        
        Args:
            audio_data: Données audio originales
            original_sr: Taux d'échantillonnage original
            target_sr: Taux d'échantillonnage cible
            
        Returns:
            Tuple (audio rééchantillonné, nouveau taux)
        """
        try:
            import librosa
            
            if original_sr == target_sr:
                return audio_data, target_sr
            
            resampled = librosa.resample(
                audio_data, 
                orig_sr=original_sr, 
                target_sr=target_sr,
                res_type='kaiser_best'  # Qualité maximale
            )
            
            self.logger.info(f"Resampled from {original_sr}Hz to {target_sr}Hz")
            
            return resampled, target_sr
            
        except ImportError:
            # Rééchantillonnage simple sans librosa
            if original_sr == target_sr:
                return audio_data, target_sr
            
            ratio = target_sr / original_sr
            new_length = int(len(audio_data) * ratio)
            
            # Interpolation linéaire simple
            old_indices = np.linspace(0, len(audio_data) - 1, new_length)
            resampled = np.interp(old_indices, np.arange(len(audio_data)), audio_data)
            
            self.logger.warning(f"Simple resampling from {original_sr}Hz to {target_sr}Hz")
            
            return resampled, target_sr
    
    def _apply_frequency_filtering(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int
    ) -> np.ndarray:
        """
        Applique un filtrage fréquentiel optimisé pour la voix.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio filtré
        """
        try:
            from scipy import signal
            
            # Filtre passe-haut pour éliminer les basses fréquences
            nyquist = sample_rate / 2
            high_freq_norm = self.highpass_freq / nyquist
            low_freq_norm = self.lowpass_freq / nyquist
            
            # Vérifier que les fréquences sont valides
            if high_freq_norm >= 1.0 or low_freq_norm >= 1.0:
                self.logger.warning("Filter frequencies too high for sample rate")
                return audio_data
            
            # Filtre passe-bande Butterworth
            sos = signal.butter(
                4,  # Ordre du filtre
                [high_freq_norm, low_freq_norm], 
                btype='band', 
                output='sos'
            )
            
            filtered = signal.sosfilt(sos, audio_data)
            
            self.logger.info(
                f"Applied bandpass filter: {self.highpass_freq}-{self.lowpass_freq}Hz"
            )
            
            return filtered
            
        except ImportError:
            self.logger.warning("scipy not available, skipping frequency filtering")
            return audio_data
        except Exception as e:
            self.logger.warning(f"Frequency filtering failed: {e}")
            return audio_data
    
    def _apply_noise_reduction(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int
    ) -> np.ndarray:
        """
        Applique une réduction de bruit spectrale.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio avec bruit réduit
        """
        try:
            import librosa
            
            # Estimation du bruit à partir des segments silencieux
            # Utiliser les 5% les plus silencieux comme profil de bruit
            sorted_indices = np.argsort(np.abs(audio_data))
            noise_samples = int(0.05 * len(audio_data))
            noise_profile = audio_data[sorted_indices[:noise_samples]]
            
            # STFT pour le traitement spectral
            stft = librosa.stft(audio_data, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimation du spectre de bruit
            noise_stft = librosa.stft(noise_profile, n_fft=2048, hop_length=512)
            noise_magnitude = np.abs(noise_stft)
            noise_spectrum = np.mean(noise_magnitude, axis=1, keepdims=True)
            
            # Soustraction spectrale avec over-subtraction factor
            alpha = 2.0  # Facteur de sur-soustraction
            beta = 0.01  # Plancher spectral
            
            # Calculer le gain de réduction
            snr_estimate = magnitude / (noise_spectrum + 1e-10)
            gain = 1.0 - alpha * (1.0 / (snr_estimate + 1e-10))
            gain = np.maximum(gain, beta)  # Appliquer le plancher
            
            # Appliquer le gain
            cleaned_magnitude = magnitude * gain
            
            # Reconstruction
            cleaned_stft = cleaned_magnitude * np.exp(1j * phase)
            cleaned_audio = librosa.istft(cleaned_stft, hop_length=512)
            
            # Ajuster la longueur si nécessaire
            if len(cleaned_audio) != len(audio_data):
                if len(cleaned_audio) > len(audio_data):
                    cleaned_audio = cleaned_audio[:len(audio_data)]
                else:
                    # Padding avec des zéros
                    padding = len(audio_data) - len(cleaned_audio)
                    cleaned_audio = np.pad(cleaned_audio, (0, padding), 'constant')
            
            self.logger.info("Applied spectral noise reduction")
            
            return cleaned_audio
            
        except ImportError:
            self.logger.warning("librosa not available, skipping noise reduction")
            return audio_data
        except Exception as e:
            self.logger.warning(f"Noise reduction failed: {e}")
            return audio_data
    
    def _apply_noise_gate(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int
    ) -> np.ndarray:
        """
        Applique un gate de bruit pour éliminer les segments silencieux.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio avec gate appliqué
        """
        # Convertir le seuil en amplitude linéaire
        threshold_linear = 10 ** (self.noise_gate_threshold_db / 20)
        
        # Calculer l'enveloppe RMS avec fenêtre glissante
        window_size = int(0.01 * sample_rate)  # 10ms
        if window_size < 1:
            window_size = 1
        
        # Padding pour la convolution
        padded_audio = np.pad(audio_data, window_size//2, mode='reflect')
        
        # Calcul de l'enveloppe RMS
        squared = padded_audio ** 2
        rms_envelope = np.sqrt(np.convolve(
            squared, 
            np.ones(window_size) / window_size, 
            mode='valid'
        ))
        
        # Ajuster la longueur
        if len(rms_envelope) != len(audio_data):
            rms_envelope = rms_envelope[:len(audio_data)]
        
        # Créer le masque de gate avec hystérésis
        gate_mask = rms_envelope > threshold_linear
        
        # Appliquer un lissage pour éviter les clics
        smoothing_samples = int(0.005 * sample_rate)  # 5ms de lissage
        if smoothing_samples > 0:
            # Convolution avec une fenêtre de Hann pour le lissage
            smooth_window = np.hanning(smoothing_samples * 2 + 1)
            smooth_window /= np.sum(smooth_window)
            
            gate_mask_float = gate_mask.astype(float)
            gate_mask_smooth = np.convolve(gate_mask_float, smooth_window, mode='same')
            gate_mask = gate_mask_smooth
        else:
            gate_mask = gate_mask.astype(float)
        
        # Appliquer le gate
        gated_audio = audio_data * gate_mask
        
        # Statistiques
        gated_ratio = np.sum(gate_mask < 0.5) / len(gate_mask)
        self.logger.info(f"Applied noise gate: {gated_ratio:.1%} of audio gated")
        
        return gated_audio
    
    def _normalize_rms_level(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalise le niveau RMS au niveau cible.
        
        Args:
            audio_data: Données audio
            
        Returns:
            Audio normalisé
        """
        # Calculer le RMS actuel
        current_rms = np.sqrt(np.mean(audio_data ** 2))
        
        if current_rms == 0:
            return audio_data
        
        # Calculer le niveau cible en amplitude linéaire
        target_rms_linear = 10 ** (self.target_rms_db / 20)
        
        # Calculer le gain nécessaire
        gain = target_rms_linear / current_rms
        
        # Limiter le gain maximal
        max_gain_linear = 10 ** (self.max_gain_db / 20)
        gain = min(gain, max_gain_linear)
        
        # Appliquer le gain
        normalized = audio_data * gain
        
        # Vérifier qu'il n'y a pas de clipping
        if np.max(np.abs(normalized)) > 0.99:
            # Réduire le gain pour éviter le clipping
            safety_factor = 0.99 / np.max(np.abs(normalized))
            normalized *= safety_factor
            gain *= safety_factor
        
        gain_db = 20 * np.log10(gain)
        self.logger.info(f"Applied RMS normalization: {gain_db:+.1f}dB gain")
        
        return normalized
    
    def _normalize_with_dynamics_preservation(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalise en préservant la dynamique naturelle.
        
        Args:
            audio_data: Données audio
            
        Returns:
            Audio normalisé avec dynamique préservée
        """
        # Calculer l'enveloppe dynamique
        window_size = int(0.1 * 22050)  # 100ms à 22kHz
        if window_size < 1:
            window_size = 1
        
        # Enveloppe RMS glissante
        padded = np.pad(audio_data, window_size//2, mode='reflect')
        squared = padded ** 2
        rms_envelope = np.sqrt(np.convolve(
            squared, 
            np.ones(window_size) / window_size, 
            mode='valid'
        ))
        
        # Ajuster la longueur
        if len(rms_envelope) != len(audio_data):
            rms_envelope = rms_envelope[:len(audio_data)]
        
        # Calculer le gain adaptatif
        target_rms_linear = 10 ** (self.target_rms_db / 20)
        
        # Éviter la division par zéro
        rms_envelope = np.maximum(rms_envelope, 1e-10)
        
        # Gain adaptatif avec compression douce
        gain_envelope = target_rms_linear / rms_envelope
        
        # Appliquer une compression douce (ratio 2:1 au-dessus du seuil)
        compression_threshold = 2.0  # Gain de 2x
        compression_ratio = 0.5  # Ratio 2:1
        
        gain_over_threshold = gain_envelope > compression_threshold
        gain_envelope[gain_over_threshold] = (
            compression_threshold + 
            (gain_envelope[gain_over_threshold] - compression_threshold) * compression_ratio
        )
        
        # Limiter le gain maximal
        max_gain_linear = 10 ** (self.max_gain_db / 20)
        gain_envelope = np.minimum(gain_envelope, max_gain_linear)
        
        # Lissage du gain pour éviter les artefacts
        smoothing_window = int(0.01 * 22050)  # 10ms
        if smoothing_window > 1:
            gain_envelope = np.convolve(
                gain_envelope, 
                np.ones(smoothing_window) / smoothing_window, 
                mode='same'
            )
        
        # Appliquer le gain adaptatif
        normalized = audio_data * gain_envelope
        
        # Vérification finale du clipping
        if np.max(np.abs(normalized)) > 0.99:
            safety_factor = 0.99 / np.max(np.abs(normalized))
            normalized *= safety_factor
        
        avg_gain_db = 20 * np.log10(np.mean(gain_envelope))
        self.logger.info(f"Applied dynamic normalization: {avg_gain_db:+.1f}dB average gain")
        
        return normalized
    
    def _apply_peak_limiting(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Applique une limitation de crête douce.
        
        Args:
            audio_data: Données audio
            
        Returns:
            Audio avec limitation de crête
        """
        # Niveau de crête cible en amplitude linéaire
        target_peak_linear = 10 ** (self.target_peak_db / 20)
        
        # Vérifier si une limitation est nécessaire
        current_peak = np.max(np.abs(audio_data))
        
        if current_peak <= target_peak_linear:
            return audio_data  # Pas de limitation nécessaire
        
        # Limitation douce (soft clipping) avec fonction tanh
        # Calculer le facteur de mise à l'échelle
        scale_factor = target_peak_linear / current_peak
        
        # Appliquer une limitation douce
        # Utiliser tanh pour une limitation progressive
        limited = np.tanh(audio_data / target_peak_linear) * target_peak_linear
        
        # Mélanger avec le signal original pour préserver le caractère
        blend_factor = 0.8  # 80% limité, 20% original mis à l'échelle
        result = (blend_factor * limited + 
                 (1 - blend_factor) * audio_data * scale_factor)
        
        reduction_db = 20 * np.log10(scale_factor)
        self.logger.info(f"Applied peak limiting: {reduction_db:.1f}dB reduction")
        
        return result
    
    def _save_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int, 
        output_path: str
    ):
        """
        Sauvegarde l'audio normalisé.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            output_path: Chemin de sortie
        """
        try:
            import soundfile as sf
            
            # Créer le dossier parent si nécessaire
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder en haute qualité
            sf.write(
                output_path, 
                audio_data, 
                sample_rate, 
                subtype='PCM_24'  # 24-bit pour la qualité maximale
            )
            
            self.logger.info(f"Saved normalized audio to {output_path}")
            
        except ImportError:
            raise ProcessingError("soundfile is required for audio saving")
        except Exception as e:
            raise ProcessingError(f"Failed to save audio: {e}")
    
    def batch_normalize_speaker_files(
        self,
        speaker_files: Dict[str, str],
        output_dir: Optional[str] = None,
        **normalize_kwargs
    ) -> Dict[str, NormalizationResult]:
        """
        Normalise plusieurs fichiers audio par lot.
        
        Args:
            speaker_files: Dictionnaire speaker_id -> chemin fichier
            output_dir: Dossier de sortie (optionnel)
            **normalize_kwargs: Arguments pour la normalisation
            
        Returns:
            Dictionnaire des résultats par locuteur
        """
        results = {}
        
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for speaker_id, audio_path in speaker_files.items():
            try:
                # Définir le chemin de sortie
                if output_dir:
                    output_path = str(Path(output_dir) / f"{speaker_id}_normalized.wav")
                else:
                    output_path = None
                
                # Normaliser
                result = self.normalize_for_voice_cloning(
                    audio_path, 
                    output_path, 
                    **normalize_kwargs
                )
                
                results[speaker_id] = result
                
                self.logger.info(f"Normalized audio for speaker {speaker_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to normalize speaker {speaker_id}: {e}")
                # Continuer avec les autres locuteurs
        
        return results
    
    def validate_audio_quality(
        self, 
        audio_path: str, 
        min_duration: float = 5.0,
        min_snr_db: float = 10.0
    ) -> Tuple[bool, List[str]]:
        """
        Valide la qualité audio pour le clonage de voix.
        
        Args:
            audio_path: Chemin vers le fichier audio
            min_duration: Durée minimale requise
            min_snr_db: SNR minimal requis
            
        Returns:
            Tuple (est_valide, liste_des_problèmes)
        """
        issues = []
        
        try:
            # Charger et analyser l'audio
            audio_data, sample_rate = self._load_audio(audio_path)
            stats = self._calculate_audio_stats(audio_data, sample_rate)
            quality = self._analyze_audio_quality(audio_data, sample_rate)
            
            # Vérifications de qualité
            if stats['duration'] < min_duration:
                issues.append(f"Duration too short: {stats['duration']:.1f}s < {min_duration}s")
            
            if quality.snr_estimate < min_snr_db:
                issues.append(f"SNR too low: {quality.snr_estimate:.1f}dB < {min_snr_db}dB")
            
            if quality.clipping_detected:
                issues.append("Clipping detected in audio")
            
            if stats['clipping_ratio'] > 0.01:
                issues.append(f"High clipping ratio: {stats['clipping_ratio']:.1%}")
            
            if quality.silence_ratio > 0.5:
                issues.append(f"Too much silence: {quality.silence_ratio:.1%}")
            
            if quality.dynamic_range < self.min_dynamic_range_db:
                issues.append(f"Low dynamic range: {quality.dynamic_range:.1f}dB")
            
            if quality.frequency_response_score < 0.3:
                issues.append(f"Poor frequency response: {quality.frequency_response_score:.2f}")
            
            is_valid = len(issues) == 0
            
            return is_valid, issues
            
        except Exception as e:
            issues.append(f"Analysis failed: {e}")
            return False, issues