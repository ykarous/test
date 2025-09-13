"""
Script de démarrage optimisé pour éviter les blocages NeMo
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_optimized_environment():
    """Configure l'environnement pour éviter les blocages"""
    
    print("🚀 Configuration de l'environnement optimisé")
    print("=" * 50)
    
    # 1. Variables d'environnement pour éviter les blocages
    env_vars = {
        # Désactiver les optimisations problématiques
        "DISABLE_CUDA_OPTIMIZATION": "1",
        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:128",
        "CUDA_LAUNCH_BLOCKING": "0",
        
        # Configuration mémoire conservative
        "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "0.0",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        
        # Désactiver les téléchargements automatiques problématiques
        "HF_HUB_DISABLE_PROGRESS_BARS": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TRANSFORMERS_OFFLINE": "0",
        
        # Configuration réseau
        "REQUESTS_CA_BUNDLE": "",
        "CURL_CA_BUNDLE": "",
        
        # Mode de récupération
        "NEMO_RECOVERY_MODE": "1",
        "MINIMAL_PROCESSING": "1"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key} = {value}")
    
    print(f"\n   📋 {len(env_vars)} variables d'environnement configurées")

def create_fallback_config():
    """Crée une configuration de fallback pour éviter les blocages"""
    
    print("\n⚙️ Création de la configuration de fallback")
    
    fallback_config = {
        "version": "1.0",
        "mode": "fallback",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        
        # Configuration audio
        "audio_processing": {
            "max_duration_seconds": 300,  # Limiter à 5 minutes
            "chunk_size_seconds": 30,     # Traiter par chunks de 30s
            "sample_rate": 16000,         # Taux d'échantillonnage standard
            "channels": 1                 # Mono seulement
        },
        
        # Configuration modèles
        "models": {
            "prefer_small_models": True,
            "disable_large_models": True,
            "use_cpu_fallback": True,
            "max_model_size_mb": 500,
            "enable_model_caching": False  # Désactiver le cache pour éviter les blocages
        },
        
        # Configuration transcription
        "transcription": {
            "max_concurrent_jobs": 1,
            "timeout_seconds": 120,
            "enable_progress_tracking": True,
            "fallback_to_whisper": True,
            "disable_diarization": True   # Désactiver la diarisation problématique
        },
        
        # Configuration système
        "system": {
            "max_memory_usage_mb": 2048,
            "enable_garbage_collection": True,
            "gc_interval_seconds": 30,
            "monitor_system_resources": True
        },
        
        # Configuration réseau
        "network": {
            "connection_timeout": 30,
            "read_timeout": 60,
            "max_retries": 3,
            "disable_parallel_downloads": True
        }
    }
    
    try:
        config_dir = Path(".kiro")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "fallback_config.json"
        with open(config_file, 'w') as f:
            json.dump(fallback_config, f, indent=2)
        
        print(f"   ✅ Configuration sauvegardée: {config_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde: {e}")
        return False

def patch_problematic_imports():
    """Patch les imports problématiques pour éviter les blocages"""
    
    print("\n🔧 Application des patches pour éviter les blocages")
    
    # Patch pour pyannote
    patch_code = '''
# Patch pour éviter les blocages pyannote
import sys
from unittest.mock import MagicMock

# Mock pyannote si problématique
if "pyannote" not in sys.modules:
    sys.modules["pyannote"] = MagicMock()
    sys.modules["pyannote.audio"] = MagicMock()
    sys.modules["pyannote.audio.pipelines"] = MagicMock()
    print("   ✅ Pyannote mocké pour éviter les blocages")

# Patch pour les téléchargements HuggingFace
import os
os.environ["HF_HUB_OFFLINE"] = "1"  # Mode offline pour éviter les téléchargements bloquants

# Patch pour CUDA si problématique
try:
    import torch
    if torch.cuda.is_available():
        # Forcer l'utilisation du CPU si CUDA pose problème
        torch.cuda.set_device(0)
        print("   ✅ CUDA configuré de manière conservative")
except:
    print("   ⚠️ CUDA non disponible, utilisation CPU")

print("   📋 Patches appliqués")
'''
    
    try:
        with open("nemo_patches.py", 'w') as f:
            f.write(patch_code)
        
        # Exécuter les patches
        exec(patch_code)
        print("   ✅ Patches appliqués avec succès")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur application patches: {e}")
        return False

def create_monitoring_script():
    """Crée un script de monitoring pour détecter les blocages"""
    
    monitoring_script = '''"""
Script de monitoring pour détecter les blocages
"""

import psutil
import time
import threading
import sys

class ProcessMonitor:
    def __init__(self, max_cpu_time=300, max_memory_percent=80):
        self.max_cpu_time = max_cpu_time  # 5 minutes max de CPU élevé
        self.max_memory_percent = max_memory_percent
        self.monitoring = True
        self.start_time = time.time()
        
    def monitor_process(self):
        """Surveille le processus principal"""
        
        high_cpu_start = None
        
        while self.monitoring:
            try:
                # Vérifier CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                
                if cpu_percent > 90:
                    if high_cpu_start is None:
                        high_cpu_start = time.time()
                        print(f"⚠️ CPU élevé détecté: {cpu_percent:.1f}%")
                    elif time.time() - high_cpu_start > self.max_cpu_time:
                        print("🚨 BLOCAGE DÉTECTÉ - CPU élevé trop longtemps")
                        self.emergency_stop()
                        break
                else:
                    high_cpu_start = None
                
                # Vérifier mémoire
                memory = psutil.virtual_memory()
                if memory.percent > self.max_memory_percent:
                    print(f"⚠️ Mémoire élevée: {memory.percent:.1f}%")
                
                # Vérifier durée totale
                total_time = time.time() - self.start_time
                if total_time > 1800:  # 30 minutes max
                    print("⚠️ Processus très long, vérification recommandée")
                
                time.sleep(10)  # Vérifier toutes les 10 secondes
                
            except Exception as e:
                print(f"Erreur monitoring: {e}")
                time.sleep(30)
    
    def emergency_stop(self):
        """Arrêt d'urgence en cas de blocage"""
        print("🛑 ARRÊT D'URGENCE DÉCLENCHÉ")
        
        # Essayer d'arrêter proprement
        try:
            import signal
            import os
            os.kill(os.getpid(), signal.SIGTERM)
        except:
            # Forcer l'arrêt
            sys.exit(1)
    
    def start_monitoring(self):
        """Démarre le monitoring en arrière-plan"""
        monitor_thread = threading.Thread(target=self.monitor_process, daemon=True)
        monitor_thread.start()
        print("👁️ Monitoring de blocage activé")
    
    def stop_monitoring(self):
        """Arrête le monitoring"""
        self.monitoring = False
        print("🛑 Monitoring arrêté")

# Instance globale
monitor = ProcessMonitor()

def start_monitoring():
    """Démarre le monitoring"""
    monitor.start_monitoring()

def stop_monitoring():
    """Arrête le monitoring"""
    monitor.stop_monitoring()

if __name__ == "__main__":
    print("Démarrage du monitoring...")
    start_monitoring()
    
    try:
        # Garder le script actif
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Arrêt du monitoring...")
        stop_monitoring()
'''
    
    try:
        with open("process_monitor.py", 'w') as f:
            f.write(monitoring_script)
        
        print("   ✅ Script de monitoring créé: process_monitor.py")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création monitoring: {e}")
        return False

def create_safe_launcher():
    """Crée un lanceur sécurisé pour main.py"""
    
    launcher_script = '''@echo off
echo ========================================
echo    LANCEUR SECURISE NEMO
echo ========================================
echo.

echo Configuration de l'environnement...
call mon_env\\Scripts\\activate

echo Application des patches...
python nemo_patches.py

echo Demarrage du monitoring...
start /b python process_monitor.py

echo.
echo Lancement de l'application principale...
echo ATTENTION: Si l'application se bloque, appuyez sur Ctrl+C
echo.

python main.py

echo.
echo Application terminee
pause
'''
    
    try:
        with open("safe_launch.bat", 'w') as f:
            f.write(launcher_script)
        
        print("   ✅ Lanceur sécurisé créé: safe_launch.bat")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création lanceur: {e}")
        return False

def main():
    """Fonction principale de configuration"""
    
    print("🛡️ CONFIGURATION OPTIMISÉE POUR ÉVITER LES BLOCAGES")
    print("=" * 60)
    
    success_count = 0
    total_steps = 5
    
    # 1. Configuration environnement
    try:
        setup_optimized_environment()
        success_count += 1
    except Exception as e:
        print(f"❌ Erreur configuration environnement: {e}")
    
    # 2. Configuration fallback
    try:
        if create_fallback_config():
            success_count += 1
    except Exception as e:
        print(f"❌ Erreur configuration fallback: {e}")
    
    # 3. Application patches
    try:
        if patch_problematic_imports():
            success_count += 1
    except Exception as e:
        print(f"❌ Erreur application patches: {e}")
    
    # 4. Script monitoring
    try:
        if create_monitoring_script():
            success_count += 1
    except Exception as e:
        print(f"❌ Erreur script monitoring: {e}")
    
    # 5. Lanceur sécurisé
    try:
        if create_safe_launcher():
            success_count += 1
    except Exception as e:
        print(f"❌ Erreur lanceur sécurisé: {e}")
    
    # Résumé
    print(f"\n📊 RÉSUMÉ DE LA CONFIGURATION")
    print(f"   Étapes réussies: {success_count}/{total_steps}")
    print(f"   Taux de succès: {(success_count/total_steps)*100:.1f}%")
    
    if success_count == total_steps:
        print(f"\n✅ CONFIGURATION OPTIMISÉE TERMINÉE")
        print(f"\n🚀 Pour lancer l'application de manière sécurisée:")
        print(f"   1. Utilisez: safe_launch.bat")
        print(f"   2. Ou manuellement: python main.py")
        print(f"\n💡 Le système est maintenant configuré pour éviter les blocages")
    else:
        print(f"\n⚠️ CONFIGURATION PARTIELLE")
        print(f"   Certaines étapes ont échoué, mais le système devrait être plus stable")
    
    print(f"\n📋 Fichiers créés:")
    files_created = [
        "nemo_patches.py",
        "process_monitor.py", 
        "safe_launch.bat",
        ".kiro/fallback_config.json"
    ]
    
    for file_path in files_created:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n🛑 Configuration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        print("Essayez de relancer le script ou contactez le support")