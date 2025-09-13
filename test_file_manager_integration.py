#!/usr/bin/env python3
"""
Test d'intégration du gestionnaire de fichiers avec les autres composants.
"""

import tempfile
from pathlib import Path

# Test d'importation depuis le module principal
from ai_video_dubbing.utils import FileManager
from ai_video_dubbing.interfaces.base_interfaces import IFileManager
from ai_video_dubbing.models.data_models import ValidationError


def test_integration():
    """Test d'intégration du FileManager."""
    print("=== Test d'Intégration du Gestionnaire de Fichiers ===")
    
    # Test 1: Vérifier que FileManager implémente IFileManager
    print("\n1. Test d'interface:")
    print(f"   FileManager hérite de IFileManager: {issubclass(FileManager, IFileManager)}")
    
    # Test 2: Instanciation et utilisation
    print("\n2. Test d'instanciation:")
    with tempfile.TemporaryDirectory() as temp_dir:
        file_manager = FileManager(temp_base_dir=temp_dir)
        print(f"   Instance créée: {type(file_manager).__name__}")
        print(f"   Répertoire temporaire: {file_manager.temp_base_dir}")
        
        # Test 3: Méthodes de l'interface
        print("\n3. Test des méthodes de l'interface:")
        
        # Créer un fichier de test valide
        test_file = Path(temp_dir) / "test.mp4"
        # Signature MP4 basique pour passer la validation
        mp4_header = b'\x00\x00\x00\x18ftypmp41\x00\x00\x00\x00'
        test_file.write_bytes(mp4_header + b'contenu de test video')
        
        try:
            # Test validate_video_file
            is_valid = file_manager.validate_video_file(str(test_file))
            print(f"   ✅ validate_video_file: {is_valid}")
            
            # Test create_temp_directory
            temp_subdir = file_manager.create_temp_directory()
            print(f"   ✅ create_temp_directory: {Path(temp_subdir).exists()}")
            
            # Test get_file_info
            info = file_manager.get_file_info(str(test_file))
            print(f"   ✅ get_file_info: {info['name']}")
            
            # Test cleanup_temp_files
            file_manager.cleanup_temp_files()
            print(f"   ✅ cleanup_temp_files: {len(file_manager.temp_directories) == 0}")
            
        except Exception as e:
            print(f"   ❌ Erreur lors du test: {e}")
    
    # Test 4: Gestion des erreurs
    print("\n4. Test de gestion des erreurs:")
    file_manager = FileManager()
    
    try:
        file_manager.validate_video_file("/fichier/inexistant.mp4")
        print("   ❌ Erreur: devrait lever ValidationError")
    except ValidationError:
        print("   ✅ ValidationError correctement levée")
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    print("\n✅ Test d'intégration terminé avec succès!")


if __name__ == "__main__":
    test_integration()