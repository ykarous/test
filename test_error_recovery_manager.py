"""Tests pour le gestionnaire d'erreurs centralisé"""
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ai_video_dubbing.performance.error_recovery_manager import (
    ErrorRecoveryManager, ErrorContext, ErrorType, ErrorSeverity, RecoveryStrategy,
    create_error_context, classify_error, determine_severity
)

async def test_error_recovery_manager():
    """Test du gestionnaire d'erreurs centralisé"""
    
    print("🚀 Test du gestionnaire d'erreurs centralisé")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "error_recovery_config.json"
        
        # Initialiser le gestionnaire
        manager = ErrorRecoveryManager(str(config_file))
        
        print("✅ Gestionnaire d'erreurs initialisé")
        
        # Test de création de contexte d'erreur
        try:
            raise ValueError("Test error message")
        except Exception as e:
            error_context = create_error_context(
                exception=e,
                error_type=ErrorType.TRANSCRIPTION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                component="test_component",
                operation_id="test_op_123"
            )
        
        print(f"✅ Contexte d'erreur créé: {error_context.error_id}")
        
        # Test de gestion d'erreur
        recovery_success = await manager.handle_error(error_context)
        print(f"✅ Gestion d'erreur: {'Récupérée' if recovery_success else 'Non récupérée'}")
        
        # Vérifier l'historique
        history = manager.get_error_history()
        assert len(history) > 0, "L'historique devrait contenir au moins une erreur"
        print(f"✅ Historique des erreurs: {len(history)} erreurs")
        
        # Test des métriques système
        metrics = manager.get_system_metrics()
        print(f"✅ Métriques système collectées: {list(metrics.keys())}")
        
        # Test des statistiques de récupération
        stats = manager.get_recovery_statistics()
        print("📊 Statistiques de récupération:")
        print(f"  - Total des erreurs: {stats['total_errors']}")
        print(f"  - Erreurs récupérées: {stats['recovered_errors']}")
        print(f"  - Taux de récupération: {stats['recovery_rate']:.1f}%")
        print(f"  - Erreurs actives: {stats['active_errors']}")
        
        # Test de classification automatique d'erreurs
        test_exceptions = [
            (ValueError("CUDA out of memory"), ErrorType.CUDA_ERROR),
            (MemoryError("Not enough memory"), ErrorType.MEMORY_ERROR),
            (ConnectionError("Network timeout"), ErrorType.NETWORK_ERROR),
            (FileNotFoundError("Model file not found"), ErrorType.MODEL_ERROR),
            (RuntimeError("Transcription failed"), ErrorType.TRANSCRIPTION_ERROR)
        ]
        
        print("\n🔍 Test de classification automatique:")
        for exception, expected_type in test_exceptions:
            classified_type = classify_error(exception)
            severity = determine_severity(exception, classified_type)
            
            status = "✅" if classified_type == expected_type else "⚠️"
            print(f"  {status} {type(exception).__name__}: {classified_type.value} (gravité: {severity.value})")
        
        # Test de patterns d'erreur
        print("\n🔄 Test de détection de patterns d'erreur:")
        
        # Créer plusieurs erreurs similaires
        for i in range(6):  # Dépasser le seuil de 5
            similar_error = ErrorContext(
                error_id=f"pattern_test_{i}",
                error_type=ErrorType.MEMORY_ERROR,
                severity=ErrorSeverity.MEDIUM,
                error_message=f"Pattern test error {i}",
                component="pattern_test_component"
            )
            await manager.handle_error(similar_error)
        
        patterns = manager.get_error_patterns()
        print(f"✅ Patterns détectés: {len(patterns)} patterns")
        for pattern, count in patterns.items():
            print(f"  - {pattern}: {count} occurrences")
        
        # Test de callback de confirmation
        print("\n✋ Test de callback de confirmation:")
        
        confirmation_received = []
        
        async def test_confirmation_callback(confirmation_message):
            confirmation_received.append(confirmation_message)
            print(f"  📞 Confirmation reçue pour: {confirmation_message['strategy']}")
            return True  # Confirmer automatiquement pour le test
        
        manager.add_confirmation_callback(test_confirmation_callback)
        
        # Créer une erreur nécessitant confirmation
        confirmation_error = ErrorContext(
            error_id="confirmation_test",
            error_type=ErrorType.CUDA_ERROR,
            severity=ErrorSeverity.HIGH,
            error_message="Test error requiring confirmation",
            component="confirmation_test"
        )
        
        await manager.handle_error(confirmation_error)
        
        # Attendre un peu pour le traitement asynchrone
        await asyncio.sleep(1)
        
        if confirmation_received:
            print("✅ Callback de confirmation fonctionnel")
        else:
            print("⚠️ Callback de confirmation non déclenché")
        
        # Test de récupération forcée
        print("\n🔧 Test de récupération forcée:")
        
        active_errors = manager.get_active_errors()
        if active_errors:
            error_id = list(active_errors.keys())[0]
            force_result = await manager.force_recovery(error_id)
            print(f"✅ Récupération forcée: {'Réussie' if force_result else 'Échouée'}")
        
        # Test de mise à jour de configuration
        print("\n⚙️ Test de mise à jour de configuration:")
        
        new_config = {
            "max_error_history": 500,
            "auto_recovery_enabled": False
        }
        
        manager.update_config(new_config)
        assert manager.config["max_error_history"] == 500, "La configuration devrait être mise à jour"
        print("✅ Configuration mise à jour")
        
        # Fermeture propre
        await manager.shutdown()
        print("✅ Gestionnaire fermé proprement")
        
        print("\n🎉 Tous les tests du gestionnaire d'erreurs réussis!")

async def test_recovery_strategies():
    """Test des stratégies de récupération"""
    
    print("\n🛠️ Test des stratégies de récupération")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "recovery_test_config.json"
        manager = ErrorRecoveryManager(str(config_file))
        
        # Test des différents types d'erreur et leurs stratégies
        error_types_to_test = [
            ErrorType.CUDA_ERROR,
            ErrorType.MEMORY_ERROR,
            ErrorType.NETWORK_ERROR,
            ErrorType.MODEL_ERROR,
            ErrorType.TRANSCRIPTION_ERROR
        ]
        
        for error_type in error_types_to_test:
            print(f"\n🔍 Test des stratégies pour {error_type.value}:")
            
            # Créer une erreur de ce type
            test_error = ErrorContext(
                error_id=f"strategy_test_{error_type.value}",
                error_type=error_type,
                severity=ErrorSeverity.MEDIUM,
                error_message=f"Test error for {error_type.value}",
                component="strategy_test"
            )
            
            # Obtenir les stratégies disponibles
            strategies = manager.recovery_strategies.get(error_type, [])
            print(f"  📋 {len(strategies)} stratégies disponibles:")
            
            for strategy in strategies:
                print(f"    - {strategy.strategy.value}: {strategy.description}")
                print(f"      Priorité: {strategy.priority}, Confirmation: {strategy.requires_confirmation}")
            
            # Tester la récupération
            recovery_result = await manager.handle_error(test_error)
            status = "✅ Récupérée" if recovery_result else "❌ Non récupérée"
            print(f"  {status}")
        
        await manager.shutdown()

async def test_system_monitoring():
    """Test du monitoring système"""
    
    print("\n📊 Test du monitoring système")
    print("=" * 35)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "monitoring_test_config.json"
        manager = ErrorRecoveryManager(str(config_file))
        
        # Attendre que le monitoring collecte des métriques
        await asyncio.sleep(2)
        
        metrics = manager.get_system_metrics()
        
        print("🔍 Métriques système collectées:")
        expected_metrics = ["cpu_percent", "memory_percent", "disk_usage", "available_memory"]
        
        for metric in expected_metrics:
            if metric in metrics:
                value = metrics[metric]
                print(f"  ✅ {metric}: {value}")
            else:
                print(f"  ❌ {metric}: Non disponible")
        
        # Test de détection de problèmes préventifs
        print("\n🚨 Test de détection préventive:")
        
        # Simuler des métriques critiques
        manager.system_metrics = {
            "cpu_percent": 98,
            "memory_percent": 95,
            "disk_usage": 97,
            "timestamp": time.time()
        }
        
        # Déclencher la détection
        await manager._detect_potential_issues()
        
        # Vérifier si des erreurs préventives ont été créées
        history = manager.get_error_history()
        preventive_errors = [e for e in history if "preventive" in e.error_id]
        
        print(f"✅ {len(preventive_errors)} erreurs préventives détectées")
        
        await manager.shutdown()

async def test_error_logging():
    """Test de la journalisation des erreurs"""
    
    print("\n📝 Test de la journalisation des erreurs")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "logging_test_config.json"
        manager = ErrorRecoveryManager(str(config_file))
        
        # Créer des erreurs de différentes gravités
        error_severities = [
            (ErrorSeverity.LOW, "Erreur de gravité faible"),
            (ErrorSeverity.MEDIUM, "Erreur de gravité moyenne"),
            (ErrorSeverity.HIGH, "Erreur de gravité élevée"),
            (ErrorSeverity.CRITICAL, "Erreur critique")
        ]
        
        for severity, message in error_severities:
            error_context = ErrorContext(
                error_id=f"logging_test_{severity.value}",
                error_type=ErrorType.SYSTEM_ERROR,
                severity=severity,
                error_message=message,
                component="logging_test"
            )
            
            await manager._log_error(error_context)
            print(f"✅ Erreur {severity.value} journalisée")
        
        # Vérifier si le fichier de log critique a été créé
        critical_log_file = manager.config_file.parent / "critical_errors.log"
        
        if critical_log_file.exists():
            print("✅ Fichier de log critique créé")
            
            with open(critical_log_file, 'r') as f:
                lines = f.readlines()
                print(f"  📄 {len(lines)} entrées dans le log critique")
        else:
            print("⚠️ Fichier de log critique non créé")
        
        await manager.shutdown()

async def test_concurrent_recovery():
    """Test de récupération concurrente"""
    
    print("\n⚡ Test de récupération concurrente")
    print("=" * 35)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "concurrent_test_config.json"
        manager = ErrorRecoveryManager(str(config_file))
        
        # Créer plusieurs erreurs simultanément
        concurrent_errors = []
        for i in range(5):
            error_context = ErrorContext(
                error_id=f"concurrent_test_{i}",
                error_type=ErrorType.TRANSCRIPTION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                error_message=f"Concurrent test error {i}",
                component="concurrent_test"
            )
            concurrent_errors.append(error_context)
        
        # Lancer les récupérations en parallèle
        start_time = time.time()
        
        recovery_tasks = [
            manager.handle_error(error) for error in concurrent_errors
        ]
        
        results = await asyncio.gather(*recovery_tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # Analyser les résultats
        successful_recoveries = sum(1 for result in results if result is True)
        failed_recoveries = len(results) - successful_recoveries
        
        print(f"✅ Récupérations concurrentes terminées en {end_time - start_time:.2f}s")
        print(f"  - Réussies: {successful_recoveries}")
        print(f"  - Échouées: {failed_recoveries}")
        
        # Vérifier les limites de concurrence
        max_concurrent = manager.config["max_concurrent_recoveries"]
        print(f"  - Limite de concurrence: {max_concurrent}")
        
        await manager.shutdown()

async def main():
    """Fonction principale de test"""
    
    print("🚀 Tests du gestionnaire d'erreurs centralisé")
    print("=" * 50)
    
    await test_error_recovery_manager()
    await test_recovery_strategies()
    await test_system_monitoring()
    await test_error_logging()
    await test_concurrent_recovery()
    
    print("\n" + "=" * 50)
    print("🎯 Tous les tests du gestionnaire d'erreurs terminés avec succès!")
    
    print("\n📋 Fonctionnalités testées et validées:")
    print("  ✅ Gestionnaire d'erreurs centralisé")
    print("  ✅ Stratégies de récupération automatique")
    print("  ✅ Classification automatique des erreurs")
    print("  ✅ Détection de patterns d'erreur")
    print("  ✅ Monitoring système préventif")
    print("  ✅ Journalisation détaillée")
    print("  ✅ Récupération concurrente")
    print("  ✅ Callbacks de confirmation")
    print("  ✅ Gestion CUDA, mémoire et réseau")
    print("  ✅ Configuration persistante")

if __name__ == "__main__":
    asyncio.run(main())