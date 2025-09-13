"""
Test simple du moteur de diagnostic (sans dépendances)
"""
import asyncio
import tempfile
import shutil
import sys
import os

# Ajouter le chemin pour importer directement
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_video_dubbing', 'performance'))

from diagnostic_engine import DiagnosticEngine, DiagnosticSeverity, ComponentStatus

async def test_diagnostic_engine_simple():
    """Test simple du moteur de diagnostic"""
    print("🔍 Test simple du moteur de diagnostic")
    print("-" * 40)
    
    # Créer un répertoire temporaire pour les tests
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        print("🚀 Lancement du diagnostic complet...")
        report = await engine.run_full_diagnostic()
        
        print(f"📊 Résultats du diagnostic:")
        print(f"   Score de santé global: {report.overall_health_score:.1f}%")
        print(f"   Composants diagnostiqués: {len(report.component_diagnostics)}")
        print(f"   Problèmes critiques: {len(report.critical_issues)}")
        print(f"   Recommandations: {len(report.recommendations)}")
        print(f"   Goulots d'étranglement: {len(report.performance_bottlenecks)}")
        
        # Afficher les détails par composant
        print("\\n🔧 Détails par composant:")
        for component_name, diagnostic in report.component_diagnostics.items():
            status_icon = {
                ComponentStatus.HEALTHY: "✅",
                ComponentStatus.DEGRADED: "⚠️",
                ComponentStatus.FAILED: "❌",
                ComponentStatus.UNKNOWN: "❓"
            }.get(diagnostic.status, "❓")
            
            print(f"   {status_icon} {component_name}: {diagnostic.health_score:.1f}% ({diagnostic.status.value})")
            
            if diagnostic.issues:
                for issue in diagnostic.issues[:2]:  # Afficher max 2 problèmes
                    severity_icon = {
                        DiagnosticSeverity.INFO: "ℹ️",
                        DiagnosticSeverity.WARNING: "⚠️",
                        DiagnosticSeverity.ERROR: "❌",
                        DiagnosticSeverity.CRITICAL: "🚨"
                    }.get(issue.severity, "❓")
                    print(f"      {severity_icon} {issue.message}")
                    
                    # Afficher les recommandations pour ce problème
                    if issue.recommendations:
                        for rec in issue.recommendations[:2]:
                            print(f"        💡 {rec}")
        
        # Afficher les recommandations globales
        if report.recommendations:
            print("\\n💡 Recommandations globales:")
            for rec in report.recommendations:
                print(f"   - {rec}")
        
        # Afficher les goulots d'étranglement
        if report.performance_bottlenecks:
            print("\\n🚧 Goulots d'étranglement identifiés:")
            for bottleneck in report.performance_bottlenecks:
                print(f"   - {bottleneck}")
        
        # Informations système
        print("\\n🖥️ Informations système:")
        sys_info = report.system_info
        if 'error' not in sys_info:
            print(f"   Système: {sys_info.get('system', 'Unknown')} {sys_info.get('release', '')}")
            print(f"   Processeur: {sys_info.get('processor', 'Unknown')}")
            print(f"   Mémoire totale: {sys_info.get('total_memory', 0) / (1024**3):.1f} GB")
            print(f"   Utilisation mémoire: {sys_info.get('memory_percent', 0):.1f}%")
            print(f"   Espace disque: {sys_info.get('disk_percent', 0):.1f}% utilisé")
        else:
            print(f"   ❌ Erreur lors de la collecte: {sys_info['error']}")
        
        return report
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_quick_health_check():
    """Test de la vérification rapide de santé"""
    print("\\n⚡ Test de vérification rapide de santé")
    print("-" * 40)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        print("🏃 Lancement de la vérification rapide...")
        quick_results = await engine.quick_health_check()
        
        print(f"📈 Score global rapide: {quick_results['overall_health_score']:.1f}%")
        print("🔧 Composants vérifiés:")
        
        for component, result in quick_results['components'].items():
            if 'error' in result:
                print(f"   ❌ {component}: Erreur - {result['error']}")
            else:
                status_icon = "✅" if result['health_score'] > 80 else "⚠️" if result['health_score'] > 60 else "❌"
                print(f"   {status_icon} {component}: {result['health_score']:.1f}% ({result['status']})")
                if result.get('critical_issues', 0) > 0:
                    print(f"      🚨 {result['critical_issues']} problème(s) critique(s)")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_individual_components():
    """Test des diagnostics individuels"""
    print("\\n🧩 Test des diagnostics individuels")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        # Tester quelques composants spécifiques
        test_components = ["system", "memory", "storage", "network"]
        
        for component_name in test_components:
            if component_name in engine.components:
                print(f"\\n🔍 Test du composant: {component_name}")
                
                try:
                    diagnostic_func = engine.components[component_name]
                    diagnostic = await diagnostic_func()
                    
                    print(f"   Statut: {diagnostic.status.value}")
                    print(f"   Score: {diagnostic.health_score:.1f}%")
                    print(f"   Problèmes: {len(diagnostic.issues)}")
                    print(f"   Métriques: {len(diagnostic.metrics)}")
                    
                    # Afficher quelques métriques intéressantes
                    interesting_metrics = {
                        "system": ["cpu_usage", "cpu_temperature"],
                        "memory": ["memory_percent", "available_memory"],
                        "storage": ["disk_percent", "free_disk"],
                        "network": ["dns_resolution", "http_connectivity"]
                    }
                    
                    if component_name in interesting_metrics:
                        print("   Métriques clés:")
                        for metric in interesting_metrics[component_name]:
                            if metric in diagnostic.metrics:
                                value = diagnostic.metrics[metric]
                                if isinstance(value, float):
                                    if metric.endswith('_percent'):
                                        print(f"     {metric}: {value:.1f}%")
                                    elif 'memory' in metric or 'disk' in metric:
                                        print(f"     {metric}: {value / (1024**3):.1f} GB")
                                    else:
                                        print(f"     {metric}: {value:.2f}")
                                else:
                                    print(f"     {metric}: {value}")
                    
                    # Afficher les problèmes les plus sévères
                    severe_issues = [i for i in diagnostic.issues 
                                   if i.severity in [DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL]]
                    
                    if severe_issues:
                        print("   Problèmes sévères:")
                        for issue in severe_issues[:2]:
                            print(f"     - {issue.message}")
                            if issue.recommendations:
                                print(f"       💡 {issue.recommendations[0]}")
                
                except Exception as e:
                    print(f"   ❌ Erreur lors du diagnostic: {e}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_performance_analysis():
    """Test de l'analyse de performance"""
    print("\\n⚡ Test de l'analyse de performance")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        print("🔍 Diagnostic du composant performance...")
        perf_diagnostic = await engine._diagnose_performance()
        
        print(f"📊 Résultats de performance:")
        print(f"   Score: {perf_diagnostic.health_score:.1f}%")
        print(f"   Statut: {perf_diagnostic.status.value}")
        
        # Afficher les métriques de performance
        if perf_diagnostic.metrics:
            print("   Métriques de performance:")
            for metric, value in perf_diagnostic.metrics.items():
                if isinstance(value, float):
                    if 'time' in metric:
                        print(f"     {metric}: {value:.3f}s")
                    else:
                        print(f"     {metric}: {value:.2f}")
                else:
                    print(f"     {metric}: {value}")
        
        # Afficher les problèmes de performance
        if perf_diagnostic.issues:
            print("   Problèmes de performance:")
            for issue in perf_diagnostic.issues:
                severity_icon = {
                    DiagnosticSeverity.INFO: "ℹ️",
                    DiagnosticSeverity.WARNING: "⚠️",
                    DiagnosticSeverity.ERROR: "❌",
                    DiagnosticSeverity.CRITICAL: "🚨"
                }.get(issue.severity, "❓")
                print(f"     {severity_icon} {issue.message}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_diagnostic_engine_simple())
    asyncio.run(test_quick_health_check())
    asyncio.run(test_individual_components())
    asyncio.run(test_performance_analysis())
    
    print("\\n✅ Tous les tests du moteur de diagnostic terminés")