"""
Test de l'interface de gestion des modèles
"""
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from ai_video_dubbing.performance.model_manager_ui import (
    ModelManagerUI, ModelInfo, ModelType, ModelStatus, DiskUsageInfo
)

async def test_model_manager_ui_basic():
    """Test basique de l'interface de gestion des modèles"""
    print("📦 Test basique de l'interface de gestion des modèles")
    print("-" * 50)
    
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
        
        for model_info in models_list:
            status_icon = {
                ModelStatus.AVAILABLE: "✅",
                ModelStatus.DOWNLOADING: "⬇️",
                ModelStatus.CORRUPTED: "❌",
                ModelStatus.MISSING: "❓",
                ModelStatus.VALIDATING: "🔍"
            }.get(model_info.status, "❓")
            
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
        
        return manager
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_model_download():
    """Test de téléchargement de modèles"""
    print("\\n⬇️ Test de téléchargement de modèles")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    cache_dir = Path(temp_dir) / "cache"
    
    try:
        manager = ModelManagerUI(models_dir=str(models_dir), cache_dir=str(cache_dir))
        
        # Callback de progression
        progress_updates = []
        
        async def progress_callback(model_id, progress, downloaded, total):
            progress_updates.append((model_id, progress, downloaded, total))
            if len(progress_updates) % 5 == 0:  # Afficher tous les 5 updates
                print(f"      Progression: {progress:.1f}% ({downloaded / (1024**2):.1f}/{total / (1024**2):.1f} MB)")
        
        # Afficher les modèles disponibles
        print("📋 Modèles disponibles au téléchargement:")
        available = manager.get_available_models()
        
        for model_key, model_spec in available.items():
            already_downloaded = "✅ Déjà téléchargé" if model_spec["already_downloaded"] else "⬇️ Disponible"
            print(f"   {model_key}: {model_spec['name']} ({model_spec['size_formatted']}) - {already_downloaded}")
        
        # Télécharger un modèle
        print("\\n⬇️ Téléchargement de whisper-tiny...")
        
        success = await manager.download_model("whisper-tiny", progress_callback)
        
        if success:
            print("   ✅ Téléchargement réussi")
            print(f"   📊 {len(progress_updates)} mises à jour de progression reçues")
        else:
            print("   ❌ Téléchargement échoué")
        
        # Vérifier que le modèle est maintenant dans la liste
        models_list = manager.get_models_list()
        downloaded_model = next((m for m in models_list if "whisper-tiny" in m.model_id), None)
        
        if downloaded_model:
            print(f"   📦 Modèle ajouté: {downloaded_model.name} ({downloaded_model.file_size / (1024**2):.1f} MB)")
            print(f"      Statut: {downloaded_model.status.value}")
            print(f"      Chemin: {downloaded_model.file_path}")
        
        # Test d'utilisation du modèle
        if downloaded_model:
            print("\\n📈 Test d'enregistrement d'utilisation...")
            
            # Enregistrer quelques utilisations
            for i in range(3):
                await manager.record_model_usage(downloaded_model.model_id)
            
            # Vérifier les statistiques mises à jour
            updated_model = manager.get_model_info(downloaded_model.model_id)
            print(f"   Utilisations: {updated_model.usage_count}")
            print(f"   Dernière utilisation: {updated_model.last_used}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_model_recommendations():
    """Test des recommandations de modèles"""
    print("\\n💡 Test des recommandations de modèles")
    print("-" * 38)
    
    temp_dir = tempfile.mkdtemp()
    manager = ModelManagerUI(models_dir=str(Path(temp_dir) / "models"))
    
    try:
        # Différents scénarios système
        scenarios = [
            {
                "name": "Système faible",
                "system_info": {
                    "available_memory": 2 * 1024**3,  # 2GB
                    "cuda_available": False,
                    "free_disk": 10 * 1024**3  # 10GB
                }
            },
            {
                "name": "Système moyen",
                "system_info": {
                    "available_memory": 8 * 1024**3,  # 8GB
                    "cuda_available": True,
                    "free_disk": 50 * 1024**3  # 50GB
                }
            },
            {
                "name": "Système puissant",
                "system_info": {
                    "available_memory": 32 * 1024**3,  # 32GB
                    "cuda_available": True,
                    "free_disk": 500 * 1024**3  # 500GB
                }
            }
        ]
        
        for scenario in scenarios:
            print(f"\\n🖥️ {scenario['name']}:")
            system_info = scenario['system_info']
            
            print(f"   RAM: {system_info['available_memory'] / (1024**3):.0f} GB")
            print(f"   GPU: {'Oui' if system_info['cuda_available'] else 'Non'}")
            print(f"   Disque libre: {system_info['free_disk'] / (1024**3):.0f} GB")
            
            recommendations = manager.get_model_recommendations(system_info)
            
            print(f"   💡 Recommandations: {len(recommendations)} modèle(s)")
            for model_key in recommendations:
                if model_key in manager.available_models:
                    model_spec = manager.available_models[model_key]
                    print(f"      - {model_spec['name']} ({model_spec['size'] / (1024**2):.0f} MB)")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_model_cleanup():
    """Test du nettoyage des modèles"""
    print("\\n🧹 Test du nettoyage des modèles")
    print("-" * 32)
    
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    
    try:
        manager = ModelManagerUI(models_dir=str(models_dir))
        
        # Créer quelques modèles factices avec différents âges d'utilisation
        print("📦 Création de modèles avec différents patterns d'utilisation...")
        
        # Modèle récemment utilisé
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
        
        # Effectuer le nettoyage (seuil de 30 jours)
        print("\\n🧹 Nettoyage des modèles non utilisés depuis 30 jours...")
        
        cleaned_models = await manager.cleanup_unused_models(days_threshold=30)
        
        print(f"   Modèles nettoyés: {len(cleaned_models)}")
        for model_name in cleaned_models:
            print(f"      - {model_name}")
        
        print(f"   Modèles restants: {len(manager.models)}")
        
        # Vérifier que seul le modèle récent reste
        remaining_models = list(manager.models.keys())
        print(f"   Modèles restants: {remaining_models}")
        
        if "recent_model" in remaining_models and len(remaining_models) == 1:
            print("   ✅ Nettoyage correct - seul le modèle récent est conservé")
        else:
            print("   ⚠️ Nettoyage inattendu")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_visualization_data():
    """Test des données de visualisation"""
    print("\\n📊 Test des données de visualisation")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    
    try:
        manager = ModelManagerUI(models_dir=str(models_dir))
        
        # Ajouter quelques modèles avec des données variées
        models_data = [
            {
                "model_id": "whisper_1",
                "name": "Whisper Tiny",
                "type": ModelType.WHISPER,
                "size": 39 * 1024**2,
                "usage": 15,
                "quality": 7.5
            },
            {
                "model_id": "whisper_2", 
                "name": "Whisper Base",
                "type": ModelType.WHISPER,
                "size": 142 * 1024**2,
                "usage": 8,
                "quality": 8.0
            },
            {
                "model_id": "nemo_1",
                "name": "NeMo Conformer",
                "type": ModelType.NEMO_ASR,
                "size": 600 * 1024**2,
                "usage": 3,
                "quality": 9.0
            }
        ]
        
        for data in models_data:
            model_info = ModelInfo(
                model_id=data["model_id"],
                name=data["name"],
                model_type=data["type"],
                status=ModelStatus.AVAILABLE,
                file_size=data["size"],
                usage_count=data["usage"],
                quality_score=data["quality"],
                download_date=time.time() - (len(models_data) - models_data.index(data)) * 24 * 3600
            )
            manager.models[data["model_id"]] = model_info
        
        print("📊 Génération des données de visualisation...")
        
        viz_data = manager.get_model_visualization_data()
        
        print("✅ Données générées:")
        print(f"   Utilisation disque: {viz_data['disk_usage']['models_gb']:.1f} GB de modèles")
        print(f"   Modèles par type: {len(viz_data['models_by_type'])} types")
        print(f"   Modèles par statut: {len(viz_data['models_by_status'])} statuts")
        print(f"   Timeline: {len(viz_data['models_timeline'])} entrées")
        print(f"   Top modèles: {len(viz_data['top_models'])} modèles")
        
        # Afficher le top des modèles
        print("\\n🏆 Top modèles par utilisation:")
        for i, model in enumerate(viz_data['top_models'][:3], 1):
            print(f"   {i}. {model['name']}: {model['usage_count']} utilisations ({model['size_mb']:.0f} MB)")
        
        # Afficher la répartition par type
        print("\\n📊 Répartition par type:")
        for type_data in viz_data['models_by_type']:
            print(f"   {type_data['type']}: {type_data['count']} modèle(s)")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def test_persistence():
    """Test de la persistance des données"""
    print("\\n💾 Test de la persistance des données")
    print("-" * 35)
    
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    cache_dir = Path(temp_dir) / "cache"
    
    try:
        # Premier gestionnaire - sauvegarder des données
        print("📝 Sauvegarde des données...")
        
        manager1 = ModelManagerUI(models_dir=str(models_dir), cache_dir=str(cache_dir))
        
        # Ajouter un modèle
        test_model = ModelInfo(
            model_id="test_persistence",
            name="Modèle de test",
            model_type=ModelType.WHISPER,
            status=ModelStatus.AVAILABLE,
            file_size=100 * 1024**2,
            usage_count=5
        )
        
        manager1.models["test_persistence"] = test_model
        
        # Sauvegarder
        await manager1.save_models_config()
        
        print(f"   Modèles sauvegardés: {len(manager1.models)}")
        
        # Deuxième gestionnaire - charger les données
        print("\\n📖 Chargement des données...")
        
        manager2 = ModelManagerUI(models_dir=str(models_dir), cache_dir=str(cache_dir))
        
        print(f"   Modèles chargés: {len(manager2.models)}")
        
        # Vérifier que le modèle a été chargé
        loaded_model = manager2.get_model_info("test_persistence")
        
        if loaded_model:
            print("   ✅ Persistance réussie")
            print(f"      Nom: {loaded_model.name}")
            print(f"      Type: {loaded_model.model_type.value}")
            print(f"      Utilisations: {loaded_model.usage_count}")
        else:
            print("   ❌ Échec de la persistance")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_model_manager_ui_basic())
    asyncio.run(test_model_download())
    asyncio.run(test_model_recommendations())
    asyncio.run(test_model_cleanup())
    asyncio.run(test_visualization_data())
    asyncio.run(test_persistence())
    
    print("\\n✅ Tous les tests de l'interface de gestion des modèles terminés")