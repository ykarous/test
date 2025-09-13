#!/usr/bin/env python3
"""
Test simple de la séparation de source audio.
"""

import tempfile
import numpy as np
from pathlib import Path

# Imports conditionnels
try:
    import soundfile as sf
    _SF_AVAILABLE = True
except ImportError:
    _SF_AVAILABLE = False
    sf = None

from ai_video_dubbing.processors.audio_processor import AudioProcessor
from ai_video_dubbing.models.data_models import ValidationError


def create_test_audio(file_path: str, duration: float = 2.0, sample_rate: int = 44100):
    """Crée un fichier audio de test."""
    if not _SF_AVAILABLE:
        print("⚠️  soundfile non disponible, création d'un fichier factice")
        Path(file_path).write_bytes(b"fake audio content")
        return
    
    # Créer un signal audio simple (sinusoïde + bruit)
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Signal principal (voix simulée - fréquence moyenne)
    voice_signal = 0.3 * np.sin(2 * np.pi * 440 * t)  # La 440Hz
    
    # Signal de fond (musique simulée - fréquences plus basses)
    music_signal = 0.2 * np.sin(2 * np.pi * 220 * t)  # La 220Hz
    
    # Bruit léger
    noise = 0.05 * np.random.randn(len(t))
    
    # Combiner les signaux
    combined_signal = voice_signal + music_signal + noise
    
    # Normaliser
    combined_signal = combined_signal / np.max(np.abs(combined_signal)) * 0.8
    
    # Sauvegarder
    sf.write(file_path, combined_signal, sample_rate)
    print(f"✅ Fichier audio de test créé: {file_path}")


def test_source_separation():
    """Test simple de la séparation de source."""
    print("=== Test de Séparation de Source Audio ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Répertoire temporaire: {temp_dir}")
        
        # Créer un processeur audio
        processor = AudioProcessor()
        
        # Test 1: Séparation désactivée
        print("\n1. Test séparation désactivée:")
        test_audio_path = Path(temp_dir) / "test_audio.wav"
        create_test_audio(str(test_audio_path))
        
        try:
            result = processor.separate_sources(str(test_audio_path), enable_separation=False)
            print(f"   ✅ Séparation désactivée réussie")
            print(f"   - Chemin voix: {result.vocals_path}")
            print(f"   - Chemin musique: {result.music_path}")
            print(f"   - Qualité: {result.separation_quality:.2f}")
            print(f"   - Temps de traitement: {result.processing_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 2: Séparation activée (avec fallback)
        print("\n2. Test séparation activée (fallback fréquentiel):")
        try:
            result = processor.separate_sources(str(test_audio_path), enable_separation=True)
            print(f"   ✅ Séparation activée réussie")
            print(f"   - Chemin voix: {result.vocals_path}")
            print(f"   - Chemin musique: {result.music_path}")
            print(f"   - Chemin effets: {result.effects_path}")
            print(f"   - Qualité: {result.separation_quality:.2f}")
            print(f"   - Temps de traitement: {result.processing_time:.2f}s")
            
            # Vérifier si les fichiers ont été créés
            if result.vocals_path and Path(result.vocals_path).exists():
                print(f"   ✅ Fichier voix créé: {Path(result.vocals_path).stat().st_size} octets")
            
            if result.music_path and Path(result.music_path).exists():
                print(f"   ✅ Fichier musique créé: {Path(result.music_path).stat().st_size} octets")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 3: Fichier inexistant
        print("\n3. Test fichier inexistant:")
        try:
            processor.separate_sources("/fichier/inexistant.wav")
            print("   ❌ Erreur: devrait lever une exception")
        except ValidationError as e:
            print(f"   ✅ Exception attendue: {e}")
        except Exception as e:
            print(f"   ❌ Exception inattendue: {e}")
        
        # Test 4: Informations sur les dépendances
        print("\n4. Informations sur les dépendances:")
        
        # Vérifier Demucs
        try:
            import demucs.api
            print("   ✅ Demucs API disponible")
        except ImportError:
            print("   ⚠️  Demucs API non disponible")
        
        # Vérifier librosa
        try:
            import librosa
            print("   ✅ Librosa disponible")
        except ImportError:
            print("   ⚠️  Librosa non disponible")
        
        # Vérifier soundfile
        if _SF_AVAILABLE:
            print("   ✅ SoundFile disponible")
        else:
            print("   ⚠️  SoundFile non disponible")
        
        # Test 5: Évaluation de qualité
        print("\n5. Test évaluation de qualité:")
        if _SF_AVAILABLE and Path(test_audio_path).exists():
            try:
                # Créer un fichier "voix" factice
                vocals_path = Path(temp_dir) / "vocals_test.wav"
                
                # Charger l'audio original et créer une version "voix"
                original_audio, sr = sf.read(str(test_audio_path))
                # Simuler une extraction de voix (filtre simple)
                vocals_audio = original_audio * 0.7  # Réduction simple
                sf.write(str(vocals_path), vocals_audio, sr)
                
                quality = processor._evaluate_separation_quality(
                    str(test_audio_path), 
                    str(vocals_path)
                )
                print(f"   ✅ Score de qualité calculé: {quality:.3f}")
                
            except Exception as e:
                print(f"   ❌ Erreur évaluation qualité: {e}")
        
        print("\n✅ Tests de séparation de source terminés!")


if __name__ == "__main__":
    test_source_separation()