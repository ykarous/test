#!/usr/bin/env python3
"""
Test basique de l'extraction OCR.
"""

import numpy as np
from ai_video_dubbing.processors.ai_model_manager import AIModelManager
from ai_video_dubbing.models.data_models import Frame, OCRResult


def test_basic_ocr():
    """Test basique OCR."""
    print("=== Test Basique OCR ===")
    
    # Créer un gestionnaire
    manager = AIModelManager()
    
    # Test 1: Liste vide
    result = manager.extract_text_from_frames([])
    print(f"1. Liste vide: {len(result)} résultats")
    
    # Test 2: Similarité textuelle
    sim = manager._calculate_text_similarity("hello", "hello")
    print(f"2. Similarité identique: {sim}")
    
    sim = manager._calculate_text_similarity("hello", "world")
    print(f"3. Similarité différente: {sim}")
    
    # Test 3: IoU
    box1 = {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    box2 = {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    iou = manager._calculate_iou(box1, box2)
    print(f"4. IoU identique: {iou}")
    
    # Test 4: Fusion groupe vide
    result = manager._merge_ocr_group([])
    print(f"5. Fusion groupe vide: {result}")
    
    # Test 5: Statistiques vides
    stats = manager.get_ocr_statistics([])
    print(f"6. Stats vides: {stats['total_segments']} segments")
    
    print("✅ Tests basiques terminés!")


if __name__ == "__main__":
    test_basic_ocr()