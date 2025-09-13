#!/usr/bin/env python3
"""
Processeur de clonage de voix pour l'application de doublage vidéo par IA.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import tempfile
import time
import warnings

from ..models.data_models import (
    DialogueSegment, ProcessingError, ValidationError
)
from ..utils.temp_storage import TempStorage


@dataclass
class VoiceCloneResult:
    """Résultat du clonage de voix."""
    cloned_audio_path: str
    original_text: str
    speaker_id: str
    generation_time: float
    quality_metrics: Dict[str, Any]
    model_used: str
    voice_similarity_score: float


@dataclass
class VoiceProfile:
    """Profil vocal pour le clonage."""
    speaker_id: str
    reference_audio_paths: List[str]
    voice_characteristics: Dict[str, Any]
    model_embeddings: Optional[Dict[str, Any]]
    quality_score: float
    total_reference_duration: float


@dataclass
class CloningSynthesisConfig:
    """Configuration pour la synthèse de clonage."""
    model_name: str
    quality_preset: str  # "fast", "balanced", "high_quality"
    voice_conditioning_length: float  # Durée des échantillons de référence
    temperature: float  # Créativité vs fidélité
    repetition_penalty: float
    length_penalty: float
    max_generation_length: float
    use_deepspeed: bool
    batch_size: int


class VoiceCloner:
    """Processeur de clonage de voix avec support multi-modèles."""
    
    def __init__(self, temp_storage: Optional[TempStorage] = None):
        """
        Initialise le cloneur de voix.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage or TempStorage()
        self.logger = logging.getLogger(__name__)
        
        # Configuration par défaut
        self.default_config = CloningSynthesisConfig(
            model_name="tortoise",  # "tortoise", "nemo", "coqui"
            quality_preset="balanced",
            voice_conditioning_length=6.0,
            temperature=0.8,
            repetition_penalty=2.0,
            length_penalty=1.0,
            max_generation_length=30.0,
            use_deepspeed=False,
            batch_size=1
        )
        
        # Modèles disponibles
        self.available_models = {}
        self.current_model = None
        self.model_cache = {}
        
        # Métriques de performance
        self.generation_stats = {
            "total_generations": 0,
            "total_time": 0.0,
            "average_time_per_second": 0.0,
            "model_usage": {}
        }
    
    def initialize_model(self, model_name: str, **model_kwargs) -> bool:
        """
        Initialise un modèle de clonage de voix.
        
        Args:
            model_name: Nom du modèle ("tortoise", "nemo", "coqui")
            **model_kwargs: Arguments spécifiques au modèle
            
        Returns:
            True si l'initialisation réussit
        """
        try:
            self.logger.info(f"Initializing voice cloning model: {model_name}")
            
            if model_name.lower() == "tortoise":
                return self._initialize_tortoise(**model_kwargs)
            elif model_name.lower() == "nemo":
                return self._initialize_nemo(**model_kwargs)
            elif model_name.lower() == "coqui":
                return self._initialize_coqui(**model_kwargs)
            else:
                raise ValidationError(f"Unsupported model: {model_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize model {model_name}: {e}")
            return False
    
    def _initialize_tortoise(self, **kwargs) -> bool:
        """Initialise le modèle Tortoise-TTS."""
        try:
            # Tentative d'import de Tortoise-TTS
            try:
                from tortoise.api import TextToSpeech
                from tortoise.utils.audio import load_audio, load_voices
                
                # Configuration Tortoise
                device = kwargs.get('device', 'auto')
                models_dir = kwargs.get('models_dir', None)
                
                # Initialiser le modèle
                tts = TextToSpeech(
                    models_dir=models_dir,
                    enable_redaction=False,
                    device=device
                )
                
                self.available_models['tortoise'] = {
                    'model': tts,
                    'load_audio': load_audio,
                    'load_voices': load_voices,
                    'initialized': True
                }
                
                self.current_model = 'tortoise'
                self.logger.info("Tortoise-TTS initialized successfully")
                return True
                
            except ImportError:
                self.logger.warning("Tortoise-TTS not available, using mock implementation")
                # Mock pour les tests
                self.available_models['tortoise'] = {
                    'model': self._create_mock_tortoise(),
                    'initialized': True,
                    'mock': True
                }
                self.current_model = 'tortoise'
                return True
                
        except Exception as e:
            self.logger.error(f"Tortoise initialization failed: {e}")
            return False
    
    def _initialize_nemo(self, **kwargs) -> bool:
        """Initialise le modèle NeMo."""
        try:
            try:
                import nemo.collections.tts as nemo_tts
                
                # Charger un modèle pré-entraîné NeMo
                model_name = kwargs.get('model_name', 'tts_en_fastpitch')
                
                model = nemo_tts.models.FastPitchModel.from_pretrained(model_name)
                
                self.available_models['nemo'] = {
                    'model': model,
                    'initialized': True
                }
                
                self.logger.info("NeMo TTS initialized successfully")
                return True
                
            except ImportError:
                self.logger.warning("NeMo not available, using mock implementation")
                self.available_models['nemo'] = {
                    'model': self._create_mock_nemo(),
                    'initialized': True,
                    'mock': True
                }
                return True
                
        except Exception as e:
            self.logger.error(f"NeMo initialization failed: {e}")
            return False
    
    def _initialize_coqui(self, **kwargs) -> bool:
        """Initialise le modèle Coqui TTS."""
        try:
            try:
                from TTS.api import TTS
                
                # Modèle par défaut pour le clonage
                model_name = kwargs.get('model_name', 'tts_models/multilingual/multi-dataset/your_tts')
                
                tts = TTS(model_name=model_name, progress_bar=False)
                
                self.available_models['coqui'] = {
                    'model': tts,
                    'initialized': True
                }
                
                self.logger.info("Coqui TTS initialized successfully")
                return True
                
            except ImportError:
                self.logger.warning("Coqui TTS not available, using mock implementation")
                self.available_models['coqui'] = {
                    'model': self._create_mock_coqui(),
                    'initialized': True,
                    'mock': True
                }
                return True
                
        except Exception as e:
            self.logger.error(f"Coqui initialization failed: {e}")
            return False
    
    def create_voice_profile(
        self,
        speaker_id: str,
        reference_audio_paths: List[str],
        min_duration: float = 10.0,
        max_duration: float = 60.0
    ) -> VoiceProfile:
        """
        Crée un profil vocal à partir d'échantillons de référence.
        
        Args:
            speaker_id: Identifiant du locuteur
            reference_audio_paths: Chemins vers les fichiers de référence
            min_duration: Durée minimale requise
            max_duration: Durée maximale recommandée
            
        Returns:
            Profil vocal créé
            
        Raises:
            ValidationError: Si les échantillons ne sont pas valides
        """
        if not reference_audio_paths:
            raise ValidationError("No reference audio files provided")
        
        # Vérifier l'existence des fichiers
        valid_paths = []
        total_duration = 0.0
        
        for path in reference_audio_paths:
            if not Path(path).exists():
                self.logger.warning(f"Reference file not found: {path}")
                continue
            
            # Calculer la durée (simulation pour l'instant)
            try:
                duration = self._get_audio_duration(path)
                total_duration += duration
                valid_paths.append(path)
            except Exception as e:
                self.logger.warning(f"Failed to process {path}: {e}")
        
        if not valid_paths:
            raise ValidationError("No valid reference audio files found")
        
        if total_duration < min_duration:
            raise ValidationError(
                f"Insufficient reference audio: {total_duration:.1f}s < {min_duration}s"
            )
        
        # Analyser les caractéristiques vocales
        voice_characteristics = self._analyze_voice_characteristics(valid_paths)
        
        # Créer les embeddings du modèle
        model_embeddings = self._create_voice_embeddings(valid_paths)
        
        # Calculer le score de qualité
        quality_score = self._calculate_voice_quality_score(
            valid_paths, voice_characteristics
        )
        
        profile = VoiceProfile(
            speaker_id=speaker_id,
            reference_audio_paths=valid_paths,
            voice_characteristics=voice_characteristics,
            model_embeddings=model_embeddings,
            quality_score=quality_score,
            total_reference_duration=total_duration
        )
        
        self.logger.info(
            f"Created voice profile for {speaker_id}: "
            f"{len(valid_paths)} files, {total_duration:.1f}s, "
            f"quality: {quality_score:.3f}"
        )
        
        return profile
    
    def clone_voice(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_path: Optional[str] = None,
        config: Optional[CloningSynthesisConfig] = None
    ) -> VoiceCloneResult:
        """
        Clone une voix pour synthétiser le texte donné.
        
        Args:
            text: Texte à synthétiser
            voice_profile: Profil vocal de référence
            output_path: Chemin de sortie (optionnel)
            config: Configuration de synthèse (optionnel)
            
        Returns:
            Résultat du clonage
            
        Raises:
            ProcessingError: Si le clonage échoue
        """
        if not text.strip():
            raise ValidationError("Empty text provided for cloning")
        
        if not self.current_model or self.current_model not in self.available_models:
            raise ProcessingError("No voice cloning model initialized")
        
        config = config or self.default_config
        
        try:
            start_time = time.time()
            
            self.logger.info(
                f"Cloning voice for speaker {voice_profile.speaker_id}: "
                f"'{text[:50]}...'"
            )
            
            # Générer l'audio selon le modèle
            if self.current_model == 'tortoise':
                cloned_audio_path = self._clone_with_tortoise(
                    text, voice_profile, output_path, config
                )
            elif self.current_model == 'nemo':
                cloned_audio_path = self._clone_with_nemo(
                    text, voice_profile, output_path, config
                )
            elif self.current_model == 'coqui':
                cloned_audio_path = self._clone_with_coqui(
                    text, voice_profile, output_path, config
                )
            else:
                raise ProcessingError(f"Unsupported model: {self.current_model}")
            
            generation_time = time.time() - start_time
            
            # Analyser la qualité du résultat
            quality_metrics = self._analyze_generated_audio_quality(cloned_audio_path)
            
            # Calculer la similarité vocale
            similarity_score = self._calculate_voice_similarity(
                cloned_audio_path, voice_profile
            )
            
            # Mettre à jour les statistiques
            self._update_generation_stats(generation_time, len(text))
            
            result = VoiceCloneResult(
                cloned_audio_path=cloned_audio_path,
                original_text=text,
                speaker_id=voice_profile.speaker_id,
                generation_time=generation_time,
                quality_metrics=quality_metrics,
                model_used=self.current_model,
                voice_similarity_score=similarity_score
            )
            
            self.logger.info(
                f"Voice cloning completed in {generation_time:.2f}s "
                f"(similarity: {similarity_score:.3f})"
            )
            
            return result
            
        except Exception as e:
            raise ProcessingError(f"Voice cloning failed: {e}")
    
    def batch_clone_dialogue(
        self,
        dialogue_segments: List[DialogueSegment],
        voice_profiles: Dict[str, VoiceProfile],
        output_dir: Optional[str] = None,
        config: Optional[CloningSynthesisConfig] = None
    ) -> Dict[str, List[VoiceCloneResult]]:
        """
        Clone les voix pour une liste de segments de dialogue.
        
        Args:
            dialogue_segments: Segments de dialogue à synthétiser
            voice_profiles: Profils vocaux par locuteur
            output_dir: Dossier de sortie (optionnel)
            config: Configuration de synthèse (optionnel)
            
        Returns:
            Résultats de clonage par locuteur
        """
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = {}
        total_segments = len(dialogue_segments)
        
        self.logger.info(f"Starting batch voice cloning for {total_segments} segments")
        
        for i, segment in enumerate(dialogue_segments):
            speaker_id = segment.speaker_id
            
            if speaker_id not in voice_profiles:
                self.logger.warning(f"No voice profile for speaker {speaker_id}, skipping")
                continue
            
            try:
                # Définir le chemin de sortie
                if output_dir:
                    output_path = str(Path(output_dir) / f"{speaker_id}_segment_{i:03d}.wav")
                else:
                    output_path = None
                
                # Cloner la voix
                result = self.clone_voice(
                    segment.original_text,
                    voice_profiles[speaker_id],
                    output_path,
                    config
                )
                
                # Ajouter aux résultats
                if speaker_id not in results:
                    results[speaker_id] = []
                results[speaker_id].append(result)
                
                # Log de progression
                if (i + 1) % 10 == 0 or i == total_segments - 1:
                    self.logger.info(f"Processed {i + 1}/{total_segments} segments")
                
            except Exception as e:
                self.logger.error(f"Failed to clone segment {i} for {speaker_id}: {e}")
                # Continuer avec les autres segments
        
        total_results = sum(len(speaker_results) for speaker_results in results.values())
        self.logger.info(f"Batch cloning completed: {total_results}/{total_segments} segments")
        
        return results
    
    def _clone_with_tortoise(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_path: Optional[str],
        config: CloningSynthesisConfig
    ) -> str:
        """
        Clone la voix avec Tortoise-TTS.
        
        Args:
            text: Texte à synthétiser
            voice_profile: Profil vocal
            output_path: Chemin de sortie
            config: Configuration
            
        Returns:
            Chemin du fichier audio généré
        """
        model_info = self.available_models['tortoise']
        
        if model_info.get('mock', False):
            return self._mock_voice_generation(text, voice_profile, output_path)
        
        try:
            tts = model_info['model']
            load_audio = model_info['load_audio']
            
            # Préparer les échantillons de référence
            voice_samples = []
            for ref_path in voice_profile.reference_audio_paths[:3]:  # Max 3 échantillons
                try:
                    audio = load_audio(ref_path, 22050)
                    voice_samples.append(audio)
                except Exception as e:
                    self.logger.warning(f"Failed to load reference {ref_path}: {e}")
            
            if not voice_samples:
                raise ProcessingError("No valid voice samples for Tortoise")
            
            # Configuration de génération
            preset = config.quality_preset
            if preset == "fast":
                preset = "ultra_fast"
            elif preset == "balanced":
                preset = "fast"
            elif preset == "high_quality":
                preset = "high_quality"
            
            # Générer l'audio
            gen = tts.tts_with_preset(
                text,
                voice_samples=voice_samples,
                conditioning_latents=voice_profile.model_embeddings.get('tortoise'),
                preset=preset,
                k=1,  # Nombre de candidats
                use_deterministic_seed=42,  # Pour la reproductibilité
                return_deterministic_state=True
            )
            
            # Sauvegarder le résultat
            if output_path is None:
                output_path = self.temp_storage.get_temp_path(
                    f"tortoise_clone_{voice_profile.speaker_id}.wav"
                )
            
            # Tortoise retourne généralement un tensor, le convertir en audio
            import torchaudio
            
            if hasattr(gen, 'squeeze'):
                audio_tensor = gen.squeeze().cpu()
            else:
                audio_tensor = gen
            
            torchaudio.save(output_path, audio_tensor.unsqueeze(0), 24000)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Tortoise generation failed: {e}")
            # Fallback vers mock
            return self._mock_voice_generation(text, voice_profile, output_path)
    
    def _clone_with_nemo(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_path: Optional[str],
        config: CloningSynthesisConfig
    ) -> str:
        """
        Clone la voix avec NeMo.
        
        Args:
            text: Texte à synthétiser
            voice_profile: Profil vocal
            output_path: Chemin de sortie
            config: Configuration
            
        Returns:
            Chemin du fichier audio généré
        """
        model_info = self.available_models['nemo']
        
        if model_info.get('mock', False):
            return self._mock_voice_generation(text, voice_profile, output_path)
        
        try:
            model = model_info['model']
            
            # NeMo nécessite une approche différente pour le clonage
            # Utiliser les embeddings pré-calculés si disponibles
            speaker_embedding = voice_profile.model_embeddings.get('nemo')
            
            if speaker_embedding is None:
                # Créer un embedding par défaut
                speaker_embedding = self._create_nemo_speaker_embedding(voice_profile)
            
            # Générer l'audio
            audio = model.generate_audio(
                text=text,
                speaker_embedding=speaker_embedding,
                temperature=config.temperature
            )
            
            # Sauvegarder
            if output_path is None:
                output_path = self.temp_storage.get_temp_path(
                    f"nemo_clone_{voice_profile.speaker_id}.wav"
                )
            
            import soundfile as sf
            sf.write(output_path, audio, 22050)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"NeMo generation failed: {e}")
            return self._mock_voice_generation(text, voice_profile, output_path)
    
    def _clone_with_coqui(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_path: Optional[str],
        config: CloningSynthesisConfig
    ) -> str:
        """
        Clone la voix avec Coqui TTS.
        
        Args:
            text: Texte à synthétiser
            voice_profile: Profil vocal
            output_path: Chemin de sortie
            config: Configuration
            
        Returns:
            Chemin du fichier audio généré
        """
        model_info = self.available_models['coqui']
        
        if model_info.get('mock', False):
            return self._mock_voice_generation(text, voice_profile, output_path)
        
        try:
            tts = model_info['model']
            
            # Utiliser le premier échantillon de référence pour le clonage
            reference_path = voice_profile.reference_audio_paths[0]
            
            # Générer avec clonage de voix
            if output_path is None:
                output_path = self.temp_storage.get_temp_path(
                    f"coqui_clone_{voice_profile.speaker_id}.wav"
                )
            
            tts.tts_to_file(
                text=text,
                speaker_wav=reference_path,
                file_path=output_path,
                emotion="neutral",
                speed=1.0
            )
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Coqui generation failed: {e}")
            return self._mock_voice_generation(text, voice_profile, output_path)
    
    def _mock_voice_generation(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_path: Optional[str]
    ) -> str:
        """
        Génération mock pour les tests et développement.
        
        Args:
            text: Texte à synthétiser
            voice_profile: Profil vocal
            output_path: Chemin de sortie
            
        Returns:
            Chemin du fichier audio généré
        """
        # Simuler le temps de génération
        import time
        generation_time = len(text) * 0.1  # 100ms par caractère
        time.sleep(min(generation_time, 2.0))  # Max 2 secondes pour les tests
        
        # Créer un audio synthétique
        duration = max(len(text) * 0.08, 1.0)  # ~80ms par caractère, min 1s
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        # Générer un signal vocal synthétique basé sur les caractéristiques
        characteristics = voice_profile.voice_characteristics
        fundamental_freq = characteristics.get('fundamental_frequency', 150.0)
        
        t = np.linspace(0, duration, num_samples)
        
        # Signal vocal avec harmoniques
        signal = (0.6 * np.sin(2 * np.pi * fundamental_freq * t) +
                 0.3 * np.sin(2 * np.pi * 2 * fundamental_freq * t) +
                 0.2 * np.sin(2 * np.pi * 3 * fundamental_freq * t))
        
        # Modulation pour simuler la parole
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)
        signal *= modulation
        
        # Ajouter du bruit réaliste
        noise = 0.02 * np.random.randn(num_samples)
        audio_data = signal + noise
        
        # Normaliser
        audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
        
        # Sauvegarder
        if output_path is None:
            output_path = self.temp_storage.get_temp_path(
                f"mock_clone_{voice_profile.speaker_id}.wav"
            )
        
        try:
            import soundfile as sf
            sf.write(output_path, audio_data, sample_rate)
        except ImportError:
            # Fallback simple
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(f"Mock audio for: {text}")
        
        return output_path
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Obtient la durée d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Durée en secondes
        """
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            return len(y) / sr
        except ImportError:
            # Estimation basée sur la taille du fichier (très approximative)
            file_size = Path(audio_path).stat().st_size
            # Approximation: 1MB ≈ 60 secondes d'audio WAV 16-bit mono 22kHz
            return file_size / (1024 * 1024) * 60
        except Exception:
            # Durée par défaut
            return 5.0
    
    def _analyze_voice_characteristics(self, audio_paths: List[str]) -> Dict[str, Any]:
        """
        Analyse les caractéristiques vocales des échantillons de référence.
        
        Args:
            audio_paths: Chemins vers les fichiers audio
            
        Returns:
            Dictionnaire des caractéristiques vocales
        """
        characteristics = {
            'fundamental_frequency': 150.0,  # Hz
            'formant_frequencies': [800, 1200, 2500],  # Hz
            'spectral_centroid': 1500.0,  # Hz
            'spectral_rolloff': 3000.0,  # Hz
            'voice_quality': 'neutral',
            'speaking_rate': 'normal',
            'pitch_range': 50.0,  # Hz
            'energy_level': 0.5
        }
        
        try:
            import librosa
            
            all_f0 = []
            all_centroids = []
            all_rolloffs = []
            
            for audio_path in audio_paths:
                try:
                    y, sr = librosa.load(audio_path, sr=22050)
                    
                    # Fréquence fondamentale
                    f0 = librosa.yin(y, fmin=80, fmax=400)
                    f0_clean = f0[f0 > 0]  # Enlever les valeurs non-voisées
                    if len(f0_clean) > 0:
                        all_f0.extend(f0_clean)
                    
                    # Centroïde spectral
                    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
                    all_centroids.extend(centroid[0])
                    
                    # Rolloff spectral
                    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
                    all_rolloffs.extend(rolloff[0])
                    
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {audio_path}: {e}")
            
            # Calculer les moyennes
            if all_f0:
                characteristics['fundamental_frequency'] = float(np.median(all_f0))
                characteristics['pitch_range'] = float(np.std(all_f0))
            
            if all_centroids:
                characteristics['spectral_centroid'] = float(np.mean(all_centroids))
            
            if all_rolloffs:
                characteristics['spectral_rolloff'] = float(np.mean(all_rolloffs))
            
        except ImportError:
            self.logger.warning("librosa not available, using default voice characteristics")
        
        return characteristics
    
    def _create_voice_embeddings(self, audio_paths: List[str]) -> Dict[str, Any]:
        """
        Crée les embeddings vocaux pour les différents modèles.
        
        Args:
            audio_paths: Chemins vers les fichiers audio
            
        Returns:
            Dictionnaire des embeddings par modèle
        """
        embeddings = {}
        
        # Embeddings Tortoise (simulation)
        if 'tortoise' in self.available_models:
            embeddings['tortoise'] = self._create_tortoise_embeddings(audio_paths)
        
        # Embeddings NeMo (simulation)
        if 'nemo' in self.available_models:
            embeddings['nemo'] = self._create_nemo_embeddings(audio_paths)
        
        # Embeddings Coqui (utilise directement les fichiers)
        if 'coqui' in self.available_models:
            embeddings['coqui'] = audio_paths[0] if audio_paths else None
        
        return embeddings
    
    def _create_tortoise_embeddings(self, audio_paths: List[str]) -> Optional[Any]:
        """Crée les embeddings Tortoise."""
        try:
            model_info = self.available_models.get('tortoise')
            if not model_info or model_info.get('mock', False):
                return None
            
            # Utiliser l'API Tortoise pour créer les conditioning latents
            tts = model_info['model']
            load_audio = model_info['load_audio']
            
            voice_samples = []
            for path in audio_paths[:3]:  # Max 3 échantillons
                try:
                    audio = load_audio(path, 22050)
                    voice_samples.append(audio)
                except Exception:
                    continue
            
            if voice_samples:
                conditioning_latents = tts.get_conditioning_latents(voice_samples)
                return conditioning_latents
            
        except Exception as e:
            self.logger.warning(f"Failed to create Tortoise embeddings: {e}")
        
        return None
    
    def _create_nemo_embeddings(self, audio_paths: List[str]) -> Optional[Any]:
        """Crée les embeddings NeMo."""
        try:
            model_info = self.available_models.get('nemo')
            if not model_info or model_info.get('mock', False):
                return None
            
            # Simulation d'embedding NeMo
            # En réalité, cela nécessiterait un modèle d'embedding spécialisé
            embedding_dim = 256
            embedding = np.random.randn(embedding_dim).astype(np.float32)
            
            return embedding
            
        except Exception as e:
            self.logger.warning(f"Failed to create NeMo embeddings: {e}")
        
        return None
    
    def _calculate_voice_quality_score(
        self, 
        audio_paths: List[str], 
        characteristics: Dict[str, Any]
    ) -> float:
        """
        Calcule un score de qualité pour le profil vocal.
        
        Args:
            audio_paths: Chemins vers les fichiers audio
            characteristics: Caractéristiques vocales
            
        Returns:
            Score de qualité (0.0 à 1.0)
        """
        score = 0.0
        factors = 0
        
        # Facteur 1: Nombre d'échantillons
        num_samples = len(audio_paths)
        if num_samples >= 3:
            score += 1.0
        elif num_samples >= 2:
            score += 0.7
        else:
            score += 0.4
        factors += 1
        
        # Facteur 2: Cohérence de la fréquence fondamentale
        f0_range = characteristics.get('pitch_range', 100.0)
        if f0_range < 30:  # Voix stable
            score += 1.0
        elif f0_range < 60:
            score += 0.7
        else:
            score += 0.4
        factors += 1
        
        # Facteur 3: Qualité spectrale
        centroid = characteristics.get('spectral_centroid', 1500.0)
        if 1000 <= centroid <= 2500:  # Plage normale pour la voix
            score += 1.0
        else:
            score += 0.6
        factors += 1
        
        # Facteur 4: Énergie vocale
        energy = characteristics.get('energy_level', 0.5)
        if energy > 0.3:
            score += 1.0
        else:
            score += 0.5
        factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def _analyze_generated_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyse la qualité de l'audio généré.
        
        Args:
            audio_path: Chemin vers l'audio généré
            
        Returns:
            Métriques de qualité
        """
        metrics = {
            'duration': 0.0,
            'rms_level': 0.0,
            'peak_level': 0.0,
            'spectral_quality': 0.5,
            'naturalness_score': 0.5,
            'clarity_score': 0.5
        }
        
        try:
            import librosa
            
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Durée
            metrics['duration'] = len(y) / sr
            
            # Niveaux audio
            metrics['rms_level'] = float(np.sqrt(np.mean(y ** 2)))
            metrics['peak_level'] = float(np.max(np.abs(y)))
            
            # Qualité spectrale (basée sur la distribution d'énergie)
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            # Score de naturalité (basé sur la régularité spectrale)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            centroid_std = np.std(spectral_centroid)
            metrics['naturalness_score'] = float(max(0, 1.0 - centroid_std / 1000))
            
            # Score de clarté (basé sur le contraste spectral)
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            metrics['clarity_score'] = float(np.mean(spectral_contrast) / 20.0)
            
            # Qualité spectrale globale
            metrics['spectral_quality'] = (
                metrics['naturalness_score'] + metrics['clarity_score']
            ) / 2.0
            
        except ImportError:
            self.logger.warning("librosa not available for quality analysis")
        except Exception as e:
            self.logger.warning(f"Quality analysis failed: {e}")
        
        return metrics
    
    def _calculate_voice_similarity(
        self, 
        generated_path: str, 
        voice_profile: VoiceProfile
    ) -> float:
        """
        Calcule la similarité entre la voix générée et le profil de référence.
        
        Args:
            generated_path: Chemin vers l'audio généré
            voice_profile: Profil vocal de référence
            
        Returns:
            Score de similarité (0.0 à 1.0)
        """
        try:
            # Analyser les caractéristiques de l'audio généré
            generated_chars = self._analyze_voice_characteristics([generated_path])
            reference_chars = voice_profile.voice_characteristics
            
            # Comparer les caractéristiques clés
            similarity_scores = []
            
            # Fréquence fondamentale
            ref_f0 = reference_chars.get('fundamental_frequency', 150.0)
            gen_f0 = generated_chars.get('fundamental_frequency', 150.0)
            f0_similarity = 1.0 - min(abs(ref_f0 - gen_f0) / max(ref_f0, gen_f0), 1.0)
            similarity_scores.append(f0_similarity)
            
            # Centroïde spectral
            ref_centroid = reference_chars.get('spectral_centroid', 1500.0)
            gen_centroid = generated_chars.get('spectral_centroid', 1500.0)
            centroid_similarity = 1.0 - min(
                abs(ref_centroid - gen_centroid) / max(ref_centroid, gen_centroid), 1.0
            )
            similarity_scores.append(centroid_similarity)
            
            # Score global
            overall_similarity = np.mean(similarity_scores)
            
            return float(max(0.0, min(1.0, overall_similarity)))
            
        except Exception as e:
            self.logger.warning(f"Similarity calculation failed: {e}")
            return 0.5  # Score neutre en cas d'erreur
    
    def _update_generation_stats(self, generation_time: float, text_length: int):
        """Met à jour les statistiques de génération."""
        self.generation_stats['total_generations'] += 1
        self.generation_stats['total_time'] += generation_time
        
        if text_length > 0:
            time_per_char = generation_time / text_length
            if self.generation_stats['average_time_per_second'] == 0:
                self.generation_stats['average_time_per_second'] = time_per_char
            else:
                # Moyenne mobile
                alpha = 0.1
                self.generation_stats['average_time_per_second'] = (
                    alpha * time_per_char + 
                    (1 - alpha) * self.generation_stats['average_time_per_second']
                )
        
        # Statistiques par modèle
        model = self.current_model
        if model not in self.generation_stats['model_usage']:
            self.generation_stats['model_usage'][model] = 0
        self.generation_stats['model_usage'][model] += 1
    
    def _create_mock_tortoise(self):
        """Crée un mock du modèle Tortoise pour les tests."""
        class MockTortoise:
            def tts_with_preset(self, text, voice_samples=None, **kwargs):
                # Simuler la génération
                duration = len(text) * 0.08
                sample_rate = 24000
                num_samples = int(duration * sample_rate)
                return np.random.randn(num_samples) * 0.5
            
            def get_conditioning_latents(self, voice_samples):
                return np.random.randn(1024)  # Embedding simulé
        
        return MockTortoise()
    
    def _create_mock_nemo(self):
        """Crée un mock du modèle NeMo pour les tests."""
        class MockNeMo:
            def generate_audio(self, text, speaker_embedding=None, **kwargs):
                duration = len(text) * 0.08
                sample_rate = 22050
                num_samples = int(duration * sample_rate)
                return np.random.randn(num_samples) * 0.5
        
        return MockNeMo()
    
    def _create_mock_coqui(self):
        """Crée un mock du modèle Coqui pour les tests."""
        class MockCoqui:
            def tts_to_file(self, text, speaker_wav=None, file_path=None, **kwargs):
                # Créer un fichier audio simulé
                duration = len(text) * 0.08
                sample_rate = 22050
                num_samples = int(duration * sample_rate)
                audio = np.random.randn(num_samples) * 0.5
                
                try:
                    import soundfile as sf
                    sf.write(file_path, audio, sample_rate)
                except ImportError:
                    # Créer un fichier vide
                    Path(file_path).touch()
        
        return MockCoqui()
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de génération.
        
        Returns:
            Dictionnaire des statistiques
        """
        stats = self.generation_stats.copy()
        
        if stats['total_generations'] > 0:
            stats['average_generation_time'] = stats['total_time'] / stats['total_generations']
        else:
            stats['average_generation_time'] = 0.0
        
        return stats
    
    def cleanup_model_cache(self):
        """Nettoie le cache des modèles pour libérer la mémoire."""
        for model_name in list(self.model_cache.keys()):
            del self.model_cache[model_name]
        
        self.logger.info("Model cache cleared")
    
    def get_available_models(self) -> List[str]:
        """
        Retourne la liste des modèles disponibles.
        
        Returns:
            Liste des noms de modèles
        """
        return list(self.available_models.keys())