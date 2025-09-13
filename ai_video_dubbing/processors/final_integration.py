#!/usr/bin/env python3
"""
Intégrateur final pour l'application de doublage vidéo par IA.
Gère l'intégration complète de tous les composants et l'export final.
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess
import json

from ..models.data_models import (
    PipelineConfig, ProcessingResults, DialogueSegment,
    ValidationError, ProcessingError, VideoMetadata
)
from ..utils.file_manager import FileManager
from ..utils.output_manager import OutputManager
from .pipeline_orchestrator import PipelineOrchestrator


class FinalIntegrator:
    """Intégrateur final pour l'assemblage et l'export vidéo."""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialise l'intégrateur final.
        
        Args:
            config: Configuration du pipeline
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Gestionnaires
        self.file_manager = FileManager()
        self.output_manager = OutputManager()
        
        # Paramètres d'export par défaut
        self.default_export_settings = {
            'video_codec': 'libx264',
            'audio_codec': 'aac',
            'video_bitrate': '5M',
            'audio_bitrate': '192k',
            'preset': 'medium',
            'crf': 23,  # Constant Rate Factor pour qualité
            'audio_sample_rate': 44100,
            'audio_channels': 2
        }
        
        self.logger.info("Final integrator initialized")
    
    def integrate_and_export(self, 
                           original_video_path: str,
                           processing_results: ProcessingResults,
                           export_settings: Dict[str, Any] = None) -> ProcessingResults:
        """
        Intègre tous les composants et exporte la vidéo finale.
        
        Args:
            original_video_path: Chemin vers la vidéo originale
            processing_results: Résultats du traitement pipeline
            export_settings: Paramètres d'export personnalisés
            
        Returns:
            Résultats mis à jour avec le chemin final
        """
        try:
            self.logger.info("Starting final integration and export")
            start_time = time.time()
            
            # Fusionner les paramètres d'export
            final_export_settings = self.default_export_settings.copy()
            if export_settings:
                final_export_settings.update(export_settings)
            
            # Étape 1: Valider les entrées
            self._validate_inputs(original_video_path, processing_results)
            
            # Étape 2: Préparer les chemins de sortie
            output_paths = self._prepare_output_paths(original_video_path)
            
            # Étape 3: Optimiser l'audio final
            optimized_audio_path = self._optimize_final_audio(
                processing_results, final_export_settings
            )
            
            # Étape 4: Synchroniser précisément l'audio avec la vidéo
            synchronized_audio_path = self._synchronize_audio_video(
                original_video_path, optimized_audio_path
            )
            
            # Étape 5: Exporter avec différents codecs et qualités
            export_results = self._export_multiple_formats(
                original_video_path,
                synchronized_audio_path,
                output_paths,
                final_export_settings
            )
            
            # Étape 6: Valider la synchronisation audio/vidéo
            sync_validation = self._validate_audio_video_sync(
                export_results['main_output']
            )
            
            # Étape 7: Créer la documentation et les métadonnées
            documentation_paths = self._create_documentation(
                processing_results, export_results, sync_validation
            )
            
            # Étape 8: Nettoyer les fichiers temporaires
            self._cleanup_temporary_files(processing_results)
            
            # Mettre à jour les résultats
            integration_time = time.time() - start_time
            
            updated_results = ProcessingResults(
                output_video_path=export_results['main_output'],
                processing_time=processing_results.processing_time + integration_time,
                transcription_result=processing_results.transcription_result,
                speaker_segments=processing_results.speaker_segments,
                ocr_results=processing_results.ocr_results,
                source_separation_result=processing_results.source_separation_result,
                success=True,
                error_message="",
                speakers_detected=processing_results.speakers_detected,
                dialogue_segments=processing_results.dialogue_segments,
                quality_metrics={
                    **processing_results.quality_metrics,
                    **sync_validation,
                    'integration_time': integration_time,
                    'export_formats': len(export_results) - 1  # -1 pour exclure 'main_output'
                },
                intermediate_files=processing_results.intermediate_files + documentation_paths
            )
            
            self.logger.info(f"Final integration completed in {integration_time:.2f}s")
            return updated_results
            
        except Exception as e:
            self.logger.error(f"Final integration failed: {e}")
            raise ProcessingError(f"Final integration failed: {e}")
    
    def _validate_inputs(self, video_path: str, results: ProcessingResults) -> None:
        """Valide les entrées pour l'intégration finale."""
        # Vérifier que la vidéo originale existe
        if not os.path.exists(video_path):
            raise ValidationError(f"Original video not found: {video_path}")
        
        # Vérifier que le traitement a réussi
        if not results.success:
            raise ValidationError("Cannot integrate failed processing results")
        
        # Vérifier qu'il y a des résultats à intégrer
        if not results.transcription_result and not results.ocr_results:
            raise ValidationError("No transcription or OCR results to integrate")
        
        self.logger.info("Input validation passed")
    
    def _prepare_output_paths(self, original_video_path: str) -> Dict[str, str]:
        """Prépare les chemins de sortie pour différents formats."""
        base_path = Path(original_video_path).stem
        
        paths = {
            'main_output': self.output_manager.prepare_output_path(
                original_video_path, "_dubbed", ".mp4"
            ),
            'high_quality': self.output_manager.prepare_output_path(
                original_video_path, "_dubbed_hq", ".mp4"
            ),
            'compressed': self.output_manager.prepare_output_path(
                original_video_path, "_dubbed_compressed", ".mp4"
            ),
            'audio_only': self.output_manager.prepare_output_path(
                original_video_path, "_dubbed_audio", ".wav"
            )
        }
        
        return paths
    
    def _optimize_final_audio(self, results: ProcessingResults, settings: Dict) -> str:
        """Optimise l'audio final pour l'export."""
        try:
            # Récupérer le chemin audio depuis les résultats
            audio_path = None
            
            # Chercher dans les fichiers intermédiaires
            for file_path in results.intermediate_files:
                if 'final_audio' in file_path or 'mixed_audio' in file_path:
                    if os.path.exists(file_path):
                        audio_path = file_path
                        break
            
            if not audio_path:
                raise ProcessingError("Final audio file not found in results")
            
            # Optimiser l'audio avec FFmpeg
            optimized_path = str(Path(audio_path).parent / "optimized_final_audio.wav")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ar', str(settings['audio_sample_rate']),
                '-ac', str(settings['audio_channels']),
                '-c:a', 'pcm_s16le',  # Format non compressé pour qualité
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Normalisation loudness
                optimized_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ProcessingError(f"Audio optimization failed: {result.stderr}")
            
            self.logger.info(f"Audio optimized: {optimized_path}")
            return optimized_path
            
        except Exception as e:
            self.logger.warning(f"Audio optimization failed, using original: {e}")
            return audio_path  # Retourner l'audio original si l'optimisation échoue
    
    def _synchronize_audio_video(self, video_path: str, audio_path: str) -> str:
        """Synchronise précisément l'audio avec la vidéo."""
        try:
            # Obtenir la durée de la vidéo originale
            video_duration = self._get_video_duration(video_path)
            audio_duration = self._get_audio_duration(audio_path)
            
            # Si les durées sont très différentes, ajuster l'audio
            duration_diff = abs(video_duration - audio_duration)
            
            if duration_diff > 0.1:  # Plus de 100ms de différence
                self.logger.info(f"Synchronizing audio: video={video_duration:.2f}s, audio={audio_duration:.2f}s")
                
                synchronized_path = str(Path(audio_path).parent / "synchronized_audio.wav")
                
                if audio_duration > video_duration:
                    # Couper l'audio
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', audio_path,
                        '-t', str(video_duration),
                        '-c:a', 'pcm_s16le',
                        synchronized_path
                    ]
                else:
                    # Étendre l'audio avec du silence
                    silence_duration = video_duration - audio_duration
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', audio_path,
                        '-af', f'apad=pad_dur={silence_duration}',
                        '-c:a', 'pcm_s16le',
                        synchronized_path
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ProcessingError(f"Audio synchronization failed: {result.stderr}")
                
                return synchronized_path
            
            return audio_path  # Pas besoin de synchronisation
            
        except Exception as e:
            self.logger.warning(f"Audio synchronization failed: {e}")
            return audio_path
    
    def _export_multiple_formats(self, 
                                video_path: str, 
                                audio_path: str, 
                                output_paths: Dict[str, str],
                                settings: Dict[str, Any]) -> Dict[str, str]:
        """Exporte la vidéo en plusieurs formats et qualités."""
        export_results = {}
        
        # Format principal (qualité équilibrée)
        main_output = self._export_video(
            video_path, audio_path, output_paths['main_output'],
            {
                'video_codec': settings['video_codec'],
                'audio_codec': settings['audio_codec'],
                'video_bitrate': settings['video_bitrate'],
                'audio_bitrate': settings['audio_bitrate'],
                'preset': settings['preset'],
                'crf': settings['crf']
            }
        )
        export_results['main_output'] = main_output
        
        # Format haute qualité
        try:
            hq_output = self._export_video(
                video_path, audio_path, output_paths['high_quality'],
                {
                    'video_codec': settings['video_codec'],
                    'audio_codec': settings['audio_codec'],
                    'video_bitrate': '10M',  # Bitrate plus élevé
                    'audio_bitrate': '320k',
                    'preset': 'slow',  # Preset plus lent pour meilleure qualité
                    'crf': 18  # CRF plus bas pour meilleure qualité
                }
            )
            export_results['high_quality'] = hq_output
        except Exception as e:
            self.logger.warning(f"High quality export failed: {e}")
        
        # Format compressé
        try:
            compressed_output = self._export_video(
                video_path, audio_path, output_paths['compressed'],
                {
                    'video_codec': settings['video_codec'],
                    'audio_codec': settings['audio_codec'],
                    'video_bitrate': '2M',  # Bitrate plus bas
                    'audio_bitrate': '128k',
                    'preset': 'fast',  # Preset plus rapide
                    'crf': 28  # CRF plus élevé pour plus de compression
                }
            )
            export_results['compressed'] = compressed_output
        except Exception as e:
            self.logger.warning(f"Compressed export failed: {e}")
        
        # Audio seul
        try:
            audio_output = self._export_audio_only(audio_path, output_paths['audio_only'])
            export_results['audio_only'] = audio_output
        except Exception as e:
            self.logger.warning(f"Audio-only export failed: {e}")
        
        return export_results
    
    def _export_video(self, 
                     video_path: str, 
                     audio_path: str, 
                     output_path: str,
                     export_settings: Dict[str, Any]) -> str:
        """Exporte une vidéo avec les paramètres spécifiés."""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', export_settings['video_codec'],
                '-c:a', export_settings['audio_codec'],
                '-b:v', export_settings['video_bitrate'],
                '-b:a', export_settings['audio_bitrate'],
                '-preset', export_settings['preset'],
                '-crf', str(export_settings['crf']),
                '-map', '0:v:0',  # Vidéo du premier input
                '-map', '1:a:0',  # Audio du deuxième input
                '-shortest',  # Arrêter quand le plus court se termine
                output_path
            ]
            
            self.logger.info(f"Exporting video: {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ProcessingError(f"Video export failed: {result.stderr}")
            
            # Vérifier que le fichier a été créé
            if not os.path.exists(output_path):
                raise ProcessingError("Output video file was not created")
            
            self.logger.info(f"Video exported successfully: {output_path}")
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Video export failed: {e}")
    
    def _export_audio_only(self, audio_path: str, output_path: str) -> str:
        """Exporte l'audio seul en haute qualité."""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-c:a', 'pcm_s24le',  # Audio 24-bit pour haute qualité
                '-ar', '48000',  # 48kHz
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ProcessingError(f"Audio export failed: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Audio export failed: {e}")
    
    def _validate_audio_video_sync(self, video_path: str) -> Dict[str, float]:
        """Valide la synchronisation audio/vidéo du résultat final."""
        try:
            # Obtenir les informations du fichier
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ProcessingError("Failed to analyze output video")
            
            info = json.loads(result.stdout)
            
            video_duration = None
            audio_duration = None
            
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_duration = float(stream.get('duration', 0))
                elif stream['codec_type'] == 'audio':
                    audio_duration = float(stream.get('duration', 0))
            
            sync_metrics = {
                'video_duration': video_duration or 0.0,
                'audio_duration': audio_duration or 0.0,
                'sync_difference': abs((video_duration or 0) - (audio_duration or 0)),
                'sync_quality': 1.0  # Par défaut
            }
            
            # Calculer la qualité de synchronisation
            if sync_metrics['sync_difference'] < 0.1:
                sync_metrics['sync_quality'] = 1.0  # Parfait
            elif sync_metrics['sync_difference'] < 0.5:
                sync_metrics['sync_quality'] = 0.9  # Très bon
            elif sync_metrics['sync_difference'] < 1.0:
                sync_metrics['sync_quality'] = 0.8  # Bon
            else:
                sync_metrics['sync_quality'] = 0.7  # Acceptable
            
            self.logger.info(f"Sync validation: {sync_metrics}")
            return sync_metrics
            
        except Exception as e:
            self.logger.warning(f"Sync validation failed: {e}")
            return {'sync_quality': 0.5, 'sync_difference': -1.0}
    
    def _create_documentation(self, 
                            results: ProcessingResults,
                            export_results: Dict[str, str],
                            sync_validation: Dict[str, float]) -> List[str]:
        """Crée la documentation et les métadonnées."""
        documentation_paths = []
        
        try:
            # Sauvegarder les résultats détaillés
            results_path = self.output_manager.save_processing_results(results)
            if results_path:
                documentation_paths.append(results_path)
            
            # Créer un résumé textuel
            summary_path = self.output_manager.create_output_summary(results)
            if summary_path:
                documentation_paths.append(summary_path)
            
            # Créer un fichier de métadonnées pour les exports
            metadata_path = self._create_export_metadata(export_results, sync_validation)
            if metadata_path:
                documentation_paths.append(metadata_path)
            
            # Créer un guide d'utilisation
            guide_path = self._create_usage_guide(export_results)
            if guide_path:
                documentation_paths.append(guide_path)
            
        except Exception as e:
            self.logger.warning(f"Documentation creation failed: {e}")
        
        return documentation_paths
    
    def _create_export_metadata(self, 
                              export_results: Dict[str, str],
                              sync_validation: Dict[str, float]) -> str:
        """Crée un fichier de métadonnées pour les exports."""
        try:
            metadata = {
                'export_timestamp': time.time(),
                'export_formats': {},
                'sync_validation': sync_validation,
                'version': '1.0.0'
            }
            
            # Analyser chaque format exporté
            for format_name, file_path in export_results.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    metadata['export_formats'][format_name] = {
                        'path': file_path,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'exists': True
                    }
            
            # Sauvegarder les métadonnées
            main_output = export_results.get('main_output', '')
            if main_output:
                metadata_path = str(Path(main_output).parent / "export_metadata.json")
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                return metadata_path
            
        except Exception as e:
            self.logger.warning(f"Export metadata creation failed: {e}")
        
        return ""
    
    def _create_usage_guide(self, export_results: Dict[str, str]) -> str:
        """Crée un guide d'utilisation des fichiers exportés."""
        try:
            main_output = export_results.get('main_output', '')
            if not main_output:
                return ""
            
            guide_path = str(Path(main_output).parent / "GUIDE_UTILISATION.txt")
            
            guide_content = [
                "=== GUIDE D'UTILISATION - DOUBLAGE VIDÉO IA ===",
                "",
                "Ce dossier contient les résultats du doublage automatique de votre vidéo.",
                "",
                "FICHIERS PRINCIPAUX:",
            ]
            
            for format_name, file_path in export_results.items():
                if os.path.exists(file_path):
                    filename = Path(file_path).name
                    
                    if format_name == 'main_output':
                        guide_content.append(f"• {filename} - Vidéo principale (qualité équilibrée)")
                    elif format_name == 'high_quality':
                        guide_content.append(f"• {filename} - Vidéo haute qualité (fichier plus volumineux)")
                    elif format_name == 'compressed':
                        guide_content.append(f"• {filename} - Vidéo compressée (fichier plus petit)")
                    elif format_name == 'audio_only':
                        guide_content.append(f"• {filename} - Audio seul (haute qualité)")
            
            guide_content.extend([
                "",
                "RECOMMANDATIONS D'USAGE:",
                "• Utilisez la vidéo principale pour un usage général",
                "• Utilisez la haute qualité pour l'archivage ou la diffusion professionnelle",
                "• Utilisez la version compressée pour le partage en ligne",
                "• L'audio seul peut être utilisé pour des podcasts ou autres usages audio",
                "",
                "QUALITÉ DU DOUBLAGE:",
                f"• Locuteurs détectés: {export_results.get('speakers_detected', 'N/A')}",
                f"• Segments de dialogue: {export_results.get('dialogue_segments', 'N/A')}",
                "",
                "Pour toute question, consultez la documentation complète.",
                "",
                "=== FIN DU GUIDE ==="
            ])
            
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(guide_content))
            
            return guide_path
            
        except Exception as e:
            self.logger.warning(f"Usage guide creation failed: {e}")
            return ""
    
    def _cleanup_temporary_files(self, results: ProcessingResults) -> None:
        """Nettoie les fichiers temporaires non nécessaires."""
        try:
            # Garder seulement les fichiers importants
            important_keywords = [
                'final_audio', 'mixed_audio', 'transcription', 
                'synchronized', 'optimized'
            ]
            
            files_to_remove = []
            
            for file_path in results.intermediate_files:
                # Vérifier si le fichier est important
                is_important = any(keyword in file_path.lower() 
                                 for keyword in important_keywords)
                
                if not is_important and os.path.exists(file_path):
                    files_to_remove.append(file_path)
            
            # Supprimer les fichiers non importants
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    self.logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")
            
            if files_to_remove:
                self.logger.info(f"Cleaned up {len(files_to_remove)} temporary files")
            
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    def _get_video_duration(self, video_path: str) -> float:
        """Obtient la durée d'une vidéo."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_entries', 'format=duration',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return float(info['format']['duration'])
            
        except Exception:
            pass
        
        return 0.0
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Obtient la durée d'un fichier audio."""
        return self._get_video_duration(audio_path)  # FFprobe fonctionne aussi pour l'audio