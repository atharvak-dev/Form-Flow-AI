"""
ElevenLabs Realtime Speech-to-Text Service
Uses WebSocket API for streaming transcription
"""

import os
import asyncio
import json
import base64
import websockets
from typing import Optional, Dict, Any

class ElevenLabsSTTService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.ws_url = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
        
        if not self.api_key:
            print("⚠️ ElevenLabs API key not found. STT will not work.")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        sample_rate: int = 16000,
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using ElevenLabs realtime STT WebSocket API
        
        Args:
            audio_data: Raw audio bytes (PCM or WebM)
            sample_rate: Audio sample rate (default 16000 Hz)
            language_code: Language code (default: en)
            
        Returns:
            Dict with transcript, confidence, and metadata
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "ElevenLabs API key not configured",
                "transcript": "",
                "confidence": 0
            }
        
        try:
            # Build WebSocket URL with query parameters
            ws_url = (
                f"{self.ws_url}"
                f"?model_id=scribe_v1"
                f"&language_code={language_code}"
                f"&commit_strategy=vad"
                f"&vad_silence_threshold_secs=1.0"
                f"&audio_format=pcm_16000"
            )
            
            headers = {
                "xi-api-key": self.api_key
            }
            
            transcript_parts = []
            final_transcript = ""
            
            async with websockets.connect(
                ws_url, 
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                
                # Wait for session_started message
                session_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                session_data = json.loads(session_msg)
                
                if session_data.get("message_type") == "session_started":
                    print(f"🎤 ElevenLabs STT session started: {session_data.get('session_id', 'unknown')}")
                elif session_data.get("message_type") in ["auth_error", "error"]:
                    return {
                        "success": False,
                        "error": session_data.get("error", "Authentication failed"),
                        "transcript": "",
                        "confidence": 0
                    }
                
                # Convert audio to base64 and send
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Send audio chunk
                audio_message = {
                    "message_type": "input_audio_chunk",
                    "audio_base_64": audio_base64,
                    "sample_rate": sample_rate,
                    "commit": True  # Commit after this chunk for immediate transcription
                }
                
                await websocket.send(json.dumps(audio_message))
                print(f"📤 Sent {len(audio_data)} bytes of audio to ElevenLabs")
                
                # Receive transcription results
                try:
                    # Wait for responses with timeout
                    while True:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=10)
                            data = json.loads(response)
                            msg_type = data.get("message_type", "")
                            
                            if msg_type == "partial_transcript":
                                # Partial result (in-progress)
                                partial_text = data.get("text", "")
                                if partial_text:
                                    print(f"📝 Partial: {partial_text}")
                                    
                            elif msg_type == "committed_transcript":
                                # Final committed result
                                final_transcript = data.get("text", "")
                                print(f"✅ Final: {final_transcript}")
                                break
                                
                            elif msg_type == "committed_transcript_with_timestamps":
                                # Final with word timestamps
                                final_transcript = data.get("text", "")
                                print(f"✅ Final (with timestamps): {final_transcript}")
                                break
                                
                            elif msg_type in ["error", "auth_error", "quota_exceeded"]:
                                error_msg = data.get("error", "Unknown error")
                                print(f"❌ ElevenLabs STT error: {error_msg}")
                                return {
                                    "success": False,
                                    "error": error_msg,
                                    "transcript": "",
                                    "confidence": 0
                                }
                                
                        except asyncio.TimeoutError:
                            print("⏳ Timeout waiting for transcription")
                            break
                            
                except Exception as e:
                    print(f"❌ Error receiving transcription: {e}")
                    
            if final_transcript:
                return {
                    "success": True,
                    "transcript": final_transcript,
                    "confidence": 0.9,  # ElevenLabs doesn't return confidence
                    "words": []
                }
            else:
                return {
                    "success": False,
                    "error": "No transcription received",
                    "transcript": "",
                    "confidence": 0
                }
                
        except websockets.exceptions.WebSocketException as e:
            print(f"❌ WebSocket error: {e}")
            return {
                "success": False,
                "error": f"WebSocket connection failed: {str(e)}",
                "transcript": "",
                "confidence": 0
            }
        except Exception as e:
            print(f"❌ ElevenLabs STT error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0
            }
    
    def is_available(self) -> bool:
        """Check if ElevenLabs STT service is configured"""
        return bool(self.api_key)
