#!/usr/bin/env python3
"""
Test simple du panneau de configuration sans dépendances complexes.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path

class SimpleConfigPanel:
    """Version simplifiée du panneau de configuration pour test."""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Test Configuration - AI Video Dubbing")
        self.window.geometry("600x400")
        
        # Variables de test
        self.enable_source_separation = tk.BooleanVar()
        self.enable_ocr = tk.BooleanVar()
        self.target_language = tk.StringVar(value="fr")
        self.asr_model = tk.StringVar(value="whisper-base")
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Crée les widgets de test."""
        # Frame principal
        self.main_frame = ttk.Frame(self.window, padding="20")
        
        # Titre
        self.title_label = ttk.Label(
            self.main_frame,
            text="⚙️ Test Configuration du Pipeline",
            font=("Arial", 16, "bold")
        )
        
        # Options de test
        self.options_frame = ttk.LabelFrame(
            self.main_frame,
            text="Options de test",
            padding="15"
        )
        
        self.source_sep_check = ttk.Checkbutton(
            self.options_frame,
            text="Activer la séparation de source audio",
            variable=self.enable_source_separation
        )
        
        self.ocr_check = ttk.Checkbutton(
            self.options_frame,
            text="Activer l'extraction OCR des sous-titres",
            variable=self.enable_ocr
        )
        
        ttk.Label(self.options_frame, text="Langue cible:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        
        self.language_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.target_language,
            values=["fr", "en", "es", "de", "it", "pt"],
            state="readonly",
            width=10
        )
        self.language_combo.grid(row=2, column=1, sticky="w", pady=(10, 0), padx=(10, 0))
        
        # Boutons
        self.buttons_frame = ttk.Frame(self.main_frame)
        
        self.reset_button = ttk.Button(
            self.buttons_frame,
            text="Réinitialiser",
            command=self._on_reset
        )
        
        self.load_button = ttk.Button(
            self.buttons_frame,
            text="📁 Charger",
            command=self._on_load_config
        )
        
        self.save_button = ttk.Button(
            self.buttons_frame,
            text="💾 Sauvegarder",
            command=self._on_save_config
        )
        
        self.apply_button = ttk.Button(
            self.buttons_frame,
            text="Appliquer",
            command=self._on_apply
        )
        
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        
        self.ok_button = ttk.Button(
            self.buttons_frame,
            text="OK",
            command=self._on_ok
        )
    
    def _setup_layout(self):
        """Configure la disposition des widgets."""
        self.main_frame.pack(fill="both", expand=True)
        
        self.title_label.pack(pady=(0, 20))
        
        self.options_frame.pack(fill="x", pady=(0, 20))
        self.source_sep_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.ocr_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        self.buttons_frame.pack(fill="x")
        self.reset_button.pack(side="left")
        self.load_button.pack(side="left", padx=(5, 0))
        self.save_button.pack(side="left", padx=(5, 0))
        self.apply_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 0))
        self.ok_button.pack(side="right", padx=(5, 0))
    
    def _on_save_config(self):
        """Sauvegarde la configuration de test."""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder la configuration",
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir=str(Path.home()),
            initialfile="config_test.json"
        )
        
        if filename:
            try:
                config_dict = {
                    "enable_source_separation": self.enable_source_separation.get(),
                    "enable_ocr": self.enable_ocr.get(),
                    "target_language": self.target_language.get(),
                    "asr_model": self.asr_model.get()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Sauvegarde réussie", f"Configuration sauvegardée dans:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder:\n{str(e)}")
    
    def _on_load_config(self):
        """Charge une configuration de test."""
        filename = filedialog.askopenfilename(
            title="Charger une configuration",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir=str(Path.home())
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                self.enable_source_separation.set(config_dict.get("enable_source_separation", False))
                self.enable_ocr.set(config_dict.get("enable_ocr", False))
                self.target_language.set(config_dict.get("target_language", "fr"))
                self.asr_model.set(config_dict.get("asr_model", "whisper-base"))
                
                messagebox.showinfo("Chargement réussi", f"Configuration chargée depuis:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur de chargement", f"Impossible de charger:\n{str(e)}")
    
    def _on_reset(self):
        """Remet les valeurs par défaut."""
        self.enable_source_separation.set(False)
        self.enable_ocr.set(False)
        self.target_language.set("fr")
        self.asr_model.set("whisper-base")
        messagebox.showinfo("Réinitialisation", "Configuration remise aux valeurs par défaut")
    
    def _on_apply(self):
        """Applique les changements."""
        messagebox.showinfo("Application", "Changements appliqués (test)")
    
    def _on_cancel(self):
        """Annule et ferme."""
        self.window.destroy()
    
    def _on_ok(self):
        """Applique et ferme."""
        self._on_apply()
        self.window.destroy()
    
    def run(self):
        """Lance l'interface de test."""
        print("Interface de test lancée.")
        print("Vérifiez que tous les boutons sont visibles:")
        print("- Réinitialiser (à gauche)")
        print("- 📁 Charger (à gauche)")
        print("- 💾 Sauvegarder (à gauche)")
        print("- Appliquer (à droite)")
        print("- Annuler (à droite)")
        print("- OK (à droite)")
        self.window.mainloop()

if __name__ == "__main__":
    app = SimpleConfigPanel()
    app.run()