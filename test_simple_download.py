"""
Test simple du téléchargement pour diagnostiquer les problèmes
"""
import asyncio
import aiohttp
import aiofiles
import tempfile
import os

async def test_basic_download():
    """Test de téléchargement basique avec aiohttp"""
    print("Test de téléchargement basique...")
    
    url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Téléchargement depuis: {url}")
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.read()
                    print(f"Contenu reçu: {len(content)} bytes")
                    
                    # Écrire dans le fichier
                    with open(temp_path, 'wb') as f:
                        f.write(content)
                    
                    # Vérifier le fichier
                    file_size = os.path.getsize(temp_path)
                    print(f"Fichier écrit: {file_size} bytes")
                    
                    if file_size > 0:
                        print("✅ Téléchargement basique réussi")
                    else:
                        print("❌ Fichier vide")
                else:
                    print(f"❌ Erreur HTTP: {response.status}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def test_chunked_download():
    """Test de téléchargement par chunks"""
    print("\nTest de téléchargement par chunks...")
    
    url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    total_size = 0
                    async with aiofiles.open(temp_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(512):
                            await file.write(chunk)
                            total_size += len(chunk)
                            print(f"Chunk écrit: {len(chunk)} bytes (total: {total_size})")
                    
                    file_size = os.path.getsize(temp_path)
                    print(f"Fichier final: {file_size} bytes")
                    
                    if file_size > 0:
                        print("✅ Téléchargement par chunks réussi")
                    else:
                        print("❌ Fichier vide")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    asyncio.run(test_basic_download())
    asyncio.run(test_chunked_download())