#!/usr/bin/env python3
"""
Gestionnaire FFmpeg pour l'application de doublage vidéo par IA.
Permet de détecter, configurer et utiliser FFmpeg sans configuration PATH.
"""
import os
import sys
import json
import logging
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import conditionnel de PyQt5
try:
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    from PyQt5.QtCore import QSettings
    _PYQT5_AVAILABLE = True
except ImportError:
    _PYQT5_AVAILABLE = False
    QFileDialog = None
    QMessageBox = None
    QSettings = None

class FFmpegManager:
    """Gestionnaire pour FFmpeg avec sélection graphique."""
    
    def __init__(self):
        """Initialise le gestionnaire FFmpeg."""
        self.logger = logging.getLogger(__name__)
        
        # Initialiser QSettings seulement si PyQt5 est disponible
        if _PYQT5_AVAILABLE:
            self.settings = QSettings("AI_Video_Dubbing", "FFmpeg")
        else:
            self.settings = None
            
        self._ffmpeg_path = None
        self._ffprobe_path = None
        
        # Chemins de recherche automatique
        self.search_paths = self._get_default_search_paths()
        
        # Charger la configuration sauvegardée
        self._load_saved_config()
        
        self.logger.info("FFmpeg Manager initialized")
    
    def _get_default_search_paths(self) -> List[str]:
        """Obtient les chemins de recherche par défaut selon l'OS."""
        paths = []
        
        if platform.system() == "Windows":
            # Chemins Windows courants
            paths.extend([
                "C:/ffmpeg/bin",
                "C:/Program Files/ffmpeg/bin",
                "C:/Program Files (x86)/ffmpeg/bin",
                os.path.expanduser("~/ffmpeg/bin"),
                os.path.expanduser("~/Downloads/ffmpeg/bin"),
                "./ffmpeg/bin",
                "./tools/ffmpeg/bin"
            ])
            
            # Chocolatey
            choco_path = "C:/ProgramData/chocolatey/bin"
            if os.path.exists(choco_path):
                paths.append(choco_path)
                
        elif platform.system() == "Darwin":  # macOS
            paths.extend([
                "/usr/local/bin",
                "/opt/homebrew/bin",
                "/usr/bin",
                os.path.expanduser("~/bin"),
                "/Applications/ffmpeg"
            ])
        else:  # Linux
            paths.extend([
                "/usr/bin",
                "/usr/local/bin",
                "/opt/ffmpeg/bin",
                os.path.expanduser("~/bin"),
                os.path.expanduser("~/.local/bin")
            ])
        
        return paths
    
    def _load_saved_config(self):
        """Charge la configuration FFmpeg sauvegardée."""
        try:
            if not self.settings:
                return
                
            saved_path = self.settings.value("ffmpeg_path", "")
            if saved_path and os.path.exists(saved_path):
                self._ffmpeg_path = saved_path
                
                # Déduire ffprobe du même répertoire
                ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
                ffprobe_path = os.path.join(os.path.dirname(saved_path), ffprobe_name)
                if os.path.exists(ffprobe_path):
                    self._ffprobe_path = ffprobe_path
                
                self.logger.info(f"Loaded saved FFmpeg path: {self._ffmpeg_path}")
        except Exception as e:
            self.logger.warning(f"Failed to load saved FFmpeg config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration FFmpeg."""
        try:
            if self._ffmpeg_path and self.settings:
                self.settings.setValue("ffmpeg_path", self._ffmpeg_path)
                self.settings.sync()
                self.logger.info(f"Saved FFmpeg path: {self._ffmpeg_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save FFmpeg config: {e}")
    
    def auto_detect_ffmpeg(self) -> bool:
        """Détection automatique de FFmpeg."""
        try:
            # 1. Vérifier si FFmpeg est dans le PATH
            try:
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # FFmpeg trouvé dans PATH
                    self._ffmpeg_path = 'ffmpeg'  # Utiliser la commande système
                    self._ffprobe_path = 'ffprobe'
                    self.logger.info("FFmpeg found in system PATH")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # 2. Rechercher dans les chemins par défaut
            ffmpeg_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
            ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
            
            for search_path in self.search_paths:
                ffmpeg_full_path = os.path.join(search_path, ffmpeg_name)
                ffprobe_full_path = os.path.join(search_path, ffprobe_name)
                
                if os.path.exists(ffmpeg_full_path) and os.path.exists(ffprobe_full_path):
                    # Tester que FFmpeg fonctionne
                    try:
                        result = subprocess.run([ffmpeg_full_path, '-version'],
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            self._ffmpeg_path = ffmpeg_full_path
                            self._ffprobe_path = ffprobe_full_path
                            self._save_config()
                            self.logger.info(f"FFmpeg auto-detected at: {ffmpeg_full_path}")
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
            
            self.logger.warning("FFmpeg not found in automatic detection")
            return False
            
        except Exception as e:
            self.logger.error(f"Error during FFmpeg auto-detection: {e}")
            return False
    
    def select_ffmpeg_manually(self, parent_widget=None) -> bool:
        """Permet à l'utilisateur de sélectionner FFmpeg manuellement."""
        if not _PYQT5_AVAILABLE:
            self.logger.error("PyQt5 not available for file dialog")
            return False
            
        try:
            # Déterminer l'extension selon l'OS
            if platform.system() == "Windows":
                file_filter = "FFmpeg Executable (ffmpeg.exe);;All Files (*.*)"
                default_name = "ffmpeg.exe"
            else:
                file_filter = "FFmpeg Executable (ffmpeg);;All Files (*)"
                default_name = "ffmpeg"
            
            # Ouvrir le dialogue de sélection
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "Sélectionner l'exécutable FFmpeg",
                "",
                file_filter
            )
            
            if file_path and os.path.exists(file_path):
                # Vérifier que c'est bien FFmpeg
                try:
                    result = subprocess.run([file_path, '-version'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and 'ffmpeg' in result.stdout.lower():
                        self._ffmpeg_path = file_path
                        
                        # Chercher ffprobe dans le même répertoire
                        ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
                        ffprobe_path = os.path.join(os.path.dirname(file_path), ffprobe_name)
                        if os.path.exists(ffprobe_path):
                            self._ffprobe_path = ffprobe_path
                        else:
                            self._ffprobe_path = None
                            self.logger.warning("ffprobe not found in the same directory")
                        
                        self._save_config()
                        self.logger.info(f"FFmpeg manually selected: {file_path}")
                        
                        # Afficher confirmation
                        if parent_widget:
                            QMessageBox.information(
                                parent_widget,
                                "FFmpeg Configuré",
                                f"FFmpeg configuré avec succès!\n\nChemin: {file_path}\n\n"
                                f"Version: {self.get_version()}"
                            )
                        return True
                    else:
                        if parent_widget:
                            QMessageBox.warning(
                                parent_widget,
                                "Fichier Invalide",
                                "Le fichier sélectionné n'est pas un exécutable FFmpeg valide."
                            )
                        return False
                        
                except subprocess.TimeoutExpired:
                    if parent_widget:
                        QMessageBox.warning(
                            parent_widget,
                            "Timeout",
                            "Timeout lors de la vérification de FFmpeg."
                        )
                    return False
                except Exception as e:
                    if parent_widget:
                        QMessageBox.warning(
                            parent_widget,
                            "Erreur",
                            f"Erreur lors de la vérification de FFmpeg:\n{e}"
                        )
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error during manual FFmpeg selection: {e}")
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur",
                    f"Erreur lors de la sélection de FFmpeg:\n{e}"
                )
            return False
    
    def is_available(self) -> bool:
        """Vérifie si FFmpeg est disponible et fonctionnel."""
        if not self._ffmpeg_path:
            return self.auto_detect_ffmpeg()
        
        try:
            result = subprocess.run([self._ffmpeg_path, '-version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_ffmpeg_path(self) -> Optional[str]:
        """Obtient le chemin vers FFmpeg."""
        if not self._ffmpeg_path and not self.auto_detect_ffmpeg():
            return None
        return self._ffmpeg_path
    
    def get_ffprobe_path(self) -> Optional[str]:
        """Obtient le chemin vers FFprobe."""
        if not self._ffprobe_path and not self.auto_detect_ffmpeg():
            return None
        return self._ffprobe_path
    
    def get_version(self) -> str:
        """Obtient la version de FFmpeg."""
        try:
            if not self._ffmpeg_path:
                return "Non disponible"
            
            result = subprocess.run([self._ffmpeg_path, '-version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Extraire la version de la première ligne
                first_line = result.stdout.split('\n')[0]
                if 'version' in first_line:
                    version_part = first_line.split('version')[1].split()[0]
                    return version_part
            return "Version inconnue"
        except:
            return "Erreur"
    
    def get_info(self) -> Dict[str, Any]:
        """Obtient les informations complètes sur FFmpeg."""
        return {
            'available': self.is_available(),
            'ffmpeg_path': self._ffmpeg_path,
            'ffprobe_path': self._ffprobe_path,
            'version': self.get_version(),
            'auto_detected': self._ffmpeg_path in ['ffmpeg', 'ffprobe'] if self._ffmpeg_path else False
        }
    
    def run_ffmpeg_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Exécute une commande FFmpeg."""
        if not self.is_available():
            raise RuntimeError("FFmpeg is not available")
        
        command = [self._ffmpeg_path] + args
        return subprocess.run(command, **kwargs)
    
    def run_ffprobe_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Exécute une commande FFprobe."""
        if not self._ffprobe_path:
            raise RuntimeError("FFprobe is not available")
        
        command = [self._ffprobe_path] + args
        return subprocess.run(command, **kwargs)
    
    def reset_configuration(self):
        """Remet à zéro la configuration FFmpeg."""
        try:
            if self.settings:
                self.settings.remove("ffmpeg_path")
                self.settings.sync()
            self._ffmpeg_path = None
            self._ffprobe_path = None
            self.logger.info("FFmpeg configuration reset")
        except Exception as e:
            self.logger.warning(f"Failed to reset FFmpeg configuration: {e}")
    
    def download_ffmpeg_info(self) -> Dict[str, str]:
        """Retourne les informations pour télécharger FFmpeg."""
        system = platform.system()
        
        if system == "Windows":
            return {
                'url': 'https://www.gyan.dev/ffmpeg/builds/',
                'instructions': [
                    '1. Téléchargez la version "release builds"',
                    '2. Extrayez l\'archive dans C:\\ffmpeg',
                    '3. Utilisez le bouton "Sélectionner FFmpeg" pour pointer vers C:\\ffmpeg\\bin\\ffmpeg.exe'
                ]
            }
        elif system == "Darwin":  # macOS
            return {
                'url': 'https://ffmpeg.org/download.html#build-mac',
                'instructions': [
                    '1. Installez Homebrew si pas déjà fait',
                    '2. Exécutez: brew install ffmpeg',
                    '3. Ou téléchargez depuis le site officiel'
                ]
            }
        else:  # Linux
            return {
                'url': 'https://ffmpeg.org/download.html#build-linux',
                'instructions': [
                    '1. Ubuntu/Debian: sudo apt install ffmpeg',
                    '2. CentOS/RHEL: sudo yum install ffmpeg',
                    '3. Ou compilez depuis les sources'
                ]
            }