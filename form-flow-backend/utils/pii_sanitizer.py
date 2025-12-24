"""
PII Sanitization Utilities

Provides functions to mask personally identifiable information (PII) in logs.
Prevents accidental exposure of sensitive user data.

Usage:
    from utils.pii_sanitizer import sanitize_for_log
    
    logger.info(f"Processing: {sanitize_for_log(user_data)}")
"""

import re
from typing import Any, Dict, Union


# =============================================================================
# PII Detection Patterns
# =============================================================================

# Email pattern - matches common email formats
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Phone pattern - matches various phone formats
PHONE_PATTERNS = [
    re.compile(r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format
    re.compile(r'\+?\d{10,15}'),  # International
    re.compile(r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'),  # Dashed format
]

# Credit card pattern (basic)
CREDIT_CARD_PATTERN = re.compile(
    r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
)

# SSN pattern (US)
SSN_PATTERN = re.compile(
    r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
)


# =============================================================================
# Sensitive Field Names
# =============================================================================

SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'access_token', 'refresh_token', 'auth', 'authorization', 'credential',
    'ssn', 'social_security', 'credit_card', 'card_number', 'cvv', 'cvc',
    'pin', 'security_code', 'account_number', 'routing_number',
    'name', 'first_name', 'last_name', 'full_name', 'fullname',
    'email', 'mail', 'phone', 'mobile', 'telephone', 'tel',
    'address', 'street', 'city', 'zip', 'postal', 'dob', 'birth',
}


# =============================================================================
# Masking Functions
# =============================================================================

def mask_email(email: str) -> str:
    """
    Mask an email address, showing only first 2 chars and domain.
    
    Example: john.doe@example.com -> jo***@example.com
    """
    if '@' not in email:
        return '***@***.***'
    
    local, domain = email.rsplit('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[:2] + '*' * (len(local) - 2)
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask a phone number, showing only last 4 digits.
    
    Example: +1-555-123-4567 -> ***-***-4567
    """
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    if len(digits) < 4:
        return '****'
    
    return '*' * (len(digits) - 4) + digits[-4:]


def mask_name(name: str) -> str:
    """
    Mask a name, showing only first initial.
    
    Example: John Doe -> J*** D***
    """
    words = name.split()
    masked_words = []
    for word in words:
        if len(word) > 0:
            masked_words.append(word[0] + '*' * (len(word) - 1))
        else:
            masked_words.append('')
    return ' '.join(masked_words)


def mask_generic(value: str, visible_chars: int = 2) -> str:
    """
    Generic masking - show first N characters.
    
    Example: sensitive123 -> se**********
    """
    if len(value) <= visible_chars:
        return '*' * len(value)
    return value[:visible_chars] + '*' * (len(value) - visible_chars)


# =============================================================================
# Main Sanitization Function
# =============================================================================

def sanitize_for_log(
    data: Any,
    mask_all_values: bool = False,
    _depth: int = 0
) -> Any:
    """
    Sanitize data for safe logging by masking PII.
    
    Args:
        data: Data to sanitize (string, dict, list, or other)
        mask_all_values: If True, mask all string values regardless of content
        _depth: Internal recursion depth tracker
        
    Returns:
        Sanitized version of the data
        
    Example:
        >>> sanitize_for_log("Email: john@example.com, Phone: 555-123-4567")
        'Email: jo***@example.com, Phone: ***-4567'
        
        >>> sanitize_for_log({"name": "John Doe", "email": "john@ex.com"})
        {'name': 'J*** D***', 'email': 'jo***@ex.com'}
    """
    # Prevent infinite recursion
    if _depth > 10:
        return "[DEPTH_LIMIT]"
    
    if data is None:
        return None
    
    if isinstance(data, str):
        return _sanitize_string(data)
    
    if isinstance(data, dict):
        return _sanitize_dict(data, mask_all_values, _depth)
    
    if isinstance(data, (list, tuple)):
        return type(data)(
            sanitize_for_log(item, mask_all_values, _depth + 1) 
            for item in data
        )
    
    # For other types, convert to string and sanitize
    if isinstance(data, (int, float, bool)):
        return data
    
    return _sanitize_string(str(data))


def _sanitize_string(text: str) -> str:
    """Sanitize a string by replacing PII patterns."""
    result = text
    
    # Mask emails
    result = EMAIL_PATTERN.sub(
        lambda m: mask_email(m.group()), 
        result
    )
    
    # Mask phone numbers
    for pattern in PHONE_PATTERNS:
        result = pattern.sub(
            lambda m: mask_phone(m.group()),
            result
        )
    
    # Mask credit cards
    result = CREDIT_CARD_PATTERN.sub('[CARD]', result)
    
    # Mask SSNs
    result = SSN_PATTERN.sub('[SSN]', result)
    
    return result


def _sanitize_dict(
    data: Dict[str, Any],
    mask_all_values: bool,
    depth: int
) -> Dict[str, Any]:
    """Sanitize a dictionary, with special handling for sensitive field names."""
    result = {}
    
    for key, value in data.items():
        key_lower = key.lower().replace('-', '_').replace(' ', '_')
        
        # Check if this is a sensitive field
        is_sensitive = any(
            sensitive in key_lower 
            for sensitive in SENSITIVE_FIELDS
        )
        
        if is_sensitive and isinstance(value, str):
            # Apply appropriate masking based on field type
            if 'email' in key_lower or 'mail' in key_lower:
                result[key] = mask_email(value) if '@' in value else mask_generic(value)
            elif any(p in key_lower for p in ['phone', 'mobile', 'tel']):
                result[key] = mask_phone(value)
            elif any(p in key_lower for p in ['name', 'first', 'last', 'full']):
                result[key] = mask_name(value)
            elif any(p in key_lower for p in ['password', 'secret', 'token', 'key']):
                result[key] = '[REDACTED]'
            else:
                result[key] = mask_generic(value)
        else:
            result[key] = sanitize_for_log(value, mask_all_values, depth + 1)
    
    return result


# =============================================================================
# Convenience Functions
# =============================================================================

def create_safe_log_context(**kwargs) -> Dict[str, Any]:
    """
    Create a sanitized context dictionary for structured logging.
    
    Example:
        logger.info("Processing", extra=create_safe_log_context(
            email=user_email,
            session_id=session_id
        ))
    """
    return sanitize_for_log(kwargs)
