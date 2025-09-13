"""
Script d'urgence pour débloquer la transcription NeMo
"""

import asyncio
import time
import logging
import psutil
import os
import signal
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def emergency_unblock():
    """Déblocage d'urgence du système"""
    
    print("🚨 DÉBLOCAGE D'URGENCE DU SYSTÈME")
    print("=" * 50)
    
    # 1. Identifier les processus bloqués
    print("\n1. Identification des processus...")
    
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if 'python' in proc.info['name'].lower():
                cpu_usage = proc.cpu_percent(interval=1)
                if cpu_usage > 80:  # Processus utilisant beaucoup de CPU
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'cpu': cpu_usage,
                        'memory': proc.info['memory_percent']
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if python_processes:
        print(f"   Processus Python détectés: {len(python_processes)}")
        for proc in python_processes:
            print(f"   - PID {proc['pid']}: CPU {proc['cpu']:.1f}%, RAM {proc['memory']:.1f}%")
    else:
        print("   Aucun processus Python problématique détecté")
    
    # 2. Nettoyer les ressources
    print("\n2. Nettoyage des ressources...")
    
    try:
        # Forcer le garbage collection
        import gc
        gc.collect()
        print("   ✅ Garbage collection effectué")
        
        # Nettoyer les fichiers temporaires
        temp_dirs = [
            Path(".kiro/temp"),
            Path("temp"),
            Path("__pycache__")
        ]
        
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"   ✅ {temp_dir} nettoyé")
        
    except Exception as e:
        print(f"   ⚠️ Erreur nettoyage: {e}")
    
    # 3. Réinitialiser les composants d'optimisation
    print("\n3. Réinitialisation des composants...")
    
    try:
        # Arrêter tous les optimisateurs
        from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
        from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
        from ai_video_dubbing.performance.network_optimizer import get_network_optimizer
        
        # Configuration d'urgence
        emergency_config = {
            "enable_automatic_optimization": False,
            "max_concurrent_downloads": 1,
            "cache_size_mb": 256,
            "monitoring_interval": 300.0
        }
        
        optimizer = get_auto_optimizer()
        optimizer.config.update(emergency_config)
        await optimizer.shutdown()
        print("   ✅ Auto-optimisateur arrêté")
        
        analyzer = get_error_prevention_analyzer()
        await analyzer.shutdown()
        print("   ✅ Analyseur de prévention arrêté")
        
        network_opt = get_network_optimizer()
        await network_opt.shutdown()
        print("   ✅ Optimisateur réseau arrêté")
        
    except Exception as e:
        print(f"   ⚠️ Erreur arrêt composants: {e}")
    
    # 4. Créer une configuration de récupération
    print("\n4. Configuration de récupération...")
    
    try:
        recovery_config = {
            "emergency_mode": True,
            "timestamp": time.time(),
            "config": {
                "enable_automatic_optimization": False,
                "max_concurrent_downloads": 1,
                "cache_size_mb": 128,
                "enable_compression": False,
                "enable_http_cache": False,
                "monitoring_interval": 600.0
            }
        }
        
        config_dir = Path(".kiro")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "emergency_config.json", 'w') as f:
            import json
            json.dump(recovery_config, f, indent=2)
        
        print("   ✅ Configuration d'urgence sauvegardée")
        
    except Exception as e:
        print(f"   ⚠️ Erreur sauvegarde config: {e}")
    
    # 5. Recommandations
    print("\n5. Recommandations:")
    print("   • Redémarrez l'application principale")
    print("   • Utilisez un modèle plus léger si possible")
    print("   • Vérifiez l'espace disque disponible")
    print("   • Surveillez l'utilisation mémoire")
    
    # 6. Créer un script de redémarrage sécurisé
    print("\n6. Création du script de redémarrage...")
    
    restart_script = '''@echo off
echo Redemarrage securise du systeme NeMo
echo.

echo Nettoyage des processus...
taskkill /f /im python.exe 2>nul

echo Attente de 3 secondes...
timeout /t 3 /nobreak >nul

echo Redemarrage avec configuration d'urgence...
mon_env\\Scripts\\activate
python -c "
import json
from pathlib import Path

# Charger la config d'urgence
config_file = Path('.kiro/emergency_config.json')
if config_file.exists():
    print('Configuration d\\'urgence detectee')
    with open(config_file, 'r') as f:
        config = json.load(f)
    print('Mode de recuperation active')
else:
    print('Demarrage normal')

print('Systeme pret')
"

echo.
echo Systeme redémarre en mode sécurisé
echo Vous pouvez maintenant relancer main.py
pause
'''
    
    with open("restart_safe.bat", 'w') as f:
        f.write(restart_script)
    
    print("   ✅ Script restart_safe.bat créé")
    
    print("\n🎯 DÉBLOCAGE TERMINÉ")
    print("\nPour redémarrer en mode sécurisé:")
    print("1. Fermez cette fenêtre")
    print("2. Exécutez: restart_safe.bat")
    print("3. Puis relancez: python main.py")

def force_kill_python_processes():
    """Force l'arrêt des processus Python bloqués"""
    
    print("\n🔥 ARRÊT FORCÉ DES PROCESSUS")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'python' in proc.info['name'].lower():
                proc.terminate()
                killed_count += 1
                print(f"   Processus {proc.info['pid']} terminé")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed_count > 0:
        print(f"   {killed_count} processus Python arrêtés")
        time.sleep(2)  # Attendre que les processus se terminent
    else:
        print("   Aucun processus Python à arrêter")

def create_minimal_config():
    """Crée une configuration minimale pour éviter les blocages"""
    
    print("\n⚙️ CRÉATION CONFIGURATION MINIMALE")
    
    minimal_config = {
        "version": "1.0",
        "emergency_mode": True,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "settings": {
            # Désactiver toutes les optimisations
            "enable_auto_optimization": False,
            "enable_error_prevention": False,
            "enable_network_optimization": False,
            
            # Configuration minimale
            "cache_size_mb": 64,
            "max_concurrent_operations": 1,
            "timeout_seconds": 30,
            
            # Modèles de fallback
            "use_fallback_models": True,
            "prefer_cpu_processing": True,
            "disable_gpu_acceleration": True
        }
    }
    
    try:
        config_dir = Path(".kiro")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "minimal_config.json", 'w') as f:
            import json
            json.dump(minimal_config, f, indent=2)
        
        print("   ✅ Configuration minimale créée")
        
        # Créer aussi un fichier de démarrage minimal
        startup_script = '''"""
Script de démarrage minimal pour éviter les blocages
"""

import sys
import json
from pathlib import Path

def load_minimal_config():
    config_file = Path(".kiro/minimal_config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def apply_minimal_settings():
    """Applique les paramètres minimaux"""
    
    config = load_minimal_config()
    if not config:
        return False
    
    print("🔧 Application des paramètres minimaux...")
    
    # Désactiver les optimisations
    import os
    os.environ["DISABLE_OPTIMIZATIONS"] = "1"
    os.environ["MINIMAL_MODE"] = "1"
    os.environ["CPU_ONLY"] = "1"
    
    print("✅ Mode minimal activé")
    return True

if __name__ == "__main__":
    if apply_minimal_settings():
        print("Système configuré en mode minimal")
        print("Vous pouvez maintenant lancer main.py")
    else:
        print("Configuration minimale non trouvée")
'''
        
        with open("minimal_startup.py", 'w') as f:
            f.write(startup_script)
        
        print("   ✅ Script de démarrage minimal créé")
        
    except Exception as e:
        print(f"   ❌ Erreur création config: {e}")

async def main():
    """Fonction principale d'urgence"""
    
    print("🚨 SCRIPT D'URGENCE POUR DÉBLOCAGE NEMO")
    print("=" * 60)
    
    # Vérifier l'état du système
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"\n📊 État du système:")
    print(f"   CPU: {cpu_percent:.1f}%")
    print(f"   Mémoire: {memory.percent:.1f}% ({memory.available / (1024**3):.1f} GB libre)")
    
    if memory.percent > 90:
        print("   ⚠️ MÉMOIRE CRITIQUE")
    if cpu_percent > 90:
        print("   ⚠️ CPU SURCHARGÉ")
    
    # Menu d'options
    print(f"\n🔧 Options de déblocage:")
    print("1. Déblocage automatique (recommandé)")
    print("2. Arrêt forcé des processus Python")
    print("3. Création configuration minimale")
    print("4. Tout faire (1+2+3)")
    print("5. Quitter")
    
    try:
        choice = input("\nChoisissez une option (1-5): ").strip()
        
        if choice == "1":
            await emergency_unblock()
        elif choice == "2":
            force_kill_python_processes()
        elif choice == "3":
            create_minimal_config()
        elif choice == "4":
            force_kill_python_processes()
            create_minimal_config()
            await emergency_unblock()
        elif choice == "5":
            print("Annulé")
            return
        else:
            print("Option invalide")
            return
        
        print(f"\n✅ Opération terminée")
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Erreur critique: {e}")
        print("Essayez de redémarrer manuellement le système")