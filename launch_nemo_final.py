"""
Lanceur final NeMo avec blocage complet Pyannote
"""

import os
import sys
import signal

# 1. PATCH SIGNAL POUR NEMO WINDOWS
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM
if not hasattr(signal, 'SIGUSR1'):
    signal.SIGUSR1 = signal.SIGTERM
if not hasattr(signal, 'SIGUSR2'):
    signal.SIGUSR2 = signal.SIGTERM

print("✅ Signal SIGKILL patché pour Windows")

# 2. APPLIQUER LE BLOCAGE PYANNOTE ULTIME
print("🚫 Application du blocage Pyannote ultime...")
exec(open('ultimate_pyannote_blocker.py').read())

# 3. VARIABLES D'ENVIRONNEMENT SPÉCIFIQUES
os.environ["NEMO_MODEL_NAME"] = "nvidia/stt_en_fastconformer_ctc_large"
os.environ["NEMO_MODEL_TYPE"] = "FastConformer"
os.environ["NEMO_MODEL_LOADED"] = "1"

print(f"📦 Modèle configuré: {os.environ['NEMO_MODEL_NAME']}")

# 4. LANCEMENT DE L'APPLICATION
print("🚀 Lancement application finale avec NeMo FastConformer...")
print("=" * 70)

try:
    # Importer et lancer l'application
    import main
    
    # Forcer le mode GUI
    if len(sys.argv) == 1:
        sys.argv.append("--gui")
    
    # Lancer
    main.main()
    
except Exception as e:
    print(f"❌ Erreur de lancement: {e}")
    import traceback
    traceback.print_exc()
    
    # Essayer un lancement alternatif
    print("\n🔄 Tentative de lancement alternatif...")
    try:
        os.system("python main.py --gui")
    except Exception as e2:
        print(f"❌ Erreur lancement alternatif: {e2}")
        input("Appuyez sur Entrée pour fermer...")