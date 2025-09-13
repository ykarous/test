"""
Gestionnaire de sortie pour l'application de doublage vidéo par IA.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

from ..models.data_models import ProcessingResults, ValidationError


class OutputManager:
    """Gestionnaire pour les fichiers de sortie et les résultats."""
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialise le gestionnaire de sortie.
        
        Args:
            output_dir: Répertoire de sortie par défaut
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire de sortie s'il n'existe pas
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_output_path(self, input_path: str, suffix: str = "_dubbed", extension: str = None) -> str:
        """
        Prépare le chemin de sortie basé sur le fichier d'entrée.
        
        Args:
            input_path: Chemin du fichier d'entrée
            suffix: Suffixe à ajouter au nom
            extension: Extension de sortie (garde l'originale si None)
            
        Returns:
            Chemin de sortie préparé
        """
        input_path = Path(input_path)
        
        # Déterminer l'extension
        if extension is None:
            extension = input_path.suffix
        elif not extension.startswith('.'):
            extension = f'.{extension}'
        
        # Créer le nom de fichier de sortie
        output_name = f"{input_path.stem}{suffix}{extension}"
        output_path = self.output_dir / output_name
        
        # Éviter les conflits de noms
        counter = 1
        while output_path.exists():
            output_name = f"{input_path.stem}{suffix}_{counter}{extension}"
            output_path = self.output_dir / output_name
            counter += 1
        
        return str(output_path)
    
    def save_final_video(self, temp_video_path: str, output_path: str) -> str:
        """
        Sauvegarde la vidéo finale.
        
        Args:
            temp_video_path: Chemin vers la vidéo temporaire
            output_path: Chemin de sortie souhaité
            
        Returns:
            Chemin réel de la vidéo sauvegardée
        """
        try:
            # S'assurer que le répertoire de sortie existe
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(temp_video_path, output_path)
            
            # Vérifier que la copie a réussi
            if not output_path.exists():
                raise ValidationError("Failed to save output video")
            
            self.logger.info(f"Final video saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ValidationError(f"Failed to save final video: {e}")
    
    def save_processing_results(self, results: ProcessingResults, output_dir: str = None) -> str:
        """
        Sauvegarde les résultats de traitement en JSON.
        
        Args:
            results: Résultats du traitement
            output_dir: Répertoire de sortie (utilise self.output_dir si None)
            
        Returns:
            Chemin vers le fichier de résultats sauvegardé
        """
        if output_dir is None:
            output_dir = self.output_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer le nom de fichier basé sur la vidéo de sortie
        video_path = Path(results.output_video_path)
        results_filename = f"{video_path.stem}_results.json"
        results_path = output_dir / results_filename
        
        # Convertir les résultats en dictionnaire
        results_dict = {
            'output_video_path': results.output_video_path,
            'processing_time': results.processing_time,
            'speakers_detected': results.speakers_detected,
            'dialogue_segments': results.dialogue_segments,
            'quality_metrics': results.quality_metrics,
            'intermediate_files': results.intermediate_files,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
        try:
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Processing results saved to: {results_path}")
            return str(results_path)
            
        except Exception as e:
            self.logger.warning(f"Failed to save processing results: {e}")
            return ""
    
    def save_intermediate_files(self, intermediate_files: Dict[str, str], output_dir: str = None) -> Dict[str, str]:
        """
        Sauvegarde les fichiers intermédiaires importants.
        
        Args:
            intermediate_files: Dictionnaire {nom: chemin_temporaire}
            output_dir: Répertoire de sortie
            
        Returns:
            Dictionnaire {nom: chemin_final} des fichiers sauvegardés
        """
        if output_dir is None:
            output_dir = self.output_dir / "intermediate"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for name, temp_path in intermediate_files.items():
            try:
                if not os.path.exists(temp_path):
                    self.logger.warning(f"Intermediate file not found: {temp_path}")
                    continue
                
                # Déterminer le nom de fichier de sortie
                temp_path_obj = Path(temp_path)
                output_filename = f"{name}{temp_path_obj.suffix}"
                output_path = output_dir / output_filename
                
                # Éviter les conflits
                counter = 1
                while output_path.exists():
                    stem = f"{name}_{counter}"
                    output_path = output_dir / f"{stem}{temp_path_obj.suffix}"
                    counter += 1
                
                # Copier le fichier
                shutil.copy2(temp_path, output_path)
                saved_files[name] = str(output_path)
                
                self.logger.debug(f"Saved intermediate file: {name} -> {output_path}")
                
            except Exception as e:
                self.logger.warning(f"Failed to save intermediate file {name}: {e}")
        
        return saved_files
    
    def create_output_summary(self, results: ProcessingResults, output_path: str = None) -> str:
        """
        Crée un résumé textuel des résultats.
        
        Args:
            results: Résultats du traitement
            output_path: Chemin de sortie pour le résumé
            
        Returns:
            Chemin vers le fichier de résumé créé
        """
        if output_path is None:
            video_path = Path(results.output_video_path)
            output_path = self.output_dir / f"{video_path.stem}_summary.txt"
        
        summary_lines = [
            "=== RÉSUMÉ DU DOUBLAGE VIDÉO PAR IA ===",
            "",
            f"Fichier de sortie: {results.output_video_path}",
            f"Temps de traitement: {results.processing_time:.2f} secondes",
            f"Locuteurs détectés: {results.speakers_detected}",
            f"Segments de dialogue: {results.dialogue_segments}",
            "",
            "=== MÉTRIQUES DE QUALITÉ ===",
        ]
        
        for metric, value in results.quality_metrics.items():
            if isinstance(value, float):
                summary_lines.append(f"{metric}: {value:.3f}")
            else:
                summary_lines.append(f"{metric}: {value}")
        
        if results.intermediate_files:
            summary_lines.extend([
                "",
                "=== FICHIERS INTERMÉDIAIRES ===",
            ])
            for file_path in results.intermediate_files:
                summary_lines.append(f"- {file_path}")
        
        summary_lines.extend([
            "",
            f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=== FIN DU RÉSUMÉ ==="
        ])
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_lines))
            
            self.logger.info(f"Summary saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.warning(f"Failed to save summary: {e}")
            return ""
    
    def validate_output_space(self, estimated_size_mb: float) -> bool:
        """
        Vérifie qu'il y a suffisamment d'espace disque.
        
        Args:
            estimated_size_mb: Taille estimée en MB
            
        Returns:
            True si l'espace est suffisant
        """
        try:
            # Obtenir l'espace disque disponible
            stat = shutil.disk_usage(self.output_dir)
            available_mb = stat.free / (1024 * 1024)
            
            # Ajouter une marge de sécurité de 20%
            required_mb = estimated_size_mb * 1.2
            
            if available_mb < required_mb:
                self.logger.warning(
                    f"Insufficient disk space. Required: {required_mb:.1f}MB, "
                    f"Available: {available_mb:.1f}MB"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not check disk space: {e}")
            return True  # Assumer que c'est OK si on ne peut pas vérifier
    
    def get_output_info(self) -> Dict[str, Any]:
        """
        Obtient les informations sur le répertoire de sortie.
        
        Returns:
            Dictionnaire avec les informations
        """
        try:
            stat = shutil.disk_usage(self.output_dir)
            
            # Compter les fichiers dans le répertoire de sortie
            file_count = 0
            total_size = 0
            
            if self.output_dir.exists():
                for file_path in self.output_dir.rglob('*'):
                    if file_path.is_file():
                        file_count += 1
                        try:
                            total_size += file_path.stat().st_size
                        except OSError:
                            pass
            
            return {
                'output_directory': str(self.output_dir),
                'exists': self.output_dir.exists(),
                'file_count': file_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'available_space_mb': round(stat.free / (1024 * 1024), 2),
                'total_space_mb': round(stat.total / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.warning(f"Could not get output info: {e}")
            return {
                'output_directory': str(self.output_dir),
                'exists': self.output_dir.exists() if self.output_dir else False,
                'error': str(e)
            }