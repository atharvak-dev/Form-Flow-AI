
import pytest
from unittest.mock import MagicMock, patch
from services.pdf.pdf_writer import PdfFormWriter, ValueTransformer, FieldFillResult

class TestValueTransformer:
    def test_format_phone(self):
        assert ValueTransformer.transform("1234567890", "phone") == "(123) 456-7890"
        assert ValueTransformer.transform("555-123-4567", "phone") == "(555) 123-4567"
        assert ValueTransformer.transform("123", "phone") == "123" # Too short

    def test_format_date(self):
        assert ValueTransformer.transform("2023-12-25", "date") == "12/25/2023"
        assert ValueTransformer.transform("12/25/2023", "date") == "12/25/2023"
        
    def test_format_ssn(self):
        assert ValueTransformer.transform("123456789", "ssn") == "123-45-6789"

class TestSmartFieldMatching:
    def setup_method(self):
        self.writer = PdfFormWriter()
        
    def test_exact_match(self):
        fields = ["FirstName", "LastName"]
        assert self.writer._smart_match_field("FirstName", fields) == "FirstName"
        
    def test_case_insensitive_match(self):
        fields = ["FirstName", "LastName"]
        assert self.writer._smart_match_field("firstname", fields) == "FirstName"
        
    def test_clean_match(self):
        fields = ["First Name", "Last Name"]
        assert self.writer._smart_match_field("firstname", fields) == "First Name"
        
    def test_fuzzy_match(self):
        fields = ["EmployeeAddress", "City"]
        # Typo in input
        assert self.writer._smart_match_field("EmployeeAdress", fields) == "EmployeeAddress"

@patch('services.pdf.pdf_writer.PdfWriter')
class TestPdfFilling:
    def setup_method(self):
        self.writer = PdfFormWriter()
        
    def test_fill_field_with_transformation(self, MockPdfWriter):
        mock_writer = MockPdfWriter()
        fields = {
            "PhoneNumber": {"/FT": "/Tx"}
        }
        
        # Input raw number, expect formatted
        result = self.writer._fill_field(
            mock_writer, 
            "phone_number", # mismatch case
            "1234567890", 
            fields
        )
        
        assert result.success
        assert result.field_name == "PhoneNumber" # Resolve match
        assert result.filled_value == "(123) 456-7890" # Transformed
