# 📥 Guide de Téléchargement des Modèles NeMo

## Vue d'ensemble

L'application dispose maintenant d'une interface intégrée pour télécharger et gérer les modèles NeMo directement depuis les paramètres.

## 🚀 Comment accéder au téléchargeur

1. **Lancer l'application** avec l'interface de téléchargement :
   ```bash
   .\start_app_with_models.bat
   ```

2. **Ouvrir les paramètres** dans l'application

3. **Aller à l'onglet "📥 Modèles NeMo"**

## 📦 Modèles disponibles

### ASR - Reconnaissance Vocale
- **nvidia/stt_en_fastconformer_ctc_large** (463MB)
  - Modèle FastConformer CTC pour l'anglais
  - Haute précision, optimisé pour la transcription
  
- **nvidia/stt_fr_fastconformer_ctc_large** (450MB)
  - Modèle FastConformer CTC pour le français
  - Spécialement entraîné pour le français

- **nvidia/stt_en_conformer_ctc_large** (400MB)
  - Modèle Conformer CTC classique pour l'anglais
  - Plus léger que FastConformer

### Multilingue - Plusieurs Langues
- **nvidia/stt_multilingual_fastconformer_hybrid_large_pc** (600MB)
  - Modèle multilingue avec support de nombreuses langues
  - Idéal pour du contenu multilingue

### Diarisation - Séparation Locuteurs
- **nvidia/speakerverification_en_titanet_large** (200MB)
  - Modèle de vérification et diarisation de locuteurs
  - Permet de distinguer différents locuteurs

### VAD - Détection Voix
- **nvidia/vad_multilingual_marblenet** (50MB)
  - Détection d'activité vocale multilingue
  - Très léger et efficace

## 🔧 Comment télécharger un modèle

1. **Sélectionner une catégorie** dans la liste déroulante
2. **Choisir un modèle spécifique**
3. **Cliquer sur "ℹ️ Info"** pour voir les détails du modèle
4. **Cliquer sur "📥 Télécharger le Modèle"**
5. **Confirmer le téléchargement** (attention à la taille !)
6. **Attendre la fin du téléchargement** (barre de progression)

## 📊 Gestion des modèles téléchargés

### Fonctionnalités disponibles :
- **🔄 Actualiser** : Met à jour la liste des modèles
- **🗑️ Supprimer** : Supprime un modèle de la liste
- **🧪 Tester** : Teste le fonctionnement d'un modèle

### Informations affichées :
- Nombre total de modèles téléchargés
- Répartition par type de modèle
- Statut de chaque modèle

## 🎯 Utilisation des modèles téléchargés

Une fois un modèle téléchargé :

1. **Il apparaît automatiquement** dans les listes de sélection
2. **Onglet "Modèles IA"** : Sélectionnable dans la liste ASR
3. **Onglet "Configuration"** : Disponible dans les modèles NeMo
4. **Utilisation immédiate** : Prêt pour la transcription

## 💾 Stockage des modèles

- **Cache local** : `~/.cache/huggingface/hub/`
- **Configuration** : `downloaded_nemo_models.json`
- **Réutilisation** : Les modèles téléchargés sont réutilisés automatiquement

## ⚠️ Points importants

### Taille des modèles
- Les modèles peuvent être volumineux (50MB à 600MB)
- Assurez-vous d'avoir suffisamment d'espace disque
- La première utilisation nécessite une connexion internet

### Performance
- **GPU recommandé** pour les gros modèles
- **CPU possible** mais plus lent
- **RAM** : Au moins 4GB recommandés

### Compatibilité
- **Windows** : Patch SIGKILL appliqué automatiquement
- **NeMo** : Version compatible installée
- **PyQt5** : Interface graphique moderne

## 🔍 Dépannage

### Erreur de téléchargement
- Vérifiez votre connexion internet
- Certains modèles peuvent nécessiter une authentification HuggingFace
- Essayez un modèle plus petit d'abord

### Modèle non visible
- Cliquez sur "🔄 Actualiser" dans la liste des modèles téléchargés
- Redémarrez l'application si nécessaire
- Vérifiez le fichier `downloaded_nemo_models.json`

### Erreur de chargement
- Vérifiez que le modèle est complètement téléchargé
- Essayez de le télécharger à nouveau
- Consultez les logs pour plus de détails

## 📝 Exemple d'utilisation

1. **Lancer** : `.\start_app_with_models.bat`
2. **Paramètres** → **📥 Modèles NeMo**
3. **Catégorie** : "ASR - Reconnaissance Vocale"
4. **Modèle** : "nvidia/stt_en_fastconformer_ctc_large"
5. **Télécharger** → **Confirmer** → **Attendre**
6. **Utiliser** : Onglet "Modèles IA" → Sélectionner le modèle téléchargé

## 🎉 Avantages

- **Interface intuitive** : Pas besoin de ligne de commande
- **Gestion centralisée** : Tous les modèles au même endroit
- **Intégration automatique** : Les modèles apparaissent dans les listes
- **Informations détaillées** : Taille, type, description de chaque modèle
- **Téléchargement sécurisé** : Avec barre de progression et gestion d'erreurs

---

**Note** : Cette fonctionnalité utilise les modèles officiels NVIDIA NeMo et respecte leurs conditions d'utilisation.