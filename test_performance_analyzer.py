"""
Test de l'analyseur de performance avec historique et tendances
"""
import asyncio
import tempfile
import shutil
import time
import random
import json
from ai_video_dubbing.performance.performance_analyzer import (
    PerformanceAnalyzer, TrendDirection, AlertLevel
)

async def test_performance_analyzer_basic():
    """Test basique de l'analyseur de performance"""
    print("📊 Test basique de l'analyseur de performance")
    print("-" * 45)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        analyzer = PerformanceAnalyzer(config_dir=temp_dir)
        
        print("📈 Enregistrement de métriques de test...")
        
        # Simuler des métriques de performance sur une période
        base_time = time.time() - 3600  # Il y a 1 heure
        
        # Métriques CPU avec tendance croissante (dégradation)
        for i in range(20):
            cpu_usage = 30 + i * 2 + random.uniform(-5, 5)  # Tendance croissante
            await analyzer.record_metric(
                component="system",
                metric_name="cpu_usage",
                value=cpu_usage,
                unit="%",
                metadata={"process_count": 50 + i}
            )
            
            # Simuler le passage du temps
            await asyncio.sleep(0.01)
        
        # Métriques mémoire avec tendance stable
        for i in range(15):
            memory_usage = 60 + random.uniform(-3, 3)  # Stable autour de 60%
            await analyzer.record_metric(
                component="system",
                metric_name="memory_percent",
                value=memory_usage,
                unit="%"
            )
            await asyncio.sleep(0.01)
        
        # Métriques GPU avec pic puis amélioration
        for i in range(10):
            if i < 5:
                gpu_usage = 90 + random.uniform(-2, 2)  # Pic élevé
            else:
                gpu_usage = 70 - (i-5) * 3 + random.uniform(-2, 2)  # Amélioration
            
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
        print(f"🚨 Alertes actives: {len(alerts)}")
        
        for alert in alerts[:3]:  # Afficher les 3 premières
            level_icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}[alert.level.value]
            print(f"   {level_icon} {alert.message}")
            if alert.recommendations:
                print(f"      💡 {alert.recommendations[0]}")
        
        # Vérifier les analyses de tendance
        trends = analyzer.get_trend_analysis()
        print(f"📈 Analyses de tendance: {len(trends)}")
        
        for trend_key, trend in trends.items():
            direction_icon = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.STABLE: "➡️",
                TrendDirection.DEGRADING: "📉",
                TrendDirection.UNKNOWN: "❓"
            }[trend.direction]
            
            print(f"   {direction_icon} {trend_key}: {trend.direction.value} ({trend.change_rate:+.1f}%, confiance: {trend.confidence:.2f})")
            if trend.recommendation:
                print(f"      💡 {trend.recommendation}")
        
        return analyzer
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_optimal_configuration_learning():
    """Test de l'apprentissage de configurations optimales"""
    print("\\n🧠 Test de l'apprentissage de configurations optimales")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        analyzer = PerformanceAnalyzer(config_dir=temp_dir)
        
        print("📚 Apprentissage de configurations optimales...")
        
        # Simuler différentes configurations et leurs performances
        configurations = [
            {
                "model_type": "nemo_gpu",
                "batch_size": 16,
                "precision": "fp16"
            },
            {
                "model_type": "nemo_gpu", 
                "batch_size": 8,
                "precision": "fp32"
            },
            {
                "model_type": "whisper_cpu",
                "batch_size": 4,
                "precision": "fp32"
            }
        ]
        
        system_conditions = [
            {
                "memory_percent": 45.0,
                "gpu_memory_percent": 30.0,
                "cuda_available": True
            },
            {
                "memory_percent": 70.0,
                "gpu_memory_percent": 80.0,
                "cuda_available": True
            },
            {
                "memory_percent": 60.0,
                "gpu_memory_percent": 0.0,
                "cuda_available": False
            }
        ]
        
        performance_scores = [95.0, 85.0, 70.0]
        
        # Apprendre les configurations
        for i, (config, conditions, score) in enumerate(zip(configurations, system_conditions, performance_scores)):
            await analyzer.learn_optimal_configuration(
                component="transcription",
                configuration=config,
                performance_score=score,
                system_conditions=conditions
            )
            
            print(f"   ✅ Configuration {i+1}: {config['model_type']} (score: {score})")
        
        # Tester la récupération de configuration optimale
        print("\\n🔍 Test de récupération de configuration optimale...")
        
        test_conditions = {
            "memory_percent": 50.0,
            "gpu_memory_percent": 40.0,
            "cuda_available": True
        }
        
        optimal_config = await analyzer.get_optimal_configuration("transcription", test_conditions)
        
        if optimal_config:
            print(f"   ✅ Configuration optimale trouvée:")
            print(f"      Modèle: {optimal_config.configuration['model_type']}")
            print(f"      Score: {optimal_config.performance_score:.1f}")
            print(f"      Utilisations: {optimal_config.usage_count}")
        else:
            print("   ❌ Aucune configuration optimale trouvée")
        
        # Afficher toutes les configurations apprises
        print("\\n📋 Configurations apprises:")
        for component, configs in analyzer.optimal_configurations.items():
            print(f"   {component}: {len(configs)} configuration(s)")
            for config in configs:
                print(f"      - {config.configuration['model_type']}: {config.performance_score:.1f} (×{config.usage_count})")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_performance_report_generation():
    """Test de génération de rapport de performance"""
    print("\\n📄 Test de génération de rapport de performance")
    print("-" * 45)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        analyzer = PerformanceAnalyzer(config_dir=temp_dir)
        
        print("📊 Génération de données de test...")
        
        # Générer des données de test variées
        components = ["system", "gpu", "memory", "network"]
        metrics = {
            "system": ["cpu_usage", "load_average"],
            "gpu": ["gpu_memory_percent", "gpu_utilization"],
            "memory": ["memory_percent", "swap_usage"],
            "network": ["response_time", "bandwidth_usage"]
        }
        
        # Générer 50 points de données sur les dernières "heures"
        for i in range(50):
            for component in components:
                for metric in metrics[component]:
                    # Simuler différents patterns
                    if metric == "cpu_usage":
                        value = 40 + i * 0.5 + random.uniform(-10, 10)  # Tendance croissante
                    elif metric == "memory_percent":
                        value = 65 + random.uniform(-5, 5)  # Stable
                    elif metric == "response_time":
                        value = 2.0 + random.uniform(-0.5, 1.5)  # Variable
                    else:
                        value = 50 + random.uniform(-20, 20)  # Aléatoire
                    
                    await analyzer.record_metric(
                        component=component,
                        metric_name=metric,
                        value=max(0, min(100, value)),  # Limiter entre 0-100
                        unit="%" if "percent" in metric else ("s" if "time" in metric else "")
                    )
            
            await asyncio.sleep(0.001)  # Petite pause
        
        print("📈 Génération du rapport de performance...")
        
        # Générer le rapport
        report = await analyzer.generate_performance_report(time_window=3600)  # 1 heure
        
        print(f"✅ Rapport généré:")
        print(f"   Période: {report['time_window_hours']:.1f} heures")
        print(f"   Composants analysés: {len(report['components'])}")
        print(f"   Tendances globales: {len(report['overall_trends'])}")
        print(f"   Alertes actives: {report['active_alerts']}")
        print(f"   Recommandations: {len(report['recommendations'])}")
        
        # Afficher les détails par composant
        print("\\n🔧 Détails par composant:")
        for component_name, component_data in report['components'].items():
            print(f"   {component_name}:")
            print(f"      Métriques: {len(component_data['metrics'])}")
            print(f"      Tendances: {len(component_data['trends'])}")
            print(f"      Alertes: {len(component_data['alerts'])}")
            
            # Afficher quelques métriques
            for metric_name, stats in list(component_data['metrics'].items())[:2]:
                if 'mean' in stats:
                    print(f"         {metric_name}: moy={stats['mean']:.1f}, min={stats['min']:.1f}, max={stats['max']:.1f}")
        
        # Afficher les tendances importantes
        if report['overall_trends']:
            print("\\n📈 Tendances importantes:")
            for trend in report['overall_trends'][:3]:
                direction_icon = {"improving": "📈", "stable": "➡️", "degrading": "📉"}[trend['direction']]
                print(f"   {direction_icon} {trend['metric']}: {trend['direction']} ({trend['change_rate']:+.1f}%)")
        
        # Afficher les recommandations
        if report['recommendations']:
            print("\\n💡 Recommandations:")
            for rec in report['recommendations'][:3]:
                print(f"   - {rec}")
        
        return report
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_trend_detection():
    """Test de détection de tendances"""
    print("\\n📈 Test de détection de tendances")
    print("-" * 32)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        analyzer = PerformanceAnalyzer(config_dir=temp_dir)
        
        print("📊 Simulation de différents patterns de tendance...")
        
        # Pattern 1: Dégradation claire
        print("   Pattern 1: Dégradation CPU")
        for i in range(15):
            cpu_value = 30 + i * 3 + random.uniform(-2, 2)  # Augmentation claire
            await analyzer.record_metric("system", "cpu_usage", cpu_value, "%")
            await asyncio.sleep(0.01)
        
        # Pattern 2: Amélioration
        print("   Pattern 2: Amélioration mémoire")
        for i in range(12):
            memory_value = 90 - i * 2 + random.uniform(-1, 1)  # Diminution claire
            await analyzer.record_metric("system", "memory_percent", memory_value, "%")
            await asyncio.sleep(0.01)
        
        # Pattern 3: Stable avec bruit
        print("   Pattern 3: Réseau stable")
        for i in range(20):
            response_time = 2.5 + random.uniform(-0.3, 0.3)  # Stable
            await analyzer.record_metric("network", "response_time", response_time, "s")
            await asyncio.sleep(0.01)
        
        # Analyser les tendances détectées
        print("\\n🔍 Analyse des tendances détectées:")
        
        # Détecter les dégradations
        degradations = await analyzer.detect_performance_degradation("system", time_window=300)
        
        print(f"   Dégradations détectées: {len(degradations)}")
        for degradation in degradations:
            print(f"      📉 {degradation.metric_name}: {degradation.change_rate:+.1f}% (confiance: {degradation.confidence:.2f})")
        
        # Vérifier toutes les tendances
        all_trends = analyzer.get_trend_analysis()
        print(f"\\n   Toutes les tendances: {len(all_trends)}")
        
        for trend_key, trend in all_trends.items():
            direction_icon = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.STABLE: "➡️", 
                TrendDirection.DEGRADING: "📉",
                TrendDirection.UNKNOWN: "❓"
            }[trend.direction]
            
            print(f"      {direction_icon} {trend_key}: {trend.change_rate:+.1f}% sur {trend.time_period:.0f}s")
        
        # Test des statistiques détaillées
        print("\\n📊 Statistiques détaillées:")
        
        stats = analyzer.get_component_statistics("system", "cpu_usage", time_window=300)
        if "error" not in stats:
            print(f"   CPU Usage - Min: {stats['min']:.1f}%, Max: {stats['max']:.1f}%, Moyenne: {stats['mean']:.1f}%")
            if "trend" in stats:
                print(f"   Tendance: {stats['trend']['direction']} ({stats['trend']['change_rate']:+.1f}%)")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_data_persistence():
    """Test de la persistance des données"""
    print("\\n💾 Test de la persistance des données")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Premier analyseur - enregistrer des données
        print("📝 Enregistrement de données...")
        analyzer1 = PerformanceAnalyzer(config_dir=temp_dir)
        
        # Enregistrer quelques métriques
        for i in range(10):
            await analyzer1.record_metric("test_component", "test_metric", i * 10, "units")
        
        # Apprendre une configuration
        await analyzer1.learn_optimal_configuration(
            component="test_component",
            configuration={"param1": "value1", "param2": 42},
            performance_score=85.0,
            system_conditions={"memory": 50.0}
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
        
        # Vérifier que les données sont identiques
        if (len(analyzer1.metrics_history) == len(analyzer2.metrics_history) and
            len(analyzer1.optimal_configurations) == len(analyzer2.optimal_configurations)):
            print("   ✅ Persistance réussie")
        else:
            print("   ❌ Problème de persistance")
        
        # Test de nettoyage
        print("\\n🧹 Test de nettoyage des anciennes données...")
        
        # Ajouter des données "anciennes" (simulées)
        old_time = time.time() - 10 * 24 * 3600  # Il y a 10 jours
        for i in range(5):
            old_metric = analyzer2.metrics_history[0]  # Copier une métrique existante
            old_metric.timestamp = old_time + i
            analyzer2.metrics_history.insert(0, old_metric)
        
        print(f"   Métriques avant nettoyage: {len(analyzer2.metrics_history)}")
        
        await analyzer2.cleanup_old_data()
        
        print(f"   Métriques après nettoyage: {len(analyzer2.metrics_history)}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_performance_analyzer_basic())
    asyncio.run(test_optimal_configuration_learning())
    asyncio.run(test_performance_report_generation())
    asyncio.run(test_trend_detection())
    asyncio.run(test_data_persistence())
    
    print("\\n✅ Tous les tests de l'analyseur de performance terminés")