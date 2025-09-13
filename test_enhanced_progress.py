"""
Test de l'interface de progression améliorée avec messages contextuels
"""
import asyncio
import time
from ai_video_dubbing.performance.progress_interface_enhanced import (
    EnhancedRealTimeProgressInterface, OperationType, OperationStatus
)
from ai_video_dubbing.performance.contextual_messages import MessageType

async def test_enhanced_progress_basic():
    """Test basique de l'interface de progression améliorée"""
    print("🚀 Test basique de l'interface de progression améliorée")
    print("-" * 50)
    
    interface = EnhancedRealTimeProgressInterface()
    
    # Collecteur de messages
    messages = []
    
    def progress_callback(progress_update):
        messages.append(progress_update)
        contextual_msg = progress_update.contextual_message
        if contextual_msg:
            print(f"📢 {contextual_msg.message}")
            if contextual_msg.eta_seconds:
                print(f"   ⏱️ ETA: {contextual_msg.eta_seconds:.1f}s")
            if contextual_msg.suggestions:
                print(f"   💡 Suggestions: {contextual_msg.suggestions}")
    
    def completion_callback(operation_id, success):
        status = "✅ Réussie" if success else "❌ Échouée"
        print(f"🏁 Opération {operation_id}: {status}")
    
    def error_callback(operation_id, error_message):
        print(f"🚨 Erreur {operation_id}: {error_message}")
    
    # Enregistrer les callbacks
    interface.add_progress_callback(progress_callback)
    interface.add_completion_callback(completion_callback)
    interface.add_error_callback(error_callback)
    
    try:
        # Test de téléchargement
        print("\\n📥 Test de téléchargement avec messages contextuels...")
        
        tracker = await interface.track_operation(
            operation_type=OperationType.DOWNLOAD,
            operation_id="download_test",
            model_name="whisper-large-v3",
            total_bytes=1000000000,  # 1GB
            estimated_duration=60.0
        )
        
        # Simulation du téléchargement
        download_steps = [
            (0, "Démarrage du téléchargement", 0, 0),
            (15, "Téléchargement en cours", 150000000, 2500000),  # 150MB, 2.5MB/s
            (35, "Téléchargement en cours", 350000000, 2800000),  # 350MB, 2.8MB/s
            (60, "Téléchargement en cours", 600000000, 3000000),  # 600MB, 3MB/s
            (85, "Téléchargement en cours", 850000000, 2900000),  # 850MB, 2.9MB/s
            (100, "Téléchargement terminé", 1000000000, 0)        # 1GB terminé
        ]
        
        for progress, step, downloaded, speed in download_steps:
            await tracker.update(
                progress_percent=progress,
                current_step=step,
                downloaded_bytes=downloaded,
                download_speed=speed if speed > 0 else None
            )
            await asyncio.sleep(0.5)  # Pause pour voir les messages
        
        await interface.complete_operation("download_test", success=True)
        
        # Test de transcription avec fallback
        print("\\n🎵 Test de transcription avec fallback...")
        
        tracker2 = await interface.track_operation(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="transcription_test",
            model_name="nemo-asr-fr",
            language="fr",
            quality_preference="balanced",
            estimated_duration=30.0
        )
        
        transcription_steps = [
            (0, "Initialisation", None),
            (10, "Chargement du modèle NeMo", None),
            (25, "Traitement audio", 65.0),  # GPU usage
            (40, "Erreur CUDA détectée", "CUDA out of memory"),
            (45, "Basculement vers Whisper", None),
            (70, "Traitement avec Whisper", 45.0),  # GPU usage réduite
            (100, "Transcription terminée", None)
        ]
        
        for i, (progress, step, gpu_usage, *error) in enumerate(transcription_steps):
            update_kwargs = {
                "progress_percent": progress,
                "current_step": step
            }
            
            if gpu_usage is not None:
                update_kwargs["gpu_usage"] = gpu_usage
            
            if error and error[0]:
                update_kwargs["error_message"] = error[0]
                # Simuler la récupération après l'erreur
                if i < len(transcription_steps) - 1:
                    update_kwargs["error_message"] = None
            
            await tracker2.update(**update_kwargs)
            await asyncio.sleep(0.4)
        
        await interface.complete_operation("transcription_test", success=True)
        
        # Test de chargement de modèle avec avertissement mémoire
        print("\\n📦 Test de chargement de modèle avec avertissement mémoire...")
        
        tracker3 = await interface.track_operation(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_loading_test",
            model_name="nemo-asr-large",
            estimated_duration=20.0
        )
        
        model_steps = [
            (0, "Initialisation du modèle", 0, 30),
            (25, "Chargement sur GPU", 40, 60),
            (50, "Optimisation mémoire", 70, 88),  # Avertissement mémoire
            (75, "Finalisation", 60, 75),
            (100, "Modèle prêt", 55, 70)
        ]
        
        for progress, step, gpu, memory in model_steps:
            await tracker3.update(
                progress_percent=progress,
                current_step=step,
                gpu_usage=gpu,
                memory_usage=memory
            )
            await asyncio.sleep(0.3)
        
        await interface.complete_operation("model_loading_test", success=True)
        
        # Test d'opération échouée
        print("\\n❌ Test d'opération échouée...")
        
        tracker4 = await interface.track_operation(
            operation_type=OperationType.DOWNLOAD,
            operation_id="failed_download",
            model_name="large-model",
            total_bytes=2000000000
        )
        
        await tracker4.update(
            progress_percent=25,
            current_step="Téléchargement interrompu",
            downloaded_bytes=500000000,
            download_speed=100000  # Connexion très lente
        )
        
        await asyncio.sleep(0.5)
        
        await interface.complete_operation(
            "failed_download", 
            success=False, 
            error_message="Connection timeout"
        )
        
        # Afficher les statistiques
        print("\\n📊 Statistiques finales:")
        stats = interface.get_statistics()
        for key, value in stats.items():
            if key == "success_rate":
                print(f"   {key}: {value:.1%}")
            else:
                print(f"   {key}: {value}")
        
        print(f"\\n📨 Messages contextuels générés: {len(messages)}")
        
        # Analyser les types de messages
        message_types = {}
        for msg in messages:
            if msg.contextual_message:
                msg_type = msg.contextual_message.message_type.value
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        print("📈 Répartition des types de messages:")
        for msg_type, count in message_types.items():
            print(f"   {msg_type}: {count}")
        
    finally:
        await interface.shutdown()
    
    print("\\n✅ Test basique terminé")

async def test_concurrent_operations():
    """Test d'opérations concurrentes avec messages contextuels"""
    print("\\n⚡ Test d'opérations concurrentes")
    print("-" * 40)
    
    interface = EnhancedRealTimeProgressInterface()
    
    # Collecteur de messages par opération
    operation_messages = {}
    
    def progress_callback(progress_update):
        op_id = progress_update.operation_id
        if op_id not in operation_messages:
            operation_messages[op_id] = []
        
        operation_messages[op_id].append(progress_update)
        
        contextual_msg = progress_update.contextual_message
        if contextual_msg:
            print(f"[{op_id[:8]}] {contextual_msg.message}")
    
    interface.add_progress_callback(progress_callback)
    
    try:
        # Lancer plusieurs opérations en parallèle
        operations = [
            ("download_1", OperationType.DOWNLOAD, {"model_name": "whisper-base", "total_bytes": 500000000}),
            ("transcription_1", OperationType.TRANSCRIPTION, {"model_name": "nemo-fr", "language": "fr"}),
            ("model_load_1", OperationType.MODEL_LOADING, {"model_name": "nemo-large"}),
            ("cache_op_1", OperationType.CACHE_OPERATION, {})
        ]
        
        # Créer tous les trackers
        trackers = {}
        for op_id, op_type, kwargs in operations:
            tracker = await interface.track_operation(
                operation_type=op_type,
                operation_id=op_id,
                **kwargs
            )
            trackers[op_id] = tracker
        
        # Simuler la progression en parallèle
        async def simulate_operation(op_id, tracker, op_type):
            steps = 5
            for i in range(steps + 1):
                progress = (i / steps) * 100
                step_name = f"Étape {i+1}/{steps+1}"
                
                update_kwargs = {
                    "progress_percent": progress,
                    "current_step": step_name
                }
                
                # Ajouter des métriques spécifiques selon le type
                if op_type == OperationType.DOWNLOAD:
                    update_kwargs.update({
                        "downloaded_bytes": int(progress * 5000000),  # 500MB total
                        "download_speed": 1500000 + (i * 200000)  # Vitesse variable
                    })
                elif op_type == OperationType.TRANSCRIPTION:
                    update_kwargs["gpu_usage"] = 50 + (i * 5)
                elif op_type == OperationType.MODEL_LOADING:
                    update_kwargs.update({
                        "gpu_usage": 30 + (i * 10),
                        "memory_usage": 40 + (i * 8)
                    })
                
                await tracker.update(**update_kwargs)
                await asyncio.sleep(0.2 + (i * 0.1))  # Vitesses différentes
            
            await interface.complete_operation(op_id, success=True)
        
        # Lancer toutes les simulations en parallèle
        tasks = [
            simulate_operation(op_id, tracker, op_type)
            for (op_id, op_type, _), tracker in zip(operations, trackers.values())
        ]
        
        await asyncio.gather(*tasks)
        
        # Analyser les résultats
        print("\\n📊 Résultats des opérations concurrentes:")
        for op_id, messages in operation_messages.items():
            print(f"   {op_id}: {len(messages)} messages générés")
        
        stats = interface.get_statistics()
        print(f"\\n📈 Statistiques: {stats['completed_operations']}/{stats['total_operations']} réussies")
        
    finally:
        await interface.shutdown()
    
    print("✅ Test de concurrence terminé")

async def test_error_scenarios():
    """Test de scénarios d'erreur avec messages contextuels"""
    print("\\n🚨 Test de scénarios d'erreur")
    print("-" * 35)
    
    interface = EnhancedRealTimeProgressInterface()
    
    error_messages = []
    
    def progress_callback(progress_update):
        contextual_msg = progress_update.contextual_message
        if contextual_msg and contextual_msg.message_type == MessageType.ERROR:
            error_messages.append(contextual_msg)
            print(f"🚨 {contextual_msg.message}")
            if contextual_msg.suggestions:
                print(f"   💡 Solutions: {contextual_msg.suggestions}")
    
    def error_callback(operation_id, error_message):
        print(f"❌ Erreur finale {operation_id}: {error_message}")
    
    interface.add_progress_callback(progress_callback)
    interface.add_error_callback(error_callback)
    
    try:
        # Scénarios d'erreur
        error_scenarios = [
            ("cuda_error", "CUDA out of memory", OperationType.TRANSCRIPTION),
            ("network_error", "Connection timeout", OperationType.DOWNLOAD),
            ("memory_error", "MemoryError: Unable to allocate tensor", OperationType.MODEL_LOADING),
            ("model_error", "FileNotFoundError: Model file not found", OperationType.MODEL_LOADING)
        ]
        
        for op_id, error_msg, op_type in error_scenarios:
            print(f"\\n🧪 Test d'erreur: {error_msg}")
            
            tracker = await interface.track_operation(
                operation_type=op_type,
                operation_id=op_id
            )
            
            # Progression normale puis erreur
            await tracker.update(
                progress_percent=30,
                current_step="Opération en cours"
            )
            
            await asyncio.sleep(0.2)
            
            await tracker.update(
                progress_percent=50,
                current_step="Erreur détectée",
                error_message=error_msg
            )
            
            await asyncio.sleep(0.2)
            
            await interface.complete_operation(op_id, success=False, error_message=error_msg)
        
        print(f"\\n📊 Messages d'erreur générés: {len(error_messages)}")
        
        # Analyser les suggestions
        all_suggestions = set()
        for msg in error_messages:
            all_suggestions.update(msg.suggestions)
        
        print(f"💡 Suggestions uniques générées: {len(all_suggestions)}")
        for suggestion in sorted(all_suggestions):
            print(f"   - {suggestion}")
        
    finally:
        await interface.shutdown()
    
    print("✅ Test de scénarios d'erreur terminé")

if __name__ == "__main__":
    asyncio.run(test_enhanced_progress_basic())
    asyncio.run(test_concurrent_operations())
    asyncio.run(test_error_scenarios())