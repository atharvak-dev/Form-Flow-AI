#!/usr/bin/env python3

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

def test_streaming_speech():
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if not api_key:
        print("ELEVENLABS_API_KEY not found in .env file")
        return
    
    # Test streaming API call
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream"
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
    
    print("Testing ElevenLabs Streaming API...")
    start_time = time.time()
    
    response = requests.post(url, json=data, headers=headers, stream=True)
    
    if response.status_code == 200:
        print("[SUCCESS] Streaming started!")
        
        audio_chunks = []
        chunk_count = 0
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                chunk_count += 1
                audio_chunks.append(chunk)
                elapsed = time.time() - start_time
                print(f"[CHUNK] {chunk_count}: {len(chunk)} bytes (at {elapsed:.2f}s)")
        
        # Save complete audio
        complete_audio = b''.join(audio_chunks)
        with open("test_stream_output.mp3", "wb") as f:
            f.write(complete_audio)
        
        total_time = time.time() - start_time
        print(f"[SUCCESS] Streaming complete! Total: {len(complete_audio)} bytes in {total_time:.2f}s")
        print(f"[SUCCESS] Audio saved as test_stream_output.mp3")
        
    else:
        print(f"[ERROR] Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_streaming_speech()