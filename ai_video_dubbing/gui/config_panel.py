"""
Panneau de configuration pour l'application de doublage vidéo par IA.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..models.data_models import PipelineConfig


class ConfigPanel:
    """Panneau de configuration des options du pipeline."""
    
    def __init__(self, parent: tk.Tk, config: PipelineConfig, on_config_changed: Callable[[PipelineConfig], None]):
        """
        Initialise le panneau de configuration.
        
        Args:
            parent: Fenêtre parente
            config: Configuration actuelle
            on_config_changed: Callback appelé quand la configuration change
        """
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
        # Options générales
        self.enable_source_separation = tk.BooleanVar()
        self.enable_ocr = tk.BooleanVar()
        self.target_language = tk.StringVar()
        
        # Modèles IA
        self.asr_model = tk.StringVar()
        self.ocr_model = tk.StringVar()
        self.voice_cloning_model = tk.StringVar()
        
        # Options de sortie
        self.output_codec = tk.StringVar()
        self.output_bitrate = tk.StringVar()
        
        # Options avancées
        self.max_memory_usage = tk.DoubleVar()
        self.temp_directory = tk.StringVar()
    
    def _load_config(self, config: PipelineConfig):
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
        # Frame principal avec scrollbar
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
        
        # Onglet Modèles IA
        self._create_models_tab()
        
        # Onglet Sortie
        self._create_output_tab()
        
        # Onglet Avancé
        self._create_advanced_tab()
        
        # Boutons
        self.buttons_frame = ttk.Frame(self.main_frame)
        
        self.ok_button = ttk.Button(
            self.buttons_frame,
            text="OK",
            command=self._on_ok
        )
        
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        
        self.apply_button = ttk.Button(
            self.buttons_frame,
            text="Appliquer",
            command=self._on_apply
        )
        
        self.reset_button = ttk.Button(
            self.buttons_frame,
            text="Réinitialiser",
            command=self._on_reset
        )
        
        self.save_button = ttk.Button(
            self.buttons_frame,
            text="💾 Sauvegarder",
            command=self._on_save_config
        )
        
        self.load_button = ttk.Button(
            self.buttons_frame,
            text="📁 Charger",
            command=self._on_load_config
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
        
        self.source_sep_info = ttk.Label(
            processing_group,
            text="Sépare la voix de la musique et des effets sonores",
            font=("Arial", 8),
            foreground="gray"
        )
        
        self.ocr_check = ttk.Checkbutton(
            processing_group,
            text="Activer l'extraction OCR des sous-titres",
            variable=self.enable_ocr
        )
        
        self.ocr_info = ttk.Label(
            processing_group,
            text="Extrait le texte des sous-titres incrustés dans la vidéo",
            font=("Arial", 8),
            foreground="gray"
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
        self.source_sep_info.pack(anchor="w", padx=(20, 0), pady=(0, 10))
        self.ocr_check.pack(anchor="w")
        self.ocr_info.pack(anchor="w", padx=(20, 0))
        
        language_group.pack(fill="x")
        self.language_combo.grid(row=0, column=1, sticky="w")
    
    def _create_models_tab(self):
        """Crée l'onglet des modèles IA."""
        self.models_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.models_frame, text="Modèles IA")
        
        # Modèles ASR
        asr_group = ttk.LabelFrame(
            self.models_frame,
            text="Reconnaissance vocale (ASR)",
            padding="10"
        )
        
        ttk.Label(asr_group, text="Modèle ASR:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Options ASR incluant NeMo et LM Studio
        asr_options = [
            "whisper-tiny",
            "whisper-base", 
            "whisper-small",
            "whisper-medium",
            "whisper-large-v3",
            "nemo-conformer-ctc-large-fr",
            "nemo-conformer-ctc-large-en",
            "nemo-fastconformer-multilingual",
            "lm-studio-whisper"
        ]
        
        self.asr_combo = ttk.Combobox(
            asr_group,
            textvariable=self.asr_model,
            values=asr_options,
            state="readonly",
            width=30
        )
        self.asr_combo.grid(row=0, column=1, sticky="w")
        
        # Bouton pour rafraîchir les modèles LM Studio
        self.refresh_lm_button = ttk.Button(
            asr_group,
            text="🔄 Actualiser LM Studio",
            command=self._refresh_lm_studio_models,
            width=20
        )
        self.refresh_lm_button.grid(row=0, column=2, sticky="w", padx=(10, 0))
        
        # Info ASR
        self.asr_info = ttk.Label(
            asr_group,
            text="Choisissez le modèle de reconnaissance vocale",
            font=("Arial", 8),
            foreground="gray"
        )
        self.asr_info.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))
        
        # Modèles OCR
        ocr_group = ttk.LabelFrame(
            self.models_frame,
            text="Reconnaissance optique (OCR)",
            padding="10"
        )
        
        ttk.Label(ocr_group, text="Modèle OCR:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Options OCR incluant NeMo et LM Studio
        ocr_options = [
            "paddleocr",
            "easyocr",
            "nemo-vision-transformer",
            "nemo-multimodal-llm",
            "lm-studio-vision"
        ]
        
        self.ocr_combo = ttk.Combobox(
            ocr_group,
            textvariable=self.ocr_model,
            values=ocr_options,
            state="readonly",
            width=30
        )
        self.ocr_combo.grid(row=0, column=1, sticky="w")
        
        # Info OCR
        self.ocr_info = ttk.Label(
            ocr_group,
            text="Choisissez le modèle d'extraction de texte",
            font=("Arial", 8),
            foreground="gray"
        )
        self.ocr_info.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        # Modèles de clonage vocal
        voice_group = ttk.LabelFrame(
            self.models_frame,
            text="Clonage vocal",
            padding="10"
        )
        
        ttk.Label(voice_group, text="Modèle de clonage:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.voice_combo = ttk.Combobox(
            voice_group,
            textvariable=self.voice_cloning_model,
            values=["tortoise-tts", "bark", "nemo-tts"],
            state="readonly",
            width=30
        )
        self.voice_combo.grid(row=0, column=1, sticky="w")
        
        # Info sur les modèles disponibles
        models_info_group = ttk.LabelFrame(
            self.models_frame,
            text="Informations sur les modèles",
            padding="10"
        )
        
        self.models_status_text = tk.Text(
            models_info_group,
            height=6,
            width=60,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        
        # Scrollbar pour le texte d'info
        models_scrollbar = ttk.Scrollbar(models_info_group, orient="vertical", command=self.models_status_text.yview)
        self.models_status_text.configure(yscrollcommand=models_scrollbar.set)
        
        # Bouton pour vérifier les modèles disponibles
        self.check_models_button = ttk.Button(
            models_info_group,
            text="🔍 Vérifier les modèles disponibles",
            command=self._check_available_models
        )
        
        # Layout de l'onglet modèles
        asr_group.pack(fill="x", pady=(0, 15))
        ocr_group.pack(fill="x", pady=(0, 15))
        voice_group.pack(fill="x", pady=(0, 15))
        models_info_group.pack(fill="both", expand=True)
        
        self.models_status_text.pack(side="left", fill="both", expand=True)
        models_scrollbar.pack(side="right", fill="y")
        self.check_models_button.pack(pady=(10, 0))
        
        # Charger les informations initiales sur les modèles
        self._update_models_info()
    
    def _create_output_tab(self):
        """Crée l'onglet des options de sortie."""
        self.output_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.output_frame, text="Sortie")
        
        # Codec vidéo
        codec_group = ttk.LabelFrame(
            self.output_frame,
            text="Encodage vidéo",
            padding="10"
        )
        
        ttk.Label(codec_group, text="Codec:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.codec_combo = ttk.Combobox(
            codec_group,
            textvariable=self.output_codec,
            values=["h264", "h265", "vp9", "av1"],
            state="readonly",
            width=15
        )
        self.codec_combo.grid(row=0, column=1, sticky="w")
        
        ttk.Label(codec_group, text="Débit:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        
        self.bitrate_combo = ttk.Combobox(
            codec_group,
            textvariable=self.output_bitrate,
            values=["2M", "5M", "8M", "10M", "15M", "20M"],
            state="readonly",
            width=15
        )
        self.bitrate_combo.grid(row=1, column=1, sticky="w", pady=(10, 0))
        
        codec_group.pack(fill="x")
    
    def _create_advanced_tab(self):
        """Crée l'onglet des options avancées."""
        self.advanced_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.advanced_frame, text="Avancé")
        
        # Gestion mémoire
        memory_group = ttk.LabelFrame(
            self.advanced_frame,
            text="Gestion mémoire",
            padding="10"
        )
        
        ttk.Label(memory_group, text="Utilisation mémoire max:").grid(row=0, column=0, sticky="w")
        
        self.memory_scale = ttk.Scale(
            memory_group,
            from_=0.3,
            to=0.9,
            variable=self.max_memory_usage,
            orient="horizontal",
            length=200
        )
        self.memory_scale.grid(row=0, column=1, padx=(10, 0))
        
        self.memory_label = ttk.Label(memory_group, text="")
        self.memory_label.grid(row=0, column=2, padx=(10, 0))
        
        # Mettre à jour le label de mémoire
        def update_memory_label(*args):
            value = self.max_memory_usage.get()
            self.memory_label.config(text=f"{value:.0%}")
        
        self.max_memory_usage.trace("w", update_memory_label)
        update_memory_label()  # Initialiser
        
        # Répertoire temporaire
        temp_group = ttk.LabelFrame(
            self.advanced_frame,
            text="Fichiers temporaires",
            padding="10"
        )
        
        ttk.Label(temp_group, text="Répertoire:").pack(anchor="w")
        
        temp_frame = ttk.Frame(temp_group)
        temp_frame.pack(fill="x", pady=(5, 0))
        
        self.temp_entry = ttk.Entry(
            temp_frame,
            textvariable=self.temp_directory,
            width=40
        )
        self.temp_entry.pack(side="left", fill="x", expand=True)
        
        self.temp_browse_button = ttk.Button(
            temp_frame,
            text="...",
            width=3,
            command=self._browse_temp_directory
        )
        self.temp_browse_button.pack(side="right", padx=(5, 0))
        
        # Layout de l'onglet avancé
        memory_group.pack(fill="x", pady=(0, 15))
        temp_group.pack(fill="x")
    
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
    
    def _browse_temp_directory(self):
        """Ouvre le dialogue de sélection de répertoire temporaire."""
        from tkinter import filedialog
        
        directory = filedialog.askdirectory(
            title="Sélectionner le répertoire temporaire",
            initialdir=self.temp_directory.get()
        )
        
        if directory:
            self.temp_directory.set(directory)
    
    def _get_current_config(self) -> PipelineConfig:
        """Retourne la configuration actuelle."""
        return PipelineConfig(
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
    
    def _on_ok(self):
        """Applique les changements et ferme la fenêtre."""
        self._on_apply()
        self.window.destroy()
    
    def _on_cancel(self):
        """Ferme la fenêtre sans appliquer les changements."""
        self.window.destroy()
    
    def _on_apply(self):
        """Applique les changements de configuration."""
        new_config = self._get_current_config()
        self.on_config_changed(new_config)
    
    def _on_reset(self):
        """Remet la configuration par défaut."""
        default_config = PipelineConfig()
        self._load_config(default_config)
    
    def _on_save_config(self):
        """Sauvegarde la configuration actuelle dans un fichier JSON."""
        from tkinter import filedialog, messagebox
        import json
        from pathlib import Path
        
        # Demander où sauvegarder
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder la configuration",
            defaultextension=".json",
            filetypes=[
                ("Fichiers JSON", "*.json"),
                ("Tous les fichiers", "*.*")
            ],
            initialdir=str(Path.home()),
            initialfile="config_doublage.json"
        )
        
        if filename:
            try:
                # Obtenir la configuration actuelle
                current_config = self._get_current_config()
                
                # Convertir en dictionnaire pour la sérialisation JSON
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
                
                # Sauvegarder dans le fichier
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo(
                    "Sauvegarde réussie",
                    f"Configuration sauvegardée dans:\n{filename}"
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Erreur de sauvegarde",
                    f"Impossible de sauvegarder la configuration:\n{str(e)}"
                )
    
    def _on_load_config(self):
        """Charge une configuration depuis un fichier JSON."""
        from tkinter import filedialog, messagebox
        import json
        from pathlib import Path
        
        # Demander quel fichier charger
        filename = filedialog.askopenfilename(
            title="Charger une configuration",
            filetypes=[
                ("Fichiers JSON", "*.json"),
                ("Tous les fichiers", "*.*")
            ],
            initialdir=str(Path.home())
        )
        
        if filename:
            try:
                # Charger le fichier JSON
                with open(filename, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                
                # Créer un objet PipelineConfig avec les valeurs chargées
                loaded_config = PipelineConfig(
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
                
                # Charger la configuration dans l'interface
                self._load_config(loaded_config)
                
                messagebox.showinfo(
                    "Chargement réussi",
                    f"Configuration chargée depuis:\n{filename}"
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Erreur de chargement",
                    f"Impossible de charger la configuration:\n{str(e)}"
                )  
  
    def _refresh_lm_studio_models(self):
        """Actualise la liste des modèles LM Studio disponibles."""
        try:
            # Importer le gestionnaire LM Studio
            from ..processors.lm_studio_manager import LMStudioManager
            
            lm_manager = LMStudioManager()
            
            if not lm_manager.is_available():
                self._show_info_message("LM Studio n'est pas disponible ou n'est pas en cours d'exécution.")
                return
            
            # Obtenir les modèles disponibles
            available_models = lm_manager.get_available_models()
            
            if not available_models:
                self._show_info_message("Aucun modèle trouvé dans LM Studio.")
                return
            
            # Mettre à jour les listes déroulantes avec les modèles LM Studio
            current_asr_values = list(self.asr_combo['values'])
            current_ocr_values = list(self.ocr_combo['values'])
            
            # Supprimer les anciens modèles LM Studio
            current_asr_values = [v for v in current_asr_values if not v.startswith('lm-studio-')]
            current_ocr_values = [v for v in current_ocr_values if not v.startswith('lm-studio-')]
            
            # Ajouter les nouveaux modèles
            transcription_models = lm_manager.get_models_for_transcription()
            ocr_models = lm_manager.get_models_for_ocr()
            
            for model in transcription_models:
                model_name = f"lm-studio-{model['name']}"
                if model_name not in current_asr_values:
                    current_asr_values.append(model_name)
            
            for model in ocr_models:
                model_name = f"lm-studio-{model['name']}"
                if model_name not in current_ocr_values:
                    current_ocr_values.append(model_name)
            
            # Mettre à jour les combobox
            self.asr_combo['values'] = current_asr_values
            self.ocr_combo['values'] = current_ocr_values
            
            self._show_info_message(
                f"Modèles LM Studio actualisés:\n"
                f"- {len(transcription_models)} modèles de transcription\n"
                f"- {len(ocr_models)} modèles OCR/Vision"
            )
            
        except Exception as e:
            self._show_info_message(f"Erreur lors de l'actualisation LM Studio: {e}")
    
    def _check_available_models(self):
        """Vérifie et affiche les modèles disponibles."""
        try:
            # Importer le gestionnaire de modèles IA
            from ..processors.ai_model_manager import AIModelManager
            
            ai_manager = AIModelManager()
            models_summary = ai_manager.get_available_models_summary()
            
            # Construire le texte d'information
            info_lines = []
            info_lines.append("=== MODÈLES DISPONIBLES ===\n")
            
            # Modèles locaux
            local_models = models_summary.get("local_models", {})
            info_lines.append("📁 MODÈLES LOCAUX:")
            info_lines.append(f"  ASR: {len(local_models.get('asr', []))} modèles")
            info_lines.append(f"  OCR: {len(local_models.get('ocr', []))} modèles")
            info_lines.append(f"  Clonage vocal: {len(local_models.get('voice_cloning', []))} modèles")
            info_lines.append("")
            
            # Modèles LM Studio
            lm_models = models_summary.get("lm_studio_models", {})
            if lm_models.get("available", False):
                info_lines.append("🤖 LM STUDIO:")
                info_lines.append(f"  Total: {lm_models.get('total_models', 0)} modèles")
                info_lines.append(f"  Transcription: {lm_models.get('transcription_models', 0)} modèles")
                info_lines.append(f"  OCR: {lm_models.get('ocr_models', 0)} modèles")
            else:
                info_lines.append("🤖 LM STUDIO: Non disponible")
            info_lines.append("")
            
            # Modèles NeMo
            nemo_models = models_summary.get("nemo_models", {})
            if nemo_models.get("available", False):
                info_lines.append("🚀 NVIDIA NEMO:")
                info_lines.append(f"  ASR: {len(nemo_models.get('asr_models', []))} modèles")
                info_lines.append(f"  OCR: {len(nemo_models.get('ocr_models', []))} modèles")
            else:
                info_lines.append("🚀 NVIDIA NEMO: Non installé")
            info_lines.append("")
            
            # Découverte de modèles
            discovery = models_summary.get("discovery_summary", {})
            if discovery:
                info_lines.append("🔍 DÉCOUVERTE AUTOMATIQUE:")
                info_lines.append(f"  Total découvert: {discovery.get('total_models', 0)} modèles")
                info_lines.append(f"  Disponibles: {discovery.get('available_models', 0)} modèles")
            
            # Afficher dans le widget de texte
            self._update_models_status_text("\n".join(info_lines))
            
        except Exception as e:
            self._update_models_status_text(f"Erreur lors de la vérification des modèles: {e}")
    
    def _update_models_info(self):
        """Met à jour les informations sur les modèles au chargement."""
        info_text = """Informations sur les modèles:

🎤 MODÈLES ASR (Reconnaissance vocale):
• Whisper: Modèles OpenAI (tiny à large-v3)
• NeMo: Modèles NVIDIA haute performance
• LM Studio: Modèles locaux personnalisés

👁️ MODÈLES OCR (Reconnaissance optique):
• PaddleOCR: Rapide et efficace
• EasyOCR: Bonne précision multilingue
• NeMo Vision: Modèles avancés NVIDIA
• LM Studio: Modèles vision locaux

🔄 Cliquez sur "Actualiser LM Studio" pour détecter les modèles disponibles
🔍 Cliquez sur "Vérifier les modèles" pour voir le statut détaillé"""
        
        self._update_models_status_text(info_text)
    
    def _update_models_status_text(self, text: str):
        """Met à jour le texte d'information sur les modèles."""
        self.models_status_text.config(state=tk.NORMAL)
        self.models_status_text.delete(1.0, tk.END)
        self.models_status_text.insert(1.0, text)
        self.models_status_text.config(state=tk.DISABLED)
    
    def _show_info_message(self, message: str):
        """Affiche un message d'information dans une popup."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Information", message)