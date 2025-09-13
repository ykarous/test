#!/usr/bin/env python3
"""
Test simple de l'intégration NVIDIA NeMo et LM Studio.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def test_model_discovery():
    """Test de la découverte de modèles."""
    print("🔍 Test de découverte de modèles...")
    
    try:
        from ai_video_dubbing.utils.model_discovery import ModelDiscovery
        
        discovery = ModelDiscovery()
        models = discovery.discover_all_models()
        
        print(f"✅ Découverte réussie: {sum(len(m) for m in models.values())} modèles trouvés")
        
        # Afficher un résumé
        for category, model_list in models.items():
            if model_list:
                print(f"  📂 {category}: {len(model_list)} modèles")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur découverte: {e}")
        return False

def test_lm_studio_manager():
    """Test du gestionnaire LM Studio."""
    print("\n🖥️  Test du gestionnaire LM Studio...")
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        # Test de connexion
        is_running = lm_manager.is_server_running()
        print(f"  Serveur LM Studio: {'✅ En cours' if is_running else '❌ Arrêté'}")
        
        # Test de récupération des modèles
        models = lm_manager.get_available_models()
        print(f"  Modèles disponibles: {len(models)}")
        
        # Test des modèles de transcription
        transcription_models = lm_manager.get_models_for_transcription()
        print(f"  Modèles transcription: {len(transcription_models)}")
        
        # Test des modèles OCR
        ocr_models = lm_manager.get_models_for_ocr()
        print(f"  Modèles OCR: {len(ocr_models)}")
        
        print("✅ Gestionnaire LM Studio testé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur LM Studio: {e}")
        return False

def test_ai_model_manager():
    """Test du gestionnaire de modèles IA intégré."""
    print("\n🤖 Test du gestionnaire de modèles IA...")
    
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        ai_manager = AIModelManager()
        
        # Test de récupération des modèles disponibles
        available_models = ai_manager.get_available_models()
        print(f"  Modèles disponibles par catégorie:")
        
        for category, models in available_models.items():
            if isinstance(models, list):
                print(f"    {category}: {len(models)} modèles")
            else:
                print(f"    {category}: {models}")
        
        # Test des capacités étendues
        has_discovery = hasattr(ai_manager, 'model_discovery')
        has_lm_studio = hasattr(ai_manager, 'lm_studio_manager')
        
        print(f"  Découverte automatique: {'✅' if has_discovery else '❌'}")
        print(f"  Intégration LM Studio: {'✅' if has_lm_studio else '❌'}")
        
        print("✅ Gestionnaire de modèles IA testé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur gestionnaire IA: {e}")
        return False

def test_nemo_availability():
    """Test de la disponibilité de NeMo."""
    print("\n🚀 Test de disponibilité NVIDIA NeMo...")
    
    try:
        import nemo
        print(f"✅ NeMo disponible - Version: {nemo.__version__}")
        
        # Test d'import des modules ASR
        try:
            import nemo.collections.asr as nemo_asr
            print("✅ Module ASR NeMo importé")
        except ImportError as e:
            print(f"⚠️  Module ASR NeMo non disponible: {e}")
        
        return True
        
    except ImportError:
        print("❌ NVIDIA NeMo non installé")
        print("💡 Installation: pip install nemo_toolkit")
        return False
    except Exception as e:
        print(f"❌ Erreur NeMo: {e}")
        return False

def test_integration_completeness():
    """Test de complétude de l'intégration."""
    print("\n🔧 Test de complétude de l'intégration...")
    
    try:
        # Vérifier que tous les fichiers nécessaires existent
        required_files = [
            "ai_video_dubbing/processors/lm_studio_manager.py",
            "ai_video_dubbing/utils/model_discovery.py",
            "ai_video_dubbing/processors/ai_model_manager.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Fichiers manquants: {missing_files}")
            return False
        
        print("✅ Tous les fichiers d'intégration sont présents")
        
        # Vérifier les imports
        try:
            from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
            from ai_video_dubbing.utils.model_discovery import ModelDiscovery
            print("✅ Imports des nouveaux modules réussis")
        except ImportError as e:
            print(f"❌ Erreur d'import: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test complétude: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 TESTS SIMPLES - INTÉGRATION NEMO & LM STUDIO")
    print("=" * 50)
    
    tests = [
        ("Complétude intégration", test_integration_completeness),
        ("Découverte modèles", test_model_discovery),
        ("Gestionnaire LM Studio", test_lm_studio_manager),
        ("Gestionnaire IA", test_ai_model_manager),
        ("Disponibilité NeMo", test_nemo_availability)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Tests réussis: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés!")
        print("   L'intégration NeMo & LM Studio est fonctionnelle.")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} test(s) ont échoué.")
        print("   Certaines fonctionnalités peuvent être limitées.")
    else:
        print("\n❌ Tous les tests ont échoué.")
        print("   L'intégration nécessite des corrections.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)