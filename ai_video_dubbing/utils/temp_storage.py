"""
Gestionnaire de stockage temporaire pour l'application de doublage vidéo par IA.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
import uuid


class TempStorage:
    """Gestionnaire de stockage temporaire avec nettoyage automatique."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialise le gestionnaire de stockage temporaire.
        
        Args:
            base_dir: Répertoire de base pour les fichiers temporaires
        """
        self.base_dir = base_dir or "./temp"
        self.session_id = str(uuid.uuid4())[:8]
        self.session_dir = None
        self.temp_files: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire de session
        self._create_session_directory()
    
    def _create_session_directory(self) -> None:
        """Crée un répertoire unique pour cette session."""
        base_path = Path(self.base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        self.session_dir = base_path / f"session_{self.session_id}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Created session directory: {self.session_dir}")
    
    def create_temp_file(self, suffix: str = "", prefix: str = "temp_", category: str = "general") -> str:
        """
        Crée un fichier temporaire unique.
        
        Args:
            suffix: Suffixe du fichier (ex: '.wav', '.mp4')
            prefix: Préfixe du fichier
            category: Catégorie pour l'organisation (ex: 'audio', 'video', 'ocr')
            
        Returns:
            Chemin vers le fichier temporaire créé
        """
        # Créer un sous-répertoire pour la catégorie
        category_dir = self.session_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Générer un nom de fichier unique
        file_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}{file_id}{suffix}"
        file_path = category_dir / filename
        
        # Créer le fichier vide
        file_path.touch()
        
        # Enregistrer le fichier
        key = f"{category}_{file_id}"
        self.temp_files[key] = str(file_path)
        
        self.logger.debug(f"Created temp file: {file_path}")
        return str(file_path)
    
    def create_temp_directory(self, name: str = None, category: str = "general") -> str:
        """
        Crée un répertoire temporaire.
        
        Args:
            name: Nom du répertoire (optionnel)
            category: Catégorie pour l'organisation
            
        Returns:
            Chemin vers le répertoire temporaire créé
        """
        if name is None:
            name = f"dir_{str(uuid.uuid4())[:8]}"
        
        category_dir = self.session_dir / category
        category_dir.mkdir(exist_ok=True)
        
        temp_dir = category_dir / name
        temp_dir.mkdir(exist_ok=True)
        
        # Enregistrer le répertoire
        key = f"{category}_dir_{name}"
        self.temp_files[key] = str(temp_dir)
        
        self.logger.debug(f"Created temp directory: {temp_dir}")
        return str(temp_dir)
    
    def get_temp_path(self, filename: str, category: str = "general") -> str:
        """
        Obtient un chemin temporaire pour un fichier donné.
        
        Args:
            filename: Nom du fichier
            category: Catégorie pour l'organisation
            
        Returns:
            Chemin complet vers le fichier temporaire
        """
        category_dir = self.session_dir / category
        category_dir.mkdir(exist_ok=True)
        
        return str(category_dir / filename)
    
    def save_intermediate_result(self, data: bytes, filename: str, category: str = "intermediate") -> str:
        """
        Sauvegarde un résultat intermédiaire.
        
        Args:
            data: Données à sauvegarder
            filename: Nom du fichier
            category: Catégorie pour l'organisation
            
        Returns:
            Chemin vers le fichier sauvegardé
        """
        file_path = self.get_temp_path(filename, category)
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        # Enregistrer le fichier
        key = f"{category}_{filename}"
        self.temp_files[key] = file_path
        
        self.logger.debug(f"Saved intermediate result: {file_path}")
        return file_path
    
    def get_session_info(self) -> Dict[str, any]:
        """
        Obtient les informations de la session courante.
        
        Returns:
            Dictionnaire avec les informations de session
        """
        total_size = 0
        file_count = 0
        
        if self.session_dir and self.session_dir.exists():
            for file_path in self.session_dir.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass
        
        return {
            'session_id': self.session_id,
            'session_dir': str(self.session_dir) if self.session_dir else None,
            'file_count': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'registered_files': len(self.temp_files)
        }
    
    def list_files_by_category(self, category: str = None) -> List[str]:
        """
        Liste les fichiers par catégorie.
        
        Args:
            category: Catégorie à lister (None pour toutes)
            
        Returns:
            Liste des chemins de fichiers
        """
        if category is None:
            return list(self.temp_files.values())
        
        return [
            path for key, path in self.temp_files.items()
            if key.startswith(f"{category}_")
        ]
    
    def cleanup_category(self, category: str) -> None:
        """
        Nettoie tous les fichiers d'une catégorie.
        
        Args:
            category: Catégorie à nettoyer
        """
        category_dir = self.session_dir / category
        
        if category_dir.exists():
            try:
                shutil.rmtree(category_dir)
                self.logger.info(f"Cleaned up category: {category}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup category {category}: {e}")
        
        # Supprimer les entrées de cette catégorie
        keys_to_remove = [
            key for key in self.temp_files.keys()
            if key.startswith(f"{category}_")
        ]
        
        for key in keys_to_remove:
            del self.temp_files[key]
    
    def cleanup_all(self) -> None:
        """Nettoie tous les fichiers temporaires de la session."""
        if self.session_dir and self.session_dir.exists():
            try:
                shutil.rmtree(self.session_dir)
                self.logger.info(f"Cleaned up session directory: {self.session_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup session directory: {e}")
        
        self.temp_files.clear()
    
    def __enter__(self):
        """Support du context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique à la sortie du context manager."""
        self.cleanup_all()
    
    def __del__(self):
        """Nettoyage automatique lors de la destruction de l'objet."""
        self.cleanup_all()