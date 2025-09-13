#!/usr/bin/env python3
"""
Lanceur de suite de tests complète pour l'application de doublage vidéo par IA
Exécute tous les types de tests et génère un rapport détaillé
"""

import unittest
import sys
import os
import time
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(__file__))

# Import des suites de tests
from tests.test_comprehensive_unit_suite import *
from tests.test_comprehensive_integration import *
from tests.test_synchronization_quality import *
from tests.test_audio_quality import *
from tests.test_performance_benchmarks import *


class ComprehensiveTestRunner:
    """Lanceur de tests complet avec rapports détaillés"""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_suite(self, suite_name: str, test_classes: List, verbose: bool = True) -> Dict:
        """Exécuter une suite de tests spécifique"""
        print(f"\n{'='*60}")
        print(f"EXÉCUTION DE LA SUITE: {suite_name}")
        print(f"{'='*60}")
        
        suite_start_time = time.time()
        suite_results = {
            'name': suite_name,
            'start_time': suite_start_time,
            'test_classes': [],
            'total_tests': 0,
            'total_failures': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'success_rate': 0.0,
            'duration': 0.0
        }
        
        for test_class in test_classes:
            print(f"\n{'-'*40}")
            print(f"Classe de test: {test_class.__name__}")
            print(f"{'-'*40}")
            
            try:
                # Créer la suite pour cette classe
                loader = unittest.TestLoader()
                class_suite = loader.loadTestsFromTestCase(test_class)
                
                # Exécuter les tests
                stream = sys.stdout if verbose else open(os.devnull, 'w')
                runner = unittest.TextTestRunner(
                    stream=stream,
                    verbosity=2 if verbose else 0,
                    buffer=True
                )
                
                class_result = runner.run(class_suite)
                
                # Collecter les résultats
                class_info = {
                    'class_name': test_class.__name__,
                    'tests_run': class_result.testsRun,
                    'failures': len(class_result.failures),
                    'errors': len(class_result.errors),
                    'skipped': len(class_result.skipped) if hasattr(class_result, 'skipped') else 0,
                    'success_rate': 0.0,
                    'failure_details': [],
                    'error_details': []
                }
                
                # Calculer le taux de succès
                if class_result.testsRun > 0:
                    successes = class_result.testsRun - len(class_result.failures) - len(class_result.errors)
                    class_info['success_rate'] = (successes / class_result.testsRun) * 100
                
                # Collecter les détails des échecs
                for test, traceback_str in class_result.failures:
                    class_info['failure_details'].append({
                        'test': str(test),
                        'traceback': traceback_str
                    })
                
                # Collecter les détails des erreurs
                for test, traceback_str in class_result.errors:
                    class_info['error_details'].append({
                        'test': str(test),
                        'traceback': traceback_str
                    })
                
                suite_results['test_classes'].append(class_info)
                suite_results['total_tests'] += class_result.testsRun
                suite_results['total_failures'] += len(class_result.failures)
                suite_results['total_errors'] += len(class_result.errors)
                suite_results['total_skipped'] += len(class_result.skipped) if hasattr(class_result, 'skipped') else 0
                
                # Afficher le résumé de la classe
                print(f"Tests: {class_result.testsRun}, "
                      f"Succès: {class_info['success_rate']:.1f}%, "
                      f"Échecs: {len(class_result.failures)}, "
                      f"Erreurs: {len(class_result.errors)}")
                
            except Exception as e:
                print(f"ERREUR lors de l'exécution de {test_class.__name__}: {e}")
                suite_results['test_classes'].append({
                    'class_name': test_class.__name__,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
        
        # Calculer les statistiques de la suite
        suite_end_time = time.time()
        suite_results['duration'] = suite_end_time - suite_start_time
        
        if suite_results['total_tests'] > 0:
            total_successes = (suite_results['total_tests'] - 
                             suite_results['total_failures'] - 
                             suite_results['total_errors'])
            suite_results['success_rate'] = (total_successes / suite_results['total_tests']) * 100
        
        return suite_results
    
    def run_all_tests(self, test_types: List[str] = None, verbose: bool = True) -> Dict:
        """Exécuter tous les tests ou types spécifiés"""
        self.start_time = time.time()
        
        # Définir les suites de tests disponibles
        available_suites = {
            'unit': {
                'name': 'Tests Unitaires',
                'classes': [
                    TestDataModelsUnit,
                    TestFileManagerUnit,
                    TestVideoProcessorUnit,
                    TestAudioProcessorUnit,
                    TestAIModelManagerUnit
                ]
            },
            'integration': {
                'name': 'Tests d\'Intégration',
                'classes': [
                    TestPipelineIntegration,
                    TestEndToEndScenarios
                ]
            },
            'synchronization': {
                'name': 'Tests de Synchronisation',
                'classes': [
                    TestSynchronizationAccuracy,
                    TestSynchronizationRobustness
                ]
            },
            'quality': {
                'name': 'Tests de Qualité Audio',
                'classes': [
                    AudioQualityTests
                ]
            },
            'performance': {
                'name': 'Tests de Performance',
                'classes': [
                    TestSmallFileBenchmarks,
                    TestMediumFileBenchmarks,
                    TestLargeFileBenchmarks,
                    TestConcurrencyBenchmarks
                ]
            }
        }
        
        # Déterminer quelles suites exécuter
        if test_types is None:
            suites_to_run = available_suites
        else:
            suites_to_run = {k: v for k, v in available_suites.items() if k in test_types}
        
        print(f"LANCEMENT DE LA SUITE DE TESTS COMPLÈTE")
        print(f"Suites à exécuter: {', '.join(suites_to_run.keys())}")
        print(f"Répertoire de sortie: {self.output_dir}")
        
        # Exécuter chaque suite
        for suite_key, suite_info in suites_to_run.items():
            try:
                suite_result = self.run_test_suite(
                    suite_info['name'],
                    suite_info['classes'],
                    verbose
                )
                self.results[suite_key] = suite_result
            except Exception as e:
                print(f"ERREUR CRITIQUE dans la suite {suite_key}: {e}")
                self.results[suite_key] = {
                    'name': suite_info['name'],
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
        
        self.end_time = time.time()
        return self.results
    
    def generate_report(self) -> str:
        """Générer un rapport détaillé des tests"""
        if not self.results:
            return "Aucun résultat de test disponible"
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Calculer les statistiques globales
        global_stats = {
            'total_tests': 0,
            'total_failures': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'total_success_rate': 0.0,
            'suites_run': len(self.results),
            'duration': total_duration
        }
        
        suite_success_rates = []
        
        for suite_result in self.results.values():
            if 'total_tests' in suite_result:
                global_stats['total_tests'] += suite_result['total_tests']
                global_stats['total_failures'] += suite_result['total_failures']
                global_stats['total_errors'] += suite_result['total_errors']
                global_stats['total_skipped'] += suite_result['total_skipped']
                suite_success_rates.append(suite_result['success_rate'])
        
        if global_stats['total_tests'] > 0:
            total_successes = (global_stats['total_tests'] - 
                             global_stats['total_failures'] - 
                             global_stats['total_errors'])
            global_stats['total_success_rate'] = (total_successes / global_stats['total_tests']) * 100
        
        # Générer le rapport texte
        report_lines = [
            "="*80,
            "RAPPORT DE TESTS COMPLET - APPLICATION DOUBLAGE VIDÉO IA",
            "="*80,
            f"Date d'exécution: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Durée totale: {total_duration:.2f} secondes",
            "",
            "STATISTIQUES GLOBALES:",
            f"  Tests exécutés: {global_stats['total_tests']}",
            f"  Succès: {global_stats['total_tests'] - global_stats['total_failures'] - global_stats['total_errors']}",
            f"  Échecs: {global_stats['total_failures']}",
            f"  Erreurs: {global_stats['total_errors']}",
            f"  Ignorés: {global_stats['total_skipped']}",
            f"  Taux de succès global: {global_stats['total_success_rate']:.1f}%",
            "",
            "RÉSULTATS PAR SUITE:",
            "-"*40
        ]
        
        # Détails par suite
        for suite_key, suite_result in self.results.items():
            if 'error' in suite_result:
                report_lines.extend([
                    f"❌ {suite_result['name']}: ERREUR CRITIQUE",
                    f"   Erreur: {suite_result['error']}",
                    ""
                ])
            else:
                status_icon = "✅" if suite_result['success_rate'] >= 90 else "⚠️" if suite_result['success_rate'] >= 70 else "❌"
                report_lines.extend([
                    f"{status_icon} {suite_result['name']}:",
                    f"   Tests: {suite_result['total_tests']}",
                    f"   Taux de succès: {suite_result['success_rate']:.1f}%",
                    f"   Durée: {suite_result['duration']:.2f}s",
                    ""
                ])
                
                # Détails des échecs si présents
                if suite_result['total_failures'] > 0 or suite_result['total_errors'] > 0:
                    report_lines.append("   PROBLÈMES DÉTECTÉS:")
                    
                    for class_info in suite_result['test_classes']:
                        if class_info.get('failures', 0) > 0 or class_info.get('errors', 0) > 0:
                            report_lines.append(f"     - {class_info['class_name']}: "
                                              f"{class_info.get('failures', 0)} échecs, "
                                              f"{class_info.get('errors', 0)} erreurs")
                    report_lines.append("")
        
        # Recommandations
        report_lines.extend([
            "RECOMMANDATIONS:",
            "-"*20
        ])
        
        if global_stats['total_success_rate'] >= 95:
            report_lines.append("✅ Excellente qualité de code - Tous les tests passent")
        elif global_stats['total_success_rate'] >= 85:
            report_lines.append("⚠️ Bonne qualité - Quelques améliorations possibles")
        elif global_stats['total_success_rate'] >= 70:
            report_lines.append("⚠️ Qualité acceptable - Corrections recommandées")
        else:
            report_lines.append("❌ Qualité insuffisante - Corrections urgentes nécessaires")
        
        if global_stats['total_failures'] > 0:
            report_lines.append(f"- Corriger {global_stats['total_failures']} échecs de tests")
        
        if global_stats['total_errors'] > 0:
            report_lines.append(f"- Résoudre {global_stats['total_errors']} erreurs de tests")
        
        report_lines.extend([
            "",
            "="*80
        ])
        
        return "\n".join(report_lines)
    
    def save_results(self):
        """Sauvegarder les résultats dans des fichiers"""
        # Sauvegarder les résultats JSON
        json_path = self.output_dir / "test_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Sauvegarder le rapport texte
        report_path = self.output_dir / "test_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        
        print(f"\nRésultats sauvegardés:")
        print(f"  JSON: {json_path}")
        print(f"  Rapport: {report_path}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Lanceur de tests complet pour l'application de doublage vidéo IA")
    parser.add_argument('--types', nargs='+', 
                       choices=['unit', 'integration', 'synchronization', 'quality', 'performance'],
                       help='Types de tests à exécuter (par défaut: tous)')
    parser.add_argument('--output', default='test_results',
                       help='Répertoire de sortie pour les résultats')
    parser.add_argument('--quiet', action='store_true',
                       help='Mode silencieux (moins de sortie)')
    parser.add_argument('--report-only', action='store_true',
                       help='Générer seulement le rapport à partir des résultats existants')
    
    args = parser.parse_args()
    
    # Créer le lanceur de tests
    runner = ComprehensiveTestRunner(args.output)
    
    if args.report_only:
        # Charger les résultats existants et générer le rapport
        json_path = Path(args.output) / "test_results.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                runner.results = json.load(f)
            print(runner.generate_report())
        else:
            print(f"Aucun fichier de résultats trouvé: {json_path}")
        return
    
    try:
        # Exécuter les tests
        results = runner.run_all_tests(
            test_types=args.types,
            verbose=not args.quiet
        )
        
        # Générer et afficher le rapport
        report = runner.generate_report()
        print(f"\n{report}")
        
        # Sauvegarder les résultats
        runner.save_results()
        
        # Code de sortie basé sur les résultats
        if any('error' in result for result in results.values()):
            sys.exit(2)  # Erreur critique
        
        total_failures = sum(result.get('total_failures', 0) for result in results.values())
        total_errors = sum(result.get('total_errors', 0) for result in results.values())
        
        if total_failures > 0 or total_errors > 0:
            sys.exit(1)  # Tests échoués
        
        sys.exit(0)  # Succès
        
    except KeyboardInterrupt:
        print("\n\nExécution interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\nERREUR CRITIQUE: {e}")
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()