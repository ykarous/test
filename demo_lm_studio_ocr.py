#!/usr/bin/env python3
"""
Démonstration de l'OCR avec LM Studio pour l'application de doublage vidéo par IA.
"""

import os
import sys
import logging
from pathlib import Path
import numpy as np
import cv2

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Configure le logging pour la démonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_demo_images():
    """Crée des images de démonstration avec différents types de texte."""
    demo_images = []
    
    try:
        # Image 1: Texte simple
        img1 = np.ones((150, 500, 3), dtype=np.uint8) * 255
        cv2.putText(img1, "Simple Text Example", (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite("demo_simple.jpg", img1)
        demo_images.append(("demo_simple.jpg", "Texte simple"))
        
        # Image 2: Texte avec style
        img2 = np.ones((150, 600, 3), dtype=np.uint8) * 240
        cv2.putText(img2, "STYLED TEXT 2024", (80, 75), cv2.FONT_HERSHEY_COMPLEX, 1.2, (50, 50, 200), 3)
        cv2.imwrite("demo_styled.jpg", img2)
        demo_images.append(("demo_styled.jpg", "Texte stylisé"))
        
        # Image 3: Texte multilingue
        img3 = np.ones((200, 600, 3), dtype=np.uint8) * 250
        cv2.putText(img3, "Hello World", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img3, "Bonjour Monde", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img3, "Hola Mundo", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite("demo_multilingual.jpg", img3)
        demo_images.append(("demo_multilingual.jpg", "Texte multilingue"))
        
        # Image 4: Texte avec fond coloré
        img4 = np.ones((150, 500, 3), dtype=np.uint8)
        img4[:, :] = [100, 150, 200]  # Fond bleu
        cv2.putText(img4, "Colored Background", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite("demo_colored.jpg", img4)
        demo_images.append(("demo_colored.jpg", "Texte sur fond coloré"))
        
        print(f"✅ {len(demo_images)} images de démonstration créées")
        return demo_images
        
    except Exception as e:
        print(f"❌ Erreur création images: {e}")
        return []

def demo_lm_studio_connection():
    """Démontre la connexion et détection des modèles LM Studio."""
    print("\n" + "="*60)
    print("DÉMONSTRATION - CONNEXION LM STUDIO OCR")
    print("="*60)
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        print("\n1. Test de connexion LM Studio...")
        if lm_manager.is_server_running():
            print("✅ Serveur LM Studio détecté et accessible")
        else:
            print("❌ Serveur LM Studio non détecté")
            print("💡 Assurez-vous que LM Studio est lancé sur http://localhost:1234")
            return False
        
        print("\n2. Découverte des modèles multimodaux...")
        multimodal_models = lm_manager.get_multimodal_models()
        
        if multimodal_models:
            print(f"📋 {len(multimodal_models)} modèles multimodaux trouvés:")
            
            for model in multimodal_models:
                quality_icon = {"high": "🟢", "medium": "🟡", "basic": "🔴"}.get(
                    model.get('ocr_quality', 'basic'), "⚪"
                )
                print(f"  {quality_icon} {model['name']}")
                print(f"     📊 Qualité OCR: {model.get('ocr_quality', 'unknown')}")
                print(f"     🎯 Capacités: {', '.join(model.get('capabilities', []))}")
                print(f"     📦 Statut: {model.get('status', 'unknown')}")
        else:
            print("📭 Aucun modèle multimodal trouvé")
            print("💡 Chargez un modèle comme LLaVA, Qwen-VL, CogVLM, ou Phi-3-Vision")
            return False
        
        print("\n3. Test du meilleur modèle OCR...")
        best_model = lm_manager.get_best_ocr_model()
        if best_model:
            print(f"🏆 Meilleur modèle: {best_model['name']}")
            print(f"   📊 Qualité: {best_model.get('ocr_quality', 'unknown')}")
            
            # Test de capacité OCR
            test_result = lm_manager.test_ocr_capability(best_model['name'])
            if test_result.get('ocr_capable'):
                print("✅ Modèle capable d'OCR confirmé")
            else:
                print("⚠️  Capacité OCR non confirmée")
                if test_result.get('error_message'):
                    print(f"   Erreur: {test_result['error_message']}")
        
        return len(multimodal_models) > 0
        
    except Exception as e:
        print(f"❌ Erreur connexion LM Studio: {e}")
        return False

def demo_single_image_ocr():
    """Démontre l'OCR sur une seule image."""
    print("\n" + "="*60)
    print("DÉMONSTRATION - OCR IMAGE UNIQUE")
    print("="*60)
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        if not lm_manager.is_server_running():
            print("❌ LM Studio non disponible")
            return False
        
        multimodal_models = lm_manager.get_multimodal_models()
        if not multimodal_models:
            print("❌ Aucun modèle multimodal disponible")
            return False
        
        test_model = multimodal_models[0]['name']
        print(f"🤖 Utilisation du modèle: {test_model}")
        
        # Créer une image de test
        demo_images = create_demo_images()
        if not demo_images:
            return False
        
        print(f"\n📸 Test OCR sur {len(demo_images)} images...")
        
        success_count = 0
        
        for img_path, description in demo_images:
            try:
                print(f"\n🔍 Analyse: {description}")
                print(f"   📁 Fichier: {img_path}")
                
                result = lm_manager.extract_text_from_image(img_path, test_model)
                
                if result and result.get('text'):
                    print(f"   ✅ Texte extrait: '{result['text']}'")
                    print(f"   🎯 Confiance: {result.get('confidence', 0):.2f}")
                    success_count += 1
                else:
                    print(f"   ❌ Aucun texte détecté")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        print(f"\n📊 Résultats: {success_count}/{len(demo_images)} images traitées avec succès")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur OCR image unique: {e}")
        return False
    
    finally:
        # Nettoyer les images de test
        for img_path, _ in demo_images:
            if os.path.exists(img_path):
                os.unlink(img_path)

def demo_multiple_frames_ocr():
    """Démontre l'OCR sur plusieurs frames simulant une vidéo."""
    print("\n" + "="*60)
    print("DÉMONSTRATION - OCR FRAMES MULTIPLES")
    print("="*60)
    
    try:
        from ai_video_dubbing.processors.lm_studio_manager import LMStudioManager
        
        lm_manager = LMStudioManager()
        
        if not lm_manager.is_server_running():
            print("❌ LM Studio non disponible")
            return False
        
        multimodal_models = lm_manager.get_multimodal_models()
        if not multimodal_models:
            print("❌ Aucun modèle multimodal disponible")
            return False
        
        test_model = multimodal_models[0]['name']
        print(f"🤖 Utilisation du modèle: {test_model}")
        
        # Simuler des frames de vidéo avec sous-titres
        subtitle_frames = [
            "Bienvenue dans cette démonstration",
            "LM Studio peut extraire du texte",
            "À partir d'images et de vidéos",
            "Avec une grande précision",
            "Merci d'avoir regardé!"
        ]
        
        print(f"\n🎬 Simulation de {len(subtitle_frames)} frames de vidéo...")
        
        # Créer les frames
        frames_data = []
        frame_files = []
        
        for i, subtitle in enumerate(subtitle_frames):
            # Créer une image avec le sous-titre
            img = np.ones((100, 600, 3), dtype=np.uint8) * 20  # Fond sombre
            
            # Ajouter le texte (sous-titre)
            font_scale = 0.8
            thickness = 2
            color = (255, 255, 255)  # Blanc
            
            # Calculer la position pour centrer le texte
            text_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_y = (img.shape[0] + text_size[1]) // 2
            
            cv2.putText(img, subtitle, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            
            # Sauvegarder temporairement
            frame_file = f"frame_{i:03d}.jpg"
            cv2.imwrite(frame_file, img)
            frame_files.append(frame_file)
            
            # Préparer les données pour LM Studio
            frames_data.append({
                "timestamp": i * 2.0,  # 2 secondes par frame
                "frame": img
            })
        
        try:
            print("🔄 Extraction OCR en cours...")
            
            # Traitement OCR
            results = lm_manager.extract_text_from_frames(frames_data, test_model)
            
            print(f"✅ OCR terminé: {len(results)} résultats")
            
            # Afficher les résultats
            print("\n📝 Sous-titres extraits:")
            for i, result in enumerate(results):
                timestamp = result.get('timestamp', 0)
                text = result.get('text', '')
                confidence = result.get('confidence', 0)
                
                print(f"  🕐 {timestamp:04.1f}s: '{text}' (confiance: {confidence:.2f})")
                
                # Comparer avec le texte original
                original = subtitle_frames[i] if i < len(subtitle_frames) else ""
                if original.lower() in text.lower() or text.lower() in original.lower():
                    print(f"       ✅ Correspondance avec l'original")
                else:
                    print(f"       ⚠️  Différent de l'original: '{original}'")
            
            # Statistiques
            avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
            print(f"\n📊 Statistiques:")
            print(f"   🎯 Confiance moyenne: {avg_confidence:.2f}")
            print(f"   📈 Taux de détection: {len(results)}/{len(subtitle_frames)} frames")
            
            return len(results) > 0
            
        finally:
            # Nettoyer les fichiers temporaires
            for frame_file in frame_files:
                if os.path.exists(frame_file):
                    os.unlink(frame_file)
        
    except Exception as e:
        print(f"❌ Erreur OCR frames multiples: {e}")
        return False

def demo_ai_manager_integration():
    """Démontre l'intégration complète dans le gestionnaire de modèles IA."""
    print("\n" + "="*60)
    print("DÉMONSTRATION - INTÉGRATION AI MANAGER")
    print("="*60)
    
    try:
        from ai_video_dubbing.processors.ai_model_manager import AIModelManager
        
        print("\n1. Initialisation du gestionnaire IA...")
        ai_manager = AIModelManager()
        print("✅ Gestionnaire IA initialisé")
        
        print("\n2. Analyse des modèles OCR disponibles...")
        ocr_models = ai_manager.get_available_ocr_models()
        
        total_models = 0
        for source, models in ocr_models.items():
            if models:
                print(f"\n📂 {source.upper()}:")
                for model in models:
                    status_icon = "✅" if model.get('status') == 'available' else "❌"
                    quality_icon = {"high": "🟢", "good": "🟡", "medium": "🟡", "basic": "🔴"}.get(
                        model.get('quality', 'medium'), "⚪"
                    )
                    print(f"  {status_icon} {quality_icon} {model['name']}")
                    print(f"     📊 Qualité: {model.get('quality', 'unknown')}")
                    print(f"     ⚡ Vitesse: {model.get('speed', 'unknown')}")
                    print(f"     🌍 Langues: {', '.join(model.get('languages', ['unknown']))}")
                    total_models += 1
        
        print(f"\n📈 Total: {total_models} modèles OCR détectés")
        
        print("\n3. Sélection du meilleur modèle...")
        best_model = ai_manager.get_best_ocr_model(prefer_quality=True)
        
        if best_model:
            print(f"🏆 Meilleur modèle sélectionné: {best_model['name']}")
            print(f"   🔧 Framework: {best_model['framework']}")
            print(f"   📊 Qualité: {best_model.get('quality', 'unknown')}")
            print(f"   ⚡ Vitesse: {best_model.get('speed', 'unknown')}")
            
            # Test du modèle
            print(f"\n4. Test du modèle {best_model['name']}...")
            test_result = ai_manager.test_ocr_model(best_model['name'])
            
            if test_result.get('functional'):
                print("✅ Modèle fonctionnel confirmé")
                
                # Test d'extraction sur une image
                print("\n5. Test d'extraction OCR...")
                
                # Créer une image de test
                test_img = np.ones((120, 500, 3), dtype=np.uint8) * 255
                cv2.putText(test_img, "AI Manager OCR Test", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                test_image_path = "ai_manager_test.jpg"
                cv2.imwrite(test_image_path, test_img)
                
                try:
                    result = ai_manager.extract_text_from_single_image(test_image_path)
                    
                    if result and result.get('text'):
                        print(f"✅ Extraction réussie!")
                        print(f"   📝 Texte: '{result['text']}'")
                        print(f"   🎯 Confiance: {result.get('confidence', 0):.2f}")
                        print(f"   🤖 Modèle: {result.get('model_used', 'unknown')}")
                        print(f"   🔧 Méthode: {result.get('method', 'unknown')}")
                        
                        return True
                    else:
                        print("❌ Aucun texte extrait")
                        return False
                        
                finally:
                    if os.path.exists(test_image_path):
                        os.unlink(test_image_path)
            else:
                print("❌ Modèle non fonctionnel")
                if test_result.get('error_message'):
                    print(f"   Erreur: {test_result['error_message']}")
                return False
        else:
            print("❌ Aucun modèle OCR disponible")
            return False
        
    except Exception as e:
        print(f"❌ Erreur intégration AI Manager: {e}")
        return False

def demo_usage_examples():
    """Montre des exemples d'utilisation pratique."""
    print("\n" + "="*60)
    print("EXEMPLES D'UTILISATION PRATIQUE")
    print("="*60)
    
    print("\n1. 🖼️  OCR SUR IMAGE UNIQUE")
    print("   # Extraction automatique avec le meilleur modèle")
    print("   ai_manager = AIModelManager()")
    print("   result = ai_manager.extract_text_from_single_image('image.jpg')")
    print("   print(f\"Texte: {result['text']}\")")
    print()
    print("   # Utiliser un modèle LM Studio spécifique")
    print("   result = ai_manager.extract_text_from_single_image('image.jpg', 'llava-1.6-34b')")
    
    print("\n2. 🎬 OCR SUR FRAMES DE VIDÉO")
    print("   # Extraction sur plusieurs frames")
    print("   frames = video_processor.extract_frames('video.mp4')")
    print("   ocr_results = ai_manager.extract_text_from_frames(frames, 'lm-studio-qwen-vl')")
    print("   for result in ocr_results:")
    print("       print(f\"{result.timestamp}s: {result.text}\")")
    
    print("\n3. 🔍 DÉCOUVERTE ET SÉLECTION DE MODÈLES")
    print("   # Obtenir tous les modèles OCR")
    print("   ocr_models = ai_manager.get_available_ocr_models()")
    print()
    print("   # Sélectionner le meilleur modèle")
    print("   best_model = ai_manager.get_best_ocr_model(prefer_quality=True)")
    print("   print(f\"Meilleur modèle: {best_model['name']}\")")
    
    print("\n4. 🧪 TEST ET VALIDATION")
    print("   # Tester un modèle spécifique")
    print("   test_result = ai_manager.test_ocr_model('llava-1.5-7b')")
    print("   if test_result['functional']:")
    print("       print(\"Modèle prêt à utiliser\")")
    
    print("\n5. ⚙️  CONFIGURATION LM STUDIO")
    print("   # Gestionnaire LM Studio direct")
    print("   lm_manager = LMStudioManager()")
    print("   multimodal_models = lm_manager.get_multimodal_models()")
    print("   best_ocr = lm_manager.get_best_ocr_model()")

def main():
    """Fonction principale de démonstration."""
    setup_logging()
    
    print("🚀 DÉMONSTRATION - OCR AVEC LM STUDIO")
    print("Application de Doublage Vidéo par IA")
    print("="*60)
    
    # Tests des différents composants
    results = {
        "connection": demo_lm_studio_connection(),
        "single_image": demo_single_image_ocr(),
        "multiple_frames": demo_multiple_frames_ocr(),
        "ai_integration": demo_ai_manager_integration()
    }
    
    # Exemples d'utilisation
    demo_usage_examples()
    
    # Résumé final
    print("\n" + "="*60)
    print("RÉSUMÉ DE LA DÉMONSTRATION OCR")
    print("="*60)
    
    total_tests = len(results)
    successful_tests = sum(1 for success in results.values() if success)
    
    print(f"\n📊 Tests réussis: {successful_tests}/{total_tests}")
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        test_display = test_name.replace('_', ' ').title()
        print(f"  {status} {test_display}")
    
    if successful_tests == total_tests:
        print("\n🎉 Toutes les fonctionnalités OCR LM Studio fonctionnent!")
        print("   L'application peut maintenant utiliser des modèles multimodaux")
        print("   pour extraire du texte d'images et de vidéos avec LM Studio.")
    elif successful_tests > 0:
        print(f"\n⚠️  {total_tests - successful_tests} fonctionnalité(s) nécessite(nt) une configuration.")
        print("   Consultez les messages ci-dessus pour les détails.")
    else:
        print("\n❌ Aucune fonctionnalité OCR n'est opérationnelle.")
        print("   Vérifiez la configuration de LM Studio.")
    
    print("\n💡 CONSEILS POUR L'OCR LM STUDIO:")
    print("   1. Utilisez des modèles multimodaux récents (LLaVA 1.6, Qwen-VL, etc.)")
    print("   2. Les modèles plus grands offrent généralement une meilleure précision")
    print("   3. Ajustez le seuil de confiance selon vos besoins")
    print("   4. Testez avec différents types d'images pour valider la performance")

if __name__ == "__main__":
    main()