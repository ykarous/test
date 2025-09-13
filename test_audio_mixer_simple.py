#!/usr/bin/env python3
"""
Test simple du système de mixage audio final.
"""

import numpy as np
from pathlib import Path

from ai_video_dubbing.processors.audio_mixer import AudioMixer, MixingConfig
from ai_video_dubbing.models.data_models import DialogueSegment
from ai_video_dubbing.utils.temp_storage import TempStorage


def create_test_audio_files(temp_storage: TempStorage) -> dict:
    """Crée des fichiers audio de test pour le mixage."""
    audio_files = {}
    
    # Définir les types d'audio à créer
    audio_specs = {
        "dialogue_speaker1": {
            "duration": 3.0,
            "frequency": 150,  # Voix masculine
            "type": "dialogue",
            "envelope": "speech"
        },
        "dialogue_speaker2": {
            "duration": 2.5,
            "frequency": 220,  # Voix féminine
            "type": "dialogue", 
            "envelope": "speech"
        },
        "background_music": {
            "duration": 15.0,
            "frequency": 440,  # Musique de fond
            "type": "music",
            "envelope": "constant"
        },
        "sound_effect": {
            "duration": 1.0,
            "frequency": 880,  # Effet sonore
            "type": "sfx",
            "envelope": "impact"
        },
        "ambient_sound": {
            "duration": 12.0,
            "frequency": 100,  # Son ambiant
            "type": "ambient",
            "envelope": "ambient"
        }
    }
    
    sample_rate = 48000
    
    for name, spec in audio_specs.items():
        duration = spec["duration"]
        frequency = spec["frequency"]
        num_samples = int(duration * sample_rate)
        
        # Générer le signal de base
        t = np.linspace(0, duration, num_samples)
        
        if spec["type"] == "dialogue":
            # Signal vocal avec harmoniques
            signal = (0.6 * np.sin(2 * np.pi * frequency * t) +
                     0.3 * np.sin(2 * np.pi * 2 * frequency * t) +
                     0.2 * np.sin(2 * np.pi * 3 * frequency * t))
            
            # Enveloppe de parole (modulation d'amplitude)
            speech_envelope = 0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
            signal *= speech_envelope
            
        elif spec["type"] == "music":
            # Signal musical complexe
            signal = (0.4 * np.sin(2 * np.pi * frequency * t) +
                     0.25 * np.sin(2 * np.pi * 1.5 * frequency * t) +
                     0.2 * np.sin(2 * np.pi * 2 * frequency * t) +
                     0.15 * np.sin(2 * np.pi * 3 * frequency * t))
            
            # Enveloppe musicale douce
            music_envelope = 0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * t)
            signal *= music_envelope
            
        elif spec["type"] == "sfx":
            # Effet sonore percutant
            signal = 0.8 * np.sin(2 * np.pi * frequency * t)
            
            # Enveloppe d'impact (décroissance rapide)
            impact_envelope = np.exp(-t * 5)
            signal *= impact_envelope
            
        else:  # ambient
            # Son ambiant subtil
            signal = (0.2 * np.sin(2 * np.pi * frequency * t) +
                     0.15 * np.sin(2 * np.pi * 1.3 * frequency * t) +
                     0.1 * np.sin(2 * np.pi * 0.7 * frequency * t))
            
            # Enveloppe ambiante stable
            ambient_envelope = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)
            signal *= ambient_envelope
        
        # Ajouter du bruit réaliste
        noise_level = 0.01 if spec["type"] == "dialogue" else 0.005
        noise = noise_level * np.random.randn(num_samples)
        audio_data = signal + noise
        
        # Normaliser
        audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
        
        # Sauvegarder
        audio_path = temp_storage.get_temp_path(f"{name}.wav")
        
        try:
            import soundfile as sf
            sf.write(audio_path, audio_data, sample_rate)
            print(f"    * Créé: {name}.wav ({duration:.1f}s, {frequency}Hz)")
        except ImportError:
            # Créer un fichier avec des métadonnées pour les tests
            with open(audio_path, 'w') as f:
                f.write(f"Mock {spec['type']} audio: {duration}s, {frequency}Hz, {len(audio_data)} samples")
            print(f"    * Créé (mock): {name}.wav")
        
        audio_files[name] = {
            "path": audio_path,
            "duration": duration,
            "type": spec["type"]
        }
    
    return audio_files


def test_audio_mixer():
    """Test simple du système de mixage audio."""
    
    print("🎛️ Test du système de mixage audio final")
    
    # Créer le mixeur
    temp_storage = TempStorage()
    mixer = AudioMixer(temp_storage)
    
    print(f"✓ Mixeur initialisé")
    print(f"  - Taux d'échantillonnage cible: {mixer.default_config.target_sample_rate}Hz")
    print(f"  - Canaux cibles: {mixer.default_config.target_channels}")
    print(f"  - Format de sortie: {mixer.default_config.output_format}")
    print(f"  - LUFS cible: {mixer.default_config.target_lufs}")
    print(f"  - Ducking automatique: {mixer.default_config.auto_ducking}")
    
    # Créer des fichiers audio de test
    print("\n🎵 Création des fichiers audio de test...")
    
    audio_files = create_test_audio_files(temp_storage)
    print(f"  ✓ {len(audio_files)} fichiers audio créés")
    
    # Test de création de pistes audio
    print("\n🎚️ Test de création de pistes audio...")
    
    tracks = []
    
    # Piste de dialogue 1
    dialogue1_track = mixer.create_audio_track(
        track_id="dialogue_speaker1",
        audio_path=audio_files["dialogue_speaker1"]["path"],
        track_type="dialogue",
        start_time=1.0,
        end_time=4.0,
        volume_level=1.0,
        fade_in=0.05,
        fade_out=0.05,
        pan=-0.2,  # Légèrement à gauche
        priority=10
    )
    tracks.append(dialogue1_track)
    
    # Piste de dialogue 2
    dialogue2_track = mixer.create_audio_track(
        track_id="dialogue_speaker2", 
        audio_path=audio_files["dialogue_speaker2"]["path"],
        track_type="dialogue",
        start_time=5.0,
        end_time=7.5,
        volume_level=1.0,
        fade_in=0.05,
        fade_out=0.05,
        pan=0.2,  # Légèrement à droite
        priority=10
    )
    tracks.append(dialogue2_track)
    
    # Piste de musique de fond
    music_track = mixer.create_audio_track(
        track_id="background_music",
        audio_path=audio_files["background_music"]["path"],
        track_type="music",
        start_time=0.0,
        end_time=10.0,
        volume_level=0.3,  # Volume réduit pour la musique de fond
        fade_in=1.0,
        fade_out=1.0,
        pan=0.0,  # Centré
        priority=2
    )
    tracks.append(music_track)
    
    # Piste d'effet sonore
    sfx_track = mixer.create_audio_track(
        track_id="sound_effect",
        audio_path=audio_files["sound_effect"]["path"],
        track_type="sfx",
        start_time=3.5,
        end_time=4.5,
        volume_level=0.7,
        fade_in=0.01,
        fade_out=0.1,
        pan=0.8,  # À droite
        priority=8
    )
    tracks.append(sfx_track)
    
    # Piste ambiante
    ambient_track = mixer.create_audio_track(
        track_id="ambient_sound",
        audio_path=audio_files["ambient_sound"]["path"],
        track_type="ambient",
        start_time=0.0,
        end_time=10.0,
        volume_level=0.15,  # Très discret
        fade_in=2.0,
        fade_out=2.0,
        pan=0.0,
        priority=1
    )
    tracks.append(ambient_track)
    
    print(f"  ✓ {len(tracks)} pistes créées:")
    for track in tracks:
        print(f"    - {track.track_id} ({track.track_type}): {track.start_time:.1f}s-{track.end_time:.1f}s, vol={track.volume_level:.2f}, pan={track.pan:+.1f}")
    
    # Test de calcul des gains de panning
    print("\n🔊 Test de calcul des gains de panning...")
    
    pan_tests = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for pan in pan_tests:
        left_gain, right_gain = mixer._calculate_pan_gains(pan)
        print(f"  - Pan {pan:+.1f}: L={left_gain:.3f}, R={right_gain:.3f}")
    
    # Test d'application des fades
    print("\n🎚️ Test d'application des fades...")
    
    # Créer un signal de test
    test_duration = 2.0
    test_sr = 48000
    test_samples = int(test_duration * test_sr)
    test_signal = np.ones(test_samples)
    
    # Test fade in
    faded_in = mixer._apply_fade_in(test_signal, 0.5, test_sr)
    print(f"  ✓ Fade in: début={faded_in[0]:.3f}, milieu={faded_in[len(faded_in)//2]:.3f}, fin={faded_in[-1]:.3f}")
    
    # Test fade out
    faded_out = mixer._apply_fade_out(test_signal, 0.5, test_sr)
    print(f"  ✓ Fade out: début={faded_out[0]:.3f}, milieu={faded_out[len(faded_out)//2]:.3f}, fin={faded_out[-1]:.3f}")
    
    # Test de mixage simple
    print("\n🎛️ Test de mixage simple...")
    
    try:
        result = mixer.mix_audio_tracks(tracks)
        
        print(f"  ✓ Mixage réussi:")
        print(f"    - Fichier de sortie: {Path(result.mixed_audio_path).name}")
        print(f"    - Durée totale: {result.total_duration:.2f}s")
        print(f"    - Nombre de pistes: {result.track_count}")
        print(f"    - Niveau de crête: {result.peak_level:.1f}dB")
        print(f"    - Niveau RMS: {result.rms_level:.1f}dB")
        print(f"    - Niveau LUFS: {result.lufs_level:.1f}")
        print(f"    - Temps de traitement: {result.processing_time:.3f}s")
        
        # Statistiques par piste
        print(f"  📊 Statistiques par piste:")
        for track_id, stats in result.mixing_statistics.items():
            print(f"    - {track_id} ({stats['type']}): {stats['duration']:.2f}s, crête={stats['peak_level']:.3f}, RMS={stats['rms_level']:.3f}")
        
        # Métriques de qualité
        print(f"  🔍 Métriques de qualité:")
        for metric, value in result.quality_metrics.items():
            if isinstance(value, float):
                print(f"    - {metric}: {value:.3f}")
            else:
                print(f"    - {metric}: {value}")
    
    except Exception as e:
        print(f"  ✗ Erreur de mixage: {e}")
    
    # Test de configuration personnalisée
    print("\n⚙️ Test de configuration personnalisée...")
    
    custom_config = MixingConfig(
        target_sample_rate=44100,
        target_channels=1,  # Mono
        output_format="wav",
        output_bitrate=192,
        normalize_output=True,
        target_lufs=-16.0,  # Plus fort que le broadcast
        limiter_threshold=-0.5,
        dialogue_level=1.2,  # Dialogues plus forts
        music_level=0.2,     # Musique plus discrète
        sfx_level=0.9,       # Effets sonores proéminents
        crossfade_duration=0.2,
        auto_ducking=True,
        ducking_amount=8.0,  # Ducking plus agressif
        ducking_attack=0.03,
        ducking_release=0.8
    )
    
    print(f"  ✓ Configuration personnalisée:")
    print(f"    - Taux d'échantillonnage: {custom_config.target_sample_rate}Hz")
    print(f"    - Canaux: {custom_config.target_channels}")
    print(f"    - LUFS cible: {custom_config.target_lufs}")
    print(f"    - Niveau dialogue: {custom_config.dialogue_level}")
    print(f"    - Niveau musique: {custom_config.music_level}")
    print(f"    - Ducking: {custom_config.ducking_amount}dB")
    
    try:
        custom_result = mixer.mix_audio_tracks(tracks, config=custom_config)
        
        print(f"  ✓ Mixage personnalisé réussi:")
        print(f"    - Durée: {custom_result.total_duration:.2f}s")
        print(f"    - Crête: {custom_result.peak_level:.1f}dB")
        print(f"    - LUFS: {custom_result.lufs_level:.1f}")
        print(f"    - Temps: {custom_result.processing_time:.3f}s")
    
    except Exception as e:
        print(f"  ✗ Erreur de mixage personnalisé: {e}")
    
    # Test de crossfade
    print("\n🔄 Test de transition crossfade...")
    
    # Créer deux pistes musicales pour le crossfade
    music1_track = mixer.create_audio_track(
        track_id="music1",
        audio_path=audio_files["background_music"]["path"],
        track_type="music",
        start_time=0.0,
        end_time=5.0,
        volume_level=0.5
    )
    
    music2_track = mixer.create_audio_track(
        track_id="music2",
        audio_path=audio_files["ambient_sound"]["path"],
        track_type="music",
        start_time=4.0,
        end_time=9.0,
        volume_level=0.5
    )
    
    # Créer le crossfade
    crossfaded_track1, crossfaded_track2 = mixer.create_crossfade_transition(
        music1_track, music2_track, 1.5
    )
    
    print(f"  ✓ Crossfade créé:")
    print(f"    - Piste 1: fade_out={crossfaded_track1.fade_out:.1f}s")
    print(f"    - Piste 2: fade_in={crossfaded_track2.fade_in:.1f}s, début={crossfaded_track2.start_time:.1f}s")
    
    # Test du cache audio
    print("\n💾 Test du cache audio...")
    
    # Charger quelques fichiers
    for name, info in audio_files.items():
        mixer._load_audio_cached(info["path"])
    
    cache_stats = mixer.get_mixing_statistics()
    print(f"  ✓ Cache audio:")
    print(f"    - Fichiers en cache: {cache_stats['cache_size']}")
    print(f"    - Taille max: {cache_stats['max_cache_size']}")
    print(f"    - Fichiers: {[Path(f).name for f in cache_stats['cached_files']]}")
    
    # Nettoyer le cache
    mixer.clear_audio_cache()
    cache_stats_after = mixer.get_mixing_statistics()
    print(f"    - Après nettoyage: {cache_stats_after['cache_size']} fichiers")
    
    # Test de limitation et normalisation
    print("\n🎚️ Test de limitation et normalisation...")
    
    # Créer un signal avec des crêtes élevées
    loud_signal = np.array([0.5, 1.8, -1.5, 0.3, 2.2, -0.8])
    
    # Test du limiteur
    limited = mixer._apply_limiter(loud_signal, -3.0)
    print(f"  ✓ Limiteur:")
    print(f"    - Signal original: max={np.max(np.abs(loud_signal)):.2f}")
    print(f"    - Signal limité: max={np.max(np.abs(limited)):.2f}")
    
    # Test de normalisation RMS
    test_audio = np.random.randn(1000) * 0.1
    normalized = mixer._normalize_rms_fallback(test_audio, -20.0)
    
    original_rms_db = 20 * np.log10(np.sqrt(np.mean(test_audio ** 2)))
    normalized_rms_db = 20 * np.log10(np.sqrt(np.mean(normalized ** 2)))
    
    print(f"  ✓ Normalisation RMS:")
    print(f"    - RMS original: {original_rms_db:.1f}dB")
    print(f"    - RMS normalisé: {normalized_rms_db:.1f}dB")
    print(f"    - Gain appliqué: {normalized_rms_db - original_rms_db:+.1f}dB")
    
    print(f"\n🎉 Tous les tests de mixage audio sont terminés!")
    
    # Résumé final
    print(f"\n📋 Résumé des tests:")
    print(f"  - Fichiers audio créés: {len(audio_files)}")
    print(f"  - Pistes mixées: {len(tracks)}")
    print(f"  - Configurations testées: 2 (défaut + personnalisée)")
    print(f"  - Transitions crossfade: 1")
    print(f"  - Cache audio testé: ✓")
    print(f"  - Limitation/normalisation: ✓")
    
    # Nettoyage
    temp_storage.cleanup_all()
    print(f"🧹 Nettoyage terminé")


if __name__ == "__main__":
    test_audio_mixer()