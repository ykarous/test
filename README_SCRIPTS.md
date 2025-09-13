# 🚀 Scripts d'Installation et de Gestion

## 📋 Scripts Disponibles

### 🔧 Installation et Configuration

#### `install_dependencies.bat` ⭐ PRINCIPAL
**Installation complète de toutes les dépendances**
```batch
# Exécution
install_dependencies.bat

# Ce qu'il fait:
✅ Vérifie Python et pip
✅ Installe tous les packages Python requis
✅ Vérifie FFmpeg
✅ Teste les dépendances critiques
✅ Installation optionnelle de NeMo
✅ Crée les répertoires nécessaires
```

#### `test_installation.bat`
**Test complet de l'installation**
```batch
# Exécution
test_installation.bat

# Ce qu'il vérifie:
✅ Python et version
✅ Tous les packages critiques
✅ FFmpeg
✅ Support GPU (CUDA)
✅ Composants de l'application
✅ LM Studio (optionnel)
```

### 🚀 Utilisation

#### `start_application.bat` ⭐ DÉMARRAGE
**Lance l'application avec vérifications**
```batch
# Exécution
start_application.bat

# Ce qu'il fait:
✅ Vérifie les dépendances
✅ Configure l'environnement
✅ Teste les services optionnels
✅ Lance l'application principale
✅ Gère les erreurs de fermeture
```

### 🔄 Maintenance

#### `update_dependencies.bat`
**Met à jour tous les packages**
```batch
# Exécution
update_dependencies.bat

# Ce qu'il fait:
✅ Met à jour pip
✅ Met à jour tous les packages
✅ Mise à jour spéciale PyTorch
✅ Mise à jour optionnelle NeMo
✅ Nettoie les packages obsolètes
✅ Vérifie la compatibilité
```

#### `uninstall.bat`
**Désinstallation complète**
```batch
# Exécution
uninstall.bat

# Ce qu'il fait:
⚠️  Supprime tous les packages Python
⚠️  Supprime les modèles et cache
⚠️  Nettoie les répertoires
⚠️  Purge le cache pip
```

## 🎯 Ordre d'Utilisation Recommandé

### Première Installation
```batch
1. install_dependencies.bat    # Installation complète
2. test_installation.bat       # Vérification
3. start_application.bat       # Premier lancement
```

### Utilisation Quotidienne
```batch
start_application.bat          # Lancement normal
```

### Maintenance Périodique
```batch
update_dependencies.bat        # Mise à jour mensuelle
test_installation.bat          # Vérification après mise à jour
```

### En Cas de Problème
```batch
1. test_installation.bat       # Diagnostic
2. update_dependencies.bat     # Tentative de réparation
3. uninstall.bat              # Si nécessaire
4. install_dependencies.bat    # Réinstallation propre
```

## 🔍 Diagnostic des Erreurs

### Messages d'Erreur Courants

#### "Python n'est pas reconnu"
```
❌ Problème: Python pas dans le PATH
🔧 Solution: Réinstaller Python avec "Add to PATH"
```

#### "Package manquant après installation"
```
❌ Problème: Installation incomplète
🔧 Solution: Réexécuter install_dependencies.bat
```

#### "FFmpeg non détecté"
```
❌ Problème: FFmpeg pas installé ou pas dans PATH
🔧 Solution: Installation manuelle ou via Chocolatey
```

#### "Erreur de mémoire"
```
❌ Problème: RAM insuffisante
🔧 Solution: Fermer applications, utiliser modèles plus petits
```

### Logs et Informations

#### Où Trouver les Logs
```
📁 Logs d'application: ./logs/
📺 Logs d'installation: Affichés dans la console
🔧 Test complet: Résultats de test_installation.bat
```

#### Informations Système Utiles
```python
# Version Python
python --version

# Packages installés
pip list

# Support GPU
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Espace disque
dir
```

## 💡 Conseils d'Utilisation

### Performance Optimale
- Utilisez un SSD pour l'installation
- Fermez les applications inutiles avant le lancement
- Activez l'accélération GPU si disponible

### Sécurité
- Exécutez les scripts en tant qu'administrateur si nécessaire
- Sauvegardez vos projets avant les mises à jour
- Testez après chaque mise à jour majeure

### Dépannage
- Toujours commencer par `test_installation.bat`
- Vérifier l'espace disque disponible
- Redémarrer l'invite de commande après modifications PATH
- Consulter les logs pour les erreurs détaillées

## 📞 Support Technique

### Avant de Demander de l'Aide
1. ✅ Exécuter `test_installation.bat`
2. ✅ Noter les messages d'erreur exacts
3. ✅ Vérifier la configuration système
4. ✅ Tester avec `python main.py` directement

### Informations à Fournir
- Version Windows
- Résultat complet de `test_installation.bat`
- Messages d'erreur exacts
- Configuration matérielle (RAM, GPU)
- Étapes qui ont mené au problème