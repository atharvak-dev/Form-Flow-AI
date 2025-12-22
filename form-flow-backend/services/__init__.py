# Services module - Unified exports for all backend services
#
# Usage:
#   from services import get_text_refiner, get_voice_processor
#   from services.ai import ConversationAgent
#   from services.voice import SpeechService

# Re-export commonly used getters
from .ai import (
    get_text_refiner,
    get_session_manager,
    get_smart_autofill,
    get_form_analytics,
    get_multilingual_processor,
)

from .voice import (
    get_voice_processor,
    get_speech_service,
)

__all__ = [
    # AI Getters
    "get_text_refiner",
    "get_session_manager",
    "get_smart_autofill",
    "get_form_analytics",
    "get_multilingual_processor",
    # Voice Getters
    "get_voice_processor",
    "get_speech_service",
]
