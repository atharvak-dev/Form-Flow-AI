"""
Unit Tests for Voice Processor Module

Tests for VoiceInputProcessor, ClarificationStrategy, ConfidenceCalibrator,
MultiModalFallback, and NoiseHandler.
"""

import pytest

from services.ai.voice_processor import (
    VoiceInputProcessor,
    ClarificationStrategy,
    ConfidenceCalibrator,
    MultiModalFallback,
    NoiseHandler,
    AudioQuality,
    FieldImportance,
    StreamingSpeechHandler,
    PartialUtterance,
    PhoneticMatcher,  # NEW
)


# =============================================================================
# VoiceInputProcessor Tests
# =============================================================================

class TestVoiceInputProcessor:
    """Tests for voice input normalization."""
    
    @pytest.mark.parametrize("voice_input,expected", [
        ("john at gmail dot com", "john@gmail.com"),
        ("john at the rate gmail dot com", "john@gmail.com"),
        ("sarah underscore doe at yahoo dot com", "sarah_doe@yahoo.com"),
        ("john at g mail dot com", "john@gmail.com"),
    ])
    def test_normalize_email(self, voice_input, expected):
        """Test email normalization from voice input."""
        result = VoiceInputProcessor.normalize_voice_input(voice_input, 'email')
        assert result == expected
    
    @pytest.mark.parametrize("voice_input,expected_contains", [
        ("five five five one two three four", "555"),
        ("plus one five five five one two three four five six seven", "+1"),
        ("nine eight seven six five four three two one zero", "987"),
    ])
    def test_normalize_phone(self, voice_input, expected_contains):
        """Test phone normalization from voice input."""
        result = VoiceInputProcessor.normalize_voice_input(voice_input, 'tel')
        assert expected_contains in result
    
    def test_normalize_phone_formats_correctly(self):
        """Test that phone numbers are formatted with dashes."""
        result = VoiceInputProcessor.normalize_voice_input(
            "five five five one two three four five six seven",
            'tel'
        )
        # Should contain dashes for 10-digit number
        assert '-' in result or len(result.replace('-', '')) == 10
    
    def test_detect_spelled_out_text(self):
        """Test detection of spelled-out letters."""
        assert VoiceInputProcessor._is_spelled_out("j o h n at g m a i l")
        assert not VoiceInputProcessor._is_spelled_out("john at gmail")
    
    def test_detect_hesitation(self):
        """Test detection of hesitation markers."""
        assert VoiceInputProcessor.detect_hesitation("uh my name is john")
        assert VoiceInputProcessor.detect_hesitation("let me think")
        assert not VoiceInputProcessor.detect_hesitation("my name is john")
    
    def test_extract_partial_email(self):
        """Test partial email extraction for step-by-step entry."""
        result = VoiceInputProcessor.extract_partial_email("john@gmail.com")
        assert result['local_part'] == 'john'
        assert result['domain'] == 'gmail.com'
        assert result['is_complete'] is True
        
        result = VoiceInputProcessor.extract_partial_email("john")
        assert result['local_part'] == 'john'
        assert result['domain'] is None
        assert result['is_complete'] is False
    
    def test_stt_corrections_applied(self):
        """Test that common STT corrections are applied."""
        # Test various articulations
        assert '@' in VoiceInputProcessor.normalize_voice_input("john at sign gmail", 'email')
        assert '_' in VoiceInputProcessor.normalize_voice_input("john underscore doe", 'text')
        assert '-' in VoiceInputProcessor.normalize_voice_input("john dash smith", 'text')


# =============================================================================
# ClarificationStrategy Tests
# =============================================================================

class TestClarificationStrategy:
    """Tests for clarification escalation."""
    
    @pytest.fixture
    def email_field(self):
        return {"name": "email", "label": "Email Address", "type": "email"}
    
    @pytest.fixture
    def phone_field(self):
        return {"name": "phone", "label": "Phone Number", "type": "tel"}
    
    def test_first_attempt_rephrases(self, email_field):
        """First attempt should be a gentle rephrase."""
        response = ClarificationStrategy.get_clarification(email_field, 1)
        assert "again" in response.lower() or "try" in response.lower()
    
    def test_second_attempt_provides_format(self, email_field):
        """Second attempt should provide format examples."""
        response = ClarificationStrategy.get_clarification(email_field, 2)
        assert "like" in response.lower() or "example" in response.lower() or "try" in response.lower()
    
    def test_third_attempt_breaks_down(self, email_field):
        """Third attempt should break into smaller steps."""
        response = ClarificationStrategy.get_clarification(email_field, 3)
        assert "@" in response or "before" in response.lower() or "first" in response.lower()
    
    def test_fourth_attempt_offers_alternatives(self, email_field):
        """Fourth attempt should offer skip/type alternatives."""
        response = ClarificationStrategy.get_clarification(email_field, 4)
        assert "skip" in response.lower() or "type" in response.lower()
    
    def test_phone_field_clarification(self, phone_field):
        """Test phone-specific clarification."""
        response = ClarificationStrategy.get_clarification(phone_field, 2)
        assert "phone" in response.lower() or "number" in response.lower()


# =============================================================================
# ConfidenceCalibrator Tests
# =============================================================================

class TestConfidenceCalibrator:
    """Tests for dynamic confidence thresholds."""
    
    def test_email_is_critical(self):
        """Email fields should be classified as critical."""
        importance = ConfidenceCalibrator.get_field_importance("email", "email")
        assert importance == FieldImportance.CRITICAL
    
    def test_phone_is_critical(self):
        """Phone fields should be classified as critical."""
        importance = ConfidenceCalibrator.get_field_importance("phone_number", "tel")
        assert importance == FieldImportance.CRITICAL
    
    def test_name_is_high(self):
        """Name fields should be classified as high importance."""
        importance = ConfidenceCalibrator.get_field_importance("full_name", "text")
        assert importance == FieldImportance.HIGH
    
    def test_notes_is_low(self):
        """Notes/message fields should be classified as low importance."""
        importance = ConfidenceCalibrator.get_field_importance("notes", "textarea")
        assert importance == FieldImportance.LOW
    
    def test_should_confirm_critical_low_confidence(self):
        """Critical fields with low confidence should require confirmation."""
        should_confirm = ConfidenceCalibrator.should_confirm(
            field_name="email",
            field_type="email",
            confidence=0.70  # Below critical threshold of 0.90
        )
        assert should_confirm is True
    
    def test_should_not_confirm_high_confidence(self):
        """High confidence should not require confirmation."""
        should_confirm = ConfidenceCalibrator.should_confirm(
            field_name="email",
            field_type="email",
            confidence=0.95  # Above critical threshold
        )
        assert should_confirm is False
    
    def test_frustration_lowers_threshold(self):
        """Frustrated users should have lower confirmation threshold."""
        # Normal: 0.85 confidence would need confirmation for critical field
        normal = ConfidenceCalibrator.should_confirm("email", "email", 0.85)
        # Frustrated: same confidence should NOT need confirmation
        frustrated = ConfidenceCalibrator.should_confirm("email", "email", 0.85, is_frustrated=True)
        
        # With frustration, threshold drops by 0.10, so 0.85 > 0.80, no confirm needed
        assert normal is True
        assert frustrated is False
    
    def test_confirmation_prompt_varies_by_confidence(self):
        """Confirmation prompts should vary based on confidence level."""
        high_conf = ConfidenceCalibrator.generate_confirmation_prompt("email", "test@example.com", 0.90)
        low_conf = ConfidenceCalibrator.generate_confirmation_prompt("email", "test@example.com", 0.55)
        
        # Low confidence should be more explicit
        assert "yes" in low_conf.lower() or "no" in low_conf.lower()
        assert len(low_conf) > len(high_conf)


# =============================================================================
# MultiModalFallback Tests
# =============================================================================

class TestMultiModalFallback:
    """Tests for multi-modal fallback handling."""
    
    def test_email_triggers_fallback_after_2_failures(self):
        """Email should offer fallback after 2 failures (it's difficult)."""
        should_fallback = MultiModalFallback.should_offer_fallback(
            field_name="email",
            field_type="email",
            failure_count=2
        )
        assert should_fallback is True
    
    def test_regular_field_needs_3_failures(self):
        """Regular fields should need 3 failures before fallback."""
        should_fallback = MultiModalFallback.should_offer_fallback(
            field_name="company",
            field_type="text",
            failure_count=2
        )
        assert should_fallback is False
        
        should_fallback = MultiModalFallback.should_offer_fallback(
            field_name="company",
            field_type="text",
            failure_count=3
        )
        assert should_fallback is True
    
    def test_fallback_response_has_options(self):
        """Fallback response should include multiple options."""
        response = MultiModalFallback.generate_fallback_response("email")
        
        assert 'message' in response
        assert 'options' in response
        assert len(response['options']) >= 2


# =============================================================================
# NoiseHandler Tests
# =============================================================================

class TestNoiseHandler:
    """Tests for audio quality handling."""
    
    def test_high_confidence_is_good_quality(self):
        """High STT confidence should be good quality."""
        quality = NoiseHandler.assess_audio_quality(stt_confidence=0.95)
        assert quality == AudioQuality.GOOD
    
    def test_low_confidence_is_poor_quality(self):
        """Low STT confidence should be poor quality."""
        quality = NoiseHandler.assess_audio_quality(stt_confidence=0.50)
        assert quality == AudioQuality.POOR
    
    def test_medium_confidence_is_fair_quality(self):
        """Medium STT confidence should be fair quality."""
        quality = NoiseHandler.assess_audio_quality(stt_confidence=0.80)
        assert quality == AudioQuality.FAIR
    
    def test_poor_quality_critical_field_gets_response(self):
        """Poor quality on critical field should get helpful response."""
        response = NoiseHandler.get_quality_adapted_response(
            audio_quality=AudioQuality.POOR,
            field_type="email",
            is_critical=True
        )
        assert response is not None
        assert "quiet" in response.lower() or "type" in response.lower()
    
    def test_good_quality_no_adaptation(self):
        """Good quality should not need adaptation."""
        response = NoiseHandler.get_quality_adapted_response(
            audio_quality=AudioQuality.GOOD,
            field_type="email",
            is_critical=True
        )
        assert response is None


# =============================================================================
# StreamingSpeechHandler Tests
# =============================================================================

class TestStreamingSpeechHandler:
    """Tests for streaming speech processing."""
    
    def test_partial_accumulates(self):
        """Partial utterances should accumulate."""
        handler = StreamingSpeechHandler()
        
        handler.process_partial(PartialUtterance("my", False, 0, 0.9))
        handler.process_partial(PartialUtterance("name", False, 0.5, 0.9))
        handler.process_partial(PartialUtterance("is", False, 1.0, 0.9))
        
        accumulated = handler.get_accumulated_text()
        assert "my" in accumulated
        assert "name" in accumulated
    
    def test_final_returns_full_text(self):
        """Final utterance should return complete text."""
        handler = StreamingSpeechHandler()
        
        handler.process_partial(PartialUtterance("my name", False, 0, 0.9))
        result = handler.process_partial(PartialUtterance("is john", True, 1.0, 0.9))
        
        assert "john" in result
    
    def test_detects_hesitation_hint(self):
        """Should detect hesitation and provide hint."""
        handler = StreamingSpeechHandler()
        
        result = handler.process_partial(
            PartialUtterance("uh let me think", False, 0, 0.9),
            expected_field_type='text'
        )
        
        assert result is not None
        assert "HINT" in result


# =============================================================================
# Enhanced VoiceInputProcessor Tests
# =============================================================================

class TestVoiceInputProcessorEnhanced:
    """Tests for enhanced voice input features."""
    
    def test_normalize_name_simple(self):
        """Test simple name normalization."""
        result = VoiceInputProcessor.normalize_voice_input("john smith", 'name')
        assert result == "John Smith"
    
    def test_normalize_name_hyphenated(self):
        """Test hyphenated name normalization."""
        result = VoiceInputProcessor.normalize_voice_input("mary-jane watson", 'name')
        assert result == "Mary-Jane Watson"
    
    def test_normalize_name_apostrophe(self):
        """Test name with apostrophe."""
        result = VoiceInputProcessor.normalize_voice_input("john o'connor", 'name')
        assert result == "John O'Connor"
    
    def test_normalize_date_month_day_year(self):
        """Test date normalization with month day year."""
        result = VoiceInputProcessor.normalize_voice_input("january 5 2024", 'date')
        assert result == "01/05/2024"
    
    def test_normalize_date_ordinal(self):
        """Test date with ordinal number."""
        result = VoiceInputProcessor.normalize_voice_input("march fifth 2024", 'date')
        assert result == "03/05/2024"
    
    def test_normalize_address_basic(self):
        """Test basic address normalization."""
        result = VoiceInputProcessor.normalize_voice_input("one two three main street", 'address')
        assert "123" in result
        assert "St" in result
    
    def test_normalize_address_with_directions(self):
        """Test address with cardinal directions."""
        result = VoiceInputProcessor.normalize_voice_input("north main street", 'address')
        assert "N" in result
    
    def test_international_phone_with_context(self):
        """Test international phone formatting with country context."""
        result = VoiceInputProcessor.normalize_voice_input(
            "nine eight seven six five four three two one zero",
            'tel',
            context={'country': 'India'}
        )
        assert "+91" in result
    
    def test_learning_from_correction(self):
        """Test that the system learns from corrections."""
        # Clear any previous corrections
        VoiceInputProcessor._user_corrections.clear()
        
        # Learn a correction
        VoiceInputProcessor.learn_from_correction(
            "john at geemail dot com",
            "john@gmail.com"
        )
        
        # Check that correction was stored
        assert "john at geemail dot com" in VoiceInputProcessor._user_corrections
    
    def test_context_parameter_backward_compatible(self):
        """Test that context parameter is optional (backward compatible)."""
        # Should work without context
        result = VoiceInputProcessor.normalize_voice_input("john at gmail dot com", 'email')
        assert "@" in result
    
    def test_tld_correction(self):
        """Test TLD typo correction."""
        result = VoiceInputProcessor.normalize_voice_input("john at gmail dot calm", 'email')
        assert result == "john@gmail.com"
    
    def test_email_domain_autocomplete(self):
        """Test email domain auto-completion."""
        result = VoiceInputProcessor.normalize_voice_input("john at gmail", 'email')
        assert result == "john@gmail.com"


# =============================================================================
# PhoneticMatcher Tests
# =============================================================================

class TestPhoneticMatcher:
    """Tests for phonetic name matching."""
    
    def test_exact_match(self):
        """Test exact name match."""
        assert PhoneticMatcher.are_similar("John", "John") is True
        assert PhoneticMatcher.are_similar("john", "JOHN") is True
    
    def test_phonetic_match_jon_john(self):
        """Test phonetic match for Jon/John."""
        assert PhoneticMatcher.are_similar("Jon", "John") is True
    
    def test_phonetic_match_stephen_steven(self):
        """Test phonetic match for Stephen/Steven."""
        assert PhoneticMatcher.are_similar("Stephen", "Steven") is True
    
    def test_phonetic_different_names(self):
        """Test that different names don't match."""
        assert PhoneticMatcher.are_similar("John", "Mary", threshold=0.9) is False
    
    def test_phonetic_key_generation(self):
        """Test phonetic key generation."""
        key1 = PhoneticMatcher.get_phonetic_key("Robert")
        key2 = PhoneticMatcher.get_phonetic_key("Rupert")
        # Both should start with 'r'
        assert key1[0] == key2[0] == 'r'
    
    def test_find_best_match(self):
        """Test finding best match from candidates."""
        candidates = ["John Smith", "Jane Doe", "Michael Johnson"]
        result = PhoneticMatcher.find_best_match("Jon Smith", candidates)
        assert result == "John Smith"


# =============================================================================
# Multi-Signal Confidence Tests
# =============================================================================

class TestMultiSignalConfidence:
    """Tests for multi-signal confidence calculation."""
    
    def test_valid_email_increases_confidence(self):
        """Test that valid email format increases confidence."""
        confidence = ConfidenceCalibrator.calculate_confidence(
            field_name="email",
            field_type="email",
            extracted_value="john@gmail.com",
            stt_confidence=0.80
        )
        assert confidence > 0.80  # Should be boosted
    
    def test_invalid_email_decreases_confidence(self):
        """Test that invalid email format decreases confidence."""
        confidence = ConfidenceCalibrator.calculate_confidence(
            field_name="email",
            field_type="email",
            extracted_value="johngmail",  # No @ sign
            stt_confidence=0.80
        )
        assert confidence < 0.80  # Should be reduced
    
    def test_valid_phone_increases_confidence(self):
        """Test that valid phone format increases confidence."""
        confidence = ConfidenceCalibrator.calculate_confidence(
            field_name="phone",
            field_type="tel",
            extracted_value="(555) 123-4567",
            stt_confidence=0.80
        )
        assert confidence > 0.80  # Should be boosted
    
    def test_confidence_bounded(self):
        """Test that confidence is bounded between 0 and 1."""
        # Very high base confidence
        confidence = ConfidenceCalibrator.calculate_confidence(
            field_name="email",
            field_type="email",
            extracted_value="john@gmail.com",
            stt_confidence=0.99
        )
        assert confidence <= 1.0
        
        # Very low base confidence
        confidence = ConfidenceCalibrator.calculate_confidence(
            field_name="email",
            field_type="email",
            extracted_value="invalid",
            stt_confidence=0.10
        )
        assert confidence >= 0.0

