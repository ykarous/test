"""
Test de l'optimisateur automatique de cache et mémoire
"""

import asyncio
import time
import logging
import json
import random
from ai_video_dubbing.performance.auto_optimizer import (
    AutoOptimizer,
    IntelligentCacheManager,
    OptimizationRule,
    OptimizationType,
    OptimizationPriority,
    get_auto_optimizer,
    optimize_system,
    get_system_optimization_stats
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_intelligent_cache_manager():
    """Test du gestionnaire de cache intelligent"""
    
    print("=== Test du Gestionnaire de Cache Intelligent ===\n")
    
    # Créer un gestionnaire de cache
    cache = IntelligentCacheManager(max_size_mb=10)  # 10MB pour les tests
    
    print("1. Test de stockage et récupération...")
    
    # Stocker quelques entrées
    test_data = {
        "small_data": "Hello World" * 100,  # Petites données
        "medium_data": "x" * (1024 * 100),  # 100KB
        "large_data": "y" * (1024 * 1024 * 2),  # 2MB - sera compressé
        "priority_data": {"important": True, "data": "z" * 1000}
    }
    
    for key, data in test_data.items():
        priority = 3 if "priority" in key else 1
        success = await cache.set(key, data, priority=priority)
        print(f"   Stocké '{key}': {success}")
    
    # Récupérer les données
    print("\n2. Test de récupération...")
    for key in test_data.keys():
        retrieved = await cache.get(key)
        success = retrieved is not None
        print(f"   Récupéré '{key}': {success}")
        
        if success and key == "large_data":
            print(f"      Taille récupérée: {len(retrieved)} caractères")
    
    # Afficher les statistiques
    print("\n3. Statistiques du cache:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    # Test de prédiction d'accès
    print("\n4. Test de prédiction d'accès...")
    
    # Simuler des accès répétés
    for i in range(5):
        await cache.get("small_data")
        await asyncio.sleep(0.1)
    
    # Vérifier la prédiction
    prediction = cache._predict_future_access("small_data")
    print(f"   Probabilité d'accès futur pour 'small_data': {prediction:.2f}")
    
    # Test de nettoyage
    print("\n5. Test de nettoyage...")
    initial_entries = len(cache.memory_cache)
    cleaned = await cache.cleanup_expired_entries(max_age_hours=0.001)  # Très court pour forcer le nettoyage
    final_entries = len(cache.memory_cache)
    
    print(f"   Entrées avant: {initial_entries}")
    print(f"   Entrées nettoyées: {cleaned}")
    print(f"   Entrées après: {final_entries}")
    
    print("\n✅ Test du cache terminé")

async def test_auto_optimizer():
    """Test de l'optimisateur automatique"""
    
    print("\n=== Test de l'Optimisateur Automatique ===\n")
    
    # Créer un optimisateur
    cache_manager = IntelligentCacheManager(max_size_mb=5)
    optimizer = AutoOptimizer(cache_manager)
    
    print("1. Configuration de l'optimisateur...")
    
    # Modifier les seuils pour déclencher plus facilement
    optimizer.config["memory_threshold_percent"] = 40.0  # 40% au lieu de 80%
    optimizer.config["disk_threshold_percent"] = 80.0    # 80% au lieu de 90%
    
    print(f"   Seuil mémoire: {optimizer.config['memory_threshold_percent']}%")
    print(f"   Seuil disque: {optimizer.config['disk_threshold_percent']}%")
    print(f"   Règles d'optimisation: {len(optimizer.optimization_rules)}")
    
    # Remplir le cache pour déclencher les optimisations
    print("\n2. Remplissage du cache...")
    
    for i in range(20):
        key = f"test_data_{i}"
        data = "x" * (1024 * 200)  # 200KB par entrée
        await cache_manager.set(key, data, priority=random.randint(1, 3))
    
    cache_stats = cache_manager.get_cache_stats()
    print(f"   Entrées dans le cache: {cache_stats['entries']}")
    print(f"   Taille du cache: {cache_stats['total_size_mb']:.2f} MB")
    print(f"   Utilisation: {cache_stats['usage_percent']:.1f}%")
    
    # Test des conditions de déclenchement
    print("\n3. Test des conditions de déclenchement...")
    
    conditions = {
        "Seuil mémoire": optimizer._check_memory_threshold(),
        "Taille cache": optimizer._check_cache_size(),
        "Nettoyage cache": optimizer._check_cache_cleanup_needed(),
        "Seuil disque": optimizer._check_disk_threshold()
    }
    
    for condition, result in conditions.items():
        print(f"   {condition}: {'✅' if result else '❌'}")
    
    # Exécuter une optimisation manuelle
    print("\n4. Exécution d'optimisation manuelle...")
    
    initial_stats = optimizer.get_optimization_stats()
    print(f"   Optimisations initiales: {initial_stats['optimization_stats']['total_optimizations']}")
    
    optimization_result = await optimizer.run_manual_optimization()
    
    print(f"   Règles exécutées: {optimization_result['rules_executed']}")
    print(f"   Optimisations réussies: {optimization_result['successful_optimizations']}")
    print(f"   Mémoire économisée: {optimization_result['total_memory_saved_mb']:.2f} MB")
    print(f"   Disque économisé: {optimization_result['total_disk_saved_mb']:.2f} MB")
    
    if optimization_result['results']:
        print("   Détails des optimisations:")
        for result in optimization_result['results']:
            status = "✅" if result['success'] else "❌"
            print(f"   - {result['rule_id']}: {status} ({result['execution_time']:.2f}s)")
    
    # Vérifier les statistiques finales
    print("\n5. Statistiques finales...")
    
    final_stats = optimizer.get_optimization_stats()
    opt_stats = final_stats['optimization_stats']
    
    print(f"   Total optimisations: {opt_stats['total_optimizations']}")
    print(f"   Optimisations réussies: {opt_stats['successful_optimizations']}")
    print(f"   Mémoire totale économisée: {opt_stats['memory_saved_mb']:.2f} MB")
    print(f"   Améliorations de performance: {opt_stats['performance_improvements']}")
    
    # Test de l'historique
    print("\n6. Historique des optimisations...")
    
    history = optimizer.get_optimization_history(limit=5)
    print(f"   Entrées dans l'historique: {len(history)}")
    
    for entry in history:
        status = "✅" if entry['success'] else "❌"
        print(f"   - {entry['rule_id']}: {status}")
    
    await optimizer.shutdown()
    print("\n✅ Test de l'optimisateur terminé")

async def test_custom_optimization_rule():
    """Test d'ajout de règle d'optimisation personnalisée"""
    
    print("\n=== Test de Règle d'Optimisation Personnalisée ===\n")
    
    optimizer = AutoOptimizer()
    
    print("1. Ajout d'une règle personnalisée...")
    
    # Compteur pour la règle de test
    test_counter = {"executions": 0}
    
    def test_condition():
        """Condition qui se déclenche toujours"""
        return True
    
    async def test_action():
        """Action de test"""
        test_counter["executions"] += 1
        await asyncio.sleep(0.1)  # Simuler du travail
        return {
            "memory_saved_mb": 1.5,
            "performance_improvement": 0.1,
            "metadata": {"test_execution": test_counter["executions"]}
        }
    
    custom_rule = OptimizationRule(
        rule_id="test_custom_rule",
        name="Règle de test personnalisée",
        description="Règle de test pour démonstration",
        optimization_type=OptimizationType.MEMORY_CLEANUP,
        priority=OptimizationPriority.MEDIUM,
        trigger_condition=test_condition,
        optimization_action=test_action,
        cooldown_seconds=1.0  # Cooldown court pour les tests
    )
    
    optimizer.add_optimization_rule(custom_rule)
    print(f"   Règle ajoutée: {custom_rule.name}")
    
    # Exécuter l'optimisation
    print("\n2. Exécution de la règle personnalisée...")
    
    result = await optimizer.run_manual_optimization()
    
    executed_rules = [r for r in result['results'] if r['rule_id'] == 'test_custom_rule']
    
    if executed_rules:
        rule_result = executed_rules[0]
        print(f"   Règle exécutée: ✅")
        print(f"   Temps d'exécution: {rule_result['execution_time']:.3f}s")
        print(f"   Mémoire économisée: {rule_result['memory_saved_mb']:.1f} MB")
        print(f"   Exécutions du compteur: {test_counter['executions']}")
    else:
        print("   Règle non exécutée: ❌")
    
    # Test du cooldown
    print("\n3. Test du cooldown...")
    
    # Exécuter immédiatement à nouveau
    result2 = await optimizer.run_manual_optimization()
    executed_rules2 = [r for r in result2['results'] if r['rule_id'] == 'test_custom_rule']
    
    if not executed_rules2:
        print("   Cooldown fonctionne: ✅")
    else:
        print("   Cooldown ne fonctionne pas: ❌")
    
    # Attendre le cooldown et re-tester
    print("   Attente du cooldown (2 secondes)...")
    await asyncio.sleep(2)
    
    result3 = await optimizer.run_manual_optimization()
    executed_rules3 = [r for r in result3['results'] if r['rule_id'] == 'test_custom_rule']
    
    if executed_rules3:
        print("   Re-exécution après cooldown: ✅")
        print(f"   Nouvelles exécutions: {test_counter['executions']}")
    else:
        print("   Re-exécution après cooldown: ❌")
    
    await optimizer.shutdown()
    print("\n✅ Test de règle personnalisée terminé")

async def test_global_functions():
    """Test des fonctions utilitaires globales"""
    
    print("\n=== Test des Fonctions Globales ===\n")
    
    print("1. Test de la fonction d'optimisation globale...")
    
    # Utiliser la fonction utilitaire
    result = await optimize_system()
    
    print(f"   Règles exécutées: {result['rules_executed']}")
    print(f"   Optimisations réussies: {result['successful_optimizations']}")
    print(f"   Mémoire économisée: {result['total_memory_saved_mb']:.2f} MB")
    
    print("\n2. Test des statistiques globales...")
    
    stats = await get_system_optimization_stats()
    
    print(f"   Règles actives: {stats['active_rules']}")
    print(f"   Optimisations récentes: {stats['recent_optimizations']}")
    
    if 'cache_stats' in stats:
        cache_stats = stats['cache_stats']
        print(f"   Entrées en cache: {cache_stats['entries']}")
        print(f"   Taux de hit cache: {cache_stats['hit_rate']:.2%}")
    
    print("\n✅ Test des fonctions globales terminé")

async def test_performance_under_load():
    """Test de performance sous charge"""
    
    print("\n=== Test de Performance sous Charge ===\n")
    
    cache = IntelligentCacheManager(max_size_mb=20)
    
    print("1. Test de performance avec beaucoup d'entrées...")
    
    start_time = time.time()
    
    # Ajouter beaucoup d'entrées
    for i in range(100):
        key = f"perf_test_{i}"
        data = f"data_{i}" * 1000  # ~7KB par entrée
        await cache.set(key, data, priority=random.randint(1, 3))
    
    set_time = time.time() - start_time
    print(f"   Temps pour 100 SET: {set_time:.3f}s ({set_time/100*1000:.1f}ms par opération)")
    
    # Récupérer toutes les entrées
    start_time = time.time()
    
    retrieved_count = 0
    for i in range(100):
        key = f"perf_test_{i}"
        data = await cache.get(key)
        if data is not None:
            retrieved_count += 1
    
    get_time = time.time() - start_time
    print(f"   Temps pour 100 GET: {get_time:.3f}s ({get_time/100*1000:.1f}ms par opération)")
    print(f"   Entrées récupérées: {retrieved_count}/100")
    
    # Statistiques finales
    stats = cache.get_cache_stats()
    print(f"   Taux de hit: {stats['hit_rate']:.2%}")
    print(f"   Compressions: {stats['compressions']}")
    print(f"   Évictions: {stats['evictions']}")
    
    print("\n2. Test d'optimisation sous charge...")
    
    optimizer = AutoOptimizer(cache)
    
    start_time = time.time()
    result = await optimizer.run_manual_optimization()
    optimization_time = time.time() - start_time
    
    print(f"   Temps d'optimisation: {optimization_time:.3f}s")
    print(f"   Règles exécutées: {result['rules_executed']}")
    
    await optimizer.shutdown()
    print("\n✅ Test de performance terminé")

async def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests de l'optimisateur automatique\n")
    
    try:
        # Test 1: Cache intelligent
        await test_intelligent_cache_manager()
        
        # Test 2: Optimisateur automatique
        await test_auto_optimizer()
        
        # Test 3: Règle personnalisée
        await test_custom_optimization_rule()
        
        # Test 4: Fonctions globales
        await test_global_functions()
        
        # Test 5: Performance sous charge
        await test_performance_under_load()
        
        print("\n🎉 Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())