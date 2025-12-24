"""
Input Validation Utilities

Provides validation functions for form schemas, user input, and session data.
Helps prevent malformed data from causing runtime errors.

Usage:
    from utils.validators import validate_form_schema, validate_user_input
    
    validate_form_schema(schema)  # Raises InputValidationError on failure
    cleaned = validate_user_input(user_input)
"""

import re
from typing import Dict, List, Any, Optional
from utils.exceptions import FormFlowError


class InputValidationError(FormFlowError):
    """
    Raised when input validation fails.
    
    Common causes:
        - Malformed form schema
        - Empty or invalid user input
        - Missing required session fields
    """
    
    def __init__(
        self,
        message: str = "Input validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details={"field": field, **(details or {})},
            status_code=400
        )


# =============================================================================
# Form Schema Validation
# =============================================================================

def validate_form_schema(schema: Any) -> List[Dict[str, Any]]:
    """
    Validate form schema structure.
    
    Args:
        schema: Form schema to validate
        
    Returns:
        Validated schema (passed through if valid)
        
    Raises:
        InputValidationError: If schema is malformed
    """
    if schema is None:
        raise InputValidationError(
            message="Form schema cannot be None",
            field="form_schema"
        )
    
    if not isinstance(schema, list):
        raise InputValidationError(
            message="Form schema must be a list",
            field="form_schema",
            details={"received_type": type(schema).__name__}
        )
    
    if len(schema) == 0:
        raise InputValidationError(
            message="Form schema cannot be empty",
            field="form_schema"
        )
    
    # Validate each form in schema
    for i, form in enumerate(schema):
        if not isinstance(form, dict):
            raise InputValidationError(
                message=f"Form at index {i} must be a dictionary",
                field=f"form_schema[{i}]",
                details={"received_type": type(form).__name__}
            )
        
        # Check for fields key
        fields = form.get('fields')
        if fields is not None and not isinstance(fields, list):
            raise InputValidationError(
                message=f"Fields in form at index {i} must be a list",
                field=f"form_schema[{i}].fields"
            )
        
        # Validate each field
        if fields:
            for j, field in enumerate(fields):
                _validate_field_definition(field, f"form_schema[{i}].fields[{j}]")
    
    return schema


def _validate_field_definition(field: Any, path: str) -> None:
    """Validate a single field definition."""
    if not isinstance(field, dict):
        raise InputValidationError(
            message=f"Field must be a dictionary",
            field=path,
            details={"received_type": type(field).__name__}
        )
    
    # Field must have a name or some identifier
    if not field.get('name') and not field.get('id') and not field.get('label'):
        raise InputValidationError(
            message="Field must have at least a name, id, or label",
            field=path
        )


# =============================================================================
# User Input Validation
# =============================================================================

# Maximum input length to prevent DoS
MAX_INPUT_LENGTH = 10000
MIN_INPUT_LENGTH = 1

# Pattern for potentially dangerous content
DANGEROUS_PATTERNS = [
    r'<script\b[^>]*>.*?</script>',  # Script tags
    r'javascript:',  # JavaScript URIs
    r'on\w+\s*=',  # Event handlers
]


def validate_user_input(
    user_input: Any,
    max_length: int = MAX_INPUT_LENGTH,
    allow_empty: bool = False
) -> str:
    """
    Validate and sanitize user input.
    
    Args:
        user_input: Raw user input
        max_length: Maximum allowed length
        allow_empty: Whether to allow empty input
        
    Returns:
        Sanitized user input string
        
    Raises:
        InputValidationError: If input is invalid
    """
    if user_input is None:
        if allow_empty:
            return ""
        raise InputValidationError(
            message="User input cannot be None",
            field="user_input"
        )
    
    if not isinstance(user_input, str):
        raise InputValidationError(
            message="User input must be a string",
            field="user_input",
            details={"received_type": type(user_input).__name__}
        )
    
    # Strip whitespace
    cleaned = user_input.strip()
    
    if not allow_empty and len(cleaned) < MIN_INPUT_LENGTH:
        raise InputValidationError(
            message="User input cannot be empty",
            field="user_input"
        )
    
    if len(cleaned) > max_length:
        raise InputValidationError(
            message=f"User input exceeds maximum length of {max_length}",
            field="user_input",
            details={"length": len(cleaned), "max_length": max_length}
        )
    
    # Check for dangerous content (log but don't block - just sanitize)
    for pattern in DANGEROUS_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    return cleaned


# =============================================================================
# Session Data Validation
# =============================================================================

REQUIRED_SESSION_FIELDS = ['id', 'form_schema']


def validate_session_data(session_data: Any) -> Dict[str, Any]:
    """
    Validate session data structure.
    
    Args:
        session_data: Session data to validate
        
    Returns:
        Validated session data (passed through if valid)
        
    Raises:
        InputValidationError: If session data is malformed
    """
    if session_data is None:
        raise InputValidationError(
            message="Session data cannot be None",
            field="session_data"
        )
    
    if not isinstance(session_data, dict):
        raise InputValidationError(
            message="Session data must be a dictionary",
            field="session_data",
            details={"received_type": type(session_data).__name__}
        )
    
    # Check required fields
    for field in REQUIRED_SESSION_FIELDS:
        if field not in session_data:
            raise InputValidationError(
                message=f"Session data missing required field: {field}",
                field=f"session_data.{field}"
            )
    
    # Validate session ID format (should be UUID)
    session_id = session_data.get('id')
    if session_id and not _is_valid_uuid(str(session_id)):
        raise InputValidationError(
            message="Session ID must be a valid UUID",
            field="session_data.id"
        )
    
    return session_data


def _is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID format."""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, value.lower()))


# =============================================================================
# Value Validators (RFC-compliant)
# =============================================================================

# RFC 5321 email pattern (simplified but robust)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# E.164 phone pattern (international format)
PHONE_PATTERN = re.compile(
    r'^\+?[1-9]\d{6,14}$'
)


def validate_email(email: str) -> bool:
    """
    Validate email against RFC 5321 pattern.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number against E.164 format.
    
    Args:
        phone: Phone number to validate (digits only or with +)
        
    Returns:
        True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone.strip())
    return bool(PHONE_PATTERN.match(cleaned))
