#!/usr/bin/env python3
"""
Tests pour le processeur de clonage de voix.
"""

import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

from ai_video_dubbing.processors.voice_cloner import (
    VoiceCloner, VoiceProfile, VoiceCloneResult, CloningSynthesisConfig
)
from ai_video_dubbing.models.data_models import (
    DialogueSegment, ProcessingError, ValidationError
)
from ai_video_dubbing.utils.temp_storage import TempStorage


class TestVoiceCloner:
    """Tests pour VoiceCloner."""
    
    def setup_method(self):
        """Configuration pour chaque test."""
        self.temp_storage = TempStorage()
        self.cloner = VoiceCloner(self.temp_storage)
        
        # Créer des fichiers audio de test
        self.test_audio_paths = self._create_test_audio_files()
        
        # Créer un profil vocal de test
        self.voice_profile = VoiceProfile(
            speaker_id="SPEAKER_00",
            reference_audio_paths=self.test_audio_paths,
            voice_characteristics={
                'fundamental_frequency': 150.0,
                'spectral_centroid': 1500.0,
                'pitch_range': 30.0,
                'energy_level': 0.6
            },
            model_embeddings={'tortoise': None, 'nemo': None},
            quality_score=0.8,
            total_reference_duration=15.0
        )
    
    def _create_test_audio_files(self) -> list:
        """Crée des fichiers audio de test."""
        audio_paths = []
        
        for i in range(3):
            # Créer des données audio simulées
            duration = 5.0
            sample_rate = 22050
            num_samples = int(duration * sample_rate)
            
            # Signal vocal simulé
            t = np.linspace(0, duration, num_samples)
            f0 = 150 + i * 10  # Fréquences légèrement différentes
            signal = 0.5 * np.sin(2 * np.pi * f0 * t)
            noise = 0.05 * np.random.randn(num_samples)
            audio_data = signal + noise
            
            # Sauvegarder
            audio_path = self.temp_storage.get_temp_path(f"test_voice_{i}.wav")
            
            try:
                import soundfile as sf
                sf.write(audio_path, audio_data, sample_rate)
            except ImportError:
                # Créer un fichier vide pour les tests
                Path(audio_path).touch()
            
            audio_paths.append(audio_path)
        
        return audio_paths
    
    def test_init(self):
        """Test d'initialisation du cloneur."""
        cloner = VoiceCloner()
        assert cloner.temp_storage is not None
        assert cloner.logger is not None
        assert cloner.default_config.model_name == "tortoise"
        assert cloner.current_model is None
        assert len(cloner.available_models) == 0
    
    def test_init_with_temp_storage(self):
        """Test d'initialisation avec gestionnaire de stockage."""
        temp_storage = TempStorage()
        cloner = VoiceCloner(temp_storage)
        assert cloner.temp_storage is temp_storage
    
    def test_initialize_model_tortoise(self):
        """Test d'initialisation du modèle Tortoise."""
        success = self.cloner.initialize_model("tortoise")
        
        assert success
        assert "tortoise" in self.cloner.available_models
        assert self.cloner.current_model == "tortoise"
        assert self.cloner.available_models["tortoise"]["initialized"]
    
    def test_initialize_model_nemo(self):
        """Test d'initialisation du modèle NeMo."""
        success = self.cloner.initialize_model("nemo")
        
        assert success
        assert "nemo" in self.cloner.available_models
    
    def test_initialize_model_coqui(self):
        """Test d'initialisation du modèle Coqui."""
        success = self.cloner.initialize_model("coqui")
        
        assert success
        assert "coqui" in self.cloner.available_models
    
    def test_initialize_model_unsupported(self):
        """Test d'initialisation avec modèle non supporté."""
        try:
            self.cloner.initialize_model("unsupported_model")
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "Unsupported model" in str(e)
    
    def test_get_audio_duration(self):
        """Test de calcul de durée audio."""
        # Test avec un fichier existant
        audio_path = self.test_audio_paths[0]
        duration = self.cloner._get_audio_duration(audio_path)
        
        # Devrait retourner une durée positive
        assert duration > 0
    
    def test_get_audio_duration_nonexistent(self):
        """Test de durée avec fichier inexistant."""
        duration = self.cloner._get_audio_duration("nonexistent.wav")
        
        # Devrait retourner la durée par défaut
        assert duration == 5.0
    
    def test_analyze_voice_characteristics(self):
        """Test d'analyse des caractéristiques vocales."""
        characteristics = self.cloner._analyze_voice_characteristics(self.test_audio_paths)
        
        # Vérifier la structure
        required_keys = [
            'fundamental_frequency', 'spectral_centroid', 'pitch_range',
            'energy_level', 'voice_quality', 'speaking_rate'
        ]
        for key in required_keys:
            assert key in characteristics
        
        # Vérifier les valeurs
        assert characteristics['fundamental_frequency'] > 0
        assert characteristics['spectral_centroid'] > 0
        assert characteristics['pitch_range'] >= 0
    
    def test_create_voice_embeddings(self):
        """Test de création d'embeddings vocaux."""
        # Initialiser un modèle pour les embeddings
        self.cloner.initialize_model("tortoise")
        
        embeddings = self.cloner._create_voice_embeddings(self.test_audio_paths)
        
        # Vérifier la structure
        assert isinstance(embeddings, dict)
        # Les embeddings peuvent être None pour les mocks
    
    def test_calculate_voice_quality_score(self):
        """Test de calcul du score de qualité vocale."""
        characteristics = {
            'fundamental_frequency': 150.0,
            'pitch_range': 25.0,  # Voix stable
            'spectral_centroid': 1500.0,  # Dans la plage normale
            'energy_level': 0.6
        }
        
        score = self.cloner._calculate_voice_quality_score(
            self.test_audio_paths, characteristics
        )
        
        # Score devrait être entre 0 et 1
        assert 0.0 <= score <= 1.0
        
        # Avec 3 échantillons et de bonnes caractéristiques, score devrait être élevé
        assert score > 0.7
    
    def test_create_voice_profile_valid(self):
        """Test de création de profil vocal valide."""
        profile = self.cloner.create_voice_profile(
            "TEST_SPEAKER",
            self.test_audio_paths,
            min_duration=5.0
        )
        
        assert profile.speaker_id == "TEST_SPEAKER"
        assert len(profile.reference_audio_paths) == len(self.test_audio_paths)
        assert profile.total_reference_duration > 0
        assert 0.0 <= profile.quality_score <= 1.0
        assert isinstance(profile.voice_characteristics, dict)
    
    def test_create_voice_profile_no_files(self):
        """Test de création de profil sans fichiers."""
        try:
            self.cloner.create_voice_profile("TEST_SPEAKER", [])
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "No reference audio files" in str(e)
    
    def test_create_voice_profile_insufficient_duration(self):
        """Test avec durée insuffisante."""
        # Mock pour retourner une durée très courte
        with patch.object(self.cloner, '_get_audio_duration', return_value=1.0):
            try:
                self.cloner.create_voice_profile(
                    "TEST_SPEAKER",
                    self.test_audio_paths,
                    min_duration=10.0
                )
                assert False, "Devrait lever ValidationError"
            except ValidationError as e:
                assert "Insufficient reference audio" in str(e)
    
    def test_mock_voice_generation(self):
        """Test de génération mock."""
        text = "Hello, this is a test."
        
        output_path = self.cloner._mock_voice_generation(
            text, self.voice_profile, None
        )
        
        # Vérifier que le fichier a été créé
        assert Path(output_path).exists()
        
        # Vérifier le nom du fichier
        assert self.voice_profile.speaker_id in output_path
    
    def test_clone_voice_no_model(self):
        """Test de clonage sans modèle initialisé."""
        try:
            self.cloner.clone_voice("Test text", self.voice_profile)
            assert False, "Devrait lever ProcessingError"
        except ProcessingError as e:
            assert "No voice cloning model initialized" in str(e)
    
    def test_clone_voice_empty_text(self):
        """Test de clonage avec texte vide."""
        self.cloner.initialize_model("tortoise")
        
        try:
            self.cloner.clone_voice("", self.voice_profile)
            assert False, "Devrait lever ValidationError"
        except ValidationError as e:
            assert "Empty text" in str(e)
    
    def test_clone_voice_success(self):
        """Test de clonage réussi."""
        # Initialiser le modèle
        self.cloner.initialize_model("tortoise")
        
        text = "Hello, this is a test of voice cloning."
        
        result = self.cloner.clone_voice(text, self.voice_profile)
        
        # Vérifier le résultat
        assert isinstance(result, VoiceCloneResult)
        assert result.original_text == text
        assert result.speaker_id == self.voice_profile.speaker_id
        assert result.generation_time > 0
        assert Path(result.cloned_audio_path).exists()
        assert result.model_used == "tortoise"
        assert 0.0 <= result.voice_similarity_score <= 1.0
    
    def test_clone_voice_with_custom_config(self):
        """Test de clonage avec configuration personnalisée."""
        self.cloner.initialize_model("tortoise")
        
        config = CloningSynthesisConfig(
            model_name="tortoise",
            quality_preset="high_quality",
            temperature=0.5,
            repetition_penalty=1.5,
            length_penalty=1.2,
            max_generation_length=20.0,
            use_deepspeed=False,
            batch_size=1,
            voice_conditioning_length=8.0
        )
        
        result = self.cloner.clone_voice(
            "Test with custom config",
            self.voice_profile,
            config=config
        )
        
        assert isinstance(result, VoiceCloneResult)
        assert Path(result.cloned_audio_path).exists()
    
    def test_analyze_generated_audio_quality(self):
        """Test d'analyse de qualité audio généré."""
        # Créer un fichier audio de test
        audio_path = self.test_audio_paths[0]
        
        metrics = self.cloner._analyze_generated_audio_quality(audio_path)
        
        # Vérifier la structure
        required_keys = [
            'duration', 'rms_level', 'peak_level', 'spectral_quality',
            'naturalness_score', 'clarity_score'
        ]
        for key in required_keys:
            assert key in metrics
        
        # Vérifier les valeurs
        assert metrics['duration'] > 0
        assert metrics['rms_level'] >= 0
        assert metrics['peak_level'] >= 0
        assert 0.0 <= metrics['spectral_quality'] <= 1.0
    
    def test_calculate_voice_similarity(self):
        """Test de calcul de similarité vocale."""
        generated_path = self.test_audio_paths[0]
        
        similarity = self.cloner._calculate_voice_similarity(
            generated_path, self.voice_profile
        )
        
        # Score devrait être entre 0 et 1
        assert 0.0 <= similarity <= 1.0
    
    def test_batch_clone_dialogue(self):
        """Test de clonage par lot."""
        # Initialiser le modèle
        self.cloner.initialize_model("tortoise")
        
        # Créer des segments de dialogue
        dialogue_segments = [
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=1.0,
                end_time=3.0,
                original_text="First segment",
                audio_path="",
                confidence_score=0.9
            ),
            DialogueSegment(
                speaker_id="SPEAKER_00",
                start_time=4.0,
                end_time=6.0,
                original_text="Second segment",
                audio_path="",
                confidence_score=0.8
            )
        ]
        
        voice_profiles = {
            "SPEAKER_00": self.voice_profile
        }
        
        results = self.cloner.batch_clone_dialogue(
            dialogue_segments, voice_profiles
        )
        
        # Vérifier les résultats
        assert "SPEAKER_00" in results
        assert len(results["SPEAKER_00"]) == 2
        
        for result in results["SPEAKER_00"]:
            assert isinstance(result, VoiceCloneResult)
            assert Path(result.cloned_audio_path).exists()
    
    def test_batch_clone_dialogue_missing_profile(self):
        """Test de clonage par lot avec profil manquant."""
        self.cloner.initialize_model("tortoise")
        
        dialogue_segments = [
            DialogueSegment(
                speaker_id="UNKNOWN_SPEAKER",
                start_time=1.0,
                end_time=3.0,
                original_text="Test segment",
                audio_path="",
                confidence_score=0.9
            )
        ]
        
        voice_profiles = {}  # Aucun profil
        
        results = self.cloner.batch_clone_dialogue(
            dialogue_segments, voice_profiles
        )
        
        # Aucun résultat ne devrait être généré
        assert len(results) == 0
    
    def test_update_generation_stats(self):
        """Test de mise à jour des statistiques."""
        initial_count = self.cloner.generation_stats['total_generations']
        
        self.cloner._update_generation_stats(2.5, 100)
        
        # Vérifier la mise à jour
        assert self.cloner.generation_stats['total_generations'] == initial_count + 1
        assert self.cloner.generation_stats['total_time'] >= 2.5
        assert self.cloner.generation_stats['average_time_per_second'] > 0
    
    def test_get_generation_statistics(self):
        """Test de récupération des statistiques."""
        # Générer quelques statistiques
        self.cloner._update_generation_stats(1.0, 50)
        self.cloner._update_generation_stats(2.0, 100)
        
        stats = self.cloner.get_generation_statistics()
        
        # Vérifier la structure
        assert 'total_generations' in stats
        assert 'total_time' in stats
        assert 'average_generation_time' in stats
        assert 'model_usage' in stats
        
        # Vérifier les valeurs
        assert stats['total_generations'] == 2
        assert stats['total_time'] == 3.0
        assert stats['average_generation_time'] == 1.5
    
    def test_get_available_models(self):
        """Test de récupération des modèles disponibles."""
        # Initialiser quelques modèles
        self.cloner.initialize_model("tortoise")
        self.cloner.initialize_model("nemo")
        
        models = self.cloner.get_available_models()
        
        assert "tortoise" in models
        assert "nemo" in models
        assert len(models) >= 2
    
    def test_cleanup_model_cache(self):
        """Test de nettoyage du cache."""
        # Ajouter quelque chose au cache
        self.cloner.model_cache["test"] = "data"
        
        self.cloner.cleanup_model_cache()
        
        # Le cache devrait être vide
        assert len(self.cloner.model_cache) == 0


class TestVoiceProfile:
    """Tests pour la classe VoiceProfile."""
    
    def test_voice_profile_creation(self):
        """Test de création d'un profil vocal."""
        profile = VoiceProfile(
            speaker_id="TEST_SPEAKER",
            reference_audio_paths=["audio1.wav", "audio2.wav"],
            voice_characteristics={"f0": 150.0},
            model_embeddings={"tortoise": None},
            quality_score=0.8,
            total_reference_duration=10.0
        )
        
        assert profile.speaker_id == "TEST_SPEAKER"
        assert len(profile.reference_audio_paths) == 2
        assert profile.quality_score == 0.8
        assert profile.total_reference_duration == 10.0


class TestCloningSynthesisConfig:
    """Tests pour la classe CloningSynthesisConfig."""
    
    def test_config_creation(self):
        """Test de création de configuration."""
        config = CloningSynthesisConfig(
            model_name="tortoise",
            quality_preset="high_quality",
            voice_conditioning_length=6.0,
            temperature=0.8,
            repetition_penalty=2.0,
            length_penalty=1.0,
            max_generation_length=30.0,
            use_deepspeed=False,
            batch_size=1
        )
        
        assert config.model_name == "tortoise"
        assert config.quality_preset == "high_quality"
        assert config.temperature == 0.8
        assert config.batch_size == 1


class TestVoiceCloneResult:
    """Tests pour la classe VoiceCloneResult."""
    
    def test_result_creation(self):
        """Test de création de résultat."""
        result = VoiceCloneResult(
            cloned_audio_path="output.wav",
            original_text="Test text",
            speaker_id="SPEAKER_00",
            generation_time=2.5,
            quality_metrics={"rms": 0.5},
            model_used="tortoise",
            voice_similarity_score=0.85
        )
        
        assert result.cloned_audio_path == "output.wav"
        assert result.original_text == "Test text"
        assert result.speaker_id == "SPEAKER_00"
        assert result.generation_time == 2.5
        assert result.model_used == "tortoise"
        assert result.voice_similarity_score == 0.85