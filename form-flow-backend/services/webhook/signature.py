"""
Webhook Signature Module

Provides HMAC-SHA256 signature generation and verification for webhook payloads.

Usage:
    from services.webhook.signature import generate_signature, verify_signature
    
    # Generate signature
    signature = generate_signature(payload, secret, timestamp)
    
    # Verify signature
    is_valid = verify_signature(payload, secret, timestamp, signature)
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Any

# Maximum age of webhook payload in seconds (5 minutes)
MAX_SIGNATURE_AGE_SECONDS = 300


def generate_signature(payload: Dict[str, Any], secret: str, timestamp: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload: JSON-serializable dictionary
        secret: Webhook secret
        timestamp: Unix timestamp string
        
    Returns:
        HMAC-SHA256 signature in format: sha256={hex_signature}
    """
    # Sort keys for consistent serialization
    payload_json = json.dumps(payload, sort_keys=True)
    
    # Create message: timestamp.payload
    message = f"{timestamp}.{payload_json}"
    
    # Generate HMAC-SHA256
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_signature(
    payload: Dict[str, Any],
    secret: str,
    timestamp: str,
    signature: str
) -> bool:
    """
    Verify HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload: JSON-serializable dictionary
        secret: Webhook secret
        timestamp: Unix timestamp string
        signature: Signature to verify (should start with "sha256=")
        
    Returns:
        True if signature is valid and not expired
        False if signature is invalid or expired (>5 minutes old)
    """
    # Check signature format
    if not signature.startswith("sha256="):
        return False
    
    # Check timestamp is within allowed age
    try:
        timestamp_int = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - timestamp_int) > MAX_SIGNATURE_AGE_SECONDS:
            return False
    except (ValueError, TypeError):
        return False
    
    # Generate expected signature
    expected_signature = generate_signature(payload, secret, timestamp)
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)