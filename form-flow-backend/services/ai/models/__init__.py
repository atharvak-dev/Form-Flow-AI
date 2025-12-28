"""
Models Package

Data models for conversation agent.
"""

from services.ai.models.session import ConversationSession
from services.ai.models.response import AgentResponse
from services.ai.models.state import (
    FieldStatus,
    ValidationStatus,
    UserIntent,
    FieldData,
    PatternMatch,
    ContextualSuggestion,
    InferenceCache,
    ContextWindow,
    FormDataManager,
)

__all__ = [
    # Core models
    'ConversationSession',
    'AgentResponse',
    # Enhanced state management
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

