"""
Unit Tests for Conversation Intelligence Module

Tests for IntentRecognizer, ConversationContext, AdaptiveResponseGenerator, and ProgressTracker.
"""

import pytest
from datetime import datetime

from services.ai.conversation_intelligence import (
    ConversationContext,
    IntentRecognizer,
    AdaptiveResponseGenerator,
    ProgressTracker,
    UserIntent,
    UserSentiment,
)


# =============================================================================
# IntentRecognizer Tests
# =============================================================================

class TestIntentRecognizer:
    """Tests for the IntentRecognizer class."""
    
    @pytest.fixture
    def recognizer(self):
        return IntentRecognizer()
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("skip", UserIntent.SKIP),
        ("skip this", UserIntent.SKIP),
        ("pass", UserIntent.SKIP),
        ("next", UserIntent.SKIP),
        ("move on", UserIntent.SKIP),
    ])
    def test_detect_skip_intent(self, recognizer, input_text, expected_intent):
        """Test detection of skip intents."""
        intent, conf = recognizer.detect_intent(input_text)
        assert intent == expected_intent
        assert conf > 0.8
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("undo", UserIntent.UNDO),
        ("undo that", UserIntent.UNDO),
        ("go back", UserIntent.UNDO),
        ("remove that", UserIntent.UNDO),
    ])
    def test_detect_undo_intent(self, recognizer, input_text, expected_intent):
        """Test detection of undo intents."""
        intent, conf = recognizer.detect_intent(input_text)
        assert intent == expected_intent
        assert conf > 0.8
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("help", UserIntent.HELP),
        ("help me", UserIntent.HELP),
        ("what should i say", UserIntent.HELP),
        ("give me an example", UserIntent.HELP),
    ])
    def test_detect_help_intent(self, recognizer, input_text, expected_intent):
        """Test detection of help intents."""
        intent, conf = recognizer.detect_intent(input_text)
        assert intent == expected_intent
        assert conf > 0.8
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("how many left", UserIntent.STATUS),
        ("progress", UserIntent.STATUS),
        ("almost done?", UserIntent.STATUS),
    ])
    def test_detect_status_intent(self, recognizer, input_text, expected_intent):
        """Test detection of status intents."""
        intent, conf = recognizer.detect_intent(input_text)
        assert intent == expected_intent
        assert conf > 0.8
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("actually my email is test@example.com", UserIntent.CORRECTION),
        ("no, my name is John", UserIntent.CORRECTION),
        ("correction: john.doe@gmail.com", UserIntent.CORRECTION),
    ])
    def test_detect_correction_intent(self, recognizer, input_text, expected_intent):
        """Test detection of correction intents."""
        intent, conf = recognizer.detect_intent(input_text)
        assert intent == expected_intent
        assert conf > 0.8
    
    def test_extract_correction_info(self, recognizer):
        """Test extraction of correction details."""
        result = recognizer.extract_correction_info("actually my email is test@example.com")
        assert result is not None
        field, value = result
        assert "email" in field.lower()
        assert "test@example.com" in value
    
    def test_has_data_content(self, recognizer):
        """Test detection of data content."""
        assert recognizer.has_data_content("My name is John Doe")
        assert recognizer.has_data_content("john@example.com")
        assert not recognizer.has_data_content("yes")  # just confirmation


# =============================================================================
# ConversationContext Tests
# =============================================================================

class TestConversationContext:
    """Tests for the ConversationContext class."""
    
    def test_default_values(self):
        """Test default context values."""
        ctx = ConversationContext()
        assert ctx.user_sentiment == UserSentiment.NEUTRAL
        assert ctx.confusion_count == 0
        assert ctx.positive_interactions == 0
    
    def test_detect_confusion(self):
        """Test confusion detection."""
        ctx = ConversationContext()
        ctx.update_from_input("what? I don't understand")
        assert ctx.user_sentiment == UserSentiment.CONFUSED
        assert ctx.confusion_count == 1
    
    def test_detect_frustration(self):
        """Test frustration detection."""
        ctx = ConversationContext()
        ctx.update_from_input("I already said that!")
        assert ctx.user_sentiment == UserSentiment.NEGATIVE
    
    def test_detect_positive(self):
        """Test positive sentiment detection."""
        ctx = ConversationContext()
        ctx.update_from_input("Thanks, that's great!")
        assert ctx.user_sentiment == UserSentiment.POSITIVE
        assert ctx.positive_interactions == 1
    
    def test_needs_extra_clarity(self):
        """Test needs_extra_clarity trigger."""
        ctx = ConversationContext()
        assert not ctx.needs_extra_clarity()
        ctx.update_from_input("huh?")
        ctx.update_from_input("what?")
        assert ctx.needs_extra_clarity()
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        ctx = ConversationContext()
        ctx.update_from_input("thanks!")
        ctx.confusion_count = 1
        
        data = ctx.to_dict()
        restored = ConversationContext.from_dict(data)
        
        assert restored.user_sentiment == ctx.user_sentiment
        assert restored.confusion_count == ctx.confusion_count
        assert restored.positive_interactions == ctx.positive_interactions


# =============================================================================
# ProgressTracker Tests
# =============================================================================

class TestProgressTracker:
    """Tests for the ProgressTracker class."""
    
    def test_calculate_progress(self):
        """Test progress calculation."""
        assert ProgressTracker.calculate_progress(0, 10) == 0
        assert ProgressTracker.calculate_progress(5, 10) == 50
        assert ProgressTracker.calculate_progress(10, 10) == 100
        assert ProgressTracker.calculate_progress(0, 0) == 100  # Edge case
    
    def test_milestone_messages(self):
        """Test milestone message generation."""
        # 25% milestone
        msg = ProgressTracker.get_milestone_message(3, 12)
        assert msg is not None
        assert "quarter" in msg.lower()
        
        # 50% milestone
        msg = ProgressTracker.get_milestone_message(5, 10)
        assert msg is not None
        assert "halfway" in msg.lower()
    
    def test_status_message(self):
        """Test status message generation."""
        msg = ProgressTracker.get_status_message(5, 10)
        assert "5" in msg and "10" in msg
        assert "50%" in msg
    
    def test_should_show_progress(self):
        """Test progress display triggers."""
        assert ProgressTracker.should_show_progress(1)  # First field
        assert ProgressTracker.should_show_progress(5)  # Every 5
        assert ProgressTracker.should_show_progress(10)


# =============================================================================
# AdaptiveResponseGenerator Tests
# =============================================================================

class TestAdaptiveResponseGenerator:
    """Tests for the AdaptiveResponseGenerator class."""
    
    @pytest.fixture
    def neutral_context(self):
        return ConversationContext()
    
    @pytest.fixture
    def confused_context(self):
        ctx = ConversationContext()
        ctx.confusion_count = 3
        return ctx
    
    @pytest.fixture
    def sample_fields(self):
        return [
            {"name": "email", "label": "Email Address", "type": "email"},
            {"name": "phone", "label": "Phone Number", "type": "tel"},
        ]
    
    def test_generate_standard_response(self, neutral_context, sample_fields):
        """Test standard response generation."""
        response = AdaptiveResponseGenerator.generate_response(
            extracted_values={"email": "test@example.com"},
            remaining_fields=sample_fields,
            context=neutral_context,
            current_batch=sample_fields[:1],
            extracted_count=1,
            total_count=5
        )
        assert len(response) > 0
        # Should contain next field question
        assert "email" in response.lower() or "phone" in response.lower() or "?" in response
    
    def test_generate_clarification_response(self, confused_context, sample_fields):
        """Test clarification response when user is confused."""
        response = AdaptiveResponseGenerator.generate_response(
            extracted_values={},
            remaining_fields=sample_fields,
            context=confused_context,
            current_batch=sample_fields[:1],
            extracted_count=0,
            total_count=5
        )
        # Should be extra clear
        assert "email" in response.lower() or "clear" in response.lower()
    
    def test_handle_small_talk(self):
        """Test small talk handling."""
        response = AdaptiveResponseGenerator._handle_small_talk(0, 5)
        assert "started" in response.lower() or "ready" in response.lower()
        
        response = AdaptiveResponseGenerator._handle_small_talk(5, 0)
        assert "done" in response.lower() or "finished" in response.lower()
