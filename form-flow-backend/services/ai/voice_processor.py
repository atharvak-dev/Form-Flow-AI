"""
Voice-Specific Processing Module

Handles the unique challenges of voice input that text doesn't have:
- STT (Speech-to-Text) error correction
- Voice normalization (emails, phones, spelled out text)
- Clarification strategies (escalating help)
- Confidence calibration (field importance)
- Multi-modal fallback
- Noise/audio quality handling

Usage:
    from services.ai.voice_processor import (
        VoiceInputProcessor,
        ClarificationStrategy,
        ConfidenceCalibrator,
        MultiModalFallback,
    )
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Voice Input Processor - STT Error Correction
# =============================================================================

class VoiceInputProcessor:
    """
    Handle voice-specific issues that text doesn't have.
    
    Converts spoken text to proper format:
    - "john at gmail dot com" → "john@gmail.com"
    - "five five five one two three four" → "555-1234"
    - "j o h n" → "john" (spelled out letters)
    """
    
    # Common STT (Speech-to-Text) articulation patterns
    STT_CORRECTIONS = {
        # Email articulations
        'at the rate': '@',
        'at the rate of': '@',
        'at sign': '@',
        'at symbol': '@',
        ' at ': '@',
        'dot com': '.com',
        'dot org': '.org',
        'dot net': '.net',
        'dot edu': '.edu',
        'dot co': '.co',
        'dot io': '.io',
        'dotcom': '.com',
        'gmail dot com': 'gmail.com',
        'gmail.com': 'gmail.com',
        'yahoo dot com': 'yahoo.com',
        'hotmail dot com': 'hotmail.com',
        'outlook dot com': 'outlook.com',
        
        # Punctuation
        'underscore': '_',
        'under score': '_',
        'hyphen': '-',
        'dash': '-',
        'period': '.',
        'dot': '.',
        'full stop': '.',
        'space': ' ',
        'plus': '+',
        'hash': '#',
        'hashtag': '#',
        'star': '*',
        'asterisk': '*',
        'ampersand': '&',
        'and sign': '&',
    }
    
    # Number words to digits
    NUMBER_WORDS = {
        'zero': '0', 'oh': '0', 'o': '0',
        'one': '1', 'won': '1',
        'two': '2', 'to': '2', 'too': '2',
        'three': '3',
        'four': '4', 'for': '4', 'fore': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8', 'ate': '8',
        'nine': '9',
        'ten': '10',
    }
    
    # Common homophones that cause STT confusion
    HOMOPHONES = {
        'male': 'mail',
        'their': 'there',
        'your': 'you\'re',
        'hear': 'here',
        'write': 'right',
        'weight': 'wait',
        'cent': 'sent',
        'no': 'know',
        'by': 'bye',
        'buy': 'bye',
        'sea': 'see',
        'week': 'weak',
    }
    
    # Domain typo corrections (matched with word boundaries in _normalize_email)
    DOMAIN_CORRECTIONS = {
        r'\bg\s*mail\b': 'gmail',
        r'\bgee\s*mail\b': 'gmail',
        r'\bgmale\b': 'gmail',
        r'\bgmal\b': 'gmail',
        r'\byaho\b': 'yahoo',  # Only match standalone 'yaho', not 'yahoo'
        r'\bhot\s*mail\b': 'hotmail',
        r'\bout\s*look\b': 'outlook',
    }
    
    @classmethod
    def normalize_voice_input(
        cls, 
        raw_voice_text: str,
        expected_field_type: Optional[str] = None
    ) -> str:
        """
        Normalize voice input to proper text format.
        
        Args:
            raw_voice_text: Raw text from STT
            expected_field_type: Hint about what type of data is expected
            
        Returns:
            Normalized text ready for extraction
        """
        if not raw_voice_text:
            return ""
        
        normalized = raw_voice_text.strip().lower()
        
        # Apply general STT corrections
        normalized = cls._apply_stt_corrections(normalized)
        
        # Handle spelled-out text: "j o h n" → "john"
        if cls._is_spelled_out(normalized):
            normalized = cls._join_spelled_letters(normalized)
        
        # Field-specific normalization
        if expected_field_type == 'email':
            normalized = cls._normalize_email(normalized)
        elif expected_field_type == 'tel':
            normalized = cls._normalize_phone(normalized)
        elif expected_field_type == 'number':
            normalized = cls._normalize_number(normalized)
        
        return normalized.strip()
    
    @classmethod
    def _apply_stt_corrections(cls, text: str) -> str:
        """Apply all STT correction patterns."""
        result = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_patterns = sorted(
            cls.STT_CORRECTIONS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for spoken, written in sorted_patterns:
            result = result.replace(spoken, written)
        
        return result
    
    @classmethod
    def _is_spelled_out(cls, text: str) -> bool:
        """
        Detect if user is spelling out letters: "j o h n at g m a i l"
        """
        words = text.split()
        # Count single character words
        single_chars = sum(1 for w in words if len(w) == 1 and w.isalpha())
        # If more than 40% are single letters, probably spelling
        return len(words) > 3 and (single_chars / len(words)) > 0.4
    
    @classmethod
    def _join_spelled_letters(cls, text: str) -> str:
        """
        Join spelled out letters: "j o h n at g m a i l" → "john@gmail"
        """
        result = []
        words = text.split()
        i = 0
        
        while i < len(words):
            word = words[i]
            
            # Keep special characters/words as-is
            if word in ['@', '.', '-', '_'] or len(word) > 1:
                if result and result[-1].isalpha() and len(result[-1]) == 1:
                    # Previous was single letter, join them
                    result[-1] = ''.join(result) + word if word in ['@', '.'] else result[-1]
                result.append(word)
            else:
                # Single letter - accumulate
                if result and len(result[-1]) == 1 and result[-1].isalpha():
                    result[-1] = result[-1] + word
                else:
                    result.append(word)
            i += 1
        
        return ' '.join(result)
    
    @classmethod
    def _normalize_email(cls, text: str) -> str:
        """
        Normalize email addresses.
        
        "john at gmail dot com" → "john@gmail.com"
        "john underscore doe at gmail dot com" → "john_doe@gmail.com"
        """
        result = text
        
        # Fix domain typos using regex patterns with word boundaries
        for pattern, correct in cls.DOMAIN_CORRECTIONS.items():
            result = re.sub(pattern, correct, result, flags=re.IGNORECASE)
        
        # Remove spaces around @ and around dots before TLD
        result = re.sub(r'\s*@\s*', '@', result)
        # Handle "yahoo .com" -> "yahoo.com"  and "yahoo. com" -> "yahoo.com"
        result = re.sub(r'\s*\.\s*(com|org|net|edu|io|co)\b', r'.\1', result)
        
        # Clean up any remaining spaces in email
        if '@' in result:
            parts = result.split('@')
            if len(parts) == 2:
                local = parts[0].replace(' ', '')
                domain = parts[1].replace(' ', '')
                result = f"{local}@{domain}"
        
        return result
    
    @classmethod
    def _normalize_phone(cls, text: str) -> str:
        """
        Normalize phone numbers.
        
        "five five five one two three four" → "555-1234"
        "plus one five five five..." → "+1-555-..."
        """
        result = text
        
        # Convert number words to digits
        for word, digit in cls.NUMBER_WORDS.items():
            result = re.sub(rf'\b{word}\b', digit, result, flags=re.IGNORECASE)
        
        # Extract just digits and plus sign
        digits = re.sub(r'[^\d+]', '', result)
        
        # Format nicely if we have enough digits
        if len(digits) >= 10:
            if digits.startswith('+'):
                # International format
                country = digits[1:2]
                remaining = digits[2:]
                if len(remaining) == 10:
                    return f"+{country}-{remaining[:3]}-{remaining[3:6]}-{remaining[6:]}"
            elif len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        
        return digits if digits else result
    
    @classmethod
    def _normalize_number(cls, text: str) -> str:
        """Convert spoken numbers to digits."""
        result = text
        for word, digit in cls.NUMBER_WORDS.items():
            result = re.sub(rf'\b{word}\b', digit, result, flags=re.IGNORECASE)
        return result
    
    @classmethod
    def detect_hesitation(cls, text: str) -> bool:
        """
        Detect if user is hesitating/struggling.
        
        Filler words indicate user needs help.
        """
        hesitation_markers = [
            'uh', 'um', 'hmm', 'uhh', 'umm',
            'let me think', 'wait', 'hold on',
            "i'm not sure", 'what was it',
        ]
        text_lower = text.lower()
        return any(marker in text_lower for marker in hesitation_markers)
    
    @classmethod
    def extract_partial_email(cls, text: str) -> Dict[str, Optional[str]]:
        """
        Extract parts of an email for step-by-step entry.
        
        Returns dict with local_part, domain if found.
        """
        normalized = cls.normalize_voice_input(text, 'email')
        
        if '@' in normalized:
            parts = normalized.split('@')
            return {
                'local_part': parts[0] if parts[0] else None,
                'domain': parts[1] if len(parts) > 1 and parts[1] else None,
                'is_complete': bool(parts[0] and len(parts) > 1 and '.' in parts[1])
            }
        
        return {'local_part': normalized or None, 'domain': None, 'is_complete': False}


# =============================================================================
# Clarification Strategy - Escalating Help
# =============================================================================

class ClarificationLevel(Enum):
    """Levels of clarification, escalating in helpfulness."""
    REPHRASE = 1
    PROVIDE_FORMAT = 2
    BREAK_DOWN = 3
    OFFER_ALTERNATIVES = 4


class ClarificationStrategy:
    """
    Provide smart, escalating clarification for voice users.
    
    When extraction fails, don't just repeat the same question.
    Each attempt provides MORE specific, DIFFERENT help.
    """
    
    @classmethod
    def get_clarification(
        cls,
        field_info: Dict[str, Any],
        attempt_count: int,
        last_input: Optional[str] = None
    ) -> str:
        """
        Generate progressive clarification based on attempt count.
        
        Args:
            field_info: Field metadata (name, label, type)
            attempt_count: How many times we've tried
            last_input: What the user said last (for context)
            
        Returns:
            Clarification prompt
        """
        field_type = field_info.get('type', 'text').lower()
        label = field_info.get('label', field_info.get('name', 'this field'))
        
        if attempt_count == 1:
            return cls._rephrase_question(label, field_type)
        elif attempt_count == 2:
            return cls._provide_format_example(label, field_type)
        elif attempt_count == 3:
            return cls._break_down_input(label, field_type)
        else:
            return cls._offer_alternatives(label, field_type)
    
    @classmethod
    def _rephrase_question(cls, label: str, field_type: str) -> str:
        """First attempt: Gentle rephrasing."""
        phrases = {
            'email': f"Let me try that again. What's your email address?",
            'tel': f"Sorry, I didn't catch your phone number. Could you say it again?",
            'text': f"I missed that. What's your {label}?",
        }
        
        if 'name' in label.lower():
            return "I didn't catch your name. Could you say it again clearly?"
        
        return phrases.get(field_type, f"Could you repeat your {label}?")
    
    @classmethod
    def _provide_format_example(cls, label: str, field_type: str) -> str:
        """Second attempt: Provide concrete format example."""
        examples = {
            'email': (
                "For your email, try saying it like: "
                "'john underscore doe at gmail dot com' or spell it out like "
                "'j-o-h-n at g-m-a-i-l dot com'"
            ),
            'tel': (
                "For your phone number, try saying it with pauses: "
                "'five five five... pause... one two three four'"
            ),
            'text': f"For {label}, just say it slowly and clearly."
        }
        
        if 'name' in label.lower():
            return "Try saying your name like: 'First name is John. Last name is Smith.'"
        
        return examples.get(field_type, f"Can you tell me your {label} slowly and clearly?")
    
    @classmethod
    def _break_down_input(cls, label: str, field_type: str) -> str:
        """Third attempt: Break into smaller pieces."""
        breakdowns = {
            'email': "Let's break it down. First, what comes before the @ sign in your email?",
            'tel': "Let's go step by step. What's your area code - the first 3 digits?",
            'text': f"Let's try one piece at a time. What's the first part of your {label}?"
        }
        
        if 'name' in label.lower():
            return "Let's start simple - what's just your first name?"
        
        return breakdowns.get(field_type, f"Can you spell out your {label} letter by letter?")
    
    @classmethod
    def _offer_alternatives(cls, label: str, field_type: str) -> str:
        """Final attempt: Offer to skip or switch input mode."""
        return (
            f"Having trouble with {label} over voice. You can say 'skip' to skip this field, "
            f"or try typing it instead if that's easier."
        )


# =============================================================================
# Confidence Calibrator - Dynamic Thresholds
# =============================================================================

class FieldImportance(Enum):
    """Importance levels for field accuracy."""
    CRITICAL = "critical"  # Email, phone - MUST be correct
    HIGH = "high"          # Name - important but minor typos ok
    MEDIUM = "medium"      # Company - can be corrected later
    LOW = "low"            # Notes, comments - very flexible


class ConfidenceCalibrator:
    """
    Adjust confidence thresholds dynamically based on:
    - Field importance
    - User frustration level
    - Past correction patterns
    """
    
    # Base thresholds by importance
    BASE_THRESHOLDS = {
        FieldImportance.CRITICAL: 0.90,
        FieldImportance.HIGH: 0.80,
        FieldImportance.MEDIUM: 0.65,
        FieldImportance.LOW: 0.50,
    }
    
    # Field importance classification
    FIELD_IMPORTANCE_MAP = {
        'email': FieldImportance.CRITICAL,
        'phone': FieldImportance.CRITICAL,
        'tel': FieldImportance.CRITICAL,
        'mobile': FieldImportance.CRITICAL,
        'name': FieldImportance.HIGH,
        'first_name': FieldImportance.HIGH,
        'last_name': FieldImportance.HIGH,
        'full_name': FieldImportance.HIGH,
        'company': FieldImportance.MEDIUM,
        'organization': FieldImportance.MEDIUM,
        'title': FieldImportance.MEDIUM,
        'message': FieldImportance.LOW,
        'notes': FieldImportance.LOW,
        'comments': FieldImportance.LOW,
    }
    
    @classmethod
    def get_field_importance(cls, field_name: str, field_type: str) -> FieldImportance:
        """Determine importance level for a field."""
        name_lower = field_name.lower()
        
        # Check direct mapping
        for key, importance in cls.FIELD_IMPORTANCE_MAP.items():
            if key in name_lower:
                return importance
        
        # Check by type
        if field_type in ['email', 'tel']:
            return FieldImportance.CRITICAL
        elif field_type == 'textarea':
            return FieldImportance.LOW
        
        return FieldImportance.MEDIUM
    
    @classmethod
    def should_confirm(
        cls,
        field_name: str,
        field_type: str,
        confidence: float,
        is_frustrated: bool = False,
        correction_count: int = 0
    ) -> bool:
        """
        Determine if we should confirm this extraction.
        
        Args:
            field_name: Name of the field
            field_type: Type of the field
            confidence: Extraction confidence (0-1)
            is_frustrated: Is user showing frustration
            correction_count: How many times this field was corrected
            
        Returns:
            True if we should ask for confirmation
        """
        importance = cls.get_field_importance(field_name, field_type)
        threshold = cls.BASE_THRESHOLDS[importance]
        
        # Reduce threshold if user is frustrated (be more lenient)
        if is_frustrated:
            threshold -= 0.10
        
        # Reduce further if they've corrected before (don't annoy them)
        if correction_count > 0:
            threshold -= 0.05 * min(correction_count, 2)
        
        return confidence < threshold
    
    @classmethod
    def generate_confirmation_prompt(
        cls,
        field_name: str,
        extracted_value: str,
        confidence: float
    ) -> str:
        """
        Generate natural confirmation prompt based on confidence.
        
        High confidence: Quick, casual confirm
        Low confidence: Careful, explicit confirm
        """
        # Clean field name for display
        display_name = field_name.replace('_', ' ').title()
        
        if confidence > 0.85:
            # High confidence - quick confirm
            return f"Got your {display_name} as '{extracted_value}' - correct?"
        elif confidence > 0.70:
            # Medium confidence
            return f"Let me confirm - your {display_name} is '{extracted_value}'?"
        else:
            # Low confidence - very explicit
            return (
                f"I want to make sure I got this right. "
                f"Did you say your {display_name} is '{extracted_value}'? "
                f"Say 'yes' to confirm or 'no' to correct."
            )


# =============================================================================
# Multi-Modal Fallback
# =============================================================================

class MultiModalFallback:
    """
    Know when voice isn't working and offer alternatives.
    
    After repeated failures, suggest:
    - Typing instead
    - Skipping for now
    - Breaking into steps
    """
    
    # Fields that are hard for voice
    DIFFICULT_VOICE_FIELDS = {'email', 'url', 'password', 'website', 'address'}
    
    @classmethod
    def should_offer_fallback(
        cls,
        field_name: str,
        field_type: str,
        failure_count: int
    ) -> bool:
        """Determine if we should offer alternative input."""
        name_lower = field_name.lower()
        
        # Complex fields fail more in voice - offer fallback sooner
        is_difficult = (
            field_type in cls.DIFFICULT_VOICE_FIELDS or
            any(df in name_lower for df in cls.DIFFICULT_VOICE_FIELDS)
        )
        
        if is_difficult and failure_count >= 2:
            return True
        
        if failure_count >= 3:
            return True
        
        return False
    
    @classmethod
    def generate_fallback_response(cls, field_name: str) -> Dict[str, Any]:
        """
        Generate response with fallback options.
        
        Returns dict with message and frontend actions.
        """
        display_name = field_name.replace('_', ' ')
        
        return {
            'message': (
                f"Having trouble with {display_name} over voice. "
                f"Would you like to type it instead, skip it for now, or try one more time?"
            ),
            'fallback_type': 'multi_option',
            'options': [
                {'action': 'keyboard', 'label': 'Type it', 'voice_trigger': 'type'},
                {'action': 'skip', 'label': 'Skip for now', 'voice_trigger': 'skip'},
                {'action': 'retry', 'label': 'Try again', 'voice_trigger': 'try again'},
            ]
        }


# =============================================================================
# Noise/Audio Quality Handler
# =============================================================================

class AudioQuality(Enum):
    """Audio quality levels."""
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class NoiseHandler:
    """
    Adapt to real-world audio environments.
    
    Adjust strategies based on audio quality metrics from STT.
    """
    
    @classmethod
    def assess_audio_quality(
        cls,
        stt_confidence: float,
        signal_to_noise: Optional[float] = None
    ) -> AudioQuality:
        """
        Assess audio quality from STT metadata.
        
        Args:
            stt_confidence: Overall STT confidence (0-1)
            signal_to_noise: SNR in dB if available
            
        Returns:
            AudioQuality level
        """
        # Use STT confidence as primary indicator
        if stt_confidence >= 0.90:
            return AudioQuality.GOOD
        elif stt_confidence >= 0.75:
            return AudioQuality.FAIR
        else:
            return AudioQuality.POOR
    
    @classmethod
    def get_quality_adapted_response(
        cls,
        audio_quality: AudioQuality,
        field_type: str,
        is_critical: bool = False
    ) -> Optional[str]:
        """
        Generate response adapted to audio quality.
        
        Returns None if no adaptation needed.
        """
        if audio_quality == AudioQuality.GOOD:
            return None  # No adaptation needed
        
        if audio_quality == AudioQuality.POOR:
            if is_critical:
                return (
                    "I'm having trouble hearing clearly. "
                    "Can you move to a quieter spot, or would you prefer to type this field?"
                )
            else:
                return (
                    "Audio quality is low. "
                    "Would you like to skip this for now and come back to it?"
                )
        
        # FAIR quality
        if field_type in ['email', 'tel']:
            return "I'm having a bit of trouble - could you speak a bit louder or slower?"
        
        return None


# =============================================================================
# Streaming Speech Handler (for future real-time processing)
# =============================================================================

@dataclass
class PartialUtterance:
    """Represents a partial/streaming utterance."""
    text: str
    is_final: bool
    timestamp: float
    confidence: float = 1.0


class StreamingSpeechHandler:
    """
    Handle streaming/partial speech input.
    
    Enables real-time processing as user speaks, not waiting
    for complete utterance.
    """
    
    def __init__(self):
        self.partial_buffer: List[str] = []
        self.last_update_time: float = 0
        self.silence_threshold_ms: int = 800
    
    def process_partial(
        self,
        partial: PartialUtterance,
        expected_field_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Process partial speech, detecting issues in real-time.
        
        Returns an interrupt message if we detect a problem,
        or None to continue listening.
        """
        if partial.is_final:
            # Complete utterance - return full text
            self.partial_buffer.append(partial.text)
            full = ' '.join(self.partial_buffer)
            self.partial_buffer.clear()
            return full
        
        self.partial_buffer.append(partial.text)
        
        # Real-time validation
        current_text = ' '.join(self.partial_buffer)
        
        # Check for common issues
        if expected_field_type == 'email':
            # User mentioned gmail but no @ - remind them
            if 'gmail' in current_text.lower() and '@' not in current_text and 'at' not in current_text.lower():
                return "HINT: Don't forget to say 'at' for the @ sign"
        
        # Detect hesitation
        if VoiceInputProcessor.detect_hesitation(partial.text):
            return "HINT: Take your time, or say 'skip' if you're not sure"
        
        return None  # Continue listening
    
    def get_accumulated_text(self) -> str:
        """Get all text accumulated so far."""
        return ' '.join(self.partial_buffer)
    
    def clear_buffer(self):
        """Clear the partial buffer."""
        self.partial_buffer.clear()
