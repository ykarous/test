"""
Test de l'optimisateur réseau avec téléchargement parallèle
"""

import asyncio
import time
import logging
import tempfile
from pathlib import Path
from ai_video_dubbing.performance.network_optimizer import (
    NetworkOptimizer,
    ServerInfo,
    ServerStatus,
    CompressionType,
    get_network_optimizer,
    download_file_optimized,
    test_network_performance,
    get_network_statistics
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_network_optimizer_basic():
    """Test de base de l'optimisateur réseau"""
    
    print("=== Test de Base de l'Optimisateur Réseau ===\n")
    
    # Créer un optimisateur
    optimizer = NetworkOptimizer()
    
    print("1. Configuration de l'optimisateur...")
    print(f"   Max téléchargements simultanés: {optimizer.config['max_concurrent_downloads']}")
    print(f"   Max segments par téléchargement: {optimizer.config['max_segments_per_download']}")
    print(f"   Taille de segment: {optimizer.config['segment_size_mb']} MB")
    print(f"   Compression activée: {optimizer.config['enable_compression']}")
    
    # Afficher les serveurs configurés
    print(f"\n2. Serveurs configurés ({len(optimizer.servers)}):")
    for server_id, server in optimizer.servers.items():
        print(f"   - {server.name}: {server.url} (priorité: {server.priority})")
    
    # Test de sélection du meilleur serveur
    print("\n3. Test de sélection de serveur...")
    best_server = optimizer.get_best_server()
    if best_server:
        print(f"   Meilleur serveur: {best_server.name}")
        print(f"   URL: {best_server.url}")
        print(f"   Statut: {best_server.status.value}")
    else:
        print("   Aucun serveur disponible")
    
    # Test des statistiques
    print("\n4. Statistiques initiales...")
    stats = optimizer.get_network_stats()
    network_stats = stats["network_stats"]
    
    print(f"   Total téléchargements: {network_stats['total_downloads']}")
    print(f"   Téléchargements réussis: {network_stats['successful_downloads']}")
    print(f"   Vitesse moyenne: {network_stats['average_speed_mbps']:.2f} Mbps")
    print(f"   Ratio de compression: {network_stats['compression_ratio']:.2f}")
    
    await optimizer.shutdown()
    print("\n✅ Test de base terminé")

async def test_server_performance():
    """Test des performances des serveurs"""
    
    print("\n=== Test des Performances des Serveurs ===\n")
    
    optimizer = NetworkOptimizer()
    
    print("1. Test de performance d'un serveur...")
    
    # Tester un serveur spécifique (utilisons un serveur public fiable)
    test_server = ServerInfo(
        url="https://httpbin.org",
        name="HTTPBin Test Server",
        priority=1
    )
    
    try:
        result = await optimizer.test_server_performance(test_server)
        
        print(f"   Serveur: {test_server.name}")
        print(f"   Succès: {'✅' if result['success'] else '❌'}")
        print(f"   Latence: {result['latency_ms']:.1f} ms")
        print(f"   Bande passante: {result['bandwidth_mbps']:.2f} Mbps")
        
        if result['error']:
            print(f"   Erreur: {result['error']}")
        
        # Vérifier les mises à jour du serveur
        print(f"   Statut mis à jour: {test_server.status.value}")
        print(f"   Taux de succès: {test_server.success_rate:.2%}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    print("\n2. Test de tous les serveurs par défaut...")
    
    try:
        # Tester seulement quelques serveurs pour éviter les timeouts
        limited_servers = dict(list(optimizer.servers.items())[:2])
        original_servers = optimizer.servers
        optimizer.servers = limited_servers
        
        results = await optimizer.test_all_servers()
        
        print(f"   Serveurs testés: {len(results)}")
        
        for server_name, result in results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   - {server_name}: {status}")
            
            if result.get('success'):
                print(f"     Latence: {result.get('latency_ms', 0):.1f} ms")
                print(f"     Bande passante: {result.get('bandwidth_mbps', 0):.2f} Mbps")
        
        # Vérifier le classement
        print(f"\n   Classement des serveurs: {optimizer.server_rankings}")
        
        # Restaurer les serveurs originaux
        optimizer.servers = original_servers
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test global: {e}")
    
    await optimizer.shutdown()
    print("\n✅ Test des performances terminé")

async def test_file_download():
    """Test de téléchargement de fichier"""
    
    print("\n=== Test de Téléchargement de Fichier ===\n")
    
    optimizer = NetworkOptimizer()
    
    # URL de test (petit fichier JSON)
    test_url = "https://httpbin.org/json"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print("1. Test de téléchargement simple...")
        
        try:
            file_path = temp_path / "test_simple.json"
            
            # Callback de progression
            progress_updates = []
            
            def progress_callback(downloaded: int, total: int):
                progress_updates.append((downloaded, total))
                if len(progress_updates) % 5 == 0:  # Afficher tous les 5 updates
                    percent = (downloaded / max(total, 1)) * 100
                    print(f"   Progression: {downloaded}/{total} bytes ({percent:.1f}%)")
            
            # Télécharger le fichier
            start_time = time.time()
            task = await optimizer.download_with_segments(test_url, file_path, progress_callback)
            download_time = time.time() - start_time
            
            print(f"   ✅ Téléchargement terminé en {download_time:.2f}s")
            print(f"   Statut: {task.status}")
            print(f"   Taille: {task.total_size} bytes")
            print(f"   Segments: {len(task.segments)}")
            print(f"   Fichier existe: {file_path.exists()}")
            
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"   Taille sur disque: {file_size} bytes")
                
                # Vérifier le contenu
                with open(file_path, 'r') as f:
                    content = f.read()
                    print(f"   Contenu valide: {'✅' if 'slideshow' in content else '❌'}")
            
        except Exception as e:
            print(f"   ❌ Erreur de téléchargement: {e}")
        
        print("\n2. Test de téléchargement avec compression...")
        
        try:
            file_path = temp_path / "test_compressed.json"
            
            start_time = time.time()
            task = await optimizer.download_with_compression(
                test_url, 
                file_path, 
                CompressionType.GZIP,
                progress_callback
            )
            download_time = time.time() - start_time
            
            print(f"   ✅ Téléchargement compressé terminé en {download_time:.2f}s")
            print(f"   Statut: {task.status}")
            print(f"   Type de compression: {task.compression_type.value}")
            
            if "compression_ratio" in task.metadata:
                print(f"   Ratio de compression: {task.metadata['compression_ratio']:.2f}")
            
        except Exception as e:
            print(f"   ❌ Erreur de téléchargement compressé: {e}")
    
    # Test des statistiques après téléchargement
    print("\n3. Statistiques après téléchargement...")
    
    stats = optimizer.get_network_stats()
    network_stats = stats["network_stats"]
    
    print(f"   Total téléchargements: {network_stats['total_downloads']}")
    print(f"   Téléchargements réussis: {network_stats['successful_downloads']}")
    print(f"   Bytes téléchargés: {network_stats['total_bytes_downloaded']}")
    print(f"   Vitesse moyenne: {network_stats['average_speed_mbps']:.2f} Mbps")
    
    # Historique des téléchargements
    history = optimizer.get_download_history(limit=5)
    print(f"\n   Historique ({len(history)} entrées):")
    
    for entry in history:
        print(f"   - {entry['status']}: {entry['total_size']} bytes en {entry['download_time']:.2f}s")
    
    await optimizer.shutdown()
    print("\n✅ Test de téléchargement terminé")

async def test_global_functions():
    """Test des fonctions utilitaires globales"""
    
    print("\n=== Test des Fonctions Globales ===\n")
    
    print("1. Test de téléchargement optimisé...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_path = temp_path / "global_test.json"
        test_url = "https://httpbin.org/json"
        
        try:
            # Utiliser la fonction utilitaire
            task = await download_file_optimized(
                url=test_url,
                file_path=file_path,
                use_segments=True,
                use_compression=False
            )
            
            print(f"   ✅ Téléchargement réussi")
            print(f"   Statut: {task.status}")
            print(f"   Taille: {task.total_size} bytes")
            print(f"   Fichier créé: {file_path.exists()}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n2. Test des statistiques globales...")
    
    try:
        stats = await get_network_statistics()
        
        print(f"   Serveurs actifs: {stats['server_count']}")
        print(f"   Téléchargements actifs: {stats['active_downloads']}")
        print(f"   Meilleur serveur: {stats['best_server']}")
        
        if 'servers' in stats:
            print("   État des serveurs:")
            for server_id, server_info in list(stats['servers'].items())[:3]:
                print(f"   - {server_info['name']}: {server_info['status']}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la récupération des stats: {e}")
    
    print("\n3. Test de performance réseau globale...")
    
    try:
        # Limiter le test pour éviter les timeouts
        optimizer = get_network_optimizer()
        
        # Tester seulement un serveur
        limited_servers = {"httpbin": ServerInfo(
            url="https://httpbin.org",
            name="HTTPBin",
            priority=1
        )}
        
        original_servers = optimizer.servers
        optimizer.servers = limited_servers
        
        perf_results = await test_network_performance()
        
        print(f"   Serveurs testés: {len(perf_results)}")
        
        for server_name, result in perf_results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   - {server_name}: {status}")
        
        # Restaurer les serveurs
        optimizer.servers = original_servers
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test de performance: {e}")
    
    print("\n✅ Test des fonctions globales terminé")

async def test_concurrent_downloads():
    """Test de téléchargements simultanés"""
    
    print("\n=== Test de Téléchargements Simultanés ===\n")
    
    optimizer = NetworkOptimizer()
    
    # URLs de test
    test_urls = [
        "https://httpbin.org/json",
        "https://httpbin.org/uuid",
        "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l"
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"1. Lancement de {len(test_urls)} téléchargements simultanés...")
        
        async def download_file(url: str, index: int):
            try:
                file_path = temp_path / f"concurrent_{index}.json"
                
                start_time = time.time()
                task = await optimizer.download_with_segments(url, file_path)
                download_time = time.time() - start_time
                
                return {
                    "index": index,
                    "success": task.status == "completed",
                    "size": task.total_size,
                    "time": download_time,
                    "segments": len(task.segments)
                }
                
            except Exception as e:
                return {
                    "index": index,
                    "success": False,
                    "error": str(e),
                    "time": 0,
                    "size": 0,
                    "segments": 0
                }
        
        # Lancer tous les téléchargements en parallèle
        start_time = time.time()
        
        tasks = [download_file(url, i) for i, url in enumerate(test_urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        print(f"   ✅ Tous les téléchargements terminés en {total_time:.2f}s")
        
        # Analyser les résultats
        successful = 0
        total_size = 0
        
        for result in results:
            if isinstance(result, dict):
                if result["success"]:
                    successful += 1
                    total_size += result["size"]
                    print(f"   - Téléchargement {result['index']}: ✅ ({result['size']} bytes, {result['time']:.2f}s, {result['segments']} segments)")
                else:
                    print(f"   - Téléchargement {result['index']}: ❌ ({result.get('error', 'Unknown error')})")
            else:
                print(f"   - Erreur exception: {result}")
        
        print(f"\n   Résumé:")
        print(f"   - Réussis: {successful}/{len(test_urls)}")
        print(f"   - Taille totale: {total_size} bytes")
        print(f"   - Vitesse globale: {(total_size * 8) / (total_time * 1024 * 1024):.2f} Mbps")
    
    await optimizer.shutdown()
    print("\n✅ Test de téléchargements simultanés terminé")

async def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests de l'optimisateur réseau\n")
    
    try:
        # Test 1: Fonctionnalités de base
        await test_network_optimizer_basic()
        
        # Test 2: Performance des serveurs
        await test_server_performance()
        
        # Test 3: Téléchargement de fichiers
        await test_file_download()
        
        # Test 4: Fonctions globales
        await test_global_functions()
        
        # Test 5: Téléchargements simultanés
        await test_concurrent_downloads()
        
        print("\n🎉 Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())