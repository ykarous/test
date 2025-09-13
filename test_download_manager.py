"""
Test du gestionnaire de téléchargement intelligent
"""
import asyncio
import os
import tempfile
import hashlib
from ai_video_dubbing.performance.download_manager import IntelligentDownloadManager
from ai_video_dubbing.performance.progress_interface import RealTimeProgressInterface

async def test_download_manager():
    """Test basique du gestionnaire de téléchargement"""
    print("Test du gestionnaire de téléchargement intelligent...")
    
    # Créer l'interface de progression
    progress_interface = RealTimeProgressInterface()
    
    # Créer le gestionnaire de téléchargement
    download_manager = IntelligentDownloadManager(
        max_concurrent_downloads=2,
        max_connections_per_download=2,
        progress_interface=progress_interface
    )
    
    # Callback de progression personnalisé
    async def progress_callback(session):
        print(f"Progression: {session.info.progress_percent:.1f}% - "
              f"Vitesse: {session.current_speed/1024:.1f} KB/s - "
              f"ETA: {session.eta_seconds:.1f}s")
    
    # Test avec un petit fichier (exemple: un fichier texte)
    test_url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        print(f"Téléchargement de test depuis: {test_url}")
        print(f"Destination: {temp_path}")
        
        # Effectuer le téléchargement
        success = await download_manager.download_model(
            url=test_url,
            destination=temp_path,
            progress_callback=progress_callback
        )
        
        if success:
            print("✅ Téléchargement réussi")
            
            # Vérifier que le fichier existe
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"✅ Fichier créé - Taille: {file_size} bytes")
            else:
                print("❌ Fichier non trouvé")
        else:
            print("❌ Téléchargement échoué")
        
        # Afficher les statistiques
        stats = download_manager.get_download_stats()
        print(f"Statistiques: {stats}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        await progress_interface.shutdown()
    
    print("Test terminé")

async def test_resume_download():
    """Test de la reprise de téléchargement"""
    print("\nTest de la reprise de téléchargement...")
    
    download_manager = IntelligentDownloadManager()
    
    # Simuler un téléchargement interrompu
    test_url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        # Écrire quelques bytes pour simuler un téléchargement partiel
        temp_file.write(b"partial_data")
    
    try:
        print(f"Test de reprise avec fichier partiel: {temp_path}")
        
        # Le gestionnaire devrait détecter le fichier partiel et reprendre
        success = await download_manager.download_model(
            url=test_url,
            destination=temp_path
        )
        
        if success:
            print("✅ Reprise de téléchargement réussie")
        else:
            print("❌ Reprise de téléchargement échouée")
    
    except Exception as e:
        print(f"❌ Erreur lors du test de reprise: {e}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def test_hash_validation():
    """Test de la validation par hash"""
    print("\nTest de la validation par hash...")
    
    download_manager = IntelligentDownloadManager()
    
    # Créer un fichier de test avec un hash connu
    test_data = b"Hello, World!"
    expected_hash = hashlib.sha256(test_data).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(test_data)
    
    try:
        # Test avec hash correct (fichier déjà existant et valide)
        success = await download_manager.download_model(
            url="https://example.com/fake",  # URL fictive
            destination=temp_path,
            expected_hash=expected_hash
        )
        
        if success:
            print("✅ Validation par hash réussie (fichier existant)")
        else:
            print("❌ Validation par hash échouée")
    
    except Exception as e:
        print(f"❌ Erreur lors du test de hash: {e}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    asyncio.run(test_download_manager())
    asyncio.run(test_resume_download())
    asyncio.run(test_hash_validation())