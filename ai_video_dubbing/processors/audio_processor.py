"""
Processeur audio pour l'application de doublage vidéo par IA.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import tempfile

# Imports conditionnels pour les dépendances audio
try:
    import torch
    import torchaudio
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = None
    torchaudio = None

try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.voice_activity_detection import VoiceActivityDetection
    from pyannote.audio.pipelines.speaker_diarization import SpeakerDiarization
    _PYANNOTE_AVAILABLE = True
except ImportError:
    _PYANNOTE_AVAILABLE = False
    Pipeline = None
    VoiceActivityDetection = None
    SpeakerDiarization = None

try:
    import librosa
    import soundfile as sf
    _LIBROSA_AVAILABLE = True
except ImportError:
    _LIBROSA_AVAILABLE = False
    librosa = None
    sf = None

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    np = None

from ..interfaces.base_interfaces import IAudioProcessor
from ..models.data_models import (
    Interval, SpeakerSegments, SourceSeparationResult, 
    DialogueSegment, ValidationError, ProcessingError
)


class AudioProcessor(IAudioProcessor):
    """Processeur audio avec VAD et diarisation des locuteurs."""
    
    def __init__(self, temp_storage=None):
        """
        Initialise le processeur audio.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage
        self.logger = logging.getLogger(__name__)
        
        # Vérifier les dépendances
        self._check_dependencies()
        
        # Initialiser les pipelines Pyannote si disponible
        self.vad_pipeline = None
        self.diarization_pipeline = None
        
        if _PYANNOTE_AVAILABLE:
            self._initialize_pipelines()
    
    def _check_dependencies(self) -> None:
        """Vérifie la disponibilité des dépendances."""
        if not _LIBROSA_AVAILABLE:
            self.logger.warning("Librosa not available. Audio processing will be limited.")
        
        if not _PYANNOTE_AVAILABLE:
            self.logger.warning("Pyannote.audio not available. VAD and diarization will use fallback methods.")
    
    def _initialize_pipelines(self) -> None:
        """Initialise les pipelines Pyannote.audio."""
        try:
            # Initialiser le pipeline VAD
            self.vad_pipeline = VoiceActivityDetection(segmentation="pyannote/segmentation")
            
            # Initialiser le pipeline de diarisation
            # Note: Nécessite un token HuggingFace pour certains modèles
            try:
                self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
            except Exception as e:
                self.logger.warning(f"Could not load diarization pipeline: {e}")
                self.diarization_pipeline = None
            
            self.logger.info("Pyannote pipelines initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pyannote pipelines: {e}")
            self.vad_pipeline = None
            self.diarization_pipeline = None
    
    def detect_voice_activity(self, audio_path: str) -> List[Interval]:
        """
        Détecte l'activité vocale dans un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Liste des intervalles où il y a de la parole
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        if self.vad_pipeline is not None:
            return self._detect_vad_pyannote(str(audio_path))
        else:
            return self._detect_vad_fallback(str(audio_path))
    
    def _detect_vad_pyannote(self, audio_path: str) -> List[Interval]:
        """Détection VAD avec Pyannote.audio."""
        try:
            # Appliquer le pipeline VAD
            vad_result = self.vad_pipeline(audio_path)
            
            # Convertir les résultats en intervalles
            intervals = []
            for segment in vad_result.get_timeline():
                interval = Interval(
                    start=segment.start,
                    end=segment.end
                )
                intervals.append(interval)
            
            self.logger.info(f"Detected {len(intervals)} speech segments with Pyannote VAD")
            return intervals
            
        except Exception as e:
            self.logger.error(f"Pyannote VAD failed: {e}")
            return self._detect_vad_fallback(audio_path)
    
    def _detect_vad_fallback(self, audio_path: str) -> List[Interval]:
        """Détection VAD de secours basée sur l'énergie."""
        if not _LIBROSA_AVAILABLE:
            raise ProcessingError("Librosa is required for fallback VAD. Please install librosa.")
        
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculer l'énergie RMS
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            rms = librosa.feature.rms(
                y=y, 
                frame_length=frame_length, 
                hop_length=hop_length
            )[0]
            
            # Calculer le seuil adaptatif
            rms_mean = np.mean(rms)
            rms_std = np.std(rms)
            threshold = rms_mean + 0.5 * rms_std
            
            # Détecter les segments de parole
            speech_frames = rms > threshold
            
            # Convertir en intervalles temporels
            intervals = []
            in_speech = False
            start_time = 0
            
            for i, is_speech in enumerate(speech_frames):
                time = i * hop_length / sr
                
                if is_speech and not in_speech:
                    # Début de parole
                    start_time = time
                    in_speech = True
                elif not is_speech and in_speech:
                    # Fin de parole
                    if time - start_time > 0.1:  # Minimum 100ms
                        intervals.append(Interval(start=start_time, end=time))
                    in_speech = False
            
            # Gérer le cas où l'audio se termine pendant la parole
            if in_speech:
                intervals.append(Interval(start=start_time, end=len(y) / sr))
            
            # Fusionner les intervalles proches
            intervals = self._merge_close_intervals(intervals, gap_threshold=0.3)
            
            self.logger.info(f"Detected {len(intervals)} speech segments with fallback VAD")
            return intervals
            
        except Exception as e:
            raise ProcessingError(f"Fallback VAD failed: {e}")
    
    def _merge_close_intervals(self, intervals: List[Interval], gap_threshold: float = 0.3) -> List[Interval]:
        """Fusionne les intervalles proches."""
        if not intervals:
            return []
        
        # Trier par temps de début
        sorted_intervals = sorted(intervals, key=lambda x: x.start)
        merged = [sorted_intervals[0]]
        
        for current in sorted_intervals[1:]:
            last = merged[-1]
            
            # Si l'intervalle actuel est proche du précédent, les fusionner
            if current.start - last.end <= gap_threshold:
                merged[-1] = Interval(start=last.start, end=current.end)
            else:
                merged.append(current)
        
        return merged
    
    def perform_speaker_diarization(self, audio_path: str) -> SpeakerSegments:
        """
        Effectue la diarisation des locuteurs.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Résultats de la diarisation avec segments par locuteur
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        if self.diarization_pipeline is not None:
            return self._diarize_pyannote(str(audio_path))
        else:
            return self._diarize_fallback(str(audio_path))
    
    def _diarize_pyannote(self, audio_path: str) -> SpeakerSegments:
        """Diarisation avec Pyannote.audio."""
        try:
            # Appliquer le pipeline de diarisation
            diarization = self.diarization_pipeline(audio_path)
            
            # Convertir en segments de dialogue
            segments = []
            confidence_scores = {}
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = DialogueSegment(
                    speaker_id=speaker,
                    start_time=turn.start,
                    end_time=turn.end,
                    original_text="",  # Sera rempli plus tard
                    audio_path="",     # Sera rempli plus tard
                    confidence_score=1.0  # Pyannote ne fournit pas de score de confiance direct
                )
                segments.append(segment)
                
                # Calculer le score de confiance moyen par locuteur
                if speaker not in confidence_scores:
                    confidence_scores[speaker] = []
                confidence_scores[speaker].append(1.0)
            
            # Calculer les scores moyens
            avg_confidence_scores = {
                speaker: np.mean(scores) 
                for speaker, scores in confidence_scores.items()
            }
            
            speaker_count = len(set(segment.speaker_id for segment in segments))
            
            result = SpeakerSegments(
                segments=segments,
                speaker_count=speaker_count,
                confidence_scores=avg_confidence_scores
            )
            
            self.logger.info(f"Diarization completed: {speaker_count} speakers, {len(segments)} segments")
            return result
            
        except Exception as e:
            self.logger.error(f"Pyannote diarization failed: {e}")
            return self._diarize_fallback(audio_path)
    
    def _diarize_fallback(self, audio_path: str) -> SpeakerSegments:
        """Diarisation de secours basée sur la détection d'activité vocale."""
        try:
            # Utiliser VAD pour détecter les segments de parole
            speech_intervals = self.detect_voice_activity(audio_path)
            
            # Créer des segments avec un seul locuteur par défaut
            segments = []
            for i, interval in enumerate(speech_intervals):
                segment = DialogueSegment(
                    speaker_id="SPEAKER_00",  # Un seul locuteur par défaut
                    start_time=interval.start,
                    end_time=interval.end,
                    original_text="",
                    audio_path="",
                    confidence_score=0.8  # Score de confiance modéré pour le fallback
                )
                segments.append(segment)
            
            result = SpeakerSegments(
                segments=segments,
                speaker_count=1,
                confidence_scores={"SPEAKER_00": 0.8}
            )
            
            self.logger.warning(f"Fallback diarization: 1 speaker assumed, {len(segments)} segments")
            return result
            
        except Exception as e:
            raise ProcessingError(f"Fallback diarization failed: {e}")
    
    def separate_sources(self, audio_path: str, enable_separation: bool = True) -> SourceSeparationResult:
        """
        Sépare les sources audio (voix, musique, effets) avec Demucs.
        
        Args:
            audio_path: Chemin vers le fichier audio
            enable_separation: Si False, retourne l'audio original sans séparation
            
        Returns:
            Résultats de la séparation avec chemins vers les fichiers séparés
            
        Raises:
            ProcessingError: Si la séparation échoue
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        # Si la séparation est désactivée, retourner l'audio original
        if not enable_separation:
            self.logger.info("Source separation disabled, using original audio")
            return SourceSeparationResult(
                vocals_path=str(audio_path),
                music_path="",
                effects_path="",
                original_path=str(audio_path),
                separation_quality=1.0,
                processing_time=0.0
            )
        
        try:
            import time
            start_time = time.time()
            
            self.logger.info(f"Starting source separation on {audio_path}")
            
            # Créer un répertoire temporaire pour les résultats
            if self.temp_storage:
                output_dir = Path(self.temp_storage.get_temp_path("separation"))
            else:
                output_dir = audio_path.parent / f"{audio_path.stem}_separated"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Essayer d'utiliser Demucs
            separated_files = self._separate_with_demucs(audio_path, output_dir)
            
            if not separated_files:
                # Fallback : utiliser une méthode simple basée sur les fréquences
                self.logger.warning("Demucs separation failed, using frequency-based fallback")
                separated_files = self._separate_with_frequency_filter(audio_path, output_dir)
            
            processing_time = time.time() - start_time
            
            # Évaluer la qualité de séparation
            quality_score = self._evaluate_separation_quality(
                str(audio_path), 
                separated_files.get('vocals', '')
            )
            
            self.logger.info(f"Source separation completed in {processing_time:.2f}s (quality: {quality_score:.2f})")
            
            return SourceSeparationResult(
                vocals_path=separated_files.get('vocals', str(audio_path)),
                music_path=separated_files.get('music', ''),
                effects_path=separated_files.get('drums', ''),  # Demucs utilise 'drums' pour les effets
                original_path=str(audio_path),
                separation_quality=quality_score,
                processing_time=processing_time
            )
            
        except Exception as e:
            # En cas d'erreur, retourner l'audio original
            self.logger.error(f"Source separation failed: {e}")
            self.logger.info("Falling back to original audio")
            
            return SourceSeparationResult(
                vocals_path=str(audio_path),
                music_path="",
                effects_path="",
                original_path=str(audio_path),
                separation_quality=0.5,  # Qualité moyenne car pas de séparation
                processing_time=0.0
            )
    
    def _separate_with_demucs(self, audio_path: Path, output_dir: Path) -> Dict[str, str]:
        """
        Sépare l'audio avec Demucs.
        
        Args:
            audio_path: Chemin vers le fichier audio
            output_dir: Répertoire de sortie
            
        Returns:
            Dictionnaire avec les chemins des fichiers séparés
        """
        try:
            # Essayer d'importer demucs
            try:
                import demucs.api
                _DEMUCS_AVAILABLE = True
            except ImportError:
                self.logger.warning("Demucs not available, trying command line")
                return self._separate_with_demucs_cli(audio_path, output_dir)
            
            self.logger.info("Using Demucs API for source separation")
            
            # Utiliser l'API Demucs
            separator = demucs.api.Separator(model="htdemucs")
            
            # Charger et séparer l'audio
            waveform, sample_rate = demucs.api.load_track(str(audio_path))
            sources = separator(waveform[None])
            
            # Sauvegarder les sources séparées
            separated_files = {}
            source_names = ["drums", "bass", "other", "vocals"]
            
            for i, source_name in enumerate(source_names):
                if i < sources.shape[1]:
                    output_path = output_dir / f"{source_name}.wav"
                    demucs.api.save_audio(
                        sources[0, i], 
                        str(output_path), 
                        sample_rate,
                        clip="rescale"
                    )
                    separated_files[source_name] = str(output_path)
                    self.logger.debug(f"Saved {source_name} to {output_path}")
            
            # Créer un fichier "music" en combinant bass et other
            if "bass" in separated_files and "other" in separated_files:
                music_path = output_dir / "music.wav"
                self._combine_audio_files(
                    [separated_files["bass"], separated_files["other"]], 
                    str(music_path)
                )
                separated_files["music"] = str(music_path)
            
            return separated_files
            
        except Exception as e:
            self.logger.error(f"Demucs API separation failed: {e}")
            return {}
    
    def _separate_with_demucs_cli(self, audio_path: Path, output_dir: Path) -> Dict[str, str]:
        """
        Sépare l'audio avec Demucs en ligne de commande.
        
        Args:
            audio_path: Chemin vers le fichier audio
            output_dir: Répertoire de sortie
            
        Returns:
            Dictionnaire avec les chemins des fichiers séparés
        """
        try:
            import subprocess
            import shutil
            
            # Vérifier si demucs est disponible en ligne de commande
            try:
                subprocess.run(["python", "-m", "demucs", "--help"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("Demucs command line not available")
                return {}
            
            self.logger.info("Using Demucs command line for source separation")
            
            # Exécuter demucs
            cmd = [
                "python", "-m", "demucs", 
                "--two-stems=vocals",  # Séparer en voix et accompagnement
                "-o", str(output_dir),
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Demucs command failed: {result.stderr}")
                return {}
            
            # Chercher les fichiers de sortie
            separated_files = {}
            
            # Demucs crée un sous-répertoire avec le nom du modèle
            model_dir = output_dir / "htdemucs" / audio_path.stem
            
            if model_dir.exists():
                for source_file in model_dir.glob("*.wav"):
                    source_name = source_file.stem
                    # Déplacer vers le répertoire de sortie principal
                    target_path = output_dir / source_file.name
                    shutil.move(str(source_file), str(target_path))
                    separated_files[source_name] = str(target_path)
                
                # Nettoyer le répertoire temporaire
                shutil.rmtree(output_dir / "htdemucs", ignore_errors=True)
            
            return separated_files
            
        except Exception as e:
            self.logger.error(f"Demucs CLI separation failed: {e}")
            return {}
    
    def _separate_with_frequency_filter(self, audio_path: Path, output_dir: Path) -> Dict[str, str]:
        """
        Séparation simple basée sur les filtres de fréquence (fallback).
        
        Args:
            audio_path: Chemin vers le fichier audio
            output_dir: Répertoire de sortie
            
        Returns:
            Dictionnaire avec les chemins des fichiers séparés
        """
        if not _LIBROSA_AVAILABLE:
            self.logger.error("librosa required for frequency-based separation")
            return {}
        
        try:
            self.logger.info("Using frequency-based separation (fallback)")
            
            # Charger l'audio
            y, sr = librosa.load(str(audio_path), sr=None)
            
            # Séparer en utilisant des filtres simples
            # Voix : généralement dans les fréquences moyennes (300-3400 Hz)
            vocals = self._apply_bandpass_filter(y, sr, low_freq=300, high_freq=3400)
            
            # Musique : tout sauf les fréquences vocales
            music = y - vocals * 0.5  # Réduction simple
            
            # Sauvegarder les résultats
            separated_files = {}
            
            vocals_path = output_dir / "vocals.wav"
            sf.write(str(vocals_path), vocals, sr)
            separated_files["vocals"] = str(vocals_path)
            
            music_path = output_dir / "music.wav"
            sf.write(str(music_path), music, sr)
            separated_files["music"] = str(music_path)
            
            self.logger.info("Frequency-based separation completed")
            return separated_files
            
        except Exception as e:
            self.logger.error(f"Frequency-based separation failed: {e}")
            return {}
    
    def _apply_bandpass_filter(self, y, sr: int, low_freq: float, high_freq: float):
        """
        Applique un filtre passe-bande simple.
        
        Args:
            y: Signal audio
            sr: Fréquence d'échantillonnage
            low_freq: Fréquence basse du filtre
            high_freq: Fréquence haute du filtre
            
        Returns:
            Signal filtré
        """
        try:
            # Utiliser la FFT pour filtrer
            fft = np.fft.fft(y)
            freqs = np.fft.fftfreq(len(y), 1/sr)
            
            # Créer le masque de filtre
            mask = (np.abs(freqs) >= low_freq) & (np.abs(freqs) <= high_freq)
            
            # Appliquer le filtre
            fft_filtered = fft * mask
            
            # Retour au domaine temporel
            y_filtered = np.real(np.fft.ifft(fft_filtered))
            
            return y_filtered.astype(y.dtype)
            
        except Exception as e:
            self.logger.error(f"Bandpass filter failed: {e}")
            return y  # Retourner le signal original en cas d'erreur
    
    def _combine_audio_files(self, file_paths: List[str], output_path: str) -> None:
        """
        Combine plusieurs fichiers audio en un seul.
        
        Args:
            file_paths: Liste des chemins des fichiers à combiner
            output_path: Chemin du fichier de sortie
        """
        if not _LIBROSA_AVAILABLE:
            return
        
        try:
            combined_audio = None
            sample_rate = None
            
            for file_path in file_paths:
                if Path(file_path).exists():
                    y, sr = librosa.load(file_path, sr=None)
                    
                    if combined_audio is None:
                        combined_audio = y
                        sample_rate = sr
                    else:
                        # S'assurer que les longueurs correspondent
                        min_length = min(len(combined_audio), len(y))
                        combined_audio = combined_audio[:min_length] + y[:min_length]
            
            if combined_audio is not None and sample_rate is not None:
                sf.write(output_path, combined_audio, sample_rate)
                self.logger.debug(f"Combined audio saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Audio combination failed: {e}")
    
    def _evaluate_separation_quality(self, original_path: str, vocals_path: str) -> float:
        """
        Évalue la qualité de la séparation de source.
        
        Args:
            original_path: Chemin vers l'audio original
            vocals_path: Chemin vers les voix séparées
            
        Returns:
            Score de qualité entre 0 et 1
        """
        if not vocals_path or not Path(vocals_path).exists():
            return 0.0
        
        if not _LIBROSA_AVAILABLE:
            return 0.7  # Score par défaut
        
        try:
            # Charger les audios
            original, sr_orig = librosa.load(original_path, sr=None)
            vocals, sr_vocals = librosa.load(vocals_path, sr=None)
            
            # S'assurer que les fréquences d'échantillonnage correspondent
            if sr_orig != sr_vocals:
                vocals = librosa.resample(vocals, orig_sr=sr_vocals, target_sr=sr_orig)
            
            # Ajuster les longueurs
            min_length = min(len(original), len(vocals))
            original = original[:min_length]
            vocals = vocals[:min_length]
            
            # Calculer des métriques simples
            # 1. Rapport signal/bruit
            noise = original - vocals
            signal_power = np.mean(vocals ** 2)
            noise_power = np.mean(noise ** 2)
            
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                snr_score = min(max(snr / 20, 0), 1)  # Normaliser entre 0 et 1
            else:
                snr_score = 1.0
            
            # 2. Corrélation avec l'original (pour détecter si les voix sont préservées)
            correlation = np.corrcoef(original, vocals)[0, 1]
            correlation_score = max(correlation, 0)  # Seulement les corrélations positives
            
            # Score final (moyenne pondérée)
            quality_score = 0.6 * snr_score + 0.4 * correlation_score
            
            return min(max(quality_score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Quality evaluation failed: {e}")
            return 0.5  # Score par défaut en cas d'erreur
    
    def segment_by_speaker(self, audio_path: str, diarization: SpeakerSegments) -> Dict[str, str]:
        """Segmente l'audio par locuteur - à implémenter dans la tâche 10."""
        raise NotImplementedError("À implémenter dans la tâche 10")
    
    def normalize_audio(self, audio_path: str) -> str:
        """Normalise l'audio - à implémenter dans la tâche 11."""
        raise NotImplementedError("À implémenter dans la tâche 11")
    
    def get_audio_info(self, audio_path: str) -> Dict[str, any]:
        """
        Obtient les informations d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Dictionnaire avec les informations audio
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")
        
        if not _LIBROSA_AVAILABLE:
            return self._get_audio_info_ffprobe(str(audio_path))
        
        try:
            # Charger l'audio avec librosa
            y, sr = librosa.load(str(audio_path), sr=None)
            
            info = {
                'duration': len(y) / sr,
                'sample_rate': sr,
                'channels': 1 if y.ndim == 1 else y.shape[0],
                'samples': len(y),
                'format': audio_path.suffix.lower(),
                'size_bytes': audio_path.stat().st_size
            }
            
            # Calculer des statistiques audio
            info.update({
                'rms_energy': float(np.sqrt(np.mean(y**2))),
                'max_amplitude': float(np.max(np.abs(y))),
                'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y)))
            })
            
            return info
            
        except Exception as e:
            self.logger.warning(f"Librosa audio info failed: {e}")
            return self._get_audio_info_ffprobe(str(audio_path))
    
    def _get_audio_info_ffprobe(self, audio_path: str) -> Dict[str, any]:
        """Obtient les informations audio avec FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise ProcessingError(f"FFprobe failed: {result.stderr}")
            
            import json
            data = json.loads(result.stdout)
            
            format_info = data.get('format', {})
            streams = data.get('streams', [])
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), {})
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'format': format_info.get('format_name', ''),
                'codec': audio_stream.get('codec_name', ''),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'size_bytes': int(format_info.get('size', 0))
            }
            
        except Exception as e:
            raise ProcessingError(f"Failed to get audio info: {e}")
    
    def convert_audio_format(self, input_path: str, output_path: str, 
                           sample_rate: int = 44100, channels: int = 2) -> str:
        """
        Convertit un fichier audio vers un format spécifique.
        
        Args:
            input_path: Chemin du fichier d'entrée
            output_path: Chemin du fichier de sortie
            sample_rate: Fréquence d'échantillonnage cible
            channels: Nombre de canaux cible
            
        Returns:
            Chemin du fichier converti
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise ValidationError(f"Input audio file not found: {input_path}")
        
        # S'assurer que le répertoire de sortie existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if _LIBROSA_AVAILABLE and _LIBROSA_AVAILABLE:
            return self._convert_with_librosa(str(input_path), str(output_path), sample_rate, channels)
        else:
            return self._convert_with_ffmpeg(str(input_path), str(output_path), sample_rate, channels)
    
    def _convert_with_librosa(self, input_path: str, output_path: str, 
                            sample_rate: int, channels: int) -> str:
        """Conversion audio avec librosa."""
        try:
            # Charger l'audio
            y, sr = librosa.load(input_path, sr=sample_rate, mono=(channels == 1))
            
            # Ajuster le nombre de canaux si nécessaire
            if channels == 2 and y.ndim == 1:
                y = np.stack([y, y])  # Convertir mono vers stéréo
            elif channels == 1 and y.ndim == 2:
                y = np.mean(y, axis=0)  # Convertir stéréo vers mono
            
            # Sauvegarder
            sf.write(output_path, y.T if y.ndim == 2 else y, sample_rate)
            
            self.logger.info(f"Audio converted with librosa: {output_path}")
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Librosa conversion failed: {e}")
    
    def _convert_with_ffmpeg(self, input_path: str, output_path: str, 
                           sample_rate: int, channels: int) -> str:
        """Conversion audio avec FFmpeg."""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise ProcessingError(f"FFmpeg conversion failed: {result.stderr}")
            
            self.logger.info(f"Audio converted with FFmpeg: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise ProcessingError("Audio conversion timed out")
        except Exception as e:
            raise ProcessingError(f"FFmpeg conversion failed: {e}")