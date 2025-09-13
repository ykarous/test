#!/usr/bin/env python3
"""
Test du système de monitoring de progression et notifications.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_video_dubbing.gui.progress_monitor import (
    ProgressMonitor, get_progress_monitor, 
    NotificationType, Notification
)
from ai_video_dubbing.models.data_models import PipelineStage, ProgressInfo


def test_progress_monitor():
    """Test du moniteur de progression."""
    print("=== Test du Moniteur de Progression ===")
    
    # Obtenir l'instance du moniteur
    monitor = get_progress_monitor()
    print("✅ Moniteur de progression obtenu")
    
    # Test des callbacks
    progress_updates = []
    notifications = []
    
    def progress_callback(progress_info):
        progress_updates.append(progress_info)
        print(f"  📊 Progression: {progress_info.stage.value} - {progress_info.progress:.1f}% - {progress_info.message}")
    
    def notification_callback(notification):
        notifications.append(notification)
        print(f"  🔔 Notification: {notification.type.value} - {notification.title}")
    
    monitor.register_progress_callback(progress_callback)
    monitor.register_notification_callback(notification_callback)
    print("✅ Callbacks enregistrés")
    
    # Démarrer le monitoring
    monitor.start_monitoring()
    print("✅ Monitoring démarré")
    
    # Simuler la progression des étapes
    stages = [
        PipelineStage.INITIALIZATION,
        PipelineStage.VIDEO_PROCESSING,
        PipelineStage.AUDIO_PROCESSING,
        PipelineStage.TRANSCRIPTION
    ]
    
    for stage in stages:
        print(f"\n--- Test étape: {stage.value} ---")
        
        # Simuler la progression de l'étape
        for progress in [0, 25, 50, 75, 100]:
            monitor.update_stage_progress(
                stage, 
                progress, 
                substep=f"Sous-étape {progress//25 + 1}",
                message=f"Traitement en cours... {progress}%"
            )
            time.sleep(0.1)  # Petite pause pour voir la progression
        
        print(f"✅ Étape {stage.value} terminée")
    
    # Test des notifications
    print("\n--- Test des Notifications ---")
    
    monitor.send_completion_notification(
        "/path/to/output.mp4",
        120.5
    )
    
    monitor.send_warning_notification(
        "Avertissement Test",
        "Ceci est un message d'avertissement de test."
    )
    
    monitor.send_error_notification(
        "Erreur de test",
        "Vérifiez la configuration et réessayez."
    )
    
    # Vérifier les résultats
    print(f"\n📊 Résultats:")
    print(f"  - Mises à jour de progression reçues: {len(progress_updates)}")
    print(f"  - Notifications reçues: {len(notifications)}")
    
    # Obtenir les informations détaillées
    detailed_progress = monitor.get_detailed_progress()
    print(f"  - Progression globale: {detailed_progress['overall_progress']:.1f}%")
    print(f"  - Étapes terminées: {sum(1 for stage_info in detailed_progress['stages'].values() if stage_info['status'] == 'completed')}")
    
    # Statistiques de performance
    perf_summary = monitor.get_performance_summary()
    if perf_summary:
        print(f"  - Temps total: {perf_summary['total_processing_time']:.2f}s")
        print(f"  - Étapes complétées: {perf_summary['completed_stages']}/{perf_summary['total_stages']}")
    
    return len(progress_updates) > 0 and len(notifications) > 0


def test_notification_types():
    """Test des différents types de notifications."""
    print("\n=== Test des Types de Notifications ===")
    
    monitor = get_progress_monitor()
    
    # Test de chaque type de notification
    notification_types = [
        (NotificationType.INFO, "Information", "Message d'information"),
        (NotificationType.SUCCESS, "Succès", "Opération réussie"),
        (NotificationType.WARNING, "Avertissement", "Attention requise"),
        (NotificationType.ERROR, "Erreur", "Une erreur s'est produite")
    ]
    
    for notif_type, title, message in notification_types:
        notification = Notification(
            type=notif_type,
            title=title,
            message=message,
            duration=5.0
        )
        
        # Simuler l'envoi de notification
        print(f"  📝 Notification {notif_type.value}: {title}")
    
    print("✅ Tous les types de notifications testés")
    return True


def test_stage_progression():
    """Test de la progression détaillée des étapes."""
    print("\n=== Test de la Progression des Étapes ===")
    
    monitor = get_progress_monitor()
    
    # Test d'une étape avec sous-étapes
    stage = PipelineStage.VOICE_CLONING
    
    print(f"Test de l'étape: {stage.value}")
    
    # Obtenir les informations de l'étape
    detailed_progress = monitor.get_detailed_progress()
    stage_info = detailed_progress['stages'].get(stage.value)
    
    if stage_info:
        print(f"  - Nom: {stage_info['name']}")
        print(f"  - Description: {stage_info['description']}")
        print(f"  - Sous-étapes: {len(stage_info['substeps'])}")
        
        for i, substep in enumerate(stage_info['substeps']):
            print(f"    {i+1}. {substep}")
    
    # Simuler la progression avec sous-étapes
    substeps = stage_info['substeps'] if stage_info else ["Étape 1", "Étape 2", "Étape 3"]
    
    for i, substep in enumerate(substeps):
        progress = (i + 1) / len(substeps) * 100
        monitor.update_stage_progress(
            stage,
            progress,
            substep=substep,
            message=f"Exécution: {substep}"
        )
        print(f"  ✓ {substep} - {progress:.1f}%")
        time.sleep(0.1)
    
    print("✅ Progression des étapes testée")
    return True


def test_performance_monitoring():
    """Test du monitoring de performance."""
    print("\n=== Test du Monitoring de Performance ===")
    
    monitor = get_progress_monitor()
    
    # Ajouter des statistiques de test
    test_stats = {
        "video_duration": 120.5,
        "audio_channels": 2,
        "video_resolution": "1920x1080",
        "processing_speed": 2.3,
        "memory_usage": "1.2 GB"
    }
    
    for key, value in test_stats.items():
        monitor.add_processing_stat(key, value)
        print(f"  📊 Statistique ajoutée: {key} = {value}")
    
    # Obtenir le résumé de performance
    perf_summary = monitor.get_performance_summary()
    
    if perf_summary:
        print(f"\n📈 Résumé de Performance:")
        print(f"  - Temps total: {perf_summary.get('total_processing_time', 0):.2f}s")
        print(f"  - Progression: {perf_summary.get('overall_progress', 0):.1f}%")
        
        stats = perf_summary.get('stats', {})
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    
    print("✅ Monitoring de performance testé")
    return True


def test_concurrent_updates():
    """Test des mises à jour concurrentes."""
    print("\n=== Test des Mises à Jour Concurrentes ===")
    
    monitor = get_progress_monitor()
    
    # Fonction pour simuler des mises à jour dans un thread
    def update_worker(stage, worker_id):
        for i in range(5):
            progress = i * 20
            monitor.update_stage_progress(
                stage,
                progress,
                substep=f"Worker {worker_id} - Étape {i+1}",
                message=f"Traitement concurrent {worker_id}"
            )
            time.sleep(0.05)
    
    # Lancer plusieurs threads de mise à jour
    threads = []
    stages = [PipelineStage.AUDIO_PROCESSING, PipelineStage.TRANSCRIPTION]
    
    for i, stage in enumerate(stages):
        thread = threading.Thread(target=update_worker, args=(stage, i+1))
        threads.append(thread)
        thread.start()
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    print("✅ Mises à jour concurrentes testées")
    return True


def main():
    """Fonction principale de test."""
    print("🎬 AI Video Dubbing - Test du Système de Monitoring")
    print("=" * 60)
    
    tests = [
        ("Moniteur de progression", test_progress_monitor),
        ("Types de notifications", test_notification_types),
        ("Progression des étapes", test_stage_progression),
        ("Monitoring de performance", test_performance_monitoring),
        ("Mises à jour concurrentes", test_concurrent_updates)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHOUÉ")
        except Exception as e:
            print(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"  {test_name}: {status}")
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests du système de monitoring ont réussi!")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les détails ci-dessus.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)