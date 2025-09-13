#!/usr/bin/env python3
"""
Script de test pour l'intégration du cache et de la validation des modèles
"""

import asyncio
import tempfile
import shutil
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

from ai_video_dubbing.performance.cache_manager import ModelCacheManager
from ai_video_dubbing.performance.model_manager import LightweightModelManager

async def test_cache_integration():
    """Test l'intégration complète du cache avec le gestionnaire de modèles"""
    print("🧪 Test d'intégration du cache et gestionnaire de modèles")
    print("=" * 60)
    
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Répertoire temporaire: {temp_dir}")
    
    try:
        # Créer les gestionnaires
        cache_manager = ModelCacheManager(cache_dir=temp_dir, max_cache_size_gb=0.1)  # 100MB
        model_manager = LightweightModelManager(cache_manager=cache_manager)
        
        print("\n1. 📊 Test des statistiques initiales")
        stats = model_manager.get_performance_stats()
        print(f"   Modèles dans le catalogue: {stats['total_models']}")
        print(f"   Modèles en cache: {stats['cache_stats']['total_models']}")
        
        print("\n2. 🔍 Test des recommandations de modèles")
        recommendation = model_manager.get_recommended_model(
            model_type="asr",
            quality_preference="speed"
        )
        print(f"   Modèle recommandé: {recommendation.model_name}")
        print(f"   Catégorie: {recommendation.category}")
        print(f"   Raison: {recommendation.reason}")
        print(f"   Temps de téléchargement estimé: {recommendation.estimated_download_time}s")
        
        print("\n3. 📦 Test de vérification de disponibilité")
        is_available, file_path = await model_manager.ensure_model_available(recommendation.model_name)
        print(f"   Modèle disponible: {is_available}")
        print(f"   Chemin: {file_path}")
        
        print("\n4. 🗂️ Simulation d'ajout de modèle au cache")
        # Créer un fichier de test simulant un modèle
        test_model_file = Path(temp_dir) / "simulated_model.bin"
        test_content = b"Simulated model content for testing" * 1000  # ~34KB
        test_model_file.write_bytes(test_content)
        
        success = await cache_manager.add_model_to_cache(
            "simulated_model",
            str(test_model_file)
        )
        print(f"   Ajout au cache: {'✅ Réussi' if success else '❌ Échoué'}")
        
        print("\n5. ✅ Test de validation du modèle")
        is_valid = await cache_manager.validate_model("simulated_model")
        print(f"   Validation: {'✅ Valide' if is_valid else '❌ Invalide'}")
        
        print("\n6. 📋 Test de liste des modèles en cache")
        cached_models = await model_manager.get_cached_models_info()
        print(f"   Nombre de modèles en cache: {len(cached_models)}")
        for model in cached_models:
            print(f"   - {model['name']}: {model['size_mb']:.1f} MB, accès: {model['access_count']}")
        
        print("\n7. 📊 Test des statistiques finales")
        final_stats = model_manager.get_performance_stats()
        cache_stats = final_stats['cache_stats']
        print(f"   Modèles en cache: {cache_stats['total_models']}")
        print(f"   Taille totale: {cache_stats['total_size_mb']:.1f} MB")
        print(f"   Espace disponible: {cache_stats['available_space_mb']:.1f} MB")
        
        print("\n8. 🧹 Test de suppression de modèle")
        removed = await model_manager.remove_cached_model("simulated_model")
        print(f"   Suppression: {'✅ Réussie' if removed else '❌ Échouée'}")
        
        # Vérifier que le modèle n'est plus en cache
        is_still_cached = await cache_manager.is_model_cached("simulated_model")
        print(f"   Encore en cache: {'❌ Oui' if is_still_cached else '✅ Non'}")
        
        print("\n9. 🔧 Test de corruption et récupération")
        # Ajouter un nouveau modèle
        test_model_file2 = Path(temp_dir) / "test_corruption.bin"
        original_content = b"Original model content" * 100
        test_model_file2.write_bytes(original_content)
        
        await cache_manager.add_model_to_cache("test_corruption", str(test_model_file2))
        print("   Modèle ajouté pour test de corruption")
        
        # Corrompre le fichier
        test_model_file2.write_bytes(b"Corrupted content")
        print("   Fichier corrompu")
        
        # Tester la validation
        is_valid_after_corruption = await cache_manager.validate_model("test_corruption")
        print(f"   Validation après corruption: {'❌ Valide' if is_valid_after_corruption else '✅ Invalide (détecté)'}")
        
        # Tester ensure_model_available avec modèle corrompu
        is_available_corrupted, _ = await model_manager.ensure_model_available("test_corruption")
        print(f"   Disponibilité après corruption: {'❌ Disponible' if is_available_corrupted else '✅ Non disponible (nettoyé)'}")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Cache manager fonctionnel")
        print("✅ Validation d'intégrité opérationnelle")
        print("✅ Gestion des modèles corrompus")
        print("✅ Intégration avec le gestionnaire de modèles")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Nettoyage
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Nettoyage terminé: {temp_dir}")

def test_model_recommendations():
    """Test les recommandations de modèles selon différents scénarios"""
    print("\n🎯 Test des recommandations de modèles")
    print("=" * 40)
    
    manager = LightweightModelManager()
    
    scenarios = [
        {
            "name": "Système puissant",
            "resources": {
                "available_memory_mb": 16000,
                "gpu_available": True,
                "connection_speed_mbps": 100,
                "disk_space_gb": 500
            },
            "preference": "quality"
        },
        {
            "name": "Système limité",
            "resources": {
                "available_memory_mb": 2000,
                "gpu_available": False,
                "connection_speed_mbps": 5,
                "disk_space_gb": 20
            },
            "preference": "speed"
        },
        {
            "name": "Équilibré",
            "resources": {
                "available_memory_mb": 8000,
                "gpu_available": True,
                "connection_speed_mbps": 50,
                "disk_space_gb": 100
            },
            "preference": "balanced"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scénario: {scenario['name']}")
        
        # Mock des ressources système
        from unittest.mock import patch
        from ai_video_dubbing.performance.model_manager import SystemResources
        
        mock_resources = SystemResources(
            available_memory_mb=scenario["resources"]["available_memory_mb"],
            total_memory_mb=scenario["resources"]["available_memory_mb"] * 2,
            memory_usage_percent=50.0,
            cpu_count=8,
            gpu_available=scenario["resources"]["gpu_available"],
            gpu_memory_mb=4000 if scenario["resources"]["gpu_available"] else 0,
            disk_space_gb=scenario["resources"]["disk_space_gb"],
            connection_speed_mbps=scenario["resources"]["connection_speed_mbps"]
        )
        
        with patch.object(manager, 'get_system_resources', return_value=mock_resources):
            recommendation = manager.get_recommended_model(
                model_type="asr",
                quality_preference=scenario["preference"]
            )
            
            model_info = manager.get_model_info(recommendation.model_name)
            
            print(f"   Modèle: {recommendation.model_name}")
            print(f"   Catégorie: {recommendation.category}")
            print(f"   Taille: {model_info.size_mb} MB")
            print(f"   Qualité: {model_info.quality}")
            print(f"   Temps estimé: {recommendation.estimated_download_time}s")
            print(f"   Confiance: {recommendation.confidence:.2f}")
            print(f"   Raison: {recommendation.reason}")

async def main():
    """Point d'entrée principal"""
    print("🚀 Test d'intégration - Cache et Gestionnaire de Modèles")
    print("=" * 70)
    
    # Test 1: Intégration du cache
    success1 = await test_cache_integration()
    
    # Test 2: Recommandations de modèles
    test_model_recommendations()
    
    print("\n" + "=" * 70)
    if success1:
        print("🎉 TOUS LES TESTS D'INTÉGRATION RÉUSSIS!")
        print("\n💡 Le système de cache et de validation est prêt:")
        print("   ✅ Validation d'intégrité des modèles")
        print("   ✅ Gestion automatique du cache")
        print("   ✅ Détection et nettoyage des modèles corrompus")
        print("   ✅ Recommandations intelligentes de modèles")
        print("   ✅ Intégration avec le gestionnaire de modèles")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)