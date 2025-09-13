#!/usr/bin/env python3
"""
Démonstration du système de monitoring et notifications.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from ai_video_dubbing.models.data_models import PipelineStage, ProgressInfo, PipelineConfig


class MonitoringDemo:
    """Démonstration du système de monitoring."""
    
    def __init__(self):
        """Initialise la démonstration."""
        self.running = False
        
        if GUI_AVAILABLE:
            self.setup_gui()
        else:
            print("Interface graphique non disponible, utilisation du mode console.")
    
    def setup_gui(self):
        """Configure l'interface graphique de démonstration."""
        self.root = tk.Tk()
        self.root.title("Démonstration - Système de Monitoring")
        self.root.geometry("800x600")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="🎬 Démonstration du Système de Monitoring",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Boutons de contrôle
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = ttk.Button(
            controls_frame,
            text="🚀 Démarrer Simulation",
            command=self.start_simulation
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            controls_frame,
            text="⏹️ Arrêter",
            command=self.stop_simulation,
            state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # Barre de progression globale
        progress_frame = ttk.LabelFrame(main_frame, text="Progression Globale", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.overall_progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=400
        )
        self.overall_progress.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="Prêt")\n        self.progress_label.pack()\n        \n        # Zone d'affichage des étapes\n        stages_frame = ttk.LabelFrame(main_frame, text="Étapes du Pipeline", padding="10")\n        stages_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))\n        \n        # Créer un canvas avec scrollbar pour les étapes\n        canvas = tk.Canvas(stages_frame)\n        scrollbar = ttk.Scrollbar(stages_frame, orient="vertical", command=canvas.yview)\n        self.stages_frame_inner = ttk.Frame(canvas)\n        \n        self.stages_frame_inner.bind(\n            "<Configure>",\n            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))\n        )\n        \n        canvas.create_window((0, 0), window=self.stages_frame_inner, anchor="nw")\n        canvas.configure(yscrollcommand=scrollbar.set)\n        \n        canvas.pack(side="left", fill="both", expand=True)\n        scrollbar.pack(side="right", fill="y")\n        \n        # Zone de logs\n        logs_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")\n        logs_frame.pack(fill=tk.X)\n        \n        self.logs_text = tk.Text(\n            logs_frame,\n            height=8,\n            font=("Consolas", 9),\n            wrap=tk.WORD\n        )\n        logs_scrollbar = ttk.Scrollbar(logs_frame, orient="vertical", command=self.logs_text.yview)\n        self.logs_text.configure(yscrollcommand=logs_scrollbar.set)\n        \n        self.logs_text.pack(side="left", fill="both", expand=True)\n        logs_scrollbar.pack(side="right", fill="y")\n        \n        # Variables pour les étapes\n        self.stage_widgets = {}\n        self.create_stage_widgets()\n        \n        # Log initial\n        self.log_message("🎬 Démonstration du système de monitoring initialisée")\n        self.log_message("Cliquez sur 'Démarrer Simulation' pour voir le monitoring en action")\n    \n    def create_stage_widgets(self):\n        """Crée les widgets pour chaque étape."""\n        stages = [\n            (PipelineStage.INITIALIZATION, "Initialisation", "Préparation du pipeline"),\n            (PipelineStage.VIDEO_PROCESSING, "Traitement Vidéo", "Extraction audio et métadonnées"),\n            (PipelineStage.AUDIO_ANALYSIS, "Analyse Audio", "Détection d'activité vocale"),\n            (PipelineStage.TRANSCRIPTION, "Transcription", "Conversion audio vers texte"),\n            (PipelineStage.OCR_EXTRACTION, "Extraction OCR", "Lecture des sous-titres"),\n            (PipelineStage.SYNCHRONIZATION, "Synchronisation", "Alignement ASR/OCR"),\n            (PipelineStage.VOICE_CLONING, "Clonage de Voix", "Génération des nouvelles voix"),\n            (PipelineStage.AUDIO_MIXING, "Mixage Audio", "Combinaison des pistes"),\n            (PipelineStage.VIDEO_ASSEMBLY, "Assemblage Final", "Création de la vidéo finale")\n        ]\n        \n        for stage, name, description in stages:\n            # Frame pour l'étape\n            stage_frame = ttk.Frame(self.stages_frame_inner)\n            stage_frame.pack(fill=tk.X, pady=2)\n            \n            # Nom de l'étape\n            name_label = ttk.Label(\n                stage_frame,\n                text=name,\n                font=("Arial", 10, "bold"),\n                width=20,\n                anchor="w"\n            )\n            name_label.pack(side=tk.LEFT, padx=(0, 10))\n            \n            # Barre de progression de l'étape\n            progress_bar = ttk.Progressbar(\n                stage_frame,\n                mode="determinate",\n                length=200\n            )\n            progress_bar.pack(side=tk.LEFT, padx=(0, 10))\n            \n            # Statut\n            status_label = ttk.Label(\n                stage_frame,\n                text="⏳ En attente",\n                width=15,\n                anchor="w"\n            )\n            status_label.pack(side=tk.LEFT, padx=(0, 10))\n            \n            # Message\n            message_label = ttk.Label(\n                stage_frame,\n                text=description,\n                font=("Arial", 9),\n                foreground="gray",\n                anchor="w"\n            )\n            message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)\n            \n            # Stocker les références\n            self.stage_widgets[stage] = {\n                'frame': stage_frame,\n                'progress_bar': progress_bar,\n                'status_label': status_label,\n                'message_label': message_label\n            }\n    \n    def start_simulation(self):\n        """Démarre la simulation du pipeline."""\n        if self.running:\n            return\n        \n        self.running = True\n        self.start_button.config(state="disabled")\n        self.stop_button.config(state="normal")\n        \n        # Réinitialiser l'interface\n        self.overall_progress["value"] = 0\n        self.progress_label.config(text="Démarrage...")\n        \n        for stage_info in self.stage_widgets.values():\n            stage_info['progress_bar']["value"] = 0\n            stage_info['status_label'].config(text="⏳ En attente")\n        \n        self.log_message("🚀 Simulation du pipeline démarrée")\n        \n        # Démarrer la simulation dans un thread\n        simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)\n        simulation_thread.start()\n    \n    def stop_simulation(self):\n        """Arrête la simulation."""\n        self.running = False\n        self.start_button.config(state="normal")\n        self.stop_button.config(state="disabled")\n        self.log_message("⏹️ Simulation arrêtée")\n    \n    def run_simulation(self):\n        """Exécute la simulation du pipeline."""\n        stages = list(self.stage_widgets.keys())\n        total_stages = len(stages)\n        \n        try:\n            for i, stage in enumerate(stages):\n                if not self.running:\n                    break\n                \n                # Mettre à jour le statut de l'étape\n                self.root.after(0, lambda s=stage: self.update_stage_status(s, "🔄 En cours"))\n                \n                stage_name = stage.value.replace("_", " ").title()\n                self.root.after(0, lambda: self.log_message(f"📊 Démarrage: {stage_name}"))\n                \n                # Simuler la progression de l'étape\n                for progress in range(0, 101, 10):\n                    if not self.running:\n                        break\n                    \n                    # Mettre à jour la progression de l'étape\n                    self.root.after(0, lambda s=stage, p=progress: self.update_stage_progress(s, p))\n                    \n                    # Mettre à jour la progression globale\n                    overall_progress = ((i * 100) + progress) / total_stages\n                    self.root.after(0, lambda p=overall_progress: self.update_overall_progress(p))\n                    \n                    # Simuler le temps de traitement\n                    time.sleep(0.2)\n                \n                if self.running:\n                    # Marquer l'étape comme terminée\n                    self.root.after(0, lambda s=stage: self.update_stage_status(s, "✅ Terminé"))\n                    self.root.after(0, lambda: self.log_message(f"✅ Terminé: {stage_name}"))\n            \n            if self.running:\n                # Simulation terminée\n                self.root.after(0, self.simulation_completed)\n            \n        except Exception as e:\n            self.root.after(0, lambda: self.log_message(f"❌ Erreur simulation: {e}"))\n            self.root.after(0, self.stop_simulation)\n    \n    def update_stage_progress(self, stage, progress):\n        """Met à jour la progression d'une étape."""\n        if stage in self.stage_widgets:\n            self.stage_widgets[stage]['progress_bar']["value"] = progress\n    \n    def update_stage_status(self, stage, status):\n        """Met à jour le statut d'une étape."""\n        if stage in self.stage_widgets:\n            self.stage_widgets[stage]['status_label'].config(text=status)\n    \n    def update_overall_progress(self, progress):\n        """Met à jour la progression globale."""\n        self.overall_progress["value"] = progress\n        self.progress_label.config(text=f"Progression: {progress:.1f}%")\n    \n    def simulation_completed(self):\n        """Appelé quand la simulation est terminée."""\n        self.stop_simulation()\n        self.progress_label.config(text="✅ Simulation terminée!")\n        self.log_message("🎉 Simulation du pipeline terminée avec succès!")\n        self.log_message("📁 Fichier de sortie: /demo/output/video_dubbed.mp4")\n        self.log_message("⏱️ Temps de traitement simulé: 45.2 secondes")\n        \n        # Afficher une notification de fin\n        try:\n            from tkinter import messagebox\n            messagebox.showinfo(\n                "Simulation Terminée",\n                "La simulation du pipeline de doublage est terminée!\\n\\n"\n                "Fichier de sortie: /demo/output/video_dubbed.mp4\\n"\n                "Temps de traitement: 45.2 secondes"\n            )\n        except:\n            pass\n    \n    def log_message(self, message):\n        """Ajoute un message aux logs."""\n        timestamp = time.strftime("%H:%M:%S")\n        log_entry = f"[{timestamp}] {message}\\n"\n        \n        self.logs_text.insert(tk.END, log_entry)\n        self.logs_text.see(tk.END)\n    \n    def run_gui(self):\n        """Lance l'interface graphique."""\n        if GUI_AVAILABLE:\n            self.root.mainloop()\n        else:\n            print("Interface graphique non disponible.")\n    \n    def run_console_demo(self):\n        """Exécute une démonstration en mode console."""\n        print("🎬 Démonstration Console du Système de Monitoring")\n        print("=" * 60)\n        \n        stages = [\n            (PipelineStage.INITIALIZATION, "Initialisation"),\n            (PipelineStage.VIDEO_PROCESSING, "Traitement Vidéo"),\n            (PipelineStage.TRANSCRIPTION, "Transcription"),\n            (PipelineStage.VOICE_CLONING, "Clonage de Voix"),\n            (PipelineStage.VIDEO_ASSEMBLY, "Assemblage Final")\n        ]\n        \n        print("\\n🚀 Simulation du pipeline démarrée...\\n")\n        \n        for i, (stage, name) in enumerate(stages):\n            print(f"📊 Étape {i+1}/{len(stages)}: {name}")\n            \n            for progress in range(0, 101, 20):\n                print(f"  [{progress:3d}%] {'█' * (progress // 5)}{'░' * (20 - progress // 5)}")\n                time.sleep(0.3)\n            \n            print(f"  ✅ {name} terminé\\n")\n        \n        print("🎉 Simulation terminée avec succès!")\n        print("📁 Fichier de sortie: /demo/output/video_dubbed.mp4")\n        print("⏱️ Temps de traitement simulé: 25.4 secondes")\n\n\ndef main():\n    """Fonction principale."""\n    print("🎬 AI Video Dubbing - Démonstration du Système de Monitoring")\n    \n    demo = MonitoringDemo()\n    \n    if GUI_AVAILABLE:\n        print("Interface graphique disponible - Lancement de la démonstration GUI")\n        demo.run_gui()\n    else:\n        print("Interface graphique non disponible - Démonstration console")\n        demo.run_console_demo()\n\n\nif __name__ == "__main__":\n    main()