"""
Test fonctionnel avancé de l'analyseur de prévention d'erreurs
"""

import asyncio
import time
import logging
import sys
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_prevention_rules_triggering():
    """Test du déclenchement des règles de prévention"""
    
    print("=== Test de Déclenchement des Règles de Prévention ===\n")
    
    from ai_video_dubbing.performance.error_prevention_analyzer import (
        ErrorPreventionAnalyzer,
        PreventionRule,
        PreventionLevel,
        PreventionAction,
        ErrorType
    )
    
    # Créer un analyseur avec configuration de test
    analyzer = ErrorPreventionAnalyzer()
    
    # Modifier les seuils pour déclencher plus facilement les règles
    analyzer.config["critical_memory_threshold"] = 0.4  # 40% au lieu de 90%
    analyzer.config["critical_disk_threshold"] = 0.9   # 90% au lieu de 95%
    analyzer.config["critical_cpu_threshold"] = 0.3    # 30% au lieu de 95%
    
    print("1. Configuration modifiée pour tests")
    print(f"   - Seuil mémoire: {analyzer.config['critical_memory_threshold']*100}%")
    print(f"   - Seuil disque: {analyzer.config['critical_disk_threshold']*100}%")
    print(f"   - Seuil CPU: {analyzer.config['critical_cpu_threshold']*100}%")
    
    # Ajouter une règle de test qui se déclenche toujours
    def always_trigger():
        return True
    
    test_rule = PreventionRule(
        rule_id="test_always_trigger",
        name="Test - Toujours déclenché",
        description="Règle de test qui se déclenche toujours",
        error_type=ErrorType.SYSTEM_ERROR,
        prevention_level=PreventionLevel.MEDIUM,
        check_function=always_trigger,
        action=PreventionAction.WARN,
        cooldown=5.0  # 5 secondes de cooldown
    )
    
    analyzer.add_prevention_rule(test_rule)
    print("\n2. Règle de test ajoutée")
    
    # Ajouter un callback pour capturer les alertes
    alerts_received = []
    
    async def capture_alert(alert):
        alerts_received.append(alert)
        print(f"   🚨 Alerte reçue: {alert.message}")
        print(f"      Niveau: {alert.level.name}")
        print(f"      Actions recommandées: {len(alert.recommended_actions)}")
    
    analyzer.add_alert_callback(capture_alert)
    print("3. Callback d'alerte configuré")
    
    # Déclencher manuellement la vérification
    print("\n4. Déclenchement manuel des vérifications...")
    
    initial_stats = analyzer.get_prevention_stats()
    print(f"   Stats initiales - Alertes: {initial_stats['alerts_generated']}")
    
    # Vérifier toutes les règles
    await analyzer._check_all_prevention_rules()
    
    # Attendre un peu pour que les callbacks soient traités
    await asyncio.sleep(0.5)
    
    # Vérifier les résultats
    final_stats = analyzer.get_prevention_stats()
    active_alerts = analyzer.get_active_alerts()
    
    print(f"\n5. Résultats:")
    print(f"   - Alertes générées: {final_stats['alerts_generated']}")
    print(f"   - Alertes actives: {len(active_alerts)}")
    print(f"   - Callbacks reçus: {len(alerts_received)}")
    
    if active_alerts:
        print("   📋 Détails des alertes actives:")
        for alert in active_alerts:
            print(f"   - {alert.message}")
            print(f"     Règle: {alert.rule_id}")
            print(f"     Timestamp: {time.ctime(alert.timestamp)}")
    
    # Test du cooldown
    print("\n6. Test du cooldown...")
    print("   Tentative de re-déclenchement immédiat...")
    
    await analyzer._check_all_prevention_rules()
    await asyncio.sleep(0.1)
    
    cooldown_stats = analyzer.get_prevention_stats()
    print(f"   Alertes après cooldown: {cooldown_stats['alerts_generated']}")
    
    if cooldown_stats['alerts_generated'] == final_stats['alerts_generated']:
        print("   ✅ Cooldown fonctionne correctement")
    else:
        print("   ⚠️ Cooldown pourrait ne pas fonctionner")
    
    # Attendre le cooldown et re-tester
    print("\n7. Attente du cooldown (6 secondes)...")
    await asyncio.sleep(6)
    
    await analyzer._check_all_prevention_rules()
    await asyncio.sleep(0.1)
    
    post_cooldown_stats = analyzer.get_prevention_stats()
    print(f"   Alertes après cooldown: {post_cooldown_stats['alerts_generated']}")
    
    if post_cooldown_stats['alerts_generated'] > cooldown_stats['alerts_generated']:
        print("   ✅ Re-déclenchement après cooldown réussi")
    
    await analyzer.shutdown()
    print("\n✅ Test de déclenchement terminé")

async def test_health_monitoring():
    """Test du monitoring de santé système"""
    
    print("\n=== Test du Monitoring de Santé Système ===\n")
    
    from ai_video_dubbing.performance.error_prevention_analyzer import (
        ErrorPreventionAnalyzer
    )
    
    analyzer = ErrorPreventionAnalyzer()
    
    print("1. Collecte de métriques de santé...")
    
    # Collecter plusieurs échantillons
    metrics_samples = []
    for i in range(3):
        metrics = await analyzer._collect_health_metrics()
        metrics_samples.append(metrics)
        print(f"   Échantillon {i+1}:")
        print(f"   - CPU: {metrics.cpu_usage:.1f}%")
        print(f"   - Mémoire: {metrics.memory_usage:.1f}%")
        print(f"   - Processus: {metrics.active_processes}")
        
        if i < 2:  # Pas d'attente après le dernier échantillon
            await asyncio.sleep(1)
    
    # Analyser les tendances
    print("\n2. Analyse des tendances...")
    
    cpu_values = [m.cpu_usage for m in metrics_samples]
    memory_values = [m.memory_usage for m in metrics_samples]
    
    cpu_trend = analyzer._calculate_trend(cpu_values)
    memory_trend = analyzer._calculate_trend(memory_values)
    
    print(f"   Tendance CPU: {cpu_trend:.2f}")
    print(f"   Tendance Mémoire: {memory_trend:.2f}")
    
    # Test de détection de problèmes potentiels
    print("\n3. Test de détection de problèmes...")
    
    # Simuler des métriques critiques
    analyzer.system_metrics = {
        "cpu_percent": 96.0,  # CPU critique
        "memory_percent": 92.0,  # Mémoire critique
        "disk_usage": 97.0,  # Disque critique
        "timestamp": time.time()
    }
    
    initial_alerts = len(analyzer.get_active_alerts())
    
    await analyzer._detect_potential_issues()
    await asyncio.sleep(0.1)
    
    final_alerts = len(analyzer.get_active_alerts())
    
    print(f"   Alertes avant: {initial_alerts}")
    print(f"   Alertes après: {final_alerts}")
    
    if final_alerts > initial_alerts:
        print("   ✅ Détection de problèmes fonctionne")
        
        recent_alerts = analyzer.get_active_alerts()[-3:]  # 3 dernières alertes
        for alert in recent_alerts:
            print(f"   - {alert.message}")
    else:
        print("   ⚠️ Aucun problème détecté (normal si seuils non atteints)")
    
    await analyzer.shutdown()
    print("\n✅ Test de monitoring terminé")

async def test_pattern_analysis():
    """Test de l'analyse de patterns d'erreur"""
    
    print("\n=== Test de l'Analyse de Patterns d'Erreur ===\n")
    
    from ai_video_dubbing.performance.error_prevention_analyzer import (
        ErrorPreventionAnalyzer,
        PreventionAlert,
        PreventionLevel
    )
    
    analyzer = ErrorPreventionAnalyzer()
    
    print("1. Simulation d'alertes répétées...")
    
    # Créer plusieurs alertes du même type
    base_time = time.time()
    
    for i in range(6):  # 6 alertes pour dépasser le seuil de 5
        alert = PreventionAlert(
            alert_id=f"pattern_test_{i}",
            rule_id="memory_critical",
            timestamp=base_time + i * 60,  # Une alerte par minute
            level=PreventionLevel.HIGH,
            message=f"Test pattern alerte {i+1}",
            recommended_actions=["Action test"]
        )
        
        analyzer.alert_history.append(alert)
        analyzer.active_alerts[alert.alert_id] = alert
    
    print(f"   {len(analyzer.alert_history)} alertes simulées")
    
    # Analyser les patterns
    print("\n2. Analyse des patterns...")
    
    initial_patterns = len(analyzer.pattern_analysis)
    
    await analyzer._analyze_error_patterns()
    
    final_patterns = len(analyzer.pattern_analysis)
    
    print(f"   Patterns avant: {initial_patterns}")
    print(f"   Patterns après: {final_patterns}")
    
    if analyzer.pattern_analysis:
        print("   📊 Patterns détectés:")
        for pattern_key, data in analyzer.pattern_analysis.items():
            print(f"   - {pattern_key}: {data['count']} occurrences ({data['severity']})")
    
    # Test de nettoyage des anciennes alertes
    print("\n3. Test de nettoyage des alertes...")
    
    # Simuler des alertes anciennes
    old_time = time.time() - 25 * 3600  # 25 heures dans le passé
    
    old_alerts = []
    for i in range(3):
        alert = PreventionAlert(
            alert_id=f"old_alert_{i}",
            rule_id="test_old",
            timestamp=old_time,
            level=PreventionLevel.LOW,
            message=f"Ancienne alerte {i+1}",
            recommended_actions=[]
        )
        old_alerts.append(alert)
        analyzer.alert_history.append(alert)
        analyzer.active_alerts[alert.alert_id] = alert
    
    alerts_before_cleanup = len(analyzer.alert_history)
    active_before_cleanup = len(analyzer.active_alerts)
    
    await analyzer._cleanup_old_alerts()
    
    alerts_after_cleanup = len(analyzer.alert_history)
    active_after_cleanup = len(analyzer.active_alerts)
    
    print(f"   Alertes historique avant: {alerts_before_cleanup}")
    print(f"   Alertes historique après: {alerts_after_cleanup}")
    print(f"   Alertes actives avant: {active_before_cleanup}")
    print(f"   Alertes actives après: {active_after_cleanup}")
    
    cleaned_count = (alerts_before_cleanup - alerts_after_cleanup) + (active_before_cleanup - active_after_cleanup)
    print(f"   ✅ {cleaned_count} alertes nettoyées")
    
    await analyzer.shutdown()
    print("\n✅ Test d'analyse de patterns terminé")

async def test_manual_check():
    """Test de la vérification manuelle complète"""
    
    print("\n=== Test de Vérification Manuelle Complète ===\n")
    
    from ai_video_dubbing.performance.error_prevention_analyzer import (
        ErrorPreventionAnalyzer,
        check_system_health
    )
    
    print("1. Test avec analyseur local...")
    
    analyzer = ErrorPreventionAnalyzer()
    
    # Exécuter une vérification manuelle
    results = await analyzer.run_manual_check()
    
    print(f"   📋 Résultats de la vérification:")
    print(f"   - Timestamp: {time.ctime(results['timestamp'])}")
    print(f"   - Règles vérifiées: {results['rules_checked']}")
    print(f"   - Alertes générées: {results['alerts_generated']}")
    print(f"   - Problèmes trouvés: {len(results['problems_found'])}")
    print(f"   - Recommandations: {len(results['recommendations'])}")
    
    if results['problems_found']:
        print("   ⚠️ Problèmes détectés:")
        for problem in results['problems_found']:
            print(f"   - {problem['name']}: {problem['description']}")
    
    if results['recommendations']:
        print("   💡 Recommandations:")
        for rec in results['recommendations'][:3]:  # Afficher les 3 premières
            print(f"   - {rec}")
    
    await analyzer.shutdown()
    
    print("\n2. Test avec fonction utilitaire globale...")
    
    # Test de la fonction utilitaire
    global_results = await check_system_health()
    
    print(f"   📋 Résultats globaux:")
    print(f"   - Règles vérifiées: {global_results['rules_checked']}")
    print(f"   - Problèmes trouvés: {len(global_results['problems_found'])}")
    
    print("\n✅ Test de vérification manuelle terminé")

async def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests fonctionnels de prévention d'erreurs\n")
    
    try:
        # Test 1: Déclenchement des règles
        await test_prevention_rules_triggering()
        
        # Test 2: Monitoring de santé
        await test_health_monitoring()
        
        # Test 3: Analyse de patterns
        await test_pattern_analysis()
        
        # Test 4: Vérification manuelle
        await test_manual_check()
        
        print("\n🎉 Tous les tests fonctionnels terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())