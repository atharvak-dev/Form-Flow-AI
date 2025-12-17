#!/usr/bin/env python3

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_speech_generation():
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if not api_key:
        print("ELEVENLABS_API_KEY not found in .env file")
        return
    
    # Test direct API call
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": "Please provide First Name. This field is required.",
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    print("Testing ElevenLabs API...")
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Success! Generated {len(response.content)} bytes of audio")
        
        # Save test audio
        with open("test_output.mp3", "wb") as f:
            f.write(response.content)
        print("✅ Audio saved as test_output.mp3")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_speech_generation()