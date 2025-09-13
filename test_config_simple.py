#!/usr/bin/env python3
"""
Test simple de l'interface de configuration sans dépendances complexes.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SimplePipelineConfig:
    """Configuration simplifiée pour les tests."""
    enable_source_separation: bool = False
    enable_ocr: bool = False
    asr_model: str = "whisper-base"
    ocr_model: str = "paddleocr"
    voice_cloning_model: str = "tortoise-tts"
    target_language: str = "fr"
    output_codec: str = "h264"
    output_bitrate: str = "5M"
    temp_directory: str = ""
    max_memory_usage: float = 0.7

class SimpleConfigPanel:
    """Version simplifiée du panneau de configuration."""
    
    def __init__(self, parent, config, on_config_changed):
        self.parent = parent
        self.original_config = config
        self.on_config_changed = on_config_changed
        
        # Créer la fenêtre
        self.window = tk.Toplevel(parent)
        self.window.title("Configuration - AI Video Dubbing")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Variables de configuration
        self._create_variables()
        self._load_config(config)
        
        # Créer l'interface
        self._create_widgets()
        self._setup_layout()
        
        # Centrer la fenêtre
        self._center_window()
    
    def _create_variables(self):
        """Crée les variables tkinter pour la configuration."""
        self.enable_source_separation = tk.BooleanVar()
        self.enable_ocr = tk.BooleanVar()
        self.target_language = tk.StringVar()
        self.asr_model = tk.StringVar()
        self.ocr_model = tk.StringVar()
        self.voice_cloning_model = tk.StringVar()
        self.output_codec = tk.StringVar()
        self.output_bitrate = tk.StringVar()
        self.max_memory_usage = tk.DoubleVar()
        self.temp_directory = tk.StringVar()
    
    def _load_config(self, config):
        """Charge la configuration dans les variables."""
        self.enable_source_separation.set(config.enable_source_separation)
        self.enable_ocr.set(config.enable_ocr)
        self.target_language.set(config.target_language)
        self.asr_model.set(config.asr_model)
        self.ocr_model.set(config.ocr_model)
        self.voice_cloning_model.set(config.voice_cloning_model)
        self.output_codec.set(config.output_codec)
        self.output_bitrate.set(config.output_bitrate)
        self.max_memory_usage.set(config.max_memory_usage)
        self.temp_directory.set(config.temp_directory)
    
    def _create_widgets(self):
        """Crée tous les widgets du panneau."""
        # Frame principal
        self.main_frame = ttk.Frame(self.window, padding="20")
        
        # Titre
        self.title_label = ttk.Label(
            self.main_frame,
            text="⚙️ Configuration du Pipeline",
            font=("Arial", 16, "bold")
        )
        
        # Notebook pour organiser les options
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Onglet Général
        self._create_general_tab()
        
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
    
    def _create_general_tab(self):
        """Crée l'onglet des options générales."""
        self.general_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.general_frame, text="Général")
        
        # Options de traitement
        processing_group = ttk.LabelFrame(
            self.general_frame,
            text="Options de traitement",
            padding="10"
        )
        
        self.source_sep_check = ttk.Checkbutton(
            processing_group,
            text="Activer la séparation de source audio",
            variable=self.enable_source_separation
        )
        
        self.ocr_check = ttk.Checkbutton(
            processing_group,
            text="Activer l'extraction OCR des sous-titres",
            variable=self.enable_ocr
        )
        
        # Langue cible
        language_group = ttk.LabelFrame(
            self.general_frame,
            text="Langue",
            padding="10"
        )
        
        ttk.Label(language_group, text="Langue cible:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.language_combo = ttk.Combobox(
            language_group,
            textvariable=self.target_language,
            values=["fr", "en", "es", "de", "it", "pt"],
            state="readonly",
            width=10
        )
        
        # Layout de l'onglet général
        processing_group.pack(fill="x", pady=(0, 15))
        self.source_sep_check.pack(anchor="w")
        self.ocr_check.pack(anchor="w", pady=(10, 0))
        
        language_group.pack(fill="x")
        self.language_combo.grid(row=0, column=1, sticky="w")
    
    def _setup_layout(self):
        """Configure la disposition des widgets."""
        self.main_frame.pack(fill="both", expand=True)
        
        self.title_label.pack(pady=(0, 20))
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))
        
        self.buttons_frame.pack(fill="x")
        self.reset_button.pack(side="left")
        self.load_button.pack(side="left", padx=(5, 0))
        self.save_button.pack(side="left", padx=(5, 0))
        self.apply_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 0))
        self.ok_button.pack(side="right", padx=(5, 0))
    
    def _center_window(self):
        """Centre la fenêtre sur le parent."""
        self.window.update_idletasks()
        
        # Obtenir les dimensions
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        # Calculer la position relative au parent
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _get_current_config(self):
        """Retourne la configuration actuelle."""
        return SimplePipelineConfig(
            enable_source_separation=self.enable_source_separation.get(),
            enable_ocr=self.enable_ocr.get(),
            asr_model=self.asr_model.get(),
            ocr_model=self.ocr_model.get(),
            voice_cloning_model=self.voice_cloning_model.get(),
            target_language=self.target_language.get(),
            output_codec=self.output_codec.get(),
            output_bitrate=self.output_bitrate.get(),
            temp_directory=self.temp_directory.get(),
            max_memory_usage=self.max_memory_usage.get()
        )
    
    def _on_save_config(self):
        """Sauvegarde la configuration actuelle dans un fichier JSON."""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder la configuration",
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir=str(Path.home()),
            initialfile="config_doublage.json"
        )
        
        if filename:
            try:
                current_config = self._get_current_config()
                
                config_dict = {
                    "enable_source_separation": current_config.enable_source_separation,
                    "enable_ocr": current_config.enable_ocr,
                    "asr_model": current_config.asr_model,
                    "ocr_model": current_config.ocr_model,
                    "voice_cloning_model": current_config.voice_cloning_model,
                    "target_language": current_config.target_language,
                    "output_codec": current_config.output_codec,
                    "output_bitrate": current_config.output_bitrate,
                    "temp_directory": current_config.temp_directory,
                    "max_memory_usage": current_config.max_memory_usage
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Sauvegarde réussie", f"Configuration sauvegardée dans:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder:\n{str(e)}")
    
    def _on_load_config(self):
        """Charge une configuration depuis un fichier JSON."""
        filename = filedialog.askopenfilename(
            title="Charger une configuration",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir=str(Path.home())
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                loaded_config = SimplePipelineConfig(
                    enable_source_separation=config_dict.get("enable_source_separation", False),
                    enable_ocr=config_dict.get("enable_ocr", False),
                    asr_model=config_dict.get("asr_model", "whisper-base"),
                    ocr_model=config_dict.get("ocr_model", "paddleocr"),
                    voice_cloning_model=config_dict.get("voice_cloning_model", "tortoise-tts"),
                    target_language=config_dict.get("target_language", "fr"),
                    output_codec=config_dict.get("output_codec", "h264"),
                    output_bitrate=config_dict.get("output_bitrate", "5M"),
                    temp_directory=config_dict.get("temp_directory", ""),
                    max_memory_usage=config_dict.get("max_memory_usage", 0.7)
                )
                
                self._load_config(loaded_config)
                
                messagebox.showinfo("Chargement réussi", f"Configuration chargée depuis:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur de chargement", f"Impossible de charger:\n{str(e)}")
    
    def _on_reset(self):
        """Remet la configuration par défaut."""
        default_config = SimplePipelineConfig()
        self._load_config(default_config)
        messagebox.showinfo("Réinitialisation", "Configuration remise aux valeurs par défaut")
    
    def _on_apply(self):
        """Applique les changements de configuration."""
        new_config = self._get_current_config()
        self.on_config_changed(new_config)
        messagebox.showinfo("Application", "Configuration appliquée!")
    
    def _on_cancel(self):
        """Ferme la fenêtre sans appliquer les changements."""
        self.window.destroy()
    
    def _on_ok(self):
        """Applique les changements et ferme la fenêtre."""
        self._on_apply()
        self.window.destroy()

def main():
    """Lance directement l'interface de configuration Tkinter."""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    # Configuration par défaut
    config = SimplePipelineConfig()
    
    def on_config_changed(new_config):
        print("Configuration changée!")
        print(f"  - Séparation de source: {new_config.enable_source_separation}")
        print(f"  - OCR: {new_config.enable_ocr}")
        print(f"  - Langue: {new_config.target_language}")
    
    # Créer le panneau de configuration
    config_panel = SimpleConfigPanel(
        parent=root,
        config=config,
        on_config_changed=on_config_changed
    )
    
    print("Interface Tkinter lancée!")
    print("Vérifiez que les boutons suivants sont présents:")
    print("- Réinitialiser")
    print("- 📁 Charger")
    print("- 💾 Sauvegarder")
    print("- Appliquer")
    print("- Annuler")
    print("- OK")
    
    root.mainloop()

if __name__ == "__main__":
    main()