# Installation PyTorch GPU/CPU

Ce guide vous aide à installer PyTorch avec le support GPU ou CPU selon votre matériel.

## 🚀 Installation Automatique (Recommandée)

### Windows
```bash
# Double-cliquer sur le fichier ou exécuter :
install_pytorch.bat
```

### Linux/Mac
```bash
python install_pytorch.py
```

## 🔧 Installation Manuelle

### 1. GPU avec CUDA 12.1 (RTX 30xx, 40xx, etc.)
```bash
pip install -r requirements_gpu_cuda121.txt
```

### 2. GPU avec CUDA 11.8 (RTX 20xx, GTX 16xx, etc.)
```bash
pip install -r requirements_gpu_cuda118.txt
```

### 3. CPU seulement
```bash
pip install -r requirements_cpu.txt
```

## 🧪 Vérification de l'installation

```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA disponible: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## 📋 Détection de votre matériel

### Vérifier CUDA
```bash
nvidia-smi
```

### Vérifier la version CUDA installée
```bash
nvcc --version
```

## 🔍 Compatibilité CUDA

| GPU Series | CUDA Version | Requirements File |
|------------|--------------|-------------------|
| RTX 40xx   | 12.1+        | requirements_gpu_cuda121.txt |
| RTX 30xx   | 12.1+        | requirements_gpu_cuda121.txt |
| RTX 20xx   | 11.8+        | requirements_gpu_cuda118.txt |
| GTX 16xx   | 11.8+        | requirements_gpu_cuda118.txt |
| Pas de GPU | N/A          | requirements_cpu.txt |

## ⚠️ Notes importantes

- **Windows** : Le problème SIGKILL de NeMo est automatiquement corrigé dans main.py
- **Performance** : GPU recommandé pour la transcription et diarisation
- **Mémoire** : GPU avec au moins 6GB VRAM recommandé pour NeMo
- **Fallback** : L'application fonctionne en mode CPU si GPU indisponible

## 🆘 Dépannage

### Erreur CUDA
```bash
# Réinstaller PyTorch CPU en cas de problème
pip install -r requirements_cpu.txt
```

### Erreur NeMo SIGKILL
Le patch est automatiquement appliqué dans main.py, aucune action requise.

### Vérification complète
```bash
python -c "import torch; import nemo; print('✅ Tout fonctionne!')"
```