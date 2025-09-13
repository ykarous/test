"""
Tests pour le gestionnaire de cache des modèles
"""

import pytest
import asyncio
import tempfile
import shutil
import hashlib
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from ai_video_dubbing.performance.cache_manager import ModelCacheManager, CacheEntry, CacheStats

class TestModelCacheManager:
    """Tests pour le gestionnaire de cache des modèles"""
    
    def setup_method(self):
        """Setup pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = ModelCacheManager(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_is_model_cached_false(self):
        """Test is_model_cached avec modèle non en cache"""
        result = await self.cache_manager.is_model_cached("non_existent_model")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_and_validate_model(self):
        """Test l'ajout et la validation d'un modèle"""
        # Créer un fichier de test
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"test model content for validation"
        test_file.write_bytes(test_content)
        
        # Ajouter au cache
        success = await self.cache_manager.add_model_to_cache(
            "test_model", 
            str(test_file)
        )
        assert success is True
        
        # Vérifier qu'il est en cache
        is_cached = await self.cache_manager.is_model_cached("test_model")
        assert is_cached is True
        
        # Valider le modèle
        is_valid = await self.cache_manager.validate_model("test_model")
        assert is_valid is True
        
        # Vérifier le chemin
        path = self.cache_manager.get_model_path("test_model")
        assert path == str(test_file.absolute())
    
    @pytest.mark.asyncio
    async def test_validate_model_with_checksum(self):
        """Test la validation avec checksum"""
        # Créer un fichier de test
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"test model content for checksum validation"
        test_file.write_bytes(test_content)
        
        # Calculer le checksum attendu
        expected_checksum = hashlib.sha256(test_content).hexdigest()
        
        # Ajouter au cache avec checksum
        success = await self.cache_manager.add_model_to_cache(
            "test_model", 
            str(test_file),
            expected_checksum=expected_checksum
        )
        assert success is True
        
        # Valider le modèle
        is_valid = await self.cache_manager.validate_model("test_model")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_model_corrupted(self):
        """Test la validation d'un modèle corrompu"""
        # Créer un fichier de test
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"original content"
        test_file.write_bytes(test_content)
        
        # Ajouter au cache
        await self.cache_manager.add_model_to_cache("test_model", str(test_file))
        
        # Corrompre le fichier
        test_file.write_bytes(b"corrupted content")
        
        # La validation devrait échouer
        is_valid = await self.cache_manager.validate_model("test_model")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_remove_model(self):
        """Test la suppression d'un modèle"""
        # Créer et ajouter un modèle
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_file.write_bytes(b"test content")
        
        await self.cache_manager.add_model_to_cache("test_model", str(test_file))
        
        # Vérifier qu'il est en cache
        assert await self.cache_manager.is_model_cached("test_model")
        
        # Supprimer
        success = await self.cache_manager.remove_model("test_model")
        assert success is True
        
        # Vérifier qu'il n'est plus en cache
        assert not await self.cache_manager.is_model_cached("test_model")
        assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self):
        """Test le nettoyage automatique du cache"""
        # Configurer un cache avec une limite très petite
        small_cache = ModelCacheManager(cache_dir=self.temp_dir, max_cache_size_gb=0.001)  # 1MB
        
        # Créer plusieurs fichiers qui dépassent la limite
        files = []
        for i in range(3):
            test_file = Path(self.temp_dir) / f"test_model_{i}.bin"
            # Créer des fichiers de 500KB chacun
            test_content = b"x" * (500 * 1024)
            test_file.write_bytes(test_content)
            files.append(test_file)
            
            await small_cache.add_model_to_cache(f"test_model_{i}", str(test_file))
        
        # Le nettoyage devrait avoir été déclenché
        cached_models = small_cache.list_cached_models()
        # Certains modèles devraient avoir été supprimés
        assert len(cached_models) < 3
    
    def test_cache_stats(self):
        """Test les statistiques du cache"""
        stats = self.cache_manager.get_cache_stats()
        
        assert isinstance(stats, CacheStats)
        assert hasattr(stats, 'total_models')
        assert hasattr(stats, 'total_size_mb')
        assert hasattr(stats, 'available_space_mb')
        assert hasattr(stats, 'cache_hit_rate')
        assert hasattr(stats, 'last_cleanup')
        
        # Initialement, le cache devrait être vide
        assert stats.total_models == 0
        assert stats.total_size_mb == 0.0
    
    def test_list_cached_models_empty(self):
        """Test la liste des modèles en cache (vide)"""
        models = self.cache_manager.list_cached_models()
        assert isinstance(models, list)
        assert len(models) == 0
    
    @pytest.mark.asyncio
    async def test_list_cached_models_with_data(self):
        """Test la liste des modèles en cache avec données"""
        # Ajouter quelques modèles
        for i in range(2):
            test_file = Path(self.temp_dir) / f"test_model_{i}.bin"
            test_file.write_bytes(b"test content")
            await self.cache_manager.add_model_to_cache(f"test_model_{i}", str(test_file))
        
        models = self.cache_manager.list_cached_models()
        assert len(models) == 2
        
        # Vérifier la structure des données
        for model in models:
            assert 'name' in model
            assert 'size_mb' in model
            assert 'download_date' in model
            assert 'last_accessed' in model
            assert 'access_count' in model
            assert 'is_validated' in model
            assert 'file_path' in model
    
    @pytest.mark.asyncio
    async def test_model_access_tracking(self):
        """Test le suivi des accès aux modèles"""
        # Créer et ajouter un modèle
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_file.write_bytes(b"test content")
        await self.cache_manager.add_model_to_cache("test_model", str(test_file))
        
        # Accéder au modèle plusieurs fois
        initial_access_count = self.cache_manager.cache_index["test_model"].access_count
        
        for _ in range(3):
            await self.cache_manager.validate_model("test_model")
        
        # Le compteur d'accès devrait avoir augmenté
        final_access_count = self.cache_manager.cache_index["test_model"].access_count
        assert final_access_count > initial_access_count
    
    @pytest.mark.asyncio
    async def test_cache_index_persistence(self):
        """Test la persistance de l'index du cache"""
        # Ajouter un modèle
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_file.write_bytes(b"test content")
        await self.cache_manager.add_model_to_cache("test_model", str(test_file))
        
        # Créer un nouveau gestionnaire de cache avec le même répertoire
        new_cache_manager = ModelCacheManager(cache_dir=self.temp_dir)
        
        # Le modèle devrait toujours être disponible
        is_cached = await new_cache_manager.is_model_cached("test_model")
        assert is_cached is True
    
    @pytest.mark.asyncio
    async def test_invalid_checksum_rejection(self):
        """Test le rejet d'un modèle avec checksum invalide"""
        # Créer un fichier de test
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"test model content"
        test_file.write_bytes(test_content)
        
        # Essayer d'ajouter avec un mauvais checksum
        wrong_checksum = "invalid_checksum"
        
        success = await self.cache_manager.add_model_to_cache(
            "test_model", 
            str(test_file),
            expected_checksum=wrong_checksum
        )
        
        # L'ajout devrait échouer
        assert success is False
        
        # Le modèle ne devrait pas être en cache
        is_cached = await self.cache_manager.is_model_cached("test_model")
        assert is_cached is False
    
    @pytest.mark.asyncio
    async def test_missing_file_handling(self):
        """Test la gestion des fichiers manquants"""
        # Ajouter un modèle
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_file.write_bytes(b"test content")
        await self.cache_manager.add_model_to_cache("test_model", str(test_file))
        
        # Supprimer le fichier manuellement
        test_file.unlink()
        
        # Le modèle ne devrait plus être considéré comme en cache
        is_cached = await self.cache_manager.is_model_cached("test_model")
        assert is_cached is False
        
        # Il devrait être supprimé de l'index
        assert "test_model" not in self.cache_manager.cache_index


if __name__ == "__main__":
    pytest.main([__file__])