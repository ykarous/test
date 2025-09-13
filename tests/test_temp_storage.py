"""
Tests pour le gestionnaire de stockage temporaire.
"""

import pytest
import tempfile
import os
from pathlib import Path

from ai_video_dubbing.utils.temp_storage import TempStorage


class TestTempStorage:
    """Tests pour TempStorage."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_base = tempfile.mkdtemp()
        self.storage = TempStorage(base_dir=self.temp_base)
    
    def teardown_method(self):
        """Nettoyage après chaque test."""
        self.storage.cleanup_all()
    
    def test_session_directory_creation(self):
        """Test de création du répertoire de session."""
        assert self.storage.session_dir is not None
        assert self.storage.session_dir.exists()
        assert self.storage.session_id is not None
        assert len(self.storage.session_id) == 8
    
    def test_create_temp_file(self):
        """Test de création de fichier temporaire."""
        temp_file = self.storage.create_temp_file(suffix='.wav', category='audio')
        
        assert os.path.exists(temp_file)
        assert temp_file.endswith('.wav')
        assert 'audio' in temp_file
        assert temp_file in self.storage.temp_files.values()
    
    def test_create_temp_directory(self):
        """Test de création de répertoire temporaire."""
        temp_dir = self.storage.create_temp_directory(name='test_dir', category='processing')
        
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        assert 'test_dir' in temp_dir
        assert 'processing' in temp_dir
        assert temp_dir in self.storage.temp_files.values()
    
    def test_get_temp_path(self):
        """Test d'obtention de chemin temporaire."""
        temp_path = self.storage.get_temp_path('test_file.mp4', category='video')
        
        assert 'test_file.mp4' in temp_path
        assert 'video' in temp_path
        # Le répertoire parent devrait exister
        assert os.path.exists(os.path.dirname(temp_path))
    
    def test_save_intermediate_result(self):
        """Test de sauvegarde de résultat intermédiaire."""
        test_data = b'test binary data'
        saved_path = self.storage.save_intermediate_result(
            test_data, 
            'result.bin', 
            category='results'
        )
        
        assert os.path.exists(saved_path)
        with open(saved_path, 'rb') as f:
            assert f.read() == test_data
        assert saved_path in self.storage.temp_files.values()
    
    def test_get_session_info(self):
        """Test d'obtention d'informations de session."""
        # Créer quelques fichiers
        self.storage.create_temp_file(suffix='.wav', category='audio')
        self.storage.create_temp_file(suffix='.mp4', category='video')
        self.storage.save_intermediate_result(b'data', 'test.txt', 'results')
        
        info = self.storage.get_session_info()
        
        assert info['session_id'] == self.storage.session_id
        assert info['file_count'] >= 3
        assert info['total_size_bytes'] > 0
        assert info['registered_files'] >= 3
    
    def test_list_files_by_category(self):
        """Test de listage de fichiers par catégorie."""
        # Créer des fichiers dans différentes catégories
        audio_file = self.storage.create_temp_file(suffix='.wav', category='audio')
        video_file = self.storage.create_temp_file(suffix='.mp4', category='video')
        
        # Lister tous les fichiers
        all_files = self.storage.list_files_by_category()
        assert audio_file in all_files
        assert video_file in all_files
        
        # Lister par catégorie
        audio_files = self.storage.list_files_by_category('audio')
        assert audio_file in audio_files
        assert video_file not in audio_files
        
        video_files = self.storage.list_files_by_category('video')
        assert video_file in video_files
        assert audio_file not in video_files
    
    def test_cleanup_category(self):
        """Test de nettoyage par catégorie."""
        # Créer des fichiers dans différentes catégories
        audio_file = self.storage.create_temp_file(suffix='.wav', category='audio')
        video_file = self.storage.create_temp_file(suffix='.mp4', category='video')
        
        # Vérifier qu'ils existent
        assert os.path.exists(audio_file)
        assert os.path.exists(video_file)
        
        # Nettoyer seulement la catégorie audio
        self.storage.cleanup_category('audio')
        
        # Vérifier que seuls les fichiers audio ont été supprimés
        assert not os.path.exists(audio_file)
        assert os.path.exists(video_file)
        
        # Vérifier que les entrées ont été supprimées
        audio_files = self.storage.list_files_by_category('audio')
        video_files = self.storage.list_files_by_category('video')
        assert len(audio_files) == 0
        assert len(video_files) > 0
    
    def test_cleanup_all(self):
        """Test de nettoyage complet."""
        # Créer quelques fichiers
        audio_file = self.storage.create_temp_file(suffix='.wav', category='audio')
        video_file = self.storage.create_temp_file(suffix='.mp4', category='video')
        
        # Vérifier qu'ils existent
        assert os.path.exists(audio_file)
        assert os.path.exists(video_file)
        assert self.storage.session_dir.exists()
        
        # Nettoyer tout
        self.storage.cleanup_all()
        
        # Vérifier que tout a été supprimé
        assert not os.path.exists(audio_file)
        assert not os.path.exists(video_file)
        assert not self.storage.session_dir.exists()
        assert len(self.storage.temp_files) == 0
    
    def test_context_manager(self):
        """Test du context manager."""
        session_dir = None
        
        with TempStorage(base_dir=self.temp_base) as storage:
            session_dir = storage.session_dir
            temp_file = storage.create_temp_file(suffix='.test')
            
            # Vérifier que tout existe pendant le contexte
            assert session_dir.exists()
            assert os.path.exists(temp_file)
        
        # Vérifier que tout a été nettoyé après la sortie du contexte
        assert not session_dir.exists()
    
    def test_multiple_files_same_category(self):
        """Test de création de multiples fichiers dans la même catégorie."""
        files = []
        for i in range(5):
            temp_file = self.storage.create_temp_file(
                suffix=f'_{i}.wav', 
                category='audio'
            )
            files.append(temp_file)
        
        # Vérifier que tous les fichiers existent
        for file_path in files:
            assert os.path.exists(file_path)
        
        # Vérifier qu'ils sont tous dans la même catégorie
        audio_files = self.storage.list_files_by_category('audio')
        assert len(audio_files) == 5
        
        for file_path in files:
            assert file_path in audio_files