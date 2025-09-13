"""
Fenêtre principale de l'application de doublage vidéo par IA.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional, Callable

from ..models.data_models import PipelineConfig, ProgressInfo
from ..processors.pipeline_orchestrator import PipelineOrchestrator, PipelineState
from .config_panel import ConfigPanel
from .progress_dialog import ProgressDialog
from .results_window import ResultsWindow
from .progress_monitor import get_progress_monitor, ProgressMonitor
from .notification_widget import NotificationManager, ProgressBar, DetailedProgressWindow
from .error_dialog import show_error_dialog, show_error_summary
from ..utils.error_handler import get_error_handler, ErrorHandler
from .error_dialog import show_error_dialog, show_error_summary
from ..utils.error_handler import get_error_handler, ErrorHandler


class MainWindow:
    """Fenêtre principale de l'application."""
    
    def __init__(self):
        """Initialise la fenêtre principale."""
        self.root = tk.Tk()
        self.root.title("AI Video Dubbing - Doublage Vidéo par IA")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Variables
        self.selected_video_path = tk.StringVar()
        self.pipeline_orchestrator: Optional[PipelineOrchestrator] = None
        
        # Système de monitoring et notifications
        self.progress_monitor = get_progress_monitor()
        self.notification_manager = NotificationManager(self.root)
        self.detailed_progress_window: Optional[DetailedProgressWindow] = None
        
        # Système de gestion d'erreurs
        self.error_handler = get_error_handler()
        
        # Enregistrer les callbacks
        self.progress_monitor.register_progress_callback(self._on_progress_update)
        self.progress_monitor.register_notification_callback(self._on_notification)
        self.error_handler.register_error_callback(self._on_error_occurred)
        self.config_panel: Optional[ConfigPanel] = None
        self.progress_dialog: Optional[ProgressDialog] = None
        self.results_window: Optional[ResultsWindow] = None
        
        # Configuration par défaut
        self.current_config = PipelineConfig()
        
        # Créer l'interface
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        # Centrer la fenêtre
        self._center_window()
    
    def _create_widgets(self):
        """Crée tous les widgets de l'interface."""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="20")
        
        # Titre
        self.title_label = ttk.Label(
            self.main_frame,
            text="🎬 AI Video Dubbing",
            font=("Arial", 24, "bold")
        )
        
        self.subtitle_label = ttk.Label(
            self.main_frame,
            text="Doublage vidéo automatique par intelligence artificielle",
            font=("Arial", 12)
        )
        
        # Section sélection de fichier
        self.file_frame = ttk.LabelFrame(
            self.main_frame,
            text="📁 Sélection du fichier vidéo",
            padding="15"
        )
        
        self.file_path_entry = ttk.Entry(
            self.file_frame,
            textvariable=self.selected_video_path,
            font=("Arial", 10),
            state="readonly",
            width=50
        )
        
        self.browse_button = ttk.Button(
            self.file_frame,
            text="Parcourir...",
            command=self._browse_video_file
        )
        
        # Section configuration
        self.config_frame = ttk.LabelFrame(
            self.main_frame,
            text="⚙️ Configuration",
            padding="15"
        )
        
        self.config_button = ttk.Button(
            self.config_frame,
            text="Configurer les options",
            command=self._open_config_panel
        )
        
        self.config_summary_label = ttk.Label(
            self.config_frame,
            text=self._get_config_summary(),
            font=("Arial", 9),
            foreground="gray"
        )
        
        # Section actions
        self.actions_frame = ttk.LabelFrame(
            self.main_frame,
            text="🚀 Actions",
            padding="15"
        )
        
        self.start_button = ttk.Button(
            self.actions_frame,
            text="Démarrer le doublage",
            command=self._start_processing,
            style="Accent.TButton"
        )
        
        self.cancel_button = ttk.Button(
            self.actions_frame,
            text="Annuler",
            command=self._cancel_processing,
            state="disabled"
        )
        
        self.detailed_progress_button = ttk.Button(
            self.actions_frame,
            text="Progression détaillée",
            command=self._show_detailed_progress,
            state="disabled"
        )
        
        self.clear_notifications_button = ttk.Button(
            self.actions_frame,
            text="Effacer notifications",
            command=self._clear_notifications
        )
        
        self.error_summary_button = ttk.Button(
            self.actions_frame,
            text="Historique d'erreurs",
            command=self._show_error_summary
        )
        
        self.system_check_button = ttk.Button(
            self.actions_frame,
            text="Vérifier système",
            command=self._check_system_resources
        )
        
        # Section informations
        self.info_frame = ttk.LabelFrame(
            self.main_frame,
            text="ℹ️ Informations",
            padding="15"
        )
        
        self.info_text = tk.Text(
            self.info_frame,
            height=8,
            width=70,
            font=("Consolas", 9),
            state="disabled",
            wrap=tk.WORD
        )
        
        self.info_scrollbar = ttk.Scrollbar(
            self.info_frame,
            orient="vertical",
            command=self.info_text.yview
        )
        self.info_text.configure(yscrollcommand=self.info_scrollbar.set)
        
        # Barre de statut
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_label = ttk.Label(
            self.status_frame,
            text="Prêt",
            relief="sunken",
            anchor="w"
        )
    
    def _setup_layout(self):
        """Configure la disposition des widgets."""
        # Frame principal
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        self.title_label.pack(pady=(0, 5))
        self.subtitle_label.pack(pady=(0, 20))
        
        # Sélection de fichier
        self.file_frame.pack(fill=tk.X, pady=(0, 15))
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.browse_button.pack(side=tk.RIGHT)
        
        # Configuration
        self.config_frame.pack(fill=tk.X, pady=(0, 15))
        self.config_button.pack(anchor=tk.W)
        self.config_summary_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Actions
        self.actions_frame.pack(fill=tk.X, pady=(0, 15))
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        self.detailed_progress_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Boutons de droite
        self.clear_notifications_button.pack(side=tk.RIGHT)
        self.system_check_button.pack(side=tk.RIGHT, padx=(0, 10))
        self.error_summary_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Informations
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Barre de statut
        self.status_frame.pack(fill=tk.X)
        self.status_label.pack(fill=tk.X)
    
    def _bind_events(self):
        """Lie les événements."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _browse_video_file(self):
        """Ouvre le dialogue de sélection de fichier vidéo."""
        filetypes = [
            ("Fichiers vidéo", "*.mp4 *.avi *.mkv *.mov *.wmv"),
            ("MP4", "*.mp4"),
            ("AVI", "*.avi"),
            ("MKV", "*.mkv"),
            ("Tous les fichiers", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier vidéo",
            filetypes=filetypes
        )
        
        if filename:
            self.selected_video_path.set(filename)
            self._log_info(f"Fichier sélectionné: {filename}")
            self._update_start_button_state()
    
    def _open_config_panel(self):
        """Ouvre le panneau de configuration."""
        if self.config_panel is None or not self.config_panel.window.winfo_exists():
            self.config_panel = ConfigPanel(
                parent=self.root,
                config=self.current_config,
                on_config_changed=self._on_config_changed
            )
        else:
            self.config_panel.window.lift()
    
    def _on_config_changed(self, new_config: PipelineConfig):
        """Appelé quand la configuration change."""
        self.current_config = new_config
        self.config_summary_label.config(text=self._get_config_summary())
        self._log_info("Configuration mise à jour")
    
    def _get_config_summary(self) -> str:
        """Retourne un résumé de la configuration."""
        summary_parts = []
        
        if self.current_config.enable_source_separation:
            summary_parts.append("Séparation de source")
        
        if self.current_config.enable_ocr:
            summary_parts.append("OCR activé")
        
        summary_parts.append(f"ASR: {self.current_config.asr_model}")
        summary_parts.append(f"Langue: {self.current_config.target_language}")
        
        return " • ".join(summary_parts) if summary_parts else "Configuration par défaut"   
 
    def _start_processing(self):
        """Démarre le traitement du doublage."""
        video_path = self.selected_video_path.get()
        
        if not video_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier vidéo.")
            return
        
        if not Path(video_path).exists():
            messagebox.showerror("Erreur", "Le fichier vidéo sélectionné n'existe pas.")
            return
        
        try:
            # Démarrer le monitoring
            self.progress_monitor.start_monitoring()
            
            # Créer l'orchestrateur
            self.pipeline_orchestrator = PipelineOrchestrator(self.current_config)
            
            # Ouvrir la fenêtre de progression
            self.progress_dialog = ProgressDialog(
                parent=self.root,
                on_cancel=self._cancel_processing
            )
            
            # Enregistrer le callback de progression
            self.pipeline_orchestrator.register_progress_callback(
                self._on_progress_update
            )
            
            # Mettre à jour l'interface
            self._set_processing_state(True)
            self._log_info(f"Démarrage du traitement: {video_path}")
            
            # Démarrer le traitement en arrière-plan
            def run_pipeline():
                try:
                    result = self.pipeline_orchestrator.execute_pipeline(video_path)
                    
                    # Traitement terminé avec succès
                    self.root.after(0, lambda: self._on_processing_completed(result))
                    
                except Exception as e:
                    # Traitement échoué
                    self.root.after(0, lambda: self._on_processing_failed(str(e)))
            
            processing_thread = threading.Thread(target=run_pipeline, daemon=True)
            processing_thread.start()
            
            # Démarrer la mise à jour périodique de la progression détaillée
            self._start_progress_updates()
            
        except Exception as e:
            # Utiliser le gestionnaire d'erreurs
            error_info = self.error_handler.handle_exception(e, {
                'component': 'main_window',
                'operation': 'start_processing',
                'video_path': video_path
            })
            
            self._set_processing_state(False)
    
    def _cancel_processing(self):
        """Annule le traitement en cours."""
        if self.pipeline_orchestrator:
            self.pipeline_orchestrator.cancel_processing()
            self._log_info("Annulation du traitement demandée...")
    
    def _on_progress_update(self, progress_info: ProgressInfo):
        """Appelé lors des mises à jour de progression."""
        # Mettre à jour dans le thread principal
        self.root.after(0, lambda: self._update_progress_ui(progress_info))
    
    def _on_notification(self, notification):
        """Appelé lors des nouvelles notifications."""
        # Afficher la notification dans le thread principal
        self.root.after(0, lambda: self.notification_manager.show_notification(notification))
    
    def _update_progress_ui(self, progress_info: ProgressInfo):
        """Met à jour l'interface de progression."""
        # Mettre à jour la barre de statut
        self.status_label.config(
            text=f"[{progress_info.progress:.1f}%] {progress_info.message}"
        )
        
        # Mettre à jour la fenêtre de progression si ouverte
        if self.progress_dialog:
            self.progress_dialog.update_progress(progress_info)
        
        # Logger l'information
        self._log_info(f"[{progress_info.progress:.1f}%] {progress_info.stage.value}: {progress_info.message}")
    
    def _start_progress_updates(self):
        """Démarre les mises à jour périodiques de la progression."""
        def update_progress():
            if self.pipeline_orchestrator and self.pipeline_orchestrator.state == PipelineState.RUNNING:
                # Mettre à jour la fenêtre de progression détaillée si ouverte
                if (self.detailed_progress_window and 
                    self.detailed_progress_window.winfo_exists()):
                    progress_data = self.progress_monitor.get_detailed_progress()
                    self.detailed_progress_window.update_detailed_progress(progress_data)
                
                # Programmer la prochaine mise à jour
                self.root.after(1000, update_progress)  # Toutes les secondes
        
        update_progress()
    
    def _on_processing_completed(self, result):
        """Appelé quand le traitement est terminé avec succès."""
        self._set_processing_state(False)
        
        # Envoyer notification de fin
        self.progress_monitor.send_completion_notification(
            result.output_video_path,
            result.processing_time
        )
        
        # Fermer la fenêtre de progression
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Afficher les résultats
        self.results_window = ResultsWindow(
            parent=self.root,
            result=result
        )
        
        self._log_info(f"✅ Traitement terminé avec succès!")
        self._log_info(f"Fichier de sortie: {result.output_video_path}")
        self._log_info(f"Temps de traitement: {result.processing_time:.2f}s")
        
        # Afficher les statistiques de performance
        perf_summary = self.progress_monitor.get_performance_summary()
        if perf_summary:
            self._log_info(f"📊 Statistiques: {perf_summary['completed_stages']}/{perf_summary['total_stages']} étapes terminées")
    
    def _on_processing_failed(self, error_message: str):
        """Appelé quand le traitement échoue."""
        self._set_processing_state(False)
        
        # Envoyer notification d'erreur
        self.progress_monitor.send_error_notification(
            error_message,
            "Vérifiez les logs pour plus de détails et réessayez avec des paramètres différents."
        )
        
        # Fermer la fenêtre de progression
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self._log_info(f"❌ Traitement échoué: {error_message}")
        
        messagebox.showerror(
            "Erreur de traitement",
            f"Le traitement a échoué:\n\n{error_message}\n\n"
            f"Consultez les informations ci-dessous pour plus de détails."
        )
    
    def _set_processing_state(self, processing: bool):
        """Met à jour l'état de l'interface selon le traitement."""
        if processing:
            self.start_button.config(state="disabled")
            self.cancel_button.config(state="normal")
            self.browse_button.config(state="disabled")
            self.config_button.config(state="disabled")
            self.detailed_progress_button.config(state="normal")
            self.status_label.config(text="Traitement en cours...")
        else:
            self.start_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            self.browse_button.config(state="normal")
            self.config_button.config(state="normal")
            self.detailed_progress_button.config(state="disabled")
            self.status_label.config(text="Prêt")
            self._update_start_button_state()
    
    def _update_start_button_state(self):
        """Met à jour l'état du bouton de démarrage."""
        if self.selected_video_path.get():
            self.start_button.config(state="normal")
        else:
            self.start_button.config(state="disabled")
    
    def _show_detailed_progress(self):
        """Affiche la fenêtre de progression détaillée."""
        if self.detailed_progress_window is None or not self.detailed_progress_window.winfo_exists():
            self.detailed_progress_window = DetailedProgressWindow(self.root)
            
            # Mettre à jour avec les données actuelles
            progress_data = self.progress_monitor.get_detailed_progress()
            self.detailed_progress_window.update_detailed_progress(progress_data)
        else:
            self.detailed_progress_window.lift()
    
    def _clear_notifications(self):
        """Efface toutes les notifications."""
        self.notification_manager.clear_all_notifications()
        self.progress_monitor.clear_notifications()
        self._log_info("Notifications effacées")
    
    def _on_error_occurred(self, error_info):
        """Appelé quand une erreur se produit."""
        # Afficher automatiquement le dialogue d'erreur pour les erreurs critiques
        if error_info.severity.value in ['high', 'critical']:
            self.root.after(0, lambda: show_error_dialog(
                self.root, 
                error_info, 
                self._on_solution_applied
            ))
        
        # Logger l'erreur
        self._log_info(f"❌ {error_info.title}: {error_info.message}")
    
    def _on_solution_applied(self, solution, result):
        """Appelé quand une solution d'erreur a été appliquée."""
        if result:
            self._log_info(f"✅ Solution appliquée: {solution.title}")
        else:
            self._log_info(f"❌ Échec de la solution: {solution.title}")
    
    def _show_error_summary(self):
        """Affiche le résumé des erreurs."""
        show_error_summary(self.root, self.error_handler)
    
    def _check_system_resources(self):
        """Vérifie les ressources système."""
        self._log_info("🔍 Vérification des ressources système...")
        
        def check_resources():
            try:
                issues = self.error_handler.check_system_resources()
                
                # Mettre à jour l'interface dans le thread principal
                self.root.after(0, lambda: self._on_resource_check_completed(issues))
                
            except Exception as e:
                self.root.after(0, lambda: self._log_info(f"❌ Erreur lors de la vérification: {e}"))
        
        # Exécuter la vérification dans un thread séparé
        check_thread = threading.Thread(target=check_resources, daemon=True)
        check_thread.start()
    
    def _on_resource_check_completed(self, issues):
        """Appelé quand la vérification des ressources est terminée."""
        if not issues:
            self._log_info("✅ Système: Toutes les ressources sont dans les limites normales")
            messagebox.showinfo(
                "Vérification Système",
                "✅ Toutes les ressources système sont dans les limites normales."
            )
        else:
            self._log_info(f"⚠️ Système: {len(issues)} problème(s) détecté(s)")
            
            # Afficher un résumé des problèmes
            problems_text = "Problèmes détectés:\\n\\n"
            for issue in issues:
                problems_text += f"• {issue.title}: {issue.message}\\n"
            
            messagebox.showwarning("Problèmes Système", problems_text)
    
    def _log_info(self, message: str):
        """Ajoute un message dans la zone d'informations."""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.info_text.config(state="normal")
        self.info_text.insert(tk.END, formatted_message)
        self.info_text.see(tk.END)
        self.info_text.config(state="disabled")
    
    def _on_closing(self):
        """Appelé lors de la fermeture de la fenêtre."""
        if self.pipeline_orchestrator and self.pipeline_orchestrator.state == PipelineState.RUNNING:
            if messagebox.askokcancel(
                "Fermeture",
                "Un traitement est en cours. Voulez-vous vraiment fermer l'application?"
            ):
                self._cancel_processing()
                self.root.after(1000, self.root.destroy)  # Attendre un peu avant de fermer
        else:
            self.root.destroy()
    
    def run(self):
        """Lance l'application."""
        self._log_info("🎬 Application AI Video Dubbing démarrée")
        self._log_info("Sélectionnez un fichier vidéo pour commencer")
        self.root.mainloop()


def main():
    """Point d'entrée principal pour l'interface graphique."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()