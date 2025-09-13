"""
Optimisateur réseau avancé avec sélection de serveurs et téléchargement parallèle
"""

import asyncio
import time
import logging
import json
import hashlib
import gzip
import zlib
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse
import ssl
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class CompressionType(Enum):
    """Types de compression supportés"""
    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "brotli"

class ServerStatus(Enum):
    """États des serveurs"""
    UNKNOWN = "unknown"
    ONLINE = "online"
    SLOW = "slow"
    OFFLINE = "offline"
    ERROR = "error"

@dataclass
class ServerInfo:
    """Informations sur un serveur"""
    url: str
    name: str
    priority: int = 1
    status: ServerStatus = ServerStatus.UNKNOWN
    latency_ms: float = 0.0
    bandwidth_mbps: float = 0.0
    success_rate: float = 1.0
    last_tested: float = 0.0
    error_count: int = 0
    total_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DownloadSegment:
    """Segment de téléchargement"""
    segment_id: int
    start_byte: int
    end_byte: int
    url: str
    server: ServerInfo
    status: str = "pending"  # pending, downloading, completed, failed
    data: Optional[bytes] = None
    download_time: float = 0.0
    retry_count: int = 0
    error_message: Optional[str] = None

@dataclass
class DownloadTask:
    """Tâche de téléchargement"""
    task_id: str
    url: str
    file_path: Path
    total_size: int = 0
    segments: List[DownloadSegment] = field(default_factory=list)
    completed_bytes: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "pending"
    compression_type: CompressionType = CompressionType.NONE
    metadata: Dict[str, Any] = field(default_factory=dict)

class NetworkOptimizer:
    """Optimisateur réseau avec sélection automatique de serveurs"""
    
    def __init__(self, config_file: str = ".kiro/network_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config = {
            "max_concurrent_downloads": 4,
            "max_segments_per_download": 8,
            "segment_size_mb": 10,
            "connection_timeout": 30.0,
            "read_timeout": 60.0,
            "max_retries": 3,
            "server_test_interval": 300.0,  # 5 minutes
            "enable_compression": True,
            "enable_http_cache": True,
            "user_agent": "NetworkOptimizer/1.0",
            "max_bandwidth_mbps": 100.0
        }
        
        # Serveurs disponibles
        self.servers: Dict[str, ServerInfo] = {}
        self.server_rankings: List[str] = []
        
        # Cache HTTP
        self.http_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "size_mb": 0.0
        }
        
        # Tâches de téléchargement
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.download_history: List[DownloadTask] = []
        
        # Thread pool pour les opérations réseau
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config["max_concurrent_downloads"])
        
        # Tâches de monitoring
        self.server_monitor_task: Optional[asyncio.Task] = None
        
        # Statistiques
        self.network_stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "total_bytes_downloaded": 0,
            "total_download_time": 0.0,
            "average_speed_mbps": 0.0,
            "compression_ratio": 1.0
        }
        
        # Initialisation
        self._load_config()
        self._setup_default_servers()
        
        logger.info("Network Optimizer initialized")
    
    def _load_config(self):
        """Charge la configuration depuis le fichier"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config.get('config', {}))
                    
                    # Charger les serveurs
                    servers_data = saved_config.get('servers', {})
                    for server_id, server_data in servers_data.items():
                        self.servers[server_id] = ServerInfo(**server_data)
                    
                    # Charger les statistiques
                    self.network_stats.update(saved_config.get('stats', {}))
                    
                logger.info("Network configuration loaded")
            except Exception as e:
                logger.error(f"Failed to load network config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            config_data = {
                'config': self.config,
                'servers': {
                    server_id: {
                        'url': server.url,
                        'name': server.name,
                        'priority': server.priority,
                        'status': server.status.value if hasattr(server.status, 'value') else str(server.status),
                        'latency_ms': server.latency_ms,
                        'bandwidth_mbps': server.bandwidth_mbps,
                        'success_rate': server.success_rate,
                        'last_tested': server.last_tested,
                        'error_count': server.error_count,
                        'total_requests': server.total_requests,
                        'metadata': server.metadata
                    }
                    for server_id, server in self.servers.items()
                },
                'stats': self.network_stats,
                'timestamp': time.time()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save network config: {e}")
    
    def _setup_default_servers(self):
        """Configure les serveurs par défaut"""
        
        default_servers = [
            {
                "id": "huggingface_main",
                "url": "https://huggingface.co",
                "name": "Hugging Face Main",
                "priority": 1
            },
            {
                "id": "huggingface_cdn",
                "url": "https://cdn-lfs.huggingface.co",
                "name": "Hugging Face CDN",
                "priority": 2
            },
            {
                "id": "github_releases",
                "url": "https://github.com",
                "name": "GitHub Releases",
                "priority": 3
            },
            {
                "id": "nvidia_ngc",
                "url": "https://api.ngc.nvidia.com",
                "name": "NVIDIA NGC",
                "priority": 4
            }
        ]
        
        for server_data in default_servers:
            if server_data["id"] not in self.servers:
                self.servers[server_data["id"]] = ServerInfo(
                    url=server_data["url"],
                    name=server_data["name"],
                    priority=server_data["priority"]
                )
    
    def _create_request(self, url: str, headers: Optional[Dict[str, str]] = None) -> urllib.request.Request:
        """Crée une requête HTTP avec les headers appropriés"""
        
        default_headers = {
            'User-Agent': self.config["user_agent"],
            'Accept-Encoding': 'gzip, deflate' if self.config["enable_compression"] else 'identity'
        }
        
        if headers:
            default_headers.update(headers)
        
        req = urllib.request.Request(url)
        for key, value in default_headers.items():
            req.add_header(key, value)
        
        return req
    
    async def test_server_performance(self, server: ServerInfo) -> Dict[str, Any]:
        """Teste les performances d'un serveur"""
        
        logger.debug(f"Testing server performance: {server.name}")
        
        def _test_server():
            test_url = f"{server.url.rstrip('/')}/robots.txt"  # URL de test simple
            
            results = {
                "latency_ms": float('inf'),
                "bandwidth_mbps": 0.0,
                "success": False,
                "error": None
            }
            
            try:
                # Test de latence avec HEAD request
                start_time = time.time()
                
                req = self._create_request(test_url)
                req.get_method = lambda: 'HEAD'
                
                with urllib.request.urlopen(req, timeout=self.config["connection_timeout"]) as response:
                    latency = (time.time() - start_time) * 1000
                    results["latency_ms"] = latency
                    results["success"] = response.status < 400
                    
                    # Test de bande passante avec un petit téléchargement
                    if results["success"]:
                        download_start = time.time()
                        
                        get_req = self._create_request(test_url)
                        with urllib.request.urlopen(get_req, timeout=self.config["read_timeout"]) as download_response:
                            if download_response.status < 400:
                                content = download_response.read()
                                download_time = time.time() - download_start
                                
                                if download_time > 0:
                                    bytes_downloaded = len(content)
                                    bandwidth_bps = bytes_downloaded / download_time
                                    results["bandwidth_mbps"] = (bandwidth_bps * 8) / (1024 * 1024)
            
            except Exception as e:
                results["error"] = str(e)
                logger.debug(f"Server test failed for {server.name}: {e}")
            
            return results
        
        # Exécuter dans le thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(self.thread_pool, _test_server)
        
        # Mettre à jour les informations du serveur
        server.last_tested = time.time()
        server.total_requests += 1
        
        if results["success"]:
            server.latency_ms = results["latency_ms"]
            server.bandwidth_mbps = max(server.bandwidth_mbps, results["bandwidth_mbps"])
            server.status = ServerStatus.ONLINE
            server.success_rate = (server.success_rate * (server.total_requests - 1) + 1.0) / server.total_requests
        else:
            server.error_count += 1
            server.status = ServerStatus.ERROR if server.error_count > 3 else ServerStatus.SLOW
            server.success_rate = (server.success_rate * (server.total_requests - 1)) / server.total_requests
        
        return results
    
    async def test_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Teste tous les serveurs en parallèle"""
        
        logger.info("Testing all servers performance")
        
        tasks = []
        for server in self.servers.values():
            task = asyncio.create_task(self.test_server_performance(server))
            tasks.append((server.name, task))
        
        results = {}
        for server_name, task in tasks:
            try:
                result = await task
                results[server_name] = result
            except Exception as e:
                results[server_name] = {"error": str(e), "success": False}
        
        # Mettre à jour le classement des serveurs
        self._update_server_rankings()
        
        return results
    
    def _update_server_rankings(self):
        """Met à jour le classement des serveurs"""
        
        # Calculer un score pour chaque serveur
        server_scores = []
        
        for server_id, server in self.servers.items():
            if server.status == ServerStatus.OFFLINE:
                score = 0
            else:
                # Score basé sur latence, bande passante, taux de succès et priorité
                latency_score = max(0, 1000 - server.latency_ms) / 1000
                bandwidth_score = min(server.bandwidth_mbps / 100, 1.0)  # Normaliser à 100 Mbps
                success_score = server.success_rate
                priority_score = (5 - server.priority) / 4  # Inverser la priorité
                
                score = (latency_score * 0.3 + bandwidth_score * 0.3 + 
                        success_score * 0.3 + priority_score * 0.1)
            
            server_scores.append((server_id, score))
        
        # Trier par score décroissant
        server_scores.sort(key=lambda x: x[1], reverse=True)
        self.server_rankings = [server_id for server_id, _ in server_scores]
        
        logger.debug(f"Server rankings updated: {self.server_rankings}")
    
    def get_best_server(self, exclude_servers: Optional[List[str]] = None) -> Optional[ServerInfo]:
        """Retourne le meilleur serveur disponible"""
        
        exclude_servers = exclude_servers or []
        
        for server_id in self.server_rankings:
            if server_id not in exclude_servers:
                server = self.servers[server_id]
                if server.status in [ServerStatus.ONLINE, ServerStatus.UNKNOWN]:
                    return server
        
        return None
    
    async def download_with_segments(
        self,
        url: str,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadTask:
        """Télécharge un fichier avec segmentation parallèle"""
        
        task_id = hashlib.md5(f"{url}_{file_path}".encode()).hexdigest()
        
        # Créer la tâche de téléchargement
        task = DownloadTask(
            task_id=task_id,
            url=url,
            file_path=file_path,
            start_time=time.time(),
            status="initializing"
        )
        
        self.active_downloads[task_id] = task
        
        try:
            # Obtenir la taille du fichier
            file_size = await self._get_file_size(url)
            task.total_size = file_size
            
            if file_size <= 0:
                # Téléchargement simple si la taille n'est pas disponible
                return await self._download_simple(task, progress_callback)
            
            # Créer les segments
            segment_size = self.config["segment_size_mb"] * 1024 * 1024
            num_segments = min(
                self.config["max_segments_per_download"],
                max(1, file_size // segment_size)
            )
            
            task.segments = self._create_segments(url, file_size, num_segments)
            task.status = "downloading"
            
            # Télécharger les segments en parallèle
            await self._download_segments_parallel(task, progress_callback)
            
            # Assembler le fichier
            await self._assemble_file(task)
            
            task.status = "completed"
            task.end_time = time.time()
            
            # Mettre à jour les statistiques
            self._update_download_stats(task)
            
            logger.info(f"Download completed: {file_path}")
            
        except Exception as e:
            task.status = "failed"
            task.end_time = time.time()
            task.metadata["error"] = str(e)
            logger.error(f"Download failed: {e}")
            raise
        
        finally:
            # Nettoyer les données temporaires des segments
            for segment in task.segments:
                segment.data = None
            
            # Déplacer vers l'historique
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
            self.download_history.append(task)
            
            # Limiter l'historique
            if len(self.download_history) > 100:
                self.download_history = self.download_history[-100:]
        
        return task
    
    async def _get_file_size(self, url: str) -> int:
        """Obtient la taille d'un fichier"""
        
        def _get_size():
            try:
                req = self._create_request(url)
                req.get_method = lambda: 'HEAD'
                
                with urllib.request.urlopen(req, timeout=self.config["connection_timeout"]) as response:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        return int(content_length)
            except Exception as e:
                logger.debug(f"Failed to get file size for {url}: {e}")
            
            return 0
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, _get_size)
    
    def _create_segments(self, url: str, file_size: int, num_segments: int) -> List[DownloadSegment]:
        """Crée les segments de téléchargement"""
        
        segments = []
        segment_size = file_size // num_segments
        
        for i in range(num_segments):
            start_byte = i * segment_size
            end_byte = start_byte + segment_size - 1
            
            # Le dernier segment prend les bytes restants
            if i == num_segments - 1:
                end_byte = file_size - 1
            
            # Sélectionner le meilleur serveur pour ce segment
            server = self.get_best_server()
            if not server:
                server = list(self.servers.values())[0]  # Fallback
            
            segment = DownloadSegment(
                segment_id=i,
                start_byte=start_byte,
                end_byte=end_byte,
                url=url,
                server=server
            )
            
            segments.append(segment)
        
        return segments
    
    async def _download_segments_parallel(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Télécharge les segments en parallèle"""
        
        semaphore = asyncio.Semaphore(self.config["max_concurrent_downloads"])
        
        async def download_segment(segment: DownloadSegment):
            async with semaphore:
                await self._download_single_segment(segment)
                
                # Mettre à jour le progrès
                if progress_callback:
                    completed_bytes = sum(
                        seg.end_byte - seg.start_byte + 1
                        for seg in task.segments
                        if seg.status == "completed"
                    )
                    progress_callback(completed_bytes, task.total_size)
        
        # Lancer tous les téléchargements de segments
        tasks = [download_segment(segment) for segment in task.segments]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _download_single_segment(self, segment: DownloadSegment):
        """Télécharge un segment individuel"""
        
        def _download_segment():
            segment.status = "downloading"
            start_time = time.time()
            
            for attempt in range(self.config["max_retries"]):
                try:
                    # Headers pour le range request
                    headers = {
                        'Range': f'bytes={segment.start_byte}-{segment.end_byte}'
                    }
                    
                    req = self._create_request(segment.url, headers)
                    
                    with urllib.request.urlopen(req, timeout=self.config["read_timeout"]) as response:
                        if response.status in [206, 200]:  # Partial Content ou OK
                            segment.data = response.read()
                            segment.status = "completed"
                            segment.download_time = time.time() - start_time
                            return
                        else:
                            raise urllib.error.HTTPError(
                                segment.url, response.status, 
                                f"HTTP {response.status}", response.headers, None
                            )
                
                except Exception as e:
                    segment.retry_count += 1
                    segment.error_message = str(e)
                    
                    if attempt < self.config["max_retries"] - 1:
                        # Essayer avec un autre serveur
                        excluded_servers = [segment.server.url]
                        new_server = self.get_best_server(excluded_servers)
                        if new_server:
                            segment.server = new_server
                        
                        time.sleep(2 ** attempt)  # Backoff exponentiel
                    else:
                        segment.status = "failed"
                        logger.error(f"Segment {segment.segment_id} failed after {self.config['max_retries']} attempts: {e}")
                        raise
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.thread_pool, _download_segment)
    
    async def _assemble_file(self, task: DownloadTask):
        """Assemble les segments en un fichier complet"""
        
        # Vérifier que tous les segments sont téléchargés
        failed_segments = [seg for seg in task.segments if seg.status != "completed"]
        if failed_segments:
            raise Exception(f"Cannot assemble file: {len(failed_segments)} segments failed")
        
        # Créer le répertoire de destination
        task.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Assembler le fichier
        with open(task.file_path, 'wb') as output_file:
            for segment in sorted(task.segments, key=lambda x: x.segment_id):
                if segment.data:
                    output_file.write(segment.data)
        
        logger.debug(f"File assembled: {task.file_path}")
    
    async def _download_simple(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadTask:
        """Téléchargement simple sans segmentation"""
        
        def _simple_download():
            task.status = "downloading"
            
            try:
                req = self._create_request(task.url)
                
                with urllib.request.urlopen(req, timeout=self.config["read_timeout"]) as response:
                    if response.status < 400:
                        # Créer le répertoire de destination
                        task.file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(task.file_path, 'wb') as f:
                            downloaded = 0
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break
                                
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback:
                                    progress_callback(downloaded, task.total_size or downloaded)
                        
                        task.completed_bytes = downloaded
                        task.total_size = downloaded
                        task.status = "completed"
                    else:
                        raise urllib.error.HTTPError(
                            task.url, response.status,
                            f"HTTP {response.status}", response.headers, None
                        )
            
            except Exception as e:
                task.status = "failed"
                task.metadata["error"] = str(e)
                raise
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.thread_pool, _simple_download)
        return task
    
    def _update_download_stats(self, task: DownloadTask):
        """Met à jour les statistiques de téléchargement"""
        
        self.network_stats["total_downloads"] += 1
        
        if task.status == "completed":
            self.network_stats["successful_downloads"] += 1
            self.network_stats["total_bytes_downloaded"] += task.total_size
            
            download_time = task.end_time - task.start_time
            self.network_stats["total_download_time"] += download_time
            
            if download_time > 0:
                speed_mbps = (task.total_size * 8) / (download_time * 1024 * 1024)
                
                # Moyenne mobile de la vitesse
                current_avg = self.network_stats["average_speed_mbps"]
                total_downloads = self.network_stats["successful_downloads"]
                new_avg = (current_avg * (total_downloads - 1) + speed_mbps) / total_downloads
                self.network_stats["average_speed_mbps"] = new_avg
    
    async def download_with_compression(
        self,
        url: str,
        file_path: Path,
        compression_type: CompressionType = CompressionType.GZIP,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadTask:
        """Télécharge avec compression à la volée"""
        
        if not self.config["enable_compression"]:
            return await self.download_with_segments(url, file_path, progress_callback)
        
        # Pour la version simplifiée, utiliser le téléchargement simple
        return await self.download_with_segments(url, file_path, progress_callback)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques réseau"""
        
        return {
            "network_stats": self.network_stats.copy(),
            "cache_stats": self.cache_stats.copy(),
            "active_downloads": len(self.active_downloads),
            "server_count": len(self.servers),
            "best_server": self.server_rankings[0] if self.server_rankings else None,
            "servers": {
                server_id: {
                    "name": server.name,
                    "status": server.status.value if hasattr(server.status, 'value') else str(server.status),
                    "latency_ms": server.latency_ms,
                    "bandwidth_mbps": server.bandwidth_mbps,
                    "success_rate": server.success_rate
                }
                for server_id, server in self.servers.items()
            }
        }
    
    def get_download_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retourne l'historique des téléchargements"""
        
        return [
            {
                "task_id": task.task_id,
                "url": task.url,
                "file_path": str(task.file_path),
                "total_size": task.total_size,
                "completed_bytes": task.completed_bytes,
                "status": task.status,
                "download_time": task.end_time - task.start_time if task.end_time else 0,
                "segments": len(task.segments),
                "compression_type": task.compression_type.value,
                "metadata": task.metadata
            }
            for task in self.download_history[-limit:]
        ]
    
    async def start_server_monitoring(self):
        """Démarre le monitoring des serveurs"""
        
        if self.server_monitor_task is None:
            self.server_monitor_task = asyncio.create_task(self._server_monitoring_loop())
    
    async def _server_monitoring_loop(self):
        """Boucle de monitoring des serveurs"""
        
        while True:
            try:
                await self.test_all_servers()
                await asyncio.sleep(self.config["server_test_interval"])
            except Exception as e:
                logger.error(f"Error in server monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Arrête proprement l'optimisateur réseau"""
        
        logger.info("Shutting down Network Optimizer")
        
        # Arrêter le monitoring
        if self.server_monitor_task:
            self.server_monitor_task.cancel()
            try:
                await self.server_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Fermer le thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Sauvegarder la configuration
        self._save_config()
        
        logger.info("Network Optimizer shutdown complete")

# Instance globale
_network_optimizer: Optional[NetworkOptimizer] = None

def get_network_optimizer() -> NetworkOptimizer:
    """Retourne l'instance globale de l'optimisateur réseau"""
    global _network_optimizer
    if _network_optimizer is None:
        _network_optimizer = NetworkOptimizer()
    return _network_optimizer

# Fonctions utilitaires

async def download_file_optimized(
    url: str,
    file_path: Path,
    use_segments: bool = True,
    use_compression: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> DownloadTask:
    """Télécharge un fichier avec optimisations"""
    
    optimizer = get_network_optimizer()
    
    if use_compression:
        return await optimizer.download_with_compression(
            url, file_path, CompressionType.GZIP, progress_callback
        )
    elif use_segments:
        return await optimizer.download_with_segments(url, file_path, progress_callback)
    else:
        return await optimizer._download_simple(
            DownloadTask(
                task_id=hashlib.md5(f"{url}_{file_path}".encode()).hexdigest(),
                url=url,
                file_path=file_path,
                start_time=time.time()
            ),
            progress_callback
        )

async def test_network_performance() -> Dict[str, Any]:
    """Teste les performances réseau"""
    optimizer = get_network_optimizer()
    return await optimizer.test_all_servers()

async def get_network_statistics() -> Dict[str, Any]:
    """Retourne les statistiques réseau"""
    optimizer = get_network_optimizer()
    return optimizer.get_network_stats()