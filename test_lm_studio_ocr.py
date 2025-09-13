#!/usr/bin/env python3
"""
Test spécifique pour l'OCR avec LM Studio.
"""

import sys
import os
from pathlib import Path
import numpy as np
import cv2

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def create_test_image_with_text(text: str = "Hello World OCR Test", filename: str = "test_ocr_image.jpg"):
    """Crée une image de test avec du texte."""
    try:
        # Créer une image blanche
        img = np.ones((200, 600, 3), dtype=np.uint8) * 255
        
        # Ajouter du texte
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        color = (0, 0, 0)  # Noir
        thickness = 2
        
        # Calculer la position du texte pour le centrer
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (img.shape[1] - text_size[0]) // 2
        text_y = (img.shape[0] + text_size[1]) // 2
        
        cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)
        
        # Sauvegarder l'image
        cv2.imwrite(filename, img)
        print(f"✅ Image de test créée: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Erreur création image: {e}")
        return None

def test_lm_studio_ocr_basic():
    """Test basique de l'OCR LM Studio."""
    print("\n🔍 Test basique OCR LM Studio...")
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        # Test de connexion
        if not lm_manager.is_server_running():
            print("⚠️  Serveur LM Studio non détecté")
            print("💡 Assurez-vous que LM Studio est lancé avec un modèle multimodal")
            return False
        
        print("✅ Serveur LM Studio connecté")
        
        # Obtenir les modèles multimodaux
        multimodal_models = lm_manager.get_multimodal_models()
        print(f"📋 {len(multimodal_models)} modèles multimodaux trouvés")
        
        for model in multimodal_models:
            print(f"  🤖 {model['name']} - Qualité OCR: {model.get('ocr_quality', 'unknown')}")
        
        if not multimodal_models:
            print("⚠️  Aucun modèle multimodal disponible")
            print("💡 Chargez un modèle comme LLaVA, Qwen-VL, ou CogVLM dans LM Studio")
            return False
        
        # Tester avec le premier modèle disponible
        test_model = multimodal_models[0]
        print(f"\n🧪 Test avec le modèle: {test_model['name']}")
        
        # Créer une image de test
        test_image = create_test_image_with_text("LM Studio OCR Test 2024")
        if not test_image:
            return False
        
        try:
            # Test d'extraction OCR
            result = lm_manager.extract_text_from_image(test_image, test_model['name'])
            
            if result:
                print(f"✅ OCR réussi!")
                print(f"📝 Texte extrait: '{result['text']}'")
                print(f"🎯 Confiance: {result.get('confidence', 0):.2f}")
                print(f"⚙️  Méthode: {result.get('method', 'unknown')}")
                
                # Vérifier si le texte attendu est présent
                expected_text = "LM Studio OCR Test"
                if expected_text.lower() in result['text'].lower():
                    print("✅ Texte attendu détecté correctement")
                else:
                    print("⚠️  Texte attendu non détecté parfaitement")
                
                return True
            else:
                print("❌ Aucun résultat OCR")
                return False
                
        finally:
            # Nettoyer l'image de test
            if os.path.exists(test_image):
                os.unlink(test_image)
        
    except Exception as e:
        print(f"❌ Erreur test OCR: {e}")
        return False

def test_lm_studio_ocr_frames():
    """Test OCR LM Studio avec plusieurs frames."""
    print("\n🎬 Test OCR LM Studio avec frames multiples...")
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        if not lm_manager.is_server_running():
            print("⚠️  Serveur LM Studio non disponible")
            return False
        
        multimodal_models = lm_manager.get_multimodal_models()
        if not multimodal_models:
            print("⚠️  Aucun modèle multimodal disponible")
            return False
        
        test_model = multimodal_models[0]['name']
        
        # Créer plusieurs images de test
        test_frames = []
        test_texts = ["Frame 1: Hello", "Frame 2: World", "Frame 3: OCR Test"]
        
        for i, text in enumerate(test_texts):
            img_file = f"test_frame_{i}.jpg"
            if create_test_image_with_text(text, img_file):
                # Lire l'image avec OpenCV
                img = cv2.imread(img_file)
                test_frames.append({
                    "timestamp": i * 1.0,  # 1 seconde d'intervalle
                    "frame": img
                })
        
        try:
            print(f"🔄 Extraction OCR sur {len(test_frames)} frames...")
            
            # Test d'extraction sur plusieurs frames
            results = lm_manager.extract_text_from_frames(test_frames, test_model)
            
            print(f"✅ OCR terminé: {len(results)} résultats")
            
            for i, result in enumerate(results):
                print(f"  📝 Frame {i+1} ({result.get('timestamp', 0):.1f}s): '{result.get('text', '')}'")
                print(f"     🎯 Confiance: {result.get('confidence', 0):.2f}")
            
            return len(results) > 0
            
        finally:
            # Nettoyer les images de test
            for i in range(len(test_texts)):
                img_file = f"test_frame_{i}.jpg"
                if os.path.exists(img_file):
                    os.unlink(img_file)
        
    except Exception as e:
        print(f"❌ Erreur test frames: {e}")
        return False

def test_ai_model_manager_ocr_integration():
    """Test de l'intégration OCR dans le gestionnaire de modèles IA."""
    print("\n🤖 Test intégration OCR dans AIModelManager...")
    
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        ai_manager = AIModelManager()
        
        # Test des modèles OCR disponibles
        print("📋 Modèles OCR disponibles:")
        ocr_models = ai_manager.get_available_ocr_models()
        
        for source, models in ocr_models.items():
            if models:
                print(f"  📂 {source.upper()}:")
                for model in models:
                    status_icon = "✅" if model.get('status') == 'available' else "❌"
                    print(f"    {status_icon} {model['name']} - Qualité: {model.get('quality', 'unknown')}")
        
        # Test du meilleur modèle OCR
        best_model = ai_manager.get_best_ocr_model(prefer_quality=True)
        if best_model:
            print(f"\n🏆 Meilleur modèle OCR: {best_model['name']} ({best_model['framework']})")
            print(f"   Qualité: {best_model.get('quality', 'unknown')}, Vitesse: {best_model.get('speed', 'unknown')}")
        else:
            print("⚠️  Aucun modèle OCR disponible")
        
        # Test d'extraction sur une image simple
        test_image = create_test_image_with_text("AI Manager OCR Integration Test")
        if test_image:
            try:
                print(f"\n🧪 Test extraction avec le meilleur modèle...")
                result = ai_manager.extract_text_from_single_image(test_image)
                
                if result:
                    print(f"✅ Extraction réussie!")
                    print(f"📝 Texte: '{result['text']}'")
                    print(f"🎯 Confiance: {result.get('confidence', 0):.2f}")
                    print(f"⚙️  Modèle utilisé: {result.get('model_used', 'unknown')}")
                    print(f"🔧 Méthode: {result.get('method', 'unknown')}")
                    return True
                else:
                    print("❌ Aucun résultat d'extraction")
                    return False
                    
            finally:
                if os.path.exists(test_image):
                    os.unlink(test_image)
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 TESTS OCR LM STUDIO")
    print("=" * 50)
    
    tests = [
        ("OCR LM Studio basique", test_lm_studio_ocr_basic),
        ("OCR LM Studio frames", test_lm_studio_ocr_frames),
        ("Intégration AI Manager", test_ai_model_manager_ocr_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("RÉSUMÉ DES TESTS OCR LM STUDIO")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Tests réussis: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 Tous les tests OCR LM Studio sont passés!")
        print("   L'intégration OCR LM Studio est fonctionnelle.")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} test(s) ont échoué.")
        print("   Certaines fonctionnalités OCR peuvent être limitées.")
        print("\n💡 Conseils:")
        print("   - Vérifiez que LM Studio est lancé")
        print("   - Chargez un modèle multimodal (LLaVA, Qwen-VL, etc.)")
        print("   - Assurez-vous que le modèle supporte les images")
    else:
        print("\n❌ Tous les tests ont échoué.")
        print("   L'intégration OCR LM Studio nécessite une configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)