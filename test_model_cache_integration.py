#!/usr/bin/env python3
"""
Test d'intégration du cache manager avec le gestionnaire de modèles
"""

import tempfile
import shutil
import sys
import asyncio
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

async def test_model_cache_integration():
    """Test l'intégration complète cache + gestionnaire de modèles"""
    print("🧪 Test d'intégration Cache + Gestionnaire de Modèles")
    print("=" * 60)
    
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Répertoire temporaire: {temp_dir}")
    
    try:
        from ai_video_dubbing.performance.simple_cache import SimpleCacheManager
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        # Créer le cache manager
        cache_manager = SimpleCacheManager(cache_dir=temp_dir)
        print("✅ Cache manager créé")
        
        # Créer le gestionnaire de modèles avec le cache
        model_manager = LightweightModelManager(cache_manager=cache_manager)
        print("✅ Gestionnaire de modèles créé")
        
        # Test 1: Vérifier qu'un modèle n'est pas disponible initialement
        print("\n📋 Test 1: Vérification modèle non disponible")
        is_available, file_path = await model_manager.ensure_model_available("test_model")
        print(f"   Modèle disponible: {is_available}")
        print(f"   Chemin: {file_path}")
        assert not is_available
        assert file_path is None
        
        # Test 2: Simuler l'ajout d'un modèle au cache
        print("\n📋 Test 2: Ajout d'un modèle au cache")
        test_file = Path(temp_dir) / "test_model.nemo"
        test_content = b"Fake NeMo model content for testing cache integration"
        test_file.write_bytes(test_content)
        print(f"   Fichier de test créé: {test_file}")
        
        success = cache_manager.add_model_to_cache("test_model", str(test_file))
        print(f"   Ajout au cache: {'✅ Réussi' if success else '❌ Échoué'}")
        assert success
        
        # Test 3: Vérifier que le modèle est maintenant disponible
        print("\n📋 Test 3: Vérification modèle disponible après ajout")
        is_available, file_path = await model_manager.ensure_model_available("test_model")
        print(f"   Modèle disponible: {is_available}")
        print(f"   Chemin: {file_path}")
        assert is_available
        assert file_path is not None
        assert Path(file_path).exists()
        
        # Test 4: Tester les recommandations de modèles
        print("\n📋 Test 4: Recommandations de modèles")
        recommendation = model_manager.get_recommended_model(
            model_type="asr",
            quality_preference="speed"
        )
        print(f"   Modèle recommandé: {recommendation.model_name}")
        print(f"   Catégorie: {recommendation.category}")
        print(f"   Qualité: {recommendation.quality_level}")
        print(f"   Raison: {recommendation.reason}")
        print(f"   Confiance: {recommendation.confidence:.2f}")
        assert recommendation.model_name is not None
        
        # Test 5: Obtenir les informations des modèles en cache
        print("\n📋 Test 5: Informations des modèles en cache")
        cached_models = await model_manager.get_cached_models_info()
        print(f"   Modèles en cache: {len(cached_models)}")
        for model in cached_models:
            print(f"     - {model['name']}: {model['size_mb']:.3f} MB ({model.get('category', 'unknown')})")
        assert len(cached_models) == 1
        assert cached_models[0]['name'] == 'test_model'
        
        # Test 6: Statistiques du cache
        print("\n📋 Test 6: Statistiques du cache")
        cache_stats = model_manager.get_cache_stats()
        print(f"   Modèles totaux: {cache_stats['total_models']}")
        print(f"   Taille totale: {cache_stats['total_size_mb']:.3f} MB")
        print(f"   Espace disponible: {cache_stats['available_space_mb']:.1f} MB")
        assert cache_stats['total_models'] == 1
        
        # Test 7: Statistiques de performance
        print("\n📋 Test 7: Statistiques de performance")
        perf_stats = model_manager.get_performance_stats()
        print(f"   Modèles dans le catalogue: {perf_stats['total_models']}")
        print(f"   Modèles par catégorie: {perf_stats['models_by_category']}")
        print(f"   Ressources système:")
        print(f"     - Mémoire disponible: {perf_stats['system_resources']['available_memory_mb']:.1f} MB")
        print(f"     - GPU disponible: {perf_stats['system_resources']['gpu_available']}")
        print(f"     - Vitesse connexion: {perf_stats['system_resources']['connection_speed_mbps']:.1f} Mbps")
        assert perf_stats['total_models'] > 0
        
        # Test 8: Suppression d'un modèle du cache
        print("\n📋 Test 8: Suppression d'un modèle du cache")
        success = await model_manager.remove_cached_model("test_model")
        print(f"   Suppression: {'✅ Réussie' if success else '❌ Échouée'}")
        assert success
        
        # Vérifier que le modèle n'est plus disponible
        is_available, file_path = await model_manager.ensure_model_available("test_model")
        print(f"   Modèle disponible après suppression: {is_available}")
        assert not is_available
        
        print("\n🎉 TOUS LES TESTS D'INTÉGRATION RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Nettoyage
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🧹 Nettoyage terminé")

async def main():
    """Point d'entrée principal"""
    print("🚀 Test d'Intégration Cache + Gestionnaire de Modèles")
    print("=" * 70)
    
    # Test principal
    success = await test_model_cache_integration()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 TOUS LES TESTS D'INTÉGRATION RÉUSSIS!")
        print("\n💡 Fonctionnalités validées:")
        print("   ✅ Intégration cache + gestionnaire de modèles")
        print("   ✅ Méthode ensure_model_available()")
        print("   ✅ Recommandations de modèles")
        print("   ✅ Statistiques et monitoring")
        print("   ✅ Gestion des modèles en cache")
        print("\n🚀 Prêt pour l'intégration avec le téléchargement intelligent!")
        return 0
    else:
        print("\n❌ Des erreurs ont été détectées dans les tests")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)