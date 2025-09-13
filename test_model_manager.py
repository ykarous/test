#!/usr/bin/env python3
"""
Script de test pour le gestionnaire de modèles légers
"""

import sys
import signal
from pathlib import Path

# Patch pour NeMo sur Windows AVANT tout import
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))


def test_model_catalog():
    """Test du catalogue de modèles"""
    print("📚 Test du catalogue de modèles...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        catalog = manager.model_catalog
        
        print(f"   Total de modèles: {len(catalog)}")
        
        # Afficher les modèles par catégorie
        categories = {}
        for model in catalog.values():
            if model.category not in categories:
                categories[model.category] = []
            categories[model.category].append(model)
        
        for category, models in categories.items():
            print(f"   {category.upper()}: {len(models)} modèles")
            for model in sorted(models, key=lambda m: m.size_mb):
                print(f"      - {model.name}: {model.size_mb}MB, {model.quality}, {model.languages}")
        
        print("   ✅ Catalogue de modèles chargé")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_system_resources():
    """Test de détection des ressources système"""
    print("\n💻 Test de détection des ressources système...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        resources = manager.get_system_resources()
        
        print(f"   Mémoire disponible: {resources.available_memory_mb:.0f} MB")
        print(f"   Mémoire totale: {resources.total_memory_mb:.0f} MB")
        print(f"   Utilisation mémoire: {resources.memory_usage_percent:.1f}%")
        print(f"   Nombre de CPU: {resources.cpu_count}")
        print(f"   GPU disponible: {resources.gpu_available}")
        if resources.gpu_available:
            print(f"   Mémoire GPU: {resources.gpu_memory_mb:.0f} MB")
        print(f"   Espace disque: {resources.disk_space_gb:.1f} GB")
        print(f"   Vitesse connexion: {resources.connection_speed_mbps:.1f} Mbps")
        
        print("   ✅ Ressources système détectées")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_recommendations():
    """Test des recommandations de modèles"""
    print("\n🎯 Test des recommandations de modèles...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        
        # Test différentes préférences
        preferences = [
            ("speed", "Vitesse prioritaire"),
            ("balanced", "Équilibré"),
            ("quality", "Qualité prioritaire")
        ]
        
        for pref, desc in preferences:
            print(f"\n   {desc} ({pref}):")
            
            recommendation = manager.get_recommended_model(
                model_type="asr",
                quality_preference=pref
            )
            
            model = manager.get_model_info(recommendation.model_name)
            
            print(f"      Modèle: {recommendation.model_name}")
            print(f"      Catégorie: {recommendation.category}")
            print(f"      Qualité: {recommendation.quality_level}")
            print(f"      Taille: {model.size_mb}MB")
            print(f"      Temps téléchargement: {recommendation.estimated_download_time}s")
            print(f"      Confiance: {recommendation.confidence:.2f}")
            print(f"      Raison: {recommendation.reason}")
            
            if recommendation.alternatives:
                print(f"      Alternatives: {', '.join(recommendation.alternatives[:2])}")
        
        print("\n   ✅ Recommandations générées")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_language_specific_recommendations():
    """Test des recommandations par langue"""
    print("\n🌍 Test des recommandations par langue...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        
        languages = ["fr", "en", None]  # None = multilingue
        
        for lang in languages:
            lang_desc = lang if lang else "multilingue"
            print(f"\n   Langue: {lang_desc}")
            
            recommendation = manager.get_recommended_model(
                model_type="asr",
                language=lang,
                quality_preference="balanced"
            )
            
            model = manager.get_model_info(recommendation.model_name)
            
            print(f"      Modèle: {recommendation.model_name}")
            print(f"      Langues supportées: {', '.join(model.languages)}")
            print(f"      Taille: {model.size_mb}MB")
            print(f"      Raison: {recommendation.reason}")
        
        print("\n   ✅ Recommandations par langue testées")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_model_filtering():
    """Test du filtrage de modèles"""
    print("\n🔍 Test du filtrage de modèles...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        
        # Test filtrage par taille
        small_models = manager.get_available_models(max_size_mb=100)
        print(f"   Modèles < 100MB: {len(small_models)}")
        for model in small_models[:3]:  # Afficher les 3 premiers
            print(f"      - {model.name}: {model.size_mb}MB")
        
        # Test filtrage par type
        asr_models = manager.get_available_models(model_type="asr")
        diarization_models = manager.get_available_models(model_type="diarization")
        print(f"   Modèles ASR: {len(asr_models)}")
        print(f"   Modèles diarisation: {len(diarization_models)}")
        
        # Test filtrage par compatibilité
        cpu_models = manager.get_available_models(device_compatibility="cpu")
        gpu_models = manager.get_available_models(device_compatibility="gpu")
        print(f"   Modèles compatibles CPU: {len(cpu_models)}")
        print(f"   Modèles compatibles GPU: {len(gpu_models)}")
        
        print("   ✅ Filtrage de modèles testé")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_performance_stats():
    """Test des statistiques de performance"""
    print("\n📊 Test des statistiques de performance...")
    
    try:
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        manager = LightweightModelManager()
        stats = manager.get_performance_stats()
        
        print(f"   Total modèles: {stats['total_models']}")
        
        print("   Modèles par catégorie:")
        for category, count in stats['models_by_category'].items():
            print(f"      {category}: {count}")
        
        print("   Modèles par type:")
        for model_type, count in stats['models_by_type'].items():
            print(f"      {model_type}: {count}")
        
        print("   Ressources système:")
        sys_res = stats['system_resources']
        print(f"      Mémoire disponible: {sys_res['available_memory_mb']:.0f} MB")
        print(f"      GPU disponible: {sys_res['gpu_available']}")
        print(f"      Vitesse connexion: {sys_res['connection_speed_mbps']:.1f} Mbps")
        print(f"      Espace disque: {sys_res['disk_space_gb']:.1f} GB")
        
        print("   ✅ Statistiques récupérées")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_model_scoring():
    """Test du système de scoring des modèles"""
    print("\n🏆 Test du système de scoring...")
    
    try:
        from ai_video_dubbing.performance.model_manager import (
            LightweightModelManager, SystemResources
        )
        
        manager = LightweightModelManager()
        
        # Créer des ressources de test
        limited_resources = SystemResources(
            available_memory_mb=1000,
            total_memory_mb=2000,
            memory_usage_percent=70.0,
            cpu_count=2,
            gpu_available=False,
            gpu_memory_mb=0,
            disk_space_gb=20.0,
            connection_speed_mbps=5.0
        )
        
        abundant_resources = SystemResources(
            available_memory_mb=8000,
            total_memory_mb=16000,
            memory_usage_percent=30.0,
            cpu_count=8,
            gpu_available=True,
            gpu_memory_mb=8000,
            disk_space_gb=500.0,
            connection_speed_mbps=100.0
        )
        
        # Tester avec différents modèles
        test_models = ["whisper-tiny", "whisper-base", "whisper-large-v3"]
        
        print("   Scores avec ressources limitées:")
        for model_name in test_models:
            if model_name in manager.model_catalog:
                model = manager.model_catalog[model_name]
                score = manager._score_model(model, limited_resources, "balanced", "auto")
                print(f"      {model_name}: {score:.1f}")
        
        print("   Scores avec ressources abondantes:")
        for model_name in test_models:
            if model_name in manager.model_catalog:
                model = manager.model_catalog[model_name]
                score = manager._score_model(model, abundant_resources, "balanced", "auto")
                print(f"      {model_name}: {score:.1f}")
        
        print("   ✅ Système de scoring testé")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def main():
    """Point d'entrée principal"""
    print("🧪 Test du Gestionnaire de Modèles Légers")
    print("=" * 50)
    
    tests = [
        ("Catalogue de Modèles", test_model_catalog),
        ("Ressources Système", test_system_resources),
        ("Recommandations", test_model_recommendations),
        ("Recommandations par Langue", test_language_specific_recommendations),
        ("Filtrage de Modèles", test_model_filtering),
        ("Statistiques", test_performance_stats),
        ("Système de Scoring", test_model_scoring),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} erreur: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status:12} {test_name}")
    
    print("-" * 50)
    print(f"Total: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("\n💡 Le gestionnaire de modèles légers est fonctionnel:")
        print("   - Catalogue de modèles complet")
        print("   - Détection des ressources système")
        print("   - Recommandations intelligentes")
        print("   - Filtrage et scoring avancés")
    else:
        print("⚠️  Certains tests ont échoué")
    
    print("\n🔧 Fonctionnalités disponibles:")
    print("   - Recommandations basées sur les ressources")
    print("   - Filtrage par taille, type et compatibilité")
    print("   - Support multilingue")
    print("   - Scoring intelligent des modèles")
    print("   - Statistiques de performance")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()