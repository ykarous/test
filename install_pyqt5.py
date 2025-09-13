#!/usr/bin/env python3
"""
Script d'installation de PyQt5 et autres dépendances.
"""
import subprocess
import sys
import os

def install_package(package_name, description=""):
    """Installe un package Python."""
    print(f"📦 Installation de {package_name}...")
    if description:
        print(f"   {description}")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {package_name} installé avec succès")
            return True
        else:
            print(f"   ❌ Erreur lors de l'installation de {package_name}")
            print(f"   Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception lors de l'installation de {package_name}: {e}")
        return False

def check_package(package_name):
    """Vérifie si un package est installé."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    """Fonction principale."""
    print("🔧 Installation des dépendances pour AI Video Dubbing")
    print("=" * 60)
    
    # Liste des packages requis
    packages = [
        ("PyQt5", "Interface graphique principale"),
        ("opencv-python", "Traitement d'images et vidéos (optionnel)"),
        ("numpy", "Calculs numériques (optionnel)"),
        ("Pillow", "Traitement d'images (optionnel)")
    ]
    
    # Vérifier les packages déjà installés
    print("\n🔍 Vérification des packages existants...")
    
    installed = []
    to_install = []
    
    for package, description in packages:
        # Nom du module pour l'import (peut être différent du nom pip)
        import_name = package
        if package == "opencv-python":
            import_name = "cv2"
        elif package == "Pillow":
            import_name = "PIL"
        
        if check_package(import_name):
            print(f"   ✅ {package} déjà installé")
            installed.append(package)
        else:
            print(f"   ❌ {package} manquant")
            to_install.append((package, description))
    
    if not to_install:
        print("\n🎉 Toutes les dépendances sont déjà installées!")
        return
    
    # Installer les packages manquants
    print(f"\n📦 Installation de {len(to_install)} package(s)...")
    
    success_count = 0
    
    for package, description in to_install:
        if install_package(package, description):
            success_count += 1
        print()  # Ligne vide pour la lisibilité
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ DE L'INSTALLATION")
    print("=" * 60)
    
    print(f"Packages déjà installés: {len(installed)}")
    print(f"Packages installés avec succès: {success_count}")
    print(f"Packages échoués: {len(to_install) - success_count}")
    
    if success_count == len(to_install):
        print("\n🎉 Installation terminée avec succès!")
        print("\n🚀 Vous pouvez maintenant démarrer l'application:")
        print("   python start_app_safe.py")
        print("   ou")
        print("   python test_startup.py")
    else:
        print(f"\n⚠️ {len(to_install) - success_count} package(s) n'ont pas pu être installés.")
        print("\n🔧 Solutions possibles:")
        print("1. Vérifiez votre connexion internet")
        print("2. Mettez à jour pip: python -m pip install --upgrade pip")
        print("3. Installez manuellement: pip install PyQt5")
        
        if len(to_install) - success_count == len(to_install):
            print("\n❌ Aucun package n'a pu être installé.")
            print("L'application ne pourra pas fonctionner sans PyQt5.")
        else:
            print(f"\n✅ {success_count} package(s) installé(s) sur {len(to_install)}")
            if any(pkg[0] == "PyQt5" for pkg in to_install[:success_count]):
                print("PyQt5 est installé, l'application devrait fonctionner.")

if __name__ == "__main__":
    main()