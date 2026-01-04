"""
Test the enhanced PDF parser to verify human-readable output.
"""
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "form-flow-backend"))

from services.pdf.pdf_parser import parse_pdf

def test_enhanced_parser():
    pdf_path = Path("form-flow-backend/storage/uploads/6aea5015-402d-4bca-affb-cda2a6cbed2c.pdf")
    if not pdf_path.exists():
        pdf_path = Path("form-flow-backend/storage/uploads/34484275-7707-41ac-aab7-66f7acbe1543.pdf")
    
    print(f"=== Testing Enhanced Parser: {pdf_path} ===\n")
    
    try:
        schema = parse_pdf(pdf_path)
        
        print(f"Total Fields: {schema.total_fields}")
        print(f"Is XFA: {schema.is_xfa}")
        print(f"Is Scanned: {schema.is_scanned}\n")
        
        print("=== FIRST 15 FIELDS ===\n")
        for i, field in enumerate(schema.fields[:15]):
            print(f"FIELD {i+1}:")
            print(f"  ID: {field.id[:50]}..." if len(field.id) > 50 else f"  ID: {field.id}")
            print(f"  Display Name: {field.display_name}")
            print(f"  Type: {field.field_type.value}")
            print(f"  Section: {field.section}")
            print(f"  Form Line: {field.form_line}")
            print(f"  Purpose: {field.purpose}")
            print()
        
        # Count how many have proper labels vs XFA IDs
        fields_with_labels = sum(1 for f in schema.fields if f.label and not f.label.startswith('topmostSubform'))
        print(f"\n=== SUMMARY ===")
        print(f"Total Fields: {len(schema.fields)}")
        print(f"Fields with proper labels: {fields_with_labels} ({100*fields_with_labels/len(schema.fields):.1f}%)")
        
        # Check for container nodes that should have been filtered
        container_count = sum(1 for f in schema.fields if 'Page1[0]' in f.id and f.id.endswith('[0]') and f.id.count('.') == 1)
        print(f"Container nodes (should be 0): {container_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_parser()
