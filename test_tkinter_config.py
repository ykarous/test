#!/usr/bin/env python3
"""
Test direct de l'interface de configuration Tkinter.
"""
import sys
import tkinter as tk
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ai_video_dubbing.models.data_models import PipelineConfig
    from ai_video_dubbing.gui.config_panel import ConfigPanel
    
    def main():
        """Lance directement l'interface de configuration Tkinter."""
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale
        
        # Configuration par défaut
        config = PipelineConfig()
        
        def on_config_changed(new_config):
            print("Configuration changée!")
            print(f"  - Séparation de source: {new_config.enable_source_separation}")
            print(f"  - OCR: {new_config.enable_ocr}")
            print(f"  - Modèle ASR: {new_config.asr_model}")
            print(f"  - Langue: {new_config.target_language}")
        
        # Créer le panneau de configuration
        config_panel = ConfigPanel(
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
        
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Vérifiez que tous les modules sont disponibles.")
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()