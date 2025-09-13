#!/usr/bin/env python3
"""
Test simple de l'extraction OCR des sous-titres.
"""

import tempfile
import numpy as np
from pathlib import Path

from ai_video_dubbing.processors.ai_model_manager import AIModelManager
from ai_video_dubbing.models.data_models import ModelType, Frame, OCRResult, ProcessingError


def create_test_frame(timestamp: float = 1.0) -> Frame:
    """Crée une frame de test avec des données d'image factices."""
    # Créer une image factice (100x50 pixels, 3 canaux RGB)
    fake_image = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
    
    return Frame(
        timestamp=timestamp,
        image_data=fake_image,
        width=100,
        height=50
    )


def test_ocr_extraction():
    """Test simple de l'extraction OCR."""
    print("=== Test d'Extraction OCR des Sous-titres ===")
    
    # Créer un gestionnaire de modèles IA
    manager = AIModelManager()
    
    # Test 1: Extraction avec liste vide
    print("\n1. Test extraction avec liste vide:")
    result = manager.extract_text_from_frames([])
    print(f"   ✅ Résultat pour liste vide: {len(result)} éléments")
    
    # Test 2: Création de frames de test
    print("\n2. Test création de frames:")
    frames = [
        create_test_frame(1.0),
        create_test_frame(2.0),
        create_test_frame(3.0)
    ]
    print(f"   ✅ Créé {len(frames)} frames de test")
    for i, frame in enumerate(frames):
        print(f"     Frame {i+1}: {frame.timestamp}s, {frame.width}x{frame.height}, shape: {frame.image_data.shape}")
    
    # Test 3: Tentative d'extraction OCR (échouera sans les dépendances)
    print("\n3. Test extraction OCR (simulation):")
    try:
        results = manager.extract_text_from_frames(frames, model_name="paddleocr")
        print(f"   ✅ Extraction réussie: {len(results)} résultats")
        for result in results:
            print(f"     - '{result.text}' à {result.timestamp}s (confiance: {result.confidence:.2f})")
    except ProcessingError as e:
        print(f"   ⚠️  Extraction échouée (attendu sans dépendances): {str(e)[:60]}...")
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    # Test 4: Méthodes de similarité
    print("\n4. Test méthodes de similarité:")
    
    # Similarité textuelle
    similarity = manager._calculate_text_similarity("hello world", "hello world")
    print(f"   Similarité textuelle identique: {similarity:.2f}")
    
    similarity = manager._calculate_text_similarity("hello world", "hello there")
    print(f"   Similarité textuelle partielle: {similarity:.2f}")
    
    similarity = manager._calculate_text_similarity("hello", "goodbye")
    print(f"   Similarité textuelle différente: {similarity:.2f}")
    
    # Test 5: Calcul IoU
    print("\n5. Test calcul IoU (Intersection over Union):")
    
    # Boxes identiques
    box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
    box2 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
    iou = manager._calculate_iou(box1, box2)
    print(f"   IoU boxes identiques: {iou:.2f}")
    
    # Boxes sans intersection
    box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
    box2 = {"x1": 300, "y1": 50, "x2": 400, "y2": 100}
    iou = manager._calculate_iou(box1, box2)
    print(f"   IoU boxes séparées: {iou:.2f}")
    
    # Intersection partielle
    box1 = {"x1": 100, "y1": 50, "x2": 200, "y2": 100}
    box2 = {"x1": 150, "y1": 75, "x2": 250, "y2": 125}
    iou = manager._calculate_iou(box1, box2)
    print(f"   IoU intersection partielle: {iou:.2f}")
    
    # Test 6: Post-traitement des résultats
    print("\n6. Test post-traitement:")
    
    # Créer des résultats OCR factices
    ocr_results = [
        OCRResult(text="Hello", timestamp=1.0, confidence=0.9),
        OCRResult(text="World", timestamp=1.05, confidence=0.8),  # Très proche temporellement
        OCRResult(text="Test", timestamp=2.0, confidence=0.85)
    ]
    
    try:
        processed = manager._post_process_ocr_results(ocr_results)
        print(f"   ✅ Post-traitement: {len(ocr_results)} → {len(processed)} résultats")
        for result in processed:
            print(f"     - '{result.text}' à {result.timestamp}s")
    except Exception as e:
        print(f"   ❌ Erreur post-traitement: {e}")
    
    # Test 7: Fusion de groupes OCR
    print("\n7. Test fusion de groupes:")
    
    # Groupe vide
    result = manager._merge_ocr_group([])
    print(f"   Fusion groupe vide: {result}")
    
    # Groupe avec un élément
    single_result = OCRResult(text="Single", timestamp=1.0, confidence=0.9)
    result = manager._merge_ocr_group([single_result])
    print(f"   Fusion groupe unique: '{result.text}' (confiance: {result.confidence:.2f})")
    
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
    
    try:
        merged = manager._merge_ocr_group(group)
        print(f"   Fusion groupe multiple: '{merged.text}' (confiance: {merged.confidence:.2f})")
        print(f"   Bounding box fusionnée: {merged.bounding_box}")
    except Exception as e:
        print(f"   ❌ Erreur fusion: {e}")
    
    # Test 8: Statistiques OCR
    print("\n8. Test statistiques OCR:")
    
    # Statistiques vides
    stats = manager.get_ocr_statistics([])
    print(f"   Statistiques vides: {stats['total_segments']} segments")
    
    # Statistiques avec données
    test_results = [
        OCRResult(text="Hello", timestamp=1.0, confidence=0.9),
        OCRResult(text="World", timestamp=2.0, confidence=0.8),
        OCRResult(text="Test", timestamp=3.0, confidence=0.7)
    ]
    
    stats = manager.get_ocr_statistics(test_results)
    print(f"   Statistiques avec données:")
    print(f"     - Segments: {stats['total_segments']}")
    print(f"     - Caractères: {stats['total_characters']}")
    print(f"     - Confiance moyenne: {stats['average_confidence']:.2f}")
    print(f"     - Durée: {stats['duration']:.1f}s")
    print(f"     - Densité de texte: {stats['text_density']:.1f} car/s")
    
    # Test 9: Vérification des dépendances OCR
    print("\n9. Dépendances OCR disponibles:")
    
    # Vérifier PaddleOCR
    try:
        import paddleocr
        print("   ✅ PaddleOCR disponible")
    except ImportError:
        print("   ⚠️  PaddleOCR non disponible")
    
    # Vérifier EasyOCR
    try:
        import easyocr
        print("   ✅ EasyOCR disponible")
    except ImportError:
        print("   ⚠️  EasyOCR non disponible")
    
    # Vérifier OpenCV (pour traitement d'images)
    try:
        import cv2
        print("   ✅ OpenCV disponible")
    except ImportError:
        print("   ⚠️  OpenCV non disponible")
    
    print("\n✅ Tests d'extraction OCR terminés!")


if __name__ == "__main__":
    test_ocr_extraction()