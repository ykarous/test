#!/usr/bin/env python3
"""
Processeur de synchronisation temporelle pour l'application de doublage vidéo par IA.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..models.data_models import (
    TranscriptionResult, TranscriptionSegment, OCRResult, 
    DialogueSegment, SpeakerSegments, ProcessingError, ValidationError
)


@dataclass
class SyncResult:
    """Résultat de synchronisation temporelle."""
    synchronized_segments: List[DialogueSegment]
    confidence_score: float
    alignment_method: str
    processing_time: float
    sync_statistics: Dict[str, Any]


@dataclass
class AlignmentPoint:
    """Point d'alignement entre ASR et OCR."""
    asr_time: float
    ocr_time: float
    text_similarity: float
    confidence: float
    asr_segment_id: int
    ocr_segment_id: int


class SyncProcessor:
    """Processeur de synchronisation temporelle entre ASR et OCR."""
    
    def __init__(self, temp_storage=None):
        """
        Initialise le processeur de synchronisation.
        
        Args:
            temp_storage: Gestionnaire de stockage temporaire
        """
        self.temp_storage = temp_storage
        self.logger = logging.getLogger(__name__)
    
    def synchronize_asr_ocr(
        self,
        asr_result: TranscriptionResult,
        ocr_results: List[OCRResult],
        method: str = "nearest_neighbor",
        similarity_threshold: float = 0.3,
        time_tolerance: float = 2.0
    ) -> SyncResult:
        """
        Synchronise les résultats ASR et OCR.
        
        Args:
            asr_result: Résultats de transcription ASR
            ocr_results: Résultats d'extraction OCR
            method: Méthode de synchronisation
            similarity_threshold: Seuil de similarité textuelle
            time_tolerance: Tolérance temporelle en secondes
            
        Returns:
            Résultats de synchronisation
            
        Raises:
            ProcessingError: Si la synchronisation échoue
        """
        if not asr_result.segments:
            raise ValidationError("ASR result has no segments")
        
        if not ocr_results:
            self.logger.warning("No OCR results provided, using ASR only")
            return self._create_asr_only_result(asr_result)
        
        try:
            import time
            start_time = time.time()
            
            self.logger.info(f"Starting synchronization with {method}")
            self.logger.info(f"ASR segments: {len(asr_result.segments)}, OCR results: {len(ocr_results)}")
            
            # Choisir la méthode de synchronisation
            if method == "nearest_neighbor":
                sync_result = self._sync_with_nearest_neighbor(
                    asr_result, ocr_results, similarity_threshold, time_tolerance
                )
            else:
                raise ProcessingError(f"Unknown synchronization method: {method}")
            
            processing_time = time.time() - start_time
            
            # Calculer les statistiques
            stats = self._calculate_sync_statistics(
                sync_result.synchronized_segments, asr_result, ocr_results
            )
            
            final_result = SyncResult(
                synchronized_segments=sync_result.synchronized_segments,
                confidence_score=sync_result.confidence_score,
                alignment_method=method,
                processing_time=processing_time,
                sync_statistics=stats
            )
            
            self.logger.info(
                f"Synchronization completed in {processing_time:.2f}s "
                f"(confidence: {final_result.confidence_score:.3f})"
            )
            
            return final_result
            
        except Exception as e:
            raise ProcessingError(f"Synchronization failed: {e}")
    
    def _sync_with_nearest_neighbor(
        self,
        asr_result: TranscriptionResult,
        ocr_results: List[OCRResult],
        similarity_threshold: float,
        time_tolerance: float
    ) -> SyncResult:
        """
        Synchronisation par plus proche voisin.
        
        Args:
            asr_result: Résultats ASR
            ocr_results: Résultats OCR
            similarity_threshold: Seuil de similarité
            time_tolerance: Tolérance temporelle
            
        Returns:
            Résultats de synchronisation
        """
        synchronized_segments = []
        total_confidence = 0.0
        matched_segments = 0
        
        for asr_segment in asr_result.segments:
            best_match = None
            best_similarity = 0.0
            best_time_diff = float('inf')
            
            # Chercher le meilleur match OCR
            for ocr_result in ocr_results:
                # Calculer la similarité textuelle
                text_similarity = self._calculate_text_similarity(
                    asr_segment.text, ocr_result.text
                )
                
                # Calculer la différence temporelle
                time_diff = abs(asr_segment.start - ocr_result.timestamp)
                
                # Vérifier les critères
                if (text_similarity >= similarity_threshold and 
                    time_diff <= time_tolerance and
                    text_similarity > best_similarity):
                    
                    best_match = ocr_result
                    best_similarity = text_similarity
                    best_time_diff = time_diff
            
            # Créer le segment synchronisé
            if best_match:
                # Utiliser les timestamps OCR si disponibles (plus précis visuellement)
                sync_segment = DialogueSegment(
                    speaker_id="unknown",
                    start_time=best_match.timestamp,
                    end_time=best_match.timestamp + (asr_segment.end - asr_segment.start),
                    original_text=asr_segment.text,
                    audio_path="",
                    confidence_score=best_similarity
                )
                total_confidence += best_similarity
                matched_segments += 1
            else:
                # Utiliser les timestamps ASR si pas de match OCR
                sync_segment = DialogueSegment(
                    speaker_id="unknown",
                    start_time=asr_segment.start,
                    end_time=asr_segment.end,
                    original_text=asr_segment.text,
                    audio_path="",
                    confidence_score=asr_segment.confidence
                )
                total_confidence += asr_segment.confidence
            
            synchronized_segments.append(sync_segment)
        
        # Calculer la confiance moyenne
        avg_confidence = total_confidence / len(synchronized_segments) if synchronized_segments else 0.0
        
        return SyncResult(
            synchronized_segments=synchronized_segments,
            confidence_score=avg_confidence,
            alignment_method="nearest_neighbor",
            processing_time=0.0,
            sync_statistics={"matched_segments": matched_segments}
        )
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes.
        
        Args:
            text1: Premier texte
            text2: Deuxième texte
            
        Returns:
            Score de similarité (0.0 à 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normaliser les textes
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Similarité de Jaccard sur les mots
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _create_asr_only_result(self, asr_result: TranscriptionResult) -> SyncResult:
        """
        Crée un résultat de synchronisation basé uniquement sur l'ASR.
        
        Args:
            asr_result: Résultats ASR
            
        Returns:
            Résultat de synchronisation
        """
        synchronized_segments = []
        
        for segment in asr_result.segments:
            sync_segment = DialogueSegment(
                speaker_id="unknown",
                start_time=segment.start,
                end_time=segment.end,
                original_text=segment.text,
                audio_path="",
                confidence_score=segment.confidence
            )
            synchronized_segments.append(sync_segment)
        
        return SyncResult(
            synchronized_segments=synchronized_segments,
            confidence_score=asr_result.confidence,
            alignment_method="asr_only",
            processing_time=0.0,
            sync_statistics={"method": "asr_only", "segments": len(synchronized_segments)}
        )
    
    def _calculate_sync_statistics(
        self,
        synchronized_segments: List[DialogueSegment],
        asr_result: TranscriptionResult,
        ocr_results: List[OCRResult]
    ) -> Dict[str, Any]:
        """
        Calcule les statistiques de synchronisation.
        
        Args:
            synchronized_segments: Segments synchronisés
            asr_result: Résultats ASR originaux
            ocr_results: Résultats OCR originaux
            
        Returns:
            Dictionnaire des statistiques
        """
        stats = {
            "total_segments": len(synchronized_segments),
            "asr_segments": len(asr_result.segments),
            "ocr_results": len(ocr_results),
            "average_confidence": 0.0,
            "total_duration": 0.0,
            "sync_coverage": 0.0
        }
        
        if synchronized_segments:
            # Confiance moyenne
            stats["average_confidence"] = sum(
                seg.confidence_score for seg in synchronized_segments
            ) / len(synchronized_segments)
            
            # Durée totale
            stats["total_duration"] = sum(
                seg.end_time - seg.start_time for seg in synchronized_segments
            )
            
            # Couverture de synchronisation
            asr_duration = sum(
                seg.end - seg.start for seg in asr_result.segments
            )
            stats["sync_coverage"] = stats["total_duration"] / asr_duration if asr_duration > 0 else 0.0
        
        return stats
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """
        Convertit les secondes au format temps SRT.
        
        Args:
            seconds: Temps en secondes
            
        Returns:
            Temps au format SRT (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """
        Convertit les secondes au format temps WebVTT.
        
        Args:
            seconds: Temps en secondes
            
        Returns:
            Temps au format WebVTT (HH:MM:SS.mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"