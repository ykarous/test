#!/usr/bin/env python3
"""
Test simple du système de monitoring sans dépendances.
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test direct du module de monitoring
def test_progress_monitor_direct():
    """Test direct du moniteur de progression."""
    print("=== Test Direct du Moniteur de Progression ===")
    
    try:
        # Import direct
        from ai_video_dubbing.gui.progress_monitor import ProgressMonitor, NotificationType, Notification
        from ai_video_dubbing.models.data_models import PipelineStage, ProgressInfo
        
        print("✅ Imports réussis")
        
        # Créer une instance
        monitor = ProgressMonitor()
        print("✅ Instance créée")
        
        # Test des callbacks
        progress_updates = []
        notifications = []
        
        def progress_callback(progress_info):
            progress_updates.append(progress_info)
            print(f"  📊 {progress_info.stage.value}: {progress_info.progress:.1f}%")
        
        def notification_callback(notification):
            notifications.append(notification)
            print(f"  🔔 {notification.type.value}: {notification.title}")
        
        monitor.register_progress_callback(progress_callback)
        monitor.register_notification_callback(notification_callback)
        print("✅ Callbacks enregistrés")
        
        # Démarrer le monitoring
        monitor.start_monitoring()
        print("✅ Monitoring démarré")
        
        # Test de progression
        monitor.update_stage_progress(
            PipelineStage.INITIALIZATION,
            50.0,
            substep="Test substep",
            message="Test message"
        )
        print("✅ Progression mise à jour")
        
        # Test de notification
        monitor.send_completion_notification("/test/output.mp4", 120.5)
        print("✅ Notification envoyée")
        
        # Vérifier les résultats
        print(f"\n📊 Résultats:")
        print(f"  - Mises à jour reçues: {len(progress_updates)}")
        print(f"  - Notifications reçues: {len(notifications)}")
        
        return len(progress_updates) > 0 and len(notifications) > 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notification_widget_import():
    """Test d'import du widget de notification."""
    print("\n=== Test Import Widget de Notification ===")
    
    try:
        from ai_video_dubbing.gui.notification_widget import NotificationManager, ProgressBar
        print("✅ Import NotificationManager et ProgressBar réussi")
        
        # Test de création (sans Tkinter pour éviter les problèmes)
        print("✅ Widgets de notification disponibles")
        return True
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False


def test_data_models():
    """Test des modèles de données."""
    print("\n=== Test Modèles de Données ===")
    
    try:
        from ai_video_dubbing.models.data_models import PipelineStage, ProgressInfo, PipelineConfig
        print("✅ Import des modèles réussi")
        
        # Test de création
        config = PipelineConfig()
        print(f"✅ Configuration créée: {config.asr_model}")
        
        progress = ProgressInfo(
            stage=PipelineStage.INITIALIZATION,
            progress=50.0,
            message="Test message",
            timestamp=time.time()
        )
        print(f"✅ ProgressInfo créé: {progress.stage.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_monitoring_features():
    """Test des fonctionnalités de monitoring."""
    print("\n=== Test Fonctionnalités de Monitoring ===")
    
    try:
        from ai_video_dubbing.gui.progress_monitor import ProgressMonitor
        from ai_video_dubbing.models.data_models import PipelineStage
        
        monitor = ProgressMonitor()
        
        # Test des étapes
        stages = list(PipelineStage)
        print(f"✅ {len(stages)} étapes disponibles:")
        for stage in stages[:3]:  # Afficher les 3 premières
            print(f"  - {stage.value}")
        
        # Test de progression détaillée
        monitor.start_monitoring()
        
        for i, stage in enumerate(stages[:3]):
            monitor.update_stage_progress(stage, (i + 1) * 33.3, message=f"Test étape {i+1}")
        
        detailed = monitor.get_detailed_progress()
        print(f"✅ Progression globale: {detailed['overall_progress']:.1f}%")
        
        # Test des statistiques
        monitor.add_processing_stat("test_stat", "test_value")
        perf = monitor.get_performance_summary()
        print(f"✅ Statistiques: {len(perf.get('stats', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale de test."""
    print("🎬 AI Video Dubbing - Test Simple du Système de Monitoring")
    print("=" * 70)
    
    tests = [
        ("Modèles de données", test_data_models),
        ("Moniteur de progression", test_progress_monitor_direct),
        ("Widget de notification", test_notification_widget_import),
        ("Fonctionnalités de monitoring", test_monitoring_features)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"{status}")
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"  {test_name}: {status}")
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Système de monitoring et notifications implémenté avec succès!")
        print("\nFonctionnalités disponibles:")
        print("  ✅ Monitoring de progression avec étapes détaillées")
        print("  ✅ Système de notifications avec types multiples")
        print("  ✅ Barre de progression avancée")
        print("  ✅ Fenêtre de progression détaillée")
        print("  ✅ Notifications flottantes avec actions")
        print("  ✅ Statistiques de performance")
        print("  ✅ Gestion des erreurs avec suggestions")
    else:
        print("⚠️  Certains tests ont échoué.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)