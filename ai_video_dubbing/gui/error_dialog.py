#!/usr/bin/env python3
"""
Interface graphique pour la gestion et l'affichage des erreurs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import List, Optional, Callable
from pathlib import Path

from ..utils.error_handler import ErrorInfo, ErrorSolution, ErrorSeverity, ErrorCategory


class ErrorDialog(tk.Toplevel):
    """Dialogue d'affichage d'erreur avec solutions suggérées."""
    
    def __init__(self, parent, error_info: ErrorInfo, on_solution_applied: Optional[Callable] = None):
        super().__init__(parent)
        
        self.error_info = error_info
        self.on_solution_applied = on_solution_applied
        
        # Configuration de la fenêtre
        self.title(f"Erreur - {error_info.title}")
        self.geometry("600x500")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Centrer la fenêtre
        self._center_window()
        
        # Couleurs selon la sévérité
        self.severity_colors = {
            ErrorSeverity.LOW: {"bg": "#fff3cd", "fg": "#856404", "border": "#ffeaa7"},
            ErrorSeverity.MEDIUM: {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"},
            ErrorSeverity.HIGH: {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"},
            ErrorSeverity.CRITICAL: {"bg": "#f8d7da", "fg": "#721c24", "border": "#dc3545"}
        }
        
        self._create_widgets()
        
        # Bind pour fermeture
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)
    
    def _center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Crée les widgets du dialogue."""
        # Frame principal
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header avec icône et titre
        self._create_header(main_frame)
        
        # Message d'erreur
        self._create_error_message(main_frame)
        
        # Détails techniques (collapsible)
        self._create_technical_details(main_frame)
        
        # Solutions suggérées
        self._create_solutions_section(main_frame)
        
        # Boutons d'action
        self._create_action_buttons(main_frame)
    
    def _create_header(self, parent):
        """Crée l'en-tête avec icône et titre."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Icône selon la sévérité
        severity_icons = {
            ErrorSeverity.LOW: "⚠️",
            ErrorSeverity.MEDIUM: "❌",
            ErrorSeverity.HIGH: "🚨",
            ErrorSeverity.CRITICAL: "💥"
        }
        
        icon_label = tk.Label(
            header_frame,
            text=severity_icons.get(self.error_info.severity, "❌"),
            font=("Arial", 24)
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Titre et catégorie
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        title_label = tk.Label(
            title_frame,
            text=self.error_info.title,
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")
        
        category_label = tk.Label(
            title_frame,
            text=f"Catégorie: {self.error_info.category.value.replace('_', ' ').title()}",
            font=("Arial", 10),
            fg="gray",
            anchor="w"
        )
        category_label.pack(anchor="w")
        
        # Sévérité
        severity_colors = self.severity_colors[self.error_info.severity]
        severity_label = tk.Label(
            header_frame,
            text=self.error_info.severity.value.upper(),
            bg=severity_colors["border"],
            fg=severity_colors["fg"],
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5
        )
        severity_label.pack(side=tk.RIGHT)
    
    def _create_error_message(self, parent):
        """Crée la section du message d'erreur."""
        message_frame = ttk.LabelFrame(parent, text="Description", padding="10")
        message_frame.pack(fill=tk.X, pady=(0, 15))
        
        message_label = tk.Label(
            message_frame,
            text=self.error_info.message,
            font=("Arial", 11),
            wraplength=550,
            justify="left",
            anchor="w"
        )
        message_label.pack(fill=tk.X)
    
    def _create_technical_details(self, parent):
        """Crée la section des détails techniques."""
        self.details_frame = ttk.LabelFrame(parent, text="Détails Techniques", padding="10")
        self.details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Bouton pour afficher/masquer les détails
        self.details_visible = False
        self.toggle_details_button = ttk.Button(
            self.details_frame,
            text="▶ Afficher les détails",
            command=self._toggle_technical_details
        )
        self.toggle_details_button.pack(anchor="w")
        
        # Zone de texte pour les détails (initialement cachée)
        self.details_text = scrolledtext.ScrolledText(
            self.details_frame,
            height=6,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        
        # Contenu des détails
        details_content = f"Détails: {self.error_info.technical_details}\\n"
        if self.error_info.context:
            details_content += f"\\nContexte: {self.error_info.context}\\n"
        if self.error_info.stack_trace:
            details_content += f"\\nStack Trace:\\n{self.error_info.stack_trace}"
        
        self.details_text.insert(tk.END, details_content)
        self.details_text.config(state="disabled")
    
    def _toggle_technical_details(self):
        """Affiche/masque les détails techniques."""
        if self.details_visible:
            self.details_text.pack_forget()
            self.toggle_details_button.config(text="▶ Afficher les détails")
            self.details_visible = False
        else:
            self.details_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            self.toggle_details_button.config(text="▼ Masquer les détails")
            self.details_visible = True
    
    def _create_solutions_section(self, parent):
        """Crée la section des solutions suggérées."""
        if not self.error_info.solutions:
            return
        
        solutions_frame = ttk.LabelFrame(parent, text="Solutions Suggérées", padding="10")
        solutions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Canvas avec scrollbar pour les solutions
        canvas = tk.Canvas(solutions_frame)
        scrollbar = ttk.Scrollbar(solutions_frame, orient="vertical", command=canvas.yview)
        self.solutions_inner_frame = ttk.Frame(canvas)
        
        self.solutions_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.solutions_inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Créer les widgets pour chaque solution
        for i, solution in enumerate(self.error_info.solutions):
            self._create_solution_widget(self.solutions_inner_frame, solution, i)
    
    def _create_solution_widget(self, parent, solution: ErrorSolution, index: int):
        """Crée un widget pour une solution."""
        # Frame pour la solution
        solution_frame = ttk.Frame(parent, relief="solid", borderwidth=1)
        solution_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Header de la solution
        header_frame = ttk.Frame(solution_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Titre avec probabilité de succès
        title_text = f"{index + 1}. {solution.title}"
        if solution.success_probability > 0:
            title_text += f" ({solution.success_probability:.0%} de réussite)"
        
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=("Arial", 11, "bold"),
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Type d'action
        action_colors = {
            "automatic": {"bg": "#d4edda", "fg": "#155724"},
            "manual": {"bg": "#fff3cd", "fg": "#856404"},
            "configuration": {"bg": "#cce7ff", "fg": "#004085"}
        }
        
        action_color = action_colors.get(solution.action_type, {"bg": "#f8f9fa", "fg": "#495057"})
        
        action_label = tk.Label(
            header_frame,
            text=solution.action_type.title(),
            bg=action_color["bg"],
            fg=action_color["fg"],
            font=("Arial", 9),
            padx=8,
            pady=2
        )
        action_label.pack(side=tk.RIGHT)
        
        # Description
        desc_label = tk.Label(
            solution_frame,
            text=solution.description,
            font=("Arial", 10),
            wraplength=500,
            justify="left",
            anchor="w"
        )
        desc_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Bouton d'action si applicable
        if solution.action_callback:
            action_button = ttk.Button(
                solution_frame,
                text=f"Appliquer cette solution",
                command=lambda s=solution: self._apply_solution(s)
            )
            action_button.pack(pady=(0, 10))
    
    def _apply_solution(self, solution: ErrorSolution):
        """Applique une solution."""
        try:
            # Afficher un dialogue de confirmation pour les actions importantes
            if solution.action_type in ["automatic", "configuration"]:
                if not messagebox.askyesno(
                    "Confirmer l'action",
                    f"Voulez-vous appliquer cette solution ?\\n\\n{solution.title}\\n\\n{solution.description}"
                ):
                    return
            
            # Exécuter l'action dans un thread séparé
            def execute_solution():
                try:
                    if solution.action_callback:
                        result = solution.action_callback(**solution.action_params)
                        
                        # Mettre à jour l'interface dans le thread principal
                        self.after(0, lambda: self._on_solution_result(solution, result))
                    
                except Exception as e:
                    self.after(0, lambda: self._on_solution_error(solution, str(e)))
            
            # Désactiver le bouton pendant l'exécution
            # (Nous pourrions stocker les références des boutons pour cela)
            
            thread = threading.Thread(target=execute_solution, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'appliquer la solution :\\n{e}")
    
    def _on_solution_result(self, solution: ErrorSolution, result):
        """Appelé quand une solution a été appliquée."""
        if result:
            messagebox.showinfo(
                "Solution Appliquée",
                f"La solution '{solution.title}' a été appliquée avec succès."
            )
            
            if self.on_solution_applied:
                self.on_solution_applied(solution, result)
            
            # Fermer le dialogue si la solution a réussi
            self.close_dialog()
        else:
            messagebox.showwarning(
                "Solution Échouée",
                f"La solution '{solution.title}' n'a pas pu être appliquée."
            )
    
    def _on_solution_error(self, solution: ErrorSolution, error_message: str):
        """Appelé quand une solution a échoué."""
        messagebox.showerror(
            "Erreur de Solution",
            f"Erreur lors de l'application de '{solution.title}' :\\n{error_message}"
        )
    
    def _create_action_buttons(self, parent):
        """Crée les boutons d'action du dialogue."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Bouton Fermer
        close_button = ttk.Button(
            buttons_frame,
            text="Fermer",
            command=self.close_dialog
        )
        close_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bouton Copier les détails
        copy_button = ttk.Button(
            buttons_frame,
            text="Copier les détails",
            command=self._copy_error_details
        )
        copy_button.pack(side=tk.RIGHT)
        
        # Bouton Signaler l'erreur
        report_button = ttk.Button(
            buttons_frame,
            text="Signaler l'erreur",
            command=self._report_error
        )
        report_button.pack(side=tk.LEFT)
    
    def _copy_error_details(self):
        """Copie les détails de l'erreur dans le presse-papiers."""
        try:
            error_details = f"""Erreur: {self.error_info.title}
Catégorie: {self.error_info.category.value}
Sévérité: {self.error_info.severity.value}
Message: {self.error_info.message}
Détails techniques: {self.error_info.technical_details}

Contexte: {self.error_info.context}

Solutions suggérées:
"""
            
            for i, solution in enumerate(self.error_info.solutions):
                error_details += f"{i+1}. {solution.title}: {solution.description}\\n"
            
            self.clipboard_clear()
            self.clipboard_append(error_details)
            
            messagebox.showinfo("Copié", "Les détails de l'erreur ont été copiés dans le presse-papiers.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier les détails : {e}")
    
    def _report_error(self):
        """Ouvre un dialogue pour signaler l'erreur."""
        messagebox.showinfo(
            "Signaler l'erreur",
            "Fonctionnalité de signalement d'erreur à implémenter.\\n\\n"
            "Vous pouvez copier les détails et les envoyer manuellement."
        )
    
    def close_dialog(self):
        """Ferme le dialogue."""
        self.grab_release()
        self.destroy()


class ErrorSummaryWindow(tk.Toplevel):
    """Fenêtre de résumé des erreurs."""
    
    def __init__(self, parent, error_handler):
        super().__init__(parent)
        
        self.error_handler = error_handler
        
        # Configuration de la fenêtre
        self.title("Résumé des Erreurs")
        self.geometry("800x600")
        self.resizable(True, True)
        self.transient(parent)
        
        self._create_widgets()
        self._update_content()
    
    def _create_widgets(self):
        """Crée les widgets de la fenêtre."""
        # Frame principal
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="📊 Résumé des Erreurs",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Statistiques
        self.stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding="10")
        self.stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Liste des erreurs
        errors_frame = ttk.LabelFrame(main_frame, text="Historique des Erreurs", padding="10")
        errors_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Treeview pour les erreurs
        columns = ("Heure", "Catégorie", "Sévérité", "Titre")
        self.errors_tree = ttk.Treeview(errors_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.errors_tree.heading(col, text=col)
            self.errors_tree.column(col, width=150)
        
        # Scrollbar pour la treeview
        tree_scrollbar = ttk.Scrollbar(errors_frame, orient="vertical", command=self.errors_tree.yview)
        self.errors_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.errors_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Bind pour double-clic
        self.errors_tree.bind("<Double-1>", self._on_error_double_click)
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame,
            text="Actualiser",
            command=self._update_content
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="Effacer l'historique",
            command=self._clear_history
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="Fermer",
            command=self.destroy
        ).pack(side=tk.RIGHT)
    
    def _update_content(self):
        """Met à jour le contenu de la fenêtre."""
        # Mettre à jour les statistiques
        self._update_statistics()
        
        # Mettre à jour la liste des erreurs
        self._update_errors_list()
    
    def _update_statistics(self):
        """Met à jour les statistiques."""
        # Effacer les widgets existants
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        stats = self.error_handler.get_error_statistics()
        
        if not stats:
            no_errors_label = ttk.Label(self.stats_frame, text="Aucune erreur enregistrée")
            no_errors_label.pack()
            return
        
        # Créer les labels de statistiques
        stats_text = f"""Total des erreurs: {stats.get('total_errors', 0)}
Erreurs récentes (1h): {stats.get('recent_errors', 0)}
Erreurs critiques: {stats.get('critical_errors', 0)}
Catégorie la plus fréquente: {stats.get('most_common_category', 'N/A')}"""
        
        stats_label = ttk.Label(self.stats_frame, text=stats_text, font=("Arial", 10))
        stats_label.pack(anchor="w")
    
    def _update_errors_list(self):
        """Met à jour la liste des erreurs."""
        # Effacer les éléments existants
        for item in self.errors_tree.get_children():
            self.errors_tree.delete(item)
        
        # Ajouter les erreurs
        for error in reversed(self.error_handler.error_history):  # Plus récentes en premier
            timestamp = time.strftime("%H:%M:%S", time.localtime(error.timestamp))
            
            self.errors_tree.insert("", "end", values=(
                timestamp,
                error.category.value.replace("_", " ").title(),
                error.severity.value.upper(),
                error.title
            ), tags=(error.severity.value,))
        
        # Configurer les couleurs selon la sévérité
        self.errors_tree.tag_configure("critical", background="#ffebee")
        self.errors_tree.tag_configure("high", background="#fff3e0")
        self.errors_tree.tag_configure("medium", background="#f3e5f5")
        self.errors_tree.tag_configure("low", background="#e8f5e8")
    
    def _on_error_double_click(self, event):
        """Appelé lors du double-clic sur une erreur."""
        selection = self.errors_tree.selection()
        if not selection:
            return
        
        # Obtenir l'index de l'erreur
        item = self.errors_tree.item(selection[0])
        error_index = len(self.error_handler.error_history) - 1 - self.errors_tree.index(selection[0])
        
        if 0 <= error_index < len(self.error_handler.error_history):
            error_info = self.error_handler.error_history[error_index]
            
            # Ouvrir le dialogue d'erreur
            ErrorDialog(self, error_info)
    
    def _clear_history(self):
        """Efface l'historique des erreurs."""
        if messagebox.askyesno("Confirmer", "Voulez-vous vraiment effacer l'historique des erreurs ?"):
            self.error_handler.error_history.clear()
            self._update_content()


def show_error_dialog(parent, error_info: ErrorInfo, on_solution_applied: Optional[Callable] = None):
    """Affiche un dialogue d'erreur."""
    dialog = ErrorDialog(parent, error_info, on_solution_applied)
    return dialog


def show_error_summary(parent, error_handler):
    """Affiche le résumé des erreurs."""
    window = ErrorSummaryWindow(parent, error_handler)
    return window