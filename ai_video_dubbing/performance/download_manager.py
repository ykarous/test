"""
Gestionnaire de téléchargement intelligent avec reprise et téléchargement parallèle
"""
import asyncio
import aiohttp
import aiofiles
import os
import time
import hashlib
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
from urllib.parse import urlparse
import math

from .progress_interface import RealTimeProgressInterface, OperationStatus

logger = logging.getLogger(__name__)

@dataclass
class DownloadInfo:
    """Informations sur un téléchargement"""
    url: str
    destination: str
    total_size: int = 0
    downloaded_size: int = 0
    chunk_size: int = 8192
    max_retries: int = 3
    retry_delay: float = 1.0
    supports_resume: bool = False
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    expected_hash: Optional[str] = None
    hash_algorithm: str = "sha256"
    
    @property
    def progress_percent(self) -> float:
        """Calcule le pourcentage de progression"""
        if self.total_size == 0:
            return 0.0
        return (self.downloaded_size / self.total_size) * 100
    
    @property
    def is_complete(self) -> bool:
        """Vérifie si le téléchargement est terminé"""
        return self.downloaded_size >= self.total_size and self.total_size > 0

@dataclass
class DownloadSession:
    """Session de téléchargement avec état persistant"""
    download_id: str
    info: DownloadInfo
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    speed_samples: List[Tuple[float, int]] = field(default_factory=list)
    is_paused: bool = False
    is_cancelled: bool = False
    error_count: int = 0
    
    def update_speed(self, bytes_downloaded: int):
        """Met à jour les échantillons de vitesse"""
        current_time = time.time()
        self.speed_samples.append((current_time, bytes_downloaded))
        
        # Garder seulement les 10 derniers échantillons
        if len(self.speed_samples) > 10:
            self.speed_samples = self.speed_samples[-10:]
        
        self.last_update = current_time
    
    @property
    def current_speed(self) -> float:
        """Calcule la vitesse actuelle en bytes/sec"""
        if len(self.speed_samples) < 2:
            return 0.0
        
        recent_samples = self.speed_samples[-5:]  # 5 derniers échantillons
        if len(recent_samples) < 2:
            return 0.0
        
        time_diff = recent_samples[-1][0] - recent_samples[0][0]
        bytes_diff = recent_samples[-1][1] - recent_samples[0][1]
        
        if time_diff <= 0:
            return 0.0
        
        return bytes_diff / time_diff
    
    @property
    def eta_seconds(self) -> float:
        """Calcule le temps restant estimé"""
        if self.info.is_complete:
            return 0.0
        
        speed = self.current_speed
        if speed <= 0:
            return float('inf')
        
        remaining_bytes = self.info.total_size - self.info.downloaded_size
        return remaining_bytes / speed

class IntelligentDownloadManager:
    """Gestionnaire de téléchargement intelligent avec reprise et parallélisation"""
    
    def __init__(self, 
                 max_concurrent_downloads: int = 3,
                 max_connections_per_download: int = 4,
                 progress_interface: Optional[RealTimeProgressInterface] = None):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_connections_per_download = max_connections_per_download
        self.progress_interface = progress_interface
        
        # Sessions actives
        self.active_sessions: Dict[str, DownloadSession] = {}
        self.session_lock = asyncio.Lock()
        
        # Configuration
        self.user_agent = "AI-Video-Dubbing/1.0"
        self.timeout = aiohttp.ClientTimeout(total=300, connect=30)
        
        # Statistiques
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_bytes_downloaded": 0,
            "total_time": 0.0
        }
    
    async def download_model(self, 
                           url: str, 
                           destination: str,
                           expected_hash: Optional[str] = None,
                           hash_algorithm: str = "sha256",
                           progress_callback: Optional[Callable] = None) -> bool:
        """
        Télécharge un modèle avec support de reprise
        
        Args:
            url: URL du modèle à télécharger
            destination: Chemin de destination
            expected_hash: Hash attendu pour validation
            hash_algorithm: Algorithme de hash (sha256, md5, etc.)
            progress_callback: Callback de progression
            
        Returns:
            True si le téléchargement a réussi
        """
        download_id = hashlib.md5(f"{url}:{destination}".encode()).hexdigest()
        
        # Vérifier si le fichier existe déjà et est valide
        if await self._is_file_valid(destination, expected_hash, hash_algorithm):
            logger.info(f"File already exists and is valid: {destination}")
            return True
        
        # Créer les informations de téléchargement
        download_info = DownloadInfo(
            url=url,
            destination=destination,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm
        )
        
        # Créer la session
        session = DownloadSession(download_id=download_id, info=download_info)
        
        async with self.session_lock:
            self.active_sessions[download_id] = session
        
        try:
            # Démarrer le suivi de progression si disponible
            progress_tracker = None
            if self.progress_interface:
                progress_tracker = await self.progress_interface.track_operation(
                    operation_type="model_download",
                    operation_id=download_id,
                    metadata={"url": url, "destination": destination}
                )
            
            # Effectuer le téléchargement
            success = await self._execute_download(session, progress_tracker, progress_callback)
            
            # Finaliser le suivi de progression
            if progress_tracker:
                await self.progress_interface.complete_operation(
                    download_id, success=success
                )
            
            # Mettre à jour les statistiques
            elapsed_time = time.time() - session.start_time
            self.stats["total_downloads"] += 1
            self.stats["total_time"] += elapsed_time
            
            if success:
                self.stats["successful_downloads"] += 1
                self.stats["total_bytes_downloaded"] += session.info.downloaded_size
            else:
                self.stats["failed_downloads"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False
        finally:
            # Nettoyer la session
            async with self.session_lock:
                if download_id in self.active_sessions:
                    del self.active_sessions[download_id]
    
    async def _execute_download(self, 
                              session: DownloadSession,
                              progress_tracker: Optional[Any] = None,
                              progress_callback: Optional[Callable] = None) -> bool:
        """Exécute le téléchargement avec gestion des erreurs et reprises"""
        
        for attempt in range(session.info.max_retries + 1):
            try:
                # Vérifier si le téléchargement a été annulé
                if session.is_cancelled:
                    return False
                
                # Obtenir les informations du serveur
                await self._get_server_info(session)
                
                # Déterminer la stratégie de téléchargement
                if session.info.supports_resume and session.info.total_size > 10 * 1024 * 1024:  # 10MB
                    # Téléchargement parallèle pour les gros fichiers
                    success = await self._parallel_download(session, progress_tracker, progress_callback)
                else:
                    # Téléchargement simple avec reprise
                    success = await self._simple_download(session, progress_tracker, progress_callback)
                
                if success:
                    # Valider le fichier téléchargé
                    if await self._validate_download(session):
                        return True
                    else:
                        logger.warning(f"Downloaded file validation failed: {session.info.destination}")
                        # Supprimer le fichier invalide
                        if os.path.exists(session.info.destination):
                            os.remove(session.info.destination)
                        session.info.downloaded_size = 0
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                session.error_count += 1
                
                if attempt < session.info.max_retries:
                    # Attendre avant de réessayer avec backoff exponentiel
                    delay = session.info.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All download attempts failed for {session.info.url}")
                    return False
        
        return False
    
    async def _get_server_info(self, session: DownloadSession):
        """Obtient les informations du serveur (taille, support de reprise, etc.)"""
        async with aiohttp.ClientSession(timeout=self.timeout) as client:
            try:
                # Faire une requête HEAD pour obtenir les informations
                async with client.head(session.info.url, headers={"User-Agent": self.user_agent}) as response:
                    if response.status == 200:
                        # Taille du fichier
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            session.info.total_size = int(content_length)
                        
                        # Support de reprise
                        accept_ranges = response.headers.get('Accept-Ranges', '').lower()
                        session.info.supports_resume = accept_ranges == 'bytes'
                        
                        # ETag et Last-Modified pour la validation
                        session.info.etag = response.headers.get('ETag')
                        session.info.last_modified = response.headers.get('Last-Modified')
                        
                        logger.info(f"Server info - Size: {session.info.total_size}, Resume: {session.info.supports_resume}")
                    
            except Exception as e:
                logger.warning(f"Failed to get server info: {e}")
                # Continuer sans les informations du serveur
    
    async def _simple_download(self, 
                             session: DownloadSession,
                             progress_tracker: Optional[Any] = None,
                             progress_callback: Optional[Callable] = None) -> bool:
        """Téléchargement simple avec support de reprise"""
        
        # Vérifier si on peut reprendre un téléchargement existant
        start_byte = 0
        if os.path.exists(session.info.destination) and session.info.supports_resume:
            start_byte = os.path.getsize(session.info.destination)
            session.info.downloaded_size = start_byte
            logger.info(f"Resuming download from byte {start_byte}")
        
        headers = {"User-Agent": self.user_agent}
        if start_byte > 0:
            headers["Range"] = f"bytes={start_byte}-"
        
        async with aiohttp.ClientSession(timeout=self.timeout) as client:
            async with client.get(session.info.url, headers=headers) as response:
                if response.status not in [200, 206]:  # 206 = Partial Content
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                # Ouvrir le fichier en mode append si on reprend, sinon en mode write
                mode = 'ab' if start_byte > 0 else 'wb'
                
                async with aiofiles.open(session.info.destination, mode) as file:
                    async for chunk in response.content.iter_chunked(session.info.chunk_size):
                        if session.is_cancelled:
                            return False
                        
                        await file.write(chunk)
                        session.info.downloaded_size += len(chunk)
                        session.update_speed(session.info.downloaded_size)
                        
                        # Mettre à jour la progression
                        await self._update_progress(session, progress_tracker, progress_callback)
        
        return True
    
    async def _parallel_download(self, 
                               session: DownloadSession,
                               progress_tracker: Optional[Any] = None,
                               progress_callback: Optional[Callable] = None) -> bool:
        """Téléchargement parallèle par segments"""
        
        if session.info.total_size <= 0:
            # Fallback vers téléchargement simple si la taille n'est pas connue
            return await self._simple_download(session, progress_tracker, progress_callback)
        
        # Calculer les segments
        num_segments = min(self.max_connections_per_download, 
                          max(1, session.info.total_size // (10 * 1024 * 1024)))  # 10MB par segment minimum
        segment_size = session.info.total_size // num_segments
        
        logger.info(f"Starting parallel download with {num_segments} segments")
        
        # Créer les tâches de téléchargement
        tasks = []
        for i in range(num_segments):
            start_byte = i * segment_size
            end_byte = start_byte + segment_size - 1
            if i == num_segments - 1:  # Dernier segment
                end_byte = session.info.total_size - 1
            
            task = asyncio.create_task(
                self._download_segment(session, i, start_byte, end_byte)
            )
            tasks.append(task)
        
        # Attendre que tous les segments soient téléchargés
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Vérifier les résultats
        success = all(result is True for result in results if not isinstance(result, Exception))
        
        if success:
            # Assembler les segments
            await self._assemble_segments(session, num_segments)
        
        return success
    
    async def _download_segment(self, session: DownloadSession, segment_id: int, start_byte: int, end_byte: int) -> bool:
        """Télécharge un segment spécifique"""
        temp_file = f"{session.info.destination}.part{segment_id}"
        
        headers = {
            "User-Agent": self.user_agent,
            "Range": f"bytes={start_byte}-{end_byte}"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as client:
                async with client.get(session.info.url, headers=headers) as response:
                    if response.status != 206:  # Partial Content
                        raise Exception(f"Segment {segment_id}: HTTP {response.status}")
                    
                    async with aiofiles.open(temp_file, 'wb') as file:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(session.info.chunk_size):
                            if session.is_cancelled:
                                return False
                            
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Mettre à jour la progression globale
                            session.info.downloaded_size += len(chunk)
                            session.update_speed(session.info.downloaded_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Segment {segment_id} download failed: {e}")
            # Nettoyer le fichier temporaire
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    
    async def _assemble_segments(self, session: DownloadSession, num_segments: int):
        """Assemble les segments téléchargés"""
        async with aiofiles.open(session.info.destination, 'wb') as output_file:
            for i in range(num_segments):
                temp_file = f"{session.info.destination}.part{i}"
                if os.path.exists(temp_file):
                    async with aiofiles.open(temp_file, 'rb') as segment_file:
                        while True:
                            chunk = await segment_file.read(session.info.chunk_size)
                            if not chunk:
                                break
                            await output_file.write(chunk)
                    
                    # Supprimer le fichier temporaire
                    os.remove(temp_file)
    
    async def _update_progress(self, 
                             session: DownloadSession,
                             progress_tracker: Optional[Any] = None,
                             progress_callback: Optional[Callable] = None):
        """Met à jour la progression du téléchargement"""
        
        # Callback personnalisé
        if progress_callback:
            try:
                await progress_callback(session)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
        
        # Interface de progression
        if progress_tracker:
            try:
                await progress_tracker.update(
                    progress_percent=session.info.progress_percent,
                    current_message=f"Téléchargement: {session.info.progress_percent:.1f}%",
                    current_step=f"Téléchargé: {self._format_bytes(session.info.downloaded_size)} / {self._format_bytes(session.info.total_size)}",
                    processing_speed=session.current_speed,
                    remaining_time=session.eta_seconds
                )
            except Exception as e:
                logger.warning(f"Progress tracker error: {e}")
    
    async def _validate_download(self, session: DownloadSession) -> bool:
        """Valide le fichier téléchargé"""
        if not os.path.exists(session.info.destination):
            return False
        
        # Vérifier la taille (avec tolérance pour la compression)
        file_size = os.path.getsize(session.info.destination)
        if session.info.total_size > 0 and file_size != session.info.total_size:
            # Calculer la différence en pourcentage
            size_diff_percent = abs(file_size - session.info.total_size) / session.info.total_size * 100
            
            if size_diff_percent > 10:  # Tolérance de 10% pour la compression
                logger.warning(f"File size difference: expected {session.info.total_size}, got {file_size} ({size_diff_percent:.1f}% difference)")
                
                # Seulement échouer si la différence est très importante (plus de 90%)
                if size_diff_percent > 90:
                    logger.error(f"File size mismatch too large: expected {session.info.total_size}, got {file_size}")
                    return False
            else:
                logger.debug(f"File size difference within tolerance: expected {session.info.total_size}, got {file_size}")
        
        # Vérifier le hash si fourni
        if session.info.expected_hash:
            calculated_hash = await self._calculate_file_hash(
                session.info.destination, 
                session.info.hash_algorithm
            )
            if calculated_hash != session.info.expected_hash.lower():
                logger.error(f"Hash mismatch: expected {session.info.expected_hash}, got {calculated_hash}")
                return False
        
        return True
    
    async def _is_file_valid(self, file_path: str, expected_hash: Optional[str], hash_algorithm: str) -> bool:
        """Vérifie si un fichier existe et est valide"""
        if not os.path.exists(file_path):
            return False
        
        # Vérifier que le fichier n'est pas vide
        if os.path.getsize(file_path) == 0:
            return False
        
        if expected_hash:
            calculated_hash = await self._calculate_file_hash(file_path, hash_algorithm)
            return calculated_hash == expected_hash.lower()
        
        return True
    
    async def _calculate_file_hash(self, file_path: str, algorithm: str) -> str:
        """Calcule le hash d'un fichier"""
        hash_obj = hashlib.new(algorithm)
        
        async with aiofiles.open(file_path, 'rb') as file:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Formate une taille en bytes de manière lisible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    async def cancel_download(self, download_id: str) -> bool:
        """Annule un téléchargement en cours"""
        async with self.session_lock:
            if download_id in self.active_sessions:
                session = self.active_sessions[download_id]
                session.is_cancelled = True
                logger.info(f"Download cancelled: {download_id}")
                return True
        return False
    
    async def pause_download(self, download_id: str) -> bool:
        """Met en pause un téléchargement"""
        async with self.session_lock:
            if download_id in self.active_sessions:
                session = self.active_sessions[download_id]
                session.is_paused = True
                logger.info(f"Download paused: {download_id}")
                return True
        return False
    
    async def resume_download(self, download_id: str) -> bool:
        """Reprend un téléchargement en pause"""
        async with self.session_lock:
            if download_id in self.active_sessions:
                session = self.active_sessions[download_id]
                session.is_paused = False
                logger.info(f"Download resumed: {download_id}")
                return True
        return False
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de téléchargement"""
        return self.stats.copy()
    
    def get_active_downloads(self) -> List[Dict[str, Any]]:
        """Retourne la liste des téléchargements actifs"""
        downloads = []
        for session in self.active_sessions.values():
            downloads.append({
                "download_id": session.download_id,
                "url": session.info.url,
                "destination": session.info.destination,
                "progress_percent": session.info.progress_percent,
                "downloaded_size": session.info.downloaded_size,
                "total_size": session.info.total_size,
                "current_speed": session.current_speed,
                "eta_seconds": session.eta_seconds,
                "is_paused": session.is_paused,
                "error_count": session.error_count
            })
        return downloads