"""
Tests pour le contrôleur asynchrone NeMo
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from ai_video_dubbing.performance.async_controller import AsyncNeMoController, TimeoutManager


class TestTimeoutManager:
    """Tests pour le gestionnaire de timeouts"""
    
    def test_get_recommended_timeout_default(self):
        """Test des timeouts par défaut"""
        manager = TimeoutManager()
        
        assert manager.get_recommended_timeout("download") == 300
        assert manager.get_recommended_timeout("model_loading") == 120
        assert manager.get_recommended_timeout("transcription") == 600
        assert manager.get_recommended_timeout("unknown") == 300
    
    def test_get_recommended_timeout_with_history(self):
        """Test des timeouts avec historique"""
        manager = TimeoutManager()
        
        # Enregistrer un temps de completion
        manager.record_completion_time("download", 200)
        
        # Le timeout recommandé devrait être 200 * 1.2 = 240
        # Mais au minimum 300 (base timeout)
        assert manager.get_recommended_timeout("download") == 300
        
        # Avec un temps plus long
        manager.record_completion_time("download", 400)
        assert manager.get_recommended_timeout("download") == 480  # 400 * 1.2


class TestAsyncNeMoController:
    """Tests pour le contrôleur asynchrone"""
    
    @pytest.fixture
    def controller(self):
        """Fixture pour créer un contrôleur"""
        return AsyncNeMoController()
    
    @pytest.mark.asyncio
    async def test_execute_simple_operation(self, controller):
        """Test d'exécution d'une opération simple"""
        
        async def simple_operation():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await controller.execute_with_timeout(
            simple_operation,
            operation_type="test",
            timeout=5
        )
        
        assert result == "success"
        assert len(controller.active_tasks) == 0  # Nettoyage automatique
    
    @pytest.mark.asyncio
    async def test_execute_sync_operation(self, controller):
        """Test d'exécution d'une opération synchrone"""
        
        def sync_operation(value):
            time.sleep(0.1)
            return f"result_{value}"
        
        result = await controller.execute_with_timeout(
            sync_operation,
            operation_type="test",
            timeout=5,
            value="test"
        )
        
        assert result == "result_test"
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, controller):
        """Test de la gestion des timeouts"""
        
        async def slow_operation():
            await asyncio.sleep(2)
            return "should_not_reach"
        
        with pytest.raises(TimeoutError):
            await controller.execute_with_timeout(
                slow_operation,
                operation_type="test",
                timeout=1
            )
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, controller):
        """Test du callback de progression"""
        progress_calls = []
        
        def progress_callback(task_id, progress, elapsed):
            progress_calls.append((task_id, progress, elapsed))
        
        async def operation_with_progress():
            await asyncio.sleep(0.5)
            return "done"
        
        result = await controller.execute_with_timeout(
            operation_with_progress,
            operation_type="test",
            timeout=5,
            progress_callback=progress_callback
        )
        
        assert result == "done"
        assert len(progress_calls) > 0  # Au moins un appel de progression
    
    @pytest.mark.asyncio
    async def test_cancel_operation(self, controller):
        """Test d'annulation d'opération"""
        
        async def long_operation():
            await asyncio.sleep(10)
            return "should_not_complete"
        
        # Démarrer l'opération
        task = asyncio.create_task(
            controller.execute_with_timeout(
                long_operation,
                operation_type="test",
                timeout=20
            )
        )
        
        # Attendre un peu puis annuler
        await asyncio.sleep(0.1)
        
        # Récupérer l'ID de la tâche active
        active_ops = controller.get_active_operations()
        assert len(active_ops) == 1
        
        task_id = list(active_ops.keys())[0]
        cancelled = await controller.cancel_operation(task_id)
        
        assert cancelled is True
        
        # La tâche devrait être annulée
        with pytest.raises(asyncio.CancelledError):
            await task
    
    @pytest.mark.asyncio
    async def test_cancel_all_operations(self, controller):
        """Test d'annulation de toutes les opérations"""
        
        async def long_operation(delay):
            await asyncio.sleep(delay)
            return f"done_{delay}"
        
        # Démarrer plusieurs opérations
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                controller.execute_with_timeout(
                    long_operation,
                    operation_type="test",
                    timeout=20,
                    delay=10
                )
            )
            tasks.append(task)
        
        # Attendre un peu
        await asyncio.sleep(0.1)
        
        # Vérifier qu'il y a des opérations actives
        active_ops = controller.get_active_operations()
        assert len(active_ops) == 3
        
        # Annuler toutes les opérations
        cancelled_count = await controller.cancel_all_operations()
        assert cancelled_count == 3
        
        # Toutes les tâches devraient être annulées
        for task in tasks:
            with pytest.raises(asyncio.CancelledError):
                await task
    
    def test_get_active_operations(self, controller):
        """Test de récupération des opérations actives"""
        
        # Pas d'opérations actives au début
        active_ops = controller.get_active_operations()
        assert len(active_ops) == 0
        
        # Cette partie nécessiterait une opération en cours
        # pour tester complètement
    
    def test_get_performance_stats(self, controller):
        """Test des statistiques de performance"""
        stats = controller.get_performance_stats()
        
        assert "active_tasks" in stats
        assert "timeout_history" in stats
        assert "total_tasks_processed" in stats
        
        assert stats["active_tasks"] == 0
        assert isinstance(stats["timeout_history"], dict)
        assert isinstance(stats["total_tasks_processed"], int)


@pytest.mark.asyncio
async def test_integration_with_mock_nemo():
    """Test d'intégration avec une opération NeMo simulée"""
    controller = AsyncNeMoController()
    
    # Simuler une opération de téléchargement de modèle
    async def mock_download_model(model_name, progress_callback=None):
        total_size = 1000
        downloaded = 0
        
        while downloaded < total_size:
            await asyncio.sleep(0.01)  # Simuler le téléchargement
            downloaded += 100
            
            if progress_callback:
                progress = (downloaded / total_size) * 100
                await progress_callback(f"download_{model_name}", progress, downloaded)
        
        return f"model_{model_name}_downloaded"
    
    progress_updates = []
    
    async def track_progress(task_id, progress, downloaded):
        progress_updates.append((task_id, progress, downloaded))
    
    # Exécuter le téléchargement simulé
    result = await controller.execute_with_timeout(
        mock_download_model,
        operation_type="download",
        timeout=10,
        progress_callback=track_progress,
        model_name="test_model"
    )
    
    assert result == "model_test_model_downloaded"
    assert len(progress_updates) > 0
    
    # Vérifier les statistiques
    stats = controller.get_performance_stats()
    assert stats["total_tasks_processed"] >= 1