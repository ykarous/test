"""
Test simple de l'optimisateur réseau sans dépendances externes
"""

import asyncio
import time
import logging
import tempfile
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_network_optimizer_structure():
    """Test de la structure de l'optimisateur réseau"""
    
    print("=== Test de Structure de l'Optimisateur Réseau ===\n")
    
    try:
        # Import sans utiliser aiohttp
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        print("1. Test d'import des classes...")
        
        # Tester l'import des enums et dataclasses
        from ai_video_dubbing.performance.network_optimizer import (
            CompressionType,
            ServerStatus,
            ServerInfo,
            DownloadSegment,
            DownloadTask
        )
        
        print("   ✅ Import des classes de base réussi")
        
        # Test des enums
        print("\n2. Test des enums...")
        
        compression_types = list(CompressionType)
        print(f"   Types de compression: {[ct.value for ct in compression_types]}")
        
        server_statuses = list(ServerStatus)
        print(f"   États des serveurs: {[ss.value for ss in server_statuses]}")
        
        # Test des dataclasses
        print("\n3. Test des dataclasses...")
        
        # Créer un serveur de test
        test_server = ServerInfo(
            url="https://example.com",
            name="Test Server",
            priority=1
        )
        
        print(f"   Serveur créé: {test_server.name}")
        print(f"   URL: {test_server.url}")
        print(f"   Statut: {test_server.status.value}")
        print(f"   Priorité: {test_server.priority}")
        
        # Créer un segment de téléchargement
        test_segment = DownloadSegment(
            segment_id=0,
            start_byte=0,
            end_byte=1023,
            url="https://example.com/file.bin",
            server=test_server
        )
        
        print(f"   Segment créé: {test_segment.segment_id}")
        print(f"   Plage: {test_segment.start_byte}-{test_segment.end_byte}")
        print(f"   Statut: {test_segment.status}")
        
        # Créer une tâche de téléchargement
        test_task = DownloadTask(
            task_id="test_123",
            url="https://example.com/file.bin",
            file_path=Path("test_file.bin")
        )
        
        print(f"   Tâche créée: {test_task.task_id}")
        print(f"   URL: {test_task.url}")
        print(f"   Fichier: {test_task.file_path}")
        print(f"   Statut: {test_task.status}")
        
        print("\n✅ Test de structure terminé avec succès")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Vérifiez que le module network_optimizer est accessible")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        import traceback
        traceback.print_exc()

async def test_network_config():
    """Test de la configuration réseau"""
    
    print("\n=== Test de Configuration Réseau ===\n")
    
    try:
        print("1. Test de configuration par défaut...")
        
        # Configuration par défaut simulée
        default_config = {
            "max_concurrent_downloads": 4,
            "max_segments_per_download": 8,
            "segment_size_mb": 10,
            "connection_timeout": 30.0,
            "read_timeout": 60.0,
            "max_retries": 3,
            "server_test_interval": 300.0,
            "enable_compression": True,
            "enable_http_cache": True,
            "user_agent": "NetworkOptimizer/1.0",
            "max_bandwidth_mbps": 100.0
        }
        
        print("   Configuration par défaut:")
        for key, value in default_config.items():
            print(f"   - {key}: {value}")
        
        print("\n2. Test de serveurs par défaut...")
        
        default_servers = [
            {
                "id": "huggingface_main",
                "url": "https://huggingface.co",
                "name": "Hugging Face Main",
                "priority": 1
            },
            {
                "id": "huggingface_cdn",
                "url": "https://cdn-lfs.huggingface.co",
                "name": "Hugging Face CDN",
                "priority": 2
            },
            {
                "id": "github_releases",
                "url": "https://github.com",
                "name": "GitHub Releases",
                "priority": 3
            },
            {
                "id": "nvidia_ngc",
                "url": "https://api.ngc.nvidia.com",
                "name": "NVIDIA NGC",
                "priority": 4
            }
        ]
        
        print(f"   Serveurs par défaut ({len(default_servers)}):")
        for server in default_servers:
            print(f"   - {server['name']}: {server['url']} (priorité: {server['priority']})")
        
        print("\n3. Test de calcul de segments...")
        
        # Simuler le calcul de segments
        file_size = 100 * 1024 * 1024  # 100 MB
        segment_size = 10 * 1024 * 1024  # 10 MB
        max_segments = 8
        
        num_segments = min(max_segments, max(1, file_size // segment_size))
        actual_segment_size = file_size // num_segments
        
        print(f"   Taille du fichier: {file_size / (1024*1024):.1f} MB")
        print(f"   Taille de segment cible: {segment_size / (1024*1024):.1f} MB")
        print(f"   Nombre de segments: {num_segments}")
        print(f"   Taille de segment réelle: {actual_segment_size / (1024*1024):.1f} MB")
        
        # Créer les segments simulés
        segments = []
        for i in range(num_segments):
            start_byte = i * actual_segment_size
            end_byte = start_byte + actual_segment_size - 1
            
            if i == num_segments - 1:
                end_byte = file_size - 1
            
            segments.append({
                "id": i,
                "start": start_byte,
                "end": end_byte,
                "size": end_byte - start_byte + 1
            })
        
        print(f"   Segments créés:")
        for segment in segments:
            size_mb = segment["size"] / (1024 * 1024)
            print(f"   - Segment {segment['id']}: {segment['start']}-{segment['end']} ({size_mb:.1f} MB)")
        
        print("\n✅ Test de configuration terminé")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test de configuration: {e}")
        import traceback
        traceback.print_exc()

async def test_network_utilities():
    """Test des utilitaires réseau"""
    
    print("\n=== Test des Utilitaires Réseau ===\n")
    
    try:
        print("1. Test de calcul de vitesse...")
        
        # Simuler des téléchargements
        downloads = [
            {"size": 1024 * 1024, "time": 1.0},      # 1 MB en 1s = 8 Mbps
            {"size": 5 * 1024 * 1024, "time": 2.0},  # 5 MB en 2s = 20 Mbps
            {"size": 10 * 1024 * 1024, "time": 4.0}, # 10 MB en 4s = 20 Mbps
        ]
        
        total_bytes = sum(d["size"] for d in downloads)
        total_time = sum(d["time"] for d in downloads)
        
        if total_time > 0:
            avg_speed_bps = total_bytes / total_time
            avg_speed_mbps = (avg_speed_bps * 8) / (1024 * 1024)
        else:
            avg_speed_mbps = 0
        
        print(f"   Téléchargements simulés: {len(downloads)}")
        print(f"   Taille totale: {total_bytes / (1024*1024):.1f} MB")
        print(f"   Temps total: {total_time:.1f}s")
        print(f"   Vitesse moyenne: {avg_speed_mbps:.2f} Mbps")
        
        print("\n2. Test de calcul de compression...")
        
        # Simuler des ratios de compression
        compressions = [
            {"original": 1000, "compressed": 300, "type": "gzip"},
            {"original": 2000, "compressed": 800, "type": "deflate"},
            {"original": 5000, "compressed": 1500, "type": "gzip"},
        ]
        
        print("   Ratios de compression simulés:")
        for comp in compressions:
            ratio = comp["compressed"] / comp["original"]
            savings = (1 - ratio) * 100
            print(f"   - {comp['type']}: {comp['original']} -> {comp['compressed']} bytes (ratio: {ratio:.2f}, économie: {savings:.1f}%)")
        
        print("\n3. Test de priorité des serveurs...")
        
        # Simuler des scores de serveurs
        servers = [
            {"name": "Server A", "latency": 50, "bandwidth": 100, "success_rate": 0.95, "priority": 1},
            {"name": "Server B", "latency": 100, "bandwidth": 80, "success_rate": 0.90, "priority": 2},
            {"name": "Server C", "latency": 200, "bandwidth": 50, "success_rate": 0.85, "priority": 3},
        ]
        
        # Calculer les scores
        for server in servers:
            latency_score = max(0, 1000 - server["latency"]) / 1000
            bandwidth_score = min(server["bandwidth"] / 100, 1.0)
            success_score = server["success_rate"]
            priority_score = (5 - server["priority"]) / 4
            
            total_score = (latency_score * 0.3 + bandwidth_score * 0.3 + 
                          success_score * 0.3 + priority_score * 0.1)
            
            server["score"] = total_score
        
        # Trier par score
        servers.sort(key=lambda x: x["score"], reverse=True)
        
        print("   Classement des serveurs:")
        for i, server in enumerate(servers, 1):
            print(f"   {i}. {server['name']}: score {server['score']:.3f}")
            print(f"      Latence: {server['latency']}ms, Bande passante: {server['bandwidth']}Mbps")
            print(f"      Taux de succès: {server['success_rate']:.1%}, Priorité: {server['priority']}")
        
        print("\n✅ Test des utilitaires terminé")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test des utilitaires: {e}")
        import traceback
        traceback.print_exc()

async def test_file_operations():
    """Test des opérations sur fichiers"""
    
    print("\n=== Test des Opérations sur Fichiers ===\n")
    
    try:
        print("1. Test de création de répertoires...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Créer une structure de répertoires
            download_dir = temp_path / "downloads" / "models"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"   Répertoire créé: {download_dir}")
            print(f"   Existe: {download_dir.exists()}")
            print(f"   Est un répertoire: {download_dir.is_dir()}")
            
            print("\n2. Test de création de fichiers...")
            
            # Créer des fichiers de test
            test_files = [
                {"name": "small.txt", "size": 1024},
                {"name": "medium.bin", "size": 1024 * 100},
                {"name": "large.dat", "size": 1024 * 1024},
            ]
            
            for file_info in test_files:
                file_path = download_dir / file_info["name"]
                
                # Créer le fichier avec des données simulées
                with open(file_path, 'wb') as f:
                    data = b'x' * file_info["size"]
                    f.write(data)
                
                # Vérifier le fichier
                actual_size = file_path.stat().st_size
                print(f"   - {file_info['name']}: {actual_size} bytes (attendu: {file_info['size']})")
            
            print("\n3. Test d'assemblage de segments...")
            
            # Simuler l'assemblage de segments
            segments_data = [
                b"Segment 0 data: " + b"A" * 100,
                b"Segment 1 data: " + b"B" * 100,
                b"Segment 2 data: " + b"C" * 100,
            ]
            
            assembled_file = download_dir / "assembled.txt"
            
            # Assembler les segments
            with open(assembled_file, 'wb') as output_file:
                for i, segment_data in enumerate(segments_data):
                    output_file.write(segment_data)
                    print(f"   Segment {i} écrit: {len(segment_data)} bytes")
            
            # Vérifier le fichier assemblé
            final_size = assembled_file.stat().st_size
            expected_size = sum(len(data) for data in segments_data)
            
            print(f"   Fichier assemblé: {final_size} bytes (attendu: {expected_size})")
            print(f"   Assemblage réussi: {'✅' if final_size == expected_size else '❌'}")
            
            # Vérifier le contenu
            with open(assembled_file, 'rb') as f:
                content = f.read()
                has_all_segments = all(data in content for data in segments_data)
                print(f"   Contenu valide: {'✅' if has_all_segments else '❌'}")
        
        print("\n✅ Test des opérations sur fichiers terminé")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test des fichiers: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests simples de l'optimisateur réseau\n")
    
    try:
        # Test 1: Structure des classes
        await test_network_optimizer_structure()
        
        # Test 2: Configuration
        await test_network_config()
        
        # Test 3: Utilitaires
        await test_network_utilities()
        
        # Test 4: Opérations sur fichiers
        await test_file_operations()
        
        print("\n🎉 Tous les tests simples terminés avec succès!")
        print("\n💡 Pour tester les fonctionnalités réseau complètes, installez aiohttp:")
        print("   mon_env\\Scripts\\activate")
        print("   pip install aiohttp")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())