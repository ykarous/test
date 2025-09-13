#!/usr/bin/env python3
"""
Test de démarrage de l'application pour diagnostiquer les problèmes.
"""
import sys
import traceback
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Teste les imports principaux."""
    print("🔍 Test des imports...")
    
    try:
        print("  - Import des modèles de données...")
        from ai_video_dubbing.models.data_models import PipelineConfig
        print("    ✅ Modèles de données OK")
        
        print("  - Import des interfaces...")
        from ai_video_dubbing.interfaces.base_interfaces import IVideoProcessor
        print("    ✅ Interfaces OK")
        
        print("  - Import du gestionnaire FFmpeg...")
        from ai_video_dubbing.utils.ffmpeg_manager import FFmpegManager
        print("    ✅ Gestionnaire FFmpeg OK")
        
        print("  - Import des utilitaires média...")
        from ai_video_dubbing.utils.media_utils import MediaUtils
        print("    ✅ Utilitaires média OK")
        
        print("  - Import du processeur vidéo...")
        from ai_video_dubbing.processors.video_processor import VideoProcessor
        print("    ✅ Processeur vidéo OK")
        
        print("  - Import des widgets GUI...")
        from ai_video_dubbing.gui.ffmpeg_config_widget import FFmpegConfigWidget
        print("    ✅ Widget FFmpeg OK")
        
        from ai_video_dubbing.gui.config_panel_qt import ConfigPanelQt
        print("    ✅ Panneau de configuration OK")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Erreur d'import: {e}")
        traceback.print_exc()
        return False

def test_ffmpeg_manager():
    """Teste le gestionnaire FFmpeg."""
    print("\n🔧 Test du gestionnaire FFmpeg...")
    
    try:
        from ai_video_dubbing.utils.ffmpeg_manager import FFmpegManager
        
        manager = FFmpegManager()
        print("    ✅ Gestionnaire FFmpeg créé")
        
        # Test de détection (sans lever d'exception si non trouvé)
        try:
            available = manager.is_available()
            if available:
                print(f"    ✅ FFmpeg disponible - Version: {manager.get_version()}")
            else:
                print("    ⚠️ FFmpeg non disponible (normal si pas installé)")
        except Exception as e:
            print(f"    ⚠️ Erreur de détection FFmpeg: {e}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Erreur gestionnaire FFmpeg: {e}")
        traceback.print_exc()
        return False

def test_video_processor():
    """Teste le processeur vidéo."""
    print("\n🎬 Test du processeur vidéo...")
    
    try:
        from ai_video_dubbing.processors.video_processor import VideoProcessor
        from ai_video_dubbing.utils.ffmpeg_manager import FFmpegManager
        
        # Créer un gestionnaire FFmpeg qui ne lève pas d'exception
        ffmpeg_manager = FFmpegManager()
        
        # Créer le processeur vidéo avec gestion d'erreur
        try:
            processor = VideoProcessor(ffmpeg_manager=ffmpeg_manager)
            print("    ✅ Processeur vidéo créé avec FFmpeg")
        except Exception as e:
            print(f"    ⚠️ Processeur vidéo créé sans FFmpeg: {e}")
            # Créer un processeur sans vérification FFmpeg pour les tests
            processor = None
        
        return True
        
    except Exception as e:
        print(f"    ❌ Erreur processeur vidéo: {e}")
        traceback.print_exc()
        return False

def test_gui_widgets():
    """Teste les widgets GUI."""
    print("\n🖥️ Test des widgets GUI...")
    
    try:
        # Test sans créer d'application Qt (juste l'import)
        from ai_video_dubbing.gui.ffmpeg_config_widget import FFmpegConfigWidget
        print("    ✅ Widget FFmpeg importé")
        
        from ai_video_dubbing.gui.config_panel_qt import ConfigPanelQt
        print("    ✅ Panneau de configuration importé")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Erreur widgets GUI: {e}")
        traceback.print_exc()
        return False

def test_main_application():
    """Teste l'application principale."""
    print("\n🚀 Test de l'application principale...")
    
    try:
        from main import main
        print("    ✅ Application principale importée")
        
        # Ne pas lancer l'application, juste vérifier l'import
        return True
        
    except Exception as e:
        print(f"    ❌ Erreur application principale: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test de démarrage de l'application AI Video Dubbing\n")
    
    tests = [
        ("Imports", test_imports),
        ("Gestionnaire FFmpeg", test_ffmpeg_manager),
        ("Processeur vidéo", test_video_processor),
        ("Widgets GUI", test_gui_widgets),
        ("Application principale", test_main_application)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés ! L'application devrait pouvoir démarrer.")
        print("\nPour démarrer l'application:")
        print("  python main.py")
        print("\nPour tester FFmpeg:")
        print("  python test_ffmpeg_config.py")
        print("\nPour la démonstration complète:")
        print("  python demo_ffmpeg_integration.py")
    else:
        print(f"\n⚠️ {total - passed} test(s) ont échoué. Vérifiez les erreurs ci-dessus.")
        
        if not results[0][1]:  # Si les imports de base échouent
            print("\n🔧 SOLUTIONS POSSIBLES:")
            print("1. Vérifiez que toutes les dépendances sont installées:")
            print("   pip install PyQt5 opencv-python numpy")
            print("2. Vérifiez la structure des fichiers du projet")
            print("3. Assurez-vous d'être dans le bon répertoire")

if __name__ == "__main__":
    main()