#!/usr/bin/env python3
"""Test CUDA après réinstallation PyTorch"""

def test_cuda():
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible: {torch.version.cuda}")
            print(f"✅ Nombre de GPUs: {torch.cuda.device_count()}")
            print(f"✅ GPU actuel: {torch.cuda.get_device_name()}")
            print(f"✅ Mémoire GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            
            # Test simple
            x = torch.randn(3, 3).cuda()
            print(f"✅ Test tensor GPU: {x.device}")
            
        else:
            print("❌ CUDA non disponible")
            
        return torch.cuda.is_available()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST CUDA APRÈS RÉINSTALLATION")
    print("=" * 40)
    success = test_cuda()
    print("=" * 40)
    if success:
        print("🎉 CUDA fonctionne parfaitement!")
    else:
        print("❌ Problème avec CUDA")