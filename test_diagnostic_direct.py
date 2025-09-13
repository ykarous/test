"""
Test direct du moteur de diagnostic
"""
import asyncio
import tempfile
import shutil
import sys
import os
import importlib.util

async def test_diagnostic_direct():
    """Test direct du moteur de diagnostic"""
    print("🔍 Test direct du moteur de diagnostic")
    print("-" * 40)
    
    # Importer directement le module
    spec = importlib.util.spec_from_file_location(
        "diagnostic_engine", 
        "ai_video_dubbing/performance/diagnostic_engine.py"
    )
    diagnostic_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnostic_module)
    
    DiagnosticEngine = diagnostic_module.DiagnosticEngine
    DiagnosticSeverity = diagnostic_module.DiagnosticSeverity
    ComponentStatus = diagnostic_module.ComponentStatus
    
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
                for issue in diagnostic.issues[:1]:  # Afficher 1 problème
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
            for rec in report.recommendations[:3]:  # Max 3
                print(f"   - {rec}")
        
        # Afficher les goulots d'étranglement
        if report.performance_bottlenecks:
            print("\\n🚧 Goulots d'étranglement identifiés:")
            for bottleneck in report.performance_bottlenecks[:3]:  # Max 3
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
        
        # Test de vérification rapide
        print("\\n⚡ Test de vérification rapide:")
        quick_results = await engine.quick_health_check()
        print(f"   Score global rapide: {quick_results['overall_health_score']:.1f}%")
        
        for component, result in quick_results['components'].items():
            if 'error' not in result:
                status_icon = "✅" if result['health_score'] > 80 else "⚠️" if result['health_score'] > 60 else "❌"
                print(f"   {status_icon} {component}: {result['health_score']:.1f}%")
        
        return report
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_component_specific():
    """Test de composants spécifiques"""
    print("\\n🧩 Test de composants spécifiques")
    print("-" * 35)
    
    # Importer le module
    spec = importlib.util.spec_from_file_location(
        "diagnostic_engine", 
        "ai_video_dubbing/performance/diagnostic_engine.py"
    )
    diagnostic_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnostic_module)
    
    DiagnosticEngine = diagnostic_module.DiagnosticEngine
    DiagnosticSeverity = diagnostic_module.DiagnosticSeverity
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        engine = DiagnosticEngine(config_dir=temp_dir)
        
        # Tester des composants individuels
        components_to_test = ["system", "memory", "storage"]
        
        for component_name in components_to_test:
            print(f"\\n🔍 Test du composant: {component_name}")
            
            try:
                if component_name in engine.components:
                    diagnostic_func = engine.components[component_name]
                    diagnostic = await diagnostic_func()
                    
                    print(f"   Statut: {diagnostic.status.value}")
                    print(f"   Score: {diagnostic.health_score:.1f}%")
                    print(f"   Problèmes: {len(diagnostic.issues)}")
                    
                    # Afficher quelques métriques
                    key_metrics = list(diagnostic.metrics.keys())[:3]  # Max 3 métriques
                    if key_metrics:
                        print("   Métriques clés:")
                        for metric in key_metrics:
                            value = diagnostic.metrics[metric]
                            if isinstance(value, (int, float)):
                                if 'percent' in metric:
                                    print(f"     {metric}: {value:.1f}%")
                                elif 'memory' in metric or 'disk' in metric:
                                    if value > 1024**3:  # Si c'est en bytes
                                        print(f"     {metric}: {value / (1024**3):.1f} GB")
                                    else:
                                        print(f"     {metric}: {value}")
                                else:
                                    print(f"     {metric}: {value}")
                            else:
                                print(f"     {metric}: {value}")
                    
                    # Afficher les problèmes
                    if diagnostic.issues:
                        print("   Problèmes:")
                        for issue in diagnostic.issues[:2]:  # Max 2 problèmes
                            severity_icon = {
                                DiagnosticSeverity.INFO: "ℹ️",
                                DiagnosticSeverity.WARNING: "⚠️",
                                DiagnosticSeverity.ERROR: "❌",
                                DiagnosticSeverity.CRITICAL: "🚨"
                            }.get(issue.severity, "❓")
                            print(f"     {severity_icon} {issue.message}")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_diagnostic_direct())
    asyncio.run(test_component_specific())
    
    print("\\n✅ Tests du moteur de diagnostic terminés")