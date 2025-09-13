#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application de doublage vidéo par IA.
"""

import sys
import argparse
import logging
from pathlib import Path

# Patch pour NeMo sur Windows AVANT tout import
import signal
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from ai_video_dubbing.models.data_models import PipelineConfig


def main():
    """Point d'entrée principal de l'application."""
    parser = argparse.ArgumentParser(
        description="Application de Doublage Vidéo par IA - Version Optimisée"
    )
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Lancer l'interface graphique améliorée"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        help="Fichier vidéo d'entrée (mode CLI)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Fichier vidéo de sortie (mode CLI)"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Fichier de configuration JSON"
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "balanced", "quality", "adaptive"],
        default="balanced",
        help="Mode de transcription (fast/balanced/quality/adaptive)"
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Désactiver les fallbacks automatiques"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Désactiver le cache"
    )
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Lancer le diagnostic système"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux avec métriques détaillées"
    )
    
    args = parser.parse_args()
    
    # Mode diagnostic
    if args.diagnostic:
        launch_diagnostic()
        return
    
    if args.gui or (not args.input and not args.output):
        # Lancer l'interface graphique
        launch_gui()
    else:
        # Mode ligne de commande
        if not args.input or not args.output:
            print("Erreur: --input et --output sont requis en mode CLI")
            sys.exit(1)
        
        launch_cli(args.input, args.output, args.config, args)


def launch_gui():
    """Lance l'interface graphique PyQt5 améliorée."""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # Essayer d'abord l'interface améliorée
        try:
            from ai_video_dubbing.gui.enhanced_main_window import EnhancedMainWindow
            enhanced_gui = True
        except ImportError as e:
            print(f"Interface améliorée non disponible ({e}), utilisation de l'interface standard...")
            enhanced_gui = False
        
        # Créer l'application PyQt5
        app = QApplication(sys.argv)
        
        # Configuration de l'application
        app.setApplicationName("AI Video Dubbing")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("AI Video Dubbing")
        
        # Activer le support des notifications système
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Créer et afficher la fenêtre principale
        if enhanced_gui:
            print("Lancement de l'interface graphique améliorée...")
            window = EnhancedMainWindow()
        else:
            # Essayer l'interface standard, sinon l'interface légère
            try:
                print("Lancement de l'interface graphique standard...")
                from ai_video_dubbing.gui.main_window_qt import MainWindowQt
                window = MainWindowQt()
            except ImportError:
                print("Interface standard non disponible, utilisation de l'interface légère...")
                from ai_video_dubbing.gui.lightweight_main_window import LightweightMainWindow
                window = LightweightMainWindow()
        
        window.show()
        
        # Lancer la boucle d'événements
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"Erreur: Impossible de charger l'interface graphique: {e}")
        print("Assurez-vous que PyQt5 est installé:")
        print("pip install PyQt5")
        sys.exit(1)


def launch_diagnostic():
    """Lance le diagnostic système simplifié."""
    try:
        import psutil
        import platform
        
        print("Lancement du diagnostic système...")
        
        # Diagnostic système de base
        print("\nInformations système:")
        print(f"  Système: {platform.system()} {platform.release()}")
        print(f"  Python: {platform.python_version()}")
        
        # Diagnostic mémoire
        memory = psutil.virtual_memory()
        print(f"  Mémoire: {memory.available / (1024**3):.1f}GB disponible / {memory.total / (1024**3):.1f}GB total")
        
        # Diagnostic CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"  CPU: {psutil.cpu_count()} cœurs, utilisation: {cpu_percent:.1f}%")
        
        # Diagnostic GPU (si disponible)
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Inconnu"
                print(f"  GPU: {gpu_count} GPU(s) CUDA disponible(s) - {gpu_name}")
            else:
                print("  GPU: Aucun GPU CUDA disponible")
        except ImportError:
            print("  GPU: PyTorch non installé, impossible de vérifier CUDA")
        
        # Diagnostic des composants de performance
        print("\nComposants de performance:")
        
        components_to_check = [
            ("EnhancedAIModelManager", "ai_video_dubbing.processors.enhanced_ai_model_manager"),
            ("AsyncController", "ai_video_dubbing.performance.async_controller"),
            ("FallbackSystem", "ai_video_dubbing.performance.fallback_system"),
            ("CacheManager", "ai_video_dubbing.performance.cache_manager"),
            ("DownloadManager", "ai_video_dubbing.performance.download_manager"),
        ]
        
        for component_name, module_path in components_to_check:
            try:
                __import__(module_path)
                print(f"  [OK] {component_name}: Disponible")
            except ImportError as e:
                print(f"  [ERREUR] {component_name}: Non disponible ({e})")
            except Exception as e:
                print(f"  [ATTENTION] {component_name}: Erreur ({e})")
        
        print("\nDiagnostic terminé!")
        
    except Exception as e:
        print(f"Erreur lors du diagnostic: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def launch_cli(input_file: str, output_file: str, config_file: str = None, args=None):
    """Lance le traitement en mode ligne de commande avec optimisations."""
    try:
        # Essayer d'importer les composants optimisés
        try:
            from ai_video_dubbing.processors.enhanced_ai_model_manager import EnhancedAIModelManager, TranscriptionConfig, TranscriptionMode
            enhanced_mode = True
        except ImportError as e:
            print(f"Mode optimisé non disponible ({e}), utilisation du mode léger...")
            from ai_video_dubbing.performance.lightweight_fallbacks import get_lightweight_ai_manager
            enhanced_mode = False
        
        from ai_video_dubbing.pipeline.orchestrator import PipelineOrchestrator
        import json
        import asyncio
        
        # Charger la configuration
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            config = PipelineConfig(**config_data)
        else:
            config = PipelineConfig()
        
        # Initialiser le gestionnaire AI (optimisé ou léger)
        if enhanced_mode:
            print("Initialisation du gestionnaire AI amélioré...")
            ai_manager = EnhancedAIModelManager()
            
            # Configuration de transcription basée sur les arguments
            mode_mapping = {
                "fast": TranscriptionMode.FAST,
                "balanced": TranscriptionMode.BALANCED,
                "quality": TranscriptionMode.QUALITY,
                "adaptive": TranscriptionMode.ADAPTIVE
            }
            
            transcription_config = TranscriptionConfig(
                mode=mode_mapping.get(args.mode if args else "balanced", TranscriptionMode.BALANCED),
                enable_fallback=not (args.no_fallback if args else False),
                enable_caching=not (args.no_cache if args else False),
                timeout=600  # 10 minutes max
            )
        else:
            print("Initialisation du gestionnaire AI léger...")
            ai_manager = get_lightweight_ai_manager()
            transcription_config = {
                "mode": args.mode if args else "balanced",
                "enable_fallback": not (args.no_fallback if args else False),
                "enable_caching": not (args.no_cache if args else False)
            }
        
        if args and args.verbose:
            print(f"Configuration de transcription:")
            if enhanced_mode:
                print(f"- Mode: {transcription_config.mode.value}")
                print(f"- Fallback activé: {transcription_config.enable_fallback}")
                print(f"- Cache activé: {transcription_config.enable_caching}")
            else:
                print(f"- Mode: {transcription_config['mode']}")
                print(f"- Fallback activé: {transcription_config['enable_fallback']}")
                print(f"- Cache activé: {transcription_config['enable_caching']}")
            print(f"- Mode optimisé: {enhanced_mode}")
        
        # Créer et exécuter le pipeline avec le gestionnaire amélioré
        orchestrator = PipelineOrchestrator(config, ai_manager=ai_manager)
        
        def progress_callback(progress_info):
            print(f"[{progress_info.progress_percentage:.1f}%] {progress_info.current_phase}: {progress_info.current_step}")
        
        orchestrator.register_progress_callback(progress_callback)
        
        print(f"Traitement de {input_file} avec optimisations de performance...")
        
        # Exécuter le pipeline de manière asynchrone si possible
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = orchestrator.execute_pipeline(input_file, transcription_config=transcription_config)
        
        print(f"Traitement terminé avec succès!")
        print(f"Fichier de sortie: {results.output_video_path}")
        print(f"Temps de traitement: {results.processing_time:.2f}s")
        print(f"Locuteurs détectés: {results.speakers_detected}")
        print(f"Segments de dialogue: {results.dialogue_segments}")
        
        # Afficher les métriques de performance si disponibles
        if hasattr(ai_manager, 'performance_metrics'):
            metrics = ai_manager.performance_metrics
            print(f"\nMétriques de performance:")
            print(f"- Transcriptions réussies: {metrics.get('successful_transcriptions', 0)}")
            print(f"- Utilisation du cache: {metrics.get('cache_hits', 0)} hits")
            print(f"- Fallbacks utilisés: {metrics.get('fallback_usage', 0)}")
        
    except Exception as e:
        print(f"Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()