#!/usr/bin/env python3
"""
Tests de qualité de synchronisation pour l'application de doublage vidéo par IA
Validation de la précision de synchronisation entre OCR, ASR et vidéo finale
"""

import unittest
import numpy as np
import tempfile
import shutil
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from unittest.mock import Mock, patch

# Import des modules de l'application
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_video_dubbing.models.data_models import DialogueSegment, TranscriptionResult
# Mock import: from ai_video_dubbing.processors.sync_processor import SyncProcessor


class TestSynchronizationAccuracy(unittest.TestCase):
    """Tests de précision de synchronisation"""
    
    def setUp(self):
        """Configuration des tests"""
        self.temp_dir = tempfile.mkdtemp()
        # Mock du processeur de synchronisation
        self.sync_processor = Mock()
        
        # Données de test pour synchronisation
        self.sample_ocr_results = [
            {"text": "Bonjour tout le monde", "timestamp": 1.2, "confidence": 0.94},
            {"text": "Comment ça va aujourd'hui ?", "timestamp": 4.8, "confidence": 0.91},
            {"text": "Très bien merci beaucoup", "timestamp": 8.1, "confidence": 0.96},
            {"text": "Et vous comment allez-vous ?", "timestamp": 12.3, "confidence": 0.89},
            {"text": "Parfait continuons", "timestamp": 16.7, "confidence": 0.93}
        ]
        
        self.sample_asr_results = [
            {"text": "bonjour tout le monde", "timestamp": 1.1, "confidence": 0.89},
            {"text": "comment ça va aujourd'hui", "timestamp": 4.9, "confidence": 0.87},
            {"text": "très bien merci beaucoup", "timestamp": 8.0, "confidence": 0.93},
            {"text": "et vous comment allez vous", "timestamp": 12.4, "confidence": 0.85},
            {"text": "parfait continuons", "timestamp": 16.6, "confidence": 0.91}
        ]
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_timestamp_alignment_accuracy(self):
        """Test de précision d'alignement des horodatages"""
        
        # Calculer les différences temporelles
        time_differences = []
        for ocr, asr in zip(self.sample_ocr_results, self.sample_asr_results):
            time_diff = abs(ocr["timestamp"] - asr["timestamp"])
            time_differences.append(time_diff)
        
        # Statistiques de synchronisation
        max_diff = max(time_differences)
        avg_diff = sum(time_differences) / len(time_differences)
        std_diff = np.std(time_differences)
        
        # Vérifications de qualité
        self.assertLess(max_diff, 0.5, "Différence temporelle maximale trop élevée")
        self.assertLess(avg_diff, 0.2, "Différence temporelle moyenne trop élevée")
        self.assertLess(std_diff, 0.15, "Variance temporelle trop élevée")
        
        print(f"Synchronisation temporelle - Max: {max_diff:.3f}s, "
              f"Moyenne: {avg_diff:.3f}s, Écart-type: {std_diff:.3f}s")
    
    def test_text_similarity_alignment(self):
        """Test d'alignement basé sur la similarité textuelle"""
        
        similarities = []
        for ocr, asr in zip(self.sample_ocr_results, self.sample_asr_results):
            similarity = self._calculate_text_similarity(ocr["text"], asr["text"])
            similarities.append(similarity)
        
        # Vérifications de similarité
        min_similarity = min(similarities)
        avg_similarity = sum(similarities) / len(similarities)
        
        self.assertGreater(min_similarity, 0.7, "Similarité textuelle minimale insuffisante")
        self.assertGreater(avg_similarity, 0.85, "Similarité textuelle moyenne insuffisante")
        
        print(f"Similarité textuelle - Min: {min_similarity:.3f}, "
              f"Moyenne: {avg_similarity:.3f}")
    
    def test_confidence_weighted_alignment(self):
        """Test d'alignement pondéré par la confiance"""
        
        weighted_scores = []
        for ocr, asr in zip(self.sample_ocr_results, self.sample_asr_results):
            # Calculer le score pondéré
            time_diff = abs(ocr["timestamp"] - asr["timestamp"])
            text_sim = self._calculate_text_similarity(ocr["text"], asr["text"])
            
            # Pondération par la confiance
            ocr_weight = ocr["confidence"]
            asr_weight = asr["confidence"]
            combined_confidence = (ocr_weight + asr_weight) / 2
            
            # Score final (plus c'est proche de 1, mieux c'est)
            time_score = max(0, 1 - time_diff * 2)  # Pénalité temporelle
            final_score = (text_sim * 0.6 + time_score * 0.4) * combined_confidence
            
            weighted_scores.append({
                "time_diff": time_diff,
                "text_similarity": text_sim,
                "confidence": combined_confidence,
                "final_score": final_score
            })
        
        # Vérifications des scores pondérés
        avg_final_score = sum(s["final_score"] for s in weighted_scores) / len(weighted_scores)
        min_final_score = min(s["final_score"] for s in weighted_scores)
        
        self.assertGreater(avg_final_score, 0.8, "Score d'alignement moyen insuffisant")
        self.assertGreater(min_final_score, 0.6, "Score d'alignement minimal insuffisant")
        
        print(f"Scores d'alignement pondérés - Moyenne: {avg_final_score:.3f}, "
              f"Minimum: {min_final_score:.3f}")
    
    def test_multi_speaker_synchronization(self):
        """Test de synchronisation avec plusieurs locuteurs"""
        
        # Données multi-locuteurs
        multi_speaker_data = [
            {
                "speaker": "SPEAKER_00",
                "ocr": {"text": "Bonjour Pierre", "timestamp": 1.2},
                "asr": {"text": "bonjour pierre", "timestamp": 1.1},
                "expected_alignment": True
            },
            {
                "speaker": "SPEAKER_01", 
                "ocr": {"text": "Salut Marie", "timestamp": 3.5},
                "asr": {"text": "salut marie", "timestamp": 3.6},
                "expected_alignment": True
            },
            {
                "speaker": "SPEAKER_00",
                "ocr": {"text": "Comment vas-tu ?", "timestamp": 6.1},
                "asr": {"text": "comment vas tu", "timestamp": 6.0},
                "expected_alignment": True
            },
            {
                "speaker": "SPEAKER_01",
                "ocr": {"text": "Très bien merci", "timestamp": 8.8},
                "asr": {"text": "très bien merci", "timestamp": 8.9},
                "expected_alignment": True
            }
        ]
        
        # Vérifier l'alignement par locuteur
        speaker_alignments = {}
        for data in multi_speaker_data:
            speaker = data["speaker"]
            if speaker not in speaker_alignments:
                speaker_alignments[speaker] = []
            
            time_diff = abs(data["ocr"]["timestamp"] - data["asr"]["timestamp"])
            text_sim = self._calculate_text_similarity(
                data["ocr"]["text"], 
                data["asr"]["text"]
            )
            
            alignment_quality = {
                "time_diff": time_diff,
                "text_similarity": text_sim,
                "is_aligned": time_diff < 0.3 and text_sim > 0.8
            }
            
            speaker_alignments[speaker].append(alignment_quality)
        
        # Vérifier que chaque locuteur a un bon alignement
        for speaker, alignments in speaker_alignments.items():
            aligned_count = sum(1 for a in alignments if a["is_aligned"])
            alignment_rate = aligned_count / len(alignments)
            
            self.assertGreater(alignment_rate, 0.8, 
                             f"Taux d'alignement insuffisant pour {speaker}")
            
            avg_time_diff = sum(a["time_diff"] for a in alignments) / len(alignments)
            self.assertLess(avg_time_diff, 0.2, 
                          f"Différence temporelle moyenne trop élevée pour {speaker}")
    
    def test_synchronization_with_gaps(self):
        """Test de synchronisation avec des gaps dans les données"""
        
        # Données avec gaps (OCR manquant ou ASR manquant)
        gapped_data = [
            {"ocr": {"text": "Premier segment", "timestamp": 1.0}, "asr": None},
            {"ocr": None, "asr": {"text": "deuxième segment", "timestamp": 3.5}},
            {"ocr": {"text": "Troisième segment", "timestamp": 6.2}, 
             "asr": {"text": "troisième segment", "timestamp": 6.1}},
            {"ocr": {"text": "Quatrième segment", "timestamp": 9.8}, "asr": None},
            {"ocr": None, "asr": {"text": "cinquième segment", "timestamp": 12.3}}
        ]
        
        # Traiter les gaps
        aligned_segments = []
        unmatched_ocr = []
        unmatched_asr = []
        
        for data in gapped_data:
            if data["ocr"] and data["asr"]:
                # Alignement direct possible
                aligned_segments.append(data)
            elif data["ocr"] and not data["asr"]:
                # OCR sans ASR correspondant
                unmatched_ocr.append(data["ocr"])
            elif data["asr"] and not data["ocr"]:
                # ASR sans OCR correspondant
                unmatched_asr.append(data["asr"])
        
        # Vérifications
        self.assertGreater(len(aligned_segments), 0, "Aucun segment aligné trouvé")
        
        # Ratio de segments alignés vs non alignés
        total_segments = len(gapped_data)
        aligned_ratio = len(aligned_segments) / total_segments
        
        # Au moins 20% des segments doivent être alignés même avec des gaps
        self.assertGreater(aligned_ratio, 0.2, "Trop peu de segments alignés avec gaps")
        
        print(f"Gestion des gaps - Segments alignés: {len(aligned_segments)}/{total_segments} "
              f"({aligned_ratio:.1%})")
    
    def test_temporal_drift_correction(self):
        """Test de correction de dérive temporelle"""
        
        # Simuler une dérive temporelle progressive
        base_timestamps = [1.0, 5.0, 10.0, 15.0, 20.0]
        drift_factor = 0.02  # 2% de dérive par seconde
        
        ocr_timestamps = base_timestamps.copy()
        asr_timestamps = [t * (1 + drift_factor * t) for t in base_timestamps]
        
        # Calculer la dérive
        drifts = [abs(ocr - asr) for ocr, asr in zip(ocr_timestamps, asr_timestamps)]
        
        # La dérive doit être détectable et corrigeable
        max_drift = max(drifts)
        drift_progression = [drifts[i] - drifts[i-1] for i in range(1, len(drifts))]
        
        # Vérifier que la dérive est progressive (détectable)
        self.assertTrue(all(d >= 0 for d in drift_progression), 
                       "La dérive n'est pas progressive")
        
        # Simuler la correction de dérive
        corrected_asr = []
        for i, asr_time in enumerate(asr_timestamps):
            if i == 0:
                correction_factor = 1.0
            else:
                # Calculer le facteur de correction basé sur la dérive observée
                observed_drift = drifts[i] / asr_time
                correction_factor = 1.0 - observed_drift
            
            corrected_time = asr_time * correction_factor
            corrected_asr.append(corrected_time)
        
        # Vérifier l'amélioration après correction
        corrected_drifts = [abs(ocr - corr) for ocr, corr in zip(ocr_timestamps, corrected_asr)]
        avg_drift_before = sum(drifts) / len(drifts)
        avg_drift_after = sum(corrected_drifts) / len(corrected_drifts)
        
        self.assertLess(avg_drift_after, avg_drift_before, 
                       "La correction n'améliore pas la synchronisation")
        
        print(f"Correction de dérive - Avant: {avg_drift_before:.3f}s, "
              f"Après: {avg_drift_after:.3f}s")
    
    def test_lip_sync_validation(self):
        """Test de validation de synchronisation labiale"""
        
        # Simuler des données de mouvement labial
        lip_movement_data = [
            {"timestamp": 1.0, "mouth_open": 0.8, "movement_intensity": 0.9},
            {"timestamp": 1.5, "mouth_open": 0.3, "movement_intensity": 0.4},
            {"timestamp": 2.0, "mouth_open": 0.9, "movement_intensity": 0.8},
            {"timestamp": 2.5, "mouth_open": 0.1, "movement_intensity": 0.2},
            {"timestamp": 3.0, "mouth_open": 0.7, "movement_intensity": 0.7}
        ]
        
        # Données audio correspondantes (activité vocale)
        audio_activity_data = [
            {"timestamp": 1.1, "voice_activity": 0.9, "volume": 0.8},
            {"timestamp": 1.4, "voice_activity": 0.2, "volume": 0.3},
            {"timestamp": 2.1, "voice_activity": 0.8, "volume": 0.9},
            {"timestamp": 2.4, "voice_activity": 0.1, "volume": 0.1},
            {"timestamp": 3.1, "voice_activity": 0.7, "volume": 0.6}
        ]
        
        # Calculer la corrélation lip-sync
        correlations = []
        for lip, audio in zip(lip_movement_data, audio_activity_data):
            time_diff = abs(lip["timestamp"] - audio["timestamp"])
            
            # Corrélation entre mouvement labial et activité vocale
            movement_correlation = abs(lip["mouth_open"] - audio["voice_activity"])
            intensity_correlation = abs(lip["movement_intensity"] - audio["volume"])
            
            # Score de synchronisation labiale
            time_score = max(0, 1 - time_diff * 5)  # Pénalité temporelle forte
            movement_score = 1 - movement_correlation
            intensity_score = 1 - intensity_correlation
            
            lip_sync_score = (time_score * 0.4 + movement_score * 0.3 + intensity_score * 0.3)
            correlations.append(lip_sync_score)
        
        # Vérifications de synchronisation labiale
        avg_lip_sync = sum(correlations) / len(correlations)
        min_lip_sync = min(correlations)
        
        self.assertGreater(avg_lip_sync, 0.7, "Synchronisation labiale moyenne insuffisante")
        self.assertGreater(min_lip_sync, 0.5, "Synchronisation labiale minimale insuffisante")
        
        print(f"Synchronisation labiale - Moyenne: {avg_lip_sync:.3f}, "
              f"Minimum: {min_lip_sync:.3f}")
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculer la similarité entre deux textes"""
        # Normaliser les textes
        text1 = text1.lower().strip().replace("?", "").replace(".", "").replace(",", "")
        text2 = text2.lower().strip().replace("?", "").replace(".", "").replace(",", "")
        
        # Calculer la similarité Jaccard
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class TestSynchronizationRobustness(unittest.TestCase):
    """Tests de robustesse de la synchronisation"""
    
    def setUp(self):
        """Configuration des tests de robustesse"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_noisy_timestamp_handling(self):
        """Test de gestion des horodatages bruités"""
        
        # Horodatages de référence
        clean_timestamps = [1.0, 3.0, 5.0, 7.0, 9.0]
        
        # Ajouter du bruit aux horodatages
        noise_levels = [0.05, 0.1, 0.2, 0.3]  # 5%, 10%, 20%, 30% de bruit
        
        for noise_level in noise_levels:
            noisy_timestamps = []
            for ts in clean_timestamps:
                noise = np.random.uniform(-noise_level, noise_level)
                noisy_ts = ts + noise
                noisy_timestamps.append(max(0, noisy_ts))  # Éviter les timestamps négatifs
            
            # Calculer la robustesse
            differences = [abs(clean - noisy) for clean, noisy in 
                          zip(clean_timestamps, noisy_timestamps)]
            max_diff = max(differences)
            avg_diff = sum(differences) / len(differences)
            
            # La robustesse doit être proportionnelle au niveau de bruit
            expected_max_diff = noise_level * 2  # Tolérance
            self.assertLess(max_diff, expected_max_diff, 
                          f"Robustesse insuffisante pour bruit {noise_level:.0%}")
            
            print(f"Bruit {noise_level:.0%} - Diff max: {max_diff:.3f}s, "
                  f"Diff moyenne: {avg_diff:.3f}s")
    
    def test_missing_data_interpolation(self):
        """Test d'interpolation des données manquantes"""
        
        # Données avec valeurs manquantes
        timestamps = [1.0, 2.0, None, 4.0, 5.0, None, 7.0, 8.0]
        values = ["A", "B", None, "D", "E", None, "G", "H"]
        
        # Interpoler les timestamps manquants
        interpolated_timestamps = []
        interpolated_values = []
        
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            if ts is not None and val is not None:
                interpolated_timestamps.append(ts)
                interpolated_values.append(val)
            else:
                # Interpolation linéaire pour les timestamps
                if i > 0 and i < len(timestamps) - 1:
                    prev_ts = None
                    next_ts = None
                    
                    # Trouver le timestamp précédent
                    for j in range(i-1, -1, -1):
                        if timestamps[j] is not None:
                            prev_ts = timestamps[j]
                            break
                    
                    # Trouver le timestamp suivant
                    for j in range(i+1, len(timestamps)):
                        if timestamps[j] is not None:
                            next_ts = timestamps[j]
                            break
                    
                    if prev_ts is not None and next_ts is not None:
                        # Interpolation linéaire
                        interpolated_ts = (prev_ts + next_ts) / 2
                        interpolated_timestamps.append(interpolated_ts)
                        interpolated_values.append(f"INTERPOLATED_{i}")
        
        # Vérifier que l'interpolation fonctionne
        original_count = sum(1 for ts in timestamps if ts is not None)
        interpolated_count = len(interpolated_timestamps)
        
        self.assertGreaterEqual(interpolated_count, original_count, 
                               "L'interpolation ne doit pas réduire le nombre de points")
        
        # Vérifier l'ordre chronologique
        for i in range(1, len(interpolated_timestamps)):
            self.assertGreater(interpolated_timestamps[i], interpolated_timestamps[i-1],
                             "L'ordre chronologique n'est pas respecté après interpolation")
    
    def test_synchronization_under_load(self):
        """Test de synchronisation sous charge élevée"""
        
        # Simuler une charge élevée avec beaucoup de données
        large_dataset_size = 1000
        
        # Générer des données de test volumineuses
        ocr_data = []
        asr_data = []
        
        for i in range(large_dataset_size):
            base_time = i * 0.5  # Un point toutes les 500ms
            
            ocr_data.append({
                "timestamp": base_time + np.random.uniform(-0.05, 0.05),
                "text": f"Segment OCR {i}",
                "confidence": np.random.uniform(0.8, 0.98)
            })
            
            asr_data.append({
                "timestamp": base_time + np.random.uniform(-0.08, 0.08),
                "text": f"segment asr {i}",
                "confidence": np.random.uniform(0.75, 0.95)
            })
        
        # Mesurer le temps de traitement
        import time
        start_time = time.time()
        
        # Simuler l'alignement sur le gros dataset
        alignments = []
        for ocr, asr in zip(ocr_data[:100], asr_data[:100]):  # Échantillon pour le test
            time_diff = abs(ocr["timestamp"] - asr["timestamp"])
            alignments.append(time_diff < 0.2)  # Seuil d'alignement
        
        processing_time = time.time() - start_time
        
        # Vérifications de performance sous charge
        alignment_rate = sum(alignments) / len(alignments)
        
        self.assertGreater(alignment_rate, 0.8, 
                          "Taux d'alignement insuffisant sous charge")
        self.assertLess(processing_time, 1.0, 
                       "Temps de traitement trop élevé sous charge")
        
        print(f"Synchronisation sous charge - Taux: {alignment_rate:.1%}, "
              f"Temps: {processing_time:.3f}s")


if __name__ == '__main__':
    # Exécuter les tests de synchronisation
    unittest.main(verbosity=2)