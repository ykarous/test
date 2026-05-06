#!/usr/bin/env python3
"""
Démonstration du système de monitoring et notifications.
"""

import os
import sys
import threading
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from ai_video_dubbing.models.data_models import PipelineStage


class MonitoringDemo:
    """Démonstration du système de monitoring."""

    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None

        if GUI_AVAILABLE:
            self._setup_gui()
        else:
            print("Interface graphique non disponible, utilisation du mode console.")

    def _setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Démonstration - Système de Monitoring")
        self.root.geometry("800x600")

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Démonstration du Système de Monitoring",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(pady=(0, 20))

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 20))

        self.start_button = ttk.Button(
            controls_frame,
            text="Démarrer Simulation",
            command=self.start_simulation,
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(
            controls_frame,
            text="Arrêter",
            command=self.stop_simulation,
            state="disabled",
        )
        self.stop_button.pack(side=tk.LEFT)

        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))

        self.overall_progress = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.overall_progress.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Prêt")
        self.progress_label.pack()

        stages_frame = ttk.LabelFrame(main_frame, text="Étapes", padding="10")
        stages_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.stage_list = tk.Listbox(stages_frame, height=10)
        self.stage_list.pack(fill=tk.BOTH, expand=True)

        logs_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=False)

        self.logs_text = tk.Text(logs_frame, height=8, font=("Consolas", 9), wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)

        self._populate_stages()
        self._log_message("Démonstration initialisée")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _populate_stages(self):
        self.stage_list.delete(0, tk.END)
        for stage in PipelineStage:
            self.stage_list.insert(tk.END, f"{stage.value}")

    def _log_message(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        if GUI_AVAILABLE:
            self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.logs_text.see(tk.END)
        else:
            print(f"[{timestamp}] {message}")

    def start_simulation(self):
        if self.running:
            return
        self.running = True
        if GUI_AVAILABLE:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.progress_label.configure(text="Simulation en cours…")
        self._thread = threading.Thread(target=self._simulate, daemon=True)
        self._thread.start()
        self._log_message("Simulation démarrée")

    def stop_simulation(self):
        self.running = False
        if GUI_AVAILABLE:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.progress_label.configure(text="Arrêt demandé")
        self._log_message("Arrêt demandé")

    def _simulate(self):
        stages = list(PipelineStage)
        total = max(1, len(stages))
        for i, stage in enumerate(stages, start=1):
            if not self.running:
                break
            percent = int((i / total) * 100)
            msg = f"Étape: {stage.value} ({percent}%)"
            if GUI_AVAILABLE:
                self.root.after(0, self._update_progress, percent, msg)
            else:
                self._log_message(msg)
            time.sleep(0.4)

        self.running = False
        if GUI_AVAILABLE:
            self.root.after(0, self._update_finished)
        else:
            self._log_message("Simulation terminée")

    def _update_progress(self, percent: int, msg: str):
        self.overall_progress["value"] = percent
        self.progress_label.configure(text=msg)
        self._log_message(msg)

    def _update_finished(self):
        self.overall_progress["value"] = 100
        self.progress_label.configure(text="Terminé")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._log_message("Simulation terminée")

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        if GUI_AVAILABLE:
            self.root.mainloop()
        else:
            self.start_simulation()
            while self.running:
                time.sleep(0.2)


def main():
    demo = MonitoringDemo()
    demo.run()


if __name__ == "__main__":
    main()
