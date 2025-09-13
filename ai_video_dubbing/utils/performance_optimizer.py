#!/usr/bin/env python3
"""
Optimiseur de performance et gestionnaire de mémoire pour l'application de doublage vidéo par IA.
"""

import gc
import os
import psutil
import threading
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np

from ..models.data_models import PipelineConfig


class OptimizationLevel(Enum):
    """Niveaux d'optimisation."""
    MINIMAL = "minimal"      # Optimisations de base
    BALANCED = "balanced"    # Équilibre performance/qualité
    AGGRESSIVE = "aggressive" # Optimisations maximales
    MEMORY_SAVER = "memory_saver"  # Priorité à l'économie mémoire


class ResourceType(Enum):
    """Types de ressources surveillées."""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    GPU = "gpu"


@dataclass
class ResourceUsage:
    """Utilisation des ressources à un instant donné."""
    timestamp: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    cpu_percent: float
    disk_usage_percent: float
    disk_free_gb: float
    gpu_memory_used: Optional[float] = None
    gpu_memory_total: Optional[float] = None


@dataclass
class OptimizationConfig:
    """Configuration des optimisations."""
    level: OptimizationLevel = OptimizationLevel.BALANCED
    max_memory_percent: float = 80.0
    max_cpu_percent: float = 90.0
    chunk_size_mb: int = 100
    enable_lazy_loading: bool = True
    enable_model_unloading: bool = True
    enable_garbage_collection: bool = True
    monitoring_interval: float = 1.0
    warning_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'memory': 75.0,
        'cpu': 85.0,
        'disk': 90.0
    })


class ModelManager:
    """Gestionnaire de modèles avec chargement paresseux."""
    
    def __init__(self):
        """Initialise le gestionnaire de modèles."""
        self.loaded_models: Dict[str, Any] = {}
        self.model_usage_count: Dict[str, int] = {}
        self.model_last_used: Dict[str, float] = {}
        self.model_memory_usage: Dict[str, float] = {}
        self.max_models_in_memory = 3
        self.model_timeout = 300.0  # 5 minutes
        self.logger = logging.getLogger(__name__)
        
        # Thread de nettoyage automatique
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Démarre le thread de nettoyage automatique."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(60):  # Vérification toutes les minutes
                self._cleanup_unused_models()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def load_model(self, model_name: str, model_loader: Callable) -> Any:
        """
        Charge un modèle avec gestion paresseuse.
        
        Args:
            model_name: Nom du modèle
            model_loader: Fonction pour charger le modèle
            
        Returns:
            Le modèle chargé
        """
        # Si le modèle est déjà chargé
        if model_name in self.loaded_models:
            self.model_usage_count[model_name] += 1
            self.model_last_used[model_name] = time.time()
            self.logger.debug(f"Modèle {model_name} réutilisé (usage: {self.model_usage_count[model_name]})")
            return self.loaded_models[model_name]
        
        # Vérifier si on doit libérer de la mémoire
        if len(self.loaded_models) >= self.max_models_in_memory:
            self._unload_least_used_model()
        
        # Charger le nouveau modèle
        self.logger.info(f"Chargement du modèle: {model_name}")
        start_time = time.time()
        
        try:
            model = model_loader()
            load_time = time.time() - start_time
            
            # Estimer l'utilisation mémoire
            memory_usage = self._estimate_model_memory(model)
            
            # Stocker le modèle
            self.loaded_models[model_name] = model
            self.model_usage_count[model_name] = 1
            self.model_last_used[model_name] = time.time()
            self.model_memory_usage[model_name] = memory_usage
            
            self.logger.info(f"Modèle {model_name} chargé en {load_time:.2f}s (mémoire: {memory_usage:.1f}MB)")
            return model
            
        except Exception as e:
            self.logger.error(f"Erreur chargement modèle {model_name}: {e}")
            raise
    
    def unload_model(self, model_name: str):
        """Décharge un modèle spécifique."""
        if model_name in self.loaded_models:
            memory_freed = self.model_memory_usage.get(model_name, 0)
            
            del self.loaded_models[model_name]
            self.model_usage_count.pop(model_name, None)
            self.model_last_used.pop(model_name, None)
            self.model_memory_usage.pop(model_name, None)
            
            # Forcer le garbage collection
            gc.collect()
            
            self.logger.info(f"Modèle {model_name} déchargé (mémoire libérée: {memory_freed:.1f}MB)")
    
    def _unload_least_used_model(self):
        """Décharge le modèle le moins utilisé."""
        if not self.loaded_models:
            return
        
        # Trouver le modèle le moins récemment utilisé
        least_used_model = min(
            self.model_last_used.keys(),
            key=lambda x: self.model_last_used[x]
        )
        
        self.unload_model(least_used_model)
    
    def _cleanup_unused_models(self):
        """Nettoie les modèles non utilisés depuis longtemps."""
        current_time = time.time()
        models_to_unload = []
        
        for model_name, last_used in self.model_last_used.items():
            if current_time - last_used > self.model_timeout:
                models_to_unload.append(model_name)
        
        for model_name in models_to_unload:
            self.unload_model(model_name)
    
    def _estimate_model_memory(self, model) -> float:
        """Estime l'utilisation mémoire d'un modèle en MB."""
        try:
            # Pour les modèles PyTorch
            if hasattr(model, 'parameters'):
                total_params = sum(p.numel() for p in model.parameters())
                # Estimation: 4 bytes par paramètre (float32)
                return (total_params * 4) / (1024 * 1024)
            
            # Pour les arrays numpy
            elif hasattr(model, 'nbytes'):
                return model.nbytes / (1024 * 1024)
            
            # Estimation générique
            else:
                return 100.0  # 100MB par défaut
                
        except Exception:
            return 100.0
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Retourne l'utilisation mémoire par modèle."""
        return self.model_memory_usage.copy()
    
    def cleanup(self):
        """Nettoie tous les modèles et arrête les threads."""
        self._stop_cleanup.set()
        
        for model_name in list(self.loaded_models.keys()):
            self.unload_model(model_name)
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)


class ChunkProcessor:
    """Processeur pour traitement par chunks des gros fichiers."""
    
    def __init__(self, chunk_size_mb: int = 100):
        """
        Initialise le processeur de chunks.
        
        Args:
            chunk_size_mb: Taille des chunks en MB
        """
        self.chunk_size_mb = chunk_size_mb
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
    
    def process_audio_chunks(self, audio_data: np.ndarray, sample_rate: int,
                           processor_func: Callable, **kwargs) -> np.ndarray:
        """
        Traite l'audio par chunks.
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            processor_func: Fonction de traitement
            **kwargs: Arguments pour la fonction de traitement
            
        Returns:
            Audio traité
        """
        # Calculer la taille des chunks en échantillons
        bytes_per_sample = audio_data.dtype.itemsize * audio_data.shape[-1] if len(audio_data.shape) > 1 else audio_data.dtype.itemsize
        samples_per_chunk = self.chunk_size_bytes // bytes_per_sample
        
        if len(audio_data) <= samples_per_chunk:
            # Fichier assez petit, traitement direct
            return processor_func(audio_data, sample_rate, **kwargs)
        
        # Traitement par chunks
        self.logger.info(f"Traitement par chunks: {len(audio_data)} échantillons, chunks de {samples_per_chunk}")
        
        processed_chunks = []
        overlap_samples = int(0.1 * sample_rate)  # 100ms d'overlap
        
        for i in range(0, len(audio_data), samples_per_chunk - overlap_samples):
            end_idx = min(i + samples_per_chunk, len(audio_data))
            chunk = audio_data[i:end_idx]
            
            # Traiter le chunk
            processed_chunk = processor_func(chunk, sample_rate, **kwargs)
            
            # Gérer l'overlap pour éviter les artefacts
            if i > 0 and overlap_samples > 0:
                # Fondu croisé sur l'overlap
                fade_samples = min(overlap_samples, len(processed_chunk))
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                
                if len(processed_chunks) > 0:
                    # Appliquer le fondu sur la fin du chunk précédent
                    prev_chunk = processed_chunks[-1]
                    if len(prev_chunk) >= fade_samples:
                        prev_chunk[-fade_samples:] *= fade_out
                    
                    # Appliquer le fondu sur le début du chunk actuel
                    processed_chunk[:fade_samples] *= fade_in
                    
                    # Additionner l'overlap
                    if len(prev_chunk) >= fade_samples and len(processed_chunk) >= fade_samples:
                        processed_chunk[:fade_samples] += prev_chunk[-fade_samples:]
                        processed_chunks[-1] = prev_chunk[:-fade_samples]
            
            processed_chunks.append(processed_chunk)
            
            # Forcer le garbage collection après chaque chunk
            gc.collect()
        
        # Concaténer tous les chunks
        return np.concatenate(processed_chunks)
    
    def process_video_chunks(self, video_path: str, processor_func: Callable,
                           output_path: str, **kwargs):
        """
        Traite une vidéo par segments temporels.
        
        Args:
            video_path: Chemin vers la vidéo
            processor_func: Fonction de traitement
            output_path: Chemin de sortie
            **kwargs: Arguments pour la fonction de traitement
        """
        try:
            import cv2
        except ImportError:
            raise ImportError("OpenCV requis pour le traitement vidéo par chunks")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")
        
        # Propriétés de la vidéo
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculer la taille des chunks en frames
        frames_per_chunk = min(int(fps * 30), total_frames // 10)  # Max 30s ou 10% du total
        
        self.logger.info(f"Traitement vidéo par chunks: {total_frames} frames, chunks de {frames_per_chunk}")
        
        # Préparer l'écriture
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        try:
            for start_frame in range(0, total_frames, frames_per_chunk):
                end_frame = min(start_frame + frames_per_chunk, total_frames)
                
                # Lire le chunk
                frames = []
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                
                for _ in range(end_frame - start_frame):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                
                if not frames:
                    break
                
                # Traiter le chunk
                processed_frames = processor_func(frames, **kwargs)
                
                # Écrire les frames traitées
                for frame in processed_frames:
                    out.write(frame)
                
                # Libérer la mémoire
                del frames, processed_frames
                gc.collect()
                
                self.logger.debug(f"Chunk traité: frames {start_frame}-{end_frame}")
        
        finally:
            cap.release()
            out.release()


class ResourceMonitor:
    """Moniteur de ressources système avec alertes."""
    
    def __init__(self, config: OptimizationConfig):
        """
        Initialise le moniteur de ressources.
        
        Args:
            config: Configuration d'optimisation
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Historique des mesures
        self.usage_history: List[ResourceUsage] = []
        self.max_history_size = 1000
        
        # Callbacks d'alerte
        self.warning_callbacks: List[Callable[[ResourceType, float], None]] = []
        
        # Thread de monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._is_monitoring = False
    
    def start_monitoring(self):
        """Démarre le monitoring des ressources."""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._stop_monitoring.clear()
        
        def monitor_worker():
            while not self._stop_monitoring.wait(self.config.monitoring_interval):
                try:
                    usage = self._collect_resource_usage()
                    self._add_usage_record(usage)
                    self._check_thresholds(usage)
                except Exception as e:
                    self.logger.error(f"Erreur monitoring ressources: {e}")
        
        self._monitoring_thread = threading.Thread(target=monitor_worker, daemon=True)
        self._monitoring_thread.start()
        
        self.logger.info("Monitoring des ressources démarré")
    
    def stop_monitoring(self):
        """Arrête le monitoring des ressources."""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        self._stop_monitoring.set()
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        
        self.logger.info("Monitoring des ressources arrêté")
    
    def _collect_resource_usage(self) -> ResourceUsage:
        """Collecte l'utilisation actuelle des ressources."""
        # Mémoire
        memory = psutil.virtual_memory()
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Disque
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        
        # GPU (optionnel)
        gpu_memory_used = None
        gpu_memory_total = None
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Premier GPU
                gpu_memory_used = gpu.memoryUsed
                gpu_memory_total = gpu.memoryTotal
        except ImportError:
            pass
        except Exception as e:
            self.logger.debug(f"Erreur lecture GPU: {e}")
        
        return ResourceUsage(
            timestamp=time.time(),
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            cpu_percent=cpu_percent,
            disk_usage_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            gpu_memory_used=gpu_memory_used,
            gpu_memory_total=gpu_memory_total
        )
    
    def _add_usage_record(self, usage: ResourceUsage):
        """Ajoute un enregistrement d'utilisation à l'historique."""
        self.usage_history.append(usage)
        
        # Limiter la taille de l'historique
        if len(self.usage_history) > self.max_history_size:
            self.usage_history = self.usage_history[-self.max_history_size//2:]
    
    def _check_thresholds(self, usage: ResourceUsage):
        """Vérifie les seuils et déclenche les alertes."""
        # Vérifier la mémoire
        if usage.memory_percent > self.config.warning_thresholds['memory']:
            self._trigger_warning(ResourceType.MEMORY, usage.memory_percent)
        
        # Vérifier le CPU
        if usage.cpu_percent > self.config.warning_thresholds['cpu']:
            self._trigger_warning(ResourceType.CPU, usage.cpu_percent)
        
        # Vérifier le disque
        if usage.disk_usage_percent > self.config.warning_thresholds['disk']:
            self._trigger_warning(ResourceType.DISK, usage.disk_usage_percent)
    
    def _trigger_warning(self, resource_type: ResourceType, value: float):
        """Déclenche une alerte de ressource."""
        self.logger.warning(f"Seuil dépassé - {resource_type.value}: {value:.1f}%")
        
        for callback in self.warning_callbacks:
            try:
                callback(resource_type, value)
            except Exception as e:
                self.logger.error(f"Erreur callback alerte: {e}")
    
    def register_warning_callback(self, callback: Callable[[ResourceType, float], None]):
        """Enregistre un callback d'alerte."""
        self.warning_callbacks.append(callback)
    
    def get_current_usage(self) -> Optional[ResourceUsage]:
        """Retourne l'utilisation actuelle des ressources."""
        if self.usage_history:
            return self.usage_history[-1]
        return self._collect_resource_usage()
    
    def get_usage_history(self, duration_minutes: int = 10) -> List[ResourceUsage]:
        """Retourne l'historique d'utilisation sur une période."""
        if not self.usage_history:
            return []
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [usage for usage in self.usage_history if usage.timestamp >= cutoff_time]
    
    def get_average_usage(self, duration_minutes: int = 5) -> Dict[str, float]:
        """Calcule l'utilisation moyenne sur une période."""
        history = self.get_usage_history(duration_minutes)
        
        if not history:
            return {}
        
        return {
            'memory_percent': sum(u.memory_percent for u in history) / len(history),
            'cpu_percent': sum(u.cpu_percent for u in history) / len(history),
            'disk_percent': sum(u.disk_usage_percent for u in history) / len(history)
        }


class PerformanceOptimizer:
    """Optimiseur de performance principal."""
    
    def __init__(self, config: OptimizationConfig = None):
        """
        Initialise l'optimiseur de performance.
        
        Args:
            config: Configuration d'optimisation
        """
        self.config = config or OptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Composants
        self.model_manager = ModelManager()
        self.chunk_processor = ChunkProcessor(self.config.chunk_size_mb)
        self.resource_monitor = ResourceMonitor(self.config)
        
        # État
        self.is_optimizing = False
        
        # Enregistrer les callbacks d'alerte
        self.resource_monitor.register_warning_callback(self._on_resource_warning)
    
    def start_optimization(self):
        """Démarre l'optimisation."""
        if self.is_optimizing:
            return
        
        self.is_optimizing = True
        self.resource_monitor.start_monitoring()
        
        self.logger.info(f"Optimisation démarrée (niveau: {self.config.level.value})")
    
    def stop_optimization(self):
        """Arrête l'optimisation."""
        if not self.is_optimizing:
            return
        
        self.is_optimizing = False
        self.resource_monitor.stop_monitoring()
        self.model_manager.cleanup()
        
        self.logger.info("Optimisation arrêtée")
    
    def _on_resource_warning(self, resource_type: ResourceType, value: float):
        """Appelé lors d'une alerte de ressource."""
        self.logger.warning(f"Alerte ressource: {resource_type.value} = {value:.1f}%")
        
        # Actions d'optimisation automatique
        if resource_type == ResourceType.MEMORY:
            self._optimize_memory_usage()
        elif resource_type == ResourceType.CPU:
            self._optimize_cpu_usage()
    
    def _optimize_memory_usage(self):
        """Optimise l'utilisation mémoire."""
        self.logger.info("Optimisation mémoire en cours...")
        
        # Décharger les modèles les moins utilisés
        if self.config.enable_model_unloading:
            self.model_manager._cleanup_unused_models()
        
        # Forcer le garbage collection
        if self.config.enable_garbage_collection:
            gc.collect()
        
        # Réduire la taille des chunks si nécessaire
        current_usage = self.resource_monitor.get_current_usage()
        if current_usage and current_usage.memory_percent > self.config.max_memory_percent:
            new_chunk_size = max(10, self.config.chunk_size_mb // 2)
            self.chunk_processor.chunk_size_mb = new_chunk_size
            self.chunk_processor.chunk_size_bytes = new_chunk_size * 1024 * 1024
            self.logger.info(f"Taille des chunks réduite à {new_chunk_size}MB")
    
    def _optimize_cpu_usage(self):
        """Optimise l'utilisation CPU."""
        self.logger.info("Optimisation CPU en cours...")
        
        # Réduire le nombre de threads si possible
        try:
            import torch
            if torch.get_num_threads() > 1:
                torch.set_num_threads(max(1, torch.get_num_threads() // 2))
                self.logger.info(f"Threads PyTorch réduits à {torch.get_num_threads()}")
        except ImportError:
            pass
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'optimisation."""
        current_usage = self.resource_monitor.get_current_usage()
        model_memory = self.model_manager.get_memory_usage()
        
        return {
            'optimization_level': self.config.level.value,
            'is_optimizing': self.is_optimizing,
            'current_usage': {
                'memory_percent': current_usage.memory_percent if current_usage else 0,
                'cpu_percent': current_usage.cpu_percent if current_usage else 0,
                'disk_percent': current_usage.disk_usage_percent if current_usage else 0
            },
            'loaded_models': list(self.model_manager.loaded_models.keys()),
            'model_memory_usage': model_memory,
            'chunk_size_mb': self.chunk_processor.chunk_size_mb,
            'thresholds': self.config.warning_thresholds
        }
    
    def cleanup(self):
        """Nettoie toutes les ressources."""
        self.stop_optimization()


# Instance globale de l'optimiseur
global_optimizer = None


def get_performance_optimizer(config: OptimizationConfig = None) -> PerformanceOptimizer:
    """Retourne l'instance globale de l'optimiseur de performance."""
    global global_optimizer
    
    if global_optimizer is None:
        global_optimizer = PerformanceOptimizer(config)
    
    return global_optimizer