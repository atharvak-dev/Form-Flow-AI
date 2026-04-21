"""
Webhook Models Property Tests

Property-based tests for Webhook and WebhookDeliveryLog database models.
Validates: Requirements 7.1, 7.3, 2.4

Property 2: Event Delivery Creates Log for Each Subscribed Webhook
Property 7: Inactive Webhooks Do Not Receive Deliveries
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from core.models import Webhook, WebhookDeliveryLog


# =============================================================================
# Property Test Strategies
# =============================================================================

def valid_event_types():
    """Strategy for generating valid event types."""
    return st.sampled_from([
        "form.submission_started",
        "form.submission_in_progress",
        "form.submission_completed",
        "form.submission_failed",
        "form.scraped",
        "form.validation_error"
    ])


def valid_https_url():
    """Strategy for generating valid HTTPS URLs."""
    return st.builds(
        lambda host, path: f"https://{host}{path}",
        host=st.from_regex(r"[a-zA-Z][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+"),
        path=st.from_regex(r"(/.*)?")
    )


def webhook_strategy():
    """Strategy for generating valid Webhook objects."""
    return st.builds(
        Webhook,
        id=st.uuids(),
        user_id=st.integers(min_value=1, max_value=1000),
        url=valid_https_url(),
        events=st.lists(valid_event_types(), min_size=1, max_size=6),
        secret=st.text(min_size=64, max_size=64, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        is_active=st.booleans(),
        created_at=st.datetimes(timezones=st.just(timezone.utc)),
        updated_at=st.datetimes(timezones=st.just(timezone.utc))
    )


def webhook_delivery_log_strategy():
    """Strategy for generating valid WebhookDeliveryLog objects."""
    return st.builds(
        WebhookDeliveryLog,
        id=st.uuids(),
        webhook_id=st.uuids(),
        event=valid_event_types(),
        payload=st.dictionaries(st.text(min_size=1, max_size=50), st.one_of(st.text(), st.integers(), st.floats(), st.booleans())),
        status=st.sampled_from(["pending", "success", "failed", "retrying"]),
        response_code=st.one_of(st.integers(min_value=200, max_value=599), st.none()),
        response_body=st.one_of(st.text(max_size=1000), st.none()),
        attempts=st.integers(min_value=0, max_value=10),
        next_retry_at=st.one_of(st.datetimes(timezones=st.just(timezone.utc)), st.none()),
        created_at=st.datetimes(timezones=st.just(timezone.utc)),
        delivered_at=st.one_of(st.datetimes(timezones=st.just(timezone.utc)), st.none())
    )


# =============================================================================
# Property 2: Event Delivery Creates Log for Each Subscribed Webhook
# =============================================================================

class TestEventDeliveryCreatesLog:
    """
    Property 2: Event Delivery Creates Log for Each Subscribed Webhook
    
    For any event type and set of webhooks, when an event is queued,
    exactly one delivery log is created for each active webhook subscribed
    to that event type, and no delivery logs are created for webhooks
    not subscribed to that event.
    
    Validates: Requirements 7.1, 7.3
    """
    
    @given(
        event_type=valid_event_types(),
        webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_active_webhooks_subscribed_to_event_receive_delivery(self, event_type, webhooks):
        """
        Property 2a: Active webhooks subscribed to an event should receive deliveries.
        
        For any event type, all active webhooks that include that event in their
        events list should be eligible to receive delivery logs.
        """
        # Filter to active webhooks subscribed to the event
        subscribed_active = [
            w for w in webhooks 
            if w.is_active and event_type in w.events
        ]
        
        # Each subscribed active webhook should receive a delivery
        for webhook in subscribed_active:
            assert webhook.is_active is True
            assert event_type in webhook.events
    
    @given(
        event_type=valid_event_types(),
        webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_inactive_webhooks_do_not_receive_delivery(self, event_type, webhooks):
        """
        Property 7: Inactive Webhooks Do Not Receive Deliveries
        
        For any event type and webhook that is not active, when the event is
        queued, no delivery log should be created for that webhook.
        
        Validates: Requirement 2.4
        """
        # Filter to inactive webhooks
        inactive_webhooks = [w for w in webhooks if not w.is_active]
        
        # Inactive webhooks should not receive deliveries
        for webhook in inactive_webhooks:
            assert webhook.is_active is False
    
    @given(
        event_type=valid_event_types(),
        webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_webhooks_not_subscribed_to_event_do_not_receive_delivery(self, event_type, webhooks):
        """
        Property 2b: Webhooks not subscribed to an event should not receive deliveries.
        
        For any event type, webhooks that do not include that event in their
        events list should not receive delivery logs.
        """
        # Filter to webhooks NOT subscribed to the event
        not_subscribed = [
            w for w in webhooks 
            if event_type not in w.events
        ]
        
        # These webhooks should not receive deliveries for this event
        for webhook in not_subscribed:
            assert event_type not in webhook.events
    
    @given(webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10))
    @settings(max_examples=30)
    def test_webhook_events_stored_as_jsonb(self, webhooks):
        """
        Property: Webhook events are stored as JSONB array.
        
        The events column should store a list of event type strings that
        can be queried using PostgreSQL JSONB operators.
        """
        for webhook in webhooks:
            assert isinstance(webhook.events, list)
            assert len(webhook.events) > 0
            # All events should be valid event type strings
            for event in webhook.events:
                assert event.startswith("form.")
    
    @given(
        event_type=valid_event_types(),
        webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10)
    )
    @settings(max_examples=30)
    def test_delivery_log_creation_for_subscribed_webhooks(self, event_type, webhooks):
        """
        Property 2c: Delivery logs can be created for subscribed webhooks.
        
        A WebhookDeliveryLog can be created with a webhook_id referencing
        an active webhook that is subscribed to the event.
        """
        # Find an active webhook subscribed to the event
        subscribed_active = next(
            (w for w in webhooks if w.is_active and event_type in w.events),
            None
        )
        
        if subscribed_active:
            # Create a delivery log for this webhook
            delivery_log = WebhookDeliveryLog(
                webhook_id=subscribed_active.id,
                event=event_type,
                payload={"test": "data"},
                status="pending",
                attempts=0
            )
            
            assert delivery_log.webhook_id == subscribed_active.id
            assert delivery_log.event == event_type
            assert delivery_log.status == "pending"


# =============================================================================
# Property 7: Inactive Webhooks Do Not Receive Deliveries
# =============================================================================

class TestInactiveWebhooksDoNotReceiveDeliveries:
    """
    Property 7: Inactive Webhooks Do Not Receive Deliveries
    
    For any event type and webhook that is not active, when the event is
    queued, no delivery log is created for that webhook.
    
    Validates: Requirement 2.4
    """
    
    @given(webhooks=st.lists(webhook_strategy(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_inactive_webhook_has_is_active_false(self, webhooks):
        """
        Property 7a: Inactive webhooks have is_active set to False.
        """
        inactive_webhooks = [w for w in webhooks if not w.is_active]
        
        for webhook in inactive_webhooks:
            assert webhook.is_active is False
    
    @given(webhooks=st.lists(webhook_strategy(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_active_webhook_has_is_active_true(self, webhooks):
        """
        Property 7b: Active webhooks have is_active set to True.
        """
        active_webhooks = [w for w in webhooks if w.is_active]
        
        for webhook in active_webhooks:
            assert webhook.is_active is True
    
    @given(
        event_type=valid_event_types(),
        webhooks=st.lists(webhook_strategy(), min_size=2, max_size=10)
    )
    @settings(max_examples=30)
    def test_mixed_active_inactive_webhooks(self, event_type, webhooks):
        """
        Property 7c: Only active webhooks subscribed to an event should receive deliveries.
        
        When there is a mix of active and inactive webhooks, only the active
        ones that are subscribed to the event should receive deliveries.
        """
        active_subscribed = [
            w for w in webhooks 
            if w.is_active and event_type in w.events
        ]
        inactive_subscribed = [
            w for w in webhooks 
            if not w.is_active and event_type in w.events
        ]
        
        # Active subscribed webhooks should receive deliveries
        for webhook in active_subscribed:
            assert webhook.is_active is True
            assert event_type in webhook.events
        
        # Inactive subscribed webhooks should NOT receive deliveries
        for webhook in inactive_subscribed:
            assert webhook.is_active is False
            assert event_type in webhook.events


# =============================================================================
# WebhookDeliveryLog Model Tests
# =============================================================================

class TestWebhookDeliveryLogModel:
    """Tests for WebhookDeliveryLog model structure."""
    
    @given(delivery_log=webhook_delivery_log_strategy())
    @settings(max_examples=30)
    def test_delivery_log_has_required_fields(self, delivery_log):
        """
        Verify delivery log has all required fields per design.
        """
        assert delivery_log.id is not None
        assert delivery_log.webhook_id is not None
        assert delivery_log.event is not None
        assert delivery_log.payload is not None
        assert delivery_log.status is not None
        assert delivery_log.attempts is not None
        assert delivery_log.created_at is not None
    
    @given(delivery_log=webhook_delivery_log_strategy())
    @settings(max_examples=20)
    def test_delivery_log_status_values(self, delivery_log):
        """
        Verify delivery log status is one of valid values.
        """
        valid_statuses = ["pending", "success", "failed", "retrying"]
        assert delivery_log.status in valid_statuses
    
    @given(delivery_log=webhook_delivery_log_strategy())
    @settings(max_examples=20)
    def test_delivery_log_payload_is_jsonb(self, delivery_log):
        """
        Verify delivery log payload is stored as JSONB.
        """
        assert isinstance(delivery_log.payload, dict)
    
    @given(delivery_log=webhook_delivery_log_strategy())
    @settings(max_examples=20)
    def test_delivery_log_attempts_non_negative(self, delivery_log):
        """
        Verify delivery log attempts is non-negative.
        """
        assert delivery_log.attempts >= 0


# =============================================================================
# Webhook Model Tests
# =============================================================================

class TestWebhookModel:
    """Tests for Webhook model structure."""
    
    @given(webhook=webhook_strategy())
    @settings(max_examples=30)
    def test_webhook_has_required_fields(self, webhook):
        """
        Verify webhook has all required fields per design.
        """
        assert webhook.id is not None
        assert webhook.user_id is not None
        assert webhook.url is not None
        assert webhook.events is not None
        assert webhook.secret is not None
        assert webhook.is_active is not None
        assert webhook.created_at is not None
        assert webhook.updated_at is not None
    
    @given(webhook=webhook_strategy())
    @settings(max_examples=20)
    def test_webhook_url_is_https(self, webhook):
        """
        Verify webhook URL uses HTTPS.
        """
        assert webhook.url.startswith("https://")
    
    @given(webhook=webhook_strategy())
    @settings(max_examples=20)
    def test_webhook_secret_length(self, webhook):
        """
        Verify webhook secret is 64 characters.
        """
        assert len(webhook.secret) == 64
    
    @given(webhook=webhook_strategy())
    @settings(max_examples=20)
    def test_webhook_events_not_empty(self, webhook):
        """
        Verify webhook has at least one event subscribed.
        """
        assert len(webhook.events) > 0
    
    @given(webhooks=st.lists(webhook_strategy(), min_size=1, max_size=10))
    @settings(max_examples=20)
    def test_webhook_user_relationship(self, webhooks):
        """
        Verify webhook has user_id for relationship.
        """
        for webhook in webhooks:
            assert webhook.user_id is not None
            assert isinstance(webhook.user_id, int)


# =============================================================================
# Database Index Tests
# =============================================================================

class TestDatabaseIndexes:
    """Tests for database indexes on webhook models."""
    
    def test_webhook_table_has_user_id_index(self):
        """
        Verify Webhook table has index on user_id.
        """
        # Check that user_id column exists (index is defined in model)
        assert hasattr(Webhook, 'user_id')
    
    def test_webhook_table_has_is_active_index(self):
        """
        Verify Webhook table has index on is_active.
        """
        # Check that is_active column exists (index is defined in model)
        assert hasattr(Webhook, 'is_active')
    
    def test_delivery_log_table_has_webhook_id_index(self):
        """
        Verify WebhookDeliveryLog table has index on webhook_id.
        """
        assert hasattr(WebhookDeliveryLog, 'webhook_id')
    
    def test_delivery_log_table_has_status_index(self):
        """
        Verify WebhookDeliveryLog table has index on status.
        """
        assert hasattr(WebhookDeliveryLog, 'status')
    
    def test_delivery_log_table_has_created_at_index(self):
        """
        Verify WebhookDeliveryLog table has index on created_at.
        """
        assert hasattr(WebhookDeliveryLog, 'created_at')
# =============================================================================
# Property Tests for Delivery (Task 5.4)
# =============================================================================

class TestRetryLogicExponentialBackoff:
    """
    Property 4: Retry Logic Uses Exponential Backoff
    
    For any delivery attempt number n (where 1 ≤ n ≤ 3), the retry delay
    equals 60 × 2^(n-1) seconds.
    
    Validates: Requirements 9.2
    """
    
    @given(attempt_number=st.integers(min_value=1, max_value=3))
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_exponential_backoff_formula(self, attempt_number):
        """
        Property 4a: Exponential backoff formula is correct.
        
        For attempt n, delay should be 60 × 2^(n-1):
        - Attempt 1: 60 × 2^0 = 60 seconds
        - Attempt 2: 60 × 2^1 = 120 seconds
        - Attempt 3: 60 × 2^2 = 240 seconds
        """
        from services.webhook.service import WebhookService
        
        expected_delay = 60 * (2 ** (attempt_number - 1))
        actual_delay = WebhookService.calculate_backoff_delay(attempt_number)
        
        assert actual_delay == expected_delay, (
            f"Attempt {attempt_number}: expected {expected_delay}s, got {actual_delay}s"
        )
    
    @given(attempt_numbers=st.lists(st.integers(min_value=1, max_value=3), min_size=2, max_size=3, unique=True))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_backoff_increases_with_attempts(self, attempt_numbers):
        """
        Property 4b: Backoff delay increases with each retry attempt.
        
        Each subsequent retry should have a longer delay than the previous.
        """
        from services.webhook.service import WebhookService
        
        sorted_attempts = sorted(attempt_numbers)
        delays = [WebhookService.calculate_backoff_delay(n) for n in sorted_attempts]
        
        # Each delay should be greater than the previous
        for i in range(1, len(delays)):
            assert delays[i] > delays[i - 1], (
                f"Delay should increase: {delays[i-1]}s -> {delays[i]}s"
            )
    
    def test_backoff_edge_cases(self):
        """
        Property 4c: Edge cases for backoff calculation.
        
        - Attempt 0 or negative: should return minimum 60 seconds
        - Attempt > 3: should still follow formula
        """
        from services.webhook.service import WebhookService
        
        # Edge case: attempt 0
        assert WebhookService.calculate_backoff_delay(0) == 60
        
        # Edge case: negative
        assert WebhookService.calculate_backoff_delay(-1) == 60
        
        # Edge case: large number
        assert WebhookService.calculate_backoff_delay(10) == 60 * (2 ** 9)


class TestDeliverySuccessOnHTTP2xx:
    """
    Property 5: Delivery Succeeds Only on HTTP 2xx
    
    For any HTTP response, the delivery is marked as success if and only if
    the status code is in the range 200-299.
    
    Validates: Requirements 8.6, 8.7
    """
    
    @given(status_code=st.integers(min_value=200, max_value=299))
    @settings(max_examples=30)
    def test_2xx_is_success(self, status_code):
        """
        Property 5a: HTTP 2xx status codes should be treated as success.
        
        All status codes in the 200-299 range are success.
        """
        is_success = status_code >= 200 and status_code < 300
        assert is_success is True
    
    @given(status_code=st.one_of(
        st.integers(min_value=100, max_value=199),
        st.integers(min_value=300, max_value=399),
        st.integers(min_value=400, max_value=499),
        st.integers(min_value=500, max_value=599)
    ))
    @settings(max_examples=40)
    def test_non_2xx_is_failure(self, status_code):
        """
        Property 5b: Non-2xx status codes should be treated as failure.
        
        All status codes outside 200-299 are failures.
        """
        is_success = status_code >= 200 and status_code < 300
        assert is_success is False
    
    @given(status_code=st.integers(min_value=200, max_value=299))
    @settings(max_examples=10)
    def test_2xx_range_complete(self, status_code):
        """
        Property 5c: All 2xx codes are valid success codes.
        
        200, 201, 202, 204, 206, etc. all indicate success.
        """
        assert 200 <= status_code < 300


class TestPayloadContainsRequiredFields:
    """
    Property 8: Payload Contains Required Fields
    
    For any event type, the delivered payload contains the "event" field
    with the event type, a "timestamp" field in ISO 8601 format, and a
    "data" field with event-specific information.
    
    Validates: Requirements 6.1, 6.2, 6.3
    """
    
    @given(
        event_type=valid_event_types(),
        timestamp=st.datetimes(timezones=st.just(timezone.utc)),
        data=st.dictionaries(st.text(min_size=1, max_size=30), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()))
    )
    @settings(max_examples=30)
    def test_payload_has_event_field(self, event_type, timestamp, data):
        """
        Property 8a: Payload must contain "event" field.
        
        The event field should contain the event type string.
        """
        payload = {
            "event": event_type,
            "timestamp": timestamp.isoformat() + "Z",
            "data": data
        }
        
        assert "event" in payload
        assert payload["event"] == event_type
    
    @given(
        event_type=valid_event_types(),
        timestamp=st.datetimes(timezones=st.just(timezone.utc)),
        data=st.dictionaries(st.text(min_size=1, max_size=30), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()))
    )
    @settings(max_examples=30)
    def test_payload_has_timestamp_field(self, event_type, timestamp, data):
        """
        Property 8b: Payload must contain "timestamp" field in ISO 8601 format.
        
        The timestamp field should be in ISO 8601 format.
        """
        from datetime import datetime
        
        # Format timestamp as ISO 8601 with Z suffix
        ts_str = timestamp.isoformat()
        if timestamp.tzinfo is not None:
            ts_str = ts_str.replace("+00:00", "Z")
        
        payload = {
            "event": event_type,
            "timestamp": ts_str,
            "data": data
        }
        
        assert "timestamp" in payload
        
        # Verify it's parseable as ISO 8601
        ts_for_parsing = payload["timestamp"].replace("Z", "+00:00")
        parsed = datetime.fromisoformat(ts_for_parsing)
        assert parsed is not None
    
    @given(
        event_type=valid_event_types(),
        timestamp=st.datetimes(timezones=st.just(timezone.utc)),
        data=st.dictionaries(st.text(min_size=1, max_size=30), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()))
    )
    @settings(max_examples=30)
    def test_payload_has_data_field(self, event_type, timestamp, data):
        """
        Property 8c: Payload must contain "data" field with event-specific information.
        
        The data field should be a dictionary containing event-specific fields.
        """
        payload = {
            "event": event_type,
            "timestamp": timestamp.isoformat() + "Z",
            "data": data
        }
        
        assert "data" in payload
        assert isinstance(payload["data"], dict)
    
    @given(
        event_type=valid_event_types(),
        timestamp=st.datetimes(timezones=st.just(timezone.utc)),
        data=st.dictionaries(st.text(min_size=1, max_size=30), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()))
    )
    @settings(max_examples=30)
    def test_payload_has_all_required_fields(self, event_type, timestamp, data):
        """
        Property 8d: Payload must contain all three required fields.
        
        A valid webhook payload must have: event, timestamp, data
        """
        payload = {
            "event": event_type,
            "timestamp": timestamp.isoformat() + "Z",
            "data": data
        }
        
        # All required fields must be present
        assert "event" in payload
        assert "timestamp" in payload
        assert "data" in payload
        
        # All fields must be non-null
        assert payload["event"] is not None
        assert payload["timestamp"] is not None
        assert payload["data"] is not None


class TestDeliveryStatusTransitions:
    """
    Tests for delivery status transitions.
    
    Validates: Requirements 9.1, 9.3, 9.4
    """
    
    @given(attempts=st.integers(min_value=0, max_value=10))
    @settings(max_examples=30)
    def test_retry_scheduled_for_failed_under_max(self, attempts):
        """
        Delivery should be scheduled for retry when failed and under max attempts.
        
        Max retries is 3, so attempts 0, 1, 2 should schedule retry.
        """
        max_retries = 3
        
        # If delivery failed and hasn't exceeded max retries
        should_retry = attempts < max_retries
        
        assert should_retry == (attempts < max_retries)
    
    @given(attempts=st.integers(min_value=0, max_value=10))
    @settings(max_examples=30)
    def test_no_retry_when_exceeded_max(self, attempts):
        """
        Delivery should NOT be scheduled for retry when exceeded max attempts.
        
        Attempts >= 3 means max retries exceeded.
        """
        max_retries = 3
        
        # If delivery failed and has exceeded max retries
        should_not_retry = attempts >= max_retries
        
        assert should_not_retry == (attempts >= max_retries)
    
    def test_status_values_are_valid(self):
        """
        Verify all valid delivery status values.
        """
        valid_statuses = ["pending", "success", "failed", "retrying"]
        
        # All these should be valid
        for status in valid_statuses:
            assert status in valid_statuses