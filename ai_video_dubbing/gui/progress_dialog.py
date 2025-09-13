"""
Dialogue de progression pour l'application de doublage vidéo par IA.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import time

from ..models.data_models import ProgressInfo, PipelineStage


class ProgressDialog:
    """Dialogue de progression avec détails des étapes."""
    
    def __init__(self, parent: tk.Tk, on_cancel: Optional[Callable[[], None]] = None):
        """
        Initialise le dialogue de progression.
        
        Args:
            parent: Fenêtre parente
            on_cancel: Callback appelé lors de l'annulation
        """
        self.parent = parent
        self.on_cancel = on_cancel
        
        # Créer la fenêtre
        self.window = tk.Toplevel(parent)
        self.window.title("Progression - AI Video Dubbing")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Variables
        self.start_time = time.time()
        self.current_stage = None
        self.stage_start_time = time.time()
        
        # Créer l'interface
        self._create_widgets()
        self._setup_layout()
        
        # Centrer la fenêtre
        self._center_window()
        
        # Gérer la fermeture
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """Crée tous les widgets du dialogue."""
        # Frame principal
        self.main_frame = ttk.Frame(self.window, padding="20")
        
        # Titre
        self.title_label = ttk.Label(
            self.main_frame,
            text="🎬 Traitement en cours...",
            font=("Arial", 16, "bold")
        )
        
        # Informations générales
        self.info_frame = ttk.LabelFrame(
            self.main_frame,
            text="Informations générales",
            padding="15"
        )
        
        # Étape actuelle
        self.stage_label = ttk.Label(
            self.info_frame,
            text="Étape: Initialisation",
            font=("Arial", 11, "bold")
        )
        
        # Message de progression
        self.message_label = ttk.Label(
            self.info_frame,
            text="Préparation du traitement...",
            font=("Arial", 10)
        )
        
        # Barre de progression principale
        self.progress_frame = ttk.LabelFrame(
            self.main_frame,
            text="Progression globale",
            padding="15"
        )
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            length=400
        )
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="0%",
            font=("Arial", 10, "bold")
        )
        
        # Temps et estimations
        self.time_frame = ttk.LabelFrame(
            self.main_frame,
            text="Temps",
            padding="15"
        )
        
        self.elapsed_label = ttk.Label(
            self.time_frame,
            text="Temps écoulé: 00:00:00"
        )
        
        self.estimated_label = ttk.Label(
            self.time_frame,
            text="Temps estimé restant: --:--:--"
        )
        
        # Détails des étapes
        self.details_frame = ttk.LabelFrame(
            self.main_frame,
            text="Détails des étapes",
            padding="15"
        )
        
        # Liste des étapes avec leur statut
        self.stages_tree = ttk.Treeview(
            self.details_frame,
            columns=("status", "time"),
            show="tree headings",
            height=8
        )
        
        self.stages_tree.heading("#0", text="Étape")
        self.stages_tree.heading("status", text="Statut")
        self.stages_tree.heading("time", text="Temps")
        
        self.stages_tree.column("#0", width=250)
        self.stages_tree.column("status", width=100)
        self.stages_tree.column("time", width=80)
        
        # Scrollbar pour la liste
        self.stages_scrollbar = ttk.Scrollbar(
            self.details_frame,
            orient="vertical",
            command=self.stages_tree.yview
        )
        self.stages_tree.configure(yscrollcommand=self.stages_scrollbar.set)
        
        # Boutons
        self.buttons_frame = ttk.Frame(self.main_frame)
        
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text="Annuler",
            command=self._on_cancel_clicked
        )
        
        self.minimize_button = ttk.Button(
            self.buttons_frame,
            text="Réduire",
            command=self._minimize_window
        )
        
        # Initialiser la liste des étapes
        self._initialize_stages()
    
    def _setup_layout(self):
        """Configure la disposition des widgets."""
        self.main_frame.pack(fill="both", expand=True)
        
        self.title_label.pack(pady=(0, 15))
        
        # Informations générales
        self.info_frame.pack(fill="x", pady=(0, 10))
        self.stage_label.pack(anchor="w")
        self.message_label.pack(anchor="w", pady=(5, 0))
        
        # Progression
        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_label.pack()
        
        # Temps
        self.time_frame.pack(fill="x", pady=(0, 10))
        self.elapsed_label.pack(anchor="w")
        self.estimated_label.pack(anchor="w", pady=(2, 0))
        
        # Détails
        self.details_frame.pack(fill="both", expand=True, pady=(0, 15))
        self.stages_tree.pack(side="left", fill="both", expand=True)
        self.stages_scrollbar.pack(side="right", fill="y")
        
        # Boutons
        self.buttons_frame.pack(fill="x")
        self.cancel_button.pack(side="right")
        self.minimize_button.pack(side="right", padx=(0, 10))
    
    def _center_window(self):
        """Centre la fenêtre sur le parent."""
        self.window.update_idletasks()
        
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _initialize_stages(self):
        """Initialise la liste des étapes."""
        stages_info = [
            ("Initialisation", "initialization"),
            ("Traitement vidéo", "video_processing"),
            ("Analyse audio", "audio_analysis"),
            ("Séparation de source", "source_separation"),
            ("Transcription", "transcription"),
            ("Extraction OCR", "ocr_extraction"),
            ("Synchronisation", "synchronization"),
            ("Segmentation locuteurs", "speaker_segmentation"),
            ("Normalisation audio", "audio_normalization"),
            ("Clonage de voix", "voice_cloning"),
            ("Mixage audio", "audio_mixing"),
            ("Assemblage vidéo", "video_assembly"),
            ("Finalisation", "completed")
        ]
        
        for display_name, stage_id in stages_info:
            self.stages_tree.insert(
                "",
                "end",
                iid=stage_id,
                text=display_name,
                values=("En attente", "--:--")
            )
    
    def update_progress(self, progress_info: ProgressInfo):
        """
        Met à jour la progression.
        
        Args:
            progress_info: Informations de progression
        """
        # Mettre à jour l'étape actuelle
        if self.current_stage != progress_info.stage:
            # Marquer l'étape précédente comme terminée
            if self.current_stage:
                stage_time = time.time() - self.stage_start_time
                self._update_stage_status(
                    self.current_stage.value,
                    "✅ Terminé",
                    self._format_time(stage_time)
                )
            
            # Commencer la nouvelle étape
            self.current_stage = progress_info.stage
            self.stage_start_time = time.time()
            self._update_stage_status(
                progress_info.stage.value,
                "🔄 En cours",
                "--:--"
            )
        
        # Mettre à jour les informations générales
        stage_display = self._get_stage_display_name(progress_info.stage)
        self.stage_label.config(text=f"Étape: {stage_display}")
        self.message_label.config(text=progress_info.message)
        
        # Mettre à jour la barre de progression
        self.progress_bar["value"] = progress_info.progress
        self.progress_label.config(text=f"{progress_info.progress:.1f}%")
        
        # Mettre à jour les temps
        self._update_time_info(progress_info.progress)
        
        # Faire défiler vers l'étape actuelle
        self.stages_tree.see(progress_info.stage.value)
        self.stages_tree.selection_set(progress_info.stage.value)
    
    def _update_stage_status(self, stage_id: str, status: str, time_str: str):
        """Met à jour le statut d'une étape."""
        try:
            self.stages_tree.set(stage_id, "status", status)
            self.stages_tree.set(stage_id, "time", time_str)
        except tk.TclError:
            # L'étape n'existe pas dans l'arbre
            pass
    
    def _get_stage_display_name(self, stage: PipelineStage) -> str:
        """Retourne le nom d'affichage d'une étape."""
        stage_names = {
            PipelineStage.INITIALIZATION: "Initialisation",
            PipelineStage.VIDEO_PROCESSING: "Traitement vidéo",
            PipelineStage.AUDIO_ANALYSIS: "Analyse audio",
            PipelineStage.SOURCE_SEPARATION: "Séparation de source",
            PipelineStage.TRANSCRIPTION: "Transcription",
            PipelineStage.OCR_EXTRACTION: "Extraction OCR",
            PipelineStage.SYNCHRONIZATION: "Synchronisation",
            PipelineStage.SPEAKER_SEGMENTATION: "Segmentation locuteurs",
            PipelineStage.AUDIO_NORMALIZATION: "Normalisation audio",
            PipelineStage.VOICE_CLONING: "Clonage de voix",
            PipelineStage.AUDIO_MIXING: "Mixage audio",
            PipelineStage.VIDEO_ASSEMBLY: "Assemblage vidéo",
            PipelineStage.COMPLETED: "Terminé"
        }
        return stage_names.get(stage, stage.value)
    
    def _update_time_info(self, progress: float):
        """Met à jour les informations de temps."""
        elapsed = time.time() - self.start_time
        self.elapsed_label.config(text=f"Temps écoulé: {self._format_time(elapsed)}")
        
        # Estimation du temps restant
        if progress > 0:
            total_estimated = elapsed / (progress / 100)
            remaining = total_estimated - elapsed
            if remaining > 0:
                self.estimated_label.config(
                    text=f"Temps estimé restant: {self._format_time(remaining)}"
                )
            else:
                self.estimated_label.config(text="Temps estimé restant: Bientôt terminé")
        else:
            self.estimated_label.config(text="Temps estimé restant: Calcul en cours...")
    
    def _format_time(self, seconds: float) -> str:
        """Formate un temps en secondes en HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _on_cancel_clicked(self):
        """Appelé quand le bouton Annuler est cliqué."""
        if self.on_cancel:
            self.on_cancel()
    
    def _minimize_window(self):
        """Réduit la fenêtre."""
        self.window.iconify()
    
    def _on_closing(self):
        """Appelé lors de la fermeture de la fenêtre."""
        # Empêcher la fermeture directe, forcer l'utilisation du bouton Annuler
        pass
    
    def close(self):
        """Ferme le dialogue de progression."""
        try:
            self.window.destroy()
        except tk.TclError:
            # La fenêtre est déjà fermée
            pass