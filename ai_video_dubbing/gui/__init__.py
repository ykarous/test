"""
Interface graphique pour l'application de doublage vidéo par IA.
"""

from .main_window import MainWindow
from .config_panel import ConfigPanel
from .progress_dialog import ProgressDialog
from .results_window import ResultsWindow

__all__ = ['MainWindow', 'ConfigPanel', 'ProgressDialog', 'ResultsWindow']