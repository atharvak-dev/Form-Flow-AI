import os
import requests
from typing import Optional, Iterator
import json

class SpeechService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def text_to_speech(self, text: str, voice_id: str = None) -> Optional[bytes]:
        if not self.api_key:
            print("ElevenLabs API key not configured")
            return None
            
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id or self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                return response.content
            else:
                print(f"TTS Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
    
    def text_to_speech_stream(self, text: str, voice_id: str = None) -> Iterator[bytes]:
        """Stream audio in real-time as it's generated"""
        if not self.api_key:
            print("ElevenLabs API key not configured")
            return
            
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id or self.voice_id}/stream"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers, stream=True)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk
            else:
                print(f"TTS Stream Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"TTS Stream Error: {e}")
    
    def generate_form_speech(self, form_schema: list) -> dict:
        """Generate speech for all form fields"""
        speech_data = {}
        
        for form in form_schema:
            for field in form.get('fields', []):
                field_name = field.get('name')
                if not field_name:
                    continue
                    
                # Generate prompt text
                prompt_text = self._create_field_prompt(field)
                
                # Convert to speech
                audio_data = self.text_to_speech(prompt_text)
                if audio_data:
                    speech_data[field_name] = {
                        'text': prompt_text,
                        'audio': audio_data,
                        'field_type': field.get('type', 'text')
                    }
        
        return speech_data
    
    def _create_field_prompt(self, field: dict) -> str:
        """Create appropriate prompt text for each field type"""
        field_name = field.get('display_name') or field.get('label') or field.get('name', 'field')
        field_type = field.get('type', 'text')
        required = field.get('required', False)
        
        prompts = {
            'email': f"Please provide your email address for {field_name}. You can say it like 'john dot smith at gmail dot com', or simply 'username at gmail' and I'll format it correctly",
            'password': f"Please speak your password for {field_name}",
            'tel': f"Please provide your phone number for {field_name}",
            'checkbox': f"Say yes to check or no to uncheck {field_name}",
            'select': f"Please choose an option for {field_name}",
            'textarea': f"Please provide your response for {field_name}",
            'date': f"Please provide the date for {field_name}",
            'text': f"Please provide {field_name}"
        }
        
        prompt = prompts.get(field_type, f"Please provide {field_name}")
        
        if required:
            prompt += ". This field is required."
            
        return prompt
    
    def get_streaming_response(self, text: str, voice_id: str = None):
        """Get streaming response object for real-time audio"""
        return self.text_to_speech_stream(text, voice_id)