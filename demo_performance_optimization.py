#!/usr/bin/env python3
"""
Démonstration du système d'optimisation des performances.
"""

import sys
import os
import time
import threading
import numpy as np
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from ai_video_dubbing.utils.performance_optimizer import (
    PerformanceOptimizer, OptimizationConfig, OptimizationLevel,
    get_performance_optimizer
)
from ai_video_dubbing.utils.cache_manager import get_cache_manager


class PerformanceDemo:
    """Démonstration du système d'optimisation des performances."""
    
    def __init__(self):
        """Initialise la démonstration."""
        self.optimizer = None
        self.cache_manager = None
        self.is_running = False
        
        if GUI_AVAILABLE:
            self.setup_gui()
        else:
            print("Interface graphique non disponible, utilisation du mode console.")
    
    def setup_gui(self):
        """Configure l'interface graphique de démonstration."""
        self.root = tk.Tk()
        self.root.title("Démonstration - Optimisation des Performances")
        self.root.geometry("900x700")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="⚡ Démonstration du Système d'Optimisation des Performances",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Section de contrôle
        self._create_control_section(main_frame)
        
        # Section de monitoring
        self._create_monitoring_section(main_frame)
        
        # Section de statistiques
        self._create_stats_section(main_frame)
        
        # Zone de logs
        self._create_logs_section(main_frame)
    
    def _create_control_section(self, parent):
        """Crée la section de contrôle."""
        control_frame = ttk.LabelFrame(parent, text="🎛️ Contrôles", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configuration d'optimisation
        config_frame = ttk.Frame(control_frame)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(config_frame, text="Niveau d'optimisation:").pack(side=tk.LEFT)
        
        self.optimization_level = tk.StringVar(value="balanced")
        level_combo = ttk.Combobox(
            config_frame,
            textvariable=self.optimization_level,
            values=["minimal", "balanced", "aggressive", "memory_saver"],
            state="readonly"
        )
        level_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Boutons de contrôle
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_button = ttk.Button(
            buttons_frame,
            text="🚀 Démarrer Optimisation",
            command=self._start_optimization
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏹️ Arrêter",
            command=self._stop_optimization,
            state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="🧪 Test Charge",
            command=self._simulate_workload
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="🧹 Nettoyer Cache",
            command=self._clear_cache
        ).pack(side=tk.LEFT)
    
    def _create_monitoring_section(self, parent):
        """Crée la section de monitoring."""
        monitor_frame = ttk.LabelFrame(parent, text="📊 Monitoring en Temps Réel", padding="15")
        monitor_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Métriques actuelles
        metrics_frame = ttk.Frame(monitor_frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mémoire
        memory_frame = ttk.Frame(metrics_frame)
        memory_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(memory_frame, text="💾 Mémoire", font=("Arial", 10, "bold")).pack()
        self.memory_label = ttk.Label(memory_frame, text="0%")
        self.memory_label.pack()
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=150)
        self.memory_progress.pack(pady=5)
        
        # CPU
        cpu_frame = ttk.Frame(metrics_frame)
        cpu_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(cpu_frame, text="🖥️ CPU", font=("Arial", 10, "bold")).pack()
        self.cpu_label = ttk.Label(cpu_frame, text="0%")
        self.cpu_label.pack()
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=150)
        self.cpu_progress.pack(pady=5)
        
        # Disque
        disk_frame = ttk.Frame(metrics_frame)
        disk_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(disk_frame, text="💿 Disque", font=("Arial", 10, "bold")).pack()
        self.disk_label = ttk.Label(disk_frame, text="0%")
        self.disk_label.pack()
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=150)
        self.disk_progress.pack(pady=5)
    
    def _create_stats_section(self, parent):
        """Crée la section de statistiques."""
        stats_frame = ttk.LabelFrame(parent, text="📈 Statistiques", padding="15")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Notebook pour les différents onglets
        notebook = ttk.Notebook(stats_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet modèles
        models_frame = ttk.Frame(notebook)
        notebook.add(models_frame, text="🧠 Modèles")
        
        self.models_tree = ttk.Treeview(
            models_frame,
            columns=("usage", "memory", "last_used"),
            show="tree headings"
        )
        self.models_tree.heading("#0", text="Modèle")
        self.models_tree.heading("usage", text="Utilisations")
        self.models_tree.heading("memory", text="Mémoire (MB)")
        self.models_tree.heading("last_used", text="Dernière utilisation")
        
        self.models_tree.pack(fill=tk.BOTH, expand=True)
        
        # Onglet cache
        cache_frame = ttk.Frame(notebook)
        notebook.add(cache_frame, text="💾 Cache")
        
        self.cache_text = tk.Text(cache_frame, height=10, font=("Consolas", 9))
        cache_scrollbar = ttk.Scrollbar(cache_frame, orient="vertical", command=self.cache_text.yview)
        self.cache_text.configure(yscrollcommand=cache_scrollbar.set)
        
        self.cache_text.pack(side="left", fill="both", expand=True)
        cache_scrollbar.pack(side="right", fill="y")
        
        # Onglet performance
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="⚡ Performance")
        
        self.perf_text = tk.Text(perf_frame, height=10, font=("Consolas", 9))
        perf_scrollbar = ttk.Scrollbar(perf_frame, orient="vertical", command=self.perf_text.yview)
        self.perf_text.configure(yscrollcommand=perf_scrollbar.set)
        
        self.perf_text.pack(side="left", fill="both", expand=True)
        perf_scrollbar.pack(side="right", fill="y")
    
    def _create_logs_section(self, parent):
        """Crée la section de logs."""
        logs_frame = ttk.LabelFrame(parent, text="📄 Logs", padding="10")
        logs_frame.pack(fill=tk.X)
        
        self.logs_text = tk.Text(
            logs_frame,
            height=6,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        logs_scrollbar = ttk.Scrollbar(logs_frame, orient="vertical", command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=logs_scrollbar.set)
        
        self.logs_text.pack(side="left", fill="both", expand=True)
        logs_scrollbar.pack(side="right", fill="y")
        
        # Message initial
        self.log_message("⚡ Système d'optimisation des performances initialisé")
        self.log_message("Configurez le niveau d'optimisation et cliquez sur 'Démarrer'")
    
    def _start_optimization(self):
        """Démarre l'optimisation."""
        if self.is_running:
            return
        
        # Créer la configuration
        level_map = {
            "minimal": OptimizationLevel.MINIMAL,
            "balanced": OptimizationLevel.BALANCED,
            "aggressive": OptimizationLevel.AGGRESSIVE,
            "memory_saver": OptimizationLevel.MEMORY_SAVER
        }
        
        config = OptimizationConfig(
            level=level_map[self.optimization_level.get()],
            monitoring_interval=1.0,
            max_memory_percent=80.0,
            chunk_size_mb=100
        )
        
        # Créer l'optimiseur
        self.optimizer = get_performance_optimizer(config)
        self.cache_manager = get_cache_manager(config)
        
        # Démarrer l'optimisation
        self.optimizer.start_optimization()
        self.is_running = True
        
        # Mettre à jour l'interface
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        self.log_message(f"🚀 Optimisation démarrée (niveau: {self.optimization_level.get()})")
        
        # Démarrer la mise à jour de l'interface
        self._start_ui_updates()
    
    def _stop_optimization(self):
        """Arrête l'optimisation."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.optimizer:
            self.optimizer.stop_optimization()
        
        # Mettre à jour l'interface
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        self.log_message("⏹️ Optimisation arrêtée")
    
    def _simulate_workload(self):
        """Simule une charge de travail."""
        if not self.optimizer:
            self.log_message("⚠️ Démarrez d'abord l'optimisation")
            return
        
        def workload_thread():
            self.log_message("🧪 Simulation de charge de travail...")
            
            try:
                # Charger plusieurs modèles
                for i in range(3):
                    def create_model(model_id=i):
                        return {
                            'id': model_id,
                            'weights': np.random.rand(1000, 1000),
                            'config': {'layers': 10 + model_id}
                        }
                    
                    model = self.optimizer.model_manager.load_model(
                        f'demo_model_{i}',
                        lambda: create_model(i)
                    )
                    
                    self.root.after(0, lambda i=i: self.log_message(f"  📦 Modèle {i} chargé"))
                
                # Simuler du traitement par chunks
                for i in range(5):
                    audio_data = np.random.rand(44100 * 5)  # 5 secondes
                    
                    def process_func(audio, sr):
                        # Simuler un traitement coûteux
                        return np.convolve(audio, np.ones(100)/100, mode='same')
                    
                    processed = self.optimizer.chunk_processor.process_audio_chunks(
                        audio_data, 44100, process_func
                    )
                    
                    self.root.after(0, lambda i=i: self.log_message(f"  🔄 Chunk {i+1}/5 traité"))
                    time.sleep(0.5)
                
                # Test du cache
                for i in range(10):
                    key = f"test_data_{i}"
                    data = np.random.rand(1000)
                    self.cache_manager.put(key, data, 'temp_results')
                    
                    # Récupérer immédiatement pour tester
                    retrieved = self.cache_manager.get(key, 'temp_results')
                    assert retrieved is not None
                
                self.root.after(0, lambda: self.log_message("✅ Simulation terminée avec succès"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"❌ Erreur simulation: {e}"))
        
        # Lancer dans un thread séparé
        thread = threading.Thread(target=workload_thread, daemon=True)
        thread.start()
    
    def _clear_cache(self):
        """Nettoie le cache."""
        if self.cache_manager:
            self.cache_manager.clear()
            self.log_message("🧹 Cache nettoyé")
        else:
            self.log_message("⚠️ Gestionnaire de cache non initialisé")
    
    def _start_ui_updates(self):
        """Démarre les mises à jour de l'interface."""
        def update_ui():
            if self.is_running and self.optimizer:
                self._update_monitoring()
                self._update_stats()
                
                # Programmer la prochaine mise à jour
                self.root.after(1000, update_ui)  # Toutes les secondes
        
        update_ui()
    
    def _update_monitoring(self):
        """Met à jour les métriques de monitoring."""
        if not self.optimizer:
            return
        
        try:
            current_usage = self.optimizer.resource_monitor.get_current_usage()
            
            if current_usage:
                # Mémoire
                memory_percent = current_usage.memory_percent
                self.memory_label.config(text=f"{memory_percent:.1f}%")
                self.memory_progress["value"] = memory_percent
                
                # CPU
                cpu_percent = current_usage.cpu_percent
                self.cpu_label.config(text=f"{cpu_percent:.1f}%")
                self.cpu_progress["value"] = cpu_percent
                
                # Disque
                disk_percent = current_usage.disk_usage_percent
                self.disk_label.config(text=f"{disk_percent:.1f}%")
                self.disk_progress["value"] = disk_percent
        
        except Exception as e:
            self.log_message(f"Erreur mise à jour monitoring: {e}")
    
    def _update_stats(self):
        """Met à jour les statistiques."""
        if not self.optimizer:
            return
        
        try:
            # Statistiques des modèles
            self._update_models_stats()
            
            # Statistiques du cache
            self._update_cache_stats()
            
            # Statistiques de performance
            self._update_performance_stats()
        
        except Exception as e:
            self.log_message(f"Erreur mise à jour stats: {e}")
    
    def _update_models_stats(self):
        """Met à jour les statistiques des modèles."""
        # Vider l'arbre
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Ajouter les modèles chargés
        for model_name in self.optimizer.model_manager.loaded_models.keys():
            usage_count = self.optimizer.model_manager.model_usage_count.get(model_name, 0)
            memory_usage = self.optimizer.model_manager.model_memory_usage.get(model_name, 0)
            last_used = self.optimizer.model_manager.model_last_used.get(model_name, 0)
            
            # Formater le temps
            if last_used > 0:
                time_diff = time.time() - last_used
                if time_diff < 60:
                    last_used_str = f"{time_diff:.0f}s"
                else:
                    last_used_str = f"{time_diff/60:.1f}min"
            else:
                last_used_str = "Jamais"
            
            self.models_tree.insert("", "end", text=model_name, values=(
                usage_count,
                f"{memory_usage:.1f}",
                last_used_str
            ))
    
    def _update_cache_stats(self):
        """Met à jour les statistiques du cache."""
        if not self.cache_manager:
            return
        
        stats = self.cache_manager.get_stats()
        
        # Effacer le texte précédent
        self.cache_text.delete(1.0, tk.END)
        
        # Ajouter les nouvelles statistiques
        self.cache_text.insert(tk.END, "📊 Statistiques du Cache\n")
        self.cache_text.insert(tk.END, "=" * 30 + "\n\n")
        
        # Cache mémoire
        memory_stats = stats['memory_cache']
        self.cache_text.insert(tk.END, "💾 Cache Mémoire:\n")
        self.cache_text.insert(tk.END, f"  Entrées: {memory_stats['entries']}\n")
        self.cache_text.insert(tk.END, f"  Taille: {memory_stats['size_mb']:.2f} MB\n")
        self.cache_text.insert(tk.END, f"  Taux de réussite: {memory_stats['hit_rate']:.1f}%\n")
        self.cache_text.insert(tk.END, f"  Évictions: {memory_stats['evictions']}\n\n")
        
        # Cache disque
        disk_stats = stats['disk_cache']
        self.cache_text.insert(tk.END, "💿 Cache Disque:\n")
        self.cache_text.insert(tk.END, f"  Entrées: {disk_stats['entries']}\n")
        self.cache_text.insert(tk.END, f"  Taille: {disk_stats['size_gb']:.4f} GB\n")
        self.cache_text.insert(tk.END, f"  Taux de réussite: {disk_stats['hit_rate']:.1f}%\n")
    
    def _update_performance_stats(self):
        """Met à jour les statistiques de performance."""
        stats = self.optimizer.get_optimization_stats()
        
        # Effacer le texte précédent
        self.perf_text.delete(1.0, tk.END)
        
        # Ajouter les nouvelles statistiques
        self.perf_text.insert(tk.END, "⚡ Statistiques de Performance\n")
        self.perf_text.insert(tk.END, "=" * 35 + "\n\n")
        
        self.perf_text.insert(tk.END, f"Niveau d'optimisation: {stats['optimization_level']}\n")
        self.perf_text.insert(tk.END, f"État: {'🟢 Actif' if stats['is_optimizing'] else '🔴 Inactif'}\n\n")
        
        # Utilisation actuelle
        usage = stats['current_usage']
        self.perf_text.insert(tk.END, "📊 Utilisation Actuelle:\n")
        self.perf_text.insert(tk.END, f"  Mémoire: {usage['memory_percent']:.1f}%\n")
        self.perf_text.insert(tk.END, f"  CPU: {usage['cpu_percent']:.1f}%\n")
        self.perf_text.insert(tk.END, f"  Disque: {usage['disk_percent']:.1f}%\n\n")
        
        # Modèles
        self.perf_text.insert(tk.END, f"🧠 Modèles chargés: {len(stats['loaded_models'])}\n")
        for model in stats['loaded_models']:
            memory_mb = stats['model_memory_usage'].get(model, 0)
            self.perf_text.insert(tk.END, f"  - {model}: {memory_mb:.1f} MB\n")
        
        self.perf_text.insert(tk.END, f"\n📦 Taille des chunks: {stats['chunk_size_mb']} MB\n")
        
        # Seuils
        thresholds = stats['thresholds']
        self.perf_text.insert(tk.END, f"\n⚠️ Seuils d'alerte:\n")
        for resource, threshold in thresholds.items():
            self.perf_text.insert(tk.END, f"  {resource}: {threshold}%\n")
    
    def log_message(self, message: str):
        """Ajoute un message aux logs."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
    
    def run_gui(self):
        """Lance l'interface graphique."""
        if GUI_AVAILABLE:
            self.root.mainloop()
        else:
            print("Interface graphique non disponible.")
    
    def run_console_demo(self):
        """Exécute une démonstration en mode console."""
        print("⚡ Démonstration Console du Système d'Optimisation")
        print("=" * 60)
        
        # Créer l'optimiseur
        config = OptimizationConfig(level=OptimizationLevel.BALANCED)
        optimizer = get_performance_optimizer(config)
        cache_manager = get_cache_manager(config)
        
        print("\\n🚀 Démarrage de l'optimisation...")
        optimizer.start_optimization()
        
        # Attendre un peu pour collecter des données
        time.sleep(2)
        
        # Afficher les statistiques initiales
        stats = optimizer.get_optimization_stats()
        print(f"\\n📊 Statistiques initiales:")
        print(f"  Niveau: {stats['optimization_level']}")
        print(f"  Mémoire: {stats['current_usage']['memory_percent']:.1f}%")
        print(f"  CPU: {stats['current_usage']['cpu_percent']:.1f}%")
        
        # Simuler une charge de travail
        print("\\n🧪 Simulation de charge de travail...")
        
        # Charger des modèles
        for i in range(3):
            def create_model(model_id=i):
                return {'id': model_id, 'data': np.random.rand(500, 500)}
            
            model = optimizer.model_manager.load_model(f'demo_model_{i}', lambda: create_model(i))
            print(f"  📦 Modèle {i} chargé")
        
        # Test du cache
        print("\\n💾 Test du cache...")
        for i in range(5):
            key = f"test_{i}"
            data = np.random.rand(1000)
            cache_manager.put(key, data, 'temp_results')
            
            retrieved = cache_manager.get(key, 'temp_results')
            assert retrieved is not None
            print(f"  ✅ Cache test {i+1}/5")
        
        # Statistiques finales
        final_stats = optimizer.get_optimization_stats()
        cache_stats = cache_manager.get_stats()
        
        print(f"\\n📈 Statistiques finales:")
        print(f"  Modèles chargés: {len(final_stats['loaded_models'])}")
        print(f"  Mémoire modèles: {sum(final_stats['model_memory_usage'].values()):.1f} MB")
        print(f"  Cache mémoire: {cache_stats['memory_cache']['entries']} entrées")
        print(f"  Taux de réussite cache: {cache_stats['memory_cache']['hit_rate']:.1f}%")
        
        # Arrêter l'optimisation
        optimizer.stop_optimization()
        print("\\n⏹️ Optimisation arrêtée")
        print("\\n🎉 Démonstration terminée!")


def main():
    """Fonction principale."""
    print("⚡ AI Video Dubbing - Démonstration du Système d'Optimisation")
    
    demo = PerformanceDemo()
    
    if GUI_AVAILABLE:
        print("Interface graphique disponible - Lancement de la démonstration GUI")
        demo.run_gui()
    else:
        print("Interface graphique non disponible - Démonstration console")
        demo.run_console_demo()


if __name__ == "__main__":
    main()