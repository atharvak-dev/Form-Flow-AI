#!/usr/bin/env python3
"""
Test PDF field mapping issue
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_field_mapping():
    """Test field name mapping logic"""
    
    # Simulate the data that was logged
    collected_data = {
        "field_3_full_name": "Atharva Karval"
    }
    
    # Simulate what the PDF writer might be looking for
    possible_field_names = [
        "field_3_full_name",
        "full_name", 
        "name",
        "applicant_name",
        "Full Name",
        "Name"
    ]
    
    print("Testing field name matching:")
    print(f"Data provided: {collected_data}")
    print(f"Possible field names in PDF: {possible_field_names}")
    
    # Test exact match
    for field_name in possible_field_names:
        if field_name in collected_data:
            print(f"✓ EXACT MATCH: {field_name} -> {collected_data[field_name]}")
        else:
            print(f"✗ No match: {field_name}")
    
    # Test fuzzy matching (like the PDF writer does)
    print("\nTesting fuzzy matching:")
    for pdf_field in possible_field_names:
        for data_field, value in collected_data.items():
            if (data_field.lower() in pdf_field.lower() or 
                pdf_field.lower() in data_field.lower()):
                print(f"✓ FUZZY MATCH: {pdf_field} <-> {data_field} -> {value}")
                break
        else:
            print(f"✗ No fuzzy match: {pdf_field}")

def test_visual_form_parsing():
    """Test the visual form parsing logic"""
    
    # Sample text that might be found in a PDF
    sample_lines = [
        "Full Name: _______________",
        "Email Address: ___________", 
        "Phone Number: ____________",
        "Date of Birth (DD/MM/YYYY): _______",
        "Emergency Contact Name & Relation: __________",
        "Emergency Contact Number: _________",
        "Applicant Name: __________",
        "Company's Authorized Person Name: _________",
        "Company's Authorized Person Signature: _______"
    ]
    
    print("\nTesting visual form field detection:")
    
    import re
    field_patterns = [
        (r'^(.+?):\s*_{2,}\s*$', 'text'), # "Label: ____"
        (r'^(.+?)\s*\([^)]+\):\s*_{2,}\s*$', 'text'), # "Label (Hint): ____"
        (r'^([A-Za-z][A-Za-z\s&/-]{2,50}):\s*$', 'text'), # "Label: "
    ]
    
    field_id = 0
    for line in sample_lines:
        print(f"Line: '{line}'")
        
        for pattern, field_type in field_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                label = match.group(1).strip()
                label = re.sub(r'\s+', ' ', label)
                label = label.rstrip(':').strip()
                
                field_id += 1
                field_name = f"field_{field_id}_{label.lower().replace(' ', '_')[:30]}"
                
                print(f"  ✓ DETECTED: {field_name} (label: '{label}', type: {field_type})")
                break
        else:
            print(f"  ✗ Not detected")
        print()

if __name__ == "__main__":
    test_field_mapping()
    test_visual_form_parsing()