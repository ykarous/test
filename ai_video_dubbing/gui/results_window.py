"""
Fenêtre de résultats pour l'application de doublage vidéo par IA.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import platform
from pathlib import Path
from typing import Optional

from ..models.data_models import ProcessingResults


class ResultsWindow:
    """Fenêtre d'affichage des résultats avec options d'export."""
    
    def __init__(self, parent: tk.Tk, result: ProcessingResults):
        """
        Initialise la fenêtre de résultats.
        
        Args:
            parent: Fenêtre parente
            result: Résultats du traitement
        """
        self.parent = parent
        self.result = result
        
        # Créer la fenêtre
        self.window = tk.Toplevel(parent)
        self.window.title("Résultats - AI Video Dubbing")
        self.window.geometry("700x500")
        self.window.resizable(True, True)
        self.window.transient(parent)
        
        # Créer l'interface
        self._create_widgets()
        self._setup_layout()
        self._populate_results()
        
        # Centrer la fenêtre
        self._center_window()
    
    def _create_widgets(self):
        """Crée tous les widgets de la fenêtre."""
        # Frame principal
        self.main_frame = ttk.Frame(self.window, padding="20")
        
        # Titre
        self.title_label = ttk.Label(
            self.main_frame,
            text="🎉 Traitement terminé avec succès !",
            font=("Arial", 18, "bold"),
            foreground="green"
        )
        
        # Informations sur le fichier de sortie
        self.output_frame = ttk.LabelFrame(
            self.main_frame,
            text="📁 Fichier de sortie",
            padding="15"
        )
        
        self.output_path_var = tk.StringVar(value=self.result.output_video_path)
        self.output_entry = ttk.Entry(
            self.output_frame,
            textvariable=self.output_path_var,
            font=("Consolas", 9),
            state="readonly",
            width=60
        )
        
        self.open_file_button = ttk.Button(
            self.output_frame,
            text="Ouvrir le fichier",
            command=self._open_output_file
        )
        
        self.open_folder_button = ttk.Button(
            self.output_frame,
            text="Ouvrir le dossier",
            command=self._open_output_folder
        )
        
        self.copy_path_button = ttk.Button(
            self.output_frame,
            text="Copier le chemin",
            command=self._copy_path_to_clipboard
        )
        
        # Statistiques du traitement
        self.stats_frame = ttk.LabelFrame(
            self.main_frame,
            text="📊 Statistiques du traitement",
            padding="15"
        )
        
        # Créer un Treeview pour les statistiques
        self.stats_tree = ttk.Treeview(
            self.stats_frame,
            columns=("value",),
            show="tree headings",
            height=10
        )
        
        self.stats_tree.heading("#0", text="Métrique")
        self.stats_tree.heading("value", text="Valeur")
        
        self.stats_tree.column("#0", width=250)
        self.stats_tree.column("value", width=200)
        
        # Scrollbar pour les statistiques
        self.stats_scrollbar = ttk.Scrollbar(
            self.stats_frame,
            orient="vertical",
            command=self.stats_tree.yview
        )
        self.stats_tree.configure(yscrollcommand=self.stats_scrollbar.set)
        
        # Actions d'export
        self.export_frame = ttk.LabelFrame(
            self.main_frame,
            text="💾 Actions d'export",
            padding="15"
        )
        
        self.save_as_button = ttk.Button(
            self.export_frame,
            text="Enregistrer sous...",
            command=self._save_as
        )
        
        self.export_report_button = ttk.Button(
            self.export_frame,
            text="Exporter le rapport",
            command=self._export_report
        )
        
        # Boutons de contrôle
        self.buttons_frame = ttk.Frame(self.main_frame)
        
        self.new_processing_button = ttk.Button(
            self.buttons_frame,
            text="Nouveau traitement",
            command=self._new_processing
        )
        
        self.close_button = ttk.Button(
            self.buttons_frame,
            text="Fermer",
            command=self.window.destroy
        )
    
    def _setup_layout(self):
        """Configure la disposition des widgets."""
        self.main_frame.pack(fill="both", expand=True)
        
        self.title_label.pack(pady=(0, 20))
        
        # Fichier de sortie
        self.output_frame.pack(fill="x", pady=(0, 15))
        
        output_path_frame = ttk.Frame(self.output_frame)
        output_path_frame.pack(fill="x", pady=(0, 10))
        
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        output_buttons_frame = ttk.Frame(self.output_frame)
        output_buttons_frame.pack(fill="x")
        
        self.open_file_button.pack(side="left", padx=(0, 5))
        self.open_folder_button.pack(side="left", padx=(0, 5))
        self.copy_path_button.pack(side="left")
        
        # Statistiques
        self.stats_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        stats_content_frame = ttk.Frame(self.stats_frame)
        stats_content_frame.pack(fill="both", expand=True)
        
        self.stats_tree.pack(side="left", fill="both", expand=True)
        self.stats_scrollbar.pack(side="right", fill="y")
        
        # Export
        self.export_frame.pack(fill="x", pady=(0, 15))
        self.save_as_button.pack(side="left", padx=(0, 10))
        self.export_report_button.pack(side="left")
        
        # Boutons de contrôle
        self.buttons_frame.pack(fill="x")
        self.close_button.pack(side="right")
        self.new_processing_button.pack(side="right", padx=(0, 10))
    
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
    
    def _populate_results(self):
        """Remplit la fenêtre avec les résultats."""
        # Statistiques générales
        general_stats = self.stats_tree.insert("", "end", text="📈 Général", open=True)
        
        self.stats_tree.insert(
            general_stats, "end",
            text="Temps de traitement",
            values=(f"{self.result.processing_time:.2f} secondes",)
        )
        
        self.stats_tree.insert(
            general_stats, "end",
            text="Statut",
            values=("✅ Succès" if self.result.success else "❌ Échec",)
        )
        
        if hasattr(self.result, 'speakers_detected') and self.result.speakers_detected:
            self.stats_tree.insert(
                general_stats, "end",
                text="Locuteurs détectés",
                values=(str(self.result.speakers_detected),)
            )
        
        if hasattr(self.result, 'dialogue_segments') and self.result.dialogue_segments:
            self.stats_tree.insert(
                general_stats, "end",
                text="Segments de dialogue",
                values=(str(self.result.dialogue_segments),)
            )
        
        # Informations sur le fichier
        if os.path.exists(self.result.output_video_path):
            file_stats = self.stats_tree.insert("", "end", text="📁 Fichier", open=True)
            
            file_path = Path(self.result.output_video_path)
            file_size = file_path.stat().st_size
            
            self.stats_tree.insert(
                file_stats, "end",
                text="Taille du fichier",
                values=(self._format_file_size(file_size),)
            )
            
            self.stats_tree.insert(
                file_stats, "end",
                text="Format",
                values=(file_path.suffix.upper(),)
            )
        
        # Transcription
        if self.result.transcription_result:
            transcription_stats = self.stats_tree.insert("", "end", text="🎤 Transcription", open=True)
            
            transcription = self.result.transcription_result
            
            if hasattr(transcription, 'language'):
                self.stats_tree.insert(
                    transcription_stats, "end",
                    text="Langue détectée",
                    values=(transcription.language.upper(),)
                )
            
            if hasattr(transcription, 'confidence'):
                self.stats_tree.insert(
                    transcription_stats, "end",
                    text="Confiance moyenne",
                    values=(f"{transcription.confidence:.1%}",)
                )
            
            if hasattr(transcription, 'word_count'):
                self.stats_tree.insert(
                    transcription_stats, "end",
                    text="Nombre de mots",
                    values=(str(transcription.word_count),)
                )
        
        # OCR
        if self.result.ocr_results:
            ocr_stats = self.stats_tree.insert("", "end", text="👁️ OCR", open=True)
            
            self.stats_tree.insert(
                ocr_stats, "end",
                text="Segments OCR extraits",
                values=(str(len(self.result.ocr_results)),)
            )
        
        # Séparation de source
        if self.result.source_separation_result:
            separation_stats = self.stats_tree.insert("", "end", text="🎵 Séparation de source", open=True)
            
            separation = self.result.source_separation_result
            
            if hasattr(separation, 'separation_quality'):
                self.stats_tree.insert(
                    separation_stats, "end",
                    text="Qualité de séparation",
                    values=(f"{separation.separation_quality:.1%}",)
                )
            
            if hasattr(separation, 'processing_time'):
                self.stats_tree.insert(
                    separation_stats, "end",
                    text="Temps de séparation",
                    values=(f"{separation.processing_time:.2f}s",)
                )
        
        # Métriques de qualité
        if hasattr(self.result, 'quality_metrics') and self.result.quality_metrics:
            quality_stats = self.stats_tree.insert("", "end", text="⭐ Qualité", open=True)
            
            for metric, value in self.result.quality_metrics.items():
                self.stats_tree.insert(
                    quality_stats, "end",
                    text=metric.replace("_", " ").title(),
                    values=(f"{value:.3f}" if isinstance(value, float) else str(value),)
                )
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formate une taille de fichier en unités lisibles."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _open_output_file(self):
        """Ouvre le fichier de sortie avec l'application par défaut."""
        try:
            if platform.system() == "Windows":
                os.startfile(self.result.output_video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.result.output_video_path])
            else:  # Linux
                subprocess.run(["xdg-open", self.result.output_video_path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier:\n{e}")
    
    def _open_output_folder(self):
        """Ouvre le dossier contenant le fichier de sortie."""
        try:
            folder_path = os.path.dirname(self.result.output_video_path)
            
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}")
    
    def _copy_path_to_clipboard(self):
        """Copie le chemin du fichier dans le presse-papiers."""
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(self.result.output_video_path)
            messagebox.showinfo("Succès", "Chemin copié dans le presse-papiers!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier le chemin:\n{e}")
    
    def _save_as(self):
        """Enregistre le fichier sous un nouveau nom."""
        try:
            source_path = Path(self.result.output_video_path)
            
            filename = filedialog.asksaveasfilename(
                title="Enregistrer sous...",
                defaultextension=source_path.suffix,
                filetypes=[
                    ("Fichiers vidéo", "*.mp4 *.avi *.mkv"),
                    ("MP4", "*.mp4"),
                    ("AVI", "*.avi"),
                    ("MKV", "*.mkv"),
                    ("Tous les fichiers", "*.*")
                ],
                initialname=f"dubbed_{source_path.stem}{source_path.suffix}"
            )
            
            if filename:
                import shutil
                shutil.copy2(self.result.output_video_path, filename)
                messagebox.showinfo("Succès", f"Fichier enregistré sous:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le fichier:\n{e}")
    
    def _export_report(self):
        """Exporte un rapport détaillé du traitement."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Exporter le rapport",
                defaultextension=".txt",
                filetypes=[
                    ("Fichiers texte", "*.txt"),
                    ("Fichiers JSON", "*.json"),
                    ("Tous les fichiers", "*.*")
                ],
                initialname="rapport_doublage.txt"
            )
            
            if filename:
                self._generate_report(filename)
                messagebox.showinfo("Succès", f"Rapport exporté vers:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter le rapport:\n{e}")
    
    def _generate_report(self, filename: str):
        """Génère un rapport détaillé."""
        import datetime
        import json
        
        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "output_file": self.result.output_video_path,
            "processing_time": self.result.processing_time,
            "success": self.result.success,
            "error_message": self.result.error_message
        }
        
        # Ajouter les données disponibles
        if hasattr(self.result, 'speakers_detected'):
            report_data["speakers_detected"] = self.result.speakers_detected
        
        if hasattr(self.result, 'dialogue_segments'):
            report_data["dialogue_segments"] = self.result.dialogue_segments
        
        if hasattr(self.result, 'quality_metrics'):
            report_data["quality_metrics"] = self.result.quality_metrics
        
        if filename.endswith('.json'):
            # Export JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
        else:
            # Export texte
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== RAPPORT DE DOUBLAGE VIDÉO IA ===\n\n")
                f.write(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Fichier de sortie: {self.result.output_video_path}\n")
                f.write(f"Temps de traitement: {self.result.processing_time:.2f} secondes\n")
                f.write(f"Statut: {'Succès' if self.result.success else 'Échec'}\n")
                
                if self.result.error_message:
                    f.write(f"Erreur: {self.result.error_message}\n")
                
                f.write("\n=== STATISTIQUES ===\n")
                
                if hasattr(self.result, 'speakers_detected'):
                    f.write(f"Locuteurs détectés: {self.result.speakers_detected}\n")
                
                if hasattr(self.result, 'dialogue_segments'):
                    f.write(f"Segments de dialogue: {self.result.dialogue_segments}\n")
                
                if hasattr(self.result, 'quality_metrics') and self.result.quality_metrics:
                    f.write("\n=== MÉTRIQUES DE QUALITÉ ===\n")
                    for metric, value in self.result.quality_metrics.items():
                        f.write(f"{metric}: {value}\n")
    
    def _new_processing(self):
        """Démarre un nouveau traitement."""
        self.window.destroy()
        # La fenêtre principale reste ouverte pour un nouveau traitement