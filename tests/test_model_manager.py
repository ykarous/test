"""
Tests pour le gestionnaire de modèles légers
"""

import pytest
from unittest.mock import Mock, patch
import psutil

from ai_video_dubbing.performance.model_manager import (
    LightweightModelManager, ModelInfo, ModelRecommendation, SystemResources
)


class TestLightweightModelManager:
    """Tests pour le gestionnaire de modèles légers"""
    
    @pytest.fixture
    def manager(self):
        """Fixture pour créer un gestionnaire"""
        return LightweightModelManager()
    
    def test_model_catalog_initialization(self, manager):
        """Test de l'initialisation du catalogue de modèles"""
        catalog = manager.model_catalog
        
        # Vérifier qu'il y a des modèles
        assert len(catalog) > 0
        
        # Vérifier la présence de modèles ultra-légers
        ultra_light_models = [m for m in catalog.values() if m.category == "ultra_light"]
        assert len(ultra_light_models) > 0
        
        # Vérifier un modèle spécifique
        assert "whisper-tiny" in catalog
        whisper_tiny = catalog["whisper-tiny"]
        assert whisper_tiny.size_mb == 39
        assert whisper_tiny.quality == "basic"
        assert "multilingual" in whisper_tiny.languages
    
    def test_get_models_by_category(self, manager):
        """Test de récupération de modèles par catégorie"""
        ultra_light = manager.get_models_by_category("ultra_light")
        light = manager.get_models_by_category("light")
        
        assert len(ultra_light) > 0
        assert len(light) > 0
        
        # Vérifier que tous les modèles ultra-légers sont bien dans cette catégorie
        for model in ultra_light:
            assert model.category == "ultra_light"
    
    def test_get_model_info(self, manager):
        """Test de récupération d'informations de modèle"""
        model_info = manager.get_model_info("whisper-tiny")
        
        assert model_info is not None
        assert model_info.name == "whisper-tiny"
        assert model_info.category == "ultra_light"
        
        # Test avec modèle inexistant
        assert manager.get_model_info("nonexistent-model") is None
    
    def test_get_available_models_with_filters(self, manager):
        """Test de récupération de modèles avec filtres"""
        # Filtrer par type
        asr_models = manager.get_available_models(model_type="asr")
        assert len(asr_models) > 0
        assert all(m.model_type == "asr" for m in asr_models)
        
        # Filtrer par taille
        small_models = manager.get_available_models(max_size_mb=100)
        assert len(small_models) > 0
        assert all(m.size_mb <= 100 for m in small_models)
        
        # Filtrer par compatibilité dispositif
        cpu_models = manager.get_available_models(device_compatibility="cpu")
        assert len(cpu_models) > 0
        assert all("cpu" in m.device_compatibility for m in cpu_models)
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    @patch('psutil.disk_usage')
    def test_detect_system_resources(self, mock_disk, mock_cpu, mock_memory, manager):
        """Test de détection des ressources système"""
        # Mock des valeurs système
        mock_memory.return_value = Mock(
            available=4 * 1024 * 1024 * 1024,  # 4GB
            total=8 * 1024 * 1024 * 1024,      # 8GB
            percent=50.0
        )
        mock_cpu.return_value = 8
        mock_disk.return_value = Mock(
            free=100 * 1024 * 1024 * 1024  # 100GB
        )
        
        # Forcer la re-détection
        manager.system_resources = None
        resources = manager.get_system_resources()
        
        assert resources.available_memory_mb == 4096
        assert resources.total_memory_mb == 8192
        assert resources.memory_usage_percent == 50.0
        assert resources.cpu_count == 8
        assert resources.disk_space_gb == 100.0
    
    def test_get_recommended_model_speed_preference(self, manager):
        """Test de recommandation avec préférence vitesse"""
        # Mock des ressources limitées
        manager.system_resources = SystemResources(
            available_memory_mb=1000,
            total_memory_mb=2000,
            memory_usage_percent=50.0,
            cpu_count=4,
            gpu_available=False,
            gpu_memory_mb=0,
            disk_space_gb=50.0,
            connection_speed_mbps=5.0
        )
        
        recommendation = manager.get_recommended_model(
            model_type="asr",
            quality_preference="speed"
        )
        
        assert recommendation.model_name in manager.model_catalog
        model = manager.model_catalog[recommendation.model_name]
        assert model.category in ["ultra_light", "light"]
        assert recommendation.confidence > 0
    
    def test_get_recommended_model_quality_preference(self, manager):
        """Test de recommandation avec préférence qualité"""
        # Mock des ressources importantes
        manager.system_resources = SystemResources(
            available_memory_mb=8000,
            total_memory_mb=16000,
            memory_usage_percent=30.0,
            cpu_count=8,
            gpu_available=True,
            gpu_memory_mb=8000,
            disk_space_gb=500.0,
            connection_speed_mbps=50.0
        )
        
        recommendation = manager.get_recommended_model(
            model_type="asr",
            quality_preference="quality"
        )
        
        assert recommendation.model_name in manager.model_catalog
        model = manager.model_catalog[recommendation.model_name]
        # Avec de bonnes ressources, devrait recommander un modèle plus lourd
        assert model.category in ["medium", "heavy"]
    
    def test_get_recommended_model_with_language(self, manager):
        """Test de recommandation avec langue spécifique"""
        recommendation = manager.get_recommended_model(
            model_type="asr",
            language="fr"
        )
        
        assert recommendation.model_name in manager.model_catalog
        model = manager.model_catalog[recommendation.model_name]
        assert "fr" in model.languages or "multilingual" in model.languages
    
    def test_score_model_logic(self, manager):
        """Test de la logique de scoring des modèles"""
        # Ressources moyennes
        resources = SystemResources(
            available_memory_mb=4000,
            total_memory_mb=8000,
            memory_usage_percent=50.0,
            cpu_count=4,
            gpu_available=True,
            gpu_memory_mb=4000,
            disk_space_gb=100.0,
            connection_speed_mbps=20.0
        )
        
        # Tester avec différents modèles
        whisper_tiny = manager.model_catalog["whisper-tiny"]
        whisper_base = manager.model_catalog["whisper-base"]
        
        score_tiny_speed = manager._score_model(whisper_tiny, resources, "speed", "auto")
        score_base_speed = manager._score_model(whisper_base, resources, "speed", "auto")
        
        # Pour préférence vitesse, tiny devrait avoir un meilleur score
        assert score_tiny_speed > score_base_speed
        
        score_tiny_quality = manager._score_model(whisper_tiny, resources, "quality", "auto")
        score_base_quality = manager._score_model(whisper_base, resources, "quality", "auto")
        
        # Pour préférence qualité, base devrait avoir un meilleur score
        assert score_base_quality > score_tiny_quality
    
    def test_adjust_download_time(self, manager):
        """Test d'ajustement du temps de téléchargement"""
        base_time = 100  # secondes
        
        # Connexion rapide
        fast_time = manager._adjust_download_time(base_time, 50.0)
        assert fast_time < base_time
        
        # Connexion lente
        slow_time = manager._adjust_download_time(base_time, 2.0)
        assert slow_time > base_time
        
        # Minimum garanti
        very_fast_time = manager._adjust_download_time(5, 1000.0)
        assert very_fast_time >= 10
    
    def test_generate_recommendation_reason(self, manager):
        """Test de génération de raison de recommandation"""
        model = manager.model_catalog["whisper-tiny"]
        resources = SystemResources(
            available_memory_mb=1000,
            total_memory_mb=2000,
            memory_usage_percent=70.0,
            cpu_count=2,
            gpu_available=False,
            gpu_memory_mb=0,
            disk_space_gb=20.0,
            connection_speed_mbps=3.0
        )
        
        reason = manager._generate_recommendation_reason(model, resources, "speed")
        
        assert isinstance(reason, str)
        assert len(reason) > 0
        # Devrait mentionner que c'est ultra-léger
        assert "ultra-léger" in reason or "mémoire limitée" in reason
    
    def test_performance_stats(self, manager):
        """Test des statistiques de performance"""
        stats = manager.get_performance_stats()
        
        assert "total_models" in stats
        assert "models_by_category" in stats
        assert "models_by_type" in stats
        assert "system_resources" in stats
        
        assert stats["total_models"] > 0
        assert "ultra_light" in stats["models_by_category"]
        assert "asr" in stats["models_by_type"]
    
    def test_refresh_system_resources(self, manager):
        """Test de rafraîchissement des ressources système"""
        # Obtenir les ressources une première fois
        resources1 = manager.get_system_resources()
        
        # Rafraîchir
        manager.refresh_system_resources()
        
        # Les ressources devraient être re-détectées
        assert manager.system_resources is None
        assert manager.connection_speed_cache is None
        
        # Obtenir à nouveau
        resources2 = manager.get_system_resources()
        
        # Devrait avoir des valeurs (même si potentiellement identiques)
        assert resources2 is not None
    
    @patch('requests.get')
    def test_estimate_connection_speed(self, mock_get, manager):
        """Test d'estimation de vitesse de connexion"""
        # Mock d'une réponse rapide
        mock_response = Mock()
        mock_response.content = b'x' * 1024  # 1KB
        mock_get.return_value = mock_response
        
        # Simuler un téléchargement rapide
        with patch('time.time', side_effect=[0, 0.1]):  # 0.1 seconde
            speed = manager._estimate_connection_speed()
            assert speed > 0
            assert speed <= 100.0  # Cap à 100 Mbps
    
    @patch('requests.get')
    def test_estimate_connection_speed_error(self, mock_get, manager):
        """Test d'estimation de vitesse avec erreur réseau"""
        # Mock d'une erreur réseau
        mock_get.side_effect = Exception("Network error")
        
        speed = manager._estimate_connection_speed()
        assert speed == 10.0  # Valeur par défaut


@pytest.mark.integration
def test_integration_with_real_system():
    """Test d'intégration avec le système réel"""
    manager = LightweightModelManager()
    
    # Test de détection des ressources réelles
    resources = manager.get_system_resources()
    assert resources.available_memory_mb > 0
    assert resources.total_memory_mb > 0
    assert resources.cpu_count > 0
    
    # Test de recommandation réelle
    recommendation = manager.get_recommended_model(model_type="asr")
    assert recommendation.model_name in manager.model_catalog
    assert recommendation.confidence > 0
    assert len(recommendation.reason) > 0
    
    # Test des statistiques
    stats = manager.get_performance_stats()
    assert stats["total_models"] > 0