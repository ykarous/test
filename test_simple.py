#!/usr/bin/env python3
"""
Test simple de l'installation - Application de Doublage Vidéo par IA
"""

import sys
import subprocess

def test_package(package_name, description=""):
    """Teste l'importation d'un package."""
    try:
        __import__(package_name)
        print(f"✅ {package_name} - {description}")
        return True
    except ImportError:
        print(f"❌ {package_name} - {description} - MANQUANT")
        return False

def test_command(command, description=""):
    """Teste la disponibilité d'une commande système."""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ {command} - {description}")
            return True
        else:
            print(f"❌ {command} - {description} - NON FONCTIONNEL")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"❌ {command} - {description} - NON DÉTECTÉ")
        return False

def main():
    print("🧪 TEST SIMPLE D'INSTALLATION")
    print("=" * 50)
    
    # Test Python
    print(f"\n🐍 Python: {sys.version.split()[0]}")
    
    # Packages critiques
    print("\n📋 PACKAGES CRITIQUES:")
    critical_packages = [
        ('PyQt5', 'Interface graphique'),
        ('cv2', 'Traitement vidéo'),
        ('librosa', 'Traitement audio'),
        ('torch', 'Intelligence artificielle'),
        ('transformers', 'Modèles de langage'),
        ('whisper', 'Transcription'),
        ('numpy', 'Calculs numériques'),
        ('requests', 'Requêtes HTTP')
    ]
    
    critical_ok = True
    for package, desc in critical_packages:
        if not test_package(package, desc):
            critical_ok = False
    
    # Packages optionnels
    print("\n📋 PACKAGES OPTIONNELS:")
    optional_packages = [
        ('paddleocr', 'OCR PaddleOCR'),
        ('easyocr', 'OCR EasyOCR'),
        ('nemo', 'NVIDIA NeMo')
    ]
    
    for package, desc in optional_packages:
        test_package(package, desc)
    
    # Commandes système
    print("\n🔧 COMMANDES SYSTÈME:")
    test_command('ffmpeg', 'Traitement audio/vidéo')
    
    # Test GPU
    print("\n🎮 SUPPORT GPU:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible - {torch.cuda.get_device_name(0)}")
        else:
            print("⚪ Mode CPU seulement")
    except:
        print("❌ PyTorch non disponible")
    
    # Test composants application
    print("\n🧩 COMPOSANTS APPLICATION:")
    app_components = [
        ('ai_video_dubbing.processors.ai_model_manager', 'Gestionnaire IA'),
        ('ai_video_dubbing.processors.lm_studio_manager', 'LM Studio'),
        ('ai_video_dubbing.utils.model_discovery', 'Découverte modèles'),
        ('ai_video_dubbing.gui.main_window', 'Interface graphique')
    ]
    
    app_ok = True
    for component, desc in app_components:
        if not test_package(component, desc):
            app_ok = False
    
    # Test LM Studio (optionnel)
    print("\n🖥️  SERVICES OPTIONNELS:")
    try:
        import requests
        response = requests.get('http://localhost:1234/v1/models', timeout=3)
        if response.status_code == 200:
            models = response.json().get('data', [])
            print(f"✅ LM Studio connecté - {len(models)} modèles")
        else:
            print("⚠️  LM Studio répond mais avec erreur")
    except:
        print("⚪ LM Studio non détecté (normal si pas utilisé)")
    
    # Résumé
    print("\n" + "=" * 50)
    if critical_ok and app_ok:
        print("🎉 INSTALLATION RÉUSSIE!")
        print("✅ Tous les composants critiques sont fonctionnels")
        print("🚀 Vous pouvez lancer l'application")
        return True
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        if not critical_ok:
            print("⚠️  Des packages Python critiques sont manquants")
        if not app_ok:
            print("⚠️  Des composants de l'application sont manquants")
        print("🔧 Exécutez: install_dependencies.bat")
        return False

if __name__ == "__main__":
    success = main()
    input("\nAppuyez sur Entrée pour continuer...")
    sys.exit(0 if success else 1)