#!/usr/bin/env python3
"""
Validateur de qualité pour l'application de doublage vidéo par IA.
Valide la qualité audio/vidéo et la synchronisation du résultat final.
"""

import os
import logging
import subprocess
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import wave
import tempfile

from ..models.data_models import ValidationError, ProcessingError


class QualityValidator:
    """Validateur de qualité pour les vidéos doublées."""
    
    def __init__(self):
        """Initialise le validateur de qualité."""
        self.logger = logging.getLogger(__name__)
        
        # Seuils de qualité
        self.quality_thresholds = {
            'min_audio_snr': 20.0,  # dB
            'max_sync_difference': 0.5,  # secondes
            'min_video_bitrate': 1000000,  # bits/s (1 Mbps)
            'min_audio_bitrate': 128000,  # bits/s (128 kbps)
            'max_audio_distortion': 0.05,  # THD
            'min_loudness': -30.0,  # LUFS
            'max_loudness': -16.0,  # LUFS
        }
        
        self.logger.info("Quality validator initialized")
    
    def validate_final_output(self, video_path: str, 
                            original_video_path: str = None) -> Dict[str, Any]:
        """
        Valide la qualité complète de la vidéo finale.
        
        Args:
            video_path: Chemin vers la vidéo finale
            original_video_path: Chemin vers la vidéo originale (pour comparaison)
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        try:
            self.logger.info(f"Starting quality validation for: {video_path}")
            
            validation_results = {
                'video_path': video_path,
                'validation_timestamp': None,
                'overall_quality_score': 0.0,
                'passed_validation': False,
                'issues_found': [],
                'recommendations': [],
                'technical_metrics': {},
                'comparison_metrics': {}
            }
            
            # Vérifier que le fichier existe
            if not os.path.exists(video_path):
                raise ValidationError(f"Video file not found: {video_path}")
            
            # 1. Validation technique de base
            technical_metrics = self._validate_technical_specs(video_path)
            validation_results['technical_metrics'] = technical_metrics
            
            # 2. Validation de la qualité audio
            audio_metrics = self._validate_audio_quality(video_path)
            validation_results['technical_metrics'].update(audio_metrics)
            
            # 3. Validation de la synchronisation
            sync_metrics = self._validate_synchronization(video_path)
            validation_results['technical_metrics'].update(sync_metrics)
            
            # 4. Validation de l'intégrité du fichier
            integrity_check = self._validate_file_integrity(video_path)
            validation_results['technical_metrics'].update(integrity_check)
            
            # 5. Comparaison avec l'original (si disponible)
            if original_video_path and os.path.exists(original_video_path):
                comparison_metrics = self._compare_with_original(
                    video_path, original_video_path
                )
                validation_results['comparison_metrics'] = comparison_metrics
            
            # 6. Calculer le score de qualité global
            quality_score, issues, recommendations = self._calculate_quality_score(
                validation_results['technical_metrics'],
                validation_results['comparison_metrics']
            )
            
            validation_results['overall_quality_score'] = quality_score
            validation_results['issues_found'] = issues
            validation_results['recommendations'] = recommendations
            validation_results['passed_validation'] = quality_score >= 0.7  # 70% minimum
            validation_results['validation_timestamp'] = self._get_timestamp()
            
            self.logger.info(f"Quality validation completed. Score: {quality_score:.2f}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
            raise ProcessingError(f"Quality validation failed: {e}")
    
    def _validate_technical_specs(self, video_path: str) -> Dict[str, Any]:
        """Valide les spécifications techniques de base."""
        try:
            # Utiliser ffprobe pour obtenir les informations
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams', '-show_format',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ProcessingError("Failed to analyze video technical specs")
            
            info = json.loads(result.stdout)
            
            video_stream = None
            audio_stream = None
            
            for stream in info['streams']:
                if stream['codec_type'] == 'video' and video_stream is None:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            metrics = {
                'file_size_mb': round(int(info['format']['size']) / (1024 * 1024), 2),
                'duration': float(info['format']['duration']),
                'format_name': info['format']['format_name'],
                'video_codec': video_stream['codec_name'] if video_stream else None,
                'video_bitrate': int(video_stream.get('bit_rate', 0)) if video_stream else 0,
                'video_width': int(video_stream['width']) if video_stream else 0,
                'video_height': int(video_stream['height']) if video_stream else 0,
                'video_fps': eval(video_stream['r_frame_rate']) if video_stream else 0,
                'audio_codec': audio_stream['codec_name'] if audio_stream else None,
                'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0,
                'audio_sample_rate': int(audio_stream['sample_rate']) if audio_stream else 0,
                'audio_channels': int(audio_stream['channels']) if audio_stream else 0
            }
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Technical specs validation failed: {e}")
            return {}
    
    def _validate_audio_quality(self, video_path: str) -> Dict[str, Any]:
        """Valide la qualité audio spécifique."""
        try:
            # Extraire l'audio temporairement pour analyse
            temp_audio = tempfile.mktemp(suffix='.wav')
            
            cmd = [
                'ffmpeg', '-y', '-v', 'quiet',
                '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2',
                temp_audio
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                raise ProcessingError("Failed to extract audio for quality analysis")
            
            # Analyser l'audio extrait
            audio_metrics = self._analyze_audio_file(temp_audio)
            
            # Nettoyer le fichier temporaire
            try:
                os.remove(temp_audio)
            except:
                pass
            
            return audio_metrics
            
        except Exception as e:
            self.logger.warning(f"Audio quality validation failed: {e}")
            return {}
    
    def _analyze_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """Analyse un fichier audio pour les métriques de qualité."""
        try:
            metrics = {}
            
            # Lire le fichier audio
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                
                # Convertir en numpy array
                if wav_file.getsampwidth() == 2:
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                else:
                    audio_data = np.frombuffer(frames, dtype=np.float32)
                
                # Reshape pour stéréo si nécessaire
                if channels == 2:
                    audio_data = audio_data.reshape(-1, 2)
                    # Prendre la moyenne des canaux pour l'analyse
                    audio_data = np.mean(audio_data, axis=1)
                
                # Normaliser
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Calculer les métriques
            metrics['audio_rms'] = float(np.sqrt(np.mean(audio_data ** 2)))
            metrics['audio_peak'] = float(np.max(np.abs(audio_data)))
            metrics['audio_dynamic_range'] = self._calculate_dynamic_range(audio_data)
            metrics['audio_snr'] = self._estimate_snr(audio_data)
            metrics['audio_thd'] = self._estimate_thd(audio_data, sample_rate)
            metrics['audio_loudness'] = self._estimate_loudness(audio_data)
            
            # Détecter les problèmes
            metrics['has_clipping'] = metrics['audio_peak'] >= 0.99
            metrics['has_silence'] = metrics['audio_rms'] < 0.001
            metrics['is_too_quiet'] = metrics['audio_rms'] < 0.01
            metrics['is_too_loud'] = metrics['audio_rms'] > 0.8
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Audio analysis failed: {e}")
            return {}
    
    def _calculate_dynamic_range(self, audio_data: np.ndarray) -> float:
        """Calcule la plage dynamique de l'audio."""
        try:
            # Calculer RMS par fenêtres
            window_size = len(audio_data) // 100  # 100 fenêtres
            if window_size < 1024:
                window_size = 1024
            
            rms_values = []
            for i in range(0, len(audio_data) - window_size, window_size):
                window = audio_data[i:i + window_size]
                rms = np.sqrt(np.mean(window ** 2))
                if rms > 0:
                    rms_values.append(rms)
            
            if len(rms_values) < 2:
                return 0.0
            
            # Plage dynamique en dB
            max_rms = np.max(rms_values)
            min_rms = np.min(rms_values)
            
            if min_rms > 0:
                dynamic_range = 20 * np.log10(max_rms / min_rms)
                return float(dynamic_range)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _estimate_snr(self, audio_data: np.ndarray) -> float:
        """Estime le rapport signal/bruit."""
        try:
            # Méthode simplifiée : comparer les segments forts vs faibles
            sorted_data = np.sort(np.abs(audio_data))
            
            # 10% des échantillons les plus forts (signal)
            signal_threshold = int(len(sorted_data) * 0.9)
            signal_power = np.mean(sorted_data[signal_threshold:] ** 2)
            
            # 10% des échantillons les plus faibles (bruit)
            noise_power = np.mean(sorted_data[:int(len(sorted_data) * 0.1)] ** 2)
            
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                return float(snr)
            
            return 60.0  # SNR très élevé si pas de bruit détectable
            
        except Exception:
            return 0.0
    
    def _estimate_thd(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Estime la distorsion harmonique totale."""
        try:
            # FFT pour analyse fréquentielle
            fft = np.fft.fft(audio_data[:sample_rate])  # 1 seconde d'analyse
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            
            # Trouver le pic fondamental (entre 80Hz et 2kHz)
            valid_range = (freqs >= 80) & (freqs <= 2000)
            if not np.any(valid_range):
                return 0.0
            
            fundamental_idx = np.argmax(np.abs(fft[valid_range]))
            fundamental_power = np.abs(fft[valid_range][fundamental_idx]) ** 2
            
            # Puissance totale
            total_power = np.sum(np.abs(fft) ** 2)
            
            # THD approximatif
            if fundamental_power > 0:
                thd = np.sqrt((total_power - fundamental_power) / fundamental_power)
                return float(min(thd, 1.0))  # Limiter à 100%
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _estimate_loudness(self, audio_data: np.ndarray) -> float:
        """Estime la loudness en LUFS (approximation)."""
        try:
            # Approximation simple de la loudness
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            if rms > 0:
                # Conversion approximative RMS vers LUFS
                lufs = 20 * np.log10(rms) - 0.691
                return float(lufs)
            
            return -60.0  # Très faible si silence
            
        except Exception:
            return -60.0
    
    def _validate_synchronization(self, video_path: str) -> Dict[str, Any]:
        """Valide la synchronisation audio/vidéo."""
        try:
            # Obtenir les informations des streams
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {}
            
            info = json.loads(result.stdout)
            
            video_duration = None
            audio_duration = None
            
            for stream in info['streams']:
                duration = float(stream.get('duration', 0))
                if stream['codec_type'] == 'video' and video_duration is None:
                    video_duration = duration
                elif stream['codec_type'] == 'audio' and audio_duration is None:
                    audio_duration = duration
            
            sync_metrics = {}
            
            if video_duration and audio_duration:
                sync_difference = abs(video_duration - audio_duration)
                sync_metrics['video_duration'] = video_duration
                sync_metrics['audio_duration'] = audio_duration
                sync_metrics['sync_difference'] = sync_difference
                sync_metrics['sync_quality'] = max(0.0, 1.0 - (sync_difference / 2.0))
                sync_metrics['is_synchronized'] = sync_difference < self.quality_thresholds['max_sync_difference']
            
            return sync_metrics
            
        except Exception as e:
            self.logger.warning(f"Synchronization validation failed: {e}")
            return {}
    
    def _validate_file_integrity(self, video_path: str) -> Dict[str, Any]:
        """Valide l'intégrité du fichier vidéo."""
        try:
            # Vérifier que le fichier peut être lu complètement
            cmd = [
                'ffmpeg', '-v', 'error',
                '-i', video_path,
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            integrity_metrics = {
                'file_readable': result.returncode == 0,
                'corruption_errors': len(result.stderr.split('\n')) if result.stderr else 0,
                'file_size_bytes': os.path.getsize(video_path) if os.path.exists(video_path) else 0
            }
            
            # Vérifier la taille minimale (au moins 1MB)
            integrity_metrics['sufficient_size'] = integrity_metrics['file_size_bytes'] > 1024 * 1024
            
            return integrity_metrics
            
        except Exception as e:
            self.logger.warning(f"File integrity validation failed: {e}")
            return {'file_readable': False}
    
    def _compare_with_original(self, dubbed_path: str, original_path: str) -> Dict[str, Any]:
        """Compare la vidéo doublée avec l'originale."""
        try:
            # Obtenir les métriques des deux vidéos
            dubbed_metrics = self._validate_technical_specs(dubbed_path)
            original_metrics = self._validate_technical_specs(original_path)
            
            comparison = {
                'duration_preserved': abs(dubbed_metrics.get('duration', 0) - 
                                        original_metrics.get('duration', 0)) < 1.0,
                'resolution_preserved': (dubbed_metrics.get('video_width', 0) == 
                                       original_metrics.get('video_width', 0) and
                                       dubbed_metrics.get('video_height', 0) == 
                                       original_metrics.get('video_height', 0)),
                'fps_preserved': abs(dubbed_metrics.get('video_fps', 0) - 
                                   original_metrics.get('video_fps', 0)) < 0.1,
                'size_ratio': (dubbed_metrics.get('file_size_mb', 0) / 
                             max(original_metrics.get('file_size_mb', 1), 1))
            }
            
            # Évaluer si les changements sont acceptables
            comparison['acceptable_changes'] = (
                comparison['duration_preserved'] and
                comparison['resolution_preserved'] and
                0.5 <= comparison['size_ratio'] <= 3.0  # Taille entre 50% et 300% de l'original
            )
            
            return comparison
            
        except Exception as e:
            self.logger.warning(f"Comparison with original failed: {e}")
            return {}
    
    def _calculate_quality_score(self, 
                                technical_metrics: Dict[str, Any],
                                comparison_metrics: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Calcule le score de qualité global."""
        score = 0.0
        issues = []
        recommendations = []
        
        # Poids des différents aspects
        weights = {
            'technical': 0.4,
            'audio': 0.3,
            'sync': 0.2,
            'integrity': 0.1
        }
        
        # Score technique
        technical_score = 0.0
        if technical_metrics.get('video_bitrate', 0) >= self.quality_thresholds['min_video_bitrate']:
            technical_score += 0.3
        else:
            issues.append("Video bitrate below recommended minimum")
            recommendations.append("Increase video bitrate for better quality")
        
        if technical_metrics.get('audio_bitrate', 0) >= self.quality_thresholds['min_audio_bitrate']:
            technical_score += 0.3
        else:
            issues.append("Audio bitrate below recommended minimum")
            recommendations.append("Increase audio bitrate for better quality")
        
        if technical_metrics.get('duration', 0) > 0:
            technical_score += 0.4
        
        # Score audio
        audio_score = 0.0
        if technical_metrics.get('audio_snr', 0) >= self.quality_thresholds['min_audio_snr']:
            audio_score += 0.4
        else:
            issues.append("Audio signal-to-noise ratio below threshold")
            recommendations.append("Improve audio quality or noise reduction")
        
        if not technical_metrics.get('has_clipping', True):
            audio_score += 0.3
        else:
            issues.append("Audio clipping detected")
            recommendations.append("Reduce audio levels to prevent clipping")
        
        if not technical_metrics.get('is_too_quiet', True) and not technical_metrics.get('is_too_loud', True):
            audio_score += 0.3
        else:
            issues.append("Audio levels not optimal")
            recommendations.append("Normalize audio levels")
        
        # Score synchronisation
        sync_score = 0.0
        if technical_metrics.get('is_synchronized', False):
            sync_score = 1.0
        else:
            sync_diff = technical_metrics.get('sync_difference', float('inf'))
            if sync_diff < 1.0:
                sync_score = 0.7
                issues.append("Minor synchronization issues detected")
                recommendations.append("Fine-tune audio/video synchronization")
            else:
                issues.append("Significant synchronization problems")
                recommendations.append("Re-synchronize audio and video tracks")
        
        # Score intégrité
        integrity_score = 0.0
        if technical_metrics.get('file_readable', False):
            integrity_score += 0.5
        else:
            issues.append("File integrity issues detected")
            recommendations.append("Re-encode the video file")
        
        if technical_metrics.get('sufficient_size', False):
            integrity_score += 0.5
        else:
            issues.append("Output file size suspiciously small")
            recommendations.append("Check encoding settings")
        
        # Calculer le score final
        final_score = (
            technical_score * weights['technical'] +
            audio_score * weights['audio'] +
            sync_score * weights['sync'] +
            integrity_score * weights['integrity']
        )
        
        return final_score, issues, recommendations
    
    def _get_timestamp(self) -> str:
        """Obtient un timestamp pour la validation."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def generate_quality_report(self, validation_results: Dict[str, Any]) -> str:
        """Génère un rapport de qualité lisible."""
        try:
            report_lines = [
                "=== RAPPORT DE QUALITÉ VIDÉO ===",
                "",
                f"Fichier analysé: {validation_results['video_path']}",
                f"Date de validation: {validation_results['validation_timestamp']}",
                f"Score de qualité global: {validation_results['overall_quality_score']:.2f}/1.00",
                f"Validation réussie: {'✅ OUI' if validation_results['passed_validation'] else '❌ NON'}",
                "",
                "=== MÉTRIQUES TECHNIQUES ===",
            ]
            
            # Ajouter les métriques techniques
            for key, value in validation_results['technical_metrics'].items():
                if isinstance(value, float):
                    report_lines.append(f"{key}: {value:.3f}")
                else:
                    report_lines.append(f"{key}: {value}")
            
            # Ajouter les problèmes détectés
            if validation_results['issues_found']:
                report_lines.extend([
                    "",
                    "=== PROBLÈMES DÉTECTÉS ===",
                ])
                for issue in validation_results['issues_found']:
                    report_lines.append(f"• {issue}")
            
            # Ajouter les recommandations
            if validation_results['recommendations']:
                report_lines.extend([
                    "",
                    "=== RECOMMANDATIONS ===",
                ])
                for rec in validation_results['recommendations']:
                    report_lines.append(f"• {rec}")
            
            report_lines.extend([
                "",
                "=== FIN DU RAPPORT ==="
            ])
            
            return '\n'.join(report_lines)
            
        except Exception as e:
            self.logger.warning(f"Quality report generation failed: {e}")
            return "Erreur lors de la génération du rapport de qualité"