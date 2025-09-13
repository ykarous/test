#!/usr/bin/env python3
"""
Test simple du système de synchronisation temporelle.
"""

from ai_video_dubbing.processors.sync_processor import SyncProcessor
from ai_video_dubbing.models.data_models import (
    TranscriptionResult, TranscriptionSegment, OCRResult
)

def test_sync_processor():
    """Test simple du processeur de synchronisation."""
    
    # Créer le processeur
    processor = SyncProcessor()
    
    # Créer des données de test
    asr_segments = [
        TranscriptionSegment(
            text="Hello world",
            start=1.0,
            end=3.0,
            confidence=0.9,
            word_timestamps=[]
        ),
        TranscriptionSegment(
            text="This is a test",
            start=4.0,
            end=6.0,
            confidence=0.8,
            word_timestamps=[]
        )
    ]
    
    asr_result = TranscriptionResult(
        text="Hello world This is a test",
        segments=asr_segments,
        language="en",
        confidence=0.85,
        processing_time=1.0,
        model_name="whisper-base",
        word_count=6
    )
    
    ocr_results = [
        OCRResult(
            text="Hello world",
            timestamp=1.2,
            confidence=0.95,
            bounding_box={"x1": 100, "y1": 50, "x2": 200, "y2": 100}
        ),
        OCRResult(
            text="This is a test",
            timestamp=4.1,
            confidence=0.88,
            bounding_box={"x1": 100, "y1": 120, "x2": 250, "y2": 150}
        )
    ]
    
    # Test de synchronisation
    print("Test de synchronisation par plus proche voisin...")
    result = processor.synchronize_asr_ocr(
        asr_result, 
        ocr_results, 
        method="nearest_neighbor"
    )
    
    print(f"Méthode d'alignement: {result.alignment_method}")
    print(f"Score de confiance: {result.confidence_score:.3f}")
    print(f"Nombre de segments synchronisés: {len(result.synchronized_segments)}")
    print(f"Temps de traitement: {result.processing_time:.3f}s")
    
    # Vérifier les résultats
    assert result.alignment_method == "nearest_neighbor"
    assert len(result.synchronized_segments) == len(asr_result.segments)
    assert result.confidence_score > 0.0
    
    # Vérifier que les timestamps OCR sont utilisés (plus précis)
    assert result.synchronized_segments[0].start_time == 1.2  # OCR timestamp
    assert result.synchronized_segments[1].start_time == 4.1  # OCR timestamp
    
    print("✓ Test de synchronisation réussi!")
    
    # Test sans OCR
    print("\nTest sans résultats OCR...")
    result_no_ocr = processor.synchronize_asr_ocr(asr_result, [])
    
    assert result_no_ocr.alignment_method == "asr_only"
    assert len(result_no_ocr.synchronized_segments) == len(asr_result.segments)
    assert result_no_ocr.confidence_score == asr_result.confidence
    
    print("✓ Test sans OCR réussi!")
    
    # Test de calcul de similarité textuelle
    print("\nTest de similarité textuelle...")
    
    # Textes identiques
    similarity = processor._calculate_text_similarity("hello world", "hello world")
    assert similarity == 1.0
    print(f"Similarité textes identiques: {similarity}")
    
    # Textes différents
    similarity = processor._calculate_text_similarity("hello", "goodbye")
    assert similarity == 0.0
    print(f"Similarité textes différents: {similarity}")
    
    # Textes partiellement similaires
    similarity = processor._calculate_text_similarity("hello world", "hello there")
    assert 0.0 < similarity < 1.0
    print(f"Similarité textes partiels: {similarity:.3f}")
    
    print("✓ Test de similarité réussi!")
    
    # Test de conversion de temps
    print("\nTest de conversion de temps...")
    
    srt_time = processor._seconds_to_srt_time(3661.123)
    assert srt_time == "01:01:01,123"
    print(f"Conversion SRT: 3661.123s -> {srt_time}")
    
    vtt_time = processor._seconds_to_vtt_time(3661.123)
    assert vtt_time == "01:01:01.123"
    print(f"Conversion VTT: 3661.123s -> {vtt_time}")
    
    print("✓ Test de conversion réussi!")
    
    print("\n🎉 Tous les tests de synchronisation sont réussis!")

if __name__ == "__main__":
    test_sync_processor()