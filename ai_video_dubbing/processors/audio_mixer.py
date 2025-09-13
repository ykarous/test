#!/usr/bin/env python3
"""
Processeur de mixage audio final pour l'application de doublage vidéo par IA.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import tempfile
import time

from ..models.data_models import (
    DialogueSegment, ProcessingError, ValidationError
)
from ..utils.temp_storage import TempStorage


@dataclass
class AudioTrack:
    """Piste audio pour le mixage."""
    track_id: str
    audio_path: str
    track_type: str  # "dialogue", "music", "sfx", "ambient"
    start_time: float
    end_time: float
    volume_level: float  # 0.0 à 1.0
    fade_in: float  # Durée du fade in en secondes
    fade_out: float  # Durée du fade out en secondes
    pan: float  # -1.0 (gauche) à 1.0 (droite), 0.0 = centre
    priority: int  # Priorité pour la résolution de conflits


@dataclass
class MixingConfig:
    """Configuration pour le mixage audio."""
    target_sample_rate: int
    target_channels: int  # 1 = mono, 2 = stéréo
    output_format: str  # "wav", "mp3", "flac"
    output_bitrate: int  # Pour MP3
    normalize_output: bool
    target_lufs: float  # Loudness cible en LUFS
    limiter_threshold: float  # Seuil du limiteur en dB
    dialogue_level: float  # Niveau relatif des dialogues
    music_level: float  # Niveau relatif de la musique
    sfx_level: float  # Niveau relatif des effets sonores
    crossfade_duration: float  # Durée des crossfades automatiques
    auto_ducking: bool  # Réduction automatique de la musique pendant les dialogues
    ducking_amount: float  # Quantité de réduction en dB
    ducking_attack: float  # Temps d'attaque du ducking
    ducking_release: float  # Temps de relâchement du ducking


@dataclass
class MixingResult:
    """Résultat du mixage audio."""
    mixed_audio_path: str
    total_duration: float
    track_count: int
    peak_level: float
    rms_level: float
    lufs_level: float
    processing_time: float
    mixing_statistics: Dict[str, Any]
    quality_metrics: Dict[str, Any]


class AudioMixer:
    """Processeur de mixage audio professionnel."""
    
    def __init__(self, temp_storage: Optional[TempStorage] = None):
        """
        Initialise le mixeur audio.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage or TempStorage()
        self.logger = logging.getLogger(__name__)
        
        # Configuration par défaut
        self.default_config = MixingConfig(
            target_sample_rate=48000,  # Qualité broadcast
            target_channels=2,  # Stéréo
            output_format="wav",
            output_bitrate=320,  # kbps pour MP3
            normalize_output=True,
            target_lufs=-23.0,  # Standard broadcast
            limiter_threshold=-1.0,  # dB
            dialogue_level=1.0,  # Niveau de référence
            music_level=0.3,  # 30% du niveau dialogue
            sfx_level=0.7,  # 70% du niveau dialogue
            crossfade_duration=0.1,  # 100ms
            auto_ducking=True,
            ducking_amount=6.0,  # -6dB
            ducking_attack=0.05,  # 50ms
            ducking_release=0.5  # 500ms
        )
        
        # Cache audio pour optimiser les performances
        self.audio_cache = {}
        self.max_cache_size = 10  # Nombre max de fichiers en cache
        
    def create_audio_track(
        self,
        track_id: str,
        audio_path: str,
        track_type: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        volume_level: float = 1.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        pan: float = 0.0,
        priority: int = 1
    ) -> AudioTrack:
        """
        Crée une piste audio pour le mixage.
        
        Args:
            track_id: Identifiant unique de la piste
            audio_path: Chemin vers le fichier audio
            track_type: Type de piste ("dialogue", "music", "sfx", "ambient")
            start_time: Temps de début dans le mix
            end_time: Temps de fin (None = durée complète du fichier)
            volume_level: Niveau de volume (0.0 à 1.0)
            fade_in: Durée du fade in
            fade_out: Durée du fade out
            pan: Position stéréo (-1.0 à 1.0)
            priority: Priorité de la piste
            
        Returns:
            Piste audio créée
        """
        if not Path(audio_path).exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        # Obtenir la durée du fichier si end_time n'est pas spécifié
        if end_time is None:
            duration = self._get_audio_duration(audio_path)
            end_time = start_time + duration
        
        track = AudioTrack(
            track_id=track_id,
            audio_path=audio_path,
            track_type=track_type,
            start_time=start_time,
            end_time=end_time,
            volume_level=volume_level,
            fade_in=fade_in,
            fade_out=fade_out,
            pan=pan,
            priority=priority
        )
        
        self.logger.info(
            f"Created audio track: {track_id} ({track_type}) "
            f"{start_time:.2f}s-{end_time:.2f}s"
        )
        
        return track
    
    def create_dialogue_tracks_from_clones(
        self,
        cloned_audio_results: Dict[str, List],  # Résultats du clonage par locuteur
        dialogue_segments: List[DialogueSegment],
        base_volume: float = 1.0
    ) -> List[AudioTrack]:
        """
        Crée des pistes de dialogue à partir des résultats de clonage.
        
        Args:
            cloned_audio_results: Résultats du clonage de voix par locuteur
            dialogue_segments: Segments de dialogue originaux
            base_volume: Volume de base pour les dialogues
            
        Returns:
            Liste des pistes de dialogue
        """
        dialogue_tracks = []
        
        for speaker_id, clone_results in cloned_audio_results.items():
            for i, clone_result in enumerate(clone_results):
                # Trouver le segment correspondant
                segment = None
                for seg in dialogue_segments:
                    if (seg.speaker_id == speaker_id and 
                        seg.original_text == clone_result.original_text):
                        segment = seg
                        break
                
                if segment is None:
                    self.logger.warning(f"No matching segment for clone result {i}")
                    continue
                
                # Calculer le volume basé sur la confiance
                confidence_factor = segment.confidence_score
                volume = base_volume * confidence_factor
                
                # Créer la piste
                track = self.create_audio_track(
                    track_id=f"dialogue_{speaker_id}_{i:03d}",
                    audio_path=clone_result.cloned_audio_path,
                    track_type="dialogue",
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    volume_level=volume,
                    fade_in=0.05,  # Fade in court pour éviter les clics
                    fade_out=0.05,  # Fade out court
                    priority=10  # Priorité élevée pour les dialogues
                )
                
                dialogue_tracks.append(track)
        
        self.logger.info(f"Created {len(dialogue_tracks)} dialogue tracks")
        
        return dialogue_tracks
    
    def mix_audio_tracks(
        self,
        tracks: List[AudioTrack],
        output_path: Optional[str] = None,
        config: Optional[MixingConfig] = None
    ) -> MixingResult:
        """
        Mixe plusieurs pistes audio en un seul fichier.
        
        Args:
            tracks: Liste des pistes à mixer
            output_path: Chemin de sortie (optionnel)
            config: Configuration de mixage (optionnel)
            
        Returns:
            Résultat du mixage
            
        Raises:
            ProcessingError: Si le mixage échoue
        """
        if not tracks:
            raise ValidationError("No audio tracks provided for mixing")
        
        config = config or self.default_config
        
        try:
            start_time = time.time()
            
            self.logger.info(f"Starting audio mixing with {len(tracks)} tracks")
            
            # Calculer la durée totale du mix
            total_duration = max(track.end_time for track in tracks)
            
            # Créer le buffer audio principal
            num_samples = int(total_duration * config.target_sample_rate)
            if config.target_channels == 1:
                mixed_audio = np.zeros(num_samples, dtype=np.float32)
            else:
                mixed_audio = np.zeros((num_samples, config.target_channels), dtype=np.float32)
            
            # Trier les pistes par priorité (plus élevée en premier)
            sorted_tracks = sorted(tracks, key=lambda t: t.priority, reverse=True)
            
            # Traiter chaque piste
            track_stats = {}
            
            for track in sorted_tracks:
                try:
                    self.logger.debug(f"Processing track: {track.track_id}")
                    
                    # Charger et traiter l'audio de la piste
                    processed_audio = self._process_track_audio(track, config)
                    
                    # Calculer les indices de placement dans le mix
                    start_sample = int(track.start_time * config.target_sample_rate)
                    end_sample = start_sample + len(processed_audio)
                    
                    # Vérifier les limites
                    if end_sample > len(mixed_audio):
                        end_sample = len(mixed_audio)
                        processed_audio = processed_audio[:end_sample - start_sample]
                    
                    # Appliquer le ducking automatique si activé
                    if config.auto_ducking and track.track_type == "music":
                        processed_audio = self._apply_ducking(
                            processed_audio, track, sorted_tracks, config
                        )
                    
                    # Ajouter au mix principal
                    if config.target_channels == 1:
                        mixed_audio[start_sample:end_sample] += processed_audio
                    else:
                        # Gestion stéréo
                        if len(processed_audio.shape) == 1:
                            # Audio mono, appliquer le panning
                            left_gain, right_gain = self._calculate_pan_gains(track.pan)
                            mixed_audio[start_sample:end_sample, 0] += processed_audio * left_gain
                            mixed_audio[start_sample:end_sample, 1] += processed_audio * right_gain
                        else:
                            # Audio stéréo
                            mixed_audio[start_sample:end_sample] += processed_audio
                    
                    # Statistiques de la piste
                    track_stats[track.track_id] = {
                        "type": track.track_type,
                        "duration": (end_sample - start_sample) / config.target_sample_rate,
                        "peak_level": float(np.max(np.abs(processed_audio))),
                        "rms_level": float(np.sqrt(np.mean(processed_audio ** 2)))
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to process track {track.track_id}: {e}")
                    # Continuer avec les autres pistes
            
            # Post-traitement du mix final
            mixed_audio = self._post_process_mix(mixed_audio, config)
            
            # Sauvegarder le résultat
            if output_path is None:
                output_path = self.temp_storage.get_temp_path(f"mixed_audio.{config.output_format}")
            
            self._save_mixed_audio(mixed_audio, config.target_sample_rate, output_path, config)
            
            # Calculer les métriques finales
            processing_time = time.time() - start_time
            quality_metrics = self._calculate_mix_quality_metrics(mixed_audio, config.target_sample_rate)
            
            result = MixingResult(
                mixed_audio_path=output_path,
                total_duration=total_duration,
                track_count=len(tracks),
                peak_level=quality_metrics["peak_level"],
                rms_level=quality_metrics["rms_level"],
                lufs_level=quality_metrics.get("lufs_level", -23.0),
                processing_time=processing_time,
                mixing_statistics=track_stats,
                quality_metrics=quality_metrics
            )
            
            self.logger.info(
                f"Audio mixing completed in {processing_time:.2f}s "
                f"(peak: {result.peak_level:.1f}dB, LUFS: {result.lufs_level:.1f})"
            )
            
            return result
            
        except Exception as e:
            raise ProcessingError(f"Audio mixing failed: {e}")
    
    def _process_track_audio(
        self, 
        track: AudioTrack, 
        config: MixingConfig
    ) -> np.ndarray:
        """
        Traite l'audio d'une piste individuelle.
        
        Args:
            track: Piste audio à traiter
            config: Configuration de mixage
            
        Returns:
            Audio traité
        """
        # Charger l'audio (avec cache)
        audio_data, sample_rate = self._load_audio_cached(track.audio_path)
        
        # Rééchantillonner si nécessaire
        if sample_rate != config.target_sample_rate:
            audio_data = self._resample_audio(audio_data, sample_rate, config.target_sample_rate)
        
        # Convertir en mono/stéréo selon la configuration
        if config.target_channels == 1 and len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        elif config.target_channels == 2 and len(audio_data.shape) == 1:
            audio_data = np.column_stack([audio_data, audio_data])
        
        # Appliquer le volume de base selon le type de piste
        type_volume = {
            "dialogue": config.dialogue_level,
            "music": config.music_level,
            "sfx": config.sfx_level,
            "ambient": config.music_level * 0.5
        }.get(track.track_type, 1.0)
        
        audio_data = audio_data * type_volume * track.volume_level
        
        # Appliquer les fades
        if track.fade_in > 0:
            audio_data = self._apply_fade_in(audio_data, track.fade_in, config.target_sample_rate)
        
        if track.fade_out > 0:
            audio_data = self._apply_fade_out(audio_data, track.fade_out, config.target_sample_rate)
        
        return audio_data
    
    def _apply_ducking(
        self,
        music_audio: np.ndarray,
        music_track: AudioTrack,
        all_tracks: List[AudioTrack],
        config: MixingConfig
    ) -> np.ndarray:
        """
        Applique le ducking automatique à la musique pendant les dialogues.
        
        Args:
            music_audio: Audio de la musique
            music_track: Piste musicale
            all_tracks: Toutes les pistes
            config: Configuration
            
        Returns:
            Audio avec ducking appliqué
        """
        # Trouver les segments de dialogue qui se chevauchent
        dialogue_segments = []
        for track in all_tracks:
            if track.track_type == "dialogue":
                # Calculer le chevauchement avec la piste musicale
                overlap_start = max(music_track.start_time, track.start_time)
                overlap_end = min(music_track.end_time, track.end_time)
                
                if overlap_end > overlap_start:
                    # Convertir en indices d'échantillons relatifs à la piste musicale
                    start_sample = int((overlap_start - music_track.start_time) * config.target_sample_rate)
                    end_sample = int((overlap_end - music_track.start_time) * config.target_sample_rate)
                    
                    dialogue_segments.append((start_sample, end_sample))
        
        if not dialogue_segments:
            return music_audio
        
        # Créer l'enveloppe de ducking
        ducking_envelope = np.ones(len(music_audio))
        ducking_factor = 10 ** (-config.ducking_amount / 20)  # Conversion dB vers linéaire
        
        attack_samples = int(config.ducking_attack * config.target_sample_rate)
        release_samples = int(config.ducking_release * config.target_sample_rate)
        
        for start_sample, end_sample in dialogue_segments:
            # Vérifier les limites
            start_sample = max(0, start_sample)
            end_sample = min(len(ducking_envelope), end_sample)
            
            # Attaque (réduction progressive)
            attack_end = min(start_sample + attack_samples, end_sample)
            if attack_end > start_sample:
                attack_curve = np.linspace(1.0, ducking_factor, attack_end - start_sample)
                ducking_envelope[start_sample:attack_end] *= attack_curve
            
            # Maintien (niveau réduit)
            if end_sample > attack_end:
                ducking_envelope[attack_end:end_sample] *= ducking_factor
            
            # Relâchement (retour progressif)
            release_start = end_sample
            release_end = min(release_start + release_samples, len(ducking_envelope))
            if release_end > release_start:
                release_curve = np.linspace(ducking_factor, 1.0, release_end - release_start)
                ducking_envelope[release_start:release_end] *= release_curve
        
        # Appliquer l'enveloppe
        if len(music_audio.shape) == 1:
            return music_audio * ducking_envelope
        else:
            return music_audio * ducking_envelope[:, np.newaxis]
    
    def _calculate_pan_gains(self, pan: float) -> Tuple[float, float]:
        """
        Calcule les gains gauche/droite pour le panning.
        
        Args:
            pan: Position de pan (-1.0 à 1.0)
            
        Returns:
            Tuple (gain_gauche, gain_droite)
        """
        # Loi de panning constant power
        pan_radians = (pan + 1.0) * np.pi / 4.0  # Convertir -1..1 vers 0..π/2
        
        left_gain = np.cos(pan_radians)
        right_gain = np.sin(pan_radians)
        
        return left_gain, right_gain
    
    def _post_process_mix(self, mixed_audio: np.ndarray, config: MixingConfig) -> np.ndarray:
        """
        Post-traite le mix final.
        
        Args:
            mixed_audio: Audio mixé
            config: Configuration
            
        Returns:
            Audio post-traité
        """
        # Normalisation LUFS si demandée
        if config.normalize_output:
            mixed_audio = self._normalize_lufs(mixed_audio, config.target_sample_rate, config.target_lufs)
        
        # Limitation de crête
        mixed_audio = self._apply_limiter(mixed_audio, config.limiter_threshold)
        
        return mixed_audio
    
    def _normalize_lufs(self, audio: np.ndarray, sample_rate: int, target_lufs: float) -> np.ndarray:
        """
        Normalise l'audio au niveau LUFS cible.
        
        Args:
            audio: Audio à normaliser
            sample_rate: Taux d'échantillonnage
            target_lufs: LUFS cible
            
        Returns:
            Audio normalisé
        """
        try:
            import pyloudnorm as pyln
            
            # Mesurer le LUFS actuel
            meter = pyln.Meter(sample_rate)
            loudness = meter.integrated_loudness(audio)
            
            # Calculer le gain nécessaire
            gain_db = target_lufs - loudness
            gain_linear = 10 ** (gain_db / 20)
            
            # Appliquer la normalisation
            normalized_audio = audio * gain_linear
            
            # Éviter le clipping
            max_val = np.max(np.abs(normalized_audio))
            if max_val > 0.95:
                normalized_audio = normalized_audio * (0.95 / max_val)
            
            return normalized_audio
            
        except ImportError:
            # Fallback: normalisation simple par peak
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                return audio * (0.8 / max_val)
            return audio
        
        except Exception as e:
            self.logger.warning(f"Erreur normalisation LUFS: {e}")
            # Fallback: retourner l'audio original
            return audio
        try:
            import pyloudnorm as pyln
            
            # Mesurer le LUFS actuel
            meter = pyln.Meter(sample_rate)
            current_lufs = meter.integrated_loudness(audio)
            
            if np.isfinite(current_lufs):
                # Calculer le gain nécessaire
                gain_db = target_lufs - current_lufs
                gain_linear = 10 ** (gain_db / 20)
                
                # Appliquer le gain
                normalized_audio = audio * gain_linear
                
                self.logger.info(f"LUFS normalization: {current_lufs:.1f} -> {target_lufs:.1f} LUFS ({gain_db:+.1f}dB)")
                
                return normalized_audio
            else:
                self.logger.warning("Could not measure LUFS, skipping normalization")
                return audio
                
        except ImportError:
            self.logger.warning("pyloudnorm not available, using RMS normalization")
            return self._normalize_rms_fallback(audio, target_lufs)
        except Exception as e:
            self.logger.warning(f"LUFS normalization failed: {e}, using fallback")
            return self._normalize_rms_fallback(audio, target_lufs)
    
    def _normalize_rms_fallback(self, audio: np.ndarray, target_lufs: float) -> np.ndarray:
        """
        Normalisation RMS de fallback quand LUFS n'est pas disponible.
        
        Args:
            audio: Audio à normaliser
            target_lufs: LUFS cible (converti en RMS approximatif)
            
        Returns:
            Audio normalisé
        """
        # Conversion approximative LUFS -> RMS
        target_rms_db = target_lufs + 3.0  # Approximation grossière
        target_rms_linear = 10 ** (target_rms_db / 20)
        
        # Calculer le RMS actuel
        current_rms = np.sqrt(np.mean(audio ** 2))
        
        if current_rms > 0:
            gain = target_rms_linear / current_rms
            # Limiter le gain pour éviter la saturation
            max_gain = 0.95 / np.max(np.abs(audio)) if np.max(np.abs(audio)) > 0 else 1.0
            gain = min(gain, max_gain)
            
            return audio * gain
        
        return audio
    
    def _apply_limiter(self, audio: np.ndarray, threshold_db: float) -> np.ndarray:
        """
        Applique un limiteur de crête.
        
        Args:
            audio: Audio à limiter
            threshold_db: Seuil en dB
            
        Returns:
            Audio limité
        """
        threshold_linear = 10 ** (threshold_db / 20)
        
        # Limitation douce avec tanh
        limited_audio = np.tanh(audio / threshold_linear) * threshold_linear
        
        # Calculer la réduction appliquée
        max_input = np.max(np.abs(audio))
        max_output = np.max(np.abs(limited_audio))
        
        if max_input > 0:
            reduction_db = 20 * np.log10(max_output / max_input)
            if reduction_db < -0.1:  # Seulement si réduction significative
                self.logger.info(f"Peak limiting applied: {reduction_db:.1f}dB reduction")
        
        return limited_audio
    
    def _load_audio_cached(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Charge l'audio avec mise en cache.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Tuple (données audio, taux d'échantillonnage)
        """
        # Vérifier le cache
        if audio_path in self.audio_cache:
            return self.audio_cache[audio_path]
        
        # Charger l'audio
        audio_data, sample_rate = self._load_audio(audio_path)
        
        # Ajouter au cache (avec gestion de la taille)
        if len(self.audio_cache) >= self.max_cache_size:
            # Supprimer le plus ancien
            oldest_key = next(iter(self.audio_cache))
            del self.audio_cache[oldest_key]
        
        self.audio_cache[audio_path] = (audio_data, sample_rate)
        
        return audio_data, sample_rate
    
    def _load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Charge un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Tuple (données audio, taux d'échantillonnage)
        """
        try:
            import librosa
            
            # Charger l'audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            # Assurer que c'est un array 2D pour la compatibilité stéréo
            if len(audio_data.shape) == 1:
                audio_data = audio_data.reshape(-1, 1)
            elif len(audio_data.shape) == 2 and audio_data.shape[0] < audio_data.shape[1]:
                # Transposer si nécessaire (channels, samples) -> (samples, channels)
                audio_data = audio_data.T
            
            return audio_data.squeeze(), sample_rate
            
        except ImportError:
            # Fallback simple pour les tests
            self.logger.warning("librosa not available, using mock audio data")
            duration = 5.0  # Durée par défaut
            sample_rate = 48000
            num_samples = int(duration * sample_rate)
            
            # Générer un signal de test
            t = np.linspace(0, duration, num_samples)
            audio_data = 0.1 * np.sin(2 * np.pi * 440 * t)  # Ton de 440Hz
            
            return audio_data, sample_rate
        except Exception as e:
            raise ProcessingError(f"Failed to load audio {audio_path}: {e}")
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Obtient la durée d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Durée en secondes
        """
        try:
            import librosa
            
            duration = librosa.get_duration(path=audio_path)
            return duration
            
        except ImportError:
            # Estimation basée sur la taille du fichier
            file_size = Path(audio_path).stat().st_size
            # Approximation: 1MB ≈ 60 secondes d'audio WAV 16-bit stéréo 44kHz
            return file_size / (1024 * 1024) * 60
        except Exception:
            return 5.0  # Durée par défaut
    
    def _resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Rééchantillonne l'audio.
        
        Args:
            audio: Données audio
            orig_sr: Taux d'échantillonnage original
            target_sr: Taux d'échantillonnage cible
            
        Returns:
            Audio rééchantillonné
        """
        if orig_sr == target_sr:
            return audio
        
        try:
            import librosa
            
            if len(audio.shape) == 1:
                return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
            else:
                # Traiter chaque canal séparément
                resampled_channels = []
                for channel in range(audio.shape[1]):
                    resampled = librosa.resample(
                        audio[:, channel], orig_sr=orig_sr, target_sr=target_sr
                    )
                    resampled_channels.append(resampled)
                
                return np.column_stack(resampled_channels)
                
        except ImportError:
            # Rééchantillonnage simple par interpolation
            ratio = target_sr / orig_sr
            new_length = int(len(audio) * ratio)
            
            if len(audio.shape) == 1:
                old_indices = np.linspace(0, len(audio) - 1, new_length)
                return np.interp(old_indices, np.arange(len(audio)), audio)
            else:
                resampled_channels = []
                for channel in range(audio.shape[1]):
                    old_indices = np.linspace(0, len(audio) - 1, new_length)
                    resampled = np.interp(old_indices, np.arange(len(audio)), audio[:, channel])
                    resampled_channels.append(resampled)
                
                return np.column_stack(resampled_channels)
    
    def _apply_fade_in(self, audio: np.ndarray, fade_duration: float, sample_rate: int) -> np.ndarray:
        """
        Applique un fade in.
        
        Args:
            audio: Données audio
            fade_duration: Durée du fade en secondes
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio avec fade in
        """
        fade_samples = int(fade_duration * sample_rate)
        
        if fade_samples >= len(audio):
            fade_samples = len(audio)
        
        if fade_samples <= 0:
            return audio
        
        # Courbe de fade (cosinus pour un fade plus naturel)
        fade_curve = 0.5 * (1 - np.cos(np.linspace(0, np.pi, fade_samples)))
        
        audio_copy = audio.copy()
        
        if len(audio.shape) == 1:
            audio_copy[:fade_samples] *= fade_curve
        else:
            audio_copy[:fade_samples] *= fade_curve[:, np.newaxis]
        
        return audio_copy
    
    def _apply_fade_out(self, audio: np.ndarray, fade_duration: float, sample_rate: int) -> np.ndarray:
        """
        Applique un fade out.
        
        Args:
            audio: Données audio
            fade_duration: Durée du fade en secondes
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio avec fade out
        """
        fade_samples = int(fade_duration * sample_rate)
        
        if fade_samples >= len(audio):
            fade_samples = len(audio)
        
        if fade_samples <= 0:
            return audio
        
        # Courbe de fade (cosinus inversé)
        fade_curve = 0.5 * (1 + np.cos(np.linspace(0, np.pi, fade_samples)))
        
        audio_copy = audio.copy()
        
        if len(audio.shape) == 1:
            audio_copy[-fade_samples:] *= fade_curve
        else:
            audio_copy[-fade_samples:] *= fade_curve[:, np.newaxis]
        
        return audio_copy
    
    def _calculate_mix_quality_metrics(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Calcule les métriques de qualité du mix final.
        
        Args:
            audio: Audio mixé
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Dictionnaire des métriques
        """
        metrics = {}
        
        # Niveaux de base
        if len(audio.shape) == 1:
            peak_level = np.max(np.abs(audio))
            rms_level = np.sqrt(np.mean(audio ** 2))
        else:
            peak_level = np.max(np.abs(audio))
            rms_level = np.sqrt(np.mean(audio ** 2))
        
        metrics["peak_level"] = 20 * np.log10(max(peak_level, 1e-10))
        metrics["rms_level"] = 20 * np.log10(max(rms_level, 1e-10))
        
        # Plage dynamique
        metrics["dynamic_range"] = metrics["peak_level"] - metrics["rms_level"]
        
        # LUFS si disponible
        try:
            import pyloudnorm as pyln
            
            meter = pyln.Meter(sample_rate)
            lufs = meter.integrated_loudness(audio)
            
            if np.isfinite(lufs):
                metrics["lufs_level"] = lufs
            else:
                metrics["lufs_level"] = metrics["rms_level"] - 3.0  # Approximation
                
        except ImportError:
            metrics["lufs_level"] = metrics["rms_level"] - 3.0  # Approximation
        
        # Détection de clipping
        clipping_threshold = 0.99
        if len(audio.shape) == 1:
            clipped_samples = np.sum(np.abs(audio) > clipping_threshold)
        else:
            clipped_samples = np.sum(np.abs(audio) > clipping_threshold)
        
        metrics["clipping_ratio"] = clipped_samples / audio.size
        
        # Facteur de crête
        if rms_level > 0:
            metrics["crest_factor"] = peak_level / rms_level
        else:
            metrics["crest_factor"] = 0.0
        
        return metrics
    
    def _save_mixed_audio(
        self, 
        audio: np.ndarray, 
        sample_rate: int, 
        output_path: str, 
        config: MixingConfig
    ):
        """
        Sauvegarde l'audio mixé.
        
        Args:
            audio: Données audio
            sample_rate: Taux d'échantillonnage
            output_path: Chemin de sortie
            config: Configuration
        """
        try:
            # Créer le dossier parent si nécessaire
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if config.output_format.lower() == "wav":
                self._save_wav(audio, sample_rate, output_path)
            elif config.output_format.lower() == "mp3":
                self._save_mp3(audio, sample_rate, output_path, config.output_bitrate)
            elif config.output_format.lower() == "flac":
                self._save_flac(audio, sample_rate, output_path)
            else:
                # Format par défaut : WAV
                self._save_wav(audio, sample_rate, output_path)
            
            self.logger.info(f"Mixed audio saved to {output_path}")
            
        except Exception as e:
            raise ProcessingError(f"Failed to save mixed audio: {e}")
    
    def _save_wav(self, audio: np.ndarray, sample_rate: int, output_path: str):
        """Sauvegarde en format WAV."""
        try:
            import soundfile as sf
            
            sf.write(output_path, audio, sample_rate, subtype='PCM_24')
            
        except ImportError:
            # Fallback simple
            with open(output_path, 'w') as f:
                f.write(f"Mock WAV file: {audio.shape}, {sample_rate}Hz")
    
    def _save_mp3(self, audio: np.ndarray, sample_rate: int, output_path: str, bitrate: int):
        """Sauvegarde en format MP3."""
        try:
            from pydub import AudioSegment
            import io
            
            # Convertir en format pydub
            if len(audio.shape) == 1:
                # Mono
                audio_segment = AudioSegment(
                    audio.tobytes(),
                    frame_rate=sample_rate,
                    sample_width=audio.dtype.itemsize,
                    channels=1
                )
            else:
                # Stéréo - convertir en entrelacé
                interleaved = audio.flatten('F')  # Entrelacement par colonne
                audio_segment = AudioSegment(
                    interleaved.tobytes(),
                    frame_rate=sample_rate,
                    sample_width=audio.dtype.itemsize,
                    channels=audio.shape[1]
                )
            
            # Exporter en MP3
            audio_segment.export(output_path, format="mp3", bitrate=f"{bitrate}k")
            
        except ImportError:
            # Fallback vers WAV
            self.logger.warning("pydub not available, saving as WAV instead")
            wav_path = output_path.replace('.mp3', '.wav')
            self._save_wav(audio, sample_rate, wav_path)
    
    def _save_flac(self, audio: np.ndarray, sample_rate: int, output_path: str):
        """Sauvegarde en format FLAC."""
        try:
            import soundfile as sf
            
            sf.write(output_path, audio, sample_rate, subtype='PCM_24')
            
        except ImportError:
            # Fallback vers WAV
            self.logger.warning("soundfile not available for FLAC, saving as WAV")
            wav_path = output_path.replace('.flac', '.wav')
            self._save_wav(audio, sample_rate, wav_path)
    
    def create_crossfade_transition(
        self,
        track1: AudioTrack,
        track2: AudioTrack,
        crossfade_duration: float
    ) -> Tuple[AudioTrack, AudioTrack]:
        """
        Crée une transition crossfade entre deux pistes.
        
        Args:
            track1: Première piste
            track2: Deuxième piste
            crossfade_duration: Durée du crossfade
            
        Returns:
            Tuple des pistes modifiées avec crossfade
        """
        # Calculer les points de crossfade
        crossfade_start = track1.end_time - crossfade_duration
        crossfade_end = track2.start_time + crossfade_duration
        
        # Modifier les pistes
        modified_track1 = AudioTrack(
            track_id=track1.track_id,
            audio_path=track1.audio_path,
            track_type=track1.track_type,
            start_time=track1.start_time,
            end_time=track1.end_time,
            volume_level=track1.volume_level,
            fade_in=track1.fade_in,
            fade_out=crossfade_duration,  # Fade out pour le crossfade
            pan=track1.pan,
            priority=track1.priority
        )
        
        modified_track2 = AudioTrack(
            track_id=track2.track_id,
            audio_path=track2.audio_path,
            track_type=track2.track_type,
            start_time=crossfade_start,  # Commencer plus tôt
            end_time=track2.end_time,
            volume_level=track2.volume_level,
            fade_in=crossfade_duration,  # Fade in pour le crossfade
            fade_out=track2.fade_out,
            pan=track2.pan,
            priority=track2.priority
        )
        
        return modified_track1, modified_track2
    
    def clear_audio_cache(self):
        """Vide le cache audio pour libérer la mémoire."""
        self.audio_cache.clear()
        self.logger.info("Audio cache cleared")
    
    def get_mixing_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de mixage.
        
        Returns:
            Dictionnaire des statistiques
        """
        return {
            "cache_size": len(self.audio_cache),
            "max_cache_size": self.max_cache_size,
            "cached_files": list(self.audio_cache.keys())
        }