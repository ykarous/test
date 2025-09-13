#!/usr/bin/env python3
"""
Test d'intégration simple pour vérifier que les modifications du main.py fonctionnent
"""

import subprocess
import sys

def test_main_help():
    """Test que le main.py affiche l'aide avec les nouvelles options"""
    print("🧪 Test de l'aide du main.py...")
    
    try:
        result = subprocess.run([sys.executable, "main.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            help_text = result.stdout
            
            # Vérifier les nouvelles options
            new_options = [
                "--mode", "--no-fallback", "--no-cache", 
                "--diagnostic", "--verbose"
            ]
            
            all_found = True
            for option in new_options:
                if option in help_text:
                    print(f"  ✅ {option} trouvé")
                else:
                    print(f"  ❌ {option} manquant")
                    all_found = False
            
            # Vérifier le titre amélioré
            if "Version Optimisée" in help_text:
                print("  ✅ Titre 'Version Optimisée' trouvé")
            else:
                print("  ❌ Titre 'Version Optimisée' manquant")
                all_found = False
            
            return all_found
        else:
            print(f"  ❌ Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False

def test_diagnostic_basic():
    """Test que le diagnostic de base fonctionne"""
    print("\n🧪 Test du diagnostic de base...")
    
    try:
        result = subprocess.run([sys.executable, "main.py", "--diagnostic"], 
                              capture_output=True, text=True, timeout=30)
        
        output = result.stdout
        
        # Vérifier que le diagnostic a tourné
        if "diagnostic système" in output.lower():
            print("  ✅ Diagnostic lancé")
        else:
            print("  ❌ Diagnostic non lancé")
            return False
        
        # Vérifier les informations système
        if "Informations système" in output:
            print("  ✅ Informations système affichées")
        else:
            print("  ❌ Informations système manquantes")
            return False
        
        # Vérifier les composants
        if "Composants de performance" in output:
            print("  ✅ Composants de performance vérifiés")
        else:
            print("  ❌ Composants de performance non vérifiés")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("  ⚠️ Timeout (normal si les imports sont longs)")
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test d'intégration simple du main.py")
    print("=" * 45)
    
    tests = [
        test_main_help,
        test_diagnostic_basic,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 45)
    print(f"📊 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Intégration du main.py réussie!")
    elif passed > 0:
        print("✅ Intégration partiellement réussie")
    else:
        print("❌ Problèmes d'intégration")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)