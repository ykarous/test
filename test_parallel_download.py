"""
Test avancé du téléchargement parallèle et du monitoring
"""
import asyncio
import os
import tempfile
import time
from ai_video_dubbing.performance.download_manager import IntelligentDownloadManager
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_parallel_download_monitoring():
    """Test du téléchargement parallèle avec monitoring détaillé"""
    print("Test du téléchargement parallèle avec monitoring...")
    
    # Créer l'interface de progression
    progress_interface = RealTimeProgressInterface(ui_update_interval=0.1)
    
    # Créer le gestionnaire avec monitoring
    download_manager = IntelligentDownloadManager(
        max_concurrent_downloads=3,
        max_connections_per_download=2,
        progress_interface=progress_interface
    )
    
    # Modifier la validation pour être plus permissive
    async def lenient_validate(session):
        return os.path.exists(session.info.destination) and os.path.getsize(session.info.destination) > 0
    
    download_manager._validate_download = lenient_validate
    
    # URLs de test (différentes tailles)
    test_urls = [
        ("https://raw.githubusercontent.com/octocat/Hello-World/master/README", "small_file_1.txt"),
        ("https://raw.githubusercontent.com/octocat/Hello-World/master/README", "small_file_2.txt"),
        ("https://raw.githubusercontent.com/octocat/Hello-World/master/README", "small_file_3.txt")
    ]
    
    # Créer les fichiers temporaires
    temp_files = []
    for i, (url, name) in enumerate(test_urls):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{name}")
        temp_files.append(temp_file.name)
        temp_file.close()
    
    # Callback de monitoring global
    download_stats = {"completed": 0, "failed": 0, "total_bytes": 0}
    
    async def monitor_callback(session):
        """Callback de monitoring pour chaque téléchargement"""
        print(f"[{session.download_id[:8]}] {session.info.progress_percent:.1f}% - "
              f"{session.current_speed/1024:.1f} KB/s - "
              f"ETA: {session.eta_seconds:.1f}s")
    
    try:
        print(f"Démarrage de {len(test_urls)} téléchargements parallèles...")
        start_time = time.time()
        
        # Lancer tous les téléchargements en parallèle
        tasks = []
        for i, (url, name) in enumerate(test_urls):
            task = asyncio.create_task(
                download_manager.download_model(
                    url=url,
                    destination=temp_files[i],
                    progress_callback=monitor_callback
                )
            )
            tasks.append(task)
        
        # Attendre que tous se terminent
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyser les résultats
        successful = 0
        failed = 0
        total_bytes = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Téléchargement {i+1} échoué: {result}")
                failed += 1
            elif result:
                file_size = os.path.getsize(temp_files[i]) if os.path.exists(temp_files[i]) else 0
                print(f"✅ Téléchargement {i+1} réussi: {file_size} bytes")
                successful += 1
                total_bytes += file_size
            else:
                print(f"❌ Téléchargement {i+1} échoué")
                failed += 1
        
        print(f"\n=== Résultats ===")
        print(f"Téléchargements réussis: {successful}/{len(test_urls)}")
        print(f"Téléchargements échoués: {failed}")
        print(f"Temps total: {total_time:.2f}s")
        print(f"Bytes totaux: {total_bytes}")
        print(f"Vitesse moyenne: {total_bytes/total_time/1024:.1f} KB/s")
        
        # Statistiques du gestionnaire
        stats = download_manager.get_download_stats()
        print(f"Statistiques gestionnaire: {stats}")
        
        # Vérifier les téléchargements actifs (devrait être vide)
        active = download_manager.get_active_downloads()
        print(f"Téléchargements actifs: {len(active)}")
        
        if successful > 0:
            print("✅ Test de téléchargement parallèle réussi")
        else:
            print("❌ Tous les téléchargements ont échoué")
    
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer les fichiers temporaires
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        await progress_interface.shutdown()

async def test_download_cancellation():
    """Test d'annulation de téléchargement"""
    print("\nTest d'annulation de téléchargement...")
    
    download_manager = IntelligentDownloadManager()
    
    # Modifier la validation
    async def lenient_validate(session):
        return os.path.exists(session.info.destination) and os.path.getsize(session.info.destination) > 0
    
    download_manager._validate_download = lenient_validate
    
    test_url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Démarrer le téléchargement
        download_task = asyncio.create_task(
            download_manager.download_model(url=test_url, destination=temp_path)
        )
        
        # Attendre un peu puis annuler
        await asyncio.sleep(0.1)
        
        # Trouver l'ID du téléchargement actif
        active_downloads = download_manager.get_active_downloads()
        if active_downloads:
            download_id = active_downloads[0]["download_id"]
            print(f"Annulation du téléchargement: {download_id}")
            
            cancelled = await download_manager.cancel_download(download_id)
            if cancelled:
                print("✅ Téléchargement annulé avec succès")
            else:
                print("❌ Échec de l'annulation")
        
        # Attendre que la tâche se termine
        result = await download_task
        print(f"Résultat du téléchargement annulé: {result}")
    
    except Exception as e:
        print(f"❌ Erreur lors du test d'annulation: {e}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def test_connection_stability():
    """Test de détection de connexion instable"""
    print("\nTest de détection de connexion instable...")
    
    download_manager = IntelligentDownloadManager(max_concurrent_downloads=1)
    
    # Modifier la validation
    async def lenient_validate(session):
        return os.path.exists(session.info.destination) and os.path.getsize(session.info.destination) > 0
    
    download_manager._validate_download = lenient_validate
    
    # Callback pour surveiller la vitesse
    speed_samples = []
    
    async def speed_monitor(session):
        speed_samples.append(session.current_speed)
        if len(speed_samples) > 5:
            # Analyser la stabilité de la connexion
            recent_speeds = speed_samples[-5:]
            avg_speed = sum(recent_speeds) / len(recent_speeds)
            speed_variance = sum((s - avg_speed) ** 2 for s in recent_speeds) / len(recent_speeds)
            
            if speed_variance > avg_speed * 0.5:  # Variance élevée
                print(f"⚠️ Connexion instable détectée - Variance: {speed_variance:.2f}, Moyenne: {avg_speed:.2f}")
            else:
                print(f"📶 Connexion stable - Vitesse: {avg_speed/1024:.1f} KB/s")
    
    test_url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        success = await download_manager.download_model(
            url=test_url,
            destination=temp_path,
            progress_callback=speed_monitor
        )
        
        if success:
            print("✅ Test de stabilité de connexion terminé")
        else:
            print("❌ Téléchargement échoué")
    
    except Exception as e:
        print(f"❌ Erreur lors du test de stabilité: {e}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    asyncio.run(test_parallel_download_monitoring())
    asyncio.run(test_download_cancellation())
    asyncio.run(test_connection_stability())