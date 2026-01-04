"""
Analyze PDF structure to understand how to extract human-readable field labels.
Uses pdfplumber for visual text extraction and pypdf for form fields.
"""
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "form-flow-backend"))

import pdfplumber
from pypdf import PdfReader

def analyze_pdf(pdf_path: str):
    """Analyze PDF structure - both form fields and visual text."""
    
    print(f"=== Analyzing: {pdf_path} ===\n")
    
    # 1. Extract form fields using pypdf
    print("--- FORM FIELDS (pypdf) ---")
    reader = PdfReader(pdf_path)
    
    # Check for XFA
    if "/XFA" in reader.trailer.get("/Root", {}).get("/AcroForm", {}):
        print("⚠️  XFA Form Detected")
    
    fields = reader.get_fields()
    if fields:
        fillable_fields = []
        container_fields = []
        
        for name, field in list(fields.items())[:30]:  # Limit output
            field_type = field.get("/FT", "unknown")
            # Skip container/structural fields
            if field_type == "unknown" or field_type is None:
                container_fields.append(name)
            else:
                fillable_fields.append({
                    "name": name,
                    "type": str(field_type),
                    "value": field.get("/V", ""),
                })
        
        print(f"\nFillable Fields ({len(fillable_fields)} shown):")
        for f in fillable_fields[:15]:
            print(f"  - {f['name']} [{f['type']}]")
        
        print(f"\nContainer/Structural Fields (skipped): {len(container_fields)}")
    else:
        print("No AcroForm fields found")
    
    # 2. Extract visual text using pdfplumber
    print("\n--- VISUAL TEXT (pdfplumber) ---")
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:1]):  # First page only
            print(f"\nPage {page_num + 1}:")
            
            # Extract text with positions
            words = page.extract_words()
            
            # Group by approximate Y position (lines)
            lines = {}
            for word in words:
                y_key = round(word['top'] / 10) * 10  # Group within 10pt
                if y_key not in lines:
                    lines[y_key] = []
                lines[y_key].append(word['text'])
            
            # Show first 20 lines
            for y_pos in sorted(lines.keys())[:20]:
                line_text = " ".join(lines[y_pos])
                print(f"  Y={y_pos}: {line_text[:80]}")
            
            # Extract tables if any
            tables = page.extract_tables()
            if tables:
                print(f"\n  Tables found: {len(tables)}")

    # 3. Proposed field schema based on IRS 1040 structure
    print("\n--- PROPOSED SCHEMA STRUCTURE ---")
    sample_schema = {
        "form_id": "irs_1040_2025",
        "sections": [
            {
                "id": "personal_info",
                "label": "Personal Information",
                "fields": [
                    {"field_id": "first_name", "label": "Your first name and middle initial", "form_line": None, "input_type": "text"},
                    {"field_id": "last_name", "label": "Last name", "form_line": None, "input_type": "text"},
                    {"field_id": "ssn", "label": "Your social security number", "form_line": None, "input_type": "ssn"},
                ]
            },
            {
                "id": "filing_status",
                "label": "Filing Status",
                "fields": [
                    {"field_id": "filing_status", "label": "Filing Status", "options": ["Single", "Married filing jointly", "Married filing separately", "Head of household", "Qualifying surviving spouse"], "input_type": "radio"},
                ]
            },
            {
                "id": "income",
                "label": "Income",
                "fields": [
                    {"field_id": "income.w2.line_1a", "label": "Total amount from Form(s) W-2, box 1", "form_line": "1a", "input_type": "currency"},
                    {"field_id": "income.w2.line_1b", "label": "Household employee wages not reported on Form(s) W-2", "form_line": "1b", "input_type": "currency"},
                ]
            }
        ]
    }
    print(json.dumps(sample_schema, indent=2)[:1000])

if __name__ == "__main__":
    pdf_path = "form-flow-backend/storage/uploads/6aea5015-402d-4bca-affb-cda2a6cbed2c.pdf"
    if not Path(pdf_path).exists():
        # Try the 1040 PDF
        pdf_path = "form-flow-backend/storage/uploads/34484275-7707-41ac-aab7-66f7acbe1543.pdf"
    
    analyze_pdf(pdf_path)
