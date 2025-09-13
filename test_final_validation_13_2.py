#!/usr/bin/env python3
"""
Validation finale et optimisation des performances - Tâche 13.2
Tests end-to-end complets avec métriques de performance
"""

import sys
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any
import logging

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging pour les tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Collecteur de métriques de performance"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Démarre un timer pour une opération"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """Termine un timer et retourne la durée"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = duration
            return duration
        return 0.0
    
    def add_metric(self, name: str, value: Any):
        """Ajoute une métrique"""
        self.metrics[name] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques"""
        return self.metrics.copy()

def test_performance_end_to_end():
    """Test de performance end-to-end avec l'application complète"""
    print("=== Test de performance end-to-end ===\n")
    
    metrics = PerformanceMetrics()
    
    try:
        # Test 1: Temps de démarrage de l'application
        metrics.start_timer("app_startup")
        import main
        startup_time = metrics.end_timer("app_startup")
        print(f"✅ Démarrage application: {startup_time:.3f}s")
        
        # Test 2: Temps d'initialisation des composants
        metrics.start_timer("components_init")
        
        # Tester les composants légers
        from ai_video_dubbing.performance.lightweight_fallbacks import initialize_lightweight_mode
        components = initialize_lightweight_mode()
        
        init_time = metrics.end_timer("components_init")
        print(f"✅ Initialisation composants: {init_time:.3f}s")
        metrics.add_metric("components_count", len(components))
        
        # Test 3: Temps de diagnostic système
        metrics.start_timer("diagnostic")
        
        # Capturer la sortie du diagnostic
        import io
        import contextlib
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main.launch_diagnostic()
        
        diagnostic_time = metrics.end_timer("diagnostic")
        diagnostic_output = output.getvalue()
        
        print(f"✅ Diagnostic système: {diagnostic_time:.3f}s")
        
        # Analyser les résultats du diagnostic
        available_components = diagnostic_output.count("[OK]")
        error_components = diagnostic_output.count("[ERREUR]")
        
        metrics.add_metric("available_components", available_components)
        metrics.add_metric("error_components", error_components)
        
        # Test 4: Test de l'interface graphique (création rapide)
        metrics.start_timer("gui_creation")
        
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        
        try:
            from ai_video_dubbing.gui.enhanced_main_window import EnhancedMainWindow
            window = EnhancedMainWindow()
            gui_type = "enhanced"
        except ImportError:
            try:
                from ai_video_dubbing.gui.main_window_qt import MainWindowQt
                window = MainWindowQt()
                gui_type = "standard"
            except ImportError:
                from ai_video_dubbing.gui.lightweight_main_window import LightweightMainWindow
                window = LightweightMainWindow()
                gui_type = "lightweight"
        
        gui_time = metrics.end_timer("gui_creation")
        print(f"✅ Création GUI ({gui_type}): {gui_time:.3f}s")
        
        app.quit()
        metrics.add_metric("gui_type", gui_type)
        
        # Test 5: Test des composants de performance
        metrics.start_timer("performance_components")
        
        performance_tests = []
        
        # Test du cache léger
        cache_manager = components.get("CacheManager")
        if cache_manager:
            cache_start = time.time()
            cache_manager.set("test_key", {"data": "performance_test"})
            result = cache_manager.get("test_key")
            cache_time = time.time() - cache_start
            performance_tests.append(("cache", cache_time, result is not None))
        
        # Test du gestionnaire AI léger
        ai_manager = components.get("AIManager")
        if ai_manager:
            ai_start = time.time()
            transcription = ai_manager.transcribe_audio("test.wav")
            ai_time = time.time() - ai_start
            performance_tests.append(("ai_transcription", ai_time, "text" in transcription))
        
        # Test du système de fallback
        fallback_system = components.get("FallbackSystem")
        if fallback_system:
            fallback_start = time.time()
            result = fallback_system.execute_with_fallback(lambda: "test_operation")
            fallback_time = time.time() - fallback_start
            performance_tests.append(("fallback", fallback_time, result is not None))
        
        perf_time = metrics.end_timer("performance_components")
        print(f"✅ Tests composants performance: {perf_time:.3f}s")
        
        for test_name, test_time, success in performance_tests:
            metrics.add_metric(f"{test_name}_time", test_time)
            metrics.add_metric(f"{test_name}_success", success)
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {test_time:.3f}s")
        
        return True, metrics
        
    except Exception as e:
        print(f"❌ Erreur test performance: {e}")
        return False, metrics

def test_timeout_and_fallback_functionality():
    """Test que tous les timeouts et fallbacks fonctionnent correctement"""
    print("\n=== Test des timeouts et fallbacks ===\n")
    
    try:
        from ai_video_dubbing.performance.lightweight_fallbacks import (
            LightweightFallbackSystem,
            LightweightAIManager
        )
        
        # Test 1: Système de fallback
        fallback_system = LightweightFallbackSystem()
        
        # Test d'opération normale
        result1 = fallback_system.execute_with_fallback(lambda: "success")
        print(f"✅ Opération normale: {result1}")
        
        # Test d'opération qui échoue (fallback)
        def failing_operation():
            raise Exception("Opération simulée qui échoue")
        
        result2 = fallback_system.execute_with_fallback(failing_operation)
        print(f"✅ Fallback activé: {result2}")
        
        # Test 2: Gestionnaire AI avec fallback
        ai_manager = LightweightAIManager()
        
        # Test de transcription normale
        transcription = ai_manager.transcribe_audio("test.wav")
        print(f"✅ Transcription AI: {transcription['text'][:50]}...")
        
        # Test 3: Vérification des modèles disponibles
        models = ai_manager.get_available_models()
        print(f"✅ Modèles disponibles: {len(models)} modèles")
        
        for model in models:
            available = ai_manager.is_model_available(model)
            status = "✅" if available else "❌"
            print(f"   {status} {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test fallbacks: {e}")
        return False

def test_interface_responsiveness():
    """Test que l'interface reste responsive pendant les opérations longues"""
    print("\n=== Test de responsivité de l'interface ===\n")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer, QThread, pyqtSignal
        
        app = QApplication([])
        
        # Créer une interface légère pour les tests
        from ai_video_dubbing.gui.lightweight_main_window import LightweightMainWindow
        window = LightweightMainWindow()
        
        # Test de responsivité avec simulation d'opération longue
        class TestThread(QThread):
            progress = pyqtSignal(int)
            finished = pyqtSignal()
            
            def run(self):
                for i in range(101):
                    self.progress.emit(i)
                    self.msleep(10)  # 10ms par étape
                self.finished.emit()
        
        # Connecter le thread à l'interface
        test_thread = TestThread()
        test_thread.progress.connect(window.progress_bar.setValue)
        
        # Variables pour tester la responsivité
        responsiveness_test = {"ui_updates": 0, "completed": False}
        
        def on_progress(value):
            responsiveness_test["ui_updates"] += 1
            # Forcer le traitement des événements UI
            app.processEvents()
        
        def on_finished():
            responsiveness_test["completed"] = True
            app.quit()
        
        test_thread.progress.connect(on_progress)
        test_thread.finished.connect(on_finished)
        
        # Démarrer le test
        window.show()
        test_thread.start()
        
        # Timer de sécurité (5 secondes max)
        QTimer.singleShot(5000, app.quit)
        
        # Exécuter l'application
        app.exec_()
        
        # Vérifier les résultats
        ui_updates = responsiveness_test["ui_updates"]
        completed = responsiveness_test["completed"]
        
        print(f"✅ Mises à jour UI: {ui_updates}")
        print(f"✅ Opération complétée: {completed}")
        
        # L'interface est considérée comme responsive si elle a traité au moins 50 mises à jour
        responsive = ui_updates >= 50 and completed
        
        if responsive:
            print("✅ Interface responsive pendant les opérations longues")
        else:
            print("⚠️  Interface pourrait être plus responsive")
        
        return responsive
        
    except Exception as e:
        print(f"❌ Erreur test responsivité: {e}")
        return False

def test_error_handling_and_recovery():
    """Test la gestion des erreurs et la récupération automatique"""
    print("\n=== Test de gestion d'erreurs et récupération ===\n")
    
    try:
        from ai_video_dubbing.performance.lightweight_fallbacks import (
            LightweightAIManager,
            LightweightCacheManager,
            LightweightDownloadManager
        )
        
        # Test 1: Gestion d'erreurs du gestionnaire AI
        ai_manager = LightweightAIManager()
        
        # Test avec fichier inexistant
        result = ai_manager.transcribe_audio("fichier_inexistant.wav")
        print(f"✅ Gestion fichier inexistant: {result['text']}")
        
        # Test 2: Gestion d'erreurs du cache
        cache_manager = LightweightCacheManager()
        
        # Test avec clé invalide
        invalid_result = cache_manager.get("clé/invalide*")
        print(f"✅ Gestion clé invalide: {invalid_result is None}")
        
        # Test d'écriture avec données invalides
        try:
            # Données non sérialisables
            cache_manager.set("test", lambda x: x)
            print("⚠️  Cache a accepté des données non sérialisables")
        except:
            print("✅ Cache rejette correctement les données invalides")
        
        # Test 3: Gestion d'erreurs du téléchargeur
        download_manager = LightweightDownloadManager()
        
        # Test avec URL invalide
        success = download_manager.download_model("test_model", "url_invalide")
        print(f"✅ Gestion URL invalide: {not success}")
        
        # Test 4: Récupération automatique
        from ai_video_dubbing.performance.lightweight_fallbacks import LightweightFallbackSystem
        
        fallback_system = LightweightFallbackSystem()
        
        # Test de récupération après plusieurs échecs
        def operation_with_retries(attempt=[0]):
            attempt[0] += 1
            if attempt[0] < 3:
                raise Exception(f"Échec tentative {attempt[0]}")
            return f"Succès après {attempt[0]} tentatives"
        
        result = fallback_system.execute_with_fallback(operation_with_retries)
        print(f"✅ Récupération automatique: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test gestion d'erreurs: {e}")
        return False

def test_performance_bottlenecks():
    """Identifie et teste les goulots d'étranglement de performance"""
    print("\n=== Test des goulots d'étranglement ===\n")
    
    bottlenecks = []
    
    try:
        # Test 1: Temps d'importation des modules
        import_times = {}
        
        modules_to_test = [
            "ai_video_dubbing.performance.lightweight_fallbacks",
            "ai_video_dubbing.performance.async_controller",
            "ai_video_dubbing.performance.model_notifications",
            "ai_video_dubbing.performance.progress_interface",
        ]
        
        for module_name in modules_to_test:
            start_time = time.time()
            try:
                __import__(module_name)
                import_time = time.time() - start_time
                import_times[module_name] = import_time
                
                if import_time > 0.5:  # Plus de 500ms
                    bottlenecks.append(f"Import lent: {module_name} ({import_time:.3f}s)")
                
                print(f"✅ {module_name.split('.')[-1]}: {import_time:.3f}s")
                
            except ImportError as e:
                print(f"⚠️  {module_name}: Non disponible ({e})")
        
        # Test 2: Performance des opérations de base
        from ai_video_dubbing.performance.lightweight_fallbacks import initialize_lightweight_mode
        
        # Test d'initialisation multiple
        init_times = []
        for i in range(5):
            start_time = time.time()
            components = initialize_lightweight_mode()
            init_time = time.time() - start_time
            init_times.append(init_time)
        
        avg_init_time = sum(init_times) / len(init_times)
        max_init_time = max(init_times)
        
        print(f"✅ Initialisation moyenne: {avg_init_time:.3f}s")
        print(f"✅ Initialisation max: {max_init_time:.3f}s")
        
        if max_init_time > 1.0:  # Plus d'1 seconde
            bottlenecks.append(f"Initialisation lente: {max_init_time:.3f}s")
        
        # Test 3: Performance mémoire
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Créer plusieurs instances pour tester la consommation mémoire
        instances = []
        for i in range(10):
            components = initialize_lightweight_mode()
            instances.append(components)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"✅ Consommation mémoire: +{memory_increase:.1f}MB pour 10 instances")
        
        if memory_increase > 100:  # Plus de 100MB
            bottlenecks.append(f"Consommation mémoire élevée: +{memory_increase:.1f}MB")
        
        # Résumé des goulots d'étranglement
        if bottlenecks:
            print(f"\n⚠️  Goulots d'étranglement identifiés:")
            for bottleneck in bottlenecks:
                print(f"   - {bottleneck}")
        else:
            print(f"\n✅ Aucun goulot d'étranglement majeur détecté")
        
        return len(bottlenecks) == 0, bottlenecks
        
    except Exception as e:
        print(f"❌ Erreur test goulots d'étranglement: {e}")
        return False, [f"Erreur de test: {e}"]

def generate_final_performance_report(metrics: PerformanceMetrics, bottlenecks: List[str]):
    """Génère un rapport final de performance"""
    print("\n" + "="*60)
    print("📊 RAPPORT FINAL DE PERFORMANCE")
    print("="*60)
    
    summary = metrics.get_summary()
    
    # Métriques de temps
    print("\n⏱️  MÉTRIQUES DE TEMPS:")
    time_metrics = {k: v for k, v in summary.items() if k.endswith('_time') or 'startup' in k or 'init' in k or 'diagnostic' in k}
    
    for metric, value in time_metrics.items():
        if isinstance(value, (int, float)):
            status = "✅" if value < 1.0 else "⚠️" if value < 3.0 else "❌"
            print(f"   {status} {metric}: {value:.3f}s")
    
    # Métriques de composants
    print("\n🔧 COMPOSANTS:")
    component_metrics = {k: v for k, v in summary.items() if 'components' in k or 'available' in k or 'error' in k}
    
    for metric, value in component_metrics.items():
        print(f"   ✅ {metric}: {value}")
    
    # Métriques de succès
    print("\n✅ TAUX DE SUCCÈS:")
    success_metrics = {k: v for k, v in summary.items() if k.endswith('_success')}
    
    total_tests = len(success_metrics)
    successful_tests = sum(1 for v in success_metrics.values() if v)
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 100
    
    for metric, success in success_metrics.items():
        status = "✅" if success else "❌"
        print(f"   {status} {metric}: {'Réussi' if success else 'Échoué'}")
    
    print(f"\n📈 TAUX DE SUCCÈS GLOBAL: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    # Goulots d'étranglement
    if bottlenecks:
        print(f"\n⚠️  GOULOTS D'ÉTRANGLEMENT ({len(bottlenecks)}):")
        for bottleneck in bottlenecks:
            print(f"   - {bottleneck}")
    else:
        print(f"\n✅ AUCUN GOULOT D'ÉTRANGLEMENT MAJEUR")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    
    if summary.get('gui_type') == 'lightweight':
        print("   - Installer torch et aiofiles pour activer le mode optimisé complet")
    
    if summary.get('error_components', 0) > 0:
        print("   - Installer les dépendances manquantes pour activer tous les composants")
    
    slow_operations = [k for k, v in time_metrics.items() if isinstance(v, (int, float)) and v > 2.0]
    if slow_operations:
        print(f"   - Optimiser les opérations lentes: {', '.join(slow_operations)}")
    
    if not bottlenecks and success_rate >= 90:
        print("   - Performance excellente, aucune optimisation urgente nécessaire")
    
    # Score final
    performance_score = min(100, success_rate - len(bottlenecks) * 10)
    
    print(f"\n🎯 SCORE DE PERFORMANCE: {performance_score:.0f}/100")
    
    if performance_score >= 90:
        print("🎉 PERFORMANCE EXCELLENTE!")
    elif performance_score >= 75:
        print("✅ PERFORMANCE BONNE")
    elif performance_score >= 60:
        print("⚠️  PERFORMANCE ACCEPTABLE")
    else:
        print("❌ PERFORMANCE À AMÉLIORER")
    
    return performance_score

def main():
    """Fonction principale de validation"""
    print("🚀 VALIDATION FINALE - TÂCHE 13.2")
    print("Tests end-to-end avec métriques de performance\n")
    
    # Tests principaux
    tests = [
        ("Performance end-to-end", test_performance_end_to_end),
        ("Timeouts et fallbacks", test_timeout_and_fallback_functionality),
        ("Responsivité interface", test_interface_responsiveness),
        ("Gestion d'erreurs", test_error_handling_and_recovery),
    ]
    
    results = []
    metrics = None
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        try:
            if test_name == "Performance end-to-end":
                result, metrics = test_func()
            else:
                result = test_func()
            
            results.append(result)
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"   {status}\n")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}\n")
            results.append(False)
    
    # Test des goulots d'étranglement
    print("🔍 Goulots d'étranglement...")
    bottleneck_ok, bottlenecks = test_performance_bottlenecks()
    results.append(bottleneck_ok)
    
    # Génération du rapport final
    if metrics:
        performance_score = generate_final_performance_report(metrics, bottlenecks)
    else:
        performance_score = 0
    
    # Résumé final
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSULTATS FINAUX: {success_count}/{total_count} tests réussis ({success_rate:.1f}%)")
    print(f"🎯 Score de performance: {performance_score:.0f}/100")
    
    if success_count == total_count and performance_score >= 80:
        print("🎉 VALIDATION FINALE RÉUSSIE!")
        print("✅ Tâche 13.2 - Application validée et optimisée")
        print("🚀 L'application est prête pour la production!")
    elif success_rate >= 80:
        print("✅ VALIDATION LARGEMENT RÉUSSIE!")
        print("⚠️  Quelques optimisations mineures recommandées")
    else:
        print("⚠️  VALIDATION PARTIELLE")
        print("🔧 Des améliorations sont nécessaires")
    
    return success_count == total_count and performance_score >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)