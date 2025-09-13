#!/usr/bin/env python3
"""
Test simple du gestionnaire de modèles IA.
"""

import tempfile
import time
from pathlib import Path

from ai_video_dubbing.processors.ai_model_manager import AIModelManager
from ai_video_dubbing.models.data_models import ModelType, ValidationError, ProcessingError


def test_ai_model_manager():
    """Test simple du gestionnaire de modèles IA."""
    print("=== Test du Gestionnaire de Modèles IA ===")
    
    # Créer un gestionnaire avec des limites de test
    manager = AIModelManager(max_memory_usage=0.8, cache_timeout=5)
    
    print(f"Gestionnaire initialisé:")
    print(f"  - Utilisation mémoire max: {manager.max_memory_usage * 100}%")
    print(f"  - Timeout cache: {manager.cache_timeout}s")
    
    # Test 1: Configuration des modèles
    print("\n1. Configuration des modèles supportés:")
    for model_type, models in manager._model_configs.items():
        print(f"   {model_type.value}:")
        for model_name, config in models.items():
            size = config.get('size', 'N/A')
            print(f"     - {model_name}: {size}MB")
    
    # Test 2: Estimation de taille de modèle
    print("\n2. Test estimation de taille:")
    test_cases = [
        (ModelType.ASR, "whisper-base"),
        (ModelType.ASR, "whisper-large-v3"),
        (ModelType.OCR, "paddleocr"),
        (ModelType.ASR, "modele-inconnu")
    ]
    
    for model_type, model_name in test_cases:
        size = manager._estimate_model_size(model_type, model_name)
        print(f"   {model_type.value}:{model_name} -> {size}MB")
    
    # Test 3: Génération de clés de modèles
    print("\n3. Test génération de clés:")
    for model_type, model_name in test_cases[:3]:
        key = manager._model_key(model_type, model_name)
        print(f"   {model_type.value}:{model_name} -> '{key}'")
    
    # Test 4: Statistiques mémoire
    print("\n4. Statistiques mémoire système:")
    try:
        stats = manager.get_memory_stats()
        print(f"   - Mémoire système: {stats['system_memory_percent']:.1f}%")
        if 'system_memory_total_mb' in stats:
            print(f"   - Mémoire totale: {stats['system_memory_total_mb']:.0f}MB")
            print(f"   - Mémoire disponible: {stats['system_memory_available_mb']:.0f}MB")
        print(f"   - Modèles chargés: {stats['models_count']}")
        print(f"   - Mémoire des modèles: {stats['models_memory_mb']:.1f}MB")
    except Exception as e:
        print(f"   ⚠️  Erreur statistiques: {e}")
    
    # Test 5: Chargement de modèle (simulation)
    print("\n5. Test chargement de modèle (simulation):")
    try:
        # Essayer de charger un modèle Whisper (échouera sans les dépendances)
        manager.load_model(ModelType.ASR, "whisper-base")
        print("   ✅ Modèle Whisper chargé")
    except ProcessingError as e:
        print(f"   ⚠️  Chargement Whisper échoué (attendu): {str(e)[:60]}...")
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    # Test 6: Chargement OCR
    print("\n6. Test chargement OCR (simulation):")
    try:
        manager.load_model(ModelType.OCR, "paddleocr")
        print("   ✅ Modèle PaddleOCR chargé")
    except ProcessingError as e:
        print(f"   ⚠️  Chargement PaddleOCR échoué (attendu): {str(e)[:60]}...")
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    # Test 7: Liste des modèles chargés
    print("\n7. Modèles actuellement chargés:")
    loaded_models = manager.get_loaded_models()
    if loaded_models:
        for model_key, info in loaded_models.items():
            print(f"   - {model_key}:")
            print(f"     Type: {info['model_type']}")
            print(f"     Mémoire: {info['memory_usage_mb']:.1f}MB")
            print(f"     Âge: {info['age_seconds']:.1f}s")
    else:
        print("   Aucun modèle chargé")
    
    # Test 8: Transcription audio (avec fichier inexistant)
    print("\n8. Test transcription audio:")
    try:
        result = manager.transcribe_audio("fichier_inexistant.wav")
        print("   ❌ Ne devrait pas réussir")
    except ValidationError as e:
        print(f"   ✅ Validation échouée comme attendu: {str(e)[:50]}...")
    except Exception as e:
        print(f"   ⚠️  Autre erreur: {e}")
    
    # Test 9: Extraction OCR (liste vide)
    print("\n9. Test extraction OCR:")
    try:
        result = manager.extract_text_from_frames([])
        print(f"   ✅ OCR sur liste vide: {len(result)} résultats")
    except Exception as e:
        print(f"   ❌ Erreur OCR: {e}")
    
    # Test 10: Méthode non implémentée
    print("\n10. Test méthode non implémentée:")
    try:
        result = manager.clone_voice("ref.wav", "texte")
        print("   ❌ Ne devrait pas réussir")
    except NotImplementedError:
        print("   ✅ NotImplementedError levée comme attendu")
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    # Test 11: Nettoyage
    print("\n11. Test nettoyage:")
    initial_count = len(manager._loaded_models)
    manager.cleanup_all()
    final_count = len(manager._loaded_models)
    print(f"   Modèles avant nettoyage: {initial_count}")
    print(f"   Modèles après nettoyage: {final_count}")
    
    # Test 12: Vérification des dépendances
    print("\n12. Dépendances disponibles:")
    
    # Vérifier PyTorch
    try:
        import torch
        print("   ✅ PyTorch disponible")
    except ImportError:
        print("   ⚠️  PyTorch non disponible")
    
    # Vérifier Whisper
    try:
        import whisper
        print("   ✅ Whisper disponible")
    except ImportError:
        print("   ⚠️  Whisper non disponible")
    
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
    
    # Vérifier psutil
    try:
        import psutil
        print("   ✅ psutil disponible")
    except ImportError:
        print("   ⚠️  psutil non disponible")
    
    print("\n✅ Tests du gestionnaire de modèles IA terminés!")


if __name__ == "__main__":
    test_ai_model_manager()