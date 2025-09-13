"""
Test du système de messages de progression contextuels
"""
import time
from ai_video_dubbing.performance.contextual_messages import (
    ContextualMessageGenerator, ProgressContext, OperationType, MessageType
)

def test_download_messages():
    """Test des messages de téléchargement"""
    print("🔄 Test des messages de téléchargement")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    # Scénarios de téléchargement
    scenarios = [
        # Démarrage
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=0.0,
            current_step="Démarrage du téléchargement",
            start_time=time.time(),
            model_name="whisper-large-v3",
            total_bytes=1500000000,  # 1.5GB
            downloaded_bytes=0
        ),
        
        # Progression normale
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=35.0,
            current_step="Téléchargement en cours",
            start_time=time.time() - 30,
            model_name="whisper-large-v3",
            total_bytes=1500000000,
            downloaded_bytes=525000000,
            download_speed=2500000  # 2.5MB/s
        ),
        
        # Connexion lente
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=15.0,
            current_step="Téléchargement lent",
            start_time=time.time() - 60,
            model_name="whisper-large-v3",
            total_bytes=1500000000,
            downloaded_bytes=225000000,
            download_speed=50000  # 50KB/s - très lent
        ),
        
        # Reprise de téléchargement
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=8.0,
            current_step="Reprise du téléchargement",
            start_time=time.time(),
            model_name="whisper-large-v3",
            total_bytes=1500000000,
            downloaded_bytes=120000000,
            download_speed=1800000
        ),
        
        # Téléchargement terminé
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=100.0,
            current_step="Téléchargement terminé",
            start_time=time.time() - 120,
            model_name="whisper-large-v3",
            total_bytes=1500000000,
            downloaded_bytes=1500000000
        ),
        
        # Échec de téléchargement
        ProgressContext(
            operation_type=OperationType.DOWNLOAD,
            operation_id="dl_001",
            progress_percent=45.0,
            current_step="Erreur de téléchargement",
            start_time=time.time() - 90,
            model_name="whisper-large-v3",
            error_message="Connection timeout"
        )
    ]
    
    for i, context in enumerate(scenarios, 1):
        message = generator.create_progress_message(context)
        
        print(f"{i}. {message.message}")
        print(f"   Type: {message.message_type.value}")
        if message.eta_seconds:
            print(f"   ETA: {message.eta_seconds:.0f}s")
        if message.details:
            print(f"   Détails: {message.details}")
        if message.suggestions:
            print(f"   Suggestions: {message.suggestions}")
        print()

def test_transcription_messages():
    """Test des messages de transcription"""
    print("🎵 Test des messages de transcription")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    scenarios = [
        # Démarrage
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=0.0,
            current_step="Initialisation",
            start_time=time.time(),
            language="fr",
            quality_preference="balanced",
            model_name="nemo-asr-fr"
        ),
        
        # Chargement du modèle
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=15.0,
            current_step="Chargement du modèle NeMo",
            start_time=time.time() - 5,
            language="fr",
            quality_preference="balanced",
            model_name="nemo-asr-fr"
        ),
        
        # Traitement en cours
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=65.0,
            current_step="Traitement audio",
            start_time=time.time() - 25,
            language="fr",
            quality_preference="balanced",
            model_name="nemo-asr-fr",
            gpu_usage=75.0
        ),
        
        # Fallback activé
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=30.0,
            current_step="Fallback vers Whisper",
            start_time=time.time() - 15,
            language="fr",
            quality_preference="balanced",
            model_name="whisper-base",
            metadata={"fallback_model": "whisper-base", "fallback_reason": "Erreur CUDA"}
        ),
        
        # Transcription terminée
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=100.0,
            current_step="Transcription terminée",
            start_time=time.time() - 45,
            language="fr",
            quality_preference="balanced",
            model_name="nemo-asr-fr"
        ),
        
        # Échec de transcription
        ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="trans_001",
            progress_percent=20.0,
            current_step="Erreur de transcription",
            start_time=time.time() - 10,
            language="fr",
            error_message="CUDA out of memory"
        )
    ]
    
    for i, context in enumerate(scenarios, 1):
        message = generator.create_progress_message(context)
        
        print(f"{i}. {message.message}")
        print(f"   Type: {message.message_type.value}")
        if message.eta_seconds:
            print(f"   ETA: {message.eta_seconds:.0f}s")
        if message.details:
            print(f"   Détails: {message.details}")
        if message.suggestions:
            print(f"   Suggestions: {message.suggestions}")
        print()

def test_model_loading_messages():
    """Test des messages de chargement de modèle"""
    print("📦 Test des messages de chargement de modèle")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    scenarios = [
        # Démarrage
        ProgressContext(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_001",
            progress_percent=0.0,
            current_step="Initialisation du modèle",
            start_time=time.time(),
            model_name="nemo-asr-large"
        ),
        
        # Chargement GPU
        ProgressContext(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_001",
            progress_percent=40.0,
            current_step="Chargement sur GPU",
            start_time=time.time() - 8,
            model_name="nemo-asr-large",
            gpu_usage=60.0,
            memory_usage=45.0
        ),
        
        # Avertissement mémoire
        ProgressContext(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_001",
            progress_percent=70.0,
            current_step="Optimisation mémoire",
            start_time=time.time() - 15,
            model_name="nemo-asr-large",
            gpu_usage=85.0,
            memory_usage=92.0
        ),
        
        # Fallback CPU
        ProgressContext(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_001",
            progress_percent=25.0,
            current_step="Basculement vers CPU",
            start_time=time.time() - 5,
            model_name="nemo-asr-large",
            memory_usage=95.0
        ),
        
        # Chargement terminé
        ProgressContext(
            operation_type=OperationType.MODEL_LOADING,
            operation_id="model_001",
            progress_percent=100.0,
            current_step="Modèle prêt",
            start_time=time.time() - 20,
            model_name="nemo-asr-large"
        )
    ]
    
    for i, context in enumerate(scenarios, 1):
        message = generator.create_progress_message(context)
        
        print(f"{i}. {message.message}")
        print(f"   Type: {message.message_type.value}")
        if message.details:
            print(f"   Détails: {message.details}")
        if message.suggestions:
            print(f"   Suggestions: {message.suggestions}")
        print()

def test_cache_messages():
    """Test des messages de cache"""
    print("🗄️ Test des messages de cache")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    scenarios = [
        # Vérification du cache
        ProgressContext(
            operation_type=OperationType.CACHE_OPERATION,
            operation_id="cache_001",
            progress_percent=20.0,
            current_step="Vérification du cache",
            start_time=time.time()
        ),
        
        # Cache hit
        ProgressContext(
            operation_type=OperationType.CACHE_OPERATION,
            operation_id="cache_001",
            progress_percent=100.0,
            current_step="Résultat trouvé dans le cache",
            start_time=time.time() - 1,
            metadata={"time_saved": 45.5}
        ),
        
        # Cache miss
        ProgressContext(
            operation_type=OperationType.CACHE_OPERATION,
            operation_id="cache_002",
            progress_percent=30.0,
            current_step="Résultat non trouvé - traitement nécessaire",
            start_time=time.time() - 2
        ),
        
        # Nettoyage du cache
        ProgressContext(
            operation_type=OperationType.CACHE_OPERATION,
            operation_id="cache_003",
            progress_percent=75.0,
            current_step="Nettoyage du cache en cours",
            start_time=time.time() - 10,
            metadata={"freed_bytes": 2500000000}  # 2.5GB libérés
        ),
        
        # Validation d'intégrité
        ProgressContext(
            operation_type=OperationType.CACHE_OPERATION,
            operation_id="cache_004",
            progress_percent=50.0,
            current_step="Validation de l'intégrité",
            start_time=time.time() - 5
        )
    ]
    
    for i, context in enumerate(scenarios, 1):
        message = generator.create_progress_message(context)
        
        print(f"{i}. {message.message}")
        print(f"   Type: {message.message_type.value}")
        if message.details:
            print(f"   Détails: {message.details}")
        print()

def test_fallback_messages():
    """Test des messages de fallback"""
    print("⚠️ Test des messages de fallback")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    scenarios = [
        # Fallback déclenché
        ProgressContext(
            operation_type=OperationType.FALLBACK,
            operation_id="fallback_001",
            progress_percent=0.0,
            current_step="Fallback activé",
            start_time=time.time(),
            metadata={"fallback_reason": "Erreur CUDA", "fallback_model": "whisper-cpu"}
        ),
        
        # Essai avec fallback
        ProgressContext(
            operation_type=OperationType.FALLBACK,
            operation_id="fallback_001",
            progress_percent=30.0,
            current_step="Essai avec modèle alternatif",
            start_time=time.time() - 5,
            metadata={"fallback_model": "whisper-cpu"}
        ),
        
        # Fallback réussi
        ProgressContext(
            operation_type=OperationType.FALLBACK,
            operation_id="fallback_001",
            progress_percent=100.0,
            current_step="Fallback réussi",
            start_time=time.time() - 15,
            model_name="whisper-cpu"
        ),
        
        # Tous les fallbacks échoués
        ProgressContext(
            operation_type=OperationType.FALLBACK,
            operation_id="fallback_002",
            progress_percent=80.0,
            current_step="Échec de tous les fallbacks",
            start_time=time.time() - 30,
            error_message="Aucun modèle disponible"
        )
    ]
    
    for i, context in enumerate(scenarios, 1):
        message = generator.create_progress_message(context)
        
        print(f"{i}. {message.message}")
        print(f"   Type: {message.message_type.value}")
        if message.suggestions:
            print(f"   Suggestions: {message.suggestions}")
        print()

def test_summary_messages():
    """Test des messages de résumé"""
    print("📊 Test des messages de résumé")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    # Résumé de transcription réussie
    summary1 = generator.create_summary_message(
        operation_type=OperationType.TRANSCRIPTION,
        success=True,
        duration=42.5,
        metrics={
            "quality_score": 0.95,
            "model_used": "nemo-asr-fr",
            "cache_hit": False
        }
    )
    
    print(f"1. {summary1.message}")
    print(f"   Type: {summary1.message_type.value}")
    print(f"   Détails: {summary1.details}")
    print()
    
    # Résumé de téléchargement réussi
    summary2 = generator.create_summary_message(
        operation_type=OperationType.DOWNLOAD,
        success=True,
        duration=125.0,
        metrics={
            "total_bytes": 1500000000,
            "average_speed": 12000000
        }
    )
    
    print(f"2. {summary2.message}")
    print(f"   Type: {summary2.message_type.value}")
    print()
    
    # Résumé d'échec
    summary3 = generator.create_summary_message(
        operation_type=OperationType.TRANSCRIPTION,
        success=False,
        duration=15.2,
        metrics={
            "error_message": "CUDA out of memory",
            "attempted_fallbacks": 3
        }
    )
    
    print(f"3. {summary3.message}")
    print(f"   Type: {summary3.message_type.value}")
    print()

def test_error_classification():
    """Test de la classification d'erreurs"""
    print("🚨 Test de la classification d'erreurs")
    print("-" * 40)
    
    generator = ContextualMessageGenerator()
    
    error_scenarios = [
        ("CUDA out of memory", "cuda_error"),
        ("RuntimeError: CUDA error: device-side assert triggered", "cuda_error"),
        ("MemoryError: Unable to allocate tensor", "memory_error"),
        ("ConnectionError: Failed to download", "network_error"),
        ("FileNotFoundError: Model file not found", "model_error"),
        ("TimeoutError: Operation timed out", "timeout_error"),
        ("ValueError: Invalid input", "general_error")
    ]
    
    for error_msg, expected_type in error_scenarios:
        classified_type = generator._classify_error(error_msg)
        status = "✅" if classified_type == expected_type else "❌"
        print(f"{status} '{error_msg}' -> {classified_type}")
        
        # Tester les suggestions
        context = ProgressContext(
            operation_type=OperationType.TRANSCRIPTION,
            operation_id="error_test",
            progress_percent=50.0,
            current_step="Erreur",
            error_message=error_msg
        )
        
        message = generator.create_progress_message(context)
        if message.suggestions:
            print(f"   Suggestions: {message.suggestions}")
        print()

if __name__ == "__main__":
    test_download_messages()
    test_transcription_messages()
    test_model_loading_messages()
    test_cache_messages()
    test_fallback_messages()
    test_summary_messages()
    test_error_classification()
    
    print("✅ Tous les tests de messages contextuels terminés")