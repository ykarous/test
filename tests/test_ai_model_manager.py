"""
Tests pour le gestionnaire de modèles IA.
"""

import time
import tempfile
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from ai_video_dubbing.processors.ai_model_manager import AIModelManager, ModelInfo
from ai_video_dubbing.models.data_models import (
    ModelType, ProcessingError, ResourceError, ValidationError
)


class TestAIModelManager:
    """Tests pour AIModelManager."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        # Mock des dépendances pour éviter les imports
        with patch.multiple(
            'ai_video_dubbing.processors.ai_model_manager',
            _TORCH_AVAILABLE=True,
            _WHISPER_AVAILABLE=True,
            _TRANSFORMERS_AVAILABLE=True,
            _PADDLEOCR_AVAILABLE=True,
            _EASYOCR_AVAILABLE=True
        ):
            self.manager = AIModelManager(max_memory_usage=0.8, cache_timeout=10)
    
    def test_init(self):
        """Test d'initialisation du gestionnaire."""
        assert self.manager.max_memory_usage == 0.8
        assert self.manager.cache_timeout == 10
        assert len(self.manager._loaded_models) == 0
        assert self.manager._cleanup_thread.is_alive()
    
    def test_model_key_generation(self):
        """Test de génération de clés de modèles."""
        key = self.manager._model_key(ModelType.ASR, "whisper-base")
        assert key == "asr:whisper-base"
        
        key = self.manager._model_key(ModelType.OCR, "paddleocr")
        assert key == "ocr:paddleocr"
    
    def test_estimate_model_size(self):
        """Test d'estimation de taille de modèle."""
        # Modèle connu
        size = self.manager._estimate_model_size(ModelType.ASR, "whisper-base")
        assert size == 74  # Défini dans la config
        
        # Modèle inconnu
        size = self.manager._estimate_model_size(ModelType.ASR, "unknown-model")
        assert size == 500  # Taille par défaut pour ASR
        
        # Type inconnu
        size = self.manager._estimate_model_size(ModelType.DIARIZATION, "unknown")
        assert size == 200  # Taille par défaut générique
    
    @patch('ai_video_dubbing.processors.ai_model_manager.psutil')
    def test_get_memory_usage(self, mock_psutil):
        """Test d'obtention de l'utilisation mémoire."""
        # Mock de psutil
        mock_memory = MagicMock()
        mock_memory.percent = 75.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        usage = self.manager._get_memory_usage()
        assert usage == 0.75
    
    @patch('ai_video_dubbing.processors.ai_model_manager.psutil')
    def test_get_available_memory_mb(self, mock_psutil):
        """Test d'obtention de la mémoire disponible."""
        # Mock de psutil
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.used = 4 * 1024 * 1024 * 1024   # 4GB utilisés
        mock_psutil.virtual_memory.return_value = mock_memory
        
        available = self.manager._get_available_memory_mb()
        
        # max_memory_usage = 0.8, donc 8GB * 0.8 = 6.4GB max
        # 6.4GB - 4GB = 2.4GB disponible = 2457.6MB
        expected = (8 * 1024 * 0.8 - 4 * 1024)  # En MB
        assert abs(available - expected) < 1  # Tolérance pour les arrondis
    
    def test_model_info_creation(self):
        """Test de création d'informations de modèle."""
        mock_model = MagicMock()
        model_info = ModelInfo(
            model=mock_model,
            model_type=ModelType.ASR,
            model_name="whisper-base",
            memory_usage=100.0
        )
        
        assert model_info.model == mock_model
        assert model_info.model_type == ModelType.ASR
        assert model_info.model_name == "whisper-base"
        assert model_info.memory_usage == 100.0
        assert model_info.last_used > 0
        assert model_info.load_time > 0
    
    @patch.object(AIModelManager, '_load_whisper_model')
    @patch.object(AIModelManager, '_get_memory_usage')
    @patch.object(AIModelManager, '_free_memory_if_needed')
    def test_load_model_success(self, mock_free_memory, mock_get_memory, mock_load_whisper):
        """Test de chargement de modèle réussi."""
        # Setup
        mock_get_memory.return_value = 0.5  # 50% utilisé
        mock_model = MagicMock()
        mock_load_whisper.return_value = mock_model
        
        # Test
        self.manager.load_model(ModelType.ASR, "whisper-base")
        
        # Vérifications
        model_key = "asr:whisper-base"
        assert model_key in self.manager._loaded_models
        
        model_info = self.manager._loaded_models[model_key]
        assert model_info.model == mock_model
        assert model_info.model_type == ModelType.ASR
        assert model_info.model_name == "whisper-base"
        
        mock_load_whisper.assert_called_once_with("whisper-base")
        mock_free_memory.assert_called_once()
    
    @patch.object(AIModelManager, '_get_memory_usage')
    def test_load_model_memory_too_high(self, mock_get_memory):
        """Test de chargement avec mémoire trop élevée."""
        mock_get_memory.return_value = 0.95  # 95% utilisé
        
        try:
            self.manager.load_model(ModelType.ASR, "whisper-base")
            assert False, "Devrait lever ResourceError"
        except ResourceError as e:
            assert "memory usage too high" in str(e).lower()
    
    def test_load_model_already_loaded(self):
        """Test de chargement d'un modèle déjà chargé."""
        # Ajouter un modèle manuellement
        mock_model = MagicMock()
        model_info = ModelInfo(
            model=mock_model,
            model_type=ModelType.ASR,
            model_name="whisper-base",
            memory_usage=100.0
        )
        model_key = "asr:whisper-base"
        self.manager._loaded_models[model_key] = model_info
        
        original_time = model_info.last_used
        time.sleep(0.01)  # Petit délai
        
        # Tenter de charger à nouveau
        with patch.object(self.manager, '_load_model_by_type') as mock_load:
            self.manager.load_model(ModelType.ASR, "whisper-base")
            
            # Ne devrait pas charger à nouveau
            mock_load.assert_not_called()
            
            # Devrait mettre à jour last_used
            assert self.manager._loaded_models[model_key].last_used > original_time
    
    @patch('ai_video_dubbing.processors.ai_model_manager.whisper')
    @patch('ai_video_dubbing.processors.ai_model_manager._WHISPER_AVAILABLE', True)
    def test_load_whisper_model(self, mock_whisper):
        """Test de chargement de modèle Whisper."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        result = self.manager._load_whisper_model("whisper-base")
        
        assert result == mock_model
        mock_whisper.load_model.assert_called_once_with("base")
    
    @patch('ai_video_dubbing.processors.ai_model_manager.paddleocr')
    @patch('ai_video_dubbing.processors.ai_model_manager._PADDLEOCR_AVAILABLE', True)
    def test_load_paddleocr_model(self, mock_paddleocr):
        """Test de chargement de modèle PaddleOCR."""
        mock_ocr = MagicMock()
        mock_paddleocr.PaddleOCR.return_value = mock_ocr
        
        result = self.manager._load_ocr_model("paddleocr")
        
        assert result == mock_ocr
        mock_paddleocr.PaddleOCR.assert_called_once_with(use_angle_cls=True, lang='en')
    
    @patch('ai_video_dubbing.processors.ai_model_manager.easyocr')
    @patch('ai_video_dubbing.processors.ai_model_manager._EASYOCR_AVAILABLE', True)
    def test_load_easyocr_model(self, mock_easyocr):
        """Test de chargement de modèle EasyOCR."""
        mock_reader = MagicMock()
        mock_easyocr.Reader.return_value = mock_reader
        
        result = self.manager._load_ocr_model("easyocr")
        
        assert result == mock_reader
        mock_easyocr.Reader.assert_called_once_with(['en', 'fr'])
    
    def test_load_unsupported_ocr_model(self):
        """Test de chargement de modèle OCR non supporté."""
        try:
            self.manager._load_ocr_model("unsupported")
            assert False, "Devrait lever ProcessingError"
        except ProcessingError as e:
            assert "Unsupported OCR model" in str(e)
    
    def test_get_model_auto_load(self):
        """Test d'obtention de modèle avec chargement automatique."""
        with patch.object(self.manager, 'load_model') as mock_load:
            mock_load.return_value = None
            
            # Ajouter le modèle après le "chargement"
            mock_model = MagicMock()
            model_info = ModelInfo(
                model=mock_model,
                model_type=ModelType.ASR,
                model_name="whisper-base",
                memory_usage=100.0
            )
            
            def side_effect(model_type, model_name):
                model_key = self.manager._model_key(model_type, model_name)
                self.manager._loaded_models[model_key] = model_info
            
            mock_load.side_effect = side_effect
            
            result = self.manager.get_model(ModelType.ASR, "whisper-base")
            
            assert result == mock_model
            mock_load.assert_called_once_with(ModelType.ASR, "whisper-base")
    
    def test_unload_specific_model(self):
        """Test de déchargement d'un modèle spécifique."""
        # Ajouter des modèles
        mock_model1 = MagicMock()
        mock_model2 = MagicMock()
        
        self.manager._loaded_models["asr:whisper-base"] = ModelInfo(
            mock_model1, ModelType.ASR, "whisper-base", 100.0
        )
        self.manager._loaded_models["asr:whisper-large"] = ModelInfo(
            mock_model2, ModelType.ASR, "whisper-large", 200.0
        )
        
        # Décharger un modèle spécifique
        self.manager.unload_model(ModelType.ASR, "whisper-base")
        
        # Vérifications
        assert "asr:whisper-base" not in self.manager._loaded_models
        assert "asr:whisper-large" in self.manager._loaded_models
    
    def test_unload_all_models_of_type(self):
        """Test de déchargement de tous les modèles d'un type."""
        # Ajouter des modèles de différents types
        self.manager._loaded_models["asr:whisper-base"] = ModelInfo(
            MagicMock(), ModelType.ASR, "whisper-base", 100.0
        )
        self.manager._loaded_models["asr:whisper-large"] = ModelInfo(
            MagicMock(), ModelType.ASR, "whisper-large", 200.0
        )
        self.manager._loaded_models["ocr:paddleocr"] = ModelInfo(
            MagicMock(), ModelType.OCR, "paddleocr", 50.0
        )
        
        # Décharger tous les modèles ASR
        self.manager.unload_model(ModelType.ASR)
        
        # Vérifications
        assert "asr:whisper-base" not in self.manager._loaded_models
        assert "asr:whisper-large" not in self.manager._loaded_models
        assert "ocr:paddleocr" in self.manager._loaded_models
    
    def test_get_loaded_models(self):
        """Test d'obtention de la liste des modèles chargés."""
        # Ajouter un modèle
        mock_model = MagicMock()
        model_info = ModelInfo(
            mock_model, ModelType.ASR, "whisper-base", 100.0
        )
        self.manager._loaded_models["asr:whisper-base"] = model_info
        
        result = self.manager.get_loaded_models()
        
        assert "asr:whisper-base" in result
        model_data = result["asr:whisper-base"]
        assert model_data["model_type"] == "asr"
        assert model_data["model_name"] == "whisper-base"
        assert model_data["memory_usage_mb"] == 100.0
        assert "last_used" in model_data
        assert "load_time" in model_data
        assert "age_seconds" in model_data
    
    @patch('ai_video_dubbing.processors.ai_model_manager.psutil')
    def test_get_memory_stats(self, mock_psutil):
        """Test d'obtention des statistiques mémoire."""
        # Mock de psutil
        mock_memory = MagicMock()
        mock_memory.percent = 60.0
        mock_memory.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_memory.total = 8 * 1024 * 1024 * 1024      # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # Ajouter des modèles
        self.manager._loaded_models["asr:whisper-base"] = ModelInfo(
            MagicMock(), ModelType.ASR, "whisper-base", 100.0
        )
        self.manager._loaded_models["ocr:paddleocr"] = ModelInfo(
            MagicMock(), ModelType.OCR, "paddleocr", 50.0
        )
        
        stats = self.manager.get_memory_stats()
        
        assert stats["system_memory_percent"] == 60.0
        assert stats["system_memory_available_mb"] == 2048.0  # 2GB en MB
        assert stats["system_memory_total_mb"] == 8192.0     # 8GB en MB
        assert stats["models_memory_mb"] == 150.0            # 100 + 50
        assert stats["models_count"] == 2
        assert stats["max_memory_usage"] == 0.8
    
    def test_cleanup_all(self):
        """Test de nettoyage de tous les modèles."""
        # Ajouter des modèles
        self.manager._loaded_models["asr:whisper-base"] = ModelInfo(
            MagicMock(), ModelType.ASR, "whisper-base", 100.0
        )
        self.manager._loaded_models["ocr:paddleocr"] = ModelInfo(
            MagicMock(), ModelType.OCR, "paddleocr", 50.0
        )
        
        assert len(self.manager._loaded_models) == 2
        
        # Nettoyer tout
        self.manager.cleanup_all()
        
        # Vérifications
        assert len(self.manager._loaded_models) == 0
    
    def test_free_memory_if_needed(self):
        """Test de libération de mémoire si nécessaire."""
        # Ajouter des modèles avec différents âges
        old_model = ModelInfo(MagicMock(), ModelType.ASR, "whisper-base", 100.0)
        old_model.last_used = time.time() - 100  # Plus ancien
        
        new_model = ModelInfo(MagicMock(), ModelType.OCR, "paddleocr", 50.0)
        new_model.last_used = time.time() - 10   # Plus récent
        
        self.manager._loaded_models["asr:whisper-base"] = old_model
        self.manager._loaded_models["ocr:paddleocr"] = new_model
        
        # Mock de la mémoire disponible (insuffisante)
        with patch.object(self.manager, '_get_available_memory_mb', return_value=50.0):
            # Demander 120MB (devrait libérer le modèle le plus ancien)
            self.manager._free_memory_if_needed(120.0)
            
            # Le modèle ancien devrait être déchargé
            assert "asr:whisper-base" not in self.manager._loaded_models
            assert "ocr:paddleocr" in self.manager._loaded_models
    
    def test_estimate_actual_memory_usage_pytorch(self):
        """Test d'estimation de mémoire pour modèle PyTorch."""
        # Mock d'un modèle PyTorch
        mock_model = MagicMock()
        mock_param1 = MagicMock()
        mock_param1.numel.return_value = 1000000  # 1M paramètres
        mock_param2 = MagicMock()
        mock_param2.numel.return_value = 500000   # 500K paramètres
        
        mock_model.parameters.return_value = [mock_param1, mock_param2]
        
        with patch('ai_video_dubbing.processors.ai_model_manager._TORCH_AVAILABLE', True):
            memory_mb = self.manager._estimate_actual_memory_usage(mock_model)
            
            # 1.5M paramètres * 4 bytes = 6MB
            expected_mb = (1500000 * 4) / (1024 * 1024)
            assert abs(memory_mb - expected_mb) < 0.1
    
    def test_estimate_actual_memory_usage_fallback(self):
        """Test d'estimation de mémoire avec fallback."""
        mock_model = MagicMock()
        # Pas de méthode parameters
        del mock_model.parameters
        
        memory_mb = self.manager._estimate_actual_memory_usage(mock_model)
        assert memory_mb == 100.0  # Valeur par défaut
    
    def test_not_implemented_methods(self):
        """Test des méthodes non encore implémentées."""
        # transcribe_audio est maintenant implémentée, mais teste avec un fichier inexistant
        try:
            self.manager.transcribe_audio("nonexistent.wav")
            assert False, "Devrait lever ValidationError"
        except ValidationError:
            pass  # Comportement attendu
        
        # extract_text_from_frames est implémentée
        result = self.manager.extract_text_from_frames([])
        assert result == []  # Liste vide pour entrée vide
        
        # clone_voice n'est pas encore implémentée (tâche 12)
        try:
            self.manager.clone_voice("ref.wav", "text")
            assert False, "Devrait lever NotImplementedError"
        except NotImplementedError:
            pass