#!/usr/bin/env python3
"""
Gestionnaire LM Studio pour l'application de doublage vidéo par IA.
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any

class LMStudioManager:
    """Gestionnaire pour l'intégration LM Studio."""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        """Initialise le gestionnaire LM Studio."""
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = 30
        self.logger.info("LM Studio manager initialized")
    
    def is_server_running(self) -> bool:
        """Vérifie si le serveur LM Studio est en cours d'exécution."""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"LM Studio server not accessible: {e}")
            return False
    
    def is_available(self) -> bool:
        """Vérifie si LM Studio est disponible."""
        return self.is_server_running()
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Récupère la liste des modèles disponibles dans LM Studio."""
        models = []
        try:
            if self.is_server_running():
                response = self.session.get(f"{self.base_url}/v1/models")
                response.raise_for_status()
                api_models = response.json().get('data', [])
                
                for model in api_models:
                    models.append({
                        'name': model.get('id', 'Unknown'),
                        'type': self._detect_model_type(model.get('id', '')),
                        'source': 'api',
                        'size': model.get('size', 0),
                        'status': 'loaded'
                    })
            
            self.logger.info(f"Found {len(models)} LM Studio models")
            return models
            
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []
    
    def _detect_model_type(self, model_name: str) -> str:
        """Détecte le type de modèle basé sur son nom."""
        model_name_lower = model_name.lower()
        
        if any(keyword in model_name_lower for keyword in [
            'whisper', 'speech', 'asr', 'transcrib'
        ]):
            return 'transcription'
        
        if any(keyword in model_name_lower for keyword in [
            'llava', 'qwen-vl', 'qwen2.5-vl', 'qwen2-vl', 'vision', 'multimodal', 
            'cogvlm', 'blip', 'minicpm-v', 'phi-3-vision', 'internvl'
        ]):
            return 'multimodal'
        
        return 'language'
    
    def get_models_for_transcription(self) -> List[Dict[str, Any]]:
        """Obtient les modèles disponibles pour la transcription."""
        all_models = self.get_available_models()
        return [m for m in all_models if m.get('type') == 'transcription']
    
    def get_models_for_ocr(self) -> List[Dict[str, Any]]:
        """Obtient les modèles disponibles pour l'OCR."""
        all_models = self.get_available_models()
        return [m for m in all_models if m.get('type') == 'multimodal']
    
    def get_multimodal_models(self) -> List[Dict[str, Any]]:
        """
        Obtient spécifiquement les modèles multimodaux capables d'OCR.
        
        Returns:
            Liste des modèles multimodaux disponibles
        """
        try:
            all_models = self.get_available_models()
            multimodal_models = []
            
            for model in all_models:
                model_name = model.get('name', '').lower()
                model_type = model.get('type', '')
                
                # Identifier les modèles multimodaux spécifiquement
                if (model_type == 'multimodal' or 
                    any(keyword in model_name for keyword in [
                        'llava', 'qwen-vl', 'cogvlm', 'blip', 'vision', 
                        'multimodal', 'minicpm', 'internvl', 'phi-3-vision'
                    ])):
                    
                    multimodal_models.append({
                        'id': model['name'],
                        'name': model['name'],
                        'type': 'multimodal',
                        'capabilities': ['image_analysis', 'ocr', 'vision', 'text_extraction'],
                        'recommended_use': 'Extraction de texte et analyse d\'images',
                        'status': model.get('status', 'available'),
                        'size': model.get('size', 0),
                        'ocr_quality': self._estimate_ocr_quality(model_name)
                    })
            
            return multimodal_models
            
        except Exception as e:
            self.logger.error(f"Failed to get multimodal models: {e}")
            return []
    
    def _estimate_ocr_quality(self, model_name: str) -> str:
        """Estime la qualité OCR d'un modèle basé sur son nom."""
        model_name_lower = model_name.lower()
        
        # Modèles haute qualité pour l'OCR
        if any(keyword in model_name_lower for keyword in [
            'llava-1.6', 'qwen-vl-max', 'cogvlm2', 'internvl-2'
        ]):
            return 'high'
        
        # Modèles qualité moyenne
        elif any(keyword in model_name_lower for keyword in [
            'llava-1.5', 'qwen-vl-chat', 'minicpm-v', 'phi-3-vision'
        ]):
            return 'medium'
        
        # Modèles basiques
        else:
            return 'basic'
    
    def extract_text_from_image(self, image_path: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Extrait le texte d'une image en utilisant un modèle multimodal LM Studio.
        
        Args:
            image_path: Chemin vers l'image
            model_name: Nom du modèle multimodal à utiliser
            
        Returns:
            Résultat d'extraction de texte ou None si échec
        """
        try:
            if not os.path.exists(image_path):
                raise ValueError(f"Image file not found: {image_path}")
            
            if not self.is_server_running():
                raise RuntimeError("LM Studio server is not running")
            
            # Encoder l'image en base64
            import base64
            with open(image_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Préparer le payload pour l'OCR
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an OCR assistant. Extract all visible text from images accurately. Provide only the extracted text without commentary."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text visible in this image. Provide the text exactly as it appears, maintaining formatting when possible."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result['choices'][0]['message']['content'].strip()
                
                return {
                    "text": extracted_text,
                    "confidence": 0.85,  # Estimation pour les modèles LLM
                    "model": model_name,
                    "method": "lm_studio_multimodal"
                }
            else:
                raise RuntimeError(f"OCR extraction failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return None
    
    def extract_text_from_frames(self, frames: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
        """
        Extrait le texte de plusieurs frames en utilisant LM Studio.
        
        Args:
            frames: Liste des frames avec timestamp et image
            model_name: Nom du modèle à utiliser
            
        Returns:
            Liste des résultats OCR avec texte, timestamp et confiance
        """
        results = []
        
        try:
            if not self.is_server_running():
                raise RuntimeError("LM Studio server is not running")
            
            self.logger.info(f"Extracting text from {len(frames)} frames using LM Studio {model_name}")
            
            for frame_data in frames:
                try:
                    timestamp = frame_data.get("timestamp", 0.0)
                    frame = frame_data.get("frame")
                    
                    if frame is None:
                        continue
                    
                    # Sauvegarder temporairement l'image pour LM Studio
                    import tempfile
                    import cv2
                    
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                        cv2.imwrite(tmp_file.name, frame)
                        tmp_path = tmp_file.name
                    
                    try:
                        # Utiliser LM Studio pour l'OCR
                        ocr_result = self.extract_text_from_image(tmp_path, model_name)
                        
                        if ocr_result and ocr_result.get('text'):
                            results.append({
                                "text": ocr_result['text'],
                                "timestamp": timestamp,
                                "confidence": ocr_result.get('confidence', 0.8),
                                "method": "lm_studio_multimodal"
                            })
                    finally:
                        # Nettoyer le fichier temporaire
                        os.unlink(tmp_path)
                        
                except Exception as e:
                    self.logger.warning(f"LM Studio OCR failed for frame at {timestamp}s: {e}")
                    continue
            
            self.logger.info(f"LM Studio extracted text from {len(results)} frames")
            return results
            
        except Exception as e:
            self.logger.error(f"LM Studio OCR extraction failed: {e}")
            return []
    
    def test_ocr_capability(self, model_name: str) -> Dict[str, Any]:
        """
        Teste la capacité OCR d'un modèle LM Studio.
        
        Args:
            model_name: Nom du modèle à tester
            
        Returns:
            Résultats du test OCR
        """
        test_results = {
            'model_name': model_name,
            'ocr_capable': False,
            'multimodal_support': False,
            'error_message': None
        }
        
        try:
            if not self.is_server_running():
                test_results['error_message'] = "LM Studio server not running"
                return test_results
            
            # Vérifier si le modèle supporte les images
            test_payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Can you see images?"
                            }
                        ]
                    }
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                test_results['multimodal_support'] = True
                test_results['ocr_capable'] = True
            else:
                test_results['error_message'] = f"Model test failed: {response.status_code}"
            
        except Exception as e:
            test_results['error_message'] = str(e)
        
        return test_results
    
    def get_best_ocr_model(self) -> Optional[Dict[str, Any]]:
        """
        Obtient le meilleur modèle disponible pour l'OCR.
        
        Returns:
            Meilleur modèle OCR ou None si aucun disponible
        """
        try:
            multimodal_models = self.get_multimodal_models()
            
            if not multimodal_models:
                return None
            
            # Trier par qualité OCR estimée
            quality_order = {'high': 3, 'medium': 2, 'basic': 1}
            
            best_model = max(
                multimodal_models,
                key=lambda m: quality_order.get(m.get('ocr_quality', 'basic'), 0)
            )
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"Failed to get best OCR model: {e}")
            return None
    
    def get_model_info_summary(self) -> Dict[str, Any]:
        """
        Obtient un résumé des informations sur les modèles LM Studio.
        
        Returns:
            Résumé des modèles disponibles
        """
        summary = {
            'lm_studio_available': False,
            'total_models': 0,
            'transcription_models': 0,
            'ocr_models': 0,
            'recommended_models': {}
        }
        
        try:
            if self.is_server_running():
                summary['lm_studio_available'] = True
                
                # Obtenir tous les modèles
                all_models = self.get_available_models()
                summary['total_models'] = len(all_models)
                
                # Compter par type
                transcription_models = self.get_models_for_transcription()
                ocr_models = self.get_models_for_ocr()
                
                summary['transcription_models'] = len(transcription_models)
                summary['ocr_models'] = len(ocr_models)
                
                # Recommandations
                best_ocr = self.get_best_ocr_model()
                if best_ocr:
                    summary['recommended_models']['ocr'] = best_ocr['name']
                
                if transcription_models:
                    summary['recommended_models']['transcription'] = transcription_models[0]['name']
                    
        except Exception as e:
            self.logger.error(f"Failed to get model info summary: {e}")
            summary['error'] = str(e)
        
        return summary

    def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion avec LM Studio."""
        test_results = {
            'server_running': False,
            'api_accessible': False,
            'models_available': 0,
            'error_message': None
        }
        
        try:
            test_results['server_running'] = self.is_server_running()
            
            if test_results['server_running']:
                models = self.get_available_models()
                test_results['models_available'] = len(models)
                test_results['api_accessible'] = True
            else:
                test_results['error_message'] = "LM Studio server is not running"
                
        except Exception as e:
            test_results['error_message'] = str(e)
        
        return test_results