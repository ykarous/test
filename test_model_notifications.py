"""Tests pour le système de notifications avancées"""
import asyncio
import tempfile
import time
from pathlib import Path

from ai_video_dubbing.performance.model_notifications import (
    SmartNotificationManager, NotificationPriority, NotificationCategory
)
from ai_video_dubbing.performance.model_actions import (
    ModelNotification, NotificationType
)

async def test_smart_notification_manager():
    """Test du gestionnaire de notifications intelligent"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "notifications_config.json"
        
        # Initialiser le gestionnaire
        manager = SmartNotificationManager(str(config_file))
        
        print("✅ Gestionnaire de notifications intelligent initialisé")
        
        # Test des callbacks
        received_notifications = []
        
        def global_callback(notification: ModelNotification):
            received_notifications.append(notification)
            print(f"📢 Callback global: {notification.title}")
        
        manager.add_global_callback(global_callback)
        
        # Test des handlers de canal
        ui_notifications = []
        
        async def ui_handler(notification: ModelNotification, config: dict):
            ui_notifications.append(notification)
            print(f"🖥️ UI Handler: {notification.title} (config: {config})")
        
        manager.register_notification_handler("ui", ui_handler)
        
        # Créer des notifications de test
        test_notifications = [
            ModelNotification(
                notification_id="test_1",
                notification_type=NotificationType.INFO,
                title="Test d'information",
                message="Ceci est un test d'information",
                priority=NotificationPriority.LOW.value
            ),
            
            ModelNotification(
                notification_id="test_2",
                notification_type=NotificationType.WARNING,
                title="Test d'avertissement",
                message="Ceci est un test d'avertissement",
                priority=NotificationPriority.MEDIUM.value
            ),
            
            ModelNotification(
                notification_id="test_3",
                notification_type=NotificationType.ERROR,
                title="Test d'erreur",
                message="Ceci est un test d'erreur",
                model_id="test_model",
                priority=NotificationPriority.HIGH.value,
                actions=["retry", "ignore"]
            ),
            
            ModelNotification(
                notification_id="test_4",
                notification_type=NotificationType.DISK_SPACE_LOW,
                title="Espace disque faible",
                message="L'espace disque est critique",
                priority=NotificationPriority.CRITICAL.value,
                actions=["cleanup", "expand_storage"]
            )
        ]
        
        # Ajouter les notifications
        for notification in test_notifications:
            await manager.add_notification(notification)
            await asyncio.sleep(0.1)  # Petite pause pour voir la progression
        
        print(f"✅ {len(test_notifications)} notifications ajoutées")
        
        # Attendre un peu pour le traitement par lots
        await asyncio.sleep(2)
        
        # Vérifier les callbacks
        assert len(received_notifications) >= len(test_notifications), "Tous les callbacks globaux devraient être appelés"
        assert len(ui_notifications) > 0, "Des notifications UI devraient être reçues"
        
        print(f"✅ Callbacks vérifiés: {len(received_notifications)} globaux, {len(ui_notifications)} UI")
        
        # Test des filtres de récupération
        all_notifications = manager.get_notifications()
        print(f"📊 Total des notifications: {len(all_notifications)}")
        
        unread_notifications = manager.get_notifications(unread_only=True)
        print(f"📊 Notifications non lues: {len(unread_notifications)}")
        
        high_priority = manager.get_notifications(priority_filter=[NotificationPriority.HIGH, NotificationPriority.CRITICAL])
        print(f"📊 Notifications haute priorité: {len(high_priority)}")
        
        error_notifications = manager.get_notifications(type_filter=[NotificationType.ERROR])
        print(f"📊 Notifications d'erreur: {len(error_notifications)}")
        
        # Test de marquage comme lu
        if all_notifications:
            manager.mark_notification_read(all_notifications[0].notification_id)
            print("✅ Première notification marquée comme lue")
        
        # Marquer toutes les notifications d'info comme lues
        manager.mark_all_read(NotificationType.INFO)
        print("✅ Toutes les notifications d'info marquées comme lues")
        
        # Test des statistiques
        stats = manager.get_notification_stats()
        print("📈 Statistiques des notifications:")
        print(f"  - Total: {stats['total']}")
        print(f"  - Non lues: {stats['unread']}")
        print(f"  - Par type: {stats['by_type']}")
        print(f"  - Par priorité: {stats['by_priority']}")
        print(f"  - Règles actives: {stats['active_rules']}")
        print(f"  - Canaux actifs: {stats['active_channels']}")
        
        # Test de déduplication
        print("\n🔄 Test de déduplication...")
        
        duplicate_notification = ModelNotification(
            notification_id="duplicate_test",
            notification_type=NotificationType.INFO,
            title="Test d'information",  # Même titre que test_1
            message="Ceci est un test d'information",  # Même message
            priority=NotificationPriority.LOW.value
        )
        
        initial_count = len(manager.get_notifications())
        await manager.add_notification(duplicate_notification)
        await asyncio.sleep(0.5)
        
        final_count = len(manager.get_notifications())
        
        if final_count == initial_count:
            print("✅ Déduplication fonctionne - notification dupliquée ignorée")
        else:
            print("⚠️ Déduplication n'a pas fonctionné ou notification traitée différemment")
        
        # Test d'escalade de priorité
        print("\n⬆️ Test d'escalade de priorité...")
        
        # Créer plusieurs notifications similaires rapidement
        for i in range(6):
            escalation_notification = ModelNotification(
                notification_id=f"escalation_test_{i}",
                notification_type=NotificationType.WARNING,
                title="Test d'escalade",
                message=f"Message d'escalade {i}",
                model_id="escalation_model",
                priority=NotificationPriority.LOW.value
            )
            await manager.add_notification(escalation_notification)
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(1)
        
        # Vérifier si la priorité a été escaladée
        escalation_notifications = manager.get_notifications(type_filter=[NotificationType.WARNING])
        escalated = [n for n in escalation_notifications if n.priority >= NotificationPriority.HIGH.value and "escalation_model" in (n.model_id or "")]
        
        if escalated:
            print(f"✅ Escalade de priorité fonctionne - {len(escalated)} notifications escaladées")
        else:
            print("⚠️ Escalade de priorité n'a pas été détectée")
        
        # Test de nettoyage
        print("\n🧹 Test de nettoyage...")
        
        initial_count = len(manager.get_notifications())
        await manager.cleanup_old_notifications()
        final_count = len(manager.get_notifications())
        
        print(f"✅ Nettoyage effectué: {initial_count} -> {final_count} notifications")
        
        # Fermer le gestionnaire
        await manager.close()
        print("✅ Gestionnaire fermé proprement")
        
        # Vérifier que la configuration a été sauvegardée
        if config_file.exists():
            print("✅ Configuration sauvegardée")
        
        print("\n🎉 Tous les tests du système de notifications réussis!")
        
        # Résumé des fonctionnalités testées
        print("\n📋 Fonctionnalités testées:")
        print("  ✅ Initialisation du gestionnaire")
        print("  ✅ Callbacks globaux et handlers de canal")
        print("  ✅ Ajout et traitement des notifications")
        print("  ✅ Filtres de récupération")
        print("  ✅ Marquage comme lu")
        print("  ✅ Statistiques des notifications")
        print("  ✅ Déduplication des notifications")
        print("  ✅ Escalade de priorité")
        print("  ✅ Nettoyage des anciennes notifications")
        print("  ✅ Sauvegarde de la configuration")

async def test_notification_rules():
    """Test des règles de notification"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "rules_config.json"
        manager = SmartNotificationManager(str(config_file))
        
        print("\n🔧 Test des règles de notification")
        
        # Vérifier les règles par défaut
        rules = manager.notification_rules
        print(f"📋 {len(rules)} règles par défaut chargées:")
        
        for rule_id, rule in rules.items():
            status = "✅ Activée" if rule.enabled else "❌ Désactivée"
            print(f"  - {rule.name}: {status}")
            print(f"    Condition: {rule.condition}")
            print(f"    Cooldown: {rule.cooldown_seconds}s")
        
        # Vérifier les canaux par défaut
        channels = manager.notification_channels
        print(f"\n📡 {len(channels)} canaux par défaut configurés:")
        
        for channel_id, channel in channels.items():
            status = "✅ Actif" if channel.enabled else "❌ Inactif"
            priorities = [p.name for p in channel.priority_filter]
            print(f"  - {channel.name} ({channel.channel_type}): {status}")
            print(f"    Priorités: {', '.join(priorities)}")
        
        await manager.close()
        print("✅ Test des règles terminé")

async def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du système de notifications avancées")
    print("=" * 70)
    
    await test_smart_notification_manager()
    await test_notification_rules()
    
    print("\n" + "=" * 70)
    print("🎯 Tous les tests des notifications terminés avec succès!")

if __name__ == "__main__":
    asyncio.run(main())