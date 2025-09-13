"""
Test de l'analyseur de prévention d'erreurs
"""

import asyncio
import time
import logging
from ai_video_dubbing.performance.error_prevention_analyzer import (
    ErrorPreventionAnalyzer,
    PreventionRule,
    PreventionLevel,
    PreventionAction,
    ErrorType,
    get_error_prevention_analyzer,
    check_system_health,
    add_custom_prevention_rule
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_error_prevention_analyzer():
    """Test complet de l'analyseur de prévention d'erreurs"""
    
    print("=== Test de l'Analyseur de Prévention d'Erreurs ===\n")
    
    # 1. Test d'initialisation
    print("1. Test d'initialisation...")
    analyzer = ErrorPreventionAnalyzer()
    
    # Vérifier que les règles par défaut sont chargées
    rules = analyzer.prevention_rules
    print(f"   Règles de prévention chargées: {len(rules)}")
    for rule_id, rule in rules.items():
        print(f"   - {rule.name} ({rule.prevention_level.name})")
    
    # 2. Test de collecte de métriques de santé
    print("\n2. Test de collecte de métriques...")
    health_metrics = await analyzer._collect_health_metrics()
    print(f"   CPU: {health_metrics.cpu_usage:.1f}%")
    print(f"   Mémoire: {health_metrics.memory_usage:.1f}%")
    print(f"   Disque: {health_metrics.disk_usage:.1f}%")
    print(f"   Processus actifs: {health_metrics.active_processes}")
    print(f"   Mémoire disponible: {health_metrics.available_memory_mb:.0f} MB")
    
    # 3. Test de vérification manuelle
    print("\n3. Test de vérification manuelle...")
    check_results = await analyzer.run_manual_check()
    print(f"   Règles vérifiées: {check_results['rules_checked']}")
    print(f"   Alertes générées: {check_results['alerts_generated']}")
    print(f"   Problèmes trouvés: {len(check_results['problems_found'])}")
    
    if check_results['problems_found']:
        print("   Problèmes détectés:")
        for problem in check_results['problems_found']:
            print(f"   - {problem['name']}: {problem['description']}")
    
    # 4. Test d'ajout de règle personnalisée
    print("\n4. Test d'ajout de règle personnalisée...")
    
    def check_test_condition():
        """Condition de test qui retourne toujours True"""
        return True
    
    await add_custom_prevention_rule(
        rule_id="test_rule",
        name="Règle de test",
        description="Règle de test pour démonstration",
        error_type=ErrorType.SYSTEM_ERROR,
        check_function=check_test_condition,
        prevention_level=PreventionLevel.LOW,
        action=PreventionAction.WARN
    )
    
    print("   Règle personnalisée ajoutée avec succès")
    
    # 5. Test de déclenchement d'alerte
    print("\n5. Test de déclenchement d'alerte...")
    
    # Forcer une vérification qui devrait déclencher notre règle de test
    test_rule = analyzer.prevention_rules["test_rule"]
    await analyzer._trigger_prevention_rule(test_rule)
    
    # Vérifier les alertes actives
    active_alerts = analyzer.get_active_alerts()
    print(f"   Alertes actives: {len(active_alerts)}")
    
    if active_alerts:
        for alert in active_alerts:
            print(f"   - {alert.message} (Niveau: {alert.level.name})")
            print(f"     Actions recommandées: {len(alert.recommended_actions)}")
    
    # 6. Test des statistiques
    print("\n6. Test des statistiques...")
    stats = analyzer.get_prevention_stats()
    print(f"   Alertes générées: {stats['alerts_generated']}")
    print(f"   Problèmes prévenus: {stats['problems_prevented']}")
    print(f"   Optimisations automatiques: {stats['automatic_optimizations']}")
    
    # 7. Test de l'historique des alertes
    print("\n7. Test de l'historique des alertes...")
    alert_history = analyzer.get_alert_history(limit=5)
    print(f"   Alertes dans l'historique: {len(alert_history)}")
    
    # 8. Test de la fonction utilitaire globale
    print("\n8. Test de la fonction de vérification globale...")
    global_check = await check_system_health()
    print(f"   Vérification globale - Règles: {global_check['rules_checked']}")
    print(f"   Problèmes trouvés: {len(global_check['problems_found'])}")
    
    # 9. Test des callbacks d'alerte
    print("\n9. Test des callbacks d'alerte...")
    
    alert_received = []
    
    async def test_alert_callback(alert):
        """Callback de test pour les alertes"""
        alert_received.append(alert)
        print(f"   Callback d'alerte reçu: {alert.message}")
    
    analyzer.add_alert_callback(test_alert_callback)
    
    # Déclencher une nouvelle alerte pour tester le callback
    def another_test_condition():
        return True
    
    callback_rule = PreventionRule(
        rule_id="callback_test",
        name="Test callback",
        description="Test du système de callback",
        error_type=ErrorType.SYSTEM_ERROR,
        prevention_level=PreventionLevel.MEDIUM,
        check_function=another_test_condition,
        action=PreventionAction.WARN
    )
    
    analyzer.add_prevention_rule(callback_rule)
    await analyzer._trigger_prevention_rule(callback_rule)
    
    # Attendre un peu pour que le callback soit traité
    await asyncio.sleep(0.1)
    
    print(f"   Callbacks reçus: {len(alert_received)}")
    
    # 10. Test de nettoyage
    print("\n10. Test de nettoyage...")
    
    # Simuler des alertes anciennes
    old_time = time.time() - 25 * 3600  # 25 heures dans le passé
    for alert in analyzer.alert_history:
        alert.timestamp = old_time
    
    await analyzer._cleanup_old_alerts()
    remaining_alerts = len(analyzer.get_alert_history())
    print(f"   Alertes restantes après nettoyage: {remaining_alerts}")
    
    print("\n=== Test terminé avec succès ===")
    
    # Arrêter proprement l'analyseur
    await analyzer.shutdown()

async def test_integration_with_error_recovery():
    """Test d'intégration avec le gestionnaire de récupération d'erreurs"""
    
    print("\n=== Test d'Intégration avec la Récupération d'Erreurs ===\n")
    
    from ai_video_dubbing.performance.error_recovery_manager import (
        get_error_recovery_manager,
        create_error_context,
        ErrorType,
        ErrorSeverity
    )
    
    # Initialiser les deux systèmes
    prevention_analyzer = get_error_prevention_analyzer()
    recovery_manager = get_error_recovery_manager()
    
    print("1. Systèmes initialisés")
    
    # Créer un contexte d'erreur simulé
    error_context = create_error_context(
        error_type=ErrorType.MEMORY_ERROR,
        error_message="Mémoire insuffisante détectée",
        component="test_integration",
        severity=ErrorSeverity.HIGH,
        metadata={"test": True}
    )
    
    print("2. Contexte d'erreur créé")
    
    # Traiter l'erreur avec le gestionnaire de récupération
    recovery_result = await recovery_manager.handle_error(error_context)
    
    if recovery_result:
        print(f"3. Récupération tentée: {recovery_result.success}")
        print(f"   Stratégie utilisée: {recovery_result.strategy_used.value}")
        print(f"   Durée: {recovery_result.duration:.2f}s")
    else:
        print("3. Aucune récupération tentée")
    
    # Vérifier les métriques des deux systèmes
    recovery_stats = recovery_manager.get_error_stats()
    prevention_stats = prevention_analyzer.get_prevention_stats()
    
    print(f"4. Stats récupération - Erreurs mémoire: {recovery_stats.get('memory_error', {}).get('count', 0)}")
    print(f"   Stats prévention - Alertes: {prevention_stats['alerts_generated']}")
    
    # Arrêter les systèmes
    await prevention_analyzer.shutdown()
    await recovery_manager.shutdown()
    
    print("\n=== Test d'intégration terminé ===")

async def main():
    """Fonction principale de test"""
    
    try:
        # Test principal de l'analyseur de prévention
        await test_error_prevention_analyzer()
        
        # Test d'intégration
        await test_integration_with_error_recovery()
        
        print("\n✅ Tous les tests sont passés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())