#!/usr/bin/env python3
"""
Test simple du système de segmentation audio par locuteur.
"""

import numpy as np
import tempfile
import os
from pathlib import Path

from ai_video_dubbing.processors.speaker_segmentation import SpeakerSegmentationProcessor
from ai_video_dubbing.models.data_models import DialogueSegment, SpeakerSegments
from ai_video_dubbing.utils.temp_storage import TempStorage


def create_test_audio_file(duration: float, sample_rate: int = 16000) -> str:
    """Crée un fichier audio de test."""
    try:
        import soundfile as sf
        
        # Générer un signal de test
        num_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        # Signal sinusoïdal avec du bruit
        frequency = 440  # La note A4
        signal = 0.3 * np.sin(2 * np.pi * frequency * t)
        noise = 0.05 * np.random.randn(num_samples)
        audio_data = signal + noise
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        # Sauvegarder l'audio
        sf.write(temp_path, audio_data, sample_rate)
        
        return temp_path
        
    except ImportError:
        print("Warning: soundfile not available, skipping audio file creation")
        return None


def test_speaker_segmentation():
    """Test simple du système de segmentation."""
    
    print("🎵 Test du système de segmentation audio par locuteur")
    
    # Créer le processeur
    temp_storage = TempStorage()
    processor = SpeakerSegmentationProcessor(temp_storage)
    
    print(f"✓ Processeur initialisé")
    print(f"  - Durée minimale de segment: {processor.min_segment_duration}s")
    print(f"  - Durée maximale de silence: {processor.max_gap_duration}s")
    print(f"  - Durée de fade: {processor.fade_duration}s")
    
    # Créer des segments de test
    speaker_segments = SpeakerSegments(
        segments=[
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=1.0,
                end_time=3.0,
                original_text="Hello world",
                audio_path="",
                confidence_score=0.9
            ),
            DialogueSegment(
                speaker_id="SPEAKER_01",
                start_time=4.0,
                end_time=6.0,
                original_text="This is a test",
                audio_path="",
                confidence_score=0.8
            ),
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=7.0,
                end_time=9.0,
                original_text="Another segment",
                audio_path="",
                confidence_score=0.85
            )
        ],
        speaker_count=2,
        confidence_scores={"SPEAKER_00": 0.875, "SPEAKER_01": 0.8}
    )
    
    print(f"✓ Segments de test créés:")
    print(f"  - {len(speaker_segments.segments)} segments au total")
    print(f"  - {speaker_segments.speaker_count} locuteurs")
    
    # Créer des données audio de test
    audio_duration = 10.0
    sample_rate = 16000
    num_samples = int(audio_duration * sample_rate)
    
    # Générer un signal de test
    t = np.linspace(0, audio_duration, num_samples)
    frequency = 440
    signal = 0.3 * np.sin(2 * np.pi * frequency * t)
    noise = 0.05 * np.random.randn(num_samples)
    audio_data = signal + noise
    
    print(f"✓ Audio de test généré: {audio_duration}s à {sample_rate}Hz")
    
    # Test d'extraction des segments
    print("\n📊 Test d'extraction des segments...")
    
    extracted_segments = processor._extract_speaker_segments(
        audio_data, sample_rate, speaker_segments
    )
    
    print(f"✓ Segments extraits pour {len(extracted_segments)} locuteurs:")
    for speaker_id, segments in extracted_segments.items():
        total_duration = sum(seg.end_time - seg.start_time for seg in segments)
        print(f"  - {speaker_id}: {len(segments)} segments, {total_duration:.1f}s total")
    
    # Test de validation de qualité
    print("\n🔍 Test de validation de qualité...")
    
    quality_metrics = processor._validate_segment_quality(extracted_segments)
    
    print(f"✓ Métriques de qualité calculées:")
    print(f"  - Total locuteurs: {quality_metrics['total_speakers']}")
    print(f"  - Total segments: {quality_metrics['total_segments']}")
    
    for speaker_id, stats in quality_metrics['speaker_statistics'].items():
        print(f"  - {speaker_id}:")
        print(f"    * Segments: {stats['segment_count']}")
        print(f"    * Durée totale: {stats['total_duration']:.1f}s")
        print(f"    * Confiance moyenne: {stats['average_confidence']:.3f}")
        print(f"    * Niveau RMS moyen: {stats['average_rms']:.4f}")
    
    if quality_metrics['quality_warnings']:
        print(f"  ⚠️ Avertissements de qualité:")
        for warning in quality_metrics['quality_warnings']:
            print(f"    - {warning}")
    else:
        print(f"  ✓ Aucun avertissement de qualité")
    
    # Test de concaténation
    print("\n🔗 Test de concaténation des segments...")
    
    for speaker_id, segments in extracted_segments.items():
        if segments:
            concatenated = processor._concatenate_segments_with_gaps(segments, sample_rate)
            duration = len(concatenated) / sample_rate
            print(f"  - {speaker_id}: {duration:.2f}s concaténés")
    
    # Test de normalisation
    print("\n🎚️ Test de normalisation audio...")
    
    test_signal = np.random.randn(1000) * 0.1  # Signal faible
    original_rms = np.sqrt(np.mean(test_signal ** 2))
    
    normalized = processor._normalize_audio(test_signal)
    normalized_rms = np.sqrt(np.mean(normalized ** 2))
    
    print(f"  - RMS original: {original_rms:.4f}")
    print(f"  - RMS normalisé: {normalized_rms:.4f}")
    print(f"  - Gain appliqué: {normalized_rms/original_rms:.2f}x")
    
    # Test de fade
    print("\n🎵 Test d'application du fade...")
    
    test_signal = np.ones(8000)  # 0.5s à 16kHz
    faded = processor._apply_fade(test_signal, sample_rate)
    
    fade_samples = int(processor.fade_duration * sample_rate)
    print(f"  - Échantillons de fade: {fade_samples}")
    print(f"  - Début du signal: {faded[0]:.3f} -> {faded[fade_samples]:.3f}")
    print(f"  - Fin du signal: {faded[-fade_samples]:.3f} -> {faded[-1]:.3f}")
    
    # Test de mapping des segments
    print("\n🗺️ Test de mapping des segments...")
    
    segment_mapping = processor._create_segment_mapping(speaker_segments)
    
    for speaker_id, segments in segment_mapping.items():
        print(f"  - {speaker_id}: {len(segments)} segments")
        for i, segment in enumerate(segments):
            print(f"    * Segment {i}: {segment.start_time:.1f}s - {segment.end_time:.1f}s")
    
    # Test de statistiques de durée
    print("\n📈 Test de statistiques de durée...")
    
    duration_stats = processor._calculate_duration_statistics(extracted_segments)
    
    for speaker_id, duration in duration_stats.items():
        print(f"  - {speaker_id}: {duration:.1f}s total")
    
    # Test d'extraction d'échantillons
    print("\n🎤 Test d'extraction d'échantillons...")
    
    # Mock de la sauvegarde pour éviter les erreurs de dépendances
    original_save = processor._save_audio
    saved_files = []
    
    def mock_save_audio(audio_data, sample_rate, output_path, format):
        saved_files.append(output_path)
        print(f"    * Échantillon sauvegardé: {Path(output_path).name}")
    
    processor._save_audio = mock_save_audio
    
    try:
        samples = processor.extract_speaker_samples(
            extracted_segments, 
            sample_duration=5.0, 
            min_quality_threshold=0.7
        )
        
        print(f"  ✓ Échantillons extraits:")
        for speaker_id, sample_files in samples.items():
            print(f"    - {speaker_id}: {len(sample_files)} échantillons")
        
    finally:
        processor._save_audio = original_save
    
    print(f"\n🎉 Tous les tests de segmentation sont réussis!")
    print(f"📁 Fichiers temporaires créés: {len(saved_files)}")
    
    # Nettoyage
    temp_storage.cleanup_all()
    print(f"🧹 Nettoyage terminé")


if __name__ == "__main__":
    test_speaker_segmentation()