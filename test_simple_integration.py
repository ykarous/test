#!/usr/bin/env python3
"""
Test simple d'intégration cache + gestionnaire de modèles
"""

import tempfile
import shutil
import sys
import asyncio
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.insert(0, str(Path(__file__).parent))

async def test_simple_integration():
    """Test simple de l'intégration"""
    print("🧪 Test Simple d'Intégration")
    print("=" * 40)
    
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Répertoire temporaire: {temp_dir}")
    
    try:
        from ai_video_dubbing.performance.simple_cache import SimpleCacheManager
        from ai_video_dubbing.performance.model_manager import LightweightModelManager
        
        # Créer les composants
        cache_manager = SimpleCacheManager(cache_dir=temp_dir)
        model_manager = LightweightModelManager(cache_manager=cache_manager)
        print("✅ Composants créés")
        
        # Test 1: Modèle non disponible
        is_available, file_path = await model_manager.ensure_model_available("test_model")
        print(f"   Modèle test_model disponible: {is_available}")
        assert not is_available
        
        # Test 2: Ajouter un modèle au cache
        test_file = Path(temp_dir) / "test_model.nemo"
        test_file.write_bytes(b"Test model content")
        
        success = cache_manager.add_model_to_cache("test_model", str(test_file))
        print(f"   Ajout au cache: {'✅' if success else '❌'}")
        assert success
        
        # Test 3: Modèle maintenant disponible
        is_available, file_path = await model_manager.ensure_model_available("test_model")
        print(f"   Modèle test_model disponible: {is_available}")
        assert is_available
        assert file_path is not None
        
        # Test 4: Recommandation
        recommendation = model_manager.get_recommended_model()
        print(f"   Modèle recommandé: {recommendation.model_name}")
        assert recommendation.model_name is not None
        
        # Test 5: Statistiques
        stats = model_manager.get_cache_stats()
        print(f"   Modèles en cache: {stats['total_models']}")
        assert stats['total_models'] == 1
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("🧹 Nettoyage terminé")

async def main():
    success = await test_simple_integration()
    
    if success:
        print("\n✅ Intégration cache + gestionnaire de modèles validée!")
        print("🚀 Prêt pour la suite de l'implémentation")
        return 0
    else:
        print("\n❌ Problème détecté")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)