# Document d'Exigences - Amélioration Détection Modèles LM Studio

## Introduction

Cette spécification vise à améliorer la détection des modèles LM Studio pour l'OCR et la transcription. Le problème actuel est que l'application ne détecte que les modèles via l'API REST de LM Studio, mais n'affiche pas les modèles qui sont chargés localement dans LM Studio. Cette limitation empêche les utilisateurs de voir et sélectionner leurs modèles multimodaux (vision/OCR) disponibles.

## Exigences

### Exigence 1 - Détection Améliorée des Modèles Chargés

**Histoire Utilisateur :** En tant qu'utilisateur, je veux voir tous les modèles chargés dans LM Studio, afin de pouvoir sélectionner mes modèles multimodaux pour l'OCR même s'ils ne sont pas listés par l'API standard.

#### Critères d'Acceptation

1. QUAND l'application interroge LM Studio ALORS elle DOIT détecter les modèles actuellement chargés en mémoire
2. QUAND un modèle multimodal est chargé dans LM Studio ALORS il DOIT apparaître dans la liste des modèles OCR disponibles
3. QUAND l'API standard ne retourne pas de modèles ALORS le système DOIT utiliser des méthodes alternatives de détection
4. QUAND des modèles sont détectés ALORS le système DOIT identifier automatiquement leur type (ASR, OCR, multimodal)
5. QUAND la détection échoue ALORS le système DOIT permettre la saisie manuelle du nom du modèle

### Exigence 2 - Interface de Gestion des Modèles

**Histoire Utilisateur :** En tant qu'utilisateur, je veux une interface claire pour gérer mes modèles LM Studio, afin de facilement voir, tester et sélectionner les modèles appropriés pour chaque tâche.

#### Critères d'Acceptation

1. QUAND l'interface de configuration est ouverte ALORS elle DOIT afficher une liste actualisée des modèles LM Studio
2. QUAND l'utilisateur clique sur "Actualiser" ALORS le système DOIT re-scanner tous les modèles disponibles
3. QUAND un modèle est sélectionné ALORS l'interface DOIT afficher ses capacités (OCR, transcription, multimodal)
4. QUAND l'utilisateur teste un modèle ALORS le système DOIT vérifier sa disponibilité et ses capacités
5. QUAND aucun modèle n'est détecté ALORS l'interface DOIT proposer un champ de saisie manuelle

### Exigence 3 - Détection Multi-Méthodes

**Histoire Utilisateur :** En tant que développeur, je veux que le système utilise plusieurs méthodes de détection, afin d'assurer une détection robuste des modèles même si l'API principale échoue.

#### Critères d'Acceptation

1. QUAND la détection démarre ALORS le système DOIT essayer l'API REST standard en premier
2. SI l'API REST échoue ALORS le système DOIT essayer l'endpoint de statut des modèles
3. SI les endpoints échouent ALORS le système DOIT scanner les processus LM Studio actifs
4. QUAND plusieurs méthodes sont utilisées ALORS le système DOIT fusionner les résultats sans doublons
5. QUAND toutes les méthodes échouent ALORS le système DOIT permettre la configuration manuelle

### Exigence 4 - Cache et Performance

**Histoire Utilisateur :** En tant qu'utilisateur, je veux que la détection des modèles soit rapide et efficace, afin de ne pas attendre longtemps lors de l'actualisation de la liste.

#### Critères d'Acceptation

1. QUAND des modèles sont détectés ALORS le système DOIT les mettre en cache pour 5 minutes
2. QUAND l'utilisateur actualise rapidement ALORS le système DOIT utiliser le cache si disponible
3. QUAND le cache expire ALORS le système DOIT automatiquement re-scanner les modèles
4. QUAND la détection prend du temps ALORS l'interface DOIT afficher une barre de progression
5. QUAND la détection est terminée ALORS le système DOIT notifier l'utilisateur du nombre de modèles trouvés

### Exigence 5 - Validation et Test des Modèles

**Histoire Utilisateur :** En tant qu'utilisateur, je veux pouvoir tester mes modèles avant de les utiliser, afin de m'assurer qu'ils fonctionnent correctement pour l'OCR.

#### Critères d'Acceptation

1. QUAND un modèle est détecté ALORS le système DOIT permettre de tester ses capacités OCR
2. QUAND un test OCR est lancé ALORS le système DOIT utiliser une image de test simple
3. QUAND le test réussit ALORS le système DOIT afficher le texte extrait et marquer le modèle comme fonctionnel
4. QUAND le test échoue ALORS le système DOIT afficher l'erreur et suggérer des solutions
5. QUAND plusieurs modèles sont testés ALORS le système DOIT recommander le meilleur pour l'OCR

### Exigence 6 - Configuration Persistante

**Histoire Utilisateur :** En tant qu'utilisateur, je veux que mes sélections de modèles soient sauvegardées, afin de ne pas avoir à reconfigurer à chaque utilisation.

#### Critères d'Acceptation

1. QUAND un modèle LM Studio est sélectionné ALORS le système DOIT sauvegarder ce choix
2. QUAND l'application redémarre ALORS elle DOIT restaurer les modèles sélectionnés précédemment
3. QUAND un modèle sauvegardé n'est plus disponible ALORS le système DOIT proposer des alternatives
4. QUAND la configuration est exportée ALORS elle DOIT inclure les paramètres LM Studio
5. QUAND la configuration est importée ALORS elle DOIT valider la disponibilité des modèles LM Studio

### Exigence 7 - Gestion des Erreurs et Fallbacks

**Histoire Utilisateur :** En tant qu'utilisateur, je veux que le système gère gracieusement les erreurs de connexion LM Studio, afin de continuer à utiliser l'application même si LM Studio a des problèmes.

#### Critères d'Acceptation

1. QUAND LM Studio n'est pas accessible ALORS le système DOIT afficher un message clair et proposer des alternatives
2. QUAND un modèle sélectionné devient indisponible ALORS le système DOIT basculer vers un modèle de fallback
3. QUAND la connexion LM Studio est instable ALORS le système DOIT implémenter des tentatives de reconnexion
4. QUAND les erreurs persistent ALORS le système DOIT permettre de désactiver temporairement LM Studio
5. QUAND LM Studio redevient disponible ALORS le système DOIT automatiquement réactiver la détection