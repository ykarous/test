#!/usr/bin/env python3
"""
Processeur de segmentation audio par locuteur pour l'application de doublage vidéo par IA.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

from ..models.data_models import (
    DialogueSegment, SpeakerSegments, ProcessingError, ValidationError
)
from ..utils.temp_storage import TempStorage


@dataclass
class SegmentationResult:
    """Résultat de la segmentation audio par locuteur."""
    speaker_audio_files: Dict[str, str]  # speaker_id -> chemin fichier audio
    segment_mapping: Dict[str, List[DialogueSegment]]  # speaker_id -> segments
    total_duration_per_speaker: Dict[str, float]  # speaker_id -> durée totale
    quality_metrics: Dict[str, Any]
    processing_time: float


@dataclass
class AudioSegment:
    """Segment audio individuel."""
    speaker_id: str
    start_time: float
    end_time: float
    audio_data: np.ndarray
    sample_rate: int
    confidence_score: float
    segment_index: int


class SpeakerSegmentationProcessor:
    """Processeur de segmentation audio par locuteur."""
    
    def __init__(self, temp_storage: Optional[TempStorage] = None):
        """
        Initialise le processeur de segmentation.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage or TempStorage()
        self.logger = logging.getLogger(__name__)
        
        # Configuration par défaut
        self.min_segment_duration = 0.5  # Durée minimale d'un segment (secondes)
        self.max_gap_duration = 0.2  # Durée maximale de silence à ignorer
        self.fade_duration = 0.05  # Durée du fade in/out
        
    def segment_audio_by_speaker(
        self,
        audio_file_path: str,
        speaker_segments: SpeakerSegments,
        output_format: str = "wav",
        normalize_audio: bool = True,
        concatenate_segments: bool = True
    ) -> SegmentationResult:
        """
        Segmente l'audio par locuteur.
        
        Args:
            audio_file_path: Chemin vers le fichier audio original
            speaker_segments: Segments de diarisation des locuteurs
            output_format: Format de sortie (wav, flac, mp3)
            normalize_audio: Normaliser le volume des segments
            concatenate_segments: Concaténer les segments par locuteur
            
        Returns:
            Résultats de la segmentation
            
        Raises:
            ProcessingError: Si la segmentation échoue
        """
        if not speaker_segments.segments:
            raise ValidationError("No speaker segments provided")
        
        if not Path(audio_file_path).exists():
            raise ValidationError(f"Audio file not found: {audio_file_path}")
        
        try:
            import time
            start_time = time.time()
            
            self.logger.info(f"Starting speaker segmentation for {len(speaker_segments.segments)} segments")
            
            # Charger l'audio original
            audio_data, sample_rate = self._load_audio(audio_file_path)
            
            # Extraire les segments par locuteur
            speaker_audio_segments = self._extract_speaker_segments(
                audio_data, sample_rate, speaker_segments
            )
            
            # Valider la qualité des segments
            quality_metrics = self._validate_segment_quality(speaker_audio_segments)
            
            # Créer les fichiers audio par locuteur
            if concatenate_segments:
                speaker_files = self._create_concatenated_speaker_files(
                    speaker_audio_segments, sample_rate, output_format, normalize_audio
                )
            else:
                speaker_files = self._create_individual_segment_files(
                    speaker_audio_segments, sample_rate, output_format, normalize_audio
                )
            
            # Calculer les statistiques
            segment_mapping = self._create_segment_mapping(speaker_segments)
            duration_stats = self._calculate_duration_statistics(speaker_audio_segments)
            
            processing_time = time.time() - start_time
            
            result = SegmentationResult(
                speaker_audio_files=speaker_files,
                segment_mapping=segment_mapping,
                total_duration_per_speaker=duration_stats,
                quality_metrics=quality_metrics,
                processing_time=processing_time
            )
            
            self.logger.info(
                f"Speaker segmentation completed in {processing_time:.2f}s "
                f"({len(speaker_files)} speakers processed)"
            )
            
            return result
            
        except Exception as e:
            raise ProcessingError(f"Speaker segmentation failed: {e}")
    
    def _load_audio(self, audio_file_path: str) -> Tuple[np.ndarray, int]:
        """
        Charge le fichier audio.
        
        Args:
            audio_file_path: Chemin vers le fichier audio
            
        Returns:
            Tuple (données audio, taux d'échantillonnage)
        """
        try:
            import librosa
            
            # Charger l'audio avec librosa
            audio_data, sample_rate = librosa.load(
                audio_file_path, 
                sr=None,  # Conserver le taux d'échantillonnage original
                mono=True  # Convertir en mono
            )
            
            self.logger.info(
                f"Loaded audio: {len(audio_data)/sample_rate:.2f}s "
                f"at {sample_rate}Hz"
            )
            
            return audio_data, sample_rate
            
        except ImportError:
            raise ProcessingError("librosa is required for audio processing")
        except Exception as e:
            raise ProcessingError(f"Failed to load audio file: {e}")
    
    def _extract_speaker_segments(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        speaker_segments: SpeakerSegments
    ) -> Dict[str, List[AudioSegment]]:
        """
        Extrait les segments audio pour chaque locuteur.
        
        Args:
            audio_data: Données audio complètes
            sample_rate: Taux d'échantillonnage
            speaker_segments: Segments de diarisation
            
        Returns:
            Dictionnaire des segments audio par locuteur
        """
        speaker_audio_segments = {}
        
        for i, segment in enumerate(speaker_segments.segments):
            speaker_id = segment.speaker_id
            
            # Convertir les timestamps en indices d'échantillons
            start_sample = int(segment.start_time * sample_rate)
            end_sample = int(segment.end_time * sample_rate)
            
            # Vérifier les limites
            start_sample = max(0, start_sample)
            end_sample = min(len(audio_data), end_sample)
            
            # Vérifier la durée minimale
            duration = (end_sample - start_sample) / sample_rate
            if duration < self.min_segment_duration:
                self.logger.warning(
                    f"Segment {i} too short ({duration:.3f}s), skipping"
                )
                continue
            
            # Extraire le segment audio
            segment_audio = audio_data[start_sample:end_sample].copy()
            
            # Appliquer un fade in/out pour éviter les clics
            segment_audio = self._apply_fade(segment_audio, sample_rate)
            
            # Créer l'objet AudioSegment
            audio_segment = AudioSegment(
                speaker_id=speaker_id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                audio_data=segment_audio,
                sample_rate=sample_rate,
                confidence_score=segment.confidence_score,
                segment_index=i
            )
            
            # Ajouter au dictionnaire
            if speaker_id not in speaker_audio_segments:
                speaker_audio_segments[speaker_id] = []
            speaker_audio_segments[speaker_id].append(audio_segment)
        
        self.logger.info(
            f"Extracted segments for {len(speaker_audio_segments)} speakers"
        )
        
        return speaker_audio_segments
    
    def _apply_fade(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Applique un fade in/out au segment audio.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio avec fade appliqué
        """
        fade_samples = int(self.fade_duration * sample_rate)
        
        if len(audio_data) <= 2 * fade_samples:
            # Segment trop court pour le fade
            return audio_data
        
        # Fade in
        fade_in = np.linspace(0, 1, fade_samples)
        audio_data[:fade_samples] *= fade_in
        
        # Fade out
        fade_out = np.linspace(1, 0, fade_samples)
        audio_data[-fade_samples:] *= fade_out
        
        return audio_data
    
    def _validate_segment_quality(
        self, 
        speaker_audio_segments: Dict[str, List[AudioSegment]]
    ) -> Dict[str, Any]:
        """
        Valide la qualité des segments audio.
        
        Args:
            speaker_audio_segments: Segments audio par locuteur
            
        Returns:
            Métriques de qualité
        """
        quality_metrics = {
            "total_speakers": len(speaker_audio_segments),
            "total_segments": sum(len(segments) for segments in speaker_audio_segments.values()),
            "speaker_statistics": {},
            "quality_warnings": []
        }
        
        for speaker_id, segments in speaker_audio_segments.items():
            # Calculer les statistiques par locuteur
            durations = [seg.end_time - seg.start_time for seg in segments]
            confidences = [seg.confidence_score for seg in segments]
            
            # Calculer les niveaux audio (RMS)
            rms_levels = []
            for segment in segments:
                rms = np.sqrt(np.mean(segment.audio_data ** 2))
                rms_levels.append(rms)
            
            speaker_stats = {
                "segment_count": len(segments),
                "total_duration": sum(durations),
                "average_duration": np.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "average_confidence": np.mean(confidences),
                "min_confidence": min(confidences),
                "average_rms": np.mean(rms_levels),
                "rms_std": np.std(rms_levels)
            }
            
            quality_metrics["speaker_statistics"][speaker_id] = speaker_stats
            
            # Vérifications de qualité
            if speaker_stats["average_confidence"] < 0.5:
                quality_metrics["quality_warnings"].append(
                    f"Low confidence for speaker {speaker_id}: {speaker_stats['average_confidence']:.3f}"
                )
            
            if speaker_stats["total_duration"] < 5.0:
                quality_metrics["quality_warnings"].append(
                    f"Short total duration for speaker {speaker_id}: {speaker_stats['total_duration']:.1f}s"
                )
            
            if speaker_stats["average_rms"] < 0.01:
                quality_metrics["quality_warnings"].append(
                    f"Low audio level for speaker {speaker_id}: {speaker_stats['average_rms']:.4f}"
                )
        
        return quality_metrics
    
    def _create_concatenated_speaker_files(
        self,
        speaker_audio_segments: Dict[str, List[AudioSegment]],
        sample_rate: int,
        output_format: str,
        normalize_audio: bool
    ) -> Dict[str, str]:
        """
        Crée des fichiers audio concaténés par locuteur.
        
        Args:
            speaker_audio_segments: Segments audio par locuteur
            sample_rate: Taux d'échantillonnage
            output_format: Format de sortie
            normalize_audio: Normaliser l'audio
            
        Returns:
            Dictionnaire speaker_id -> chemin fichier
        """
        speaker_files = {}
        
        for speaker_id, segments in speaker_audio_segments.items():
            if not segments:
                continue
            
            # Trier les segments par ordre chronologique
            segments.sort(key=lambda x: x.start_time)
            
            # Concaténer les segments avec des silences entre eux
            concatenated_audio = self._concatenate_segments_with_gaps(
                segments, sample_rate
            )
            
            # Normaliser si demandé
            if normalize_audio:
                concatenated_audio = self._normalize_audio(concatenated_audio)
            
            # Créer le fichier de sortie
            output_path = self.temp_storage.get_temp_path(
                f"speaker_{speaker_id}.{output_format}"
            )
            
            self._save_audio(
                concatenated_audio, sample_rate, output_path, output_format
            )
            
            speaker_files[speaker_id] = output_path
            
            self.logger.info(
                f"Created concatenated file for speaker {speaker_id}: "
                f"{len(concatenated_audio)/sample_rate:.2f}s"
            )
        
        return speaker_files
    
    def _create_individual_segment_files(
        self,
        speaker_audio_segments: Dict[str, List[AudioSegment]],
        sample_rate: int,
        output_format: str,
        normalize_audio: bool
    ) -> Dict[str, str]:
        """
        Crée des fichiers audio individuels pour chaque segment.
        
        Args:
            speaker_audio_segments: Segments audio par locuteur
            sample_rate: Taux d'échantillonnage
            output_format: Format de sortie
            normalize_audio: Normaliser l'audio
            
        Returns:
            Dictionnaire speaker_id -> dossier contenant les segments
        """
        speaker_directories = {}
        
        for speaker_id, segments in speaker_audio_segments.items():
            if not segments:
                continue
            
            # Créer un dossier pour ce locuteur
            speaker_dir = self.temp_storage.get_temp_path(f"speaker_{speaker_id}")
            os.makedirs(speaker_dir, exist_ok=True)
            
            segment_files = []
            
            for i, segment in enumerate(segments):
                # Normaliser si demandé
                audio_data = segment.audio_data
                if normalize_audio:
                    audio_data = self._normalize_audio(audio_data)
                
                # Créer le fichier de segment
                segment_filename = f"segment_{i:03d}_{segment.start_time:.3f}s.{output_format}"
                segment_path = os.path.join(speaker_dir, segment_filename)
                
                self._save_audio(audio_data, sample_rate, segment_path, output_format)
                segment_files.append(segment_path)
            
            speaker_directories[speaker_id] = speaker_dir
            
            self.logger.info(
                f"Created {len(segment_files)} individual files for speaker {speaker_id}"
            )
        
        return speaker_directories
    
    def _concatenate_segments_with_gaps(
        self, 
        segments: List[AudioSegment], 
        sample_rate: int
    ) -> np.ndarray:
        """
        Concatène les segments audio avec des silences appropriés.
        
        Args:
            segments: Liste des segments à concaténer
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Audio concaténé
        """
        if not segments:
            return np.array([])
        
        concatenated_parts = []
        
        for i, segment in enumerate(segments):
            # Ajouter le segment audio
            concatenated_parts.append(segment.audio_data)
            
            # Ajouter un silence entre les segments (sauf pour le dernier)
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                gap_duration = next_segment.start_time - segment.end_time
                
                # Limiter la durée du silence
                gap_duration = min(gap_duration, self.max_gap_duration)
                
                if gap_duration > 0:
                    silence_samples = int(gap_duration * sample_rate)
                    silence = np.zeros(silence_samples)
                    concatenated_parts.append(silence)
        
        return np.concatenate(concatenated_parts)
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalise l'audio pour optimiser le niveau.
        
        Args:
            audio_data: Données audio à normaliser
            
        Returns:
            Audio normalisé
        """
        if len(audio_data) == 0:
            return audio_data
        
        # Calculer le niveau RMS
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        if rms == 0:
            return audio_data
        
        # Normaliser à -12dB RMS (niveau optimal pour le clonage de voix)
        target_rms = 0.25  # Environ -12dB
        normalization_factor = target_rms / rms
        
        # Limiter le gain pour éviter la saturation
        max_gain = 0.95 / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else 1.0
        normalization_factor = min(normalization_factor, max_gain)
        
        normalized_audio = audio_data * normalization_factor
        
        return normalized_audio
    
    def _save_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int, 
        output_path: str, 
        output_format: str
    ):
        """
        Sauvegarde les données audio dans un fichier.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            output_path: Chemin de sortie
            output_format: Format de sortie
        """
        try:
            import soundfile as sf
            
            # Créer le dossier parent si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Sauvegarder selon le format
            if output_format.lower() == "wav":
                sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            elif output_format.lower() == "flac":
                sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            elif output_format.lower() == "mp3":
                # Pour MP3, utiliser pydub si disponible
                try:
                    from pydub import AudioSegment
                    from pydub.utils import make_chunks
                    
                    # Convertir en format pydub
                    audio_segment = AudioSegment(
                        audio_data.tobytes(),
                        frame_rate=sample_rate,
                        sample_width=audio_data.dtype.itemsize,
                        channels=1
                    )
                    
                    audio_segment.export(output_path, format="mp3", bitrate="192k")
                    
                except ImportError:
                    # Fallback vers WAV si pydub n'est pas disponible
                    wav_path = output_path.replace('.mp3', '.wav')
                    sf.write(wav_path, audio_data, sample_rate, subtype='PCM_16')
                    self.logger.warning(f"MP3 not supported, saved as WAV: {wav_path}")
            else:
                # Format par défaut : WAV
                sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            
        except ImportError:
            raise ProcessingError("soundfile is required for audio saving")
        except Exception as e:
            raise ProcessingError(f"Failed to save audio file: {e}")
    
    def _create_segment_mapping(
        self, 
        speaker_segments: SpeakerSegments
    ) -> Dict[str, List[DialogueSegment]]:
        """
        Crée un mapping des segments par locuteur.
        
        Args:
            speaker_segments: Segments de diarisation
            
        Returns:
            Dictionnaire speaker_id -> liste de segments
        """
        segment_mapping = {}
        
        for segment in speaker_segments.segments:
            speaker_id = segment.speaker_id
            
            if speaker_id not in segment_mapping:
                segment_mapping[speaker_id] = []
            
            segment_mapping[speaker_id].append(segment)
        
        # Trier les segments par ordre chronologique
        for speaker_id in segment_mapping:
            segment_mapping[speaker_id].sort(key=lambda x: x.start_time)
        
        return segment_mapping
    
    def _calculate_duration_statistics(
        self, 
        speaker_audio_segments: Dict[str, List[AudioSegment]]
    ) -> Dict[str, float]:
        """
        Calcule les statistiques de durée par locuteur.
        
        Args:
            speaker_audio_segments: Segments audio par locuteur
            
        Returns:
            Dictionnaire speaker_id -> durée totale
        """
        duration_stats = {}
        
        for speaker_id, segments in speaker_audio_segments.items():
            total_duration = sum(
                segment.end_time - segment.start_time for segment in segments
            )
            duration_stats[speaker_id] = total_duration
        
        return duration_stats
    
    def merge_speaker_segments(
        self,
        speaker_files: Dict[str, str],
        output_path: str,
        crossfade_duration: float = 0.1
    ) -> str:
        """
        Fusionne les segments de tous les locuteurs en un seul fichier.
        
        Args:
            speaker_files: Dictionnaire des fichiers par locuteur
            output_path: Chemin de sortie
            crossfade_duration: Durée du crossfade entre segments
            
        Returns:
            Chemin du fichier fusionné
        """
        try:
            import soundfile as sf
            from pydub import AudioSegment
            
            if not speaker_files:
                raise ValidationError("No speaker files to merge")
            
            # Charger tous les fichiers audio
            audio_segments = []
            for speaker_id, file_path in speaker_files.items():
                audio_segment = AudioSegment.from_file(file_path)
                audio_segments.append((speaker_id, audio_segment))
            
            # Fusionner avec crossfade
            merged_audio = audio_segments[0][1]
            
            for i in range(1, len(audio_segments)):
                speaker_id, audio_segment = audio_segments[i]
                
                # Appliquer un crossfade
                crossfade_ms = int(crossfade_duration * 1000)
                merged_audio = merged_audio.append(audio_segment, crossfade=crossfade_ms)
            
            # Exporter le résultat
            merged_audio.export(output_path, format="wav")
            
            self.logger.info(f"Merged {len(speaker_files)} speaker files into {output_path}")
            
            return output_path
            
        except ImportError:
            raise ProcessingError("pydub is required for audio merging")
        except Exception as e:
            raise ProcessingError(f"Failed to merge speaker segments: {e}")
    
    def extract_speaker_samples(
        self,
        speaker_audio_segments: Dict[str, List[AudioSegment]],
        sample_duration: float = 10.0,
        min_quality_threshold: float = 0.7
    ) -> Dict[str, List[str]]:
        """
        Extrait des échantillons de qualité pour chaque locuteur.
        
        Args:
            speaker_audio_segments: Segments audio par locuteur
            sample_duration: Durée souhaitée des échantillons
            min_quality_threshold: Seuil de qualité minimum
            
        Returns:
            Dictionnaire speaker_id -> liste de chemins d'échantillons
        """
        speaker_samples = {}
        
        for speaker_id, segments in speaker_audio_segments.items():
            # Filtrer les segments de bonne qualité
            quality_segments = [
                seg for seg in segments 
                if seg.confidence_score >= min_quality_threshold
                and (seg.end_time - seg.start_time) >= 2.0  # Au moins 2 secondes
            ]
            
            if not quality_segments:
                self.logger.warning(f"No quality segments found for speaker {speaker_id}")
                continue
            
            # Trier par confiance décroissante
            quality_segments.sort(key=lambda x: x.confidence_score, reverse=True)
            
            samples = []
            current_duration = 0.0
            
            for segment in quality_segments:
                if current_duration >= sample_duration:
                    break
                
                # Créer un échantillon à partir de ce segment
                sample_path = self.temp_storage.get_temp_path(
                    f"sample_{speaker_id}_{len(samples):02d}.wav"
                )
                
                self._save_audio(
                    segment.audio_data, 
                    segment.sample_rate, 
                    sample_path, 
                    "wav"
                )
                
                samples.append(sample_path)
                current_duration += segment.end_time - segment.start_time
            
            speaker_samples[speaker_id] = samples
            
            self.logger.info(
                f"Extracted {len(samples)} samples for speaker {speaker_id} "
                f"({current_duration:.1f}s total)"
            )
        
        return speaker_samples