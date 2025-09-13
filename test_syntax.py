"""
Test de syntaxe du fichier progress_interface.py
"""
import ast

try:
    with open('ai_video_dubbing/performance/progress_interface.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Taille du fichier: {len(content)} caractères")
    print(f"Nombre de lignes: {len(content.splitlines())}")
    
    # Vérifier la syntaxe
    ast.parse(content)
    print("✅ Syntaxe correcte")
    
    # Vérifier si RealTimeProgressInterface est présent
    if 'class RealTimeProgressInterface' in content:
        print("✅ Classe RealTimeProgressInterface trouvée dans le contenu")
    else:
        print("❌ Classe RealTimeProgressInterface non trouvée dans le contenu")
    
    # Afficher les dernières lignes
    lines = content.splitlines()
    print("\nDernières lignes du fichier:")
    for i, line in enumerate(lines[-10:], len(lines)-9):
        print(f"{i:3d}: {line}")
        
except SyntaxError as e:
    print(f"❌ Erreur de syntaxe: {e}")
    print(f"Ligne {e.lineno}: {e.text}")
except Exception as e:
    print(f"❌ Erreur: {e}")