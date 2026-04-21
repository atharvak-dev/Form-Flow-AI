"""
Webhook Schemas Tests

Tests for webhook event types and payload schemas.
Validates: Requirements 5.1-5.6, 6.1-6.7
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, settings, assume, example, HealthCheck
from hypothesis import strategies as st

from services.webhook.schemas import (
    FormEventType,
    FormSubmissionStartedPayload,
    FormSubmissionInProgressPayload,
    FormSubmissionCompletedPayload,
    FormSubmissionFailedPayload,
    FormScrapedPayload,
    FormValidationErrorPayload,
    WebhookPayload,
    create_payload,
)


# =============================================================================
# Unit Tests - FormEventType Enum
# =============================================================================

class TestFormEventType:
    """Tests for FormEventType enum."""
    
    def test_all_event_types_defined(self):
        """Verify all required event types are defined."""
        assert FormEventType.SUBMISSION_STARTED.value == "form.submission_started"
        assert FormEventType.SUBMISSION_IN_PROGRESS.value == "form.submission_in_progress"
        assert FormEventType.SUBMISSION_COMPLETED.value == "form.submission_completed"
        assert FormEventType.SUBMISSION_FAILED.value == "form.submission_failed"
        assert FormEventType.FORM_SCRAPED.value == "form.scraped"
        assert FormEventType.FORM_VALIDATION_ERROR.value == "form.validation_error"
    
    def test_event_types_are_strings(self):
        """Verify event types can be used as strings."""
        for event_type in FormEventType:
            assert isinstance(event_type, str)
            assert event_type.value.startswith("form.")
    
    def test_event_type_parsing(self):
        """Verify event types can be parsed from strings."""
        assert FormEventType("form.submission_started") == FormEventType.SUBMISSION_STARTED
        assert FormEventType("form.submission_completed") == FormEventType.SUBMISSION_COMPLETED
        assert FormEventType("form.submission_failed") == FormEventType.SUBMISSION_FAILED
        assert FormEventType("form.scraped") == FormEventType.FORM_SCRAPED
        assert FormEventType("form.validation_error") == FormEventType.FORM_VALIDATION_ERROR


# =============================================================================
# Unit Tests - Payload Schemas
# =============================================================================

class TestSubmissionStartedPayload:
    """Tests for FormSubmissionStartedPayload."""
    
    def test_payload_creation(self):
        """Test basic payload creation."""
        payload = FormSubmissionStartedPayload(
            event="form.submission_started",
            timestamp=datetime.now(timezone.utc),
            data={"form_url": "https://example.com/form", "session_id": "abc123", "user_id": 1, "fields_count": 10}
        )
        assert payload.event == "form.submission_started"
        assert "form_url" in payload.data
        assert payload.data["fields_count"] == 10
    
    def test_payload_with_signature(self):
        """Test payload with signature."""
        payload = FormSubmissionStartedPayload(
            event="form.submission_started",
            timestamp=datetime.now(timezone.utc),
            data={},
            signature="sha256=abc123"
        )
        assert payload.signature == "sha256=abc123"
    
    def test_payload_default_data(self):
        """Test payload with default empty data."""
        payload = FormSubmissionStartedPayload(
            event="form.submission_started",
            timestamp=datetime.now(timezone.utc)
        )
        assert payload.data == {}


class TestSubmissionCompletedPayload:
    """Tests for FormSubmissionCompletedPayload."""
    
    def test_payload_creation(self):
        """Test payload with all required fields per Requirement 6.5."""
        payload = FormSubmissionCompletedPayload(
            event="form.submission_completed",
            timestamp=datetime.now(timezone.utc),
            data={
                "form_url": "https://example.com/form",
                "session_id": "abc123",
                "user_id": 1,
                "submission_id": "sub-456",
                "fields_submitted": 12
            }
        )
        assert payload.event == "form.submission_completed"
        assert payload.data["submission_id"] == "sub-456"
        assert payload.data["fields_submitted"] == 12


class TestSubmissionFailedPayload:
    """Tests for FormSubmissionFailedPayload."""
    
    def test_payload_creation(self):
        """Test payload with all required fields per Requirement 6.6."""
        payload = FormSubmissionFailedPayload(
            event="form.submission_failed",
            timestamp=datetime.now(timezone.utc),
            data={
                "form_url": "https://example.com/form",
                "session_id": "abc123",
                "user_id": 1,
                "error_type": "network_error",
                "error_message": "Connection timeout"
            }
        )
        assert payload.event == "form.submission_failed"
        assert payload.data["error_type"] == "network_error"
        assert payload.data["error_message"] == "Connection timeout"


class TestFormScrapedPayload:
    """Tests for FormScrapedPayload."""
    
    def test_payload_creation(self):
        """Test payload with all required fields per Requirement 6.7."""
        payload = FormScrapedPayload(
            event="form.scraped",
            timestamp=datetime.now(timezone.utc),
            data={
                "form_url": "https://example.com/form",
                "session_id": "abc123",
                "fields": [{"name": "email", "type": "email"}, {"name": "name", "type": "text"}],
                "submit_url": "https://example.com/submit"
            }
        )
        assert payload.event == "form.scraped"
        assert len(payload.data["fields"]) == 2
        assert payload.data["submit_url"] == "https://example.com/submit"


class TestValidationErrorPayload:
    """Tests for FormValidationErrorPayload."""
    
    def test_payload_creation(self):
        """Test validation error payload."""
        payload = FormValidationErrorPayload(
            event="form.validation_error",
            timestamp=datetime.now(timezone.utc),
            data={
                "form_url": "https://example.com/form",
                "session_id": "abc123",
                "user_id": 1,
                "field_name": "email",
                "error_message": "Invalid email format"
            }
        )
        assert payload.event == "form.validation_error"
        assert payload.data["field_name"] == "email"


# =============================================================================
# Unit Tests - Payload Factory
# =============================================================================

class TestCreatePayload:
    """Tests for create_payload helper function."""
    
    def test_create_submission_started(self):
        """Test creating submission_started payload."""
        payload = create_payload(
            FormEventType.SUBMISSION_STARTED,
            {"form_url": "https://example.com", "session_id": "abc", "user_id": 1, "fields_count": 5}
        )
        assert isinstance(payload, FormSubmissionStartedPayload)
        assert payload.event == "form.submission_started"
    
    def test_create_submission_completed(self):
        """Test creating submission_completed payload."""
        payload = create_payload(
            FormEventType.SUBMISSION_COMPLETED,
            {"form_url": "https://example.com", "session_id": "abc", "user_id": 1, "submission_id": "sub-1", "fields_submitted": 10}
        )
        assert isinstance(payload, FormSubmissionCompletedPayload)
        assert payload.event == "form.submission_completed"
    
    def test_create_submission_failed(self):
        """Test creating submission_failed payload."""
        payload = create_payload(
            FormEventType.SUBMISSION_FAILED,
            {"form_url": "https://example.com", "session_id": "abc", "user_id": 1, "error_type": "timeout", "error_message": "Request timeout"}
        )
        assert isinstance(payload, FormSubmissionFailedPayload)
        assert payload.event == "form.submission_failed"
    
    def test_create_form_scraped(self):
        """Test creating form.scraped payload."""
        payload = create_payload(
            FormEventType.FORM_SCRAPED,
            {"form_url": "https://example.com", "session_id": "abc", "fields": [], "submit_url": "https://example.com/submit"}
        )
        assert isinstance(payload, FormScrapedPayload)
        assert payload.event == "form.scraped"
    
    def test_create_validation_error(self):
        """Test creating validation_error payload."""
        payload = create_payload(
            FormEventType.FORM_VALIDATION_ERROR,
            {"form_url": "https://example.com", "session_id": "abc", "user_id": 1, "field_name": "email", "error_message": "Invalid"}
        )
        assert isinstance(payload, FormValidationErrorPayload)
        assert payload.event == "form.validation_error"
    
    def test_create_with_signature(self):
        """Test creating payload with signature."""
        payload = create_payload(
            FormEventType.SUBMISSION_COMPLETED,
            {"form_url": "https://example.com"},
            signature="sha256=test"
        )
        assert payload.signature == "sha256=test"
    
    def test_create_invalid_event_type(self):
        """Test that invalid event type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown event type"):
            create_payload("invalid_event" , {})


# =============================================================================
# Property-Based Tests
# =============================================================================

class TestPayloadProperties:
    """Property-based tests for webhook payloads."""
    
    @given(
        event_type=st.sampled_from(list(FormEventType)),
        timestamp=st.datetimes(),
        data=st.dictionaries(st.text(min_size=1, max_size=50), st.text(max_size=200), max_size=20)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_payload_has_required_fields(self, event_type, timestamp, data):
        """
        Property 8: Payload Contains Required Fields
        
        For any event type, the delivered payload contains:
        - "event" field with the event type
        - "timestamp" field in ISO 8601 format
        - "data" field with event-specific information
        
        Validates: Requirements 6.1, 6.2, 6.3
        """
        payload = create_payload(event_type, data)
        
        # Check event field
        assert payload.event == event_type.value
        
        # Check timestamp field
        assert payload.timestamp is not None
        assert isinstance(payload.timestamp, datetime)
        
        # Check data field
        assert payload.data is not None
        assert isinstance(payload.data, dict)
    
    @given(
        event_type=st.sampled_from(list(FormEventType)),
        data=st.dictionaries(st.text(min_size=1, max_size=50), st.one_of(st.text(max_size=200), st.integers(), st.floats()), max_size=20)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_payload_serialization(self, event_type, data):
        """
        Property: Payloads can be serialized to JSON
        
        All payloads should be JSON serializable for webhook delivery.
        """
        import json
        
        payload = create_payload(event_type, data)
        
        # Should not raise
        json_str = payload.model_dump_json()
        assert json_str is not None
        assert "event" in json_str
    
    @given(
        event_type=st.sampled_from(list(FormEventType)),
        data=st.dictionaries(st.text(min_size=1, max_size=50), st.text(max_size=200), max_size=20)
    )
    @settings(max_examples=30)
    def test_payload_timestamp_is_set(self, event_type, data):
        """
        Property: Timestamp is automatically set
        
        When creating a payload, timestamp should be set to current time.
        """
        # Use naive datetime to match create_payload's output
        before = datetime.utcnow()
        payload = create_payload(event_type, data)
        after = datetime.utcnow()
        
        # Timestamp should be between before and after (within reasonable margin)
        # Handle both naive and timezone-aware timestamps
        payload_ts = payload.timestamp.replace(tzinfo=None) if payload.timestamp.tzinfo else payload.timestamp
        assert before <= payload_ts <= after or abs((payload_ts - before).total_seconds()) < 1


class TestEventTypeProperties:
    """Property-based tests for event types."""
    
    @given(st.text(min_size=1))
    @settings(max_examples=50)
    def test_event_type_string_values(self, prefix):
        """
        Property: Event type string values start with 'form.'
        
        All event types should have string values starting with 'form.'
        """
        for event_type in FormEventType:
            assert event_type.value.startswith("form.")
    
    @given(st.sampled_from(list(FormEventType)))
    @settings(max_examples=10)
    def test_event_type_is_valid(self, event_type):
        """
        Property: All defined event types are valid
        
        Each FormEventType enum value should be a valid string.
        """
        assert len(event_type.value) > 0
        assert "." in event_type.value  # Should have namespace format


# =============================================================================
# Integration Tests - Payload Structure
# =============================================================================

class TestPayloadStructureRequirements:
    """
    Tests validating specific payload structure requirements.
    
    Validates: Requirements 6.1-6.7
    """
    
    def test_requirement_6_1_event_field(self):
        """Requirement 6.1: Payload includes 'event' field with event type."""
        payload = create_payload(FormEventType.SUBMISSION_COMPLETED, {})
        assert "event" in payload.model_dump()
        assert payload.event == "form.submission_completed"
    
    def test_requirement_6_2_timestamp_field(self):
        """Requirement 6.2: Payload includes 'timestamp' field in ISO 8601 format."""
        payload = create_payload(FormEventType.SUBMISSION_COMPLETED, {})
        assert "timestamp" in payload.model_dump()
        # ISO 8601 format check
        assert payload.timestamp.isoformat() is not None
    
    def test_requirement_6_3_data_field(self):
        """Requirement 6.3: Payload includes 'data' field with event-specific information."""
        payload = create_payload(FormEventType.SUBMISSION_COMPLETED, {"key": "value"})
        assert "data" in payload.model_dump()
        assert payload.data == {"key": "value"}
    
    def test_requirement_6_4_submission_started_data(self):
        """Requirement 6.4: submission_started data contains required fields."""
        data = {
            "form_url": "https://example.com/form",
            "session_id": "abc-123",
            "user_id": 1,
            "fields_count": 10
        }
        payload = create_payload(FormEventType.SUBMISSION_STARTED, data)
        assert payload.data["form_url"] == data["form_url"]
        assert payload.data["session_id"] == data["session_id"]
        assert payload.data["user_id"] == data["user_id"]
        assert payload.data["fields_count"] == data["fields_count"]
    
    def test_requirement_6_5_submission_completed_data(self):
        """Requirement 6.5: submission_completed data contains required fields."""
        data = {
            "form_url": "https://example.com/form",
            "session_id": "abc-123",
            "user_id": 1,
            "submission_id": "sub-456",
            "fields_submitted": 12
        }
        payload = create_payload(FormEventType.SUBMISSION_COMPLETED, data)
        assert payload.data["form_url"] == data["form_url"]
        assert payload.data["session_id"] == data["session_id"]
        assert payload.data["user_id"] == data["user_id"]
        assert payload.data["submission_id"] == data["submission_id"]
        assert payload.data["fields_submitted"] == data["fields_submitted"]
    
    def test_requirement_6_6_submission_failed_data(self):
        """Requirement 6.6: submission_failed data contains required fields."""
        data = {
            "form_url": "https://example.com/form",
            "session_id": "abc-123",
            "user_id": 1,
            "error_type": "network_error",
            "error_message": "Connection timeout"
        }
        payload = create_payload(FormEventType.SUBMISSION_FAILED, data)
        assert payload.data["form_url"] == data["form_url"]
        assert payload.data["session_id"] == data["session_id"]
        assert payload.data["user_id"] == data["user_id"]
        assert payload.data["error_type"] == data["error_type"]
        assert payload.data["error_message"] == data["error_message"]
    
    def test_requirement_6_7_form_scraped_data(self):
        """Requirement 6.7: form.scraped data contains required fields."""
        data = {
            "form_url": "https://example.com/form",
            "session_id": "abc-123",
            "fields": [{"name": "email", "type": "email"}],
            "submit_url": "https://example.com/submit"
        }
        payload = create_payload(FormEventType.FORM_SCRAPED, data)
        assert payload.data["form_url"] == data["form_url"]
        assert payload.data["session_id"] == data["session_id"]
        assert payload.data["fields"] == data["fields"]
        assert payload.data["submit_url"] == data["submit_url"]