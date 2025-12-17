#!/usr/bin/env python3

from speech_service import SpeechService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_speech_service():
    print("Testing ElevenLabs Speech Service...")
    
    # Initialize service
    speech_service = SpeechService()
    
    # Check if API key is configured
    if not speech_service.api_key:
        print("[ERROR] ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"[OK] API Key configured: {speech_service.api_key[:10]}...")
    
    # Test text-to-speech
    test_text = "Please provide your email address"
    print(f"[TEST] Testing TTS with: '{test_text}'")
    
    audio_data = speech_service.text_to_speech(test_text)
    
    if audio_data:
        print(f"[OK] Speech generated successfully! Audio size: {len(audio_data)} bytes")
        
        # Save test audio file
        with open("test_speech.mp3", "wb") as f:
            f.write(audio_data)
        print("[SAVE] Test audio saved as 'test_speech.mp3'")
        return True
    else:
        print("[ERROR] Failed to generate speech")
        return False

if __name__ == "__main__":
    success = test_speech_service()
    if success:
        print("\n[SUCCESS] Speech service is working correctly!")
    else:
        print("\n[FAILED] Speech service test failed!")