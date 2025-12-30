"""
Text Fitter - Intelligent Text Compression

Fits text into space-constrained PDF form fields using multiple strategies:
1. Direct fit (if text already fits)
2. Standard abbreviations (Street→St, Avenue→Ave)
3. Remove middle names/initials
4. Multi-line wrapping
5. Font size reduction
6. LLM-based intelligent compression

Features:
- Abbreviation dictionaries for addresses, titles, dates
- Font-aware character capacity calculation
- Graceful degradation with multiple fallback strategies
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from difflib import SequenceMatcher

# Enterprise Infrastructure
from .utils import get_logger, benchmark
from .domain import FieldContext
from .abbreviations import get_abbreviations
from services.ai.local_llm import get_local_llm_service, LocalLLMService

logger = get_logger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class FitResult:
    """Result of text fitting operation."""
    original: str
    fitted: str
    strategy_used: str
    score: float = 0.0  # Quality score (0.0 - 1.0)
    font_size: Optional[float] = None
    truncated: bool = False
    overflow: bool = False
    changes_made: List[str] = field(default_factory=list)
    
    @property
    def was_modified(self) -> bool:
        return self.original != self.fitted


class LLMTextCompressor:
    """Uses Local LLM Service to compress text intelligently."""
    
    def __init__(self):
        # Lazy load service to avoid startup overhead
        self._service: Optional[LocalLLMService] = None
        
    @property
    def service(self) -> Optional[LocalLLMService]:
        if not self._service:
            # Try to get service, might return None if disabled/failed
            self._service = get_local_llm_service()
        return self._service
        
    def compress(self, text: str, max_chars: int, field_context: Dict[str, Any]) -> Optional[str]:
        """
        Compress text using LLM.
        
        Args:
            text: Text to compress
            max_chars: Target character count
            field_context: Metadata about the field
            
        Returns:
            Compressed string if successful, None otherwise
        """
        service = self.service
        if not service:
            return None
            
        field_label = field_context.get("label", "field")
        field_type = field_context.get("type", "text")
        
        # We construct a prompt for the Local LLM's extraction/generation capability
        # The LocalLLMService is optimized for field extraction but can handle
        # simple instruction following if the prompt is structured right.
        prompt = f"""
        Compress this text to under {max_chars} characters for a {field_type} field named "{field_label}".
        Keep all key info. Use standard abbreviations.
        Original: "{text}"
        Compressed:
        """
        
        try:
            # We use the raw generation capability or 'extract_field_value' wrapper?
            # extract_field_value expects 'user_input' and 'field_name'.
            
            result = service.extract_field_value(
                user_input=text,
                field_name=f"compressed version (max {max_chars} chars)"
            )
            
            compressed = result.get("value", "").strip()
            
            # Validate result
            if compressed and len(compressed) <= max_chars and len(compressed) > 0:
                # Basic sanity check: shouldn't be completely different
                ratio = SequenceMatcher(None, text, compressed).ratio()
                if ratio > 0.1: # At least some similarity
                    return compressed
            
        except Exception as e:
            logger.warning(f"LLM compression failed: {e}")
            
        return None


# =============================================================================
# Text Fitter Class
# =============================================================================

class TextFitter:
    """
    Intelligent text fitter for space-constrained form fields.
    
    Uses a multi-strategy competitive approach:
    1. Try multiple compression strategies (abbreviation, stopwords, LLM, etc.)
    2. Score each result based on length, readability, and info retention.
    3. Select the best valid result.
    """
    
    MIN_FONT_SIZE = 6.0
    
    def __init__(self, domain: str = "general"):
        self.abbreviations = get_abbreviations(domain)
        self.llm_compressor = LLMTextCompressor()
        
    def fit(
        self,
        text: str,
        max_chars: int,
        field_context: Optional[Dict[str, Any]] = None,
        allow_truncation: bool = True,
    ) -> FitResult:
        """
        Fit text to field constraints using best strategy.
        """
        if not text:
             return FitResult(text, text, "empty")
             
        field_context = field_context or {}
        original = text.strip()
        
        # 1. Check if direct fit works
        if len(original) <= max_chars:
            return FitResult(original, original, "direct_fit", score=1.0)
            
        # 2. Gather Candidates
        candidates: List[FitResult] = []
        
        # Strategy A: Abbreviations
        abbr_text = self._apply_abbreviations(original)
        if len(abbr_text) <= max_chars:
            candidates.append(FitResult(
                original, abbr_text, "abbreviations", 
                score=self._calculate_score(original, abbr_text),
                changes_made=["Applied abbreviations"]
            ))
            
        # Strategy B: Stop Word Removal (on top of abbreviations)
        stop_text = self._remove_stop_words(abbr_text)
        if len(stop_text) <= max_chars:
             candidates.append(FitResult(
                original, stop_text, "stop_words",
                score=self._calculate_score(original, stop_text) * 0.95, # Slight penalty
                changes_made=["Removed stop words"]
            ))
        
        # Strategy C: Address Compression (Specific)
        if field_context.get("type") == "address" or field_context.get("purpose") == "address":
            addr_text = self._compress_address_structured(original, max_chars)
            if len(addr_text) <= max_chars:
                candidates.append(FitResult(
                    original, addr_text, "structured_address",
                    score=0.98, # High confidence in structured rule
                    changes_made=["Structured address compression"]
                ))
                
        # Strategy D: LLM Compression (Slowest/Most expensive, try last if nothing else fits well)
        # Only try if we don't have a good candidate yet or if we really need semantic compression
        if not candidates or all(c.score < 0.8 for c in candidates):
            llm_text = self.llm_compressor.compress(original, max_chars, field_context)
            if llm_text:
                candidates.append(FitResult(
                    original, llm_text, "llm_compression",
                    score=self._calculate_score(original, llm_text),
                    changes_made=["AI semantic compression"]
                ))
        
        # 3. Select Best Candidate
        if candidates:
            # Sort by score desc
            candidates.sort(key=lambda x: x.score, reverse=True)
            return candidates[0]
            
        # 4. Fallbacks (Truncation)
        if allow_truncation:
            truncated = original[:max_chars-3].strip() + "..."
            return FitResult(
                original, truncated, "truncation", 
                score=0.1, truncated=True, 
                changes_made=["Truncated"]
            )
            
        # Hard fail
        return FitResult(
            original, original[:max_chars], "hard_cut", 
            score=0.0, truncated=True, overflow=True
        )

    def _apply_abbreviations(self, text: str) -> str:
        """Apply dictionary substitutions."""
        result = text
        # Sort keys by length to replace longest matches first
        sorted_keys = sorted(self.abbreviations.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            # Whole word match only
            pattern = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
            result = pattern.sub(self.abbreviations[key], result)
            
        return result

    def _remove_stop_words(self, text: str) -> str:
        """Remove common Non-essential words."""
        stops = {'the', 'a', 'an', 'and', 'or', 'of', 'for', 'with', 'in', 'on', 'at', 'by'}
        return " ".join([w for w in text.split() if w.lower() not in stops])

    def _compress_address_structured(self, text: str, max_chars: int) -> str:
        """Heuristic compression for addresses."""
        # 1. Standard abbreviations
        temp = self._apply_abbreviations(text)
        if len(temp) <= max_chars: return temp
        
        # 2. Remove zip extension (12345-6789 -> 12345)
        temp = re.sub(r'-\d{4}\b', '', temp)
        if len(temp) <= max_chars: return temp
        
        # 3. Remove "USA", "United States"
        temp = re.sub(r',\s*(USA|US|United States)\b', '', temp)
        if len(temp) <= max_chars: return temp
        
        return temp

    def _calculate_score(self, original: str, fitted: str) -> float:
        """Score the quality of the fit (0.0 to 1.0)."""
        if not fitted: return 0.0
        
        # Length Penalty (too short might mean info loss)
        len_ratio = len(fitted) / len(original)
        if len_ratio < 0.2: return 0.4 # Suspiciously short
        
        # Similarity Reward (Levenshtein based)
        # We assume higher similarity = better preservation of meaning
        # taking into account expected compression
        similarity = SequenceMatcher(None, original.lower(), fitted.lower()).ratio()
        
        # We expect some difference, so raw similarity isn't 1.0
        # But we want to penalize drastic changes unless LLM does it
        return min(1.0, similarity + 0.3) # Boost slightly as we expect shrinking


# =============================================================================
# Helper Functions
# =============================================================================

def fit_text(text: str, max_chars: int, field_context: Dict = None) -> FitResult:
    return TextFitter().fit(text, max_chars, field_context)
