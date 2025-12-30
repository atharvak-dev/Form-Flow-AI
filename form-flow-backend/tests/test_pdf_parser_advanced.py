
import pytest
from unittest.mock import MagicMock
from services.pdf.pdf_parser import (
    _detect_field_type_enhanced,
    _extract_validation_rules,
    _group_fields,
    FieldType,
    FieldGroup,
    GroupType,
    PdfField,
    FieldContext,
    FieldPosition,
    FieldConstraints
)

class TestAdvancedParser:
    
    def test_detect_field_type_enhanced_date(self):
        context = FieldContext(nearby_text="Date of Birth", instructions="MM/DD/YYYY")
        ft = _detect_field_type_enhanced({}, "dob_field", context)
        assert ft == FieldType.DATE

    def test_detect_field_type_enhanced_email(self):
        context = FieldContext(nearby_text="Contact Email Address")
        ft = _detect_field_type_enhanced({}, "contact_field", context)
        assert ft == FieldType.EMAIL

    def test_detect_field_type_enhanced_phone(self):
        context = FieldContext(nearby_text="Mobile Number")
        ft = _detect_field_type_enhanced({}, "phone_field", context)
        assert ft == FieldType.PHONE

    def test_extract_validation_rules_date(self):
        context = FieldContext(nearby_text="", instructions="Please enter in MM/DD/YYYY format")
        constraints = _extract_validation_rules({}, context)
        assert constraints.pattern == r"^\d{2}/\d{2}/\d{4}$"

    def test_extract_validation_rules_required(self):
        context = FieldContext(nearby_text="First Name *", is_required_visually=True)
        constraints = _extract_validation_rules({}, context)
        assert constraints.required is True

    def test_group_fields_radio(self):
        f1 = PdfField(id="r1", name="gender", field_type=FieldType.RADIO, label="Male", position=MagicMock(), constraints=MagicMock())
        f2 = PdfField(id="r2", name="gender", field_type=FieldType.RADIO, label="Female", position=MagicMock(), constraints=MagicMock())
        fields = [f1, f2]
        
        groups = _group_fields(fields)
        assert len(groups) == 1
        assert groups[0].id == "group_radio_gender"
        assert len(groups[0].fields) == 2

    def test_group_fields_address(self):
        f1 = PdfField(id="a1", name="addr", field_type=FieldType.TEXT, label="Street", purpose="address", position=MagicMock(), constraints=MagicMock())
        f2 = PdfField(id="a2", name="city", field_type=FieldType.TEXT, label="City", purpose="city", position=MagicMock(), constraints=MagicMock())
        f3 = PdfField(id="a3", name="zip", field_type=FieldType.TEXT, label="Zip", purpose="zip", position=MagicMock(), constraints=MagicMock())
        fields = [f1, f2, f3]
        
        groups = _group_fields(fields)
        assert len(groups) == 1
        assert groups[0].group_type == GroupType.ADDRESS
        assert "a1" in groups[0].fields
        assert "a3" in groups[0].fields
