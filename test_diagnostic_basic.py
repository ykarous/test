"""
Test basique du moteur de diagnostic
"""
import asyncio
import tempfile
import shutil
import psutil
import time

# Test des fonctions de base sans import du module complet
def test_system_info():
    """Test de collecte d'informations système"""
    print("🖥️ Test de collecte d'informations système")
    print("-" * 40)
    
    try:
        # Informations système de base
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        print(f"✅ Informations système collectées:")
        print(f"   CPU: {cpu_percent:.1f}%")
        print(f"   Mémoire: {memory.percent:.1f}% ({memory.available / (1024**3):.1f} GB disponible)")
        print(f"   Disque: {(disk.used / disk.total) * 100:.1f}% ({disk.free / (1024**3):.1f} GB libre)")
        
        # Test de performance simple
        start_time = time.time()
        result = sum(i * i for i in range(100000))
        cpu_test_time = time.time() - start_time
        
        print(f"   Test CPU: {cpu_test_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_gpu_detection():
    """Test de détection GPU"""
    print("\\n🎮 Test de détection GPU")
    print("-" * 25)
    
    try:
        # Test PyTorch CUDA
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            print(f"✅ PyTorch CUDA: {'Disponible' if cuda_available else 'Non disponible'}")
            
            if cuda_available:
                print(f"   Appareils CUDA: {torch.cuda.device_count()}")
                print(f"   Appareil actuel: {torch.cuda.get_device_name()}")
                
                # Test simple
                test_tensor = torch.randn(10, 10).cuda()
                result = torch.matmul(test_tensor, test_tensor)
                del test_tensor, result
                torch.cuda.empty_cache()
                print("   ✅ Test CUDA réussi")
            
        except ImportError:
            print("⚠️ PyTorch non installé")
        except Exception as e:
            print(f"❌ Erreur CUDA: {e}")
        
        # Test nvidia-smi
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split('\\n')[0].split(', ')
                print(f"✅ nvidia-smi: {gpu_info[0]}")
                print(f"   Mémoire: {gpu_info[2]}/{gpu_info[1]} MB")
            else:
                print("⚠️ nvidia-smi non disponible")
        except:
            print("⚠️ nvidia-smi non trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_network_connectivity():
    """Test de connectivité réseau"""
    print("\\n🌐 Test de connectivité réseau")
    print("-" * 30)
    
    try:
        import socket
        import urllib.request
        
        # Test DNS
        try:
            socket.gethostbyname('google.com')
            print("✅ Résolution DNS: OK")
        except:
            print("❌ Résolution DNS: Échec")
        
        # Test HTTP
        try:
            start_time = time.time()
            response = urllib.request.urlopen('http://httpbin.org/get', timeout=10)
            response_time = time.time() - start_time
            print(f"✅ Connectivité HTTP: OK ({response_time:.2f}s)")
        except Exception as e:
            print(f"❌ Connectivité HTTP: Échec ({e})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_storage_performance():
    """Test de performance de stockage"""
    print("\\n💾 Test de performance de stockage")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test d'écriture/lecture
        test_file = f"{temp_dir}/perf_test.tmp"
        test_data = "x" * 1000000  # 1MB
        
        # Écriture
        start_time = time.time()
        with open(test_file, 'w') as f:
            f.write(test_data)
        write_time = time.time() - start_time
        
        # Lecture
        start_time = time.time()
        with open(test_file, 'r') as f:
            content = f.read()
        read_time = time.time() - start_time
        
        print(f"✅ Performance disque:")
        print(f"   Écriture 1MB: {write_time:.3f}s")
        print(f"   Lecture 1MB: {read_time:.3f}s")
        
        if write_time > 1.0 or read_time > 1.0:
            print("⚠️ Performance disque lente détectée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_python_environment():
    """Test de l'environnement Python"""
    print("\\n🐍 Test de l'environnement Python")
    print("-" * 32)
    
    try:
        import sys
        import pkg_resources
        
        print(f"✅ Version Python: {sys.version.split()[0]}")
        print(f"   Exécutable: {sys.executable}")
        
        # Vérifier l'environnement virtuel
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        print(f"   Environnement virtuel: {'Oui' if in_venv else 'Non'}")
        
        # Vérifier quelques packages critiques
        critical_packages = ["torch", "numpy", "psutil"]
        
        print("   Packages critiques:")
        for package in critical_packages:
            try:
                version = pkg_resources.get_distribution(package).version
                print(f"     ✅ {package}: {version}")
            except pkg_resources.DistributionNotFound:
                print(f"     ❌ {package}: Non installé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def generate_health_score(test_results):
    """Génère un score de santé basé sur les résultats des tests"""
    print("\\n📊 Score de santé global")
    print("-" * 25)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    health_score = (passed_tests / total_tests) * 100
    
    if health_score >= 90:
        status = "✅ Excellent"
    elif health_score >= 70:
        status = "⚠️ Bon"
    elif health_score >= 50:
        status = "⚠️ Moyen"
    else:
        status = "❌ Critique"
    
    print(f"Score global: {health_score:.1f}% ({status})")
    print(f"Tests réussis: {passed_tests}/{total_tests}")
    
    return health_score

if __name__ == "__main__":
    print("🔍 Diagnostic basique du système")
    print("=" * 40)
    
    # Exécuter tous les tests
    test_results = {
        "system_info": test_system_info(),
        "gpu_detection": test_gpu_detection(),
        "network": test_network_connectivity(),
        "storage": test_storage_performance(),
        "python_env": test_python_environment()
    }
    
    # Générer le score de santé
    health_score = generate_health_score(test_results)
    
    # Recommandations basées sur les résultats
    print("\\n💡 Recommandations:")
    if not test_results["gpu_detection"]:
        print("   - Installer PyTorch avec support CUDA pour de meilleures performances")
    if not test_results["network"]:
        print("   - Vérifier la connexion internet pour le téléchargement de modèles")
    if health_score < 70:
        print("   - Plusieurs composants nécessitent une attention")
        print("   - Considérer un redémarrage du système")
    
    print("\\n✅ Diagnostic basique terminé")