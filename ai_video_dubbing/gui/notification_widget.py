#!/usr/bin/env python3
"""
Widget de notifications pour l'interface graphique.
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
from typing import Dict, List, Optional

from .progress_monitor import Notification, NotificationType


class NotificationWidget(tk.Toplevel):
    """Widget de notification flottante."""
    
    def __init__(self, parent, notification: Notification):
        super().__init__(parent)
        
        self.notification = notification
        self.parent = parent
        
        # Configuration de la fenêtre
        self.withdraw()  # Cacher initialement
        self.overrideredirect(True)  # Pas de bordure de fenêtre
        self.attributes('-topmost', True)  # Toujours au premier plan
        
        # Style selon le type
        self.colors = {
            NotificationType.INFO: {"bg": "#e3f2fd", "fg": "#1976d2", "border": "#2196f3"},
            NotificationType.SUCCESS: {"bg": "#e8f5e8", "fg": "#2e7d32", "border": "#4caf50"},
            NotificationType.WARNING: {"bg": "#fff3e0", "fg": "#f57c00", "border": "#ff9800"},
            NotificationType.ERROR: {"bg": "#ffebee", "fg": "#d32f2f", "border": "#f44336"}
        }
        
        self._create_widgets()
        self._position_window()
        
        # Auto-fermeture si durée spécifiée
        if notification.duration:
            self.after(int(notification.duration * 1000), self.close_notification)
    
    def _create_widgets(self):
        """Crée les widgets de la notification."""
        color_scheme = self.colors[self.notification.type]
        
        # Frame principal avec bordure colorée
        main_frame = tk.Frame(
            self,
            bg=color_scheme["bg"],
            relief="solid",
            bd=2,
            highlightbackground=color_scheme["border"],
            highlightthickness=1
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Header avec titre et bouton fermer
        header_frame = tk.Frame(main_frame, bg=color_scheme["bg"])
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Icône selon le type
        icon_text = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌"
        }
        
        icon_label = tk.Label(
            header_frame,
            text=icon_text[self.notification.type],
            bg=color_scheme["bg"],
            font=("Arial", 12)
        )
        icon_label.pack(side="left")
        
        # Titre
        title_label = tk.Label(
            header_frame,
            text=self.notification.title,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("Arial", 10, "bold")
        )
        title_label.pack(side="left", padx=(5, 0))
        
        # Bouton fermer
        close_button = tk.Button(
            header_frame,
            text="✕",
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            relief="flat",
            font=("Arial", 8),
            command=self.close_notification,
            cursor="hand2"
        )
        close_button.pack(side="right")
        
        # Message
        message_label = tk.Label(
            main_frame,
            text=self.notification.message,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("Arial", 9),
            wraplength=300,
            justify="left"
        )
        message_label.pack(fill="x", padx=10, pady=(0, 10))
        
        # Bouton d'action si présent
        if self.notification.action_callback and self.notification.action_text:
            action_button = tk.Button(
                main_frame,
                text=self.notification.action_text,
                bg=color_scheme["border"],
                fg="white",
                relief="flat",
                font=("Arial", 9),
                command=self._execute_action,
                cursor="hand2"
            )
            action_button.pack(pady=(0, 10))
        
        # Horodatage
        timestamp = time.strftime("%H:%M:%S", time.localtime(self.notification.timestamp))
        time_label = tk.Label(
            main_frame,
            text=timestamp,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("Arial", 8)
        )
        time_label.pack(anchor="e", padx=10, pady=(0, 5))
    
    def _position_window(self):
        """Positionne la fenêtre de notification."""
        self.update_idletasks()
        
        # Obtenir les dimensions
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Position en bas à droite de l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = screen_width - width - 20
        y = screen_height - height - 60
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Afficher avec animation
        self.deiconify()
        self._animate_in()
    
    def _animate_in(self):
        """Animation d'apparition."""
        self.attributes('-alpha', 0.0)
        self._fade_in(0.0)
    
    def _fade_in(self, alpha):
        """Effet de fondu entrant."""
        if alpha < 1.0:
            self.attributes('-alpha', alpha)
            self.after(20, lambda: self._fade_in(alpha + 0.1))
        else:
            self.attributes('-alpha', 1.0)
    
    def _execute_action(self):
        """Exécute l'action de la notification."""
        if self.notification.action_callback:
            try:
                self.notification.action_callback()
            except Exception as e:
                print(f"Erreur action notification: {e}")
        self.close_notification()
    
    def close_notification(self):
        """Ferme la notification avec animation."""
        self._fade_out(1.0)
    
    def _fade_out(self, alpha):
        """Effet de fondu sortant."""
        if alpha > 0.0:
            self.attributes('-alpha', alpha)
            self.after(20, lambda: self._fade_out(alpha - 0.1))
        else:
            self.destroy()


class NotificationManager:
    """Gestionnaire de notifications pour l'interface graphique."""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.active_notifications: List[NotificationWidget] = []
        self.max_notifications = 5
        
    def show_notification(self, notification: Notification):
        """Affiche une nouvelle notification."""
        # Limiter le nombre de notifications actives
        if len(self.active_notifications) >= self.max_notifications:
            # Fermer la plus ancienne
            oldest = self.active_notifications.pop(0)
            oldest.close_notification()
        
        # Créer et afficher la nouvelle notification
        try:
            widget = NotificationWidget(self.parent, notification)
            self.active_notifications.append(widget)
            
            # Repositionner les notifications existantes
            self._reposition_notifications()
            
        except Exception as e:
            print(f"Erreur affichage notification: {e}")
    
    def _reposition_notifications(self):
        """Repositionne toutes les notifications actives."""
        screen_height = self.parent.winfo_screenheight()
        screen_width = self.parent.winfo_screenwidth()
        
        y_offset = 60
        for i, notification in enumerate(reversed(self.active_notifications)):
            try:
                notification.update_idletasks()
                width = notification.winfo_reqwidth()
                height = notification.winfo_reqheight()
                
                x = screen_width - width - 20
                y = screen_height - y_offset - height
                
                notification.geometry(f"{width}x{height}+{x}+{y}")
                y_offset += height + 10
                
            except Exception as e:
                print(f"Erreur repositionnement notification: {e}")
    
    def clear_all_notifications(self):
        """Ferme toutes les notifications actives."""
        for notification in self.active_notifications[:]:
            notification.close_notification()
        self.active_notifications.clear()


class ProgressBar(ttk.Frame):
    """Barre de progression avancée avec détails des étapes."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_progress = 0.0
        self.current_stage = None
        self.current_message = ""
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crée les widgets de la barre de progression."""
        # Label de l'étape actuelle
        self.stage_label = tk.Label(
            self,
            text="Prêt",
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        self.stage_label.pack(fill="x", pady=(0, 5))
        
        # Frame pour la barre et le pourcentage
        progress_frame = tk.Frame(self)
        progress_frame.pack(fill="x", pady=(0, 5))
        
        # Barre de progression
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=400
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)
        
        # Label du pourcentage
        self.percent_label = tk.Label(
            progress_frame,
            text="0%",
            font=("Arial", 9),
            width=6
        )
        self.percent_label.pack(side="right", padx=(10, 0))
        
        # Message détaillé
        self.message_label = tk.Label(
            self,
            text="En attente...",
            font=("Arial", 9),
            anchor="w",
            fg="gray"
        )
        self.message_label.pack(fill="x")
        
        # Temps estimé
        self.time_label = tk.Label(
            self,
            text="",
            font=("Arial", 8),
            anchor="e",
            fg="gray"
        )
        self.time_label.pack(fill="x", pady=(5, 0))
    
    def update_progress(self, progress: float, stage: str = None, 
                       message: str = None, estimated_remaining: float = None):
        """Met à jour la progression."""
        self.current_progress = progress
        
        # Mettre à jour la barre
        self.progress_bar["value"] = progress
        self.percent_label.config(text=f"{progress:.1f}%")
        
        # Mettre à jour l'étape
        if stage and stage != self.current_stage:
            self.current_stage = stage
            self.stage_label.config(text=stage)
        
        # Mettre à jour le message
        if message and message != self.current_message:
            self.current_message = message
            self.message_label.config(text=message)
        
        # Mettre à jour le temps estimé
        if estimated_remaining is not None:
            if estimated_remaining > 0:
                minutes, seconds = divmod(int(estimated_remaining), 60)
                time_text = f"Temps restant estimé: {minutes:02d}:{seconds:02d}"
                self.time_label.config(text=time_text)
            else:
                self.time_label.config(text="")
    
    def reset(self):
        """Remet la barre à zéro."""
        self.current_progress = 0.0
        self.current_stage = None
        self.current_message = ""
        
        self.progress_bar["value"] = 0
        self.percent_label.config(text="0%")
        self.stage_label.config(text="Prêt")
        self.message_label.config(text="En attente...")
        self.time_label.config(text="")


class DetailedProgressWindow(tk.Toplevel):
    """Fenêtre de progression détaillée."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Progression Détaillée")
        self.geometry("600x500")
        self.resizable(True, True)
        
        # Centrer la fenêtre
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Variables
        self.stage_frames = {}
    
    def _create_widgets(self):
        """Crée les widgets de la fenêtre."""
        # Frame principal avec scrollbar
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = ttk.Frame(main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titre
        title_label = tk.Label(
            self.scrollable_frame,
            text="Progression Détaillée du Pipeline",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame pour les étapes
        self.stages_frame = ttk.Frame(self.scrollable_frame)
        self.stages_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    def update_detailed_progress(self, progress_data: Dict):
        """Met à jour la progression détaillée."""
        stages_data = progress_data.get("stages", {})
        
        for stage_key, stage_info in stages_data.items():
            if stage_key not in self.stage_frames:
                self._create_stage_frame(stage_key, stage_info)
            
            self._update_stage_frame(stage_key, stage_info)
    
    def _create_stage_frame(self, stage_key: str, stage_info: Dict):
        """Crée un frame pour une étape."""
        # Frame principal de l'étape
        stage_frame = ttk.LabelFrame(
            self.stages_frame,
            text=stage_info["name"],
            padding=10
        )
        stage_frame.pack(fill="x", pady=5)
        
        # Description
        desc_label = tk.Label(
            stage_frame,
            text=stage_info["description"],
            font=("Arial", 9),
            fg="gray",
            wraplength=500
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        # Barre de progression de l'étape
        progress_frame = tk.Frame(stage_frame)
        progress_frame.pack(fill="x", pady=5)
        
        progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=300
        )
        progress_bar.pack(side="left", fill="x", expand=True)
        
        status_label = tk.Label(
            progress_frame,
            text="En attente",
            font=("Arial", 9),
            width=15
        )
        status_label.pack(side="right", padx=(10, 0))
        
        # Sous-étapes
        substeps_frame = tk.Frame(stage_frame)
        substeps_frame.pack(fill="x", pady=(5, 0))
        
        # Stocker les références
        self.stage_frames[stage_key] = {
            "frame": stage_frame,
            "progress_bar": progress_bar,
            "status_label": status_label,
            "substeps_frame": substeps_frame,
            "substep_labels": {}
        }
    
    def _update_stage_frame(self, stage_key: str, stage_info: Dict):
        """Met à jour un frame d'étape."""
        if stage_key not in self.stage_frames:
            return
        
        frame_info = self.stage_frames[stage_key]
        
        # Mettre à jour la progression
        progress = stage_info.get("progress", 0)
        frame_info["progress_bar"]["value"] = progress
        
        # Mettre à jour le statut
        status = stage_info.get("status", "pending")
        status_text = {
            "pending": "⏳ En attente",
            "running": "🔄 En cours",
            "completed": "✅ Terminé",
            "failed": "❌ Échoué"
        }.get(status, status)
        
        frame_info["status_label"].config(text=status_text)
        
        # Mettre à jour les sous-étapes
        current_substep = stage_info.get("current_substep")
        substeps = stage_info.get("substeps", [])
        
        # Créer les labels de sous-étapes si nécessaire
        for i, substep in enumerate(substeps):
            if i not in frame_info["substep_labels"]:
                substep_label = tk.Label(
                    frame_info["substeps_frame"],
                    text=f"  • {substep}",
                    font=("Arial", 8),
                    anchor="w"
                )
                substep_label.pack(anchor="w")
                frame_info["substep_labels"][i] = substep_label
        
        # Mettre en évidence la sous-étape actuelle
        for i, label in frame_info["substep_labels"].items():
            if i < len(substeps):
                substep_text = substeps[i]
                if substep_text == current_substep:
                    label.config(fg="blue", font=("Arial", 8, "bold"))
                    label.config(text=f"  ▶ {substep_text}")
                else:
                    label.config(fg="black", font=("Arial", 8))
                    label.config(text=f"  • {substep_text}")