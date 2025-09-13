#!/usr/bin/env python3
"""
Test simple du gestionnaire de fichiers.
"""

import tempfile
import os
from pathlib import Path

from ai_video_dubbing.utils.file_manager import FileManager
from ai_video_dubbing.models.data_models import ValidationError


def test_file_manager():
    """Test simple du FileManager."""
    print("=== Test du Gestionnaire de Fichiers ===")
    
    # Créer un répertoire temporaire pour les tests
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Répertoire temporaire: {temp_dir}")
        
        # Initialiser le gestionnaire
        file_manager = FileManager(temp_base_dir=temp_dir)
        
        # Test 1: Formats supportés
        print("\n1. Formats supportés:")
        print(f"   Formats vidéo: {file_manager.SUPPORTED_VIDEO_FORMATS}")
        print(f"   Formats audio: {file_manager.SUPPORTED_AUDIO_FORMATS}")
        
        # Test 2: Validation d'un fichier inexistant
        print("\n2. Test fichier inexistant:")
        try:
            file_manager.validate_video_file("/path/inexistant.mp4")
            print("   ❌ Erreur: devrait lever une exception")
        except ValidationError as e:
            print(f"   ✅ Exception attendue: {e}")
        
        # Test 3: Validation d'un format non supporté
        print("\n3. Test format non supporté:")
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("contenu test")
        
        try:
            file_manager.validate_video_file(str(test_file))
            print("   ❌ Erreur: devrait lever une exception")
        except ValidationError as e:
            print(f"   ✅ Exception attendue: {e}")
        
        # Test 4: Validation d'un fichier vide
        print("\n4. Test fichier vide:")
        empty_file = Path(temp_dir) / "empty.mp4"
        empty_file.touch()
        
        try:
            file_manager.validate_video_file(str(empty_file))
            print("   ❌ Erreur: devrait lever une exception")
        except ValidationError as e:
            print(f"   ✅ Exception attendue: {e}")
        
        # Test 5: Création de répertoire temporaire
        print("\n5. Test création répertoire temporaire:")
        temp_subdir = file_manager.create_temp_directory()
        print(f"   Répertoire créé: {temp_subdir}")
        print(f"   Existe: {os.path.exists(temp_subdir)}")
        
        # Test 6: Nom de fichier sécurisé
        print("\n6. Test nom de fichier sécurisé:")
        unsafe_name = 'test<>:"/\\|?*file.mp4'
        safe_name = file_manager.get_safe_filename(unsafe_name)
        print(f"   Nom non sûr: {unsafe_name}")
        print(f"   Nom sécurisé: {safe_name}")
        
        # Test 7: Copie de fichier
        print("\n7. Test copie de fichier:")
        source_file = Path(temp_dir) / "source.txt"
        source_file.write_text("contenu de test")
        
        dest_file = Path(temp_dir) / "subdir" / "dest.txt"
        file_manager.copy_file(str(source_file), str(dest_file))
        
        print(f"   Source: {source_file}")
        print(f"   Destination: {dest_file}")
        print(f"   Copie réussie: {dest_file.exists()}")
        print(f"   Contenu identique: {source_file.read_text() == dest_file.read_text()}")
        
        # Test 8: Informations de fichier
        print("\n8. Test informations de fichier:")
        info = file_manager.get_file_info(str(source_file))
        print(f"   Nom: {info['name']}")
        print(f"   Taille: {info['size']} octets ({info['size_mb']} MB)")
        print(f"   Extension: {info['extension']}")
        
        # Test 9: Validation basique de fichier vidéo
        print("\n9. Test validation basique MP4:")
        fake_mp4 = Path(temp_dir) / "fake.mp4"
        # Créer un fichier avec une signature MP4 basique
        mp4_header = b'\x00\x00\x00\x18ftypmp41\x00\x00\x00\x00'
        fake_mp4.write_bytes(mp4_header + b'contenu factice')
        
        is_valid = file_manager._basic_file_validation(str(fake_mp4))
        print(f"   Fichier MP4 factice valide: {is_valid}")
        
        # Test 10: Nettoyage
        print("\n10. Test nettoyage:")
        print(f"   Répertoires temporaires avant: {len(file_manager.temp_directories)}")
        file_manager.cleanup_temp_files()
        print(f"   Répertoires temporaires après: {len(file_manager.temp_directories)}")
        
        print("\n✅ Tous les tests du gestionnaire de fichiers sont terminés!")


if __name__ == "__main__":
    test_file_manager()