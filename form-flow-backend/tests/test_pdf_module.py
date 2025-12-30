"""
Tests for PDF Parser

Tests field extraction from PDF forms.
"""

import pytest
from pathlib import Path
from typing import Dict, Any
import tempfile
import io

# Import PDF services
from services.pdf.pdf_parser import (
    parse_pdf,
    PdfFormSchema,
    PdfField,
    FieldType,
    _detect_field_type,
    _detect_purpose,
)
from services.pdf.text_fitter import (
    TextFitter,
    FitResult,
    fit_text,
)





class TestFieldTypeDetection:
    """Tests for field type detection."""
    
    def test_email_detection(self):
        """Email fields should be detected from name."""
        purpose = _detect_purpose("email_address", "")
        assert purpose == "email"
        
        purpose = _detect_purpose("user_email", "Your E-mail")
        assert purpose == "email"
    
    def test_phone_detection(self):
        """Phone fields should be detected."""
        purpose = _detect_purpose("phone_number", "")
        assert purpose == "phone"
        
        purpose = _detect_purpose("contact_tel", "Mobile Number")
        assert purpose == "phone"
    
    def test_name_detection(self):
        """Name fields should be detected."""
        purpose = _detect_purpose("first_name", "")
        assert purpose == "first_name"
        
        purpose = _detect_purpose("last_name", "Surname")
        assert purpose == "last_name"
    
    def test_address_detection(self):
        """Address fields should be detected."""
        purpose = _detect_purpose("street_address", "")
        assert purpose == "address"
        
        purpose = _detect_purpose("addr1", "Mailing Address")
        assert purpose == "address"


# =============================================================================
# Integration-like Tests (without actual PDF)
# =============================================================================

class TestPdfSchemaConversion:
    """Tests for schema conversion utilities."""
    
    def test_field_to_dict(self):
        """PdfField should convert to dict correctly."""
        from services.pdf.pdf_parser import FieldPosition, FieldConstraints
        
        field = PdfField(
            id="test_field",
            name="test_field",
            field_type=FieldType.TEXT,
            label="Test Field",
            position=FieldPosition(page=0, x=100, y=200, width=150, height=20),
            constraints=FieldConstraints(max_length=50, required=True),
            display_name="Test Field",
        )
        
        d = field.to_dict()
        
        assert d["id"] == "test_field"
        assert d["type"] == "text"
        assert d["label"] == "Test Field"
        assert d["constraints"]["max_length"] == 50
        assert d["constraints"]["required"] == True
    
    def test_schema_to_dict(self):
        """PdfFormSchema should convert correctly."""
        from services.pdf.pdf_parser import FieldPosition, FieldConstraints
        
        schema = PdfFormSchema(
            file_path="/test/form.pdf",
            file_name="form.pdf",
            total_pages=2,
            fields=[
                PdfField(
                    id="f1",
                    name="f1",
                    field_type=FieldType.TEXT,
                    label="Field 1",
                    position=FieldPosition(page=0, x=0, y=0, width=100, height=20),
                    constraints=FieldConstraints(),
                ),
            ],
        )
        
        d = schema.to_dict()
        
        assert d["source"] == "pdf"
        assert d["total_pages"] == 2
        assert d["total_fields"] == 1
        assert len(d["fields"]) == 1



