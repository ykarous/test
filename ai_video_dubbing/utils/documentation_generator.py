#!/usr/bin/env python3
"""
Générateur de documentation pour l'application de doublage vidéo par IA.
Crée automatiquement la documentation utilisateur et les exemples d'utilisation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.data_models import ProcessingResults, PipelineConfig


class DocumentationGenerator:
    """Générateur de documentation automatique."""
    
    def __init__(self, output_dir: str = "./docs"):
        """
        Initialise le générateur de documentation.
        
        Args:
            output_dir: Répertoire de sortie pour la documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Documentation generator initialized")
    
    def generate_complete_documentation(self, 
                                      results: ProcessingResults,
                                      config: PipelineConfig,
                                      export_results: Dict[str, str] = None,
                                      quality_validation: Dict[str, Any] = None) -> List[str]:
        """
        Génère la documentation complète.
        
        Args:
            results: Résultats du traitement
            config: Configuration utilisée
            export_results: Résultats d'export
            quality_validation: Résultats de validation qualité
            
        Returns:
            Liste des chemins des fichiers de documentation créés
        """
        try:
            self.logger.info("Generating complete documentation")
            
            doc_files = []
            
            # 1. Guide utilisateur principal
            user_guide = self._generate_user_guide(results, config, export_results)
            if user_guide:
                doc_files.append(user_guide)
            
            # 2. Rapport technique détaillé
            technical_report = self._generate_technical_report(results, config, quality_validation)
            if technical_report:
                doc_files.append(technical_report)
            
            # 3. Exemples d'utilisation
            usage_examples = self._generate_usage_examples(config)
            if usage_examples:
                doc_files.append(usage_examples)
            
            # 4. FAQ et dépannage
            faq_guide = self._generate_faq_guide()
            if faq_guide:
                doc_files.append(faq_guide)
            
            # 5. Spécifications techniques
            tech_specs = self._generate_technical_specifications(results)
            if tech_specs:
                doc_files.append(tech_specs)
            
            # 6. Guide de configuration
            config_guide = self._generate_configuration_guide()
            if config_guide:
                doc_files.append(config_guide)
            
            self.logger.info(f"Generated {len(doc_files)} documentation files")
            return doc_files
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return []
    
    def _generate_user_guide(self, 
                           results: ProcessingResults,
                           config: PipelineConfig,
                           export_results: Dict[str, str] = None) -> str:
        """Génère le guide utilisateur principal."""
        try:
            guide_path = self.output_dir / "GUIDE_UTILISATEUR.md"
            
            content = [
                "# Guide Utilisateur - Doublage Vidéo par IA",
                "",
                "## Vue d'ensemble",
                "",
                "Cette application utilise l'intelligence artificielle pour automatiser le processus de doublage vidéo.",
                "Elle analyse votre vidéo, extrait les dialogues, et génère automatiquement une nouvelle version doublée.",
                "",
                "## Résultats de votre traitement",
                "",
                f"**Fichier traité :** `{Path(results.output_video_path).name}`",
                f"**Temps de traitement :** {results.processing_time:.1f} secondes",
                f"**Locuteurs détectés :** {results.speakers_detected}",
                f"**Segments de dialogue :** {results.dialogue_segments}",
                "",
                "## Fichiers générés",
                "",
            ]
            
            if export_results:
                content.append("### Formats vidéo disponibles")
                content.append("")
                
                format_descriptions = {
                    'main_output': 'Vidéo principale (qualité équilibrée) - **Recommandé pour usage général**',
                    'high_quality': 'Vidéo haute qualité (fichier plus volumineux) - Pour archivage ou diffusion professionnelle',
                    'compressed': 'Vidéo compressée (fichier plus petit) - Pour partage en ligne ou stockage limité',
                    'audio_only': 'Audio seul (haute qualité) - Pour podcasts ou autres usages audio'
                }
                
                for format_name, file_path in export_results.items():
                    if os.path.exists(file_path):
                        filename = Path(file_path).name
                        description = format_descriptions.get(format_name, 'Format spécialisé')
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        content.append(f"- **{filename}** ({file_size:.1f} MB) - {description}")
                
                content.append("")
            
            content.extend([
                "## Qualité du doublage",
                "",
                "### Métriques de performance",
                ""
            ])
            
            if results.quality_metrics:
                for metric, value in results.quality_metrics.items():
                    if isinstance(value, float):
                        content.append(f"- **{metric.replace('_', ' ').title()}:** {value:.3f}")
                    else:
                        content.append(f"- **{metric.replace('_', ' ').title()}:** {value}")
                content.append("")
            
            content.extend([
                "## Utilisation des fichiers",
                "",
                "### Lecture vidéo",
                "- Utilisez n'importe quel lecteur vidéo moderne (VLC, Windows Media Player, QuickTime)",
                "- La vidéo principale est optimisée pour la plupart des usages",
                "- La version haute qualité est recommandée pour l'édition ou la diffusion",
                "",
                "### Partage et distribution",
                "- Version compressée : idéale pour l'upload sur les réseaux sociaux",
                "- Version principale : bon compromis qualité/taille pour la plupart des plateformes",
                "- Version haute qualité : pour les plateformes supportant la haute définition",
                "",
                "### Édition ultérieure",
                "- Utilisez la version haute qualité comme source",
                "- L'audio seul peut être utilisé dans des logiciels d'édition audio",
                "- Conservez les fichiers originaux pour de futures modifications",
                "",
                "## Conseils d'utilisation",
                "",
                "### Pour de meilleurs résultats",
                "- Utilisez des vidéos avec des dialogues clairs et audibles",
                "- Évitez les vidéos avec trop de bruit de fond",
                "- Les sous-titres incrustés améliorent la précision",
                "",
                "### Dépannage rapide",
                "- **Audio désynchronisé :** Vérifiez que votre lecteur supporte le format",
                "- **Qualité dégradée :** Utilisez la version haute qualité",
                "- **Fichier trop volumineux :** Utilisez la version compressée",
                "",
                "## Support technique",
                "",
                "Pour toute question ou problème :",
                "1. Consultez la FAQ dans la documentation complète",
                "2. Vérifiez les spécifications techniques de votre fichier",
                "3. Contactez le support avec les détails de votre traitement",
                "",
                f"**Documentation générée le :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                "",
                "---",
                "*Ce guide a été généré automatiquement par l'application de doublage vidéo par IA.*"
            ])
            
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"User guide generated: {guide_path}")
            return str(guide_path)
            
        except Exception as e:
            self.logger.warning(f"User guide generation failed: {e}")
            return ""
    
    def _generate_technical_report(self, 
                                 results: ProcessingResults,
                                 config: PipelineConfig,
                                 quality_validation: Dict[str, Any] = None) -> str:
        """Génère le rapport technique détaillé."""
        try:
            report_path = self.output_dir / "RAPPORT_TECHNIQUE.md"
            
            content = [
                "# Rapport Technique - Doublage Vidéo par IA",
                "",
                "## Informations générales",
                "",
                f"**Date de traitement :** {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
                f"**Durée de traitement :** {results.processing_time:.2f} secondes",
                f"**Statut :** {'✅ Succès' if results.success else '❌ Échec'}",
                "",
                "## Configuration utilisée",
                "",
                f"- **Modèle ASR :** {config.asr_model}",
                f"- **Modèle OCR :** {config.ocr_model}",
                f"- **Modèle de clonage vocal :** {config.voice_cloning_model}",
                f"- **Séparation de source :** {'Activée' if config.enable_source_separation else 'Désactivée'}",
                f"- **OCR :** {'Activé' if config.enable_ocr else 'Désactivé'}",
                f"- **Langue cible :** {config.target_language}",
                f"- **Codec de sortie :** {config.output_codec}",
                f"- **Débit vidéo :** {config.output_bitrate}",
                "",
                "## Résultats de l'analyse",
                "",
                f"- **Locuteurs détectés :** {results.speakers_detected}",
                f"- **Segments de dialogue :** {results.dialogue_segments}",
                f"- **Transcription disponible :** {'Oui' if results.transcription_result else 'Non'}",
                f"- **Résultats OCR :** {len(results.ocr_results)} éléments",
                f"- **Séparation de source :** {'Effectuée' if results.source_separation_result else 'Non effectuée'}",
                "",
            ]
            
            # Métriques de qualité
            if results.quality_metrics:
                content.extend([
                    "## Métriques de qualité",
                    "",
                ])
                
                for metric, value in results.quality_metrics.items():
                    if isinstance(value, float):
                        content.append(f"- **{metric.replace('_', ' ').title()} :** {value:.4f}")
                    else:
                        content.append(f"- **{metric.replace('_', ' ').title()} :** {value}")
                
                content.append("")
            
            # Validation de qualité
            if quality_validation:
                content.extend([
                    "## Validation de qualité",
                    "",
                    f"- **Score global :** {quality_validation.get('overall_quality_score', 0):.2f}/1.00",
                    f"- **Validation réussie :** {'✅ Oui' if quality_validation.get('passed_validation', False) else '❌ Non'}",
                    "",
                ])
                
                if quality_validation.get('issues_found'):
                    content.extend([
                        "### Problèmes détectés",
                        "",
                    ])
                    for issue in quality_validation['issues_found']:
                        content.append(f"- ⚠️ {issue}")
                    content.append("")
                
                if quality_validation.get('recommendations'):
                    content.extend([
                        "### Recommandations",
                        "",
                    ])
                    for rec in quality_validation['recommendations']:
                        content.append(f"- 💡 {rec}")
                    content.append("")
            
            # Détails de transcription
            if results.transcription_result:
                content.extend([
                    "## Détails de transcription",
                    "",
                    f"- **Langue détectée :** {getattr(results.transcription_result, 'language', 'N/A')}",
                    f"- **Confiance moyenne :** {getattr(results.transcription_result, 'confidence', 0):.2f}",
                    f"- **Nombre de mots :** {getattr(results.transcription_result, 'word_count', 0)}",
                    "",
                ])
            
            # Fichiers intermédiaires
            if results.intermediate_files:
                content.extend([
                    "## Fichiers intermédiaires générés",
                    "",
                ])
                for file_path in results.intermediate_files:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        content.append(f"- `{Path(file_path).name}` ({file_size:.1f} MB)")
                    else:
                        content.append(f"- `{Path(file_path).name}` (fichier temporaire supprimé)")
                content.append("")
            
            content.extend([
                "## Spécifications techniques",
                "",
                "### Formats supportés en entrée",
                "- **Vidéo :** MP4, MKV, AVI",
                "- **Audio :** Extraction automatique vers WAV/FLAC",
                "- **Sous-titres :** Incrustés dans la vidéo (OCR)",
                "",
                "### Formats de sortie",
                "- **Vidéo principale :** MP4 (H.264 + AAC)",
                "- **Haute qualité :** MP4 (H.264 haute qualité + AAC 320k)",
                "- **Compressée :** MP4 (H.264 optimisé + AAC 128k)",
                "- **Audio seul :** WAV 24-bit 48kHz",
                "",
                "### Technologies utilisées",
                "- **Extraction vidéo/audio :** FFmpeg",
                "- **Détection d'activité vocale :** Pyannote.audio",
                "- **Reconnaissance vocale :** Whisper/WhisperX",
                "- **OCR :** PaddleOCR ou Qwen-VL",
                "- **Clonage vocal :** Tortoise-TTS ou NeMo",
                "- **Séparation de source :** Demucs (optionnel)",
                "",
                "---",
                f"*Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*"
            ])
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Technical report generated: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.warning(f"Technical report generation failed: {e}")
            return ""
    
    def _generate_usage_examples(self, config: PipelineConfig) -> str:
        """Génère des exemples d'utilisation."""
        try:
            examples_path = self.output_dir / "EXEMPLES_UTILISATION.md"
            
            content = [
                "# Exemples d'Utilisation - Doublage Vidéo par IA",
                "",
                "## Interface Graphique (Recommandé)",
                "",
                "### Utilisation basique",
                "1. Lancez l'application : `python main.py --gui`",
                "2. Cliquez sur 'Sélectionner une vidéo'",
                "3. Choisissez votre fichier vidéo (MP4, MKV, ou AVI)",
                "4. Configurez les options si nécessaire",
                "5. Cliquez sur 'Démarrer le doublage'",
                "6. Attendez la fin du traitement",
                "7. Récupérez vos fichiers dans le dossier de sortie",
                "",
                "### Configuration avancée",
                "- **Séparation de source :** Activez pour séparer dialogues/musique/effets",
                "- **OCR :** Désactivez si votre vidéo n'a pas de sous-titres incrustés",
                "- **Modèles IA :** Choisissez selon vos besoins qualité/vitesse",
                "",
                "## Ligne de Commande",
                "",
                "### Utilisation simple",
                "```bash",
                "python main.py --input ma_video.mp4 --output video_doublee.mp4",
                "```",
                "",
                "### Avec fichier de configuration",
                "```bash",
                "python main.py --input ma_video.mp4 --output video_doublee.mp4 --config config.json",
                "```",
                "",
                "### Exemple de fichier de configuration (config.json)",
                "```json",
                "{",
                f'  "enable_source_separation": {str(config.enable_source_separation).lower()},',
                f'  "enable_ocr": {str(config.enable_ocr).lower()},',
                f'  "asr_model": "{config.asr_model}",',
                f'  "ocr_model": "{config.ocr_model}",',
                f'  "voice_cloning_model": "{config.voice_cloning_model}",',
                f'  "target_language": "{config.target_language}",',
                f'  "output_codec": "{config.output_codec}",',
                f'  "output_bitrate": "{config.output_bitrate}"',
                "}",
                "```",
                "",
                "## Cas d'usage spécifiques",
                "",
                "### Vidéo avec sous-titres incrustés",
                "- Activez l'OCR pour extraire les sous-titres",
                "- Utilisez un modèle OCR performant (Qwen-VL recommandé)",
                "- La synchronisation sera plus précise",
                "",
                "### Vidéo avec musique de fond",
                "- Activez la séparation de source",
                "- Le traitement sera plus long mais la qualité meilleure",
                "- La musique originale sera préservée",
                "",
                "### Vidéo courte (< 5 minutes)",
                "- Utilisez les paramètres par défaut",
                "- Le traitement sera rapide",
                "- Privilégiez la qualité",
                "",
                "### Vidéo longue (> 30 minutes)",
                "- Activez le traitement par chunks",
                "- Surveillez l'utilisation mémoire",
                "- Prévoyez plus de temps de traitement",
                "",
                "## Optimisation des performances",
                "",
                "### Pour la vitesse",
                "```json",
                "{",
                '  "asr_model": "whisper-base",',
                '  "ocr_model": "paddleocr",',
                '  "enable_source_separation": false,',
                '  "output_codec": "h264",',
                '  "output_bitrate": "3M"',
                "}",
                "```",
                "",
                "### Pour la qualité",
                "```json",
                "{",
                '  "asr_model": "whisper-large-v3",',
                '  "ocr_model": "qwen-vl",',
                '  "enable_source_separation": true,',
                '  "output_codec": "h264",',
                '  "output_bitrate": "8M"',
                "}",
                "```",
                "",
                "## Dépannage",
                "",
                "### Erreurs courantes",
                "",
                "**Erreur : 'Fichier vidéo non supporté'**",
                "- Vérifiez que le format est MP4, MKV ou AVI",
                "- Convertissez votre vidéo si nécessaire",
                "",
                "**Erreur : 'Mémoire insuffisante'**",
                "- Fermez les autres applications",
                "- Utilisez un modèle plus léger (whisper-base)",
                "- Activez le traitement par chunks",
                "",
                "**Erreur : 'Aucun locuteur détecté'**",
                "- Vérifiez que votre vidéo contient bien des dialogues",
                "- Augmentez le volume de l'audio source",
                "- Réduisez le bruit de fond",
                "",
                "### Améliorer les résultats",
                "",
                "**Audio de mauvaise qualité :**",
                "- Utilisez la séparation de source",
                "- Nettoyez l'audio avant traitement",
                "- Vérifiez les niveaux audio",
                "",
                "**Synchronisation imprécise :**",
                "- Activez l'OCR si des sous-titres sont présents",
                "- Vérifiez que la vidéo n'est pas corrompue",
                "- Utilisez un modèle ASR plus précis",
                "",
                "**Voix clonées peu naturelles :**",
                "- Assurez-vous d'avoir suffisamment d'échantillons vocaux",
                "- Utilisez un modèle de clonage plus avancé",
                "- Vérifiez la qualité de l'audio source",
                "",
                "---",
                f"*Exemples générés le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*"
            ]
            
            with open(examples_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Usage examples generated: {examples_path}")
            return str(examples_path)
            
        except Exception as e:
            self.logger.warning(f"Usage examples generation failed: {e}")
            return ""
    
    def _generate_faq_guide(self) -> str:
        """Génère le guide FAQ et dépannage."""
        try:
            faq_path = self.output_dir / "FAQ_DEPANNAGE.md"
            
            content = [
                "# FAQ et Dépannage - Doublage Vidéo par IA",
                "",
                "## Questions Fréquentes",
                "",
                "### Q: Quels formats vidéo sont supportés ?",
                "**R:** L'application supporte les formats MP4, MKV et AVI. Ces formats couvrent la majorité des vidéos courantes.",
                "",
                "### Q: Combien de temps prend le traitement ?",
                "**R:** Le temps varie selon :",
                "- Durée de la vidéo (comptez 2-5x la durée réelle)",
                "- Qualité des modèles choisis",
                "- Puissance de votre ordinateur",
                "- Options activées (séparation de source, OCR)",
                "",
                "### Q: Puis-je traiter des vidéos sans sous-titres ?",
                "**R:** Oui, l'application utilise la reconnaissance vocale (ASR) pour extraire les dialogues. Les sous-titres incrustés améliorent la précision mais ne sont pas obligatoires.",
                "",
                "### Q: La qualité des voix clonées est-elle bonne ?",
                "**R:** La qualité dépend de :",
                "- Clarté de l'audio original",
                "- Durée des échantillons vocaux disponibles",
                "- Modèle de clonage utilisé",
                "- Absence de bruit de fond",
                "",
                "### Q: Puis-je traiter des vidéos en langues étrangères ?",
                "**R:** L'application est optimisée pour le français mais peut traiter d'autres langues. Ajustez le paramètre `target_language` dans la configuration.",
                "",
                "### Q: L'application fonctionne-t-elle hors ligne ?",
                "**R:** Oui, une fois les modèles IA téléchargés, l'application fonctionne entièrement hors ligne.",
                "",
                "## Problèmes Techniques",
                "",
                "### Problème: L'application ne démarre pas",
                "**Solutions :**",
                "1. Vérifiez que Python 3.8+ est installé",
                "2. Installez les dépendances : `pip install -r requirements.txt`",
                "3. Vérifiez que FFmpeg est installé et accessible",
                "4. Consultez les logs d'erreur pour plus de détails",
                "",
                "### Problème: Erreur 'CUDA out of memory'",
                "**Solutions :**",
                "1. Fermez les autres applications gourmandes",
                "2. Utilisez des modèles plus légers",
                "3. Activez le traitement par chunks",
                "4. Réduisez la résolution vidéo si possible",
                "",
                "### Problème: Audio désynchronisé dans le résultat",
                "**Solutions :**",
                "1. Vérifiez que votre lecteur vidéo supporte le format",
                "2. Utilisez VLC pour tester la lecture",
                "3. Re-traitez avec l'OCR activé si des sous-titres sont présents",
                "4. Vérifiez l'intégrité du fichier source",
                "",
                "### Problème: Aucun locuteur détecté",
                "**Solutions :**",
                "1. Vérifiez que l'audio contient bien de la parole",
                "2. Augmentez le volume de l'audio source",
                "3. Réduisez les seuils de détection dans la configuration",
                "4. Nettoyez l'audio du bruit de fond",
                "",
                "### Problème: Traitement très lent",
                "**Solutions :**",
                "1. Utilisez des modèles plus rapides (whisper-base, paddleocr)",
                "2. Désactivez la séparation de source si non nécessaire",
                "3. Fermez les autres applications",
                "4. Vérifiez l'utilisation CPU/GPU",
                "",
                "## Optimisation des Résultats",
                "",
                "### Pour améliorer la précision",
                "- Utilisez des vidéos avec audio clair",
                "- Activez l'OCR si des sous-titres sont présents",
                "- Utilisez des modèles de haute qualité",
                "- Prétraitez l'audio pour réduire le bruit",
                "",
                "### Pour accélérer le traitement",
                "- Utilisez des modèles plus légers",
                "- Désactivez les options non essentielles",
                "- Traitez des segments plus courts",
                "- Utilisez un SSD pour les fichiers temporaires",
                "",
                "### Pour économiser l'espace disque",
                "- Utilisez la compression automatique",
                "- Supprimez les fichiers intermédiaires",
                "- Choisissez des débits adaptés à vos besoins",
                "- Activez le nettoyage automatique",
                "",
                "## Configuration Système",
                "",
                "### Configuration minimale",
                "- **CPU :** Processeur 4 cœurs 2.5GHz+",
                "- **RAM :** 8 GB (16 GB recommandés)",
                "- **Stockage :** 10 GB d'espace libre",
                "- **GPU :** Optionnel mais recommandé (NVIDIA avec CUDA)",
                "",
                "### Configuration recommandée",
                "- **CPU :** Processeur 8 cœurs 3.0GHz+",
                "- **RAM :** 32 GB",
                "- **Stockage :** SSD avec 50 GB d'espace libre",
                "- **GPU :** NVIDIA RTX 3060 ou équivalent",
                "",
                "## Logs et Diagnostic",
                "",
                "### Localisation des logs",
                "- **Windows :** `%APPDATA%/ai_video_dubbing/logs/`",
                "- **Linux/Mac :** `~/.ai_video_dubbing/logs/`",
                "- **Répertoire courant :** `./logs/`",
                "",
                "### Informations utiles pour le support",
                "1. Version de l'application",
                "2. Système d'exploitation",
                "3. Fichiers de logs récents",
                "4. Configuration utilisée",
                "5. Description détaillée du problème",
                "",
                "## Contact et Support",
                "",
                "Pour obtenir de l'aide :",
                "1. Consultez cette FAQ",
                "2. Vérifiez les logs d'erreur",
                "3. Testez avec les paramètres par défaut",
                "4. Contactez le support technique avec les informations de diagnostic",
                "",
                "---",
                f"*FAQ mise à jour le {datetime.now().strftime('%d/%m/%Y')}*"
            ]
            
            with open(faq_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"FAQ guide generated: {faq_path}")
            return str(faq_path)
            
        except Exception as e:
            self.logger.warning(f"FAQ guide generation failed: {e}")
            return ""
    
    def _generate_technical_specifications(self, results: ProcessingResults) -> str:
        """Génère les spécifications techniques."""
        try:
            specs_path = self.output_dir / "SPECIFICATIONS_TECHNIQUES.md"
            
            content = [
                "# Spécifications Techniques - Doublage Vidéo par IA",
                "",
                "## Architecture du Système",
                "",
                "### Composants Principaux",
                "- **Interface Utilisateur :** Tkinter/PyQt6",
                "- **Pipeline de Traitement :** Architecture modulaire en Python",
                "- **Traitement Vidéo/Audio :** FFmpeg",
                "- **Intelligence Artificielle :** Modèles pré-entraînés",
                "",
                "### Technologies Utilisées",
                "",
                "#### Traitement Multimédia",
                "- **FFmpeg :** Extraction, conversion et assemblage audio/vidéo",
                "- **OpenCV :** Traitement d'images pour l'OCR",
                "- **Librosa :** Analyse et traitement audio avancé",
                "- **PyAudio :** Interface audio système",
                "",
                "#### Intelligence Artificielle",
                "- **Whisper/WhisperX :** Reconnaissance vocale automatique (ASR)",
                "- **PaddleOCR/Qwen-VL :** Reconnaissance optique de caractères",
                "- **Pyannote.audio :** Diarisation et détection d'activité vocale",
                "- **Tortoise-TTS/NeMo :** Clonage et synthèse vocale",
                "- **Demucs :** Séparation de sources audio (optionnel)",
                "",
                "#### Frameworks et Bibliothèques",
                "- **PyTorch :** Framework d'apprentissage automatique",
                "- **NumPy/SciPy :** Calcul scientifique",
                "- **Pandas :** Manipulation de données",
                "- **Matplotlib :** Visualisation (diagnostic)",
                "",
                "## Formats Supportés",
                "",
                "### Entrée",
                "- **Vidéo :** MP4 (H.264/H.265), MKV, AVI",
                "- **Audio :** Extraction automatique vers WAV/FLAC",
                "- **Résolutions :** 480p à 4K (optimisé pour 720p-1080p)",
                "- **Débits :** 1 Mbps à 50 Mbps",
                "",
                "### Sortie",
                "- **Vidéo Principale :** MP4 (H.264 + AAC)",
                "- **Haute Qualité :** MP4 (H.264 CRF 18 + AAC 320k)",
                "- **Compressée :** MP4 (H.264 CRF 28 + AAC 128k)",
                "- **Audio Seul :** WAV 24-bit 48kHz",
                "",
                "## Pipeline de Traitement",
                "",
                "### Phase 1: Analyse (15-25% du temps)",
                "1. **Validation d'entrée :** Vérification format et intégrité",
                "2. **Extraction audio :** Conversion vers format de travail",
                "3. **Détection d'activité vocale :** Identification des segments de parole",
                "4. **Diarisation :** Séparation des locuteurs",
                "",
                "### Phase 2: Extraction (25-35% du temps)",
                "1. **Transcription ASR :** Conversion parole vers texte",
                "2. **OCR (optionnel) :** Extraction sous-titres incrustés",
                "3. **Synchronisation :** Alignement OCR/ASR",
                "4. **Séparation de source (optionnel) :** Isolation dialogues/musique",
                "",
                "### Phase 3: Préparation (15-25% du temps)",
                "1. **Segmentation par locuteur :** Découpage audio individuel",
                "2. **Normalisation :** Optimisation pour clonage vocal",
                "3. **Validation qualité :** Contrôle échantillons de référence",
                "",
                "### Phase 4: Synthèse (25-35% du temps)",
                "1. **Clonage vocal :** Génération nouvelles voix",
                "2. **Mixage audio :** Combinaison voix/musique/effets",
                "3. **Assemblage vidéo :** Fusion audio/vidéo finale",
                "4. **Export multi-format :** Génération versions optimisées",
                "",
                "## Métriques de Performance",
                "",
                f"### Résultats du Traitement Actuel",
                f"- **Temps total :** {results.processing_time:.1f} secondes",
                f"- **Locuteurs détectés :** {results.speakers_detected}",
                f"- **Segments traités :** {results.dialogue_segments}",
                "",
                "### Benchmarks Typiques",
                "- **Vidéo 5 min (720p) :** 2-8 minutes de traitement",
                "- **Vidéo 30 min (1080p) :** 15-45 minutes de traitement",
                "- **Ratio moyen :** 3-5x la durée vidéo réelle",
                "",
                "## Optimisations Techniques",
                "",
                "### Gestion Mémoire",
                "- **Chargement paresseux :** Modèles IA chargés à la demande",
                "- **Libération automatique :** Nettoyage mémoire entre phases",
                "- **Traitement par chunks :** Segmentation pour gros fichiers",
                "- **Cache intelligent :** Réutilisation résultats intermédiaires",
                "",
                "### Parallélisation",
                "- **OCR/ASR simultané :** Traitement parallèle quand possible",
                "- **Multi-threading :** Segmentation audio multi-cœurs",
                "- **GPU/CPU hybride :** Répartition optimale des tâches",
                "",
                "### Optimisations Spécifiques",
                "- **Formats optimisés :** FLAC pour qualité, WAV pour vitesse",
                "- **Résolution adaptative :** Réduction pour OCR si nécessaire",
                "- **Compression temporaire :** Économie d'espace disque",
                "- **Nettoyage automatique :** Suppression fichiers temporaires",
                "",
                "## Qualité et Validation",
                "",
                "### Métriques de Qualité Audio",
                "- **SNR (Signal-to-Noise Ratio) :** > 20 dB recommandé",
                "- **THD (Total Harmonic Distortion) :** < 5% acceptable",
                "- **Loudness :** -16 à -30 LUFS selon usage",
                "- **Plage dynamique :** > 10 dB pour naturalité",
                "",
                "### Validation Synchronisation",
                "- **Précision temporelle :** < 100ms différence audio/vidéo",
                "- **Alignement OCR/ASR :** > 85% correspondance textuelle",
                "- **Cohérence locuteurs :** Attribution correcte > 90%",
                "",
                "### Tests de Régression",
                "- **Échantillons de référence :** Validation qualité constante",
                "- **Métriques automatisées :** Contrôle qualité systématique",
                "- **Validation manuelle :** Vérification échantillons critiques",
                "",
                "## Sécurité et Confidentialité",
                "",
                "### Traitement Local",
                "- **Aucune donnée envoyée :** Traitement 100% local",
                "- **Modèles pré-téléchargés :** Fonctionnement hors ligne",
                "- **Fichiers temporaires :** Suppression automatique",
                "",
                "### Gestion des Données",
                "- **Chiffrement temporaire :** Protection fichiers sensibles",
                "- **Nettoyage sécurisé :** Effacement complet données temporaires",
                "- **Logs anonymisés :** Aucune information personnelle",
                "",
                "## Extensibilité",
                "",
                "### Architecture Modulaire",
                "- **Interfaces standardisées :** Ajout facile nouveaux modèles",
                "- **Plugins supportés :** Extension fonctionnalités",
                "- **Configuration flexible :** Adaptation besoins spécifiques",
                "",
                "### Modèles IA",
                "- **Mise à jour automatique :** Nouveaux modèles intégrables",
                "- **Formats multiples :** Support GGUF, PyTorch, ONNX",
                "- **Optimisations matériel :** CPU, GPU, TPU selon disponibilité",
                "",
                "---",
                f"*Spécifications mises à jour le {datetime.now().strftime('%d/%m/%Y')}*"
            ]
            
            with open(specs_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Technical specifications generated: {specs_path}")
            return str(specs_path)
            
        except Exception as e:
            self.logger.warning(f"Technical specifications generation failed: {e}")
            return ""
    
    def _generate_configuration_guide(self) -> str:
        """Génère le guide de configuration."""
        try:
            config_path = self.output_dir / "GUIDE_CONFIGURATION.md"
            
            content = [
                "# Guide de Configuration - Doublage Vidéo par IA",
                "",
                "## Configuration de Base",
                "",
                "### Fichier de Configuration (config.json)",
                "```json",
                "{",
                '  "enable_source_separation": false,',
                '  "enable_ocr": true,',
                '  "asr_model": "whisper-base",',
                '  "ocr_model": "paddleocr",',
                '  "voice_cloning_model": "tortoise-tts",',
                '  "target_language": "fr",',
                '  "output_codec": "h264",',
                '  "output_bitrate": "5M",',
                '  "temp_directory": "./temp",',
                '  "max_memory_usage": 0.8',
                "}",
                "```",
                "",
                "## Paramètres Détaillés",
                "",
                "### Séparation de Source",
                "**`enable_source_separation`** (boolean)",
                "- **true :** Active la séparation dialogues/musique/effets",
                "- **false :** Traite l'audio complet (plus rapide)",
                "- **Recommandation :** true pour vidéos avec musique de fond",
                "",
                "### OCR (Reconnaissance Optique)",
                "**`enable_ocr`** (boolean)",
                "- **true :** Extrait les sous-titres incrustés",
                "- **false :** Se base uniquement sur l'ASR",
                "- **Recommandation :** true si sous-titres présents",
                "",
                "### Modèles IA",
                "",
                "#### Modèle ASR (Reconnaissance Vocale)",
                "**`asr_model`** (string)",
                "- **whisper-tiny :** Très rapide, qualité basique",
                "- **whisper-base :** Équilibre vitesse/qualité",
                "- **whisper-small :** Bonne qualité, vitesse correcte",
                "- **whisper-medium :** Haute qualité, plus lent",
                "- **whisper-large-v3 :** Meilleure qualité, très lent",
                "",
                "#### Modèle OCR",
                "**`ocr_model`** (string)",
                "- **paddleocr :** Rapide, bon pour textes simples",
                "- **qwen-vl :** Plus précis, meilleur pour textes complexes",
                "",
                "#### Modèle de Clonage Vocal",
                "**`voice_cloning_model`** (string)",
                "- **tortoise-tts :** Qualité élevée, lent",
                "- **nemo-tts :** Plus rapide, qualité correcte",
                "",
                "### Paramètres de Sortie",
                "",
                "#### Codec Vidéo",
                "**`output_codec`** (string)",
                "- **h264 :** Standard, compatible partout",
                "- **h265 :** Meilleure compression, moins compatible",
                "",
                "#### Débit Vidéo",
                "**`output_bitrate`** (string)",
                "- **2M :** Qualité basique, fichier petit",
                "- **5M :** Qualité standard (recommandé)",
                "- **10M :** Haute qualité, fichier volumineux",
                "",
                "### Paramètres Système",
                "",
                "#### Répertoire Temporaire",
                "**`temp_directory`** (string)",
                "- Chemin vers dossier pour fichiers temporaires",
                "- Recommandation : SSD avec espace suffisant",
                "",
                "#### Utilisation Mémoire",
                "**`max_memory_usage`** (float, 0.0-1.0)",
                "- Pourcentage maximum de RAM utilisable",
                "- 0.8 = 80% de la RAM disponible",
                "",
                "## Configurations Prédéfinies",
                "",
                "### Configuration Rapide",
                "```json",
                "{",
                '  "enable_source_separation": false,',
                '  "enable_ocr": false,',
                '  "asr_model": "whisper-tiny",',
                '  "voice_cloning_model": "nemo-tts",',
                '  "output_bitrate": "3M"',
                "}",
                "```",
                "**Usage :** Tests rapides, vidéos courtes",
                "",
                "### Configuration Équilibrée",
                "```json",
                "{",
                '  "enable_source_separation": false,',
                '  "enable_ocr": true,',
                '  "asr_model": "whisper-base",',
                '  "ocr_model": "paddleocr",',
                '  "voice_cloning_model": "tortoise-tts",',
                '  "output_bitrate": "5M"',
                "}",
                "```",
                "**Usage :** Usage général, bon compromis",
                "",
                "### Configuration Haute Qualité",
                "```json",
                "{",
                '  "enable_source_separation": true,',
                '  "enable_ocr": true,',
                '  "asr_model": "whisper-large-v3",',
                '  "ocr_model": "qwen-vl",',
                '  "voice_cloning_model": "tortoise-tts",',
                '  "output_bitrate": "10M"',
                "}",
                "```",
                "**Usage :** Production, archivage, diffusion",
                "",
                "## Configuration par Type de Contenu",
                "",
                "### Vidéos avec Dialogue Seul",
                "```json",
                "{",
                '  "enable_source_separation": false,',
                '  "asr_model": "whisper-medium",',
                '  "voice_cloning_model": "tortoise-tts"',
                "}",
                "```",
                "",
                "### Vidéos avec Musique de Fond",
                "```json",
                "{",
                '  "enable_source_separation": true,',
                '  "asr_model": "whisper-large-v3",',
                '  "voice_cloning_model": "tortoise-tts"',
                "}",
                "```",
                "",
                "### Vidéos avec Sous-titres Incrustés",
                "```json",
                "{",
                '  "enable_ocr": true,',
                '  "ocr_model": "qwen-vl",',
                '  "asr_model": "whisper-base"',
                "}",
                "```",
                "",
                "## Optimisation par Matériel",
                "",
                "### Configuration CPU Faible",
                "```json",
                "{",
                '  "asr_model": "whisper-tiny",',
                '  "voice_cloning_model": "nemo-tts",',
                '  "max_memory_usage": 0.6,',
                '  "enable_source_separation": false',
                "}",
                "```",
                "",
                "### Configuration GPU Disponible",
                "```json",
                "{",
                '  "asr_model": "whisper-large-v3",',
                '  "voice_cloning_model": "tortoise-tts",',
                '  "enable_source_separation": true,',
                '  "max_memory_usage": 0.9',
                "}",
                "```",
                "",
                "### Configuration RAM Limitée",
                "```json",
                "{",
                '  "max_memory_usage": 0.5,',
                '  "asr_model": "whisper-base",',
                '  "enable_source_separation": false,',
                '  "temp_directory": "/tmp"',
                "}",
                "```",
                "",
                "## Variables d'Environnement",
                "",
                "### Configuration Système",
                "```bash",
                "# Répertoire de cache des modèles",
                "export AI_MODELS_CACHE=/path/to/models",
                "",
                "# Niveau de log",
                "export LOG_LEVEL=INFO",
                "",
                "# Utilisation GPU",
                "export CUDA_VISIBLE_DEVICES=0",
                "",
                "# Répertoire temporaire",
                "export TEMP_DIR=/fast/ssd/temp",
                "```",
                "",
                "## Validation de Configuration",
                "",
                "### Vérification Automatique",
                "L'application vérifie automatiquement :",
                "- Validité des paramètres",
                "- Disponibilité des modèles",
                "- Espace disque suffisant",
                "- Compatibilité matérielle",
                "",
                "### Test de Configuration",
                "```bash",
                "python main.py --config test_config.json --validate-only",
                "```",
                "",
                "## Dépannage Configuration",
                "",
                "### Erreurs Courantes",
                "",
                "**Modèle non trouvé :**",
                "- Vérifiez l'orthographe du nom",
                "- Téléchargez le modèle manuellement",
                "- Vérifiez la connexion internet",
                "",
                "**Mémoire insuffisante :**",
                "- Réduisez `max_memory_usage`",
                "- Utilisez des modèles plus légers",
                "- Fermez les autres applications",
                "",
                "**Espace disque insuffisant :**",
                "- Changez `temp_directory`",
                "- Nettoyez l'espace disque",
                "- Utilisez un débit plus faible",
                "",
                "---",
                f"*Guide mis à jour le {datetime.now().strftime('%d/%m/%Y')}*"
            ]
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Configuration guide generated: {config_path}")
            return str(config_path)
            
        except Exception as e:
            self.logger.warning(f"Configuration guide generation failed: {e}")
            return ""
