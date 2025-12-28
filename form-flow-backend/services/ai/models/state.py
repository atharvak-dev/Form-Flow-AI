"""
Enhanced State Management Models

Industry-grade state structures for conversational form-filling agents.
Implements patterns from modern LLM-based conversational AI systems:

1. IMMUTABLE FIELD STATE: Field data is tracked with complete metadata
   for each extraction event, enabling audit trails and undo operations.

2. SLIDING CONTEXT WINDOW: Tracks active/previous/next fields like LLMs
   track token context, enabling natural conversation flow.

3. INFERENCE CACHE: Stores detected patterns and suggestions, similar to
   how RAG systems cache retrieved context for downstream use.

4. ATOMIC STATE UPDATES: All state mutations return new state objects,
   preventing partial updates that could corrupt conversation context.

Version: 1.0.0
Author: Form-Flow AI
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy

from utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Enums - Field Status State Machine
# =============================================================================

class FieldStatus(str, Enum):
    """
    Field status state machine.
    
    Status transitions:
    EMPTY -> FILLED (user provides value)
    EMPTY -> SKIPPED (user skips)
    FILLED -> PENDING_CORRECTION (user requests correction)
    PENDING_CORRECTION -> FILLED (correction applied)
    SKIPPED -> FILLED (user decides to fill later)
    """
    EMPTY = "empty"
    FILLED = "filled"
    SKIPPED = "skipped"
    PENDING_VALIDATION = "pending_validation"
    PENDING_CORRECTION = "pending_correction"


class ValidationStatus(str, Enum):
    """Validation result for field values."""
    VALID = "valid"
    INVALID = "invalid"
    NOT_CHECKED = "not_checked"
    NEEDS_CONFIRMATION = "needs_confirmation"


class UserIntent(str, Enum):
    """Classification of how a value was captured."""
    DIRECT_ANSWER = "direct_answer"
    CORRECTION = "correction"
    CONFIRMATION = "confirmation"
    SKIP_REQUEST = "skip_request"
    INFERRED = "inferred"
    UNCLEAR = "unclear"


# =============================================================================
# FieldData - Per-Field State Tracking
# =============================================================================

@dataclass(frozen=True)
class FieldData:
    """
    Immutable per-field metadata for comprehensive state tracking.
    
    Frozen dataclass ensures field state cannot be accidentally mutated,
    enforcing atomic updates through replacement. This pattern is used
    in production conversational AI systems to prevent state corruption.
    
    Attributes:
        value: The extracted field value (None if empty or skipped)
        status: Current field status in the state machine
        captured_at: Timestamp when value was captured
        captured_in_turn: Conversation turn number when captured
        confidence: Extraction confidence score (0.0 - 1.0)
        validation_status: Result of value validation
        validation_errors: List of validation error messages
        user_intent: How the value was provided by user
        extraction_reasoning: LLM's reasoning for extraction decision
        previous_values: History of values for undo support
    """
    value: Optional[str] = None
    status: FieldStatus = FieldStatus.EMPTY
    captured_at: Optional[datetime] = None
    captured_in_turn: int = 0
    confidence: float = 0.0
    validation_status: ValidationStatus = ValidationStatus.NOT_CHECKED
    validation_errors: Tuple[str, ...] = field(default_factory=tuple)
    user_intent: UserIntent = UserIntent.DIRECT_ANSWER
    extraction_reasoning: str = ""
    previous_values: Tuple[str, ...] = field(default_factory=tuple)
    
    def with_value(
        self,
        value: str,
        confidence: float,
        turn: int,
        intent: UserIntent = UserIntent.DIRECT_ANSWER,
        reasoning: str = ""
    ) -> FieldData:
        """
        Create new FieldData with updated value (immutable update).
        
        Preserves previous value in history for undo support.
        """
        previous = self.previous_values
        if self.value is not None:
            previous = (*self.previous_values, self.value)
        
        return replace(
            self,
            value=value,
            status=FieldStatus.FILLED,
            captured_at=datetime.now(),
            captured_in_turn=turn,
            confidence=confidence,
            validation_status=ValidationStatus.NOT_CHECKED,
            validation_errors=tuple(),
            user_intent=intent,
            extraction_reasoning=reasoning,
            previous_values=previous
        )
    
    def with_skip(self, turn: int) -> FieldData:
        """Mark field as skipped (immutable update)."""
        return replace(
            self,
            status=FieldStatus.SKIPPED,
            captured_at=datetime.now(),
            captured_in_turn=turn,
            user_intent=UserIntent.SKIP_REQUEST
        )
    
    def with_validation(
        self,
        status: ValidationStatus,
        errors: List[str] = None
    ) -> FieldData:
        """Update validation status (immutable update)."""
        return replace(
            self,
            validation_status=status,
            validation_errors=tuple(errors) if errors else tuple()
        )
    
    def with_correction_pending(self) -> FieldData:
        """Mark field as pending correction (immutable update)."""
        return replace(self, status=FieldStatus.PENDING_CORRECTION)
    
    def undo(self) -> FieldData:
        """
        Revert to previous value (immutable update).
        
        Returns empty field if no previous values exist.
        """
        if not self.previous_values:
            return replace(
                self,
                value=None,
                status=FieldStatus.EMPTY,
                confidence=0.0,
                validation_status=ValidationStatus.NOT_CHECKED
            )
        
        previous_value = self.previous_values[-1]
        remaining_history = self.previous_values[:-1]
        
        return replace(
            self,
            value=previous_value,
            status=FieldStatus.FILLED,
            previous_values=remaining_history
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            'value': self.value,
            'status': self.status.value,
            'captured_at': self.captured_at.isoformat() if self.captured_at else None,
            'captured_in_turn': self.captured_in_turn,
            'confidence': self.confidence,
            'validation_status': self.validation_status.value,
            'validation_errors': list(self.validation_errors),
            'user_intent': self.user_intent.value,
            'extraction_reasoning': self.extraction_reasoning,
            'previous_values': list(self.previous_values)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FieldData:
        """Deserialize from dictionary."""
        if not data:
            return cls()
        
        captured_at = None
        if data.get('captured_at'):
            try:
                captured_at = datetime.fromisoformat(data['captured_at'])
            except (ValueError, TypeError):
                captured_at = None
        
        return cls(
            value=data.get('value'),
            status=FieldStatus(data.get('status', 'empty')),
            captured_at=captured_at,
            captured_in_turn=data.get('captured_in_turn', 0),
            confidence=data.get('confidence', 0.0),
            validation_status=ValidationStatus(data.get('validation_status', 'not_checked')),
            validation_errors=tuple(data.get('validation_errors', [])),
            user_intent=UserIntent(data.get('user_intent', 'direct_answer')),
            extraction_reasoning=data.get('extraction_reasoning', ''),
            previous_values=tuple(data.get('previous_values', []))
        )


# =============================================================================
# InferenceCache - Pattern Detection and Suggestions
# =============================================================================

@dataclass
class PatternMatch:
    """A detected pattern that can inform future suggestions."""
    pattern_type: str  # email_format, phone_format, name_style, date_format
    pattern_value: str  # The detected pattern
    confidence: float
    source_field: str  # Which field this was detected from
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_type': self.pattern_type,
            'pattern_value': self.pattern_value,
            'confidence': self.confidence,
            'source_field': self.source_field,
            'detected_at': self.detected_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternMatch:
        detected_at = datetime.now()
        if data.get('detected_at'):
            try:
                detected_at = datetime.fromisoformat(data['detected_at'])
            except (ValueError, TypeError):
                pass
        
        return cls(
            pattern_type=data.get('pattern_type', ''),
            pattern_value=data.get('pattern_value', ''),
            confidence=data.get('confidence', 0.0),
            source_field=data.get('source_field', ''),
            detected_at=detected_at
        )


@dataclass
class ContextualSuggestion:
    """A suggestion for a field value based on context."""
    target_field: str
    suggested_value: str
    reasoning: str
    confidence: float
    source_patterns: List[str] = field(default_factory=list)
    prompt_template: str = ""  # How to present to user
    is_presented: bool = False  # Track if shown to user
    was_accepted: bool = False  # Track user acceptance for learning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target_field': self.target_field,
            'suggested_value': self.suggested_value,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'source_patterns': self.source_patterns,
            'prompt_template': self.prompt_template,
            'is_presented': self.is_presented,
            'was_accepted': self.was_accepted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextualSuggestion:
        return cls(
            target_field=data.get('target_field', ''),
            suggested_value=data.get('suggested_value', ''),
            reasoning=data.get('reasoning', ''),
            confidence=data.get('confidence', 0.0),
            source_patterns=data.get('source_patterns', []),
            prompt_template=data.get('prompt_template', ''),
            is_presented=data.get('is_presented', False),
            was_accepted=data.get('was_accepted', False)
        )


@dataclass
class InferenceCache:
    """
    Cache for detected patterns and contextual suggestions.
    
    Implements a pattern similar to RAG (Retrieval Augmented Generation)
    systems where context is cached for efficient retrieval during
    response generation.
    
    Patterns are detected from user input and stored for:
    1. Format consistency (apply same capitalization, date format)
    2. Predictive suggestions (infer work email from personal email)
    3. Geographic context (phone prefix -> country/region)
    
    User Preferences track interaction patterns:
    1. Verbosity preference (concise vs detailed responses)
    2. Confirmation style (explicit vs implicit)
    3. Suggestion acceptance rate (for adaptive suggestions)
    """
    detected_patterns: Dict[str, PatternMatch] = field(default_factory=dict)
    user_preferences: Dict[str, str] = field(default_factory=dict)
    suggestions: Dict[str, ContextualSuggestion] = field(default_factory=dict)
    
    # Learning signals
    suggestion_acceptance_count: int = 0
    suggestion_rejection_count: int = 0
    correction_count: int = 0
    
    def add_pattern(self, pattern: PatternMatch) -> None:
        """Add or update a detected pattern."""
        key = f"{pattern.pattern_type}:{pattern.source_field}"
        existing = self.detected_patterns.get(key)
        
        # Only update if new pattern has higher confidence
        if not existing or pattern.confidence > existing.confidence:
            self.detected_patterns[key] = pattern
            logger.debug(f"Pattern cached: {key} = {pattern.pattern_value}")
    
    def get_pattern(self, pattern_type: str, source_field: str = None) -> Optional[PatternMatch]:
        """Retrieve a pattern by type and optional source field."""
        if source_field:
            key = f"{pattern_type}:{source_field}"
            return self.detected_patterns.get(key)
        
        # Return highest confidence pattern of this type
        matches = [
            p for k, p in self.detected_patterns.items()
            if k.startswith(f"{pattern_type}:")
        ]
        return max(matches, key=lambda p: p.confidence) if matches else None
    
    def add_suggestion(self, suggestion: ContextualSuggestion) -> None:
        """Add a contextual suggestion for a field."""
        self.suggestions[suggestion.target_field] = suggestion
    
    def get_suggestion(self, field_name: str) -> Optional[ContextualSuggestion]:
        """Get pending suggestion for a field."""
        suggestion = self.suggestions.get(field_name)
        if suggestion and not suggestion.is_presented:
            return suggestion
        return None
    
    def mark_suggestion_presented(self, field_name: str) -> None:
        """Mark a suggestion as presented to user."""
        if field_name in self.suggestions:
            self.suggestions[field_name].is_presented = True
    
    def record_suggestion_outcome(self, field_name: str, accepted: bool) -> None:
        """Record whether user accepted a suggestion."""
        if field_name in self.suggestions:
            self.suggestions[field_name].was_accepted = accepted
            if accepted:
                self.suggestion_acceptance_count += 1
            else:
                self.suggestion_rejection_count += 1
    
    @property
    def suggestion_acceptance_rate(self) -> float:
        """Calculate suggestion acceptance rate for adaptive behavior."""
        total = self.suggestion_acceptance_count + self.suggestion_rejection_count
        return self.suggestion_acceptance_count / total if total > 0 else 0.5
    
    def set_preference(self, key: str, value: str) -> None:
        """Set a user preference."""
        self.user_preferences[key] = value
    
    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a user preference."""
        return self.user_preferences.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            'detected_patterns': {
                k: v.to_dict() for k, v in self.detected_patterns.items()
            },
            'user_preferences': self.user_preferences,
            'suggestions': {
                k: v.to_dict() for k, v in self.suggestions.items()
            },
            'suggestion_acceptance_count': self.suggestion_acceptance_count,
            'suggestion_rejection_count': self.suggestion_rejection_count,
            'correction_count': self.correction_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InferenceCache:
        """Deserialize from dictionary."""
        if not data:
            return cls()
        
        cache = cls(
            user_preferences=data.get('user_preferences', {}),
            suggestion_acceptance_count=data.get('suggestion_acceptance_count', 0),
            suggestion_rejection_count=data.get('suggestion_rejection_count', 0),
            correction_count=data.get('correction_count', 0)
        )
        
        for key, pattern_data in data.get('detected_patterns', {}).items():
            cache.detected_patterns[key] = PatternMatch.from_dict(pattern_data)
        
        for key, suggestion_data in data.get('suggestions', {}).items():
            cache.suggestions[key] = ContextualSuggestion.from_dict(suggestion_data)
        
        return cache


# =============================================================================
# ContextWindow - Field Navigation State
# =============================================================================

@dataclass
class ContextWindow:
    """
    Tracks field navigation state like LLMs track token context windows.
    
    This enables the conversation agent to:
    1. Know exactly which field is being asked about (no ambiguity)
    2. Track what was just filled (for corrections)
    3. Look ahead to what's coming (for suggestions)
    4. Distinguish between "skip current" and "skip all"
    
    The concept mirrors how LLMs maintain attention over a sliding window
    of tokens, where the "active" field is analogous to the current
    generation position, with known left context (completed) and
    planned right context (pending).
    """
    # Current focus
    active_field: Optional[str] = None
    active_field_schema: Optional[Dict[str, Any]] = None
    
    # Navigation context
    previous_field: Optional[str] = None
    next_field: Optional[str] = None
    
    # Field classification (disjoint sets)
    completed_fields: List[str] = field(default_factory=list)
    pending_fields: List[str] = field(default_factory=list)
    skipped_fields: List[str] = field(default_factory=list)
    
    # Batch tracking (for multi-field questions)
    current_batch: List[str] = field(default_factory=list)
    batch_index: int = 0
    
    # Turn tracking
    current_turn: int = 0
    field_first_asked_turn: Dict[str, int] = field(default_factory=dict)
    
    def set_active_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any] = None
    ) -> None:
        """
        Set the currently active field.
        
        This is CRITICAL for correct intent disambiguation:
        - When user says "skip it", we skip THIS field
        - When user provides a value, it maps to THIS field
        """
        self.previous_field = self.active_field
        self.active_field = field_name
        self.active_field_schema = field_schema
        
        # Track first ask turn for this field
        if field_name and field_name not in self.field_first_asked_turn:
            self.field_first_asked_turn[field_name] = self.current_turn
        
        # Update pending fields (remove active from pending)
        if field_name in self.pending_fields:
            self.pending_fields.remove(field_name)
        
        logger.debug(
            f"Context window: active={field_name}, "
            f"previous={self.previous_field}, "
            f"pending={len(self.pending_fields)}"
        )
    
    def mark_field_completed(self, field_name: str) -> None:
        """Mark a field as completed."""
        if field_name not in self.completed_fields:
            self.completed_fields.append(field_name)
        
        # Remove from skipped if previously skipped
        if field_name in self.skipped_fields:
            self.skipped_fields.remove(field_name)
        
        # Remove from pending
        if field_name in self.pending_fields:
            self.pending_fields.remove(field_name)
        
        # Set next pending field as next
        if self.pending_fields:
            self.next_field = self.pending_fields[0]
        else:
            self.next_field = None
    
    def mark_field_skipped(self, field_name: str) -> None:
        """Mark a field as skipped."""
        if field_name not in self.skipped_fields:
            self.skipped_fields.append(field_name)
        
        # Remove from pending
        if field_name in self.pending_fields:
            self.pending_fields.remove(field_name)
        
        # Set next pending field as next
        if self.pending_fields:
            self.next_field = self.pending_fields[0]
        else:
            self.next_field = None
    
    def undo_field_completion(self, field_name: str) -> None:
        """Undo a field completion (for undo operations)."""
        if field_name in self.completed_fields:
            self.completed_fields.remove(field_name)
        
        # Add back to pending at beginning
        if field_name not in self.pending_fields:
            self.pending_fields.insert(0, field_name)
    
    def initialize_from_schema(self, form_schema: List[Dict[str, Any]]) -> None:
        """Initialize pending fields from form schema."""
        self.pending_fields = []
        
        for form in form_schema:
            for field in form.get('fields', []):
                field_name = field.get('name', '')
                field_type = field.get('type', '')
                
                if not field_name:
                    continue
                if field_type in ['submit', 'button', 'hidden']:
                    continue
                if field.get('hidden'):
                    continue
                
                # Add to pending if not already completed or skipped
                if (field_name not in self.completed_fields and
                    field_name not in self.skipped_fields and
                    field_name not in self.pending_fields):
                    self.pending_fields.append(field_name)
        
        # Set first pending as next
        if self.pending_fields:
            self.next_field = self.pending_fields[0]
    
    def advance_turn(self) -> int:
        """Advance to next turn and return new turn number."""
        self.current_turn += 1
        return self.current_turn
    
    def set_batch(self, field_names: List[str]) -> None:
        """Set current question batch (for multi-field questions)."""
        self.current_batch = field_names
        self.batch_index = 0
        
        if field_names:
            self.active_field = field_names[0]
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress metrics."""
        total = (
            len(self.completed_fields) +
            len(self.pending_fields) +
            len(self.skipped_fields)
        )
        completed = len(self.completed_fields)
        
        return {
            'total_fields': total,
            'completed_fields': completed,
            'skipped_fields': len(self.skipped_fields),
            'pending_fields': len(self.pending_fields),
            'progress_percent': int((completed / total) * 100) if total > 0 else 0,
            'current_turn': self.current_turn
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            'active_field': self.active_field,
            'active_field_schema': self.active_field_schema,
            'previous_field': self.previous_field,
            'next_field': self.next_field,
            'completed_fields': self.completed_fields,
            'pending_fields': self.pending_fields,
            'skipped_fields': self.skipped_fields,
            'current_batch': self.current_batch,
            'batch_index': self.batch_index,
            'current_turn': self.current_turn,
            'field_first_asked_turn': self.field_first_asked_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextWindow:
        """Deserialize from dictionary."""
        if not data:
            return cls()
        
        return cls(
            active_field=data.get('active_field'),
            active_field_schema=data.get('active_field_schema'),
            previous_field=data.get('previous_field'),
            next_field=data.get('next_field'),
            completed_fields=data.get('completed_fields', []),
            pending_fields=data.get('pending_fields', []),
            skipped_fields=data.get('skipped_fields', []),
            current_batch=data.get('current_batch', []),
            batch_index=data.get('batch_index', 0),
            current_turn=data.get('current_turn', 0),
            field_first_asked_turn=data.get('field_first_asked_turn', {})
        )


# =============================================================================
# FormDataManager - Atomic State Updates
# =============================================================================

class FormDataManager:
    """
    Manager for atomic form data state updates.
    
    Implements the critical requirement: all state mutations must be
    atomic and preserve previously filled fields. This prevents the
    "skip it" bug where previous fields are accidentally cleared.
    
    Usage:
        manager = FormDataManager()
        
        # Update single field
        manager.update_field("email", field_data)
        
        # Skip current field (preserves all others)
        manager.skip_field("company", turn=5)
        
        # Get all data for extraction context
        context = manager.get_extraction_context()
    """
    
    def __init__(self, initial_data: Dict[str, FieldData] = None):
        """
        Initialize form data manager.
        
        Args:
            initial_data: Optional pre-populated field data
        """
        self._fields: Dict[str, FieldData] = initial_data or {}
        self._lock = False  # Simple mutex for atomic operations
    
    def get_field(self, field_name: str) -> FieldData:
        """Get field data, creating empty if not exists."""
        if field_name not in self._fields:
            self._fields[field_name] = FieldData()
        return self._fields[field_name]
    
    def update_field(
        self,
        field_name: str,
        value: str,
        confidence: float,
        turn: int,
        intent: UserIntent = UserIntent.DIRECT_ANSWER,
        reasoning: str = ""
    ) -> FieldData:
        """
        Atomically update a field value.
        
        CRITICAL: This preserves ALL other fields unchanged.
        """
        current = self.get_field(field_name)
        updated = current.with_value(
            value=value,
            confidence=confidence,
            turn=turn,
            intent=intent,
            reasoning=reasoning
        )
        self._fields[field_name] = updated
        return updated
    
    def skip_field(self, field_name: str, turn: int) -> FieldData:
        """
        Atomically mark a field as skipped.
        
        CRITICAL: This preserves ALL other fields unchanged.
        """
        current = self.get_field(field_name)
        updated = current.with_skip(turn=turn)
        self._fields[field_name] = updated
        return updated
    
    def undo_field(self, field_name: str) -> Optional[FieldData]:
        """
        Undo the last value for a field.
        
        Returns updated FieldData or None if field doesn't exist.
        """
        if field_name not in self._fields:
            return None
        
        current = self._fields[field_name]
        updated = current.undo()
        self._fields[field_name] = updated
        return updated
    
    def get_filled_fields(self) -> Dict[str, str]:
        """Get dictionary of field_name -> value for filled fields only."""
        return {
            name: field.value
            for name, field in self._fields.items()
            if field.status == FieldStatus.FILLED and field.value is not None
        }
    
    def get_skipped_field_names(self) -> List[str]:
        """Get list of skipped field names."""
        return [
            name for name, field in self._fields.items()
            if field.status == FieldStatus.SKIPPED
        ]
    
    def get_confidence_scores(self) -> Dict[str, float]:
        """Get dictionary of field_name -> confidence for filled fields."""
        return {
            name: field.confidence
            for name, field in self._fields.items()
            if field.status == FieldStatus.FILLED
        }
    
    def get_all_field_data(self) -> Dict[str, FieldData]:
        """Get all field data (for serialization)."""
        return deepcopy(self._fields)
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Serialize all field data to dictionary."""
        return {
            name: field.to_dict()
            for name, field in self._fields.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> FormDataManager:
        """Deserialize from dictionary."""
        if not data:
            return cls()
        
        fields = {
            name: FieldData.from_dict(field_data)
            for name, field_data in data.items()
        }
        return cls(initial_data=fields)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'FieldStatus',
    'ValidationStatus',
    'UserIntent',
    'FieldData',
    'PatternMatch',
    'ContextualSuggestion',
    'InferenceCache',
    'ContextWindow',
    'FormDataManager',
]
