"""
Test direct de l'analyseur de performance
"""
import asyncio
import tempfile
import shutil
import time
import random
import sys
import os
import importlib.util

async def test_performance_analyzer_direct():
    """Test direct de l'analyseur de performance"""
    print("📊 Test direct de l'analyseur de performance")
    print("-" * 45)
    
    # Importer directement le module
    spec = importlib.util.spec_from_file_location(
        "performance_analyzer", 
        "ai_video_dubbing/performance/performance_analyzer.py"
    )
    analyzer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer_module)
    
    PerformanceAnalyzer = analyzer_module.PerformanceAnalyzer
    TrendDirection = analyzer_module.TrendDirection
    AlertLevel = analyzer_module.AlertLevel
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        analyzer = PerformanceAnalyzer(config_dir=temp_dir)
        
        print("📈 Enregistrement de métriques de test...")
        
        # Simuler des métriques CPU avec tendance croissante (dégradation)
        print("   Simulation CPU (tendance dégradante)...")
        for i in range(15):
            cpu_usage = 40 + i * 3 + random.uniform(-2, 2)  # Tendance croissante
            await analyzer.record_metric(
                component="system",
                metric_name="cpu_usage",
                value=cpu_usage,
                unit="%"
            )
            await asyncio.sleep(0.01)
        
        # Simuler des métriques mémoire stables
        print("   Simulation mémoire (stable)...")
        for i in range(12):
            memory_usage = 65 + random.uniform(-3, 3)  # Stable
            await analyzer.record_metric(
                component="system",
                metric_name="memory_percent",
                value=memory_usage,
                unit="%"
            )
            await asyncio.sleep(0.01)
        
        # Simuler des métriques GPU avec amélioration
        print("   Simulation GPU (amélioration)...")
        for i in range(10):
            gpu_usage = 85 - i * 2 + random.uniform(-1, 1)  # Tendance décroissante (amélioration)
            await analyzer.record_metric(
                component="gpu",
                metric_name="gpu_memory_percent",
                value=gpu_usage,
                unit="%"
            )
            await asyncio.sleep(0.01)
        
        print(f"✅ {len(analyzer.metrics_history)} métriques enregistrées")
        
        # Vérifier les alertes générées
        alerts = analyzer.get_active_alerts()
        print(f"\\n🚨 Alertes actives: {len(alerts)}")
        
        for alert in alerts[:3]:  # Afficher les 3 premières
            level_icons = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️", 
                AlertLevel.CRITICAL: "🚨"
            }
            level_icon = level_icons.get(alert.level, "❓")
            print(f"   {level_icon} {alert.message}")
            if alert.recommendations:
                print(f"      💡 {alert.recommendations[0]}")
        
        # Vérifier les analyses de tendance
        trends = analyzer.get_trend_analysis()
        print(f"\\n📈 Analyses de tendance: {len(trends)}")
        
        direction_icons = {
            TrendDirection.IMPROVING: "📈",
            TrendDirection.STABLE: "➡️",
            TrendDirection.DEGRADING: "📉",
            TrendDirection.UNKNOWN: "❓"
        }
        
        for trend_key, trend in trends.items():
            direction_icon = direction_icons.get(trend.direction, "❓")
            print(f"   {direction_icon} {trend_key}: {trend.direction.value} ({trend.change_rate:+.1f}%, confiance: {trend.confidence:.2f})")
            if trend.recommendation:
                print(f"      💡 {trend.recommendation}")
        
        # Test de génération de rapport
        print("\\n📄 Génération de rapport de performance...")
        report = await analyzer.generate_performance_report(time_window=300)  # 5 minutes
        
        print(f"✅ Rapport généré:")
        print(f"   Composants analysés: {len(report['components'])}")
        print(f"   Tendances globales: {len(report['overall_trends'])}")
        print(f"   Alertes actives: {report['active_alerts']}")
        print(f"   Recommandations: {len(report['recommendations'])}")
        
        # Afficher les détails par composant
        for component_name, component_data in report['components'].items():
            print(f"\\n   📊 {component_name}:")
            print(f"      Métriques: {len(component_data['metrics'])}")
            print(f"      Tendances: {len(component_data['trends'])}")
            
            # Afficher une métrique exemple
            for metric_name, stats in list(component_data['metrics'].items())[:1]:
                if 'mean' in stats:
                    print(f"         {metric_name}: moy={stats['mean']:.1f}, min={stats['min']:.1f}, max={stats['max']:.1f}")
        
        # Test d'apprentissage de configuration optimale
        print("\\n🧠 Test d'apprentissage de configuration optimale...")
        
        await analyzer.learn_optimal_configuration(
            component="transcription",
            configuration={"model_type": "nemo_gpu", "batch_size": 16},
            performance_score=92.5,
            system_conditions={"memory_percent": 60.0, "cuda_available": True}
        )
        
        # Récupérer la configuration optimale
        optimal_config = await analyzer.get_optimal_configuration(
            "transcription", 
            {"memory_percent": 65.0, "cuda_available": True}
        )
        
        if optimal_config:
            print(f"   ✅ Configuration optimale: {optimal_config.configuration}")
            print(f"      Score: {optimal_config.performance_score:.1f}")
        else:
            print("   ❌ Aucune configuration optimale trouvée")
        
        # Test de statistiques détaillées
        print("\\n📊 Statistiques détaillées:")
        
        stats = analyzer.get_component_statistics("system", "cpu_usage", time_window=300)
        if "error" not in stats:
            print(f"   CPU Usage:")
            print(f"      Min: {stats['min']:.1f}%, Max: {stats['max']:.1f}%")
            print(f"      Moyenne: {stats['mean']:.1f}%, Médiane: {stats['median']:.1f}%")
            print(f"      Points de données: {stats['data_points']}")
            
            if "trend" in stats:
                trend_info = stats["trend"]
                direction_icon = direction_icons.get(TrendDirection(trend_info["direction"]), "❓")
                print(f"      Tendance: {direction_icon} {trend_info['direction']} ({trend_info['change_rate']:+.1f}%)")
        
        # Test de détection de dégradation
        print("\\n🔍 Détection de dégradations:")
        degradations = await analyzer.detect_performance_degradation("system", time_window=300)
        
        if degradations:
            print(f"   {len(degradations)} dégradation(s) détectée(s):")
            for degradation in degradations:
                print(f"      📉 {degradation.metric_name}: {degradation.change_rate:+.1f}% (confiance: {degradation.confidence:.2f})")
        else:
            print("   ✅ Aucune dégradation détectée")
        
        return analyzer
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_data_persistence_direct():
    """Test de persistance des données"""
    print("\\n💾 Test de persistance des données")
    print("-" * 32)
    
    # Importer le module
    spec = importlib.util.spec_from_file_location(
        "performance_analyzer", 
        "ai_video_dubbing/performance/performance_analyzer.py"
    )
    analyzer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer_module)
    
    PerformanceAnalyzer = analyzer_module.PerformanceAnalyzer
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Premier analyseur - enregistrer des données
        print("📝 Enregistrement de données...")
        analyzer1 = PerformanceAnalyzer(config_dir=temp_dir)
        
        # Enregistrer quelques métriques
        for i in range(5):
            await analyzer1.record_metric("test_component", "test_metric", i * 20, "units")
        
        # Apprendre une configuration
        await analyzer1.learn_optimal_configuration(
            component="test_component",
            configuration={"param1": "value1", "param2": 42},
            performance_score=88.0,
            system_conditions={"memory": 55.0}
        )
        
        print(f"   Métriques: {len(analyzer1.metrics_history)}")
        print(f"   Configurations: {len(analyzer1.optimal_configurations)}")
        
        # Sauvegarder
        await analyzer1.save_historical_data()
        print("   ✅ Données sauvegardées")
        
        # Deuxième analyseur - charger les données
        print("\\n📖 Chargement de données...")
        analyzer2 = PerformanceAnalyzer(config_dir=temp_dir)
        
        print(f"   Métriques chargées: {len(analyzer2.metrics_history)}")
        print(f"   Configurations chargées: {len(analyzer2.optimal_configurations)}")
        
        # Vérifier la cohérence
        if analyzer2.metrics_history and analyzer2.optimal_configurations:
            print("   ✅ Persistance réussie")
            
            # Vérifier une métrique
            last_metric = analyzer2.metrics_history[-1]
            print(f"      Dernière métrique: {last_metric.component}.{last_metric.metric_name} = {last_metric.value}")
            
            # Vérifier une configuration
            for component, configs in analyzer2.optimal_configurations.items():
                if configs:
                    config = configs[0]
                    print(f"      Configuration {component}: score {config.performance_score:.1f}")
        else:
            print("   ❌ Problème de persistance")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_performance_analyzer_direct())
    asyncio.run(test_data_persistence_direct())
    
    print("\\n✅ Tests de l'analyseur de performance terminés")