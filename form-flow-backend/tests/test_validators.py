"""
Unit Tests for Validators Module

Tests input validation for form schemas, user input, and session data.
"""

import pytest
from utils.validators import (
    validate_form_schema,
    validate_user_input,
    validate_session_data,
    validate_email,
    validate_phone,
    InputValidationError
)


# =============================================================================
# Form Schema Validation Tests
# =============================================================================

class TestValidateFormSchema:
    """Tests for validate_form_schema function."""
    
    def test_valid_schema_single_form(self):
        """Test that a valid single-form schema passes validation."""
        schema = [
            {
                "form_id": "test_form",
                "fields": [
                    {"name": "email", "label": "Email", "type": "email"},
                    {"name": "name", "label": "Full Name", "type": "text"}
                ]
            }
        ]
        result = validate_form_schema(schema)
        assert result == schema
    
    def test_valid_schema_multiple_forms(self):
        """Test that a valid multi-form schema passes validation."""
        schema = [
            {"form_id": "form1", "fields": [{"name": "field1", "type": "text"}]},
            {"form_id": "form2", "fields": [{"name": "field2", "type": "email"}]}
        ]
        result = validate_form_schema(schema)
        assert result == schema
    
    def test_none_schema_raises_error(self):
        """Test that None schema raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_form_schema(None)
        assert "cannot be None" in str(exc_info.value)
    
    def test_non_list_schema_raises_error(self):
        """Test that non-list schema raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_form_schema({"fields": []})
        assert "must be a list" in str(exc_info.value)
    
    def test_empty_schema_raises_error(self):
        """Test that empty schema raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_form_schema([])
        assert "cannot be empty" in str(exc_info.value)
    
    def test_non_dict_form_raises_error(self):
        """Test that non-dict form entry raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_form_schema(["not_a_dict"])
        assert "must be a dictionary" in str(exc_info.value)
    
    def test_field_without_name_raises_error(self):
        """Test that field without name/id/label raises InputValidationError."""
        schema = [{"fields": [{"type": "text"}]}]
        with pytest.raises(InputValidationError) as exc_info:
            validate_form_schema(schema)
        assert "at least a name, id, or label" in str(exc_info.value)
    
    def test_field_with_only_id_passes(self):
        """Test that field with only id passes validation."""
        schema = [{"fields": [{"id": "test_id"}]}]
        result = validate_form_schema(schema)
        assert result == schema
    
    def test_field_with_only_label_passes(self):
        """Test that field with only label passes validation."""
        schema = [{"fields": [{"label": "Test Label"}]}]
        result = validate_form_schema(schema)
        assert result == schema


# =============================================================================
# User Input Validation Tests
# =============================================================================

class TestValidateUserInput:
    """Tests for validate_user_input function."""
    
    def test_valid_input(self):
        """Test that valid input passes validation."""
        result = validate_user_input("Hello, my name is John")
        assert result == "Hello, my name is John"
    
    def test_strips_whitespace(self):
        """Test that input is stripped of leading/trailing whitespace."""
        result = validate_user_input("   Hello   ")
        assert result == "Hello"
    
    def test_none_input_raises_error(self):
        """Test that None input raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_user_input(None)
        assert "cannot be None" in str(exc_info.value)
    
    def test_non_string_input_raises_error(self):
        """Test that non-string input raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_user_input(12345)
        assert "must be a string" in str(exc_info.value)
    
    def test_empty_input_raises_error(self):
        """Test that empty input raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_user_input("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_empty_allowed_when_flag_set(self):
        """Test that empty input passes when allow_empty=True."""
        result = validate_user_input("", allow_empty=True)
        assert result == ""
    
    def test_exceeds_max_length_raises_error(self):
        """Test that input exceeding max_length raises InputValidationError."""
        long_input = "x" * 100
        with pytest.raises(InputValidationError) as exc_info:
            validate_user_input(long_input, max_length=50)
        assert "exceeds maximum length" in str(exc_info.value)
    
    def test_sanitizes_script_tags(self):
        """Test that dangerous script tags are removed."""
        result = validate_user_input("Hello <script>alert('xss')</script> World")
        assert "<script>" not in result
        assert "Hello" in result and "World" in result


# =============================================================================
# Session Data Validation Tests
# =============================================================================

class TestValidateSessionData:
    """Tests for validate_session_data function."""
    
    def test_valid_session_data(self):
        """Test that valid session data passes validation."""
        data = {
            "id": "12345678-1234-1234-1234-123456789abc",
            "form_schema": [{"fields": []}]
        }
        result = validate_session_data(data)
        assert result == data
    
    def test_none_session_data_raises_error(self):
        """Test that None session data raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_session_data(None)
        assert "cannot be None" in str(exc_info.value)
    
    def test_missing_id_raises_error(self):
        """Test that missing id raises InputValidationError."""
        data = {"form_schema": []}
        with pytest.raises(InputValidationError) as exc_info:
            validate_session_data(data)
        assert "missing required field" in str(exc_info.value)
    
    def test_invalid_uuid_raises_error(self):
        """Test that invalid UUID format raises InputValidationError."""
        data = {
            "id": "not-a-valid-uuid",
            "form_schema": [{"fields": []}]
        }
        with pytest.raises(InputValidationError) as exc_info:
            validate_session_data(data)
        assert "valid UUID" in str(exc_info.value)


# =============================================================================
# Email Validation Tests
# =============================================================================

class TestValidateEmail:
    """Tests for validate_email function."""
    
    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user.name@domain.org",
        "user+tag@example.co.uk",
        "simple@test.io",
    ])
    def test_valid_emails(self, email):
        """Test that valid emails pass validation."""
        assert validate_email(email) is True
    
    @pytest.mark.parametrize("email", [
        "",
        "not_an_email",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com",
        None,
    ])
    def test_invalid_emails(self, email):
        """Test that invalid emails fail validation."""
        assert validate_email(email) is False


# =============================================================================
# Phone Validation Tests
# =============================================================================

class TestValidatePhone:
    """Tests for validate_phone function."""
    
    @pytest.mark.parametrize("phone", [
        "+1234567890",
        "1234567890",
        "+44 20 7946 0958",
        "(555) 123-4567",
        "+91-9876543210",
    ])
    def test_valid_phones(self, phone):
        """Test that valid phone numbers pass validation."""
        assert validate_phone(phone) is True
    
    @pytest.mark.parametrize("phone", [
        "",
        "12345",  # Too short
        "abc",
        None,
    ])
    def test_invalid_phones(self, phone):
        """Test that invalid phone numbers fail validation."""
        assert validate_phone(phone) is False
