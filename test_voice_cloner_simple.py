#!/usr/bin/env python3
"""
Test simple du système de clonage de voix.
"""

import numpy as np
from pathlib import Path

from ai_video_dubbing.processors.voice_cloner import VoiceCloner, CloningSynthesisConfig
from ai_video_dubbing.models.data_models import DialogueSegment
from ai_video_dubbing.utils.temp_storage import TempStorage


def create_test_audio_files(temp_storage: TempStorage) -> list:
    """Crée des fichiers audio de test pour les références vocales."""
    audio_paths = []
    
    for i in range(3):
        # Créer des données audio simulées pour différentes voix
        duration = 6.0 + i  # Durées variables
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        # Simuler des caractéristiques vocales différentes
        if i == 0:  # Voix masculine grave
            f0 = 120
            harmonics = [0.6, 0.4, 0.25, 0.15, 0.1]
        elif i == 1:  # Voix féminine aiguë
            f0 = 220
            harmonics = [0.5, 0.35, 0.2, 0.12, 0.08]
        else:  # Voix mixte
            f0 = 180
            harmonics = [0.55, 0.38, 0.22, 0.13, 0.09]
        
        # Générer le signal vocal
        t = np.linspace(0, duration, num_samples)
        signal = np.zeros(num_samples)
        
        for h, amplitude in enumerate(harmonics, 1):
            signal += amplitude * np.sin(2 * np.pi * f0 * h * t)
        
        # Modulation d'amplitude pour simuler la parole
        envelope = 0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * t))
        signal *= envelope
        
        # Ajouter du bruit réaliste
        noise = 0.02 * np.random.randn(num_samples)
        audio_data = signal + noise
        
        # Normaliser
        audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
        
        # Sauvegarder
        audio_path = temp_storage.get_temp_path(f"reference_voice_{i}.wav")
        
        try:
            import soundfile as sf
            sf.write(audio_path, audio_data, sample_rate)
            print(f"    * Créé: {Path(audio_path).name} ({duration:.1f}s, f0={f0}Hz)")
        except ImportError:
            # Créer un fichier avec une taille simulée pour les tests sans soundfile
            with open(audio_path, 'w') as f:
                # Écrire des données simulées proportionnelles à la durée
                fake_data = "x" * int(duration * 1000)  # Simuler des données audio
                f.write(fake_data)
            print(f"    * Créé (mock): {Path(audio_path).name} ({duration:.1f}s simulées)")
        
        audio_paths.append(audio_path)
    
    return audio_paths


def test_voice_cloner():
    """Test simple du système de clonage de voix."""
    
    print("🎤 Test du système de clonage de voix")
    
    # Créer le cloneur
    temp_storage = TempStorage()
    cloner = VoiceCloner(temp_storage)
    
    print(f"✓ Cloneur initialisé")
    print(f"  - Modèle par défaut: {cloner.default_config.model_name}")
    print(f"  - Qualité par défaut: {cloner.default_config.quality_preset}")
    print(f"  - Température: {cloner.default_config.temperature}")
    
    # Test d'initialisation des modèles
    print("\n🔧 Test d'initialisation des modèles...")
    
    models_to_test = ["tortoise", "nemo", "coqui"]
    initialized_models = []
    
    for model_name in models_to_test:
        success = cloner.initialize_model(model_name)
        if success:
            initialized_models.append(model_name)
            print(f"  ✓ {model_name}: Initialisé avec succès")
        else:
            print(f"  ✗ {model_name}: Échec d'initialisation")
    
    print(f"  📊 Modèles disponibles: {initialized_models}")
    
    # Créer des fichiers audio de référence
    print("\n🎵 Création des fichiers audio de référence...")
    
    reference_files = create_test_audio_files(temp_storage)
    print(f"  ✓ {len(reference_files)} fichiers de référence créés")
    
    # Test d'analyse des caractéristiques vocales
    print("\n📊 Test d'analyse des caractéristiques vocales...")
    
    characteristics = cloner._analyze_voice_characteristics(reference_files)
    
    print(f"  ✓ Caractéristiques analysées:")
    print(f"    - Fréquence fondamentale: {characteristics['fundamental_frequency']:.1f}Hz")
    print(f"    - Centroïde spectral: {characteristics['spectral_centroid']:.0f}Hz")
    print(f"    - Plage de pitch: {characteristics['pitch_range']:.1f}Hz")
    print(f"    - Niveau d'énergie: {characteristics['energy_level']:.3f}")
    print(f"    - Qualité vocale: {characteristics['voice_quality']}")
    print(f"    - Vitesse de parole: {characteristics['speaking_rate']}")
    
    # Test de création de profil vocal
    print("\n👤 Test de création de profil vocal...")
    
    voice_profile = cloner.create_voice_profile(
        speaker_id="SPEAKER_TEST",
        reference_audio_paths=reference_files,
        min_duration=1.0,  # Durée minimale réduite pour les tests
        max_duration=30.0
    )
    
    print(f"  ✓ Profil vocal créé:")
    print(f"    - Locuteur: {voice_profile.speaker_id}")
    print(f"    - Fichiers de référence: {len(voice_profile.reference_audio_paths)}")
    print(f"    - Durée totale: {voice_profile.total_reference_duration:.1f}s")
    print(f"    - Score de qualité: {voice_profile.quality_score:.3f}")
    print(f"    - Embeddings disponibles: {list(voice_profile.model_embeddings.keys())}")
    
    # Test de clonage de voix
    print("\n🎭 Test de clonage de voix...")
    
    if initialized_models:
        # Utiliser le premier modèle disponible
        model_name = initialized_models[0]
        print(f"  🔄 Utilisation du modèle: {model_name}")
        
        test_texts = [
            "Bonjour, ceci est un test de clonage de voix.",
            "La technologie de synthèse vocale permet de créer des voix artificielles.",
            "Ce système peut reproduire les caractéristiques uniques de chaque locuteur."
        ]
        
        clone_results = []
        
        for i, text in enumerate(test_texts):
            print(f"    🎯 Test {i+1}: '{text[:30]}...'")
            
            try:
                result = cloner.clone_voice(
                    text=text,
                    voice_profile=voice_profile,
                    output_path=None
                )
                
                clone_results.append(result)
                
                print(f"      ✓ Généré en {result.generation_time:.2f}s")
                print(f"      📁 Fichier: {Path(result.cloned_audio_path).name}")
                print(f"      🎯 Similarité: {result.voice_similarity_score:.3f}")
                print(f"      📊 Qualité RMS: {result.quality_metrics.get('rms_level', 0):.3f}")
                
            except Exception as e:
                print(f"      ✗ Erreur: {e}")
        
        print(f"  📈 Résultats du clonage: {len(clone_results)}/{len(test_texts)} réussis")
    
    # Test de configuration personnalisée
    print("\n⚙️ Test de configuration personnalisée...")
    
    custom_config = CloningSynthesisConfig(
        model_name="tortoise",
        quality_preset="high_quality",
        voice_conditioning_length=8.0,
        temperature=0.6,
        repetition_penalty=1.8,
        length_penalty=1.1,
        max_generation_length=25.0,
        use_deepspeed=False,
        batch_size=1
    )
    
    print(f"  ✓ Configuration personnalisée:")
    print(f"    - Qualité: {custom_config.quality_preset}")
    print(f"    - Température: {custom_config.temperature}")
    print(f"    - Longueur de conditionnement: {custom_config.voice_conditioning_length}s")
    
    if initialized_models:
        try:
            custom_result = cloner.clone_voice(
                text="Test avec configuration personnalisée pour une qualité optimale.",
                voice_profile=voice_profile,
                config=custom_config
            )
            
            print(f"    ✓ Génération personnalisée réussie:")
            print(f"      - Temps: {custom_result.generation_time:.2f}s")
            print(f"      - Similarité: {custom_result.voice_similarity_score:.3f}")
            
        except Exception as e:
            print(f"    ✗ Erreur de génération personnalisée: {e}")
    
    # Test de clonage par lot
    print("\n📦 Test de clonage par lot...")
    
    dialogue_segments = [
        DialogueSegment(
            speaker_id="SPEAKER_TEST",
            start_time=1.0,
            end_time=3.0,
            original_text="Premier segment de dialogue à cloner.",
            audio_path="",
            confidence_score=0.9
        ),
        DialogueSegment(
            speaker_id="SPEAKER_TEST",
            start_time=4.0,
            end_time=6.0,
            original_text="Deuxième segment avec un texte différent.",
            audio_path="",
            confidence_score=0.85
        ),
        DialogueSegment(
            speaker_id="SPEAKER_TEST",
            start_time=7.0,
            end_time=9.0,
            original_text="Troisième et dernier segment du dialogue.",
            audio_path="",
            confidence_score=0.88
        )
    ]
    
    voice_profiles = {
        "SPEAKER_TEST": voice_profile
    }
    
    if initialized_models:
        try:
            batch_results = cloner.batch_clone_dialogue(
                dialogue_segments=dialogue_segments,
                voice_profiles=voice_profiles,
                output_dir=None
            )
            
            print(f"  ✓ Clonage par lot réussi:")
            for speaker_id, results in batch_results.items():
                print(f"    - {speaker_id}: {len(results)} segments clonés")
                
                total_time = sum(r.generation_time for r in results)
                avg_similarity = sum(r.voice_similarity_score for r in results) / len(results)
                
                print(f"      * Temps total: {total_time:.2f}s")
                print(f"      * Similarité moyenne: {avg_similarity:.3f}")
        
        except Exception as e:
            print(f"  ✗ Erreur de clonage par lot: {e}")
    
    # Test des statistiques de génération
    print("\n📊 Test des statistiques de génération...")
    
    stats = cloner.get_generation_statistics()
    
    print(f"  ✓ Statistiques de génération:")
    print(f"    - Générations totales: {stats['total_generations']}")
    print(f"    - Temps total: {stats['total_time']:.2f}s")
    print(f"    - Temps moyen par génération: {stats.get('average_generation_time', 0):.2f}s")
    print(f"    - Temps moyen par seconde: {stats['average_time_per_second']:.3f}s/char")
    print(f"    - Utilisation des modèles: {stats['model_usage']}")
    
    # Test de validation de qualité
    print("\n🔍 Test de validation de qualité...")
    
    if clone_results:
        test_audio = clone_results[0].cloned_audio_path
        quality_metrics = cloner._analyze_generated_audio_quality(test_audio)
        
        print(f"  ✓ Métriques de qualité:")
        print(f"    - Durée: {quality_metrics['duration']:.2f}s")
        print(f"    - Niveau RMS: {quality_metrics['rms_level']:.4f}")
        print(f"    - Niveau de crête: {quality_metrics['peak_level']:.4f}")
        print(f"    - Qualité spectrale: {quality_metrics['spectral_quality']:.3f}")
        print(f"    - Score de naturalité: {quality_metrics['naturalness_score']:.3f}")
        print(f"    - Score de clarté: {quality_metrics['clarity_score']:.3f}")
    
    # Test de nettoyage
    print("\n🧹 Test de nettoyage...")
    
    available_models_before = len(cloner.get_available_models())
    cloner.cleanup_model_cache()
    available_models_after = len(cloner.get_available_models())
    
    print(f"  ✓ Cache nettoyé")
    print(f"    - Modèles avant: {available_models_before}")
    print(f"    - Modèles après: {available_models_after}")
    
    print(f"\n🎉 Tous les tests de clonage de voix sont terminés!")
    
    # Résumé final
    print(f"\n📋 Résumé des tests:")
    print(f"  - Modèles initialisés: {len(initialized_models)}")
    print(f"  - Profils vocaux créés: 1")
    print(f"  - Clonages individuels: {len(clone_results) if 'clone_results' in locals() else 0}")
    print(f"  - Segments par lot: {len(dialogue_segments)}")
    print(f"  - Générations totales: {stats['total_generations']}")
    
    # Nettoyage
    temp_storage.cleanup_all()
    print(f"🧹 Nettoyage terminé")


if __name__ == "__main__":
    test_voice_cloner()