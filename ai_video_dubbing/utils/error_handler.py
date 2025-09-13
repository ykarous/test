#!/usr/bin/env python3
"""
Système de gestion d'erreurs complet pour l'application de doublage vidéo par IA.
"""

import logging
import traceback
import psutil
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..models.data_models import ProcessingError, ValidationError, ResourceError


class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Catégories d'erreurs."""
    VALIDATION = "validation"
    RESOURCE = "resource"
    PROCESSING = "processing"
    NETWORK = "network"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


@dataclass
class ErrorSolution:
    """Solution proposée pour une erreur."""
    title: str
    description: str
    action_callback: Optional[Callable] = None
    automatic: bool = False  # Si la solution peut être appliquée automatiquement
    requires_restart: bool = False
    estimated_time: Optional[str] = None


@dataclass
class ErrorInfo:
    """Informations complètes sur une erreur."""
    error_id: str
    title: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    solutions: List[ErrorSolution] = field(default_factory=list)
    resolved: bool = False
    resolution_time: Optional[float] = None


class ErrorHandler:
    """
    Gestionnaire d'erreurs avancé avec suggestions de résolution et monitoring des ressources.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'erreurs."""
        self.logger = logging.getLogger(__name__)
        
        # Stockage des erreurs
        self.error_history: List[ErrorInfo] = []
        self.active_errors: Dict[str, ErrorInfo] = {}
        
        # Callbacks
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        
        # Configuration
        self.max_history_size = 100
        self.auto_resolve_enabled = True
        
        # Monitoring des ressources
        self.resource_thresholds = {
            'memory_percent': 85.0,  # % de RAM utilisée
            'disk_percent': 90.0,    # % d'espace disque utilisé
            'cpu_percent': 95.0,     # % CPU utilisé
            'temperature': 80.0      # Température CPU (si disponible)
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialiser les solutions prédéfinies
        self._initialize_error_solutions()
    
    def _initialize_error_solutions(self):
        """Initialise les solutions prédéfinies pour les erreurs communes."""
        self.predefined_solutions = {
            # Erreurs de validation
            'invalid_video_format': [
                ErrorSolution(
                    title="Convertir le fichier vidéo",
                    description="Utilisez FFmpeg pour convertir le fichier vers un format supporté (MP4, AVI, MKV)",
                    action_callback=self._suggest_video_conversion,
                    estimated_time="2-5 minutes"
                ),
                ErrorSolution(
                    title="Vérifier l'intégrité du fichier",
                    description="Le fichier pourrait être corrompu. Essayez de le télécharger à nouveau",
                    estimated_time="Variable"
                )
            ],
            
            # Erreurs de ressources
            'insufficient_memory': [
                ErrorSolution(
                    title="Fermer les applications inutiles",
                    description="Libérez de la mémoire en fermant d'autres applications",
                    action_callback=self._suggest_memory_cleanup,
                    automatic=True,
                    estimated_time="Immédiat"
                ),
                ErrorSolution(
                    title="Réduire la qualité de traitement",
                    description="Utilisez un modèle plus petit ou réduisez la résolution",
                    action_callback=self._suggest_quality_reduction,
                    estimated_time="Immédiat"
                ),
                ErrorSolution(
                    title="Traitement par segments",
                    description="Divisez le fichier en segments plus petits",
                    action_callback=self._suggest_chunked_processing,
                    estimated_time="Variable"
                )
            ],
            
            'insufficient_disk_space': [
                ErrorSolution(
                    title="Nettoyer les fichiers temporaires",
                    description="Supprimez les fichiers temporaires de l'application",
                    action_callback=self._cleanup_temp_files,
                    automatic=True,
                    estimated_time="1-2 minutes"
                ),
                ErrorSolution(
                    title="Changer le répertoire de sortie",
                    description="Sélectionnez un disque avec plus d'espace libre",
                    action_callback=self._suggest_output_change,
                    estimated_time="Immédiat"
                )
            ],
            
            # Erreurs de dépendances
            'missing_dependency': [
                ErrorSolution(
                    title="Installer la dépendance manquante",
                    description="Installez automatiquement la dépendance requise",
                    action_callback=self._install_dependency,
                    automatic=True,
                    estimated_time="2-10 minutes"
                ),
                ErrorSolution(
                    title="Utiliser une alternative",
                    description="Utilisez un modèle ou processeur alternatif",
                    action_callback=self._suggest_alternative,
                    estimated_time="Immédiat"
                )
            ],
            
            # Erreurs de traitement
            'model_loading_failed': [
                ErrorSolution(
                    title="Télécharger à nouveau le modèle",
                    description="Le modèle pourrait être corrompu. Téléchargez-le à nouveau",
                    action_callback=self._redownload_model,
                    estimated_time="5-30 minutes"
                ),
                ErrorSolution(
                    title="Utiliser un modèle alternatif",
                    description="Essayez avec un modèle différent",
                    action_callback=self._suggest_alternative_model,
                    estimated_time="Immédiat"
                )
            ],
            
            'transcription_failed': [
                ErrorSolution(
                    title="Améliorer la qualité audio",
                    description="Activez la réduction de bruit et la normalisation",
                    action_callback=self._suggest_audio_enhancement,
                    estimated_time="Immédiat"
                ),
                ErrorSolution(
                    title="Changer de modèle ASR",
                    description="Utilisez un modèle plus robuste (whisper-large-v3)",
                    action_callback=self._suggest_better_asr_model,
                    estimated_time="Immédiat"
                )
            ]
        }
    
    def register_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """Enregistre un callback pour les nouvelles erreurs."""
        with self._lock:
            self.error_callbacks.append(callback)
    
    def handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """
        Gère une exception et retourne les informations d'erreur.
        
        Args:
            exception: L'exception à traiter
            context: Contexte additionnel sur l'erreur
            
        Returns:
            Informations complètes sur l'erreur
        """
        context = context or {}
        
        # Déterminer la catégorie et la sévérité
        category, severity = self._classify_error(exception)
        
        # Générer un ID unique pour l'erreur
        error_id = f"{category.value}_{int(time.time())}_{hash(str(exception)) % 10000}"
        
        # Créer les informations d'erreur
        error_info = ErrorInfo(
            error_id=error_id,
            title=self._generate_error_title(exception, category),
            message=str(exception),
            category=category,
            severity=severity,
            context=context,
            stack_trace=traceback.format_exc(),
            solutions=self._get_solutions_for_error(exception, category, context)
        )
        
        # Stocker l'erreur
        with self._lock:
            self.active_errors[error_id] = error_info
            self.error_history.append(error_info)
            
            # Limiter la taille de l'historique
            if len(self.error_history) > self.max_history_size:
                self.error_history = self.error_history[-self.max_history_size:]
        
        # Logger l'erreur
        self.logger.error(f"[{error_id}] {error_info.title}: {error_info.message}")
        if error_info.stack_trace:
            self.logger.debug(f"Stack trace for {error_id}:\n{error_info.stack_trace}")
        
        # Notifier les callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
        
        # Tentative de résolution automatique
        if self.auto_resolve_enabled:
            self._attempt_auto_resolution(error_info)
        
        return error_info
    
    def _classify_error(self, exception: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classifie une erreur selon sa catégorie et sa sévérité."""
        
        # Classification par type d'exception
        if isinstance(exception, ValidationError):
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM
        elif isinstance(exception, ResourceError):
            return ErrorCategory.RESOURCE, ErrorSeverity.HIGH
        elif isinstance(exception, ProcessingError):
            return ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM
        elif isinstance(exception, ImportError):
            return ErrorCategory.DEPENDENCY, ErrorSeverity.HIGH
        elif isinstance(exception, FileNotFoundError):
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM
        elif isinstance(exception, PermissionError):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        elif isinstance(exception, MemoryError):
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL
        elif isinstance(exception, OSError):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        
        # Classification par message d'erreur
        error_message = str(exception).lower()
        
        if any(keyword in error_message for keyword in ['memory', 'ram', 'out of memory']):
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL
        elif any(keyword in error_message for keyword in ['disk', 'space', 'no space']):
            return ErrorCategory.RESOURCE, ErrorSeverity.HIGH
        elif any(keyword in error_message for keyword in ['network', 'connection', 'timeout']):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        elif any(keyword in error_message for keyword in ['model', 'loading', 'download']):
            return ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM
        elif any(keyword in error_message for keyword in ['config', 'configuration', 'setting']):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.LOW
        
        # Par défaut
        return ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM
    
    def _generate_error_title(self, exception: Exception, category: ErrorCategory) -> str:
        """Génère un titre clair pour l'erreur."""
        
        error_titles = {
            ErrorCategory.VALIDATION: "Erreur de Validation",
            ErrorCategory.RESOURCE: "Ressources Insuffisantes",
            ErrorCategory.PROCESSING: "Erreur de Traitement",
            ErrorCategory.NETWORK: "Problème de Connexion",
            ErrorCategory.DEPENDENCY: "Dépendance Manquante",
            ErrorCategory.CONFIGURATION: "Erreur de Configuration",
            ErrorCategory.SYSTEM: "Erreur Système"
        }
        
        base_title = error_titles.get(category, "Erreur Inconnue")
        
        # Personnaliser selon le type d'exception
        if isinstance(exception, FileNotFoundError):
            return "Fichier Introuvable"
        elif isinstance(exception, PermissionError):
            return "Permissions Insuffisantes"
        elif isinstance(exception, MemoryError):
            return "Mémoire Insuffisante"
        elif isinstance(exception, ImportError):
            return "Module Non Disponible"
        
        return base_title
    
    def _get_solutions_for_error(self, exception: Exception, category: ErrorCategory, 
                                context: Dict[str, Any]) -> List[ErrorSolution]:
        """Obtient les solutions appropriées pour une erreur."""
        solutions = []
        
        # Solutions basées sur le type d'exception
        if isinstance(exception, FileNotFoundError):
            solutions.extend(self.predefined_solutions.get('invalid_video_format', []))
        elif isinstance(exception, MemoryError):
            solutions.extend(self.predefined_solutions.get('insufficient_memory', []))
        elif isinstance(exception, ImportError):
            solutions.extend(self.predefined_solutions.get('missing_dependency', []))
        
        # Solutions basées sur le message d'erreur
        error_message = str(exception).lower()
        
        if 'disk' in error_message or 'space' in error_message:
            solutions.extend(self.predefined_solutions.get('insufficient_disk_space', []))
        elif 'model' in error_message and 'load' in error_message:
            solutions.extend(self.predefined_solutions.get('model_loading_failed', []))
        elif 'transcription' in error_message or 'whisper' in error_message:
            solutions.extend(self.predefined_solutions.get('transcription_failed', []))
        
        # Solutions basées sur le contexte
        if context.get('component') == 'video_processor' and 'format' in error_message:
            solutions.extend(self.predefined_solutions.get('invalid_video_format', []))
        
        # Solution générique si aucune solution spécifique
        if not solutions:
            solutions.append(ErrorSolution(
                title="Redémarrer l'opération",
                description="Essayez de relancer l'opération après avoir vérifié les paramètres",
                estimated_time="Variable"
            ))
        
        return solutions
    
    def _attempt_auto_resolution(self, error_info: ErrorInfo):
        """Tente de résoudre automatiquement une erreur."""
        for solution in error_info.solutions:
            if solution.automatic and solution.action_callback:
                try:
                    self.logger.info(f"Tentative de résolution automatique: {solution.title}")
                    result = solution.action_callback()
                    
                    if result:
                        self.mark_error_resolved(error_info.error_id, solution.title)
                        break
                        
                except Exception as e:
                    self.logger.error(f"Échec de la résolution automatique {solution.title}: {e}")
    
    def mark_error_resolved(self, error_id: str, resolution_method: str = None):
        """Marque une erreur comme résolue."""
        with self._lock:
            if error_id in self.active_errors:
                error_info = self.active_errors[error_id]
                error_info.resolved = True
                error_info.resolution_time = time.time()
                
                # Retirer des erreurs actives
                del self.active_errors[error_id]
                
                self.logger.info(f"Erreur {error_id} résolue: {resolution_method or 'Méthode inconnue'}")
    
    def get_active_errors(self) -> List[ErrorInfo]:
        """Retourne la liste des erreurs actives."""
        with self._lock:
            return list(self.active_errors.values())
    
    def get_error_history(self, limit: int = 50) -> List[ErrorInfo]:
        """Retourne l'historique des erreurs."""
        with self._lock:
            return self.error_history[-limit:] if self.error_history else []
    
    def check_system_resources(self) -> List[ErrorInfo]:
        """Vérifie les ressources système et retourne les problèmes détectés."""
        issues = []
        
        try:
            # Vérifier la mémoire
            memory = psutil.virtual_memory()
            if memory.percent > self.resource_thresholds['memory_percent']:
                issue = ErrorInfo(
                    error_id=f"memory_warning_{int(time.time())}",
                    title="Utilisation Mémoire Élevée",
                    message=f"Utilisation mémoire: {memory.percent:.1f}% (seuil: {self.resource_thresholds['memory_percent']}%)",
                    category=ErrorCategory.RESOURCE,
                    severity=ErrorSeverity.HIGH if memory.percent > 95 else ErrorSeverity.MEDIUM,
                    solutions=self.predefined_solutions.get('insufficient_memory', [])
                )
                issues.append(issue)
            
            # Vérifier l'espace disque
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    percent_used = (usage.used / usage.total) * 100
                    
                    if percent_used > self.resource_thresholds['disk_percent']:
                        issue = ErrorInfo(
                            error_id=f"disk_warning_{disk.device}_{int(time.time())}",
                            title=f"Espace Disque Faible ({disk.device})",
                            message=f"Utilisation disque {disk.device}: {percent_used:.1f}% (seuil: {self.resource_thresholds['disk_percent']}%)",
                            category=ErrorCategory.RESOURCE,
                            severity=ErrorSeverity.HIGH if percent_used > 98 else ErrorSeverity.MEDIUM,
                            solutions=self.predefined_solutions.get('insufficient_disk_space', [])
                        )
                        issues.append(issue)
                except:
                    continue
            
            # Vérifier le CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.resource_thresholds['cpu_percent']:
                issue = ErrorInfo(
                    error_id=f"cpu_warning_{int(time.time())}",
                    title="Utilisation CPU Élevée",
                    message=f"Utilisation CPU: {cpu_percent:.1f}% (seuil: {self.resource_thresholds['cpu_percent']}%)",
                    category=ErrorCategory.RESOURCE,
                    severity=ErrorSeverity.MEDIUM,
                    solutions=[
                        ErrorSolution(
                            title="Réduire la charge CPU",
                            description="Fermez les applications gourmandes en CPU ou réduisez les paramètres de traitement",
                            estimated_time="Immédiat"
                        )
                    ]
                )
                issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des ressources: {e}")
        
        return issues
    
    # Méthodes de résolution automatique
    
    def _suggest_video_conversion(self) -> bool:
        """Suggère la conversion vidéo."""
        # Cette méthode serait implémentée pour guider l'utilisateur
        # vers la conversion du fichier vidéo
        return False  # Pas de résolution automatique possible
    
    def _suggest_memory_cleanup(self) -> bool:
        """Tente de libérer de la mémoire."""
        try:
            import gc
            gc.collect()
            return True
        except:
            return False
    
    def _suggest_quality_reduction(self) -> bool:
        """Suggère la réduction de qualité."""
        # Cette méthode modifierait la configuration pour réduire la qualité
        return False  # Nécessite une intervention utilisateur
    
    def _suggest_chunked_processing(self) -> bool:
        """Suggère le traitement par segments."""
        return False  # Nécessite une intervention utilisateur
    
    def _cleanup_temp_files(self) -> bool:
        """Nettoie les fichiers temporaires."""
        try:
            import tempfile
            import shutil
            
            temp_dir = Path(tempfile.gettempdir()) / "ai_video_dubbing"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                return True
        except Exception as e:
            self.logger.error(f"Erreur nettoyage fichiers temporaires: {e}")
        
        return False
    
    def _suggest_output_change(self) -> bool:
        """Suggère le changement de répertoire de sortie."""
        return False  # Nécessite une intervention utilisateur
    
    def _install_dependency(self) -> bool:
        """Tente d'installer une dépendance manquante."""
        # Cette méthode pourrait utiliser pip pour installer des dépendances
        return False  # Implémentation complexe nécessaire
    
    def _suggest_alternative(self) -> bool:
        """Suggère une alternative."""
        return False  # Nécessite une intervention utilisateur
    
    def _redownload_model(self) -> bool:
        """Retélécharge un modèle."""
        return False  # Implémentation complexe nécessaire
    
    def _suggest_alternative_model(self) -> bool:
        """Suggère un modèle alternatif."""
        return False  # Nécessite une intervention utilisateur
    
    def _suggest_audio_enhancement(self) -> bool:
        """Suggère l'amélioration audio."""
        return False  # Nécessite une intervention utilisateur
    
    def _suggest_better_asr_model(self) -> bool:
        """Suggère un meilleur modèle ASR."""
        return False  # Nécessite une intervention utilisateur


# Instance globale du gestionnaire d'erreurs
global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Retourne l'instance globale du gestionnaire d'erreurs."""
    return global_error_handler