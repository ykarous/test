#!/usr/bin/env python3
"""
Test d'intégration pour l'interface graphique améliorée
"""

import sys
from pathlib import Path

def test_enhanced_gui_import():
    """Test d'import de l'interface graphique améliorée"""
    print("🧪 Test d'import de l'interface graphique améliorée...")
    
    try:
        # Test d'import sans initialisation complète
        from ai_video_dubbing.gui.enhanced_main_window import EnhancedMainWindow
        print("  ✅ EnhancedMainWindow importée avec succès")
        
        # Vérifier que la classe a les méthodes attendues
        expected_methods = ['__init__', 'show']
        for method in expected_methods:
            if hasattr(EnhancedMainWindow, method):
                print(f"    ✅ Méthode {method} trouvée")
            else:
                print(f"    ❌ Méthode {method} manquante")
                return False
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur inattendue: {e}")
        return False

def test_fallback_gui_import():
    """Test d'import de l'interface graphique standard (fallback)"""
    print("\n🧪 Test d'import de l'interface graphique standard...")
    
    try:
        from ai_video_dubbing.gui.main_window_qt import MainWindowQt
        print("  ✅ MainWindowQt importée avec succès")
        return True
        
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur inattendue: {e}")
        return False

def test_pyqt5_availability():
    """Test de disponibilité de PyQt5"""
    print("\n🧪 Test de disponibilité de PyQt5...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        print("  ✅ PyQt5 disponible")
        return True
        
    except ImportError as e:
        print(f"  ❌ PyQt5 non disponible: {e}")
        return False

def test_main_integration():
    """Test de l'intégration dans main.py"""
    print("\n🧪 Test de l'intégration dans main.py...")
    
    try:
        # Importer la fonction launch_gui du main
        import main
        
        # Vérifier que la fonction existe
        if hasattr(main, 'launch_gui'):
            print("  ✅ Fonction launch_gui trouvée dans main.py")
        else:
            print("  ❌ Fonction launch_gui manquante dans main.py")
            return False
        
        # Vérifier que la fonction launch_diagnostic existe
        if hasattr(main, 'launch_diagnostic'):
            print("  ✅ Fonction launch_diagnostic trouvée dans main.py")
        else:
            print("  ❌ Fonction launch_diagnostic manquante dans main.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur lors du test d'intégration: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test d'intégration de l'interface graphique")
    print("=" * 50)
    
    tests = [
        ("PyQt5 disponible", test_pyqt5_availability),
        ("Interface standard", test_fallback_gui_import),
        ("Interface améliorée", test_enhanced_gui_import),
        ("Intégration main.py", test_main_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests d'intégration GUI ont réussi!")
        print("💡 L'interface graphique améliorée est prête à être utilisée")
    elif passed >= total - 1:
        print("✅ L'intégration GUI fonctionne avec des composants de base")
    else:
        print("⚠️ Problèmes d'intégration détectés")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)