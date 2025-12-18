"""
Deepgram Speech-to-Text Service
Provides high-accuracy transcription using Deepgram's Nova-2 model
"""

import os
import httpx
from typing import Optional, Dict, Any
import json

class DeepgramService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        self.base_url = "https://api.deepgram.com/v1/listen"
        
        if not self.api_key:
            print("⚠️ Deepgram API key not found. Speech-to-text will use fallback.")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        mime_type: str = "audio/webm",
        language: str = "en",
        smart_format: bool = True,
        punctuate: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Deepgram's API
        
        Args:
            audio_data: Raw audio bytes
            mime_type: Audio MIME type (audio/webm, audio/wav, etc.)
            language: Language code (default: en)
            smart_format: Enable smart formatting (emails, numbers, etc.)
            punctuate: Enable punctuation
            
        Returns:
            Dict with transcript, confidence, and metadata
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Deepgram API key not configured",
                "transcript": "",
                "confidence": 0
            }
        
        try:
            # Deepgram API parameters for best accuracy
            params = {
                "model": "nova-2",  # Latest and most accurate model
                "language": language,
                "smart_format": str(smart_format).lower(),
                "punctuate": str(punctuate).lower(),
                "diarize": "false",
                "filler_words": "false",
                "numerals": "true",  # Better number handling
            }
            
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": mime_type
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    params=params,
                    headers=headers,
                    content=audio_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract transcript from Deepgram response
                    channels = result.get("results", {}).get("channels", [])
                    if channels:
                        alternatives = channels[0].get("alternatives", [])
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "")
                            confidence = alternatives[0].get("confidence", 0)
                            
                            return {
                                "success": True,
                                "transcript": transcript,
                                "confidence": confidence,
                                "words": alternatives[0].get("words", []),
                                "metadata": result.get("metadata", {})
                            }
                    
                    return {
                        "success": True,
                        "transcript": "",
                        "confidence": 0,
                        "error": "No transcription available"
                    }
                else:
                    error_detail = response.text
                    print(f"❌ Deepgram API error: {response.status_code} - {error_detail}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "transcript": "",
                        "confidence": 0
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Transcription timeout",
                "transcript": "",
                "confidence": 0
            }
        except Exception as e:
            print(f"❌ Deepgram transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0
            }
    
    def is_available(self) -> bool:
        """Check if Deepgram service is configured and available"""
        return bool(self.api_key)
