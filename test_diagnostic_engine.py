"""
Test du moteur de diagnostic avancé
"""
import asyncio
import tempfile
import shutil
from ai_video_dubbing.performance.diagnostic_engine import (
    DiagnosticEngine, DiagnosticSeverity, ComponentStatus
)

async def test_diagnostic_engine_basic():
    """Test basique du moteur de diagnostic"""
    print("🔍 Test basique du moteur de diagnostic")
    print("-" * 45)
    
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
        
        # Afficher les recommandations globales
        if report.recommendations:
            print("\\n💡 Recommandations globales:")
            for rec in report.recommendations[:5]:  # Max 5 recommandations
                print(f"   - {rec}")
        
        # Afficher les goulots d'étranglement
        if report.performance_bottlenecks:
            print("\\n🚧 Goulots d'étranglement identifiés:")
            for bottleneck in report.performance_bottlenecks:
                print(f"   - {bottleneck}")
        
        # Informations système
        print("\\n🖥️ Informations système:")
        sys_info = report.system_info
        print(f"   Système: {sys_info.get('system', 'Unknown')} {sys_info.get('release', '')}")
        print(f"   Processeur: {sys_info.get('processor', 'Unknown')}")
        print(f"   Mémoire totale: {sys_info.get('total_memory', 0) / (1024**3):.1f} GB")
        print(f"   Utilisation mémoire: {sys_info.get('memory_percent', 0):.1f}%")
        
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

async def test_component_diagnostics():
    """Test des diagnostics individuels de composants"""
    print("\\n🧩 Test des diagnostics individuels")
    print("-" * 38)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        # Tester quelques composants spécifiques
        test_components = ["system", "memory", "gpu", "network"]
        
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
                        "gpu": ["cuda_available", "gpu_memory_percent"],
                        "network": ["dns_resolution", "http_connectivity"]
                    }
                    
                    if component_name in interesting_metrics:
                        for metric in interesting_metrics[component_name]:
                            if metric in diagnostic.metrics:
                                value = diagnostic.metrics[metric]
                                print(f"   {metric}: {value}")
                    
                    # Afficher les problèmes les plus sévères
                    severe_issues = [i for i in diagnostic.issues 
                                   if i.severity in [DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL]]
                    
                    if severe_issues:
                        print("   Problèmes sévères:")
                        for issue in severe_issues[:2]:
                            print(f"     - {issue.message}")
                
                except Exception as e:
                    print(f"   ❌ Erreur lors du diagnostic: {e}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_diagnostic_history():
    """Test de l'historique des diagnostics"""
    print("\\n📚 Test de l'historique des diagnostics")
    print("-" * 38)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        # Effectuer plusieurs diagnostics pour créer un historique
        print("🔄 Création de l'historique...")
        
        for i in range(3):
            print(f"   Diagnostic {i+1}/3...")
            report = await engine.quick_health_check()
            await asyncio.sleep(0.1)  # Petite pause entre les diagnostics
        
        # Vérifier l'historique
        history = engine.get_diagnostic_history()
        print(f"📊 Historique: {len(history)} entrées")
        
        if history:
            latest = history[-1]
            print(f"   Dernier diagnostic: Score {latest.overall_health_score:.1f}%")
            print(f"   Composants: {len(latest.component_diagnostics)}")
        
        # Tester les tendances (si on avait des données)
        print("📈 Test des tendances...")
        trend = engine.get_component_trend("system", "cpu_usage", limit=5)
        print(f"   Tendance CPU: {len(trend)} points de données")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_diagnostic_report_export():
    """Test de l'export du rapport de diagnostic"""
    print("\\n📄 Test de l'export du rapport")
    print("-" * 32)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        print("🔍 Génération du rapport...")
        report = await engine.run_full_diagnostic()
        
        # Convertir en dictionnaire (pour export JSON)
        report_dict = report.to_dict()
        
        print("📋 Structure du rapport:")
        print(f"   Clés principales: {list(report_dict.keys())}")
        print(f"   Taille du rapport: {len(str(report_dict))} caractères")
        
        # Vérifier que toutes les données importantes sont présentes
        required_keys = [
            "timestamp", "overall_health_score", "system_info",
            "component_diagnostics", "critical_issues", "recommendations"
        ]
        
        missing_keys = [key for key in required_keys if key not in report_dict]
        if missing_keys:
            print(f"   ⚠️ Clés manquantes: {missing_keys}")
        else:
            print("   ✅ Toutes les clés requises sont présentes")
        
        # Statistiques du rapport
        print("\\n📊 Statistiques du rapport:")
        print(f"   Composants diagnostiqués: {len(report_dict['component_diagnostics'])}")
        print(f"   Problèmes critiques: {len(report_dict['critical_issues'])}")
        print(f"   Recommandations: {len(report_dict['recommendations'])}")
        print(f"   Goulots d'étranglement: {len(report_dict['performance_bottlenecks'])}")
        
        # Compter les problèmes par sévérité
        severity_counts = {}
        for component_diag in report_dict['component_diagnostics'].values():
            for issue in component_diag['issues']:
                severity = issue['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts:
            print("   Problèmes par sévérité:")
            for severity, count in severity_counts.items():
                print(f"     {severity}: {count}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_diagnostic_engine_basic())
    asyncio.run(test_quick_health_check())
    asyncio.run(test_component_diagnostics())
    asyncio.run(test_diagnostic_history())
    asyncio.run(test_diagnostic_report_export())
    
    print("\\n✅ Tous les tests du moteur de diagnostic terminés")