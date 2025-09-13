#!/usr/bin/env python3
"""
Tests pour le processeur de mixage audio.
"""

import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

from ai_video_dubbing.processors.audio_mixer import (
    AudioMixer, AudioTrack, MixingConfig, MixingResult
)
from ai_video_dubbing.models.data_models import (
    DialogueSegment, ProcessingError, ValidationError
)
from ai_video_dubbing.utils.temp_storage import TempStorage


class TestAudioMixer:
    """Tests pour AudioMixer."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_storage = TempStorage()
        self.mixer = AudioMixer(self.temp_storage)
        
        # Créer des fichiers audio de test
        self.test_audio_paths = self._create_test_audio_files()
    
    def _create_test_audio_files(self) -> list:
        """Crée des fichiers audio de test."""
        audio_paths = []
        
        # Créer différents types d'audio
        audio_types = [
            ("dialogue", 3.0, 440),  # Dialogue, 3s, 440Hz
            ("music", 10.0, 220),    # Musique, 10s, 220Hz
            ("sfx", 1.0, 880)        # Effet sonore, 1s, 880Hz
        ]
        
        for i, (audio_type, duration, frequency) in enumerate(audio_types):
            sample_rate = 48000
            num_samples = int(duration * sample_rate)
            
            # Générer le signal
            t = np.linspace(0, duration, num_samples)
            
            if audio_type == "dialogue":
                # Signal vocal simulé
                signal = 0.3 * np.sin(2 * np.pi * frequency * t)
                envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # Modulation
                audio_data = signal * envelope
            elif audio_type == "music":
                # Signal musical avec harmoniques
                signal = (0.4 * np.sin(2 * np.pi * frequency * t) +
                         0.2 * np.sin(2 * np.pi * 2 * frequency * t) +
                         0.1 * np.sin(2 * np.pi * 3 * frequency * t))
                audio_data = signal
            else:  # sfx
                # Effet sonore court et percutant
                signal = 0.5 * np.sin(2 * np.pi * frequency * t)
                envelope = np.exp(-t * 3)  # Décroissance exponentielle
                audio_data = signal * envelope
            
            # Ajouter du bruit léger
            noise = 0.01 * np.random.randn(num_samples)
            audio_data += noise
            
            # Sauvegarder
            audio_path = self.temp_storage.get_temp_path(f"test_{audio_type}_{i}.wav")
            
            try:
                import soundfile as sf
                sf.write(audio_path, audio_data, sample_rate)
            except ImportError:
                # Créer un fichier avec des données simulées
                with open(audio_path, 'w') as f:
                    f.write(f"Mock {audio_type} audio: {duration}s, {frequency}Hz")
            
            audio_paths.append(audio_path)
        
        return audio_paths
    
    def test_init(self):
        """Test d'initialisation du mixeur."""
        mixer = AudioMixer()
        assert mixer.temp_storage is not None
        assert mixer.logger is not None
        assert mixer.default_config.target_sample_rate == 48000
        assert mixer.default_config.target_channels == 2
        assert mixer.default_config.auto_ducking == True
        assert len(mixer.audio_cache) == 0
    
    def test_init_with_temp_storage(self):
        """Test d'initialisation avec gestionnaire de stockage."""
        temp_storage = TempStorage()
        mixer = AudioMixer(temp_storage)
        assert mixer.temp_storage is temp_storage
    
    def test_create_audio_track_valid(self):
        """Test de création de piste audio valide."""
        audio_path = self.test_audio_paths[0]
        
        track = self.mixer.create_audio_track(
            track_id="test_track",
            audio_path=audio_path,
            track_type="dialogue",
            start_time=1.0,
            end_time=4.0,
            volume_level=0.8,
            fade_in=0.1,
            fade_out=0.2,
            pan=0.5,
            priority=5
        )
        
        assert track.track_id == "test_track"
        assert track.audio_path == audio_path
        assert track.track_type == "dialogue"
        assert track.start_time == 1.0
        assert track.end_time == 4.0
        assert track.volume_level == 0.8
        assert track.fade_in == 0.1
        assert track.fade_out == 0.2
        assert track.pan == 0.5
        assert track.priority == 5
    
    def test_create_audio_track_nonexistent_file(self):
        """Test de création de piste avec fichier inexistant."""
        try:
            self.mixer.create_audio_track(
                track_id="invalid_track",
                audio_path="nonexistent.wav",
                track_type="dialogue"
            )
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "not found" in str(e)
    
    def test_create_audio_track_auto_duration(self):
        """Test de création de piste avec durée automatique."""
        audio_path = self.test_audio_paths[0]
        
        track = self.mixer.create_audio_track(
            track_id="auto_duration",
            audio_path=audio_path,
            track_type="dialogue",
            start_time=2.0
            # end_time non spécifié
        )
        
        # end_time devrait être calculé automatiquement
        assert track.end_time > track.start_time
    
    def test_get_audio_duration(self):
        """Test de calcul de durée audio."""
        audio_path = self.test_audio_paths[0]
        duration = self.mixer._get_audio_duration(audio_path)
        
        # Devrait retourner une durée positive
        assert duration > 0
    
    def test_load_audio_cached(self):
        """Test de chargement audio avec cache."""
        audio_path = self.test_audio_paths[0]
        
        # Premier chargement
        audio1, sr1 = self.mixer._load_audio_cached(audio_path)
        assert len(self.mixer.audio_cache) == 1
        
        # Deuxième chargement (depuis le cache)
        audio2, sr2 = self.mixer._load_audio_cached(audio_path)
        assert np.array_equal(audio1, audio2)
        assert sr1 == sr2
        assert len(self.mixer.audio_cache) == 1  # Pas d'ajout supplémentaire
    
    def test_calculate_pan_gains(self):
        """Test de calcul des gains de panning."""
        # Centre
        left, right = self.mixer._calculate_pan_gains(0.0)
        assert abs(left - right) < 0.01  # Approximativement égaux
        
        # Complètement à gauche
        left, right = self.mixer._calculate_pan_gains(-1.0)
        assert left > right
        assert abs(left - 1.0) < 0.01
        assert abs(right - 0.0) < 0.01
        
        # Complètement à droite
        left, right = self.mixer._calculate_pan_gains(1.0)
        assert right > left
        assert abs(right - 1.0) < 0.01
        assert abs(left - 0.0) < 0.01
    
    def test_apply_fade_in(self):
        """Test d'application du fade in."""
        # Créer un signal de test
        sample_rate = 48000
        duration = 1.0
        num_samples = int(duration * sample_rate)
        audio = np.ones(num_samples)  # Signal constant
        
        # Appliquer fade in de 0.1s
        faded = self.mixer._apply_fade_in(audio, 0.1, sample_rate)
        
        # Le début devrait être atténué
        assert faded[0] < 1.0
        assert faded[-1] == 1.0  # La fin devrait être inchangée
        
        # Vérifier la progression du fade
        fade_samples = int(0.1 * sample_rate)
        assert faded[fade_samples - 1] < 1.0
        assert faded[fade_samples] == 1.0
    
    def test_apply_fade_out(self):
        """Test d'application du fade out."""
        # Créer un signal de test
        sample_rate = 48000
        duration = 1.0
        num_samples = int(duration * sample_rate)
        audio = np.ones(num_samples)  # Signal constant
        
        # Appliquer fade out de 0.1s
        faded = self.mixer._apply_fade_out(audio, 0.1, sample_rate)
        
        # Le début devrait être inchangé
        assert faded[0] == 1.0
        assert faded[-1] < 1.0  # La fin devrait être atténuée
        
        # Vérifier la progression du fade
        fade_samples = int(0.1 * sample_rate)
        assert faded[-fade_samples] == 1.0
        assert faded[-1] < 1.0
    
    def test_normalize_rms_fallback(self):
        """Test de normalisation RMS de fallback."""
        # Créer un signal avec niveau spécifique
        audio = np.random.randn(1000) * 0.1  # Niveau faible
        
        normalized = self.mixer._normalize_rms_fallback(audio, -20.0)
        
        # Le niveau devrait avoir augmenté
        original_rms = np.sqrt(np.mean(audio ** 2))
        normalized_rms = np.sqrt(np.mean(normalized ** 2))
        
        assert normalized_rms > original_rms
    
    def test_apply_limiter(self):
        """Test d'application du limiteur."""
        # Créer un signal avec des crêtes élevées
        audio = np.array([0.5, 1.5, -1.2, 0.3, 2.0])  # Avec saturation
        
        limited = self.mixer._apply_limiter(audio, -3.0)  # Seuil à -3dB (≈0.7)
        
        # Les crêtes devraient être limitées
        assert np.max(np.abs(limited)) <= 0.71  # Légèrement au-dessus du seuil théorique
    
    def test_calculate_mix_quality_metrics(self):
        """Test de calcul des métriques de qualité."""
        # Créer un signal de test
        sample_rate = 48000
        audio = np.random.randn(sample_rate) * 0.5  # 1 seconde de bruit
        
        metrics = self.mixer._calculate_mix_quality_metrics(audio, sample_rate)
        
        # Vérifier la structure
        required_keys = [
            "peak_level", "rms_level", "dynamic_range", "lufs_level",
            "clipping_ratio", "crest_factor"
        ]
        for key in required_keys:
            assert key in metrics
        
        # Vérifier les valeurs
        assert metrics["peak_level"] < 0  # En dB, devrait être négatif
        assert metrics["rms_level"] < 0   # En dB, devrait être négatif
        assert metrics["dynamic_range"] > 0
        assert 0 <= metrics["clipping_ratio"] <= 1
    
    def test_create_crossfade_transition(self):
        """Test de création de transition crossfade."""
        # Créer deux pistes
        track1 = AudioTrack(
            track_id="track1",
            audio_path=self.test_audio_paths[0],
            track_type="music",
            start_time=0.0,
            end_time=5.0,
            volume_level=1.0,
            fade_in=0.0,
            fade_out=0.0,
            pan=0.0,
            priority=1
        )
        
        track2 = AudioTrack(
            track_id="track2",
            audio_path=self.test_audio_paths[1],
            track_type="music",
            start_time=4.0,
            end_time=9.0,
            volume_level=1.0,
            fade_in=0.0,
            fade_out=0.0,
            pan=0.0,
            priority=1
        )
        
        # Créer le crossfade
        modified_track1, modified_track2 = self.mixer.create_crossfade_transition(
            track1, track2, 1.0
        )
        
        # Vérifier les modifications
        assert modified_track1.fade_out == 1.0  # Fade out ajouté
        assert modified_track2.fade_in == 1.0   # Fade in ajouté
        assert modified_track2.start_time == 4.0  # Début ajusté
    
    def test_mix_audio_tracks_empty(self):
        """Test de mixage avec liste vide."""
        try:
            self.mixer.mix_audio_tracks([])
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "No audio tracks" in str(e)
    
    def test_mix_audio_tracks_single(self):
        """Test de mixage avec une seule piste."""
        track = self.mixer.create_audio_track(
            track_id="single_track",
            audio_path=self.test_audio_paths[0],
            track_type="dialogue",
            start_time=0.0,
            volume_level=0.8
        )
        
        result = self.mixer.mix_audio_tracks([track])
        
        # Vérifier le résultat
        assert isinstance(result, MixingResult)
        assert Path(result.mixed_audio_path).exists()
        assert result.track_count == 1
        assert result.total_duration > 0
        assert result.processing_time > 0
    
    def test_mix_audio_tracks_multiple(self):
        """Test de mixage avec plusieurs pistes."""
        tracks = []
        
        # Créer plusieurs pistes
        for i, audio_path in enumerate(self.test_audio_paths):
            track_type = ["dialogue", "music", "sfx"][i]
            track = self.mixer.create_audio_track(
                track_id=f"track_{i}",
                audio_path=audio_path,
                track_type=track_type,
                start_time=i * 2.0,  # Décalage temporel
                volume_level=0.7,
                priority=10 - i  # Priorités différentes
            )
            tracks.append(track)
        
        result = self.mixer.mix_audio_tracks(tracks)
        
        # Vérifier le résultat
        assert isinstance(result, MixingResult)
        assert Path(result.mixed_audio_path).exists()
        assert result.track_count == len(tracks)
        assert result.total_duration > 0
        assert len(result.mixing_statistics) == len(tracks)
    
    def test_mix_audio_tracks_with_custom_config(self):
        """Test de mixage avec configuration personnalisée."""
        track = self.mixer.create_audio_track(
            track_id="custom_track",
            audio_path=self.test_audio_paths[0],
            track_type="dialogue"
        )
        
        custom_config = MixingConfig(
            target_sample_rate=44100,
            target_channels=1,  # Mono
            output_format="wav",
            output_bitrate=192,
            normalize_output=False,
            target_lufs=-16.0,
            limiter_threshold=-2.0,
            dialogue_level=1.2,
            music_level=0.4,
            sfx_level=0.8,
            crossfade_duration=0.2,
            auto_ducking=False,
            ducking_amount=4.0,
            ducking_attack=0.1,
            ducking_release=0.3
        )
        
        result = self.mixer.mix_audio_tracks([track], config=custom_config)
        
        assert isinstance(result, MixingResult)
        assert Path(result.mixed_audio_path).exists()
    
    def test_clear_audio_cache(self):
        """Test de nettoyage du cache."""
        # Charger quelques fichiers pour remplir le cache
        for audio_path in self.test_audio_paths:
            self.mixer._load_audio_cached(audio_path)
        
        assert len(self.mixer.audio_cache) > 0
        
        # Nettoyer le cache
        self.mixer.clear_audio_cache()
        
        assert len(self.mixer.audio_cache) == 0
    
    def test_get_mixing_statistics(self):
        """Test de récupération des statistiques."""
        # Charger un fichier pour avoir des données
        self.mixer._load_audio_cached(self.test_audio_paths[0])
        
        stats = self.mixer.get_mixing_statistics()
        
        # Vérifier la structure
        assert "cache_size" in stats
        assert "max_cache_size" in stats
        assert "cached_files" in stats
        
        # Vérifier les valeurs
        assert stats["cache_size"] == 1
        assert stats["max_cache_size"] == self.mixer.max_cache_size
        assert len(stats["cached_files"]) == 1


class TestAudioTrack:
    """Tests pour la classe AudioTrack."""
    
    def test_audio_track_creation(self):
        """Test de création d'une piste audio."""
        track = AudioTrack(
            track_id="test_track",
            audio_path="test.wav",
            track_type="dialogue",
            start_time=1.0,
            end_time=5.0,
            volume_level=0.8,
            fade_in=0.1,
            fade_out=0.2,
            pan=0.5,
            priority=10
        )
        
        assert track.track_id == "test_track"
        assert track.audio_path == "test.wav"
        assert track.track_type == "dialogue"
        assert track.start_time == 1.0
        assert track.end_time == 5.0
        assert track.volume_level == 0.8
        assert track.fade_in == 0.1
        assert track.fade_out == 0.2
        assert track.pan == 0.5
        assert track.priority == 10


class TestMixingConfig:
    """Tests pour la classe MixingConfig."""
    
    def test_mixing_config_creation(self):
        """Test de création de configuration de mixage."""
        config = MixingConfig(
            target_sample_rate=48000,
            target_channels=2,
            output_format="wav",
            output_bitrate=320,
            normalize_output=True,
            target_lufs=-23.0,
            limiter_threshold=-1.0,
            dialogue_level=1.0,
            music_level=0.3,
            sfx_level=0.7,
            crossfade_duration=0.1,
            auto_ducking=True,
            ducking_amount=6.0,
            ducking_attack=0.05,
            ducking_release=0.5
        )
        
        assert config.target_sample_rate == 48000
        assert config.target_channels == 2
        assert config.output_format == "wav"
        assert config.normalize_output == True
        assert config.auto_ducking == True


class TestMixingResult:
    """Tests pour la classe MixingResult."""
    
    def test_mixing_result_creation(self):
        """Test de création de résultat de mixage."""
        result = MixingResult(
            mixed_audio_path="output.wav",
            total_duration=10.5,
            track_count=3,
            peak_level=-2.1,
            rms_level=-18.5,
            lufs_level=-23.0,
            processing_time=2.3,
            mixing_statistics={"track1": {"type": "dialogue"}},
            quality_metrics={"dynamic_range": 16.4}
        )
        
        assert result.mixed_audio_path == "output.wav"
        assert result.total_duration == 10.5
        assert result.track_count == 3
        assert result.peak_level == -2.1
        assert result.rms_level == -18.5
        assert result.lufs_level == -23.0
        assert result.processing_time == 2.3
        assert "track1" in result.mixing_statistics
        assert "dynamic_range" in result.quality_metrics