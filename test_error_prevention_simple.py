"""
Test simple de l'analyseur de prévention d'erreurs
"""

import asyncio
import time
import logging
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_error_prevention_basic():
    """Test de base de l'analyseur de prévention d'erreurs"""
    
    print("=== Test Simple de l'Analyseur de Prévention d'Erreurs ===\n")
    
    try:
        # Import local pour éviter les problèmes de dépendances
        from ai_video_dubbing.performance.error_prevention_analyzer import (
            ErrorPreventionAnalyzer,
            PreventionLevel,
            PreventionAction
        )
        
        print("✅ Imports réussis")
        
        # 1. Test d'initialisation
        print("\n1. Test d'initialisation...")
        analyzer = ErrorPreventionAnalyzer()
        print(f"   ✅ Analyseur initialisé")
        
        # Vérifier que les règles par défaut sont chargées
        rules = analyzer.prevention_rules
        print(f"   📋 Règles de prévention chargées: {len(rules)}")
        
        for rule_id, rule in list(rules.items())[:3]:  # Afficher les 3 premières
            print(f"   - {rule.name} ({rule.prevention_level.name})")
        
        # 2. Test de collecte de métriques de santé
        print("\n2. Test de collecte de métriques...")
        try:
            health_metrics = await analyzer._collect_health_metrics()
            print(f"   ✅ Métriques collectées:")
            print(f"   - CPU: {health_metrics.cpu_usage:.1f}%")
            print(f"   - Mémoire: {health_metrics.memory_usage:.1f}%")
            print(f"   - Disque: {health_metrics.disk_usage:.1f}%")
            print(f"   - Processus actifs: {health_metrics.active_processes}")
        except Exception as e:
            print(f"   ⚠️ Erreur lors de la collecte: {e}")
        
        # 3. Test des statistiques
        print("\n3. Test des statistiques...")
        stats = analyzer.get_prevention_stats()
        print(f"   📊 Statistiques:")
        print(f"   - Alertes générées: {stats['alerts_generated']}")
        print(f"   - Problèmes prévenus: {stats['problems_prevented']}")
        print(f"   - Optimisations automatiques: {stats['automatic_optimizations']}")
        
        # 4. Test de vérification manuelle (sans déclencher les règles)
        print("\n4. Test de vérification des règles...")
        rules_tested = 0
        rules_triggered = 0
        
        for rule in list(analyzer.prevention_rules.values())[:3]:  # Tester 3 règles
            try:
                should_trigger = await analyzer._execute_rule_check(rule)
                rules_tested += 1
                if should_trigger:
                    rules_triggered += 1
                    print(f"   ⚠️ Règle déclenchée: {rule.name}")
                else:
                    print(f"   ✅ Règle OK: {rule.name}")
            except Exception as e:
                print(f"   ❌ Erreur règle {rule.name}: {e}")
        
        print(f"   📋 Règles testées: {rules_tested}, déclenchées: {rules_triggered}")
        
        # 5. Test de la configuration
        print("\n5. Test de la configuration...")
        config = analyzer.config
        print(f"   ⚙️ Configuration:")
        print(f"   - Intervalle monitoring: {config['monitoring_interval']}s")
        print(f"   - Seuil mémoire critique: {config['critical_memory_threshold']*100}%")
        print(f"   - Nettoyage proactif: {config['enable_proactive_cleanup']}")
        
        # 6. Test des alertes actives
        print("\n6. Test des alertes...")
        active_alerts = analyzer.get_active_alerts()
        alert_history = analyzer.get_alert_history(limit=5)
        print(f"   📢 Alertes actives: {len(active_alerts)}")
        print(f"   📜 Historique: {len(alert_history)} alertes")
        
        # 7. Test de santé système
        print("\n7. Test de santé système...")
        health_metrics = analyzer.get_health_metrics()
        if health_metrics:
            print(f"   💓 Dernières métriques:")
            print(f"   - Timestamp: {time.ctime(health_metrics.timestamp)}")
            print(f"   - Mémoire disponible: {health_metrics.available_memory_mb:.0f} MB")
        else:
            print("   ⚠️ Aucune métrique de santé disponible")
        
        print("\n✅ Test de base terminé avec succès!")
        
        # Arrêter proprement l'analyseur
        await analyzer.shutdown()
        print("🔄 Analyseur arrêté proprement")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Vérifiez que le module error_prevention_analyzer est correctement installé")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        import traceback
        traceback.print_exc()

async def test_system_metrics():
    """Test simple des métriques système"""
    
    print("\n=== Test des Métriques Système ===\n")
    
    try:
        import psutil
        
        print("📊 Métriques système actuelles:")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   🖥️ CPU: {cpu_percent:.1f}%")
        
        # Mémoire
        memory = psutil.virtual_memory()
        print(f"   💾 Mémoire: {memory.percent:.1f}% utilisée")
        print(f"   💾 Disponible: {memory.available / (1024*1024):.0f} MB")
        
        # Disque
        disk = psutil.disk_usage('/')
        print(f"   💿 Disque: {disk.percent:.1f}% utilisé")
        print(f"   💿 Libre: {disk.free / (1024*1024*1024):.1f} GB")
        
        # Processus
        processes = len(psutil.pids())
        print(f"   🔄 Processus actifs: {processes}")
        
        # GPU (si disponible)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                print(f"   🎮 GPU: {gpu.load*100:.1f}% charge")
                print(f"   🎮 GPU Mémoire: {gpu.memoryUtil*100:.1f}%")
                print(f"   🌡️ GPU Température: {gpu.temperature}°C")
            else:
                print("   🎮 Aucun GPU détecté")
        except ImportError:
            print("   🎮 GPUtil non disponible")
        
        print("\n✅ Métriques collectées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la collecte des métriques: {e}")

async def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests de prévention d'erreurs\n")
    
    # Test des métriques système
    await test_system_metrics()
    
    # Test principal
    await test_error_prevention_basic()
    
    print("\n🎉 Tous les tests terminés!")

if __name__ == "__main__":
    asyncio.run(main())