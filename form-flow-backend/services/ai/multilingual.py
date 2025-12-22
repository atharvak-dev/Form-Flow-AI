"""
Multilingual Voice Processor

Features:
- Auto-detect spoken language
- Translate non-English to English for processing
- Accent-aware phone/date formatting
- Support for Indian English, British English, Spanish, Hindi

Uses Google Gemini for translation and language detection.
"""

import re
from typing import Optional, Tuple, Dict, List
from enum import Enum

from utils.logging import get_logger

logger = get_logger(__name__)


class Language(str, Enum):
    """Supported languages"""
    ENGLISH_US = "en-US"
    ENGLISH_UK = "en-GB"
    ENGLISH_IN = "en-IN"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    AUTO = "auto"


# Language-specific patterns
LANGUAGE_PATTERNS = {
    Language.HINDI: {
        'indicators': [
            r'\b(mera|meri|hai|hain|kya|aur|main|aap|naam|ghar|phone)\b',
            r'[\u0900-\u097F]'  # Devanagari script
        ],
        'greetings': ['namaste', 'namaskar'],
    },
    Language.SPANISH: {
        'indicators': [
            r'\b(mi|tu|es|el|la|los|las|y|que|de|en|con|para|por)\b',
            r'\b(nombre|correo|teléfono|direccion)\b'
        ],
        'greetings': ['hola', 'buenos'],
    },
    Language.FRENCH: {
        'indicators': [
            r'\b(je|tu|il|elle|nous|vous|est|sont|et|le|la|les|de|du)\b',
            r'\b(nom|email|téléphone|adresse)\b'
        ],
        'greetings': ['bonjour', 'salut'],
    },
    Language.ENGLISH_IN: {
        'indicators': [
            r'\b(kindly|prepone|revert back|do the needful|only|itself)\b',
            r'\b(lakh|crore|pincode)\b'
        ],
        'number_words': {
            'double': lambda d: d * 2,  # "double five" = "55"
        }
    },
    Language.ENGLISH_UK: {
        'indicators': [
            r'\b(postcode|flat|lift|mobile|colour|favour)\b',
            r'\b(nought|nil)\b'
        ],
        'transforms': {
            'postcode': 'zipcode',
            'flat': 'apartment',
            'mobile': 'phone',
        }
    }
}


class MultilingualProcessor:
    """
    Handles multilingual voice input processing.
    
    Workflow:
    1. Detect language of input
    2. If non-English, translate to English
    3. Apply accent-specific transformations
    4. Process with English-based refinement
    """
    
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM for translation."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from config.settings import settings
            
            if settings.GOOGLE_API_KEY:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.1
                )
                logger.info("Multilingual LLM initialized")
        except Exception as e:
            logger.warning(f"Could not initialize multilingual LLM: {e}")
            self.llm = None
    
    def detect_language(self, text: str) -> Language:
        """
        Detect the language of input text.
        
        Uses pattern matching first, then LLM for edge cases.
        
        Args:
            text: Input text
        
        Returns:
            Detected Language enum
        """
        text_lower = text.lower()
        
        # Check for Devanagari (Hindi) first
        if re.search(r'[\u0900-\u097F]', text):
            return Language.HINDI
        
        # Check greetings
        for lang, patterns in LANGUAGE_PATTERNS.items():
            greetings = patterns.get('greetings', [])
            if any(g in text_lower for g in greetings):
                return lang
        
        # Check language indicators
        scores = {}
        for lang, patterns in LANGUAGE_PATTERNS.items():
            indicators = patterns.get('indicators', [])
            score = sum(
                1 for pattern in indicators 
                if re.search(pattern, text_lower, re.IGNORECASE)
            )
            if score > 0:
                scores[lang] = score
        
        if scores:
            # Return language with highest score
            return max(scores, key=scores.get)
        
        # Default to US English
        return Language.ENGLISH_US
    
    async def translate_to_english(
        self, 
        text: str, 
        source_lang: Language
    ) -> Tuple[str, float]:
        """
        Translate text to English.
        
        Args:
            text: Text to translate
            source_lang: Source language
        
        Returns:
            (translated_text, confidence)
        """
        if source_lang in [Language.ENGLISH_US, Language.ENGLISH_UK, Language.ENGLISH_IN]:
            # Already English, just apply transforms
            transformed = self._apply_dialect_transforms(text, source_lang)
            return transformed, 0.95
        
        if not self.llm:
            logger.warning("LLM not available for translation")
            return text, 0.5
        
        try:
            prompt = f"""Translate the following text from {source_lang.value} to English.
Maintain the meaning and context. For form fields, keep proper formatting.
If there are any numbers (phone, dates), keep them in the original format.

Text to translate:
{text}

Provide ONLY the English translation, nothing else."""

            response = await self.llm.ainvoke(prompt)
            translated = response.content.strip()
            
            logger.info(f"Translated from {source_lang.value}: '{text}' → '{translated}'")
            
            return translated, 0.85
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text, 0.3
    
    def _apply_dialect_transforms(self, text: str, dialect: Language) -> str:
        """Apply dialect-specific transformations."""
        if dialect not in LANGUAGE_PATTERNS:
            return text
        
        transforms = LANGUAGE_PATTERNS[dialect].get('transforms', {})
        result = text
        
        for source, target in transforms.items():
            result = re.sub(
                rf'\b{source}\b', 
                target, 
                result, 
                flags=re.IGNORECASE
            )
        
        return result
    
    def apply_accent_patterns(
        self, 
        text: str, 
        accent: Language,
        field_type: str = ""
    ) -> str:
        """
        Apply accent-specific patterns for better recognition.
        
        Indian English:
        - "double five" → "55"
        - "mobile number" → phone field
        
        British English:
        - "nought" → "0"
        - "postcode" → zipcode
        """
        result = text.lower()
        
        # Indian English number patterns
        if accent == Language.ENGLISH_IN:
            # "double five" → "55"
            result = re.sub(
                r'double\s+(\w+)',
                lambda m: self._double_number_word(m.group(1)),
                result
            )
            
            # Indian number words
            indian_numbers = {
                'lakh': '100000',
                'crore': '10000000'
            }
            for word, value in indian_numbers.items():
                result = result.replace(word, value)
        
        # British English patterns
        elif accent == Language.ENGLISH_UK:
            uk_numbers = {
                'nought': '0',
                'nil': '0'
            }
            for word, value in uk_numbers.items():
                result = result.replace(word, value)
        
        return result
    
    def _double_number_word(self, word: str) -> str:
        """Convert doubled number words."""
        number_words = {
            'zero': '00', 'one': '11', 'two': '22', 'three': '33',
            'four': '44', 'five': '55', 'six': '66', 'seven': '77',
            'eight': '88', 'nine': '99', 'oh': '00', 'o': '00'
        }
        return number_words.get(word.lower(), word)
    
    async def process_multilingual(
        self, 
        text: str,
        target_language: Language = Language.AUTO,
        field_type: str = ""
    ) -> Dict:
        """
        Full multilingual processing pipeline.
        
        Args:
            text: Raw input text (any language)
            target_language: Expected language (or AUTO for detection)
            field_type: Field type for context
        
        Returns:
            {
                detected_language: str,
                original: str,
                processed: str,
                was_translated: bool,
                confidence: float
            }
        """
        # Detect language if AUTO
        if target_language == Language.AUTO:
            detected = self.detect_language(text)
        else:
            detected = target_language
        
        # Translate if non-English
        if detected in [Language.HINDI, Language.SPANISH, Language.FRENCH, Language.GERMAN]:
            translated, confidence = await self.translate_to_english(text, detected)
            was_translated = True
        else:
            # Apply dialect transforms for English variants
            translated = self._apply_dialect_transforms(text, detected)
            was_translated = False
            confidence = 0.95
        
        # Apply accent patterns
        processed = self.apply_accent_patterns(translated, detected, field_type)
        
        return {
            'detected_language': detected.value,
            'original': text,
            'processed': processed,
            'was_translated': was_translated,
            'confidence': confidence
        }


# Singleton instance
_multilingual_processor: Optional[MultilingualProcessor] = None


def get_multilingual_processor() -> MultilingualProcessor:
    """Get singleton MultilingualProcessor."""
    global _multilingual_processor
    if _multilingual_processor is None:
        _multilingual_processor = MultilingualProcessor()
    return _multilingual_processor
