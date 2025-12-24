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
import difflib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

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
    
    # Common STT (Speech-to-Text) articulation patterns (ENHANCED)
    STT_CORRECTIONS = {
        # Email articulations (expanded)
        'at the rate': '@',
        'at the rate of': '@',
        'at sign': '@',
        'at symbol': '@',
        'at the': '@',  # Common mishearing
        'dot com': '.com',
        'dot org': '.org',
        'dot net': '.net',
        'dot edu': '.edu',
        'dot co dot': '.co.',  # UK domains
        'dot co': '.co',
        'dot gov': '.gov',
        'dot io': '.io',
        'dotcom': '.com',
        'gmail dot com': 'gmail.com',
        'gmail.com': 'gmail.com',
        'yahoo dot com': 'yahoo.com',
        'hotmail dot com': 'hotmail.com',
        'outlook dot com': 'outlook.com',
        # Domain name corrections (before @ replacement)
        'g mail': 'gmail',
        'gee mail': 'gmail',
        'hot mail': 'hotmail',
        'out look': 'outlook',
        
        # Punctuation (expanded)
        'underscore': '_',
        'under score': '_',
        'hyphen': '-',
        'minus': '-',
        'dash': '-',
        'en dash': '-',
        'period': '.',
        'dot': '.',
        'full stop': '.',
        'space': ' ',
        'plus': '+',
        'plus sign': '+',
        'hash': '#',
        'hashtag': '#',
        'pound': '#',
        'star': '*',
        'asterisk': '*',
        'ampersand': '&',
        'and sign': '&',
        'forward slash': '/',
        'slash': '/',
        'backslash': '\\',
        'colon': ':',
        'semicolon': ';',
        'comma': ',',
    }
    
    # Number words to digits (ENHANCED)
    NUMBER_WORDS = {
        'zero': '0', 'oh': '0', 'o': '0',
        'one': '1', 'won': '1',
        'two': '2', 'to': '2', 'too': '2', 'tue': '2',
        'three': '3', 'tree': '3',
        'four': '4', 'for': '4', 'fore': '4',
        'five': '5', 'fife': '5',
        'six': '6',
        'seven': '7',
        'eight': '8', 'ate': '8',
        'nine': '9', 'niner': '9',
        'ten': '10',
        'eleven': '11',
        'twelve': '12',
        'thirteen': '13',
        'fourteen': '14',
        'fifteen': '15',
        'sixteen': '16',
        'seventeen': '17',
        'eighteen': '18',
        'nineteen': '19',
        'twenty': '20',
        'thirty': '30',
        'forty': '40',
        'fifty': '50',
        'sixty': '60',
        'seventy': '70',
        'eighty': '80',
        'ninety': '90',
        'hundred': '00',
        'thousand': '000',
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
    
    # Domain typo corrections (ENHANCED with more patterns)
    DOMAIN_CORRECTIONS = {
        r'\bg[\s\-]*mail\b': 'gmail',
        r'\bgee[\s\-]*mail\b': 'gmail',
        r'\bgmale\b': 'gmail',
        r'\bgmal\b': 'gmail',
        r'\bjee[\s\-]*mail\b': 'gmail',
        r'\byaho+\b': 'yahoo',  # Handles 'yaho', 'yahoo', 'yahooo'
        r'\byellow\b': 'yahoo',  # Common mishearing
        r'\bhot[\s\-]*mail\b': 'hotmail',
        r'\bhought[\s\-]*mail\b': 'hotmail',
        r'\bout[\s\-]*look\b': 'outlook',
        r'\baol\b': 'aol',
        r'\ba[\s\-]*o[\s\-]*l\b': 'aol',
        r'\bicloud\b': 'icloud',
        r'\bproton\b': 'proton',
        r'\bproton[\s\-]*mail\b': 'protonmail',
    }
    
    # TLD variations/typos
    TLD_CORRECTIONS = {
        'calm': 'com',
        'cam': 'com',
        'come': 'com',
        'con': 'com',
        'comb': 'com',
        'org': 'org',
        'net': 'net',
        'edu': 'edu',
        'gov': 'gov',
    }
    
    # Learning system for user corrections (class-level storage)
    _user_corrections: Dict[str, str] = {}
    _correction_count: Dict[str, int] = defaultdict(int)
    
    @classmethod
    def normalize_voice_input(
        cls, 
        raw_voice_text: str,
        expected_field_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        ENHANCED: Normalize voice input with context awareness and learning.
        
        Args:
            raw_voice_text: Raw text from STT
            expected_field_type: Hint about what type of data is expected
            context: Previous field values for cross-field validation
            
        Returns:
            Normalized text ready for extraction
        """
        if not raw_voice_text:
            return ""
        
        normalized = raw_voice_text.strip().lower()
        
        # NEW: Apply learned corrections first
        normalized = cls._apply_learned_corrections(normalized)
        
        # Apply general STT corrections
        normalized = cls._apply_stt_corrections(normalized)
        
        # Handle spelled-out text: "j o h n" → "john"
        if cls._is_spelled_out(normalized):
            normalized = cls._join_spelled_letters(normalized)
        
        # Field-specific normalization
        if expected_field_type == 'email':
            normalized = cls._normalize_email(normalized)
        elif expected_field_type in ['tel', 'phone']:
            normalized = cls._normalize_phone(normalized, context)
        elif expected_field_type == 'number':
            normalized = cls._normalize_number(normalized)
        elif expected_field_type == 'date':
            normalized = cls._normalize_date(normalized)
        elif expected_field_type == 'address':
            normalized = cls._normalize_address(normalized)
        elif expected_field_type == 'name':
            normalized = cls._normalize_name(normalized)
        
        return normalized.strip()
    
    @classmethod
    def _apply_learned_corrections(cls, text: str) -> str:
        """NEW: Apply corrections learned from user feedback."""
        result = text
        for wrong, correct in cls._user_corrections.items():
            if wrong in result:
                result = result.replace(wrong, correct)
        return result
    
    @classmethod
    def learn_from_correction(cls, heard: str, actual: str):
        """
        NEW: Learn from user corrections to improve over time.
        
        Args:
            heard: What the STT heard
            actual: What the user corrected it to
        """
        heard_lower = heard.lower().strip()
        actual_lower = actual.lower().strip()
        
        if heard_lower != actual_lower:
            cls._user_corrections[heard_lower] = actual_lower
            cls._correction_count[heard_lower] += 1
            
            logger.info(f"Learned correction: '{heard_lower}' → '{actual_lower}'")
            
            # Extract patterns for similar corrections
            if '@' in actual_lower and '@' not in heard_lower:
                # Learn email patterns
                parts_heard = heard_lower.split()
                # Find what was said instead of '@'
                for word in parts_heard:
                    if word not in actual_lower and word not in cls.STT_CORRECTIONS:
                        if word not in ['at', 'the', 'and', 'or', 'is', 'my']:
                            cls.STT_CORRECTIONS[word] = '@'
                            logger.info(f"Learned new STT pattern: '{word}' → '@'")
    
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
            # Skip plain ' at ' - handled specially below to prevent word corruption
            # (e.g., "is at harva" becoming "is@harva" when user meant "atharva")
            if spoken == ' at ':
                continue
            result = result.replace(spoken, written)
        
        # Handle ' at ' replacement carefully - only when followed by domain-like words
        # This prevents "is at harva" (where user meant "atharva") from becoming "@harva"
        # Match: (word) at (domain) where domain can be gmail, gmail.com, yahoo.com, etc.
        domain_words = r'(gmail\.com|yahoo\.com|hotmail\.com|outlook\.com|gmail|yahoo|hotmail|outlook|aol|icloud|proton|mail|live|msn|\w+\.com|\w+\.org|\w+\.net)'
        result = re.sub(rf'(\S)\s+at\s+{domain_words}', r'\1@\2', result, flags=re.IGNORECASE)
        
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
        ENHANCED: Normalize email addresses with TLD correction.
        
        "john at gmail dot com" → "john@gmail.com"
        "john underscore doe at gmail dot calm" → "john_doe@gmail.com"
        """
        result = text
        
        # Fix TLD typos/corrections in word form (before dot replacement)
        for wrong, correct in cls.TLD_CORRECTIONS.items():
            # Match "dot calm" -> "dot com"
            result = re.sub(rf'\bdot\s+{wrong}\b', f'dot {correct}', result, flags=re.IGNORECASE)
            # Match ".calm" -> ".com"
            result = re.sub(rf'\.{wrong}\b', f'.{correct}', result, flags=re.IGNORECASE)
        
        # Fix domain typos using regex patterns with word boundaries
        for pattern, correct in cls.DOMAIN_CORRECTIONS.items():
            result = re.sub(pattern, correct, result, flags=re.IGNORECASE)
        
        # Remove spaces around @ and around dots before TLD
        result = re.sub(r'\s*@\s*', '@', result)
        # Handle "yahoo .com" -> "yahoo.com" and "yahoo. com" -> "yahoo.com"
        result = re.sub(r'\s*\.\s*(com|org|net|edu|io|co|gov)\b', r'.\1', result)
        
        # Clean up any remaining spaces in email
        if '@' in result:
            parts = result.split('@')
            if len(parts) == 2:
                local = parts[0].replace(' ', '').strip()
                domain = parts[1].replace(' ', '').strip()
                
                # Remove invalid characters from local part
                local = re.sub(r'[^\w\.\-\+]', '', local)
                
                # Fix TLD typos in domain (one more pass after cleanup)
                for wrong, correct in cls.TLD_CORRECTIONS.items():
                    domain = re.sub(rf'\.{wrong}$', f'.{correct}', domain, flags=re.IGNORECASE)
                
                # Ensure domain has TLD
                if '.' not in domain:
                    domain_lower = domain.lower()
                    if domain_lower in ['gmail', 'geemail', 'gmal']:
                        domain = 'gmail.com'
                    elif domain_lower in ['yahoo', 'yaho']:
                        domain = 'yahoo.com'
                    elif domain_lower in ['hotmail', 'hotmale']:
                        domain = 'hotmail.com'
                    elif domain_lower in ['outlook']:
                        domain = 'outlook.com'
                    elif domain_lower in ['icloud']:
                        domain = 'icloud.com'
                
                result = f"{local}@{domain}"
        
        return result
    
    @classmethod
    def _normalize_phone(cls, text: str, context: Optional[Dict] = None) -> str:
        """
        ENHANCED: Normalize phone numbers with international support.
        
        Handles:
        - US: (555) 123-4567, 555-123-4567
        - UK: +44 20 7123 4567
        - India: +91 98765 43210
        - Generic international: +XX ...
        """
        result = text
        
        # Handle compound numbers like "twenty three" -> "23"
        result = cls._handle_compound_numbers(result)
        
        # Convert number words to digits
        for word, digit in cls.NUMBER_WORDS.items():
            result = re.sub(rf'\b{word}\b', digit, result, flags=re.IGNORECASE)
        
        # Extract just digits and plus sign
        digits = re.sub(r'[^\d+]', '', result)
        
        if not digits:
            return result
        
        # Use context to infer country code
        country_code = None
        if context and 'country' in context:
            country_map = {
                'US': '1', 'USA': '1', 'United States': '1',
                'UK': '44', 'GB': '44', 'United Kingdom': '44',
                'India': '91', 'IN': '91',
                'Canada': '1', 'CA': '1',
                'Australia': '61', 'AU': '61',
                'Germany': '49', 'DE': '49',
                'France': '33', 'FR': '33',
            }
            country_code = country_map.get(context['country'])
        
        # Format based on length and country
        if digits.startswith('+'):
            # Already has country code
            return cls._format_international_phone(digits)
        elif country_code:
            # Add inferred country code
            return cls._format_international_phone(f"+{country_code}{digits}")
        elif len(digits) >= 10:
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return digits if digits else result
    
    @classmethod
    def _format_international_phone(cls, phone: str) -> str:
        """NEW: Format international phone numbers properly."""
        if not phone.startswith('+'):
            return phone
        
        # Extract country code
        match = re.match(r'^\+(\d{1,3})(\d+)$', phone)
        if not match:
            return phone
        
        country, number = match.groups()
        
        # Format based on common patterns
        if country == '1':  # US/Canada
            if len(number) == 10:
                return f"+1 ({number[:3]}) {number[3:6]}-{number[6:]}"
        elif country == '44':  # UK
            if len(number) >= 10:
                return f"+44 {number[:2]} {number[2:6]} {number[6:]}"
        elif country == '91':  # India
            if len(number) == 10:
                return f"+91 {number[:5]} {number[5:]}"
        elif country == '61':  # Australia
            if len(number) == 9:
                return f"+61 {number[:1]} {number[1:5]} {number[5:]}"
        
        # Default formatting
        return f"+{country} {number}"
    
    @classmethod
    def _handle_compound_numbers(cls, text: str) -> str:
        """NEW: Handle compound numbers like 'twenty three' -> '23'."""
        compounds = {
            'twenty one': '21', 'twenty two': '22', 'twenty three': '23',
            'twenty four': '24', 'twenty five': '25', 'twenty six': '26',
            'twenty seven': '27', 'twenty eight': '28', 'twenty nine': '29',
            'thirty one': '31', 'thirty two': '32', 'thirty three': '33',
            'thirty four': '34', 'thirty five': '35', 'thirty six': '36',
            'thirty seven': '37', 'thirty eight': '38', 'thirty nine': '39',
            'forty one': '41', 'forty two': '42', 'forty three': '43',
            'forty four': '44', 'forty five': '45', 'forty six': '46',
            'forty seven': '47', 'forty eight': '48', 'forty nine': '49',
            'fifty one': '51', 'fifty two': '52', 'fifty three': '53',
            'fifty four': '54', 'fifty five': '55', 'fifty six': '56',
            'fifty seven': '57', 'fifty eight': '58', 'fifty nine': '59',
        }
        
        result = text.lower()
        for compound, digit in compounds.items():
            result = result.replace(compound, digit)
        
        return result
    
    @classmethod
    def _normalize_number(cls, text: str) -> str:
        """ENHANCED: Convert spoken numbers to digits."""
        result = text
        # Handle compound numbers first
        result = cls._handle_compound_numbers(result)
        # Then individual number words
        for word, digit in cls.NUMBER_WORDS.items():
            result = re.sub(rf'\b{word}\b', digit, result, flags=re.IGNORECASE)
        return result
    
    @classmethod
    def _normalize_date(cls, text: str) -> str:
        """
        NEW: Normalize date from voice input.
        
        Handles:
        - "january fifth twenty twenty four" -> "01/05/2024"
        - "first of march" -> "03/01/YYYY"
        - "march first" -> "03/01/YYYY"
        """
        result = text.lower()
        
        # Month names
        months = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05',
            'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09', 'sept': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12',
        }
        
        # Ordinal numbers
        ordinals = {
            'first': '1', 'second': '2', 'third': '3', 'fourth': '4',
            'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8',
            'ninth': '9', 'tenth': '10', 'eleventh': '11', 'twelfth': '12',
            'thirteenth': '13', 'fourteenth': '14', 'fifteenth': '15',
            'sixteenth': '16', 'seventeenth': '17', 'eighteenth': '18',
            'nineteenth': '19', 'twentieth': '20', 'twenty first': '21',
            'twenty second': '22', 'twenty third': '23', 'twenty fourth': '24',
            'twenty fifth': '25', 'twenty sixth': '26', 'twenty seventh': '27',
            'twenty eighth': '28', 'twenty ninth': '29', 'thirtieth': '30',
            'thirty first': '31',
        }
        
        # Replace ordinals
        for ordinal, num in ordinals.items():
            result = result.replace(ordinal, num)
        
        # Try to parse common formats
        for month_name, month_num in months.items():
            # "march 5 2024"
            pattern = rf'\b{month_name}\s+(\d+)\s+(\d{{4}})\b'
            match = re.search(pattern, result)
            if match:
                day, year = match.groups()
                return f"{month_num}/{day.zfill(2)}/{year}"
            
            # "5 march 2024"
            pattern = rf'\b(\d+)\s+{month_name}\s+(\d{{4}})\b'
            match = re.search(pattern, result)
            if match:
                day, year = match.groups()
                return f"{month_num}/{day.zfill(2)}/{year}"
            
            # "march 5" (no year)
            pattern = rf'\b{month_name}\s+(\d+)\b'
            match = re.search(pattern, result)
            if match:
                day = match.group(1)
                return f"{month_num}/{day.zfill(2)}"
        
        return result
    
    @classmethod
    def _normalize_address(cls, text: str) -> str:
        """
        NEW: Normalize addresses from voice.
        
        Handles:
        - Street abbreviations: "one two three main street" -> "123 Main St"
        - Cardinal directions: "north" -> "N"
        - Unit numbers: "apartment five" -> "Apt 5"
        """
        result = text
        
        # Convert number words in address
        result = cls._normalize_number(result)
        
        # Concatenate consecutive single digits at the start (street number)
        # "1 2 3 main" -> "123 main"
        words = result.split()
        street_number = []
        remaining_words = []
        in_number = True
        
        for word in words:
            if in_number and word.isdigit() and len(word) <= 2:
                street_number.append(word)
            else:
                in_number = False
                remaining_words.append(word)
        
        if street_number:
            result = ''.join(street_number) + ' ' + ' '.join(remaining_words)
        else:
            result = ' '.join(words)
        
        # Common address abbreviations
        abbrev = {
            'street': 'St',
            'avenue': 'Ave',
            'boulevard': 'Blvd',
            'road': 'Rd',
            'drive': 'Dr',
            'lane': 'Ln',
            'court': 'Ct',
            'place': 'Pl',
            'square': 'Sq',
            'apartment': 'Apt',
            'suite': 'Ste',
            'unit': 'Unit',
            'floor': 'Fl',
            'north': 'N',
            'south': 'S',
            'east': 'E',
            'west': 'W',
            'northeast': 'NE',
            'northwest': 'NW',
            'southeast': 'SE',
            'southwest': 'SW',
        }
        
        for full, abbr in abbrev.items():
            result = re.sub(rf'\b{full}\b', abbr, result, flags=re.IGNORECASE)
        
        # Capitalize properly
        words = result.split()
        result = ' '.join(word.capitalize() if not word.isdigit() else word for word in words)
        
        return result.strip()
    
    @classmethod
    def _normalize_name(cls, text: str) -> str:
        """
        NEW: Normalize names with better capitalization.
        
        Handles:
        - "john smith" -> "John Smith"
        - "mary jane o'connor" -> "Mary Jane O'Connor"
        - "james van der berg" -> "James Van Der Berg"
        """
        # Remove filler words
        result = re.sub(r'\b(is|my name is|i\'m|called|this is)\b', '', text, flags=re.IGNORECASE)
        result = result.strip()
        
        # Split into words
        words = result.split()
        
        # Capitalize each word
        capitalized = []
        for word in words:
            if '-' in word:
                # Handle hyphenated names: "mary-jane" -> "Mary-Jane"
                parts = word.split('-')
                word = '-'.join(p.capitalize() for p in parts)
            elif "'" in word:
                # Handle apostrophes: "o'connor" -> "O'Connor"
                parts = word.split("'")
                word = "'".join(p.capitalize() for p in parts)
            else:
                word = word.capitalize()
            
            capitalized.append(word)
        
        return ' '.join(capitalized)
    
    @classmethod
    def detect_hesitation(cls, text: str) -> bool:
        """
        ENHANCED: Detect if user is hesitating/struggling.
        
        Filler words indicate user needs help.
        """
        hesitation_markers = [
            'uh', 'um', 'hmm', 'uhh', 'umm', 'err', 'ah',
            'let me think', 'wait', 'hold on', 'one moment',
            "i'm not sure", 'what was it', 'i forget',
            'let me see', 'give me a second', 'hang on',
        ]
        text_lower = text.lower()
        
        # Check for markers
        has_markers = any(marker in text_lower for marker in hesitation_markers)
        
        # Check for repeated words (sign of uncertainty)
        words = text_lower.split()
        has_repeats = len(words) != len(set(words)) and len(words) > 2
        
        return has_markers or has_repeats
    
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
    
    @classmethod
    def calculate_confidence(
        cls,
        field_name: str,
        field_type: str,
        extracted_value: str,
        stt_confidence: float,
        context: Optional[Dict] = None
    ) -> float:
        """
        NEW: Multi-signal confidence calculation.
        
        Considers:
        1. STT confidence (base)
        2. Validation rules (format correctness)
        3. Context consistency (cross-field validation)
        4. Common patterns (expected formats)
        
        Args:
            field_name: Name of the field
            field_type: Type of the field
            extracted_value: The extracted/normalized value
            stt_confidence: Base confidence from STT engine
            context: Previous field values for cross-validation
            
        Returns:
            Adjusted confidence score (0.0-1.0)
        """
        # Start with STT confidence
        confidence = stt_confidence
        
        # Adjust based on validation
        if field_type == 'email':
            if cls._is_valid_email(extracted_value):
                confidence += 0.10
            else:
                confidence -= 0.20
        
        elif field_type in ['phone', 'tel']:
            if cls._is_valid_phone(extracted_value):
                confidence += 0.10
            else:
                confidence -= 0.20
        
        # Context consistency bonus
        if context and cls._is_contextually_consistent(
            field_name, field_type, extracted_value, context
        ):
            confidence += 0.05
        
        # Common pattern bonus
        if cls._matches_common_pattern(field_type, extracted_value):
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
    
    @classmethod
    def _is_valid_email(cls, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @classmethod
    def _is_valid_phone(cls, phone: str) -> bool:
        """Validate phone format."""
        # Remove formatting
        digits = re.sub(r'[^\d]', '', phone)
        # Check length (10-15 digits is reasonable)
        return 10 <= len(digits) <= 15
    
    @classmethod
    def _is_contextually_consistent(
        cls, field_name: str, field_type: str, value: str, context: Dict
    ) -> bool:
        """
        NEW: Check if value is consistent with context.
        
        Example: If email domain is "company.com" and company name
        is "Company Inc", that's consistent.
        """
        if field_type == 'email' and 'company' in context:
            company = context['company']
            if company:
                company_clean = company.lower().replace(' ', '').replace('inc', '').replace('llc', '')
                if '@' in value:
                    domain = value.split('@')[1].split('.')[0].lower()
                    # Check if company name appears in domain
                    return company_clean.startswith(domain) or domain.startswith(company_clean[:3])
        
        return False
    
    @classmethod
    def _matches_common_pattern(cls, field_type: str, value: str) -> bool:
        """Check if value matches common patterns for the field type."""
        if field_type == 'name':
            # Names typically have 1-4 words, each starting with capital
            words = value.split()
            return (
                1 <= len(words) <= 4 and
                all(w[0].isupper() for w in words if w)
            )
        
        return False


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


# =============================================================================
# Phonetic Matcher - Name Similarity
# =============================================================================

class PhoneticMatcher:
    """
    NEW: Match names phonetically for better STT error handling.
    
    Uses a Soundex-like algorithm to match similar-sounding names:
    - "Jon" matches "John"
    - "Caitlyn" matches "Katelyn"
    - "Steven" matches "Stephen"
    """
    
    @classmethod
    def get_phonetic_key(cls, name: str) -> str:
        """
        Generate phonetic key for name matching.
        Simplified Soundex-like algorithm.
        
        Args:
            name: Name to generate key for
            
        Returns:
            4-character phonetic key
        """
        name = name.lower().strip()
        if not name:
            return ""
        
        # Remove non-letters
        name = re.sub(r'[^a-z]', '', name)
        
        if not name:
            return ""
        
        # Keep first letter
        key = name[0]
        
        # Map similar sounds to numbers
        soundex_map = {
            'b': '1', 'f': '1', 'p': '1', 'v': '1',
            'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
            'd': '3', 't': '3',
            'l': '4',
            'm': '5', 'n': '5',
            'r': '6'
        }
        
        prev_code = None
        for char in name[1:]:
            code = soundex_map.get(char, '0')
            if code != '0' and code != prev_code:
                key += code
                prev_code = code
        
        return key[:4].ljust(4, '0')
    
    @classmethod
    def are_similar(cls, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """
        Check if two names are phonetically similar.
        
        Args:
            name1: First name to compare
            name2: Second name to compare
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            True if names are similar enough
        """
        # Exact match (case-insensitive)
        if name1.lower().strip() == name2.lower().strip():
            return True
        
        # Phonetic match (Soundex keys are equal)
        if cls.get_phonetic_key(name1) == cls.get_phonetic_key(name2):
            return True
        
        # Fuzzy string match using difflib
        similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        return similarity >= threshold
    
    @classmethod
    def find_best_match(cls, name: str, candidates: List[str], threshold: float = 0.8) -> Optional[str]:
        """
        Find the best matching name from a list of candidates.
        
        Args:
            name: Name to match
            candidates: List of candidate names
            threshold: Minimum similarity threshold
            
        Returns:
            Best matching candidate or None
        """
        if not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            # Check phonetic match first
            if cls.get_phonetic_key(name) == cls.get_phonetic_key(candidate):
                return candidate  # Phonetic match is very strong
            
            # Calculate fuzzy similarity
            similarity = difflib.SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = candidate
        
        return best_match
