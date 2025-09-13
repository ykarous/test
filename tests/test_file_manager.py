"""
Tests pour le gestionnaire de fichiers.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_video_dubbing.utils.file_manager import FileManager
from ai_video_dubbing.models.data_models import ValidationError


class TestFileManager:
    """Tests pour FileManager."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(temp_base_dir=self.temp_dir)
    
    def teardown_method(self):
        """Nettoyage après chaque test."""
        self.file_manager.cleanup_temp_files()
    
    def test_supported_formats(self):
        """Test des formats supportés."""
        assert '.mp4' in FileManager.SUPPORTED_VIDEO_FORMATS
        assert '.mkv' in FileManager.SUPPORTED_VIDEO_FORMATS
        assert '.avi' in FileManager.SUPPORTED_VIDEO_FORMATS
    
    def test_validate_nonexistent_file(self):
        """Test de validation d'un fichier inexistant."""
        with pytest.raises(ValidationError, match="n'existe pas"):
            self.file_manager.validate_video_file("/path/to/nonexistent.mp4")
    
    def test_validate_unsupported_format(self):
        """Test de validation d'un format non supporté."""
        # Créer un fichier temporaire avec une extension non supportée
        temp_file = Path(self.temp_dir) / "test.txt"
        temp_file.write_text("test content")
        
        with pytest.raises(ValidationError, match="Format de fichier non supporté"):
            self.file_manager.validate_video_file(str(temp_file))
    
    def test_validate_empty_file(self):
        """Test de validation d'un fichier vide."""
        # Créer un fichier vide avec une extension supportée
        temp_file = Path(self.temp_dir) / "empty.mp4"
        temp_file.touch()
        
        with pytest.raises(ValidationError, match="est vide"):
            self.file_manager.validate_video_file(str(temp_file))
    
    @patch('subprocess.run')
    def test_validate_valid_file_with_ffprobe(self, mock_run):
        """Test de validation d'un fichier valide avec FFprobe."""
        # Créer un fichier de test
        temp_file = Path(self.temp_dir) / "test.mp4"
        temp_file.write_bytes(b"fake video content")
        
        # Mock de la réponse FFprobe
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [
                {"codec_type": "video", "codec_name": "h264"}
            ],
            "format": {
                "duration": "120.5"
            }
        }
        '''
        mock_run.return_value = mock_result
        
        # Le test devrait passer
        assert self.file_manager.validate_video_file(str(temp_file)) is True
    
    @patch('subprocess.run')
    def test_validate_corrupted_file_with_ffprobe(self, mock_run):
        """Test de validation d'un fichier corrompu avec FFprobe."""
        # Créer un fichier de test
        temp_file = Path(self.temp_dir) / "corrupted.mp4"
        temp_file.write_bytes(b"fake video content")
        
        # Mock d'une réponse d'erreur FFprobe
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid data found"
        mock_run.return_value = mock_result
        
        with pytest.raises(ValidationError, match="corrompu ou non lisible"):
            self.file_manager.validate_video_file(str(temp_file))
    
    def test_basic_file_validation_mp4(self):
        """Test de validation basique pour MP4."""
        # Créer un fichier avec signature MP4
        temp_file = Path(self.temp_dir) / "test.mp4"
        # Signature MP4 basique
        mp4_header = b'\x00\x00\x00\x18ftypmp41\x00\x00\x00\x00'
        temp_file.write_bytes(mp4_header + b'fake content')
        
        # Test de validation basique (sans FFprobe)
        assert self.file_manager._basic_file_validation(str(temp_file)) is True
    
    def test_basic_file_validation_avi(self):
        """Test de validation basique pour AVI."""
        # Créer un fichier avec signature AVI
        temp_file = Path(self.temp_dir) / "test.avi"
        # Signature AVI basique
        avi_header = b'RIFF\x00\x00\x00\x00AVI LIST'
        temp_file.write_bytes(avi_header + b'fake content')
        
        assert self.file_manager._basic_file_validation(str(temp_file)) is True
    
    def test_create_temp_directory(self):
        """Test de création de répertoire temporaire."""
        temp_dir = self.file_manager.create_temp_directory()
        
        assert os.path.exists(temp_dir)
        assert temp_dir in self.file_manager.temp_directories
    
    def test_cleanup_temp_files(self):
        """Test de nettoyage des fichiers temporaires."""
        # Créer quelques répertoires temporaires
        temp_dir1 = self.file_manager.create_temp_directory()
        temp_dir2 = self.file_manager.create_temp_directory()
        
        # Vérifier qu'ils existent
        assert os.path.exists(temp_dir1)
        assert os.path.exists(temp_dir2)
        
        # Nettoyer
        self.file_manager.cleanup_temp_files()
        
        # Vérifier qu'ils ont été supprimés
        assert not os.path.exists(temp_dir1)
        assert not os.path.exists(temp_dir2)
        assert len(self.file_manager.temp_directories) == 0
    
    def test_get_file_info_basic(self):
        """Test d'obtention d'informations de fichier basiques."""
        # Créer un fichier de test
        temp_file = Path(self.temp_dir) / "test.mp4"
        content = b"fake video content"
        temp_file.write_bytes(content)
        
        info = self.file_manager.get_file_info(str(temp_file))
        
        assert info['name'] == 'test.mp4'
        assert info['size'] == len(content)
        assert info['extension'] == '.mp4'
        assert 'path' in info
        assert 'created' in info
        assert 'modified' in info
    
    def test_parse_fps(self):
        """Test du parsing de FPS."""
        assert self.file_manager._parse_fps('25/1') == 25.0
        assert self.file_manager._parse_fps('30000/1001') == pytest.approx(29.97, rel=1e-2)
        assert self.file_manager._parse_fps('invalid') == 0.0
        assert self.file_manager._parse_fps('25/0') == 0.0
    
    def test_get_safe_filename(self):
        """Test de génération de nom de fichier sûr."""
        unsafe_name = 'test<>:"/\\|?*file.mp4'
        safe_name = self.file_manager.get_safe_filename(unsafe_name)
        
        assert '<' not in safe_name
        assert '>' not in safe_name
        assert ':' not in safe_name
        assert '"' not in safe_name
        assert '/' not in safe_name
        assert '\\' not in safe_name
        assert '|' not in safe_name
        assert '?' not in safe_name
        assert '*' not in safe_name
    
    def test_get_safe_filename_empty(self):
        """Test de génération de nom de fichier sûr pour chaîne vide."""
        safe_name = self.file_manager.get_safe_filename("")
        assert safe_name == "unnamed_file"
    
    def test_copy_file(self):
        """Test de copie de fichier."""
        # Créer un fichier source
        source_file = Path(self.temp_dir) / "source.mp4"
        content = b"test content"
        source_file.write_bytes(content)
        
        # Copier vers une destination
        dest_file = Path(self.temp_dir) / "subdir" / "dest.mp4"
        self.file_manager.copy_file(str(source_file), str(dest_file))
        
        # Vérifier que la copie a réussi
        assert dest_file.exists()
        assert dest_file.read_bytes() == content
    
    def test_ensure_directory_exists(self):
        """Test de création de répertoire."""
        test_dir = Path(self.temp_dir) / "new" / "nested" / "directory"
        
        self.file_manager.ensure_directory_exists(str(test_dir))
        
        assert test_dir.exists()
        assert test_dir.is_dir()