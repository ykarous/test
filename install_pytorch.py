#!/usr/bin/env python3
"""
Script d'installation automatique de PyTorch selon le matériel disponible
"""
import subprocess
import sys
import os

def check_nvidia_gpu():
    """Vérifie si une GPU NVIDIA est disponible"""
    try:
        # Essayer d'importer torch pour vérifier CUDA
        try:
            import torch
            if torch.cuda.is_available():
                # PyTorch déjà installé avec CUDA
                return "12.1"  # Version par défaut
        except ImportError:
            pass
        
        # Essayer nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            if 'CUDA Version:' in output:
                # Extraire la version CUDA
                for line in output.split('\n'):
                    if 'CUDA Version:' in line:
                        cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                        return cuda_version
        return None
    except FileNotFoundError:
        return None

def install_pytorch():
    """Installe PyTorch selon le matériel détecté"""
    print("🔍 Détection du matériel...")
    
    # Vérifier si PyTorch est déjà installé
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} déjà installé")
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible: {torch.cuda.get_device_name(0)}")
        else:
            print("💻 Mode CPU activé")
        print("🎉 Aucune installation nécessaire!")
        return
    except ImportError:
        pass
    
    cuda_version = check_nvidia_gpu()
    
    if cuda_version:
        print(f"✅ GPU NVIDIA détectée avec CUDA {cuda_version}")
        
        # Choisir la version CUDA appropriée
        if cuda_version.startswith('13.') or cuda_version.startswith('12.'):
            install_cmd = [
                sys.executable, "-m", "pip", "install", 
                "torch>=2.5.0", "torchvision>=0.20.0", "torchaudio>=2.5.0",
                "--index-url", "https://download.pytorch.org/whl/cu121"
            ]
            print("📦 Installation de PyTorch avec CUDA 12.1...")
        elif cuda_version.startswith('11.'):
            install_cmd = [
                sys.executable, "-m", "pip", "install", 
                "torch>=2.5.0", "torchvision>=0.20.0", "torchaudio>=2.5.0",
                "--index-url", "https://download.pytorch.org/whl/cu118"
            ]
            print("📦 Installation de PyTorch avec CUDA 11.8...")
        else:
            install_cmd = [
                sys.executable, "-m", "pip", "install", 
                "torch>=2.5.0", "torchvision>=0.20.0", "torchaudio>=2.5.0",
                "--index-url", "https://download.pytorch.org/whl/cu121"
            ]
            print("⚠️  Version CUDA non reconnue, utilisation de CUDA 12.1...")
    else:
        install_cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch>=2.5.0", "torchvision>=0.20.0", "torchaudio>=2.5.0",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ]
        print("💻 Aucune GPU NVIDIA détectée, installation version CPU...")
    
    # Installer PyTorch
    try:
        print("🚀 Installation de PyTorch...")
        subprocess.run(install_cmd, check=True)
        
        print("✅ Installation PyTorch terminée avec succès!")
        
        # Test rapide
        print("🧪 Test de l'installation...")
        test_pytorch()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        print("💡 Essayez l'installation manuelle:")
        print("   pip install torch torchvision torchaudio")
        sys.exit(1)

def test_pytorch():
    """Test rapide de l'installation PyTorch"""
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} installé")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible: {torch.cuda.get_device_name(0)}")
        else:
            print("💻 Mode CPU activé")
            
    except ImportError as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    print("🎯 Installation automatique de PyTorch")
    print("=" * 40)
    install_pytorch()
    print("=" * 40)
    print("🎉 Installation terminée!")