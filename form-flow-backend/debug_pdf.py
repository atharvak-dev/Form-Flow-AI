#!/usr/bin/env python3
"""
Debug PDF filling issue
"""

import sys
import json
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.pdf import parse_pdf, fill_pdf

def debug_pdf_filling():
    """Debug PDF parsing and filling"""
    
    # Check if there are any uploaded PDFs
    storage_dir = Path("storage/uploads")
    if not storage_dir.exists():
        print("No storage directory found")
        return
    
    pdf_files = list(storage_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in storage")
        return
    
    # Use the most recent PDF
    latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing: {latest_pdf.name}")
    
    # Parse the PDF
    try:
        pdf_bytes = latest_pdf.read_bytes()
        schema = parse_pdf(pdf_bytes)
        
        print(f"PDF Info:")
        print(f"  - Pages: {schema.total_pages}")
        print(f"  - Fields: {schema.total_fields}")
        print(f"  - Scanned: {schema.is_scanned}")
        print(f"  - XFA: {schema.is_xfa}")
        
        print(f"\nFields found:")
        for i, field in enumerate(schema.fields, 1):
            print(f"  {i}. {field.name}")
            print(f"     Label: {field.label}")
            print(f"     Display: {field.display_name}")
            print(f"     Type: {field.field_type.value}")
            print(f"     Purpose: {field.purpose}")
            print(f"     Position: Page {field.position.page}, X={field.position.x:.1f}, Y={field.position.y:.1f}")
            print()
        
        # Test filling with comprehensive sample data that matches the PDF fields
        test_data = {
            "field_3_full_name": "Atharva Karval",
            "full_name": "Atharva Karval",
            "date": "30/12/2025",
            "date_of_birth": "15/01/2000",
            "gender": "Male",
            "marital_status": "Single",
            "current_address": "123 Main Street, Mumbai",
            "permanent_address": "456 Home Street, Pune",
            "primary_contact_number": "+91 9876543210",
            "alternate_contact_number": "+91 8765432109",
            "emergency_contact_name": "John Doe - Father",
            "emergency_contact_number": "+91 7654321098",
            "applicant_name": "Atharva Karval",
            "company_authorized_person_name": "HR Manager"
        }
        
        print(f"Testing fill with data: {test_data}")
        
        result = fill_pdf(
            template_path=pdf_bytes,
            data=test_data,
            flatten=False
        )
        
        print(f"Fill result:")
        print(f"  - Success: {result.success}")
        print(f"  - Fields filled: {result.fields_filled}")
        print(f"  - Fields failed: {result.fields_failed}")
        print(f"  - Warnings: {result.warnings}")
        print(f"  - Errors: {result.errors}")
        
        if result.field_results:
            print(f"\nField Results:")
            for fr in result.field_results:
                status = "SUCCESS" if fr.success else "FAILED"
                print(f"  - {fr.field_name}: {status} {fr.filled_value}")
                if fr.error:
                    print(f"    Error: {fr.error}")
        
        if result.output_bytes:
            output_path = Path("debug_filled.pdf")
            output_path.write_bytes(result.output_bytes)
            print(f"Saved filled PDF to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf_filling()