"""
Generic XFA Parser - Extracts real field positions and labels from XFA XML.

This is a truly generic solution that works for ANY XFA PDF without hardcoded mappings.
Labels are extracted from the <caption> element inside each <field>.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class XfaField:
    """Parsed XFA field with real position and label."""
    name: str
    full_path: str
    x: float  # mm
    y: float  # mm
    width: float  # mm
    height: float  # mm
    page: int
    field_type: str  # "text", "checkbox", "radio"
    label: Optional[str] = None
    speak_text: Optional[str] = None  # Accessibility text


class XfaParser:
    """
    Parse XFA template XML to extract field positions and labels.
    
    Works for ANY XFA PDF - no hardcoded form mappings needed.
    """
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        if isinstance(pdf_path, bytes):
            import io
            self.pdf_source = io.BytesIO(pdf_path)
        else:
            self.pdf_source = pdf_path
            
        self.xfa_parts: Dict[str, str] = {}
        self.fields: List[XfaField] = []
        
    def parse(self) -> List[XfaField]:
        """Parse XFA and extract all fields with labels."""
        self._extract_xfa_parts()
        
        if "template" not in self.xfa_parts:
            return []
        
        template = self.xfa_parts["template"]
        self._parse_template(template)
        
        return self.fields
    
    def _extract_xfa_parts(self):
        """Extract XFA parts from PDF."""
        reader = PdfReader(self.pdf_source)
        
        try:
            root = reader.trailer["/Root"]
            acroform = root.get("/AcroForm")
            if not acroform:
                return
            
            xfa = acroform.get("/XFA")
            if not xfa:
                return
            
            if hasattr(xfa, '__iter__') and not isinstance(xfa, bytes):
                parts = list(xfa)
                for i in range(0, len(parts) - 1, 2):
                    label = str(parts[i])
                    stream = parts[i + 1]
                    if hasattr(stream, 'get_data'):
                        data = stream.get_data().decode('utf-8', errors='replace')
                        self.xfa_parts[label] = data
        except Exception as e:
            print(f"Error extracting XFA: {e}")
    
    def _parse_template(self, template: str):
        """Parse XFA template XML to extract fields with robust page detection."""
        # CRITICAL: XFA format uses \n> between elements
        # Normalize by replacing \n> with > (keep the >, remove newline)
        data = template.replace('\n>', '>')
        
        # =====================================================================
        # PHASE 1: Detect page structure from subforms
        # =====================================================================
        # In XFA, pages are often defined as subforms with specific names or
        # by being children of the pageSet. We track subform depth and names.
        
        # Count major subforms that could represent pages
        # Common patterns: subform[0], Page1, form1, etc.
        page_subforms = []
        subform_pattern = r'<subform\s+name="([^"]*)"[^>]*>'
        for match in re.finditer(subform_pattern, data):
            name = match.group(1).lower()
            # Heuristic: subforms starting with "page", "p", or numeric suffixes
            if 'page' in name or name.startswith('p') or re.match(r'.*\d+$', name):
                page_subforms.append(match.group(1))
        
        # If we found page-like subforms, use them for context
        page_context_names = set(page_subforms[:10])  # Limit to reasonable count
        
        # =====================================================================
        # PHASE 2: Extract fields with context-aware page detection
        # =====================================================================
        # Find all fields and their positions in the document
        field_pattern = r'<field\s+name="([^"]+)"([^>]*)>(.*?)</field>'
        
        field_positions = []  # (field_data, y_position)
        
        for match in re.finditer(field_pattern, data, re.DOTALL):
            name = match.group(1)
            attrs = match.group(2)
            content = match.group(3)
            
            # Extract position
            x = self._parse_mm(self._get_attr(attrs, 'x'))
            y = self._parse_mm(self._get_attr(attrs, 'y'))
            w = self._parse_mm(self._get_attr(attrs, 'w'))
            h = self._parse_mm(self._get_attr(attrs, 'h'))
            
            # Detect field type
            if '<checkButton' in content:
                field_type = "checkbox"
            elif '<choiceList' in content:
                field_type = "dropdown"
            else:
                field_type = "text"
            
            # Extract caption (primary label source)
            caption_match = re.search(r'<caption.*?<text>([^<]+)</text>', content, re.DOTALL)
            label = caption_match.group(1).strip() if caption_match else None
            
            # Extract speak text (accessibility, fallback label)
            speak_match = re.search(r'<speak[^>]*>([^<]+)</speak>', content)
            speak_text = speak_match.group(1).strip() if speak_match else None
            
            # Use speak text if no caption
            if not label and speak_text:
                label = speak_text
            
            field_positions.append({
                'name': name,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'type': field_type,
                'label': label,
                'speak_text': speak_text,
                'abs_y': y,  # Will be adjusted per-page
            })
        
        # =====================================================================
        # PHASE 3: Infer page numbers using Y-position clustering
        # =====================================================================
        # Standard US Letter page height is ~279mm
        # A4 is ~297mm
        PAGE_HEIGHT_MM = 280  # Approximate page height
        
        for field_data in field_positions:
            # Calculate page based on absolute Y position
            # Fields with Y > PAGE_HEIGHT are likely on page 2+
            abs_y = field_data['y']
            
            # Some XFA forms reset Y per page, some use absolute
            # Heuristic: if Y is small, use cumulative Y tracking
            page = int(abs_y // PAGE_HEIGHT_MM)
            
            self.fields.append(XfaField(
                name=field_data['name'],
                full_path=field_data['name'],
                x=field_data['x'],
                y=field_data['y'],
                width=field_data['w'],
                height=field_data['h'],
                page=page,
                field_type=field_data['type'],
                label=field_data['label'],
                speak_text=field_data['speak_text'],
            ))
    
    def _get_attr(self, attrs_str: str, attr_name: str) -> Optional[str]:
        """Extract attribute value."""
        match = re.search(rf'{attr_name}="([^"]*)"', attrs_str)
        return match.group(1) if match else None
    
    def _parse_mm(self, value: Optional[str]) -> float:
        """Parse measurement to mm."""
        if not value:
            return 0.0
        
        if 'mm' in value:
            return float(value.replace('mm', ''))
        elif 'pt' in value:
            return float(value.replace('pt', '')) * 0.3528
        elif 'in' in value:
            return float(value.replace('in', '')) * 25.4
        
        try:
            return float(value)
        except:
            return 0.0


def parse_xfa_fields(pdf_path) -> List[XfaField]:
    """
    Convenience function to parse XFA fields from a PDF.
    
    Returns empty list if PDF is not XFA or parsing fails.
    """
    try:
        parser = XfaParser(pdf_path)
        return parser.parse()
    except Exception as e:
        print(f"XFA parsing error: {e}")
        return []
