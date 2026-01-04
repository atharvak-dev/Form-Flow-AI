
import json
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'form-flow-backend'))

from services.pdf.pdf_parser import parse_pdf
from services.pdf.pdf_writer import PdfFormWriter

def reproduce():
    base_path = Path("form-flow-backend/storage/uploads")
    pdf_path = base_path / "34484275-7707-41ac-aab7-66f7acbe1543.pdf"
    json_path = base_path / "34484275-7707-41ac-aab7-66f7acbe1543.json"

    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"Parsing PDF: {pdf_path}")
    try:
        parsed_schema = parse_pdf(pdf_path)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"Successfully parsed PDF. Found {len(parsed_schema.fields)} fields.")
    parser_keys = [f.name for f in parsed_schema.fields]
    print(f"Sample Parser Keys: {parser_keys[:5]}")

    if not json_path.exists():
        print(f"JSON not found at {json_path}")
    else:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Extract keys from schema -> fields
        json_keys = []
        if 'schema' in data and 'fields' in data['schema']:
             json_keys = [f['name'] for f in data['schema']['fields']]
        
        print(f"JSON contains {len(json_keys)} fields.")
        print(f"Sample JSON Keys: {json_keys[:5]}")
        
        # Check for overlap
        overlap = set(parser_keys).intersection(set(json_keys))
        print(f"Exact matches: {len(overlap)}")
        
        # Test Writer Matching with SIMPLIFIED keys
        # We suspect the issue is that users/frontend send 'f1_01' but parser has 'topmostSubform[0]...f1_01[0]'
        writer = PdfFormWriter()
        print("\nTesting Smart Matching with Simplified Keys...")
        
        test_cases = [
            "f1_01", "F1 01", "c1_1", "C1 1", "Address_ReadOrder", "Doing Business As"
        ]
        
        for key in test_cases:
            matched = writer._smart_match_field(key, parser_keys)
            print(f"Input: '{key}' -> Matched: '{matched}'")

if __name__ == "__main__":
    reproduce()
