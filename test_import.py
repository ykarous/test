#!/usr/bin/env python3
"""
Test simple d'import
"""

try:
    import ai_video_dubbing.performance.cache_manager as cache_module
    print("✅ Import du module réussi")
    
    # Lister les classes disponibles
    classes = [name for name in dir(cache_module) if not name.startswith('_')]
    print(f"Classes disponibles: {classes}")
    
    # Tester l'import de ModelCacheManager
    from ai_video_dubbing.performance.cache_manager import ModelCacheManager
    print("✅ Import de ModelCacheManager réussi")
    
    # Créer une instance
    manager = ModelCacheManager()
    print("✅ Création d'instance réussie")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()