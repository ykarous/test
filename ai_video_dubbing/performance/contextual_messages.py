"""
Système de messages de progression contextuels
Génère des messages adaptés selon le type d'opération et le contexte
"""
import time
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    """Types de messages de progression"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

class OperationType(Enum):
    """Types d'opérations supportées"""
    DOWNLOAD = "download"
    TRANSCRIPTION = "transcription"
    MODEL_LOADING = "model_loading"
    CACHE_OPERATION = "cache_operation"
    FALLBACK = "fallback"
    OPTIMIZATION = "optimization"
    DIAGNOSTIC = "diagnostic"
    INITIALIZATION = "initialization"

@dataclass
class ProgressContext:
    """Contexte de progression pour la génération de messages"""
    operation_type: OperationType
    operation_id: str
    progress_percent: float
    current_step: str
    total_steps: Optional[int] = None
    current_step_index: Optional[int] = None
    start_time: float = 0.0
    estimated_duration: Optional[float] = None
    
    # Métriques spécifiques
    download_speed: Optional[float] = None  # bytes/sec
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    model_name: Optional[str] = None
    language: Optional[str] = None
    quality_preference: Optional[str] = None
    gpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    
    # Erreurs et solutions
    error_message: Optional[str] = None
    suggested_solutions: List[str] = None
    
    # Métadonnées additionnelles
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggested_solutions is None:
            self.suggested_solutions = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ContextualMessage:
    """Message contextuel généré"""
    message: str
    message_type: MessageType
    progress_percent: float
    eta_seconds: Optional[float] = None
    details: Dict[str, Any] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.suggestions is None:
            self.suggestions = []

class ContextualMessageGenerator:
    """Générateur de messages de progression contextuels"""
    
    def __init__(self):
        # Templates de messages par type d'opération
        self.message_templates = {
            OperationType.DOWNLOAD: {
                "starting": "🔄 Démarrage du téléchargement de {model_name}...",
                "progress": "⬇️ Téléchargement en cours: {progress}% ({speed}) - ETA: {eta}",
                "resuming": "🔄 Reprise du téléchargement à {progress}%...",
                "completed": "✅ Téléchargement terminé: {model_name} ({total_size})",
                "failed": "❌ Échec du téléchargement: {error}",
                "slow_connection": "⚠️ Connexion lente détectée - Optimisation en cours..."
            },
            
            OperationType.TRANSCRIPTION: {
                "starting": "🎵 Démarrage de la transcription ({language}, {quality})...",
                "progress": "🔄 Transcription en cours: {progress}% - {current_step}",
                "model_loading": "📦 Chargement du modèle {model_name}...",
                "processing": "⚙️ Traitement audio avec {model_name}...",
                "completed": "✅ Transcription terminée en {duration}s",
                "failed": "❌ Échec de la transcription: {error}",
                "fallback": "⚠️ Basculement vers {fallback_model}..."
            },
            
            OperationType.MODEL_LOADING: {
                "starting": "📦 Chargement du modèle {model_name}...",
                "progress": "⏳ Initialisation: {progress}% - {current_step}",
                "gpu_loading": "🎮 Chargement sur GPU ({gpu_usage}% utilisé)...",
                "cpu_fallback": "💻 Basculement vers CPU...",
                "completed": "✅ Modèle {model_name} prêt",
                "failed": "❌ Échec du chargement: {error}",
                "memory_warning": "⚠️ Mémoire limitée - Optimisation automatique..."
            },
            
            OperationType.CACHE_OPERATION: {
                "checking": "🗄️ Vérification du cache...",
                "hit": "✅ Résultat trouvé dans le cache (gain: {time_saved}s)",
                "miss": "🔄 Résultat non trouvé - Traitement nécessaire",
                "storing": "💾 Mise en cache du résultat...",
                "cleanup": "🧹 Nettoyage du cache ({freed_space} libérés)...",
                "validation": "🔍 Validation de l'intégrité du cache..."
            },
            
            OperationType.FALLBACK: {
                "triggered": "⚠️ Fallback activé: {reason}",
                "trying": "🔄 Essai avec {fallback_model}...",
                "success": "✅ Fallback réussi avec {model_name}",
                "failed": "❌ Tous les fallbacks ont échoué",
                "optimization": "🔧 Optimisation automatique des paramètres..."
            },
            
            OperationType.OPTIMIZATION: {
                "analyzing": "🔍 Analyse des performances système...",
                "optimizing": "⚙️ Optimisation en cours: {optimization_type}",
                "completed": "✅ Optimisation terminée - Amélioration: {improvement}%",
                "learning": "🧠 Apprentissage des préférences utilisateur...",
                "config_update": "⚙️ Mise à jour de la configuration optimale..."
            },
            
            OperationType.DIAGNOSTIC: {
                "starting": "🔍 Démarrage du diagnostic système...",
                "checking": "🔍 Vérification: {component}",
                "issue_found": "⚠️ Problème détecté: {issue}",
                "completed": "✅ Diagnostic terminé - {issues_count} problèmes trouvés",
                "recommendations": "💡 Recommandations générées"
            },
            
            OperationType.INITIALIZATION: {
                "starting": "🚀 Initialisation du système...",
                "component": "⚙️ Initialisation: {component}",
                "completed": "✅ Système initialisé et prêt",
                "failed": "❌ Échec de l'initialisation: {error}"
            }
        }
        
        # Messages d'erreur avec solutions suggérées
        self.error_solutions = {
            "cuda_error": [
                "Vérifier que CUDA est installé et compatible",
                "Redémarrer l'application",
                "Utiliser le mode CPU comme alternative"
            ],
            "memory_error": [
                "Fermer d'autres applications",
                "Utiliser un modèle plus léger",
                "Redémarrer l'application"
            ],
            "network_error": [
                "Vérifier la connexion internet",
                "Réessayer le téléchargement",
                "Utiliser un modèle local si disponible"
            ],
            "model_error": [
                "Re-télécharger le modèle",
                "Vérifier l'intégrité du fichier",
                "Utiliser un modèle alternatif"
            ],
            "timeout_error": [
                "Augmenter le timeout",
                "Vérifier les ressources système",
                "Utiliser un modèle plus rapide"
            ]
        }
    
    def create_progress_message(self, context: ProgressContext) -> ContextualMessage:
        """Crée un message de progression contextuel"""
        
        # Calculer l'ETA
        eta_seconds = self._calculate_eta(context)
        
        # Générer le message principal
        message = self._generate_main_message(context)
        
        # Déterminer le type de message
        message_type = self._determine_message_type(context)
        
        # Générer les détails
        details = self._generate_details(context)
        
        # Générer les suggestions si nécessaire
        suggestions = self._generate_suggestions(context)
        
        return ContextualMessage(
            message=message,
            message_type=message_type,
            progress_percent=context.progress_percent,
            eta_seconds=eta_seconds,
            details=details,
            suggestions=suggestions
        )
    
    def _generate_main_message(self, context: ProgressContext) -> str:
        """Génère le message principal selon le contexte"""
        
        templates = self.message_templates.get(context.operation_type, {})
        
        # Déterminer le template à utiliser
        template_key = self._select_template_key(context)
        template = templates.get(template_key, "🔄 Opération en cours: {progress}%")
        
        # Préparer les variables pour le template
        variables = self._prepare_template_variables(context)
        
        try:
            return template.format(**variables)
        except KeyError as e:
            # Fallback si une variable manque
            return f"🔄 {context.current_step} ({context.progress_percent:.1f}%)"
    
    def _select_template_key(self, context: ProgressContext) -> str:
        """Sélectionne la clé de template appropriée"""
        
        if context.error_message:
            return "failed"
        
        if context.progress_percent >= 100:
            return "completed"
        
        if context.progress_percent == 0:
            return "starting"
        
        # Logique spécifique par type d'opération
        if context.operation_type == OperationType.DOWNLOAD:
            if context.download_speed and context.download_speed < 100000:  # < 100KB/s
                return "slow_connection"
            elif context.downloaded_bytes and context.downloaded_bytes > 0:
                return "resuming" if context.progress_percent < 10 else "progress"
            return "progress"
        
        elif context.operation_type == OperationType.TRANSCRIPTION:
            if "fallback" in context.current_step.lower():
                return "fallback"
            elif "modèle" in context.current_step.lower() or "model" in context.current_step.lower():
                return "model_loading"
            elif context.progress_percent > 20:
                return "processing"
            return "progress"
        
        elif context.operation_type == OperationType.MODEL_LOADING:
            if context.gpu_usage and context.gpu_usage > 0:
                return "gpu_loading"
            elif "cpu" in context.current_step.lower():
                return "cpu_fallback"
            elif context.memory_usage and context.memory_usage > 80:
                return "memory_warning"
            return "progress"
        
        elif context.operation_type == OperationType.CACHE_OPERATION:
            if "vérification" in context.current_step.lower():
                return "checking"
            elif "trouvé" in context.current_step.lower():
                return "hit"
            elif "nettoyage" in context.current_step.lower():
                return "cleanup"
            elif "validation" in context.current_step.lower():
                return "validation"
            return "storing"
        
        return "progress"
    
    def _prepare_template_variables(self, context: ProgressContext) -> Dict[str, str]:
        """Prépare les variables pour le template"""
        
        variables = {
            "progress": f"{context.progress_percent:.1f}",
            "current_step": context.current_step,
            "operation_id": context.operation_id,
            "model_name": context.model_name or "modèle",
            "language": self._format_language(context.language),
            "quality": self._format_quality(context.quality_preference),
            "error": context.error_message or "erreur inconnue"
        }
        
        # Variables spécifiques au téléchargement
        if context.operation_type == OperationType.DOWNLOAD:
            variables.update({
                "speed": self._format_download_speed(context.download_speed),
                "eta": self._format_eta(self._calculate_eta(context)),
                "total_size": self._format_file_size(context.total_bytes)
            })
        
        # Variables spécifiques à la transcription
        if context.operation_type == OperationType.TRANSCRIPTION:
            duration = time.time() - context.start_time if context.start_time else 0
            variables.update({
                "duration": f"{duration:.1f}",
                "fallback_model": context.metadata.get("fallback_model", "modèle alternatif")
            })
        
        # Variables spécifiques au modèle
        if context.operation_type == OperationType.MODEL_LOADING:
            variables.update({
                "gpu_usage": f"{context.gpu_usage:.1f}" if context.gpu_usage else "0",
                "memory_usage": f"{context.memory_usage:.1f}" if context.memory_usage else "0"
            })
        
        # Variables spécifiques au cache
        if context.operation_type == OperationType.CACHE_OPERATION:
            variables.update({
                "time_saved": f"{context.metadata.get('time_saved', 0):.1f}",
                "freed_space": self._format_file_size(context.metadata.get("freed_bytes", 0))
            })
        
        # Variables spécifiques au fallback
        if context.operation_type == OperationType.FALLBACK:
            variables.update({
                "reason": context.metadata.get("fallback_reason", "erreur système"),
                "fallback_model": context.metadata.get("fallback_model", "modèle alternatif")
            })
        
        # Variables spécifiques à l'optimisation
        if context.operation_type == OperationType.OPTIMIZATION:
            variables.update({
                "optimization_type": context.metadata.get("optimization_type", "performance"),
                "improvement": f"{context.metadata.get('improvement_percent', 0):.1f}"
            })
        
        # Variables spécifiques au diagnostic
        if context.operation_type == OperationType.DIAGNOSTIC:
            variables.update({
                "component": context.metadata.get("component", "système"),
                "issue": context.metadata.get("issue", "problème détecté"),
                "issues_count": str(context.metadata.get("issues_count", 0))
            })
        
        # Variables spécifiques à l'initialisation
        if context.operation_type == OperationType.INITIALIZATION:
            variables.update({
                "component": context.metadata.get("component", "composant")
            })
        
        return variables
    
    def _calculate_eta(self, context: ProgressContext) -> Optional[float]:
        """Calcule l'ETA basé sur le contexte"""
        
        if context.estimated_duration:
            elapsed = time.time() - context.start_time if context.start_time else 0
            remaining = context.estimated_duration - elapsed
            return max(0, remaining)
        
        if context.progress_percent > 0 and context.start_time:
            elapsed = time.time() - context.start_time
            if elapsed > 0:
                total_estimated = elapsed * (100 / context.progress_percent)
                return max(0, total_estimated - elapsed)
        
        # ETA spécifique au téléchargement
        if (context.operation_type == OperationType.DOWNLOAD and 
            context.download_speed and context.total_bytes and context.downloaded_bytes):
            remaining_bytes = context.total_bytes - context.downloaded_bytes
            return remaining_bytes / context.download_speed
        
        return None
    
    def _determine_message_type(self, context: ProgressContext) -> MessageType:
        """Détermine le type de message"""
        
        if context.error_message:
            return MessageType.ERROR
        
        if context.progress_percent >= 100:
            return MessageType.SUCCESS
        
        # Warnings spécifiques
        if (context.operation_type == OperationType.DOWNLOAD and 
            context.download_speed and context.download_speed < 50000):  # < 50KB/s
            return MessageType.WARNING
        
        if (context.operation_type == OperationType.MODEL_LOADING and 
            context.memory_usage and context.memory_usage > 85):
            return MessageType.WARNING
        
        if context.operation_type == OperationType.FALLBACK:
            return MessageType.WARNING
        
        return MessageType.PROGRESS
    
    def _generate_details(self, context: ProgressContext) -> Dict[str, Any]:
        """Génère les détails additionnels"""
        
        details = {}
        
        # Détails temporels
        if context.start_time:
            details["elapsed_time"] = time.time() - context.start_time
        
        eta = self._calculate_eta(context)
        if eta:
            details["eta_seconds"] = eta
            details["eta_formatted"] = self._format_eta(eta)
        
        # Détails spécifiques au téléchargement
        if context.operation_type == OperationType.DOWNLOAD:
            if context.download_speed:
                details["download_speed"] = context.download_speed
                details["download_speed_formatted"] = self._format_download_speed(context.download_speed)
            
            if context.downloaded_bytes and context.total_bytes:
                details["progress_bytes"] = f"{context.downloaded_bytes}/{context.total_bytes}"
                details["progress_formatted"] = f"{self._format_file_size(context.downloaded_bytes)}/{self._format_file_size(context.total_bytes)}"
        
        # Détails système
        if context.gpu_usage is not None:
            details["gpu_usage"] = context.gpu_usage
        
        if context.memory_usage is not None:
            details["memory_usage"] = context.memory_usage
        
        if context.cache_hit_rate is not None:
            details["cache_hit_rate"] = context.cache_hit_rate
        
        # Détails d'étapes
        if context.total_steps and context.current_step_index is not None:
            details["step_progress"] = f"{context.current_step_index + 1}/{context.total_steps}"
        
        # Métadonnées additionnelles
        if context.metadata:
            details.update(context.metadata)
        
        return details
    
    def _generate_suggestions(self, context: ProgressContext) -> List[str]:
        """Génère des suggestions basées sur le contexte"""
        
        suggestions = []
        
        # Suggestions d'erreur
        if context.error_message:
            error_type = self._classify_error(context.error_message)
            suggestions.extend(self.error_solutions.get(error_type, []))
        
        # Suggestions de performance
        if context.operation_type == OperationType.DOWNLOAD:
            if context.download_speed and context.download_speed < 100000:  # < 100KB/s
                suggestions.extend([
                    "Vérifier la connexion internet",
                    "Essayer à un moment de moindre affluence",
                    "Utiliser un modèle plus léger si disponible"
                ])
        
        if context.operation_type == OperationType.TRANSCRIPTION:
            if context.progress_percent < 50 and context.start_time:
                elapsed = time.time() - context.start_time
                if elapsed > 30:  # Plus de 30 secondes
                    suggestions.extend([
                        "Considérer un modèle plus rapide",
                        "Vérifier les ressources système disponibles"
                    ])
        
        if context.operation_type == OperationType.MODEL_LOADING:
            if context.memory_usage and context.memory_usage > 85:
                suggestions.extend([
                    "Fermer d'autres applications",
                    "Utiliser un modèle plus léger",
                    "Redémarrer l'application"
                ])
        
        # Suggestions d'optimisation
        if context.operation_type == OperationType.OPTIMIZATION:
            suggestions.extend([
                "Les optimisations sont appliquées automatiquement",
                "Les performances s'amélioreront avec l'usage"
            ])
        
        # Ajouter les suggestions du contexte
        if context.suggested_solutions:
            suggestions.extend(context.suggested_solutions)
        
        return list(set(suggestions))  # Supprimer les doublons
    
    def _classify_error(self, error_message: str) -> str:
        """Classifie le type d'erreur"""
        
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ["cuda", "gpu", "device"]):
            return "cuda_error"
        
        if any(keyword in error_lower for keyword in ["memory", "ram", "out of memory"]):
            return "memory_error"
        
        if any(keyword in error_lower for keyword in ["network", "connection", "download", "http"]):
            return "network_error"
        
        if any(keyword in error_lower for keyword in ["model", "file", "corrupt", "invalid"]):
            return "model_error"
        
        if any(keyword in error_lower for keyword in ["timeout", "time out", "expired"]):
            return "timeout_error"
        
        return "general_error"
    
    def _format_language(self, language: Optional[str]) -> str:
        """Formate le nom de la langue"""
        if not language:
            return "auto"
        
        language_names = {
            "fr": "français",
            "en": "anglais",
            "es": "espagnol",
            "de": "allemand",
            "it": "italien",
            "pt": "portugais",
            "ru": "russe",
            "ja": "japonais",
            "ko": "coréen",
            "zh": "chinois",
            "ar": "arabe"
        }
        
        return language_names.get(language.lower(), language)
    
    def _format_quality(self, quality: Optional[str]) -> str:
        """Formate la préférence de qualité"""
        if not quality:
            return "équilibré"
        
        quality_names = {
            "speed": "rapide",
            "balanced": "équilibré",
            "quality": "qualité"
        }
        
        return quality_names.get(quality.lower(), quality)
    
    def _format_download_speed(self, speed: Optional[float]) -> str:
        """Formate la vitesse de téléchargement"""
        if not speed:
            return "0 B/s"
        
        if speed < 1024:
            return f"{speed:.0f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed/1024:.1f} KB/s"
        else:
            return f"{speed/(1024*1024):.1f} MB/s"
    
    def _format_file_size(self, size: Optional[int]) -> str:
        """Formate la taille de fichier"""
        if not size:
            return "0 B"
        
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.1f} GB"
    
    def _format_eta(self, eta_seconds: Optional[float]) -> str:
        """Formate l'ETA"""
        if not eta_seconds:
            return "inconnue"
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f}s"
        elif eta_seconds < 3600:
            minutes = eta_seconds / 60
            return f"{minutes:.1f}min"
        else:
            hours = eta_seconds / 3600
            return f"{hours:.1f}h"
    
    def create_summary_message(self, operation_type: OperationType, 
                             success: bool, duration: float, 
                             metrics: Dict[str, Any]) -> ContextualMessage:
        """Crée un message de résumé final"""
        
        if success:
            message_type = MessageType.SUCCESS
            if operation_type == OperationType.TRANSCRIPTION:
                message = f"✅ Transcription terminée en {duration:.1f}s"
                if metrics.get("quality_score"):
                    message += f" (qualité: {metrics['quality_score']:.1%})"
            
            elif operation_type == OperationType.DOWNLOAD:
                size = metrics.get("total_bytes", 0)
                message = f"✅ Téléchargement terminé: {self._format_file_size(size)} en {duration:.1f}s"
            
            elif operation_type == OperationType.MODEL_LOADING:
                message = f"✅ Modèle chargé et prêt en {duration:.1f}s"
            
            else:
                message = f"✅ Opération terminée en {duration:.1f}s"
        
        else:
            message_type = MessageType.ERROR
            error = metrics.get("error_message", "erreur inconnue")
            message = f"❌ Opération échouée après {duration:.1f}s: {error}"
        
        return ContextualMessage(
            message=message,
            message_type=message_type,
            progress_percent=100.0 if success else 0.0,
            details=metrics
        )

# Instance globale pour faciliter l'utilisation
message_generator = ContextualMessageGenerator()