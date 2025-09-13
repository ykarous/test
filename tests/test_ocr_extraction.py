"""
Tests pour l'extraction OCR des sous-titres.
"""

import tempfile
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from ai_video_dubbing.processors.ai_model_manager import AIModelManager
from ai_video_dubbing.models.data_models import (
    ModelType, Frame, OCRResult, ProcessingError
)


class TestOCRExtraction:
    """Tests pour l'extraction OCR."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        # Mock des dépendances
        with patch.multiple(
            'ai_video_dubbing.processors.ai_model_manager',
            _TORCH_AVAILABLE=True,
            _WHISPER_AVAILABLE=True,
            _TRANSFORMERS_AVAILABLE=True,
            _PADDLEOCR_AVAILABLE=True,
            _EASYOCR_AVAILABLE=True
        ):
            self.manager = AIModelManager()
    
    def test_extract_text_from_frames_empty(self):
        """Test d'extraction avec liste vide."""
        result = self.manager.extract_text_from_frames([])
        assert result == []
    
    @patch.object(AIModelManager, 'get_model')
    @patch.object(AIModelManager, '_extract_text_from_single_frame')
    @patch.object(AIModelManager, '_post_process_ocr_results')
    def test_extract_text_from_frames_success(
        self, mock_post_process, mock_extract_single, mock_get_model
    ):
        """Test d'extraction réussie."""
        # Setup
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Créer des frames de test
        frames = [
            Frame(image_path="frame1.jpg", timestamp=1.0),
            Frame(image_path="frame2.jpg", timestamp=2.0)
        ]
        
        # Mock des résultats d'extraction
        ocr_results = [
            OCRResult(text="Hello", timestamp=1.0, confidence=0.9),
            OCRResult(text="World", timestamp=2.0, confidence=0.8)
        ]
        
        mock_extract_single.side_effect = [
            [ocr_results[0]],
            [ocr_results[1]]
        ]
        
        mock_post_process.return_value = ocr_results
        
        # Test
        result = self.manager.extract_text_from_frames(frames)
        
        # Vérifications
        assert result == ocr_results
        mock_get_model.assert_called_once_with(ModelType.OCR, "paddleocr")
        assert mock_extract_single.call_count == 2
        mock_post_process.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_extract_text_from_single_frame_file_not_found(self, mock_exists):
        """Test d'extraction avec fichier inexistant."""
        mock_exists.return_value = False
        
        frame = Frame(image_path="nonexistent.jpg", timestamp=1.0)
        mock_model = MagicMock()
        
        result = self.manager._extract_text_from_single_frame(
            frame, mock_model, "paddleocr"
        )
        
        assert result == []
    
    @patch('pathlib.Path.exists')
    @patch.object(AIModelManager, '_extract_with_paddleocr')
    def test_extract_text_from_single_frame_paddleocr(
        self, mock_paddle, mock_exists
    ):
        """Test d'extraction avec PaddleOCR."""
        # Setup
        mock_exists.return_value = True
        
        expected_result = [
            OCRResult(text="Test", timestamp=1.0, confidence=0.9)
        ]
        mock_paddle.return_value = expected_result
        
        frame = Frame(image_path="test.jpg", timestamp=1.0)
        mock_model = MagicMock()
        
        # Test
        result = self.manager._extract_text_from_single_frame(
            frame, mock_model, "paddleocr"
        )
        
        # Vérifications
        assert result == expected_result
        mock_paddle.assert_called_once_with(
            "test.jpg", mock_model, 1.0, 0.5
        )
    
    @patch('pathlib.Path.exists')
    @patch.object(AIModelManager, '_extract_with_easyocr')
    def test_extract_text_from_single_frame_easyocr(
        self, mock_easy, mock_exists
    ):
        """Test d'extraction avec EasyOCR."""
        # Setup
        mock_exists.return_value = True
        
        expected_result = [
            OCRResult(text="Test", timestamp=1.0, confidence=0.8)
        ]
        mock_easy.return_value = expected_result
        
        frame = Frame(image_path="test.jpg", timestamp=1.0)
        mock_model = MagicMock()
        
        # Test
        result = self.manager._extract_text_from_single_frame(
            frame, mock_model, "easyocr", languages=["en"]
        )
        
        # Vérifications
        assert result == expected_result
        mock_easy.assert_called_once_with(
            "test.jpg", mock_model, 1.0, 0.5, ["en"]
        )
    
    def test_extract_with_paddleocr_success(self):
        """Test d'extraction PaddleOCR réussie."""
        # Mock du modèle PaddleOCR
        mock_model = MagicMock()
        
        # Mock des résultats PaddleOCR
        mock_results = [[
            [
                [[100, 50], [200, 50], [200, 100], [100, 100]],  # bbox
                ("Hello World", 0.95)  # text, confidence
            ],
            [
                [[100, 120], [180, 120], [180, 150], [100, 150]],
                ("Test", 0.85)
            ]
        ]]
        
        mock_model.ocr.return_value = mock_results
        
        # Test
        results = self.manager._extract_with_paddleocr(
            "test.jpg", mock_model, 1.5, 0.8
        )
        
        # Vérifications
        assert len(results) == 2
        
        # Premier résultat
        assert results[0].text == "Hello World"
        assert results[0].timestamp == 1.5
        assert results[0].confidence == 0.95
        assert results[0].bounding_box == {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        
        # Deuxième résultat
        assert results[1].text == "Test"
        assert results[1].confidence == 0.85
        assert results[1].bounding_box == {"x1": 100, "y1": 120, "x2": 180, "y2": 150}
    
    def test_extract_with_paddleocr_low_confidence(self):
        """Test PaddleOCR avec confiance faible."""
        mock_model = MagicMock()
        
        # Résultat avec confiance faible
        mock_results = [[
            [
                [[100, 50], [200, 50], [200, 100], [100, 100]],
                ("Low confidence", 0.3)  # Confiance < seuil (0.5)
            ]
        ]]
        
        mock_model.ocr.return_value = mock_results
        
        results = self.manager._extract_with_paddleocr(
            "test.jpg", mock_model, 1.0, 0.5
        )
        
        # Devrait être filtré
        assert len(results) == 0
    
    def test_extract_with_easyocr_success(self):
        """Test d'extraction EasyOCR réussie."""
        mock_model = MagicMock()
        
        # Mock des résultats EasyOCR
        mock_results = [
            (
                [[100, 50], [200, 50], [200, 100], [100, 100]],  # bbox
                "Hello World",  # text
                0.92  # confidence
            ),
            (
                [[100, 120], [180, 120], [180, 150], [100, 150]],
                "Test",
                0.87
            )
        ]
        
        mock_model.readtext.return_value = mock_results
        
        # Test
        results = self.manager._extract_with_easyocr(
            "test.jpg", mock_model, 2.0, 0.8, ["en"]
        )
        
        # Vérifications
        assert len(results) == 2
        
        assert results[0].text == "Hello World"
        assert results[0].timestamp == 2.0
        assert results[0].confidence == 0.92
        
        assert results[1].text == "Test"
        assert results[1].confidence == 0.87
    
    def test_calculate_text_similarity(self):
        """Test de calcul de similarité textuelle."""
        # Textes identiques
        similarity = self.manager._calculate_text_similarity("hello world", "hello world")
        assert similarity == 1.0
        
        # Textes complètement différents
        similarity = self.manager._calculate_text_similarity("hello", "goodbye")
        assert similarity == 0.0
        
        # Textes partiellement similaires
        similarity = self.manager._calculate_text_similarity("hello world", "hello there")
        assert 0.0 < similarity < 1.0
        
        # Textes vides
        similarity = self.manager._calculate_text_similarity("", "")
        assert similarity == 1.0
        
        # Un texte vide
        similarity = self.manager._calculate_text_similarity("hello", "")
        assert similarity == 0.0
    
    def test_calculate_spatial_similarity(self):
        """Test de calcul de similarité spatiale."""
        # Boxes identiques
        boxes1 = [{"x1": 100, "y1": 50, "x2": 200, "y2": 100}]
        boxes2 = [{"x1": 100, "y1": 50, "x2": 200, "y2": 100}]
        
        similarity = self.manager._calculate_spatial_similarity(boxes1, boxes2)
        assert similarity == 1.0
        
        # Boxes sans intersection
        boxes1 = [{"x1": 100, "y1": 50, "x2": 200, "y2": 100}]
        boxes2 = [{"x1": 300, "y1": 50, "x2": 400, "y2": 100}]
        
        similarity = self.manager._calculate_spatial_similarity(boxes1, boxes2)
        assert similarity == 0.0
        
        # Listes vides
        similarity = self.manager._calculate_spatial_similarity([], [])
        assert similarity == 0.0
    
    def test_calculate_iou(self):
        """Test de calcul IoU."""
        # Boxes identiques
        box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        box2 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        
        iou = self.manager._calculate_iou(box1, box2)
        assert iou == 1.0
        
        # Boxes sans intersection
        box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        box2 = {"x1": 300, "y1": 50, "x2": 400, "y2": 100}
        
        iou = self.manager._calculate_iou(box1, box2)
        assert iou == 0.0
        
        # Intersection partielle
        box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        box2 = {"x1": 150, "y1": 75, "x2": 250, "y2": 125}
        
        iou = self.manager._calculate_iou(box1, box2)
        assert 0.0 < iou < 1.0
    
    def test_post_process_ocr_results(self):
        """Test de post-traitement des résultats OCR."""
        # Résultats avec timestamps proches
        ocr_results = [
            OCRResult(text="Hello", timestamp=1.0, confidence=0.9),
            OCRResult(text="World", timestamp=1.05, confidence=0.8),  # Très proche
            OCRResult(text="Test", timestamp=2.0, confidence=0.85)
        ]
        
        processed = self.manager._post_process_ocr_results(ocr_results)
        
        # Les deux premiers devraient être fusionnés
        assert len(processed) == 2
        assert processed[0].text == "Hello World"
        assert processed[0].timestamp == 1.0
        assert processed[1].text == "Test"
        assert processed[1].timestamp == 2.0
    
    def test_merge_ocr_group(self):
        """Test de fusion d'un groupe OCR."""
        # Groupe vide
        result = self.manager._merge_ocr_group([])
        assert result is None
        
        # Groupe avec un seul élément
        single_result = OCRResult(text="Single", timestamp=1.0, confidence=0.9)
        result = self.manager._merge_ocr_group([single_result])
        assert result == single_result
        
        # Groupe avec plusieurs éléments
        group = [
            OCRResult(
                text="Hello", 
                timestamp=1.0, 
                confidence=0.9,
                bounding_box={"x1": 100, "y1": 50, "x2": 150, "y2": 80}
            ),
            OCRResult(
                text="World", 
                timestamp=1.05, 
                confidence=0.8,
                bounding_box={"x1": 160, "y1": 50, "x2": 200, "y2": 80}
            )
        ]
        
        merged = self.manager._merge_ocr_group(group)
        
        assert merged.text == "Hello World"
        assert merged.timestamp == 1.0
        assert merged.confidence == 0.85  # Moyenne
        assert merged.bounding_box == {"x1": 100, "y1": 50, "x2": 200, "y2": 80}
    
    def test_get_ocr_statistics_empty(self):
        """Test de statistiques avec résultats vides."""
        stats = self.manager.get_ocr_statistics([])
        
        assert stats["total_segments"] == 0
        assert stats["total_characters"] == 0
        assert stats["average_confidence"] == 0.0
        assert stats["duration"] == 0.0
        assert stats["text_density"] == 0.0
    
    def test_get_ocr_statistics_with_data(self):
        """Test de statistiques avec données."""
        ocr_results = [
            OCRResult(text="Hello", timestamp=1.0, confidence=0.9),
            OCRResult(text="World", timestamp=2.0, confidence=0.8),
            OCRResult(text="Test", timestamp=3.0, confidence=0.7)
        ]
        
        stats = self.manager.get_ocr_statistics(ocr_results)
        
        assert stats["total_segments"] == 3
        assert stats["total_characters"] == 14  # "Hello" + "World" + "Test"
        assert abs(stats["average_confidence"] - 0.8) < 0.01
        assert stats["duration"] == 2.0  # 3.0 - 1.0
        assert abs(stats["text_density"] - 7.0) < 0.01  # 14 / 2.0
        
        # Vérifier la distribution de confiance
        distribution = stats["confidence_distribution"]
        assert distribution["high"] == 2  # 0.9 et 0.8
        assert distribution["medium"] == 1  # 0.7
    
    def test_calculate_confidence_distribution(self):
        """Test de calcul de distribution de confiance."""
        ocr_results = [
            OCRResult(text="Very Low", timestamp=1.0, confidence=0.2),
            OCRResult(text="Low", timestamp=2.0, confidence=0.4),
            OCRResult(text="Medium", timestamp=3.0, confidence=0.6),
            OCRResult(text="High", timestamp=4.0, confidence=0.8),
            OCRResult(text="Very High", timestamp=5.0, confidence=0.95)
        ]
        
        distribution = self.manager._calculate_confidence_distribution(ocr_results)
        
        assert distribution["very_low"] == 1
        assert distribution["low"] == 1
        assert distribution["medium"] == 1
        assert distribution["high"] == 1
        assert distribution["very_high"] == 1
    
    @patch.object(AIModelManager, 'extract_text_from_frames')
    def test_extract_text_from_video_segment(self, mock_extract_frames):
        """Test d'extraction depuis un segment vidéo."""
        # Mock des résultats
        expected_results = [
            OCRResult(text="Subtitle", timestamp=1.5, confidence=0.9)
        ]
        mock_extract_frames.return_value = expected_results
        
        # Mock du VideoProcessor
        with patch('ai_video_dubbing.processors.video_processor.VideoProcessor') as mock_vp_class:
            mock_vp = MagicMock()
            mock_vp_class.return_value = mock_vp
            
            mock_frames = [Frame(image_path="frame.jpg", timestamp=1.5)]
            mock_vp.extract_frames_from_interval.return_value = mock_frames
            
            # Test
            results = self.manager.extract_text_from_video_segment(
                "video.mp4", 1.0, 2.0, frame_interval=0.5
            )
            
            # Vérifications
            assert results == expected_results
            mock_vp.extract_frames_from_interval.assert_called_once_with(
                "video.mp4", 1.0, 2.0, 0.5
            )
            mock_extract_frames.assert_called_once_with(mock_frames)
    
    def test_unsupported_ocr_model(self):
        """Test avec modèle OCR non supporté."""
        frame = Frame(image_path="test.jpg", timestamp=1.0)
        mock_model = MagicMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            try:
                self.manager._extract_text_from_single_frame(
                    frame, mock_model, "unsupported_model"
                )
                assert False, "Devrait lever ProcessingError"
            except Exception:
                pass  # Attendu