#!/usr/bin/env python3
"""
Test simple du cache manager
"""

import tempfile
import shutil
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_cache():
    """Test le cache manager simple"""
    print("🧪 Test du cache manager simple")
    print("=" * 40)
    
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Répertoire temporaire: {temp_dir}")
    
    try:
        from ai_video_dubbing.performance.simple_cache import SimpleCacheManager
        
        # Créer le gestionnaire de cache
        cache_manager = SimpleCacheManager(cache_dir=temp_dir)
        print("✅ Cache manager créé")
        
        # Test 1: Vérifier qu'un modèle n'est pas en cache
        is_cached = cache_manager.is_model_cached("test_model")
        print(f"   Modèle en cache (initial): {is_cached}")
        assert not is_cached
        
        # Test 2: Créer un fichier de test et l'ajouter au cache
        test_file = Path(temp_dir) / "test_model.bin"
        test_content = b"Test model content for cache validation"
        test_file.write_bytes(test_content)
        print(f"   Fichier de test créé: {test_file}")
        
        success = cache_manager.add_model_to_cache("test_model", str(test_file))
        print(f"   Ajout au cache: {'✅ Réussi' if success else '❌ Échoué'}")
        assert success
        
        # Test 3: Vérifier que le modèle est maintenant en cache
        is_cached = cache_manager.is_model_cached("test_model")
        print(f"   Modèle en cache (après ajout): {is_cached}")
        assert is_cached
        
        # Test 4: Récupérer le chemin du modèle
        model_path = cache_manager.get_model_path("test_model")
        print(f"   Chemin du modèle: {model_path}")
        assert model_path is not None
        
        # Test 5: Statistiques du cache
        stats = cache_manager.get_cache_stats()
        print(f"   Statistiques:")
        print(f"     - Modèles: {stats.total_models}")
        print(f"     - Taille: {stats.total_size_mb:.3f} MB")
        print(f"     - Espace disponible: {stats.available_space_mb:.1f} MB")
        assert stats.total_models == 1
        
        # Test 6: Liste des modèles
        models = cache_manager.list_cached_models()
        print(f"   Modèles en cache: {len(models)}")
        for model in models:
            print(f"     - {model['name']}: {model['size_mb']:.3f} MB")
        assert len(models) == 1
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
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

def main():
    """Point d'entrée principal"""
    print("🚀 Test du Cache Manager Simple")
    print("=" * 50)
    
    success = test_simple_cache()
    
    if success:
        print("\n✅ Le cache manager simple fonctionne correctement!")
        print("   Prêt pour l'intégration avec le gestionnaire de modèles")
    else:
        print("\n❌ Des erreurs ont été détectées")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)