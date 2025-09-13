"""
Test direct de l'interface de gestion des modèles
"""
import asyncio
import tempfile
import shutil
import time
import sys
import os
import importlib.util
from pathlib import Path

async def test_model_manager_direct():
    """Test direct de l'interface de gestion des modèles"""
    print("📦 Test direct de l'interface de gestion des modèles")
    print("-" * 50)
    
    # Importer directement le module
    spec = importlib.util.spec_from_file_location(
        "model_manager_ui", 
        "ai_video_dubbing/performance/model_manager_ui.py"
    )
    manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager_module)
    
    ModelManagerUI = manager_module.ModelManagerUI
    ModelInfo = manager_module.ModelInfo
    ModelType = manager_module.ModelType
    ModelStatus = manager_module.ModelStatus
    
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    cache_dir = Path(temp_dir) / "cache"
    
    try:
        manager = ModelManagerUI(models_dir=str(models_dir), cache_dir=str(cache_dir))
        
        # Callbacks pour capturer les événements
        events = []
        
        def event_callback(data):
            events.append(data)
            print(f"📢 Événement: {data}")
        
        # Enregistrer les callbacks
        manager.add_event_callback("model_added", event_callback)
        manager.add_event_callback("model_updated", event_callback)
        manager.add_event_callback("download_progress", event_callback)
        
        print("🔍 Scan initial des modèles...")
        discovered = await manager.scan_models()
        print(f"   Modèles découverts: {len(discovered)}")
        
        # Créer quelques fichiers de modèles factices
        print("\\n📁 Création de modèles factices...")
        
        fake_models = [
            ("whisper_tiny.pt", 39 * 1024**2),
            ("nemo_conformer.pt", 600 * 1024**2),
            ("custom_model.onnx", 200 * 1024**2)
        ]
        
        for model_name, size in fake_models:
            model_path = models_dir / model_name
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Créer un fichier factice
            with open(model_path, 'wb') as f:
                f.write(b'0' * size)
            
            print(f"   Créé: {model_name} ({size / (1024**2):.1f} MB)")
        
        # Scanner à nouveau pour détecter les nouveaux modèles
        print("\\n🔍 Nouveau scan après création...")
        discovered = await manager.scan_models()
        print(f"   Nouveaux modèles découverts: {len(discovered)}")
        
        # Afficher la liste des modèles
        print("\\n📋 Liste des modèles:")
        models_list = manager.get_models_list()
        
        status_icons = {
            ModelStatus.AVAILABLE: "✅",
            ModelStatus.DOWNLOADING: "⬇️",
            ModelStatus.CORRUPTED: "❌",
            ModelStatus.MISSING: "❓",
            ModelStatus.VALIDATING: "🔍"
        }
        
        for model_info in models_list:
            status_icon = status_icons.get(model_info.status, "❓")
            size_mb = model_info.file_size / (1024**2)
            print(f"   {status_icon} {model_info.name} ({model_info.model_type.value}) - {size_mb:.1f} MB")
        
        # Test de validation
        print("\\n🔍 Test de validation des modèles...")
        
        for model_info in models_list[:2]:  # Valider les 2 premiers
            print(f"   Validation de {model_info.name}...")
            is_valid = await manager.validate_model(model_info.model_id)
            print(f"      {'✅ Valide' if is_valid else '❌ Invalide'}")
        
        # Statistiques
        print("\\n📊 Statistiques des modèles:")
        stats = manager.get_models_statistics()
        
        print(f"   Total: {stats['total_models']} modèles")
        print(f"   Taille totale: {stats['total_size'] / (1024**2):.1f} MB")
        print(f"   Par type: {stats['by_type']}")
        print(f"   Par statut: {stats['by_status']}")
        
        if stats['most_used']:
            print(f"   Plus utilisé: {stats['most_used']['name']} ({stats['most_used']['usage_count']} fois)")
        
        # Utilisation disque
        print("\\n💾 Utilisation disque:")
        disk_usage = manager.get_disk_usage()
        
        print(f"   Espace total: {disk_usage.total_space / (1024**3):.1f} GB")
        print(f"   Espace utilisé: {disk_usage.used_space / (1024**3):.1f} GB ({disk_usage.usage_percent:.1f}%)")
        print(f"   Espace libre: {disk_usage.free_space / (1024**3):.1f} GB")
        print(f"   Espace modèles: {disk_usage.models_space / (1024**2):.1f} MB")
        
        # Test de téléchargement
        print("\\n⬇️ Test de téléchargement de modèle...")
        
        # Afficher les modèles disponibles
        available = manager.get_available_models()
        print(f"   Modèles disponibles: {len(available)}")
        
        for model_key, model_spec in list(available.items())[:3]:  # Afficher les 3 premiers
            status = "✅ Déjà téléchargé" if model_spec["already_downloaded"] else "⬇️ Disponible"
            print(f"      {model_key}: {model_spec['name']} ({model_spec['size_formatted']}) - {status}")
        
        # Télécharger whisper-tiny
        print("\\n   Téléchargement de whisper-tiny...")
        
        progress_updates = []
        
        async def progress_callback(model_id, progress, downloaded, total):
            progress_updates.append((progress, downloaded, total))
            if len(progress_updates) % 5 == 0:  # Afficher tous les 5 updates
                print(f"      Progression: {progress:.1f}% ({downloaded / (1024**2):.1f}/{total / (1024**2):.1f} MB)")
        
        success = await manager.download_model("whisper-tiny", progress_callback)
        
        if success:
            print("      ✅ Téléchargement réussi")
            print(f"      📊 {len(progress_updates)} mises à jour de progression")
        else:
            print("      ❌ Téléchargement échoué")
        
        # Test de recommandations
        print("\\n💡 Test de recommandations:")
        
        system_scenarios = [
            {
                "name": "Système faible",
                "info": {
                    "available_memory": 2 * 1024**3,  # 2GB
                    "cuda_available": False,
                    "free_disk": 10 * 1024**3  # 10GB
                }
            },
            {
                "name": "Système puissant",
                "info": {
                    "available_memory": 16 * 1024**3,  # 16GB
                    "cuda_available": True,
                    "free_disk": 100 * 1024**3  # 100GB
                }
            }
        ]
        
        for scenario in system_scenarios:
            print(f"\\n   🖥️ {scenario['name']}:")
            recommendations = manager.get_model_recommendations(scenario['info'])
            print(f"      Recommandations: {len(recommendations)} modèle(s)")
            
            for model_key in recommendations[:3]:  # Max 3
                if model_key in manager.available_models:
                    model_spec = manager.available_models[model_key]
                    print(f"         - {model_spec['name']} ({model_spec['size'] / (1024**2):.0f} MB)")
        
        # Test de données de visualisation
        print("\\n📊 Données de visualisation:")
        viz_data = manager.get_model_visualization_data()
        
        print(f"   Utilisation disque: {viz_data['disk_usage']['models_gb']:.1f} GB de modèles")
        print(f"   Types de modèles: {len(viz_data['models_by_type'])}")
        print(f"   Statuts: {len(viz_data['models_by_status'])}")
        
        if viz_data['top_models']:
            print("   🏆 Top modèles:")
            for model in viz_data['top_models'][:2]:
                print(f"      - {model['name']}: {model['usage_count']} utilisations")
        
        print(f"\\n📢 Événements capturés: {len(events)}")
        
        return manager
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_model_cleanup_direct():
    """Test du nettoyage des modèles"""
    print("\\n🧹 Test du nettoyage des modèles")
    print("-" * 32)
    
    # Importer le module
    spec = importlib.util.spec_from_file_location(
        "model_manager_ui", 
        "ai_video_dubbing/performance/model_manager_ui.py"
    )
    manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager_module)
    
    ModelManagerUI = manager_module.ModelManagerUI
    ModelInfo = manager_module.ModelInfo
    ModelType = manager_module.ModelType
    ModelStatus = manager_module.ModelStatus
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = ModelManagerUI(models_dir=str(Path(temp_dir) / "models"))
        
        # Créer des modèles avec différents patterns d'utilisation
        print("📦 Création de modèles avec différents âges...")
        
        # Modèle récent
        recent_model = ModelInfo(
            model_id="recent_model",
            name="Modèle récent",
            model_type=ModelType.WHISPER,
            status=ModelStatus.AVAILABLE,
            file_size=100 * 1024**2,
            usage_count=5,
            last_used=time.time() - 3600  # Il y a 1 heure
        )
        
        # Modèle ancien non utilisé
        old_unused_model = ModelInfo(
            model_id="old_unused_model",
            name="Modèle ancien non utilisé",
            model_type=ModelType.NEMO_ASR,
            status=ModelStatus.AVAILABLE,
            file_size=500 * 1024**2,
            usage_count=0,
            last_used=time.time() - 40 * 24 * 3600  # Il y a 40 jours
        )
        
        # Modèle jamais utilisé
        never_used_model = ModelInfo(
            model_id="never_used_model",
            name="Modèle jamais utilisé",
            model_type=ModelType.CUSTOM,
            status=ModelStatus.AVAILABLE,
            file_size=200 * 1024**2,
            usage_count=0,
            last_used=None
        )
        
        # Ajouter les modèles
        manager.models.update({
            "recent_model": recent_model,
            "old_unused_model": old_unused_model,
            "never_used_model": never_used_model
        })
        
        print(f"   Modèles avant nettoyage: {len(manager.models)}")
        for model_id, model_info in manager.models.items():
            age_text = "jamais utilisé" if not model_info.last_used else f"utilisé il y a {(time.time() - model_info.last_used) / (24*3600):.0f} jours"
            print(f"      - {model_info.name}: {age_text} ({model_info.usage_count} fois)")
        
        # Effectuer le nettoyage
        print("\\n🧹 Nettoyage des modèles non utilisés depuis 30 jours...")
        
        cleaned_models = await manager.cleanup_unused_models(days_threshold=30)
        
        print(f"   Modèles nettoyés: {len(cleaned_models)}")
        for model_name in cleaned_models:
            print(f"      - {model_name}")
        
        print(f"   Modèles restants: {len(manager.models)}")
        for model_id, model_info in manager.models.items():
            print(f"      - {model_info.name}")
        
        if len(manager.models) == 1 and "recent_model" in manager.models:
            print("   ✅ Nettoyage correct - seul le modèle récent est conservé")
        else:
            print("   ⚠️ Résultat de nettoyage inattendu")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_model_manager_direct())
    asyncio.run(test_model_cleanup_direct())
    
    print("\\n✅ Tests de l'interface de gestion des modèles terminés")