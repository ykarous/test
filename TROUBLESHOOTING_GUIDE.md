# Guide de Dépannage - Optimisations NeMo

## 🚨 Guide de Résolution Rapide

### Problèmes Critiques (Action Immédiate Requise)

#### ❌ Système Bloqué / Non Responsive

**Symptômes** :
- Interface figée
- Aucune réponse aux commandes
- Processus à 100% CPU

**Solution Immédiate** :
```bash
# 1. Arrêter tous les processus Python
taskkill /f /im python.exe

# 2. Nettoyer les fichiers temporaires
rmdir /s /q .kiro\temp

# 3. Redémarrer avec configuration minimale
mon_env\Scripts\activate
python -c "
from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
opt = get_auto_optimizer()
opt.config['enable_automatic_optimization'] = False
opt.config['max_concurrent_downloads'] = 1
print('Configuration sécurisée activée')
"
```

#### 🔥 Erreur "Out of Memory" Critique

**Symptômes** :
- `CUDA out of memory`
- `MemoryError`
- Système très lent

**Solution Immédiate** :
```python
# Mode de récupération d'urgence
import gc
gc.collect()

from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
optimizer = get_auto_optimizer()

# Configuration d'urgence
emergency_config = {
    "cache_size_mb": 256,              # Cache minimal
    "max_concurrent_downloads": 1,      # Un seul téléchargement
    "enable_compression": True,         # Activer compression
    "enable_automatic_optimization": True
}

optimizer.config.update(emergency_config)
await optimizer.run_manual_optimization()
print("Mode de récupération activé")
```

---

## 🔍 Diagnostic Automatique

### Outil de Diagnostic Rapide

```python
async def quick_diagnostic():
    """Diagnostic rapide du système"""
    
    print("🔍 Diagnostic Rapide du Système")
    print("=" * 40)
    
    # 1. Vérifier les composants
    try:
        from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
        optimizer = get_auto_optimizer()
        print("✅ Auto-optimisateur : OK")
    except Exception as e:
        print(f"❌ Auto-optimisateur : {e}")
    
    try:
        from ai_video_dubbing.performance.network_optimizer import get_network_optimizer
        network = get_network_optimizer()
        print("✅ Optimisateur réseau : OK")
    except Exception as e:
        print(f"❌ Optimisateur réseau : {e}")
    
    try:
        from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
        analyzer = get_error_prevention_analyzer()
        print("✅ Analyseur de prévention : OK")
    except Exception as e:
        print(f"❌ Analyseur de prévention : {e}")
    
    # 2. Vérifier les ressources système
    import psutil
    
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    print(f"\n💾 Mémoire : {memory.percent:.1f}% utilisée")
    if memory.percent > 90:
        print("⚠️ ATTENTION : Mémoire critique")
    
    print(f"💿 Disque : {disk.percent:.1f}% utilisé")
    if disk.percent > 95:
        print("⚠️ ATTENTION : Espace disque critique")
    
    # 3. Vérifier les fichiers de configuration
    from pathlib import Path
    
    config_files = [
        ".kiro/error_recovery_config.json",
        ".kiro/error_prevention_config.json", 
        ".kiro/network_config.json"
    ]
    
    print(f"\n📁 Fichiers de configuration :")
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"⚠️ {config_file} (sera créé automatiquement)")
    
    print("\n🎯 Diagnostic terminé")

# Exécuter le diagnostic
import asyncio
asyncio.run(quick_diagnostic())
```

---

## 🐛 Problèmes Fréquents et Solutions

### 1. Problèmes de Cache

#### Cache Plein ou Corrompu

**Symptômes** :
- Messages "Cache full"
- Erreurs de lecture/écriture
- Performances dégradées

**Diagnostic** :
```python
from ai_video_dubbing.performance.auto_optimizer import IntelligentCacheManager

cache = IntelligentCacheManager()
stats = cache.get_cache_stats()

print(f"Utilisation cache : {stats['usage_percent']:.1f}%")
print(f"Taux de hit : {stats['hit_rate']:.1%}")
print(f"Évictions : {stats['evictions']}")

if stats['usage_percent'] > 95:
    print("⚠️ Cache saturé")
if stats['hit_rate'] < 0.5:
    print("⚠️ Cache inefficace")
```

**Solutions** :

1. **Nettoyage automatique** :
```python
# Nettoyer les entrées expirées
expired = await cache.cleanup_expired_entries(max_age_hours=12)
print(f"Entrées nettoyées : {expired}")
```

2. **Augmenter la taille** :
```python
# Créer un cache plus grand
cache = IntelligentCacheManager(max_size_mb=4096)  # 4GB
```

3. **Réinitialisation complète** :
```python
import shutil
shutil.rmtree(".kiro/cache", ignore_errors=True)
print("Cache réinitialisé")
```

### 2. Problèmes de Téléchargement

#### Téléchargements Lents ou Échoués

**Symptômes** :
- Vitesse < 5 Mbps
- Timeouts fréquents
- Téléchargements interrompus

**Diagnostic** :
```python
from ai_video_dubbing.performance.network_optimizer import get_network_optimizer

optimizer = get_network_optimizer()

# Tester les serveurs
results = await optimizer.test_all_servers()

print("État des serveurs :")
for server_name, result in results.items():
    if result.get('success'):
        print(f"✅ {server_name}: {result['latency_ms']:.1f}ms")
    else:
        print(f"❌ {server_name}: {result.get('error', 'Erreur inconnue')}")
```

**Solutions** :

1. **Optimiser la configuration** :
```python
# Configuration optimisée
optimizer.config.update({
    "max_concurrent_downloads": 4,     # Réduire si instable
    "max_segments_per_download": 6,    # Réduire si timeouts
    "connection_timeout": 60.0,        # Augmenter si lent
    "max_retries": 5                   # Plus de tentatives
})
```

2. **Forcer un serveur spécifique** :
```python
# Utiliser le serveur le plus fiable
best_server = optimizer.get_best_server()
if best_server:
    print(f"Utilisation forcée de : {best_server.name}")
```

3. **Mode de récupération réseau** :
```python
# Configuration de récupération
recovery_config = {
    "max_concurrent_downloads": 1,
    "max_segments_per_download": 1,
    "enable_compression": False,
    "connection_timeout": 120.0
}
optimizer.config.update(recovery_config)
```

### 3. Problèmes de Mémoire

#### Utilisation Mémoire Excessive

**Symptômes** :
- RAM > 8GB utilisée
- Système lent
- Erreurs "Out of memory"

**Diagnostic** :
```python
import psutil
from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer

# Vérifier l'utilisation mémoire
memory = psutil.virtual_memory()
print(f"Mémoire totale : {memory.total / (1024**3):.1f} GB")
print(f"Mémoire utilisée : {memory.used / (1024**3):.1f} GB")
print(f"Mémoire disponible : {memory.available / (1024**3):.1f} GB")

# Vérifier le cache
optimizer = get_auto_optimizer()
cache_stats = optimizer.cache_manager.get_cache_stats()
print(f"Cache : {cache_stats['total_size_mb']:.1f} MB")
```

**Solutions** :

1. **Optimisation immédiate** :
```python
# Nettoyage d'urgence
import gc
gc.collect()

# Optimisation automatique
result = await optimizer.run_manual_optimization()
print(f"Mémoire libérée : {result['total_memory_saved_mb']:.1f} MB")
```

2. **Configuration mémoire réduite** :
```python
# Configuration économe
low_memory_config = {
    "cache_size_mb": 512,              # Cache réduit
    "max_concurrent_downloads": 2,      # Moins de parallélisme
    "enable_compression": True,         # Compression obligatoire
    "cleanup_interval": 300            # Nettoyage fréquent
}

optimizer.config.update(low_memory_config)
```

3. **Mode minimal** :
```python
# Mode ultra-minimal
minimal_cache = IntelligentCacheManager(max_size_mb=128)
print("Mode minimal activé")
```

### 4. Problèmes de Performance

#### Performances Dégradées

**Symptômes** :
- Transcription lente
- Interface non responsive
- CPU à 100%

**Diagnostic** :
```python
# Test de performance rapide
import time

start_time = time.time()

# Test du cache
cache = IntelligentCacheManager(max_size_mb=100)
for i in range(100):
    await cache.set(f"test_{i}", f"data_{i}")

cache_time = time.time() - start_time
print(f"Performance cache : {cache_time:.2f}s pour 100 opérations")

if cache_time > 5.0:
    print("⚠️ Cache lent")

# Test réseau
start_time = time.time()
network = get_network_optimizer()
await network.test_all_servers()
network_time = time.time() - start_time

print(f"Performance réseau : {network_time:.2f}s")
if network_time > 10.0:
    print("⚠️ Réseau lent")
```

**Solutions** :

1. **Optimisation ciblée** :
```python
# Identifier les goulots d'étranglement
from ai_video_dubbing.performance.diagnostic_engine import DiagnosticEngine

engine = DiagnosticEngine()
report = await engine.run_full_diagnostic()

for issue in report['issues']:
    if issue['severity'] == 'HIGH':
        print(f"🔥 Problème critique : {issue['description']}")
        print(f"   Solution : {issue['recommendation']}")
```

2. **Configuration performance** :
```python
# Configuration haute performance
performance_config = {
    "optimization_interval": 180.0,    # Optimisation fréquente
    "enable_predictive_caching": True, # Cache prédictif
    "max_concurrent_downloads": 8,     # Parallélisme max
    "enable_compression": True         # Compression
}

optimizer.config.update(performance_config)
```

---

## 🔧 Outils de Réparation

### Script de Réparation Automatique

```python
async def auto_repair():
    """Script de réparation automatique"""
    
    print("🔧 Démarrage de la réparation automatique")
    
    repairs_done = []
    
    # 1. Nettoyer les fichiers temporaires
    try:
        import shutil
        temp_dirs = [".kiro/temp", ".kiro/logs/old"]
        for temp_dir in temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                repairs_done.append(f"Nettoyé {temp_dir}")
    except Exception as e:
        print(f"⚠️ Erreur nettoyage : {e}")
    
    # 2. Optimiser le cache
    try:
        from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
        optimizer = get_auto_optimizer()
        
        result = await optimizer.run_manual_optimization()
        if result['successful_optimizations'] > 0:
            repairs_done.append(f"Optimisations appliquées : {result['successful_optimizations']}")
    except Exception as e:
        print(f"⚠️ Erreur optimisation : {e}")
    
    # 3. Vérifier et réparer les configurations
    try:
        config_files = {
            ".kiro/error_recovery_config.json": {"config": {"auto_recovery_enabled": True}},
            ".kiro/error_prevention_config.json": {"config": {"monitoring_interval": 30.0}},
            ".kiro/network_config.json": {"config": {"max_concurrent_downloads": 4}}
        }
        
        for config_file, default_config in config_files.items():
            config_path = Path(config_file)
            if not config_path.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                repairs_done.append(f"Créé {config_file}")
    except Exception as e:
        print(f"⚠️ Erreur configuration : {e}")
    
    # 4. Tester les composants
    try:
        from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
        analyzer = get_error_prevention_analyzer()
        
        health_check = await analyzer.run_manual_check()
        if health_check['rules_checked'] > 0:
            repairs_done.append("Vérification santé système OK")
    except Exception as e:
        print(f"⚠️ Erreur vérification : {e}")
    
    # Résumé
    print(f"\n✅ Réparation terminée - {len(repairs_done)} actions effectuées :")
    for repair in repairs_done:
        print(f"   • {repair}")
    
    if not repairs_done:
        print("ℹ️ Aucune réparation nécessaire")

# Exécuter la réparation
import asyncio
asyncio.run(auto_repair())
```

### Réinitialisation Complète

```python
def complete_reset():
    """Réinitialisation complète du système"""
    
    print("🔄 Réinitialisation complète du système")
    print("⚠️ ATTENTION : Toutes les configurations seront perdues")
    
    import shutil
    import os
    from pathlib import Path
    
    # Confirmer l'action
    confirm = input("Tapez 'RESET' pour confirmer : ")
    if confirm != "RESET":
        print("Annulé")
        return
    
    # Supprimer tous les fichiers de configuration
    kiro_dir = Path(".kiro")
    if kiro_dir.exists():
        shutil.rmtree(kiro_dir, ignore_errors=True)
        print("✅ Répertoire .kiro supprimé")
    
    # Supprimer les caches temporaires
    temp_dirs = ["temp", "__pycache__"]
    for temp_dir in temp_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"✅ {temp_dir} supprimé")
    
    # Recréer la structure de base
    kiro_dir.mkdir(exist_ok=True)
    (kiro_dir / "cache").mkdir(exist_ok=True)
    (kiro_dir / "logs").mkdir(exist_ok=True)
    (kiro_dir / "reports").mkdir(exist_ok=True)
    
    print("✅ Structure de base recréée")
    print("🎯 Réinitialisation terminée - Redémarrez l'application")

# Utilisation : complete_reset()
```

---

## 📊 Monitoring et Alertes

### Surveillance Continue

```python
async def continuous_monitoring():
    """Surveillance continue du système"""
    
    from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
    import asyncio
    
    analyzer = get_error_prevention_analyzer()
    
    print("👁️ Surveillance continue activée")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    try:
        while True:
            # Vérification de santé
            health = analyzer.get_health_metrics()
            
            if health:
                # Alertes critiques
                if health.memory_usage > 90:
                    print(f"🚨 ALERTE : Mémoire critique {health.memory_usage:.1f}%")
                
                if health.disk_usage > 95:
                    print(f"🚨 ALERTE : Disque critique {health.disk_usage:.1f}%")
                
                if health.cpu_usage > 95:
                    print(f"🚨 ALERTE : CPU critique {health.cpu_usage:.1f}%")
                
                # Status normal
                if health.memory_usage < 80 and health.disk_usage < 90:
                    print(f"✅ Système OK - CPU:{health.cpu_usage:.1f}% RAM:{health.memory_usage:.1f}% Disk:{health.disk_usage:.1f}%")
            
            await asyncio.sleep(30)  # Vérification toutes les 30 secondes
            
    except KeyboardInterrupt:
        print("\n🛑 Surveillance arrêtée")
    
    finally:
        await analyzer.shutdown()

# Lancer la surveillance
# asyncio.run(continuous_monitoring())
```

### Alertes par Email (Optionnel)

```python
def setup_email_alerts():
    """Configuration des alertes par email"""
    
    # Configuration email (à adapter)
    EMAIL_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "votre_email@gmail.com",
        "password": "votre_mot_de_passe",
        "recipient": "admin@votre-domaine.com"
    }
    
    async def send_alert(message):
        """Envoyer une alerte par email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(f"Alerte Système NeMo:\n\n{message}")
            msg['Subject'] = "🚨 Alerte Système NeMo"
            msg['From'] = EMAIL_CONFIG["username"]
            msg['To'] = EMAIL_CONFIG["recipient"]
            
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.starttls()
                server.login(EMAIL_CONFIG["username"], EMAIL_CONFIG["password"])
                server.send_message(msg)
            
            print("📧 Alerte envoyée par email")
            
        except Exception as e:
            print(f"❌ Erreur envoi email : {e}")
    
    # Ajouter le callback d'alerte
    from ai_video_dubbing.performance.error_prevention_analyzer import get_error_prevention_analyzer
    
    analyzer = get_error_prevention_analyzer()
    analyzer.add_alert_callback(send_alert)
    
    print("📧 Alertes email configurées")

# setup_email_alerts()
```

---

## 🆘 Support d'Urgence

### Contacts et Ressources

1. **Diagnostic Immédiat** :
   ```bash
   python -c "
   import asyncio
   from test_performance_suite import PerformanceTestSuite
   suite = PerformanceTestSuite()
   asyncio.run(suite.run_all_tests())
   "
   ```

2. **Logs Système** :
   - Logs généraux : `.kiro/logs/`
   - Logs d'erreurs critiques : `.kiro/critical_errors.log`
   - Rapports de performance : `.kiro/performance_reports/`

3. **Informations Système** :
   ```python
   import platform
   import sys
   import psutil
   
   print(f"OS : {platform.system()} {platform.release()}")
   print(f"Python : {sys.version}")
   print(f"RAM : {psutil.virtual_memory().total / (1024**3):.1f} GB")
   print(f"CPU : {psutil.cpu_count()} cores")
   ```

### Procédure d'Escalade

1. **Niveau 1** : Diagnostic automatique et réparation
2. **Niveau 2** : Réinitialisation partielle
3. **Niveau 3** : Réinitialisation complète
4. **Niveau 4** : Support technique avec logs

### Collecte d'Informations pour Support

```python
async def collect_support_info():
    """Collecter les informations pour le support"""
    
    import json
    import platform
    import sys
    from datetime import datetime
    
    support_info = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "os": platform.system(),
            "version": platform.release(),
            "python": sys.version,
            "architecture": platform.architecture()[0]
        },
        "hardware": {
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "disk_gb": psutil.disk_usage('.').total / (1024**3)
        }
    }
    
    # Ajouter les configurations
    try:
        from ai_video_dubbing.performance.auto_optimizer import get_auto_optimizer
        optimizer = get_auto_optimizer()
        support_info["optimizer_config"] = optimizer.config
        support_info["optimizer_stats"] = optimizer.get_optimization_stats()
    except Exception as e:
        support_info["optimizer_error"] = str(e)
    
    # Sauvegarder
    support_file = f".kiro/support_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(support_file, 'w') as f:
        json.dump(support_info, f, indent=2)
    
    print(f"📋 Informations support sauvegardées : {support_file}")
    return support_file

# asyncio.run(collect_support_info())
```

---

*Guide de dépannage mis à jour le 26 août 2025 - Version 1.0*