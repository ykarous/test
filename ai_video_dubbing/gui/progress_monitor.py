#!/usr/bin/env python3
"""
Système de monitoring de progression avancé pour l'application de doublage vidéo.
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from ..models.data_models import ProgressInfo, PipelineStage


class NotificationType(Enum):
    """Types de notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """Représente une notification."""
    type: NotificationType
    title: str
    message: str
    timestamp: float = field(default_factory=time.time)
    duration: Optional[float] = None  # Durée d'affichage en secondes
    action_callback: Optional[Callable] = None
    action_text: Optional[str] = None


@dataclass
class StageProgress:
    """Progression détaillée d'une étape."""
    stage: PipelineStage
    name: str
    description: str
    progress: float = 0.0
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    substeps: List[str] = field(default_factory=list)
    current_substep: Optional[str] = None
    estimated_duration: Optional[float] = None


class ProgressMonitor:
    """
    Moniteur de progression avancé avec notifications et statistiques détaillées.
    """
    
    def __init__(self):
        """Initialise le moniteur de progression."""
        self.stages: Dict[PipelineStage, StageProgress] = {}
        self.notifications: List[Notification] = []
        self.callbacks: List[Callable[[ProgressInfo], None]] = []
        self.notification_callbacks: List[Callable[[Notification], None]] = []
        
        # État global
        self.overall_progress: float = 0.0
        self.current_stage: Optional[PipelineStage] = None
        self.start_time: Optional[float] = None
        self.estimated_total_duration: Optional[float] = None
        
        # Statistiques
        self.processing_stats: Dict[str, Any] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialiser les étapes
        self._initialize_stages()
    
    def _initialize_stages(self):
        """Initialise les étapes du pipeline avec leurs descriptions."""
        stage_definitions = {
            PipelineStage.INITIALIZATION: StageProgress(
                stage=PipelineStage.INITIALIZATION,
                name="Initialisation",
                description="Préparation du pipeline et validation des entrées",
                substeps=[
                    "Validation du fichier vidéo",
                    "Création des répertoires temporaires",
                    "Chargement de la configuration",
                    "Vérification des dépendances"
                ],
                estimated_duration=5.0
            ),
            PipelineStage.VIDEO_PROCESSING: StageProgress(
                stage=PipelineStage.VIDEO_PROCESSING,
                name="Traitement Vidéo",
                description="Extraction audio et préparation des données vidéo",
                substeps=[
                    "Analyse des propriétés vidéo",
                    "Extraction de la piste audio",
                    "Extraction des images clés",
                    "Préparation des métadonnées"
                ],
                estimated_duration=30.0
            ),
            PipelineStage.AUDIO_ANALYSIS: StageProgress(
                stage=PipelineStage.AUDIO_ANALYSIS,
                name="Traitement Audio",
                description="Analyse et préparation de l'audio pour la transcription",
                substeps=[
                    "Normalisation audio",
                    "Détection d'activité vocale",
                    "Diarisation des locuteurs",
                    "Séparation de source (optionnel)"
                ],
                estimated_duration=60.0
            ),
            PipelineStage.TRANSCRIPTION: StageProgress(
                stage=PipelineStage.TRANSCRIPTION,
                name="Transcription",
                description="Conversion de l'audio en texte avec horodatages",
                substeps=[
                    "Chargement du modèle ASR",
                    "Transcription des segments audio",
                    "Génération des horodatages",
                    "Post-traitement du texte"
                ],
                estimated_duration=120.0
            ),
            PipelineStage.OCR_EXTRACTION: StageProgress(
                stage=PipelineStage.OCR_EXTRACTION,
                name="Extraction OCR",
                description="Extraction des sous-titres depuis les images",
                substeps=[
                    "Chargement du modèle OCR",
                    "Détection des zones de texte",
                    "Reconnaissance des caractères",
                    "Synchronisation avec l'audio"
                ],
                estimated_duration=90.0
            ),
            PipelineStage.SYNCHRONIZATION: StageProgress(
                stage=PipelineStage.SYNCHRONIZATION,
                name="Synchronisation",
                description="Alignement des transcriptions et sous-titres",
                substeps=[
                    "Comparaison ASR/OCR",
                    "Correction des erreurs",
                    "Attribution aux locuteurs",
                    "Validation de la synchronisation"
                ],
                estimated_duration=45.0
            ),
            PipelineStage.VOICE_CLONING: StageProgress(
                stage=PipelineStage.VOICE_CLONING,
                name="Clonage de Voix",
                description="Génération des nouvelles voix doublées",
                substeps=[
                    "Chargement du modèle de clonage",
                    "Analyse des échantillons vocaux",
                    "Synthèse des nouvelles voix",
                    "Optimisation de la qualité"
                ],
                estimated_duration=180.0
            ),
            PipelineStage.AUDIO_MIXING: StageProgress(
                stage=PipelineStage.AUDIO_MIXING,
                name="Mixage Audio",
                description="Combinaison des voix avec la bande sonore",
                substeps=[
                    "Synchronisation des nouvelles voix",
                    "Mixage avec la musique de fond",
                    "Ajustement des niveaux",
                    "Finalisation de l'audio"
                ],
                estimated_duration=60.0
            ),
            PipelineStage.VIDEO_ASSEMBLY: StageProgress(
                stage=PipelineStage.VIDEO_ASSEMBLY,
                name="Export Final",
                description="Génération de la vidéo finale doublée",
                substeps=[
                    "Combinaison audio/vidéo",
                    "Encodage final",
                    "Validation de la sortie",
                    "Nettoyage des fichiers temporaires"
                ],
                estimated_duration=45.0
            )
        }
        
        with self._lock:
            self.stages = stage_definitions
            # Calculer la durée totale estimée
            self.estimated_total_duration = sum(
                stage.estimated_duration for stage in self.stages.values()
            )
    
    def register_progress_callback(self, callback: Callable[[ProgressInfo], None]):
        """Enregistre un callback pour les mises à jour de progression."""
        with self._lock:
            self.callbacks.append(callback)
    
    def register_notification_callback(self, callback: Callable[[Notification], None]):
        """Enregistre un callback pour les notifications."""
        with self._lock:
            self.notification_callbacks.append(callback)
    
    def start_monitoring(self):
        """Démarre le monitoring du pipeline."""
        with self._lock:
            self.start_time = time.time()
            self.overall_progress = 0.0
            self.current_stage = None
            self.processing_stats.clear()
            
            # Réinitialiser toutes les étapes
            for stage in self.stages.values():
                stage.progress = 0.0
                stage.status = "pending"
                stage.start_time = None
                stage.end_time = None
                stage.current_substep = None
        
        self._send_notification(
            NotificationType.INFO,
            "Traitement Démarré",
            "Le pipeline de doublage vidéo a été initialisé avec succès."
        )
    
    def update_stage_progress(self, stage: PipelineStage, progress: float, 
                            substep: Optional[str] = None, message: Optional[str] = None):
        """Met à jour la progression d'une étape."""
        with self._lock:
            if stage not in self.stages:
                return
            
            stage_info = self.stages[stage]
            
            # Démarrer l'étape si nécessaire
            if stage_info.status == "pending":
                stage_info.status = "running"
                stage_info.start_time = time.time()
                self.current_stage = stage
            
            # Mettre à jour la progression
            stage_info.progress = min(100.0, max(0.0, progress))
            if substep:
                stage_info.current_substep = substep
            
            # Marquer comme terminée si 100%
            if stage_info.progress >= 100.0 and stage_info.status == "running":
                stage_info.status = "completed"
                stage_info.end_time = time.time()
            
            # Calculer la progression globale
            self._calculate_overall_progress()
            
            # Envoyer les callbacks
            progress_info = ProgressInfo(
                stage=stage,
                progress=stage_info.progress,
                message=message or f"{stage_info.name}: {substep or 'En cours...'}"
            )
            
            for callback in self.callbacks:
                try:
                    callback(progress_info)
                except Exception as e:
                    print(f"Erreur callback progression: {e}")
    
    def mark_stage_failed(self, stage: PipelineStage, error_message: str):
        """Marque une étape comme échouée."""
        with self._lock:
            if stage in self.stages:
                stage_info = self.stages[stage]
                stage_info.status = "failed"
                stage_info.end_time = time.time()
        
        self._send_notification(
            NotificationType.ERROR,
            f"Erreur - {self.stages[stage].name}",
            error_message
        )
    
    def _calculate_overall_progress(self):
        """Calcule la progression globale basée sur les étapes."""
        total_weight = len(self.stages)
        if total_weight == 0:
            self.overall_progress = 0.0
            return
        
        completed_weight = 0.0
        for stage_info in self.stages.values():
            if stage_info.status == "completed":
                completed_weight += 1.0
            elif stage_info.status == "running":
                completed_weight += stage_info.progress / 100.0
        
        self.overall_progress = (completed_weight / total_weight) * 100.0
    
    def get_detailed_progress(self) -> Dict[str, Any]:
        """Retourne les informations détaillées de progression."""
        with self._lock:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            
            # Estimer le temps restant
            estimated_remaining = None
            if self.overall_progress > 0 and self.estimated_total_duration:
                progress_ratio = self.overall_progress / 100.0
                estimated_total = elapsed_time / progress_ratio
                estimated_remaining = max(0, estimated_total - elapsed_time)
            
            return {
                "overall_progress": self.overall_progress,
                "current_stage": self.current_stage,
                "elapsed_time": elapsed_time,
                "estimated_remaining": estimated_remaining,
                "stages": {
                    stage.value: {
                        "name": info.name,
                        "description": info.description,
                        "progress": info.progress,
                        "status": info.status,
                        "current_substep": info.current_substep,
                        "substeps": info.substeps,
                        "duration": (info.end_time - info.start_time) if info.start_time and info.end_time else None
                    }
                    for stage, info in self.stages.items()
                },
                "stats": self.processing_stats.copy()
            }
    
    def _send_notification(self, notification_type: NotificationType, title: str, 
                          message: str, duration: Optional[float] = None,
                          action_callback: Optional[Callable] = None,
                          action_text: Optional[str] = None):
        """Envoie une notification."""
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            duration=duration,
            action_callback=action_callback,
            action_text=action_text
        )
        
        with self._lock:
            self.notifications.append(notification)
            
            # Limiter le nombre de notifications stockées
            if len(self.notifications) > 100:
                self.notifications = self.notifications[-50:]
        
        # Envoyer aux callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                print(f"Erreur callback notification: {e}")
    
    def send_completion_notification(self, output_path: str, processing_time: float):
        """Envoie une notification de fin de traitement."""
        def open_output():
            import os
            import sys
            try:
                if sys.platform == "win32":
                    os.startfile(output_path)
                elif sys.platform == "darwin":
                    os.system(f"open '{output_path}'")
                else:
                    os.system(f"xdg-open '{output_path}'")
            except Exception as e:
                print(f"Erreur ouverture fichier: {e}")
        
        minutes, seconds = divmod(int(processing_time), 60)
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        self._send_notification(
            NotificationType.SUCCESS,
            "Traitement Terminé !",
            f"Le doublage vidéo est terminé en {time_str}.\n\nFichier de sortie:\n{output_path}",
            duration=10.0,
            action_callback=open_output,
            action_text="Ouvrir le fichier"
        )
    
    def send_error_notification(self, error_message: str, suggestion: Optional[str] = None):
        """Envoie une notification d'erreur avec suggestion."""
        full_message = error_message
        if suggestion:
            full_message += f"\n\nSuggestion: {suggestion}"
        
        self._send_notification(
            NotificationType.ERROR,
            "Erreur de Traitement",
            full_message,
            duration=15.0
        )
    
    def send_warning_notification(self, title: str, message: str):
        """Envoie une notification d'avertissement."""
        self._send_notification(
            NotificationType.WARNING,
            title,
            message,
            duration=8.0
        )
    
    def get_recent_notifications(self, limit: int = 10) -> List[Notification]:
        """Retourne les notifications récentes."""
        with self._lock:
            return self.notifications[-limit:] if self.notifications else []
    
    def clear_notifications(self):
        """Efface toutes les notifications."""
        with self._lock:
            self.notifications.clear()
    
    def add_processing_stat(self, key: str, value: Any):
        """Ajoute une statistique de traitement."""
        with self._lock:
            self.processing_stats[key] = value
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des performances."""
        with self._lock:
            if not self.start_time:
                return {}
            
            total_time = time.time() - self.start_time
            completed_stages = sum(1 for stage in self.stages.values() if stage.status == "completed")
            
            return {
                "total_processing_time": total_time,
                "completed_stages": completed_stages,
                "total_stages": len(self.stages),
                "average_stage_time": total_time / max(1, completed_stages),
                "overall_progress": self.overall_progress,
                "stats": self.processing_stats.copy()
            }


# Instance globale du moniteur
global_progress_monitor = ProgressMonitor()


def get_progress_monitor() -> ProgressMonitor:
    """Retourne l'instance globale du moniteur de progression."""
    return global_progress_monitor