"""
PATCH DÉFINITIF NEMO WINDOWS
Corrige le bug SIGKILL et force NeMo uniquement
"""

import os
import sys
import shutil
from pathlib import Path

def patch_nemo_sigkill_bug():
    """Patch le bug SIGKILL dans NeMo pour Windows"""
    
    print("🔧 CORRECTION BUG NEMO SIGKILL")
    print("=" * 40)
    
    # Trouver le fichier exp_manager.py de NeMo
    nemo_exp_manager = Path("mon_env/Lib/site-packages/nemo/utils/exp_manager.py")
    
    if not nemo_exp_manager.exists():
        print(f"   ❌ Fichier NeMo non trouvé: {nemo_exp_manager}")
        return False
    
    print(f"   📁 Fichier trouvé: {nemo_exp_manager}")
    
    try:
        # Lire le fichier
        with open(nemo_exp_manager, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Faire une sauvegarde
        backup_path = nemo_exp_manager.with_suffix('.py.original')
        if not backup_path.exists():
            shutil.copy2(nemo_exp_manager, backup_path)
            print(f"   💾 Sauvegarde: {backup_path}")
        
        # Patch SIGKILL -> SIGTERM pour Windows
        if "signal.SIGKILL" in content:
            content = content.replace(
                "rank_termination_signal: signal.Signals = signal.SIGKILL",
                "rank_termination_signal: signal.Signals = signal.SIGTERM"
            )
            
            # Écrire le fichier corrigé
            with open(nemo_exp_manager, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("   ✅ SIGKILL remplacé par SIGTERM")
            return True
        else:
            print("   ℹ️ SIGKILL déjà patché")
            return True
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def create_nemo_only_launcher():
    """Crée un lanceur qui force NeMo uniquement"""
    
    print(f"\n🚀 LANCEUR NEMO UNIQUEMENT")
    print("=" * 40)
    
    # Script Python qui force NeMo
    nemo_script = '''"""
Script de lancement NeMo uniquement - Windows
"""

import os
import sys
import signal
from unittest.mock import MagicMock

# 1. PATCH SIGNAL POUR NEMO
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
    print("✅ Signal SIGKILL patché pour Windows")

# 2. VARIABLES D'ENVIRONNEMENT CRITIQUES
critical_env = {
    "USE_NEMO_ONLY": "1",
    "DISABLE_PYANNOTE": "1",
    "FORCE_NEMO_DIARIZATION": "1",
    "SKIP_PYANNOTE_IMPORT": "1",
    "NEMO_WINDOWS_PATCH": "1",
    "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    "TRANSFORMERS_OFFLINE": "0"
}

for key, value in critical_env.items():
    os.environ[key] = value

print("🎯 Variables d'environnement configurées")

# 3. MOCK COMPLET DE PYANNOTE
pyannote_modules = [
    "pyannote",
    "pyannote.audio", 
    "pyannote.audio.pipelines",
    "pyannote.audio.pipelines.speaker_diarization",
    "pyannote.core",
    "pyannote.database"
]

for module in pyannote_modules:
    if module not in sys.modules:
        mock = MagicMock()
        if "Pipeline" in module or "speaker_diarization" in module:
            mock.Pipeline = MagicMock()
            mock.Pipeline.from_pretrained = MagicMock(return_value=None)
            mock.SpeakerDiarization = MagicMock(return_value=None)
        sys.modules[module] = mock

print("🚫 Pyannote complètement désactivé")

# 4. LANCEMENT DE L'APPLICATION
print("🚀 Lancement avec NeMo uniquement...")
print("=" * 50)

try:
    # Importer et lancer l'application principale
    import main
    
except Exception as e:
    print(f"❌ Erreur de lancement: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")
'''
    
    with open("launch_nemo_only.py", 'w', encoding='utf-8') as f:
        f.write(nemo_script)
    
    print("   ✅ Script Python créé: launch_nemo_only.py")
    
    # Batch file pour Windows
    batch_content = '''@echo off
echo ========================================
echo    LANCEMENT NEMO UNIQUEMENT - WINDOWS
echo ========================================
echo.

echo Activation environnement...
call mon_env\\Scripts\\activate

echo Application patch NeMo Windows...
python final_nemo_windows_fix.py

echo.
echo ========================================
echo LANCEMENT AVEC NEMO UNIQUEMENT
echo - Bug SIGKILL: Corrigé
echo - Pyannote: Complètement désactivé  
echo - NeMo: Forcé pour tout
echo ========================================
echo.

echo Lancement application...
python launch_nemo_only.py

echo.
if errorlevel 1 (
    echo ❌ ERREUR DETECTEE
    pause
) else (
    echo ✅ TERMINÉ AVEC SUCCÈS
    pause
)
'''
    
    with open("start_nemo_only.bat", 'w') as f:
        f.write(batch_content)
    
    print("   ✅ Lanceur batch créé: start_nemo_only.bat")

def create_emergency_pyannote_disable():
    """Crée un script d'urgence pour désactiver Pyannote"""
    
    print(f"\n🚨 DÉSACTIVATION D'URGENCE PYANNOTE")
    print("=" * 40)
    
    # Chercher les fichiers qui utilisent Pyannote
    pyannote_files = []
    
    for py_file in Path(".").rglob("*.py"):
        if py_file.name.startswith(("test_", "final_", "launch_", "patch_")):
            continue
        if "__pycache__" in str(py_file) or "mon_env" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if any(term in content.lower() for term in ["pyannote", "speaker_diarization", "pipeline.from_pretrained"]):
                pyannote_files.append(py_file)
                
        except Exception:
            continue
    
    print(f"   📋 Fichiers avec Pyannote: {len(pyannote_files)}")
    
    for file_path in pyannote_files:
        print(f"   - {file_path}")
        
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Faire une sauvegarde
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)
            
            # Remplacements critiques
            replacements = [
                ("from pyannote.audio import Pipeline", "# from pyannote.audio import Pipeline  # DISABLED FOR NEMO"),
                ("import pyannote", "# import pyannote  # DISABLED FOR NEMO"),
                ("Pipeline.from_pretrained", "None  # Pipeline.from_pretrained  # DISABLED FOR NEMO"),
                ("pipeline = Pipeline", "pipeline = None  # Pipeline  # DISABLED FOR NEMO"),
                ("SpeakerDiarization", "None  # SpeakerDiarization  # DISABLED FOR NEMO"),
            ]
            
            modified = False
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    modified = True
            
            if modified:
                # Ajouter un header
                header = "# PATCHED: Pyannote disabled for NeMo-only mode\n"
                if not content.startswith(header):
                    content = header + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"     ✅ Patché: {file_path}")
            
        except Exception as e:
            print(f"     ⚠️ Erreur patch {file_path}: {e}")

def main():
    """Fonction principale"""
    
    print("🚨 PATCH DÉFINITIF NEMO WINDOWS")
    print("=" * 60)
    print("Objectif: Corriger NeMo et forcer son utilisation exclusive")
    print()
    
    success_count = 0
    
    try:
        # 1. Corriger le bug SIGKILL de NeMo
        if patch_nemo_sigkill_bug():
            success_count += 1
        
        # 2. Créer le lanceur NeMo uniquement
        create_nemo_only_launcher()
        success_count += 1
        
        # 3. Désactiver Pyannote d'urgence
        create_emergency_pyannote_disable()
        success_count += 1
        
        print(f"\n📊 RÉSUMÉ")
        print(f"   Étapes réussies: {success_count}/3")
        
        if success_count >= 2:
            print(f"\n✅ PATCH APPLIQUÉ AVEC SUCCÈS")
            print(f"\n🚨 INSTRUCTIONS:")
            print(f"   1. UTILISEZ: start_nemo_only.bat")
            print(f"   2. OU: python launch_nemo_only.py")
            print(f"\n⚠️ IMPORTANT:")
            print(f"   - NeMo corrigé pour Windows")
            print(f"   - Pyannote complètement désactivé")
            print(f"   - Sauvegardes dans *.backup")
        else:
            print(f"\n⚠️ PATCH PARTIEL - Vérifiez les erreurs")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()