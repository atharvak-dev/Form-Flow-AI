"""
Webhook Schemas Module

Defines Pydantic schemas for webhook events and payloads.

Usage:
    from services.webhook.schemas import FormEventType, FormSubmissionCompletedPayload
"""

from typing import Literal, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


# =============================================================================
# Event Types
# =============================================================================

class FormEventType(str, Enum):
    """
    All supported form submission event types.
    
    Validates: Requirements 5.1-5.6
    """
    SUBMISSION_STARTED = "form.submission_started"
    SUBMISSION_IN_PROGRESS = "form.submission_in_progress"
    SUBMISSION_COMPLETED = "form.submission_completed"
    SUBMISSION_FAILED = "form.submission_failed"
    FORM_SCRAPED = "form.scraped"
    FORM_VALIDATION_ERROR = "form.validation_error"


# =============================================================================
# Payload Schemas
# =============================================================================

class FormSubmissionStartedPayload(BaseModel):
    """
    Payload for form.submission_started event.
    
    Validates: Requirements 6.1-6.4
    """
    event: Literal["form.submission_started"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, user_id, fields_count"
    )
    signature: Optional[str] = None


class FormSubmissionInProgressPayload(BaseModel):
    """
    Payload for form.submission_in_progress event.
    
    Validates: Requirements 6.1-6.3
    """
    event: Literal["form.submission_in_progress"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, user_id, current_field"
    )
    signature: Optional[str] = None


class FormSubmissionCompletedPayload(BaseModel):
    """
    Payload for form.submission_completed event.
    
    Validates: Requirements 6.1-6.3, 6.5
    """
    event: Literal["form.submission_completed"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, user_id, submission_id, fields_submitted"
    )
    signature: Optional[str] = None


class FormSubmissionFailedPayload(BaseModel):
    """
    Payload for form.submission_failed event.
    
    Validates: Requirements 6.1-6.3, 6.6
    """
    event: Literal["form.submission_failed"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, user_id, error_type, error_message"
    )
    signature: Optional[str] = None


class FormScrapedPayload(BaseModel):
    """
    Payload for form.scraped event.
    
    Validates: Requirements 6.1-6.3, 6.7
    """
    event: Literal["form.scraped"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, fields[], submit_url"
    )
    signature: Optional[str] = None


class FormValidationErrorPayload(BaseModel):
    """
    Payload for form.validation_error event.
    
    Validates: Requirements 6.1-6.3
    """
    event: Literal["form.validation_error"]
    timestamp: datetime
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains: form_url, session_id, user_id, field_name, error_message"
    )
    signature: Optional[str] = None


# Union type for all event payloads
WebhookPayload = Union[
    FormSubmissionStartedPayload,
    FormSubmissionInProgressPayload,
    FormSubmissionCompletedPayload,
    FormSubmissionFailedPayload,
    FormScrapedPayload,
    FormValidationErrorPayload,
]


# =============================================================================
# Helper Functions
# =============================================================================

def create_payload(
    event_type: FormEventType,
    data: Dict[str, Any],
    signature: Optional[str] = None
) -> WebhookPayload:
    """
    Create a webhook payload for the given event type.
    
    Args:
        event_type: The type of form event
        data: Event-specific data
        signature: Optional HMAC signature
        
    Returns:
        Appropriate payload model for the event type
    """
    timestamp = datetime.utcnow()
    
    payload_map = {
        FormEventType.SUBMISSION_STARTED: FormSubmissionStartedPayload,
        FormEventType.SUBMISSION_IN_PROGRESS: FormSubmissionInProgressPayload,
        FormEventType.SUBMISSION_COMPLETED: FormSubmissionCompletedPayload,
        FormEventType.SUBMISSION_FAILED: FormSubmissionFailedPayload,
        FormEventType.FORM_SCRAPED: FormScrapedPayload,
        FormEventType.FORM_VALIDATION_ERROR: FormValidationErrorPayload,
    }
    
    payload_class = payload_map.get(event_type)
    if not payload_class:
        raise ValueError(f"Unknown event type: {event_type}")
    
    return payload_class(
        event=event_type.value,
        timestamp=timestamp,
        data=data,
        signature=signature
    )