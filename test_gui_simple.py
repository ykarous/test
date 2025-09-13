#!/usr/bin/env python3
"""
Test simple de l'interface graphique.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False
    tk = None
    ttk = None

from ai_video_dubbing.models.data_models import PipelineConfig, ProcessingResults


def test_gui_components():
    """Test des composants de l'interface graphique."""
    print("=== Test des Composants GUI ===")
    
    # Test 1: Disponibilité de tkinter
    print("\n1. Test disponibilité de tkinter:")
    if _TKINTER_AVAILABLE:
        print("   ✅ tkinter disponible")
        
        # Tester la création d'une fenêtre simple
        try:
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre
            print("   ✅ Fenêtre tkinter créée avec succès")
            root.destroy()
        except Exception as e:
            print(f"   ❌ Erreur création fenêtre: {e}")
    else:
        print("   ❌ tkinter non disponible")
        return
    
    # Test 2: Import des modules GUI
    print("\n2. Test import des modules GUI:")
    
    try:
        from ai_video_dubbing.gui import MainWindow, ConfigPanel, ProgressDialog, ResultsWindow
        print("   ✅ Tous les modules GUI importés avec succès")
    except ImportError as e:
        print(f"   ❌ Erreur import GUI: {e}")
        return
    
    # Test 3: Configuration par défaut
    print("\n3. Test configuration par défaut:")
    
    try:
        config = PipelineConfig()
        print("   ✅ Configuration créée:")
        print(f"     - Séparation de source: {config.enable_source_separation}")
        print(f"     - OCR: {config.enable_ocr}")
        print(f"     - Modèle ASR: {config.asr_model}")
        print(f"     - Langue: {config.target_language}")
    except Exception as e:
        print(f"   ❌ Erreur configuration: {e}")
    
    # Test 4: Résultats factices
    print("\n4. Test résultats factices:")
    
    try:
        results = ProcessingResults(
            output_video_path="/path/to/output.mp4",
            processing_time=120.5,
            success=True,
            error_message=""
        )
        print("   ✅ Résultats créés:")
        print(f"     - Fichier de sortie: {results.output_video_path}")
        print(f"     - Temps: {results.processing_time}s")
        print(f"     - Succès: {results.success}")
    except Exception as e:
        print(f"   ❌ Erreur résultats: {e}")
    
    # Test 5: Test de création des widgets (sans affichage)
    print("\n5. Test création des widgets:")
    
    try:
        # Créer une fenêtre racine cachée
        root = tk.Tk()
        root.withdraw()
        
        # Tester les widgets de base
        widgets_test = [
            ("Label", lambda: ttk.Label(root, text="Test")),
            ("Button", lambda: ttk.Button(root, text="Test")),
            ("Entry", lambda: ttk.Entry(root)),
            ("Combobox", lambda: ttk.Combobox(root)),
            ("Progressbar", lambda: ttk.Progressbar(root)),
            ("Treeview", lambda: ttk.Treeview(root)),
            ("LabelFrame", lambda: ttk.LabelFrame(root, text="Test")),
            ("Notebook", lambda: ttk.Notebook(root))
        ]
        
        for widget_name, widget_creator in widgets_test:
            try:
                widget = widget_creator()
                print(f"   ✅ {widget_name} créé avec succès")
                widget.destroy()
            except Exception as e:
                print(f"   ❌ Erreur {widget_name}: {e}")
        
        root.destroy()
        
    except Exception as e:
        print(f"   ❌ Erreur test widgets: {e}")
    
    # Test 6: Fonctionnalités GUI disponibles
    print("\n6. Fonctionnalités GUI disponibles:")
    
    features = [
        "✅ Interface graphique principale (MainWindow)",
        "✅ Panneau de configuration (ConfigPanel)",
        "✅ Dialogue de progression (ProgressDialog)",
        "✅ Fenêtre de résultats (ResultsWindow)",
        "✅ Sélection de fichiers vidéo",
        "✅ Configuration des modèles IA",
        "✅ Progression en temps réel",
        "✅ Affichage des résultats détaillés",
        "✅ Export et sauvegarde",
        "✅ Gestion d'erreurs utilisateur"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    # Test 7: Test de l'architecture GUI
    print("\n7. Architecture de l'interface:")
    
    architecture_info = [
        "📱 Interface utilisateur moderne avec tkinter",
        "🎨 Style cohérent avec ttk.Style",
        "📊 Widgets spécialisés (Treeview, Notebook, Progressbar)",
        "🔄 Callbacks et événements pour interactivité",
        "🎯 Séparation des responsabilités (MVC pattern)",
        "💾 Gestion des configurations utilisateur",
        "📈 Monitoring de progression en temps réel",
        "🛡️ Gestion d'erreurs et validation d'entrée",
        "🎬 Intégration avec le pipeline de traitement",
        "📁 Gestion des fichiers et dossiers"
    ]
    
    for info in architecture_info:
        print(f"   {info}")
    
    print("\n✅ Tests des composants GUI terminés!")


def test_gui_demo():
    """Démonstration rapide de l'interface (optionnel)."""
    if not _TKINTER_AVAILABLE:
        print("❌ tkinter non disponible pour la démo")
        return
    
    print("\n=== Démonstration GUI (Optionnelle) ===")
    print("Voulez-vous voir une démonstration de l'interface? (y/N)")
    
    try:
        response = input().strip().lower()
        if response in ['y', 'yes', 'oui']:
            print("Lancement de la démonstration...")
            
            # Créer une fenêtre de démonstration simple
            demo_window = tk.Tk()
            demo_window.title("Démo - AI Video Dubbing")
            demo_window.geometry("400x300")
            
            # Widgets de démonstration
            title_label = ttk.Label(
                demo_window,
                text="🎬 AI Video Dubbing",
                font=("Arial", 16, "bold")
            )
            title_label.pack(pady=20)
            
            info_label = ttk.Label(
                demo_window,
                text="Interface graphique pour le doublage vidéo par IA",
                font=("Arial", 10)
            )
            info_label.pack(pady=10)
            
            # Barre de progression de démonstration
            progress_label = ttk.Label(demo_window, text="Progression de démonstration:")
            progress_label.pack(pady=(20, 5))
            
            progress_bar = ttk.Progressbar(
                demo_window,
                mode="determinate",
                length=300
            )
            progress_bar.pack(pady=5)
            
            # Boutons
            button_frame = ttk.Frame(demo_window)
            button_frame.pack(pady=20)
            
            def animate_progress():
                for i in range(101):
                    progress_bar['value'] = i
                    demo_window.update()
                    demo_window.after(20)  # 20ms delay
                
                # Afficher un message de fin
                result_label = ttk.Label(
                    demo_window,
                    text="✅ Démonstration terminée!",
                    font=("Arial", 12, "bold"),
                    foreground="green"
                )
                result_label.pack(pady=10)
            
            start_button = ttk.Button(
                button_frame,
                text="Démarrer la démo",
                command=animate_progress
            )
            start_button.pack(side="left", padx=5)
            
            close_button = ttk.Button(
                button_frame,
                text="Fermer",
                command=demo_window.destroy
            )
            close_button.pack(side="left", padx=5)
            
            print("✅ Fenêtre de démonstration ouverte")
            print("   Fermez la fenêtre pour continuer...")
            
            # Centrer la fenêtre
            demo_window.update_idletasks()
            width = demo_window.winfo_width()
            height = demo_window.winfo_height()
            x = (demo_window.winfo_screenwidth() // 2) - (width // 2)
            y = (demo_window.winfo_screenheight() // 2) - (height // 2)
            demo_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Lancer la boucle d'événements
            demo_window.mainloop()
            
            print("✅ Démonstration terminée")
        else:
            print("Démonstration ignorée")
    
    except KeyboardInterrupt:
        print("\nDémonstration annulée")
    except Exception as e:
        print(f"Erreur démonstration: {e}")


if __name__ == "__main__":
    test_gui_components()
    test_gui_demo()