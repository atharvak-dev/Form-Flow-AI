"""
Unified Exception Hierarchy for PDF Services.

This module defines the standard exceptions thrown by the PDF parser, writer,
and text fitter. Using a unified hierarchy allows for consistent error handling,
logging, and reporting across the application.
"""

from typing import Optional, Any, Dict

class PdfServiceError(Exception):
    """
    Base exception for all PDF service errors.
    
    Attributes:
        message (str): Human-readable error message.
        details (Optional[Dict[str, Any]]): Additional context about the error.
        original_error (Optional[Exception]): The underlying exception, if any.
    """
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None, 
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error

    def __str__(self):
        error_msg = self.message
        if self.details:
            error_msg += f" | Details: {self.details}"
        if self.original_error:
            error_msg += f" | Caused by: {repr(self.original_error)}"
        return error_msg


class PdfParsingError(PdfServiceError):
    """
    Raised when PDF parsing fails.
    
    Examples:
        - Corrupted PDF file.
        - Failure to extract fields.
        - OCR failure.
    """
    pass


class PdfFillingError(PdfServiceError):
    """
    Raised when form filling fails.
    
    Examples:
        - Field not found.
        - Value does not fit constraints.
        - PDF write permission denied.
    """
    pass


class PdfValidationError(PdfServiceError):
    """
    Raised when data validation fails before filling.
    
    Examples:
        - Required field missing.
        - Invalid format (e.g., malformed email).
        - Value exceeds max length.
    """
    pass


class PdfResourceError(PdfServiceError):
    """
    Raised when a required resource is unavailable.
    
    Examples:
        - Missing font file.
        - Missing dependency (e.g., Poppler for OCR).
        - LLM service unavailable.
    """
    pass


class PdfConfigurationError(PdfServiceError):
    """
    Raised when the service is misconfigured.
    
    Examples:
        - Invalid option passed to parser.
        - Missing API keys.
    """
    pass
