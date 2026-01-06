"""
Word Document Parser

Extracts fillable placeholders from .docx files.
Supports:
- Bracket placeholders: [Name], [Email], [Phone]
- Underscore placeholders: ____, _________
- Content Controls (SDT) from modern Word forms
"""

import re
import io
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from docx import Document
from docx.oxml.ns import qn

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocxField:
    """Represents a detected placeholder in a Word document."""
    name: str
    display_name: str
    field_type: str = "text"
    placeholder_text: str = ""
    paragraph_index: int = 0
    run_index: int = 0
    original_text: str = ""
    

class DocxParser:
    """
    Parse Word documents to extract fillable placeholders.
    
    Strategies:
    1. Bracket patterns: [Name], [Email], etc.
    2. Underscore patterns: ____, _________
    3. Content Controls (SDT elements)
    """
    
    # Common placeholder patterns
    BRACKET_PATTERN = re.compile(r'\[([A-Za-z][A-Za-z0-9_\s]{1,50})\]')
    UNDERSCORE_PATTERN = re.compile(r'_{3,}')  # 3+ underscores
    
    # Field type inference from name
    FIELD_TYPE_MAP = {
        'email': 'email',
        'mail': 'email',
        'phone': 'tel',
        'mobile': 'tel',
        'cell': 'tel',
        'telephone': 'tel',
        'date': 'date',
        'dob': 'date',
        'birthday': 'date',
        'birth': 'date',
        'number': 'number',
        'amount': 'number',
        'quantity': 'number',
        'age': 'number',
        'zip': 'text',
        'postal': 'text',
    }
    
    def __init__(self, file_source):
        """
        Initialize parser with file source.
        
        Args:
            file_source: File path (str/Path) or bytes
        """
        if isinstance(file_source, bytes):
            self.doc = Document(io.BytesIO(file_source))
            self.file_name = "uploaded.docx"
        else:
            self.doc = Document(file_source)
            self.file_name = Path(file_source).name
            
        self.fields: List[DocxField] = []
        self.field_locations: Dict[str, Tuple[int, int]] = {}  # name -> (para_idx, run_idx)
        
    def parse(self) -> List[DocxField]:
        """Parse document and extract all placeholders."""
        logger.info(f"Parsing Word document: {self.file_name}")
        
        # Strategy 1: Content Controls (SDT)
        self._extract_content_controls()
        
        # Strategy 2: Bracket patterns
        self._extract_bracket_placeholders()
        
        # Strategy 3: Underscore patterns (if no other fields found)
        if not self.fields:
            self._extract_underscore_placeholders()
        
        logger.info(f"Found {len(self.fields)} fields in document")
        return self.fields
    
    def _extract_content_controls(self):
        """Extract Content Controls (Structured Document Tags)."""
        # Access the document's XML
        body = self.doc.element.body
        
        # Find all sdt (Structured Document Tag) elements
        for sdt in body.iter(qn('w:sdt')):
            try:
                # Get the tag/alias
                sdt_pr = sdt.find(qn('w:sdtPr'))
                if sdt_pr is None:
                    continue
                    
                # Try to get alias (display name)
                alias = sdt_pr.find(qn('w:alias'))
                tag = sdt_pr.find(qn('w:tag'))
                
                name = None
                if alias is not None:
                    name = alias.get(qn('w:val'))
                elif tag is not None:
                    name = tag.get(qn('w:val'))
                    
                if not name:
                    continue
                
                # Get current text content
                sdt_content = sdt.find(qn('w:sdtContent'))
                text = ""
                if sdt_content is not None:
                    for t in sdt_content.iter(qn('w:t')):
                        text += t.text or ""
                
                field = DocxField(
                    name=self._sanitize_name(name),
                    display_name=name,
                    field_type=self._infer_field_type(name),
                    placeholder_text=text.strip(),
                    original_text=text.strip()
                )
                self.fields.append(field)
                logger.debug(f"Found content control: {name}")
                
            except Exception as e:
                logger.debug(f"Error parsing SDT: {e}")
                continue
    
    def _extract_bracket_placeholders(self):
        """Extract [Placeholder] style fields from paragraphs."""
        seen_names = {f.name for f in self.fields}
        
        for para_idx, paragraph in enumerate(self.doc.paragraphs):
            text = paragraph.text
            
            for match in self.BRACKET_PATTERN.finditer(text):
                name = match.group(1).strip()
                sanitized = self._sanitize_name(name)
                
                if sanitized in seen_names:
                    continue
                    
                # Find which run contains this placeholder
                run_idx = self._find_run_index(paragraph, match.start())
                
                field = DocxField(
                    name=sanitized,
                    display_name=name,
                    field_type=self._infer_field_type(name),
                    placeholder_text=match.group(0),
                    paragraph_index=para_idx,
                    run_index=run_idx,
                    original_text=match.group(0)
                )
                self.fields.append(field)
                self.field_locations[sanitized] = (para_idx, run_idx)
                seen_names.add(sanitized)
                logger.debug(f"Found bracket placeholder: {name}")
    
    def _extract_underscore_placeholders(self):
        """Extract ____ style fields (last resort)."""
        underscore_count = 0
        
        for para_idx, paragraph in enumerate(self.doc.paragraphs):
            text = paragraph.text
            
            # Look for labels followed by underscores
            # e.g., "Name: ____" or "Email _______"
            label_underscore_pattern = re.compile(r'([A-Za-z][A-Za-z\s]{1,30})[:\s]*_{3,}')
            
            for match in label_underscore_pattern.finditer(text):
                label = match.group(1).strip()
                sanitized = self._sanitize_name(label)
                
                field = DocxField(
                    name=sanitized,
                    display_name=label,
                    field_type=self._infer_field_type(label),
                    placeholder_text=match.group(0),
                    paragraph_index=para_idx,
                    original_text=match.group(0)
                )
                self.fields.append(field)
                underscore_count += 1
                
        # If no labeled underscores, just count blank underscores as generic fields
        if underscore_count == 0:
            for para_idx, paragraph in enumerate(self.doc.paragraphs):
                for match in self.UNDERSCORE_PATTERN.finditer(paragraph.text):
                    underscore_count += 1
                    field = DocxField(
                        name=f"field_{underscore_count}",
                        display_name=f"Field {underscore_count}",
                        field_type="text",
                        placeholder_text=match.group(0),
                        paragraph_index=para_idx,
                        original_text=match.group(0)
                    )
                    self.fields.append(field)
    
    def _find_run_index(self, paragraph, char_offset: int) -> int:
        """Find which run contains a given character offset."""
        current_pos = 0
        for idx, run in enumerate(paragraph.runs):
            run_len = len(run.text)
            if current_pos <= char_offset < current_pos + run_len:
                return idx
            current_pos += run_len
        return 0
    
    def _sanitize_name(self, name: str) -> str:
        """Convert display name to valid field name."""
        # Replace spaces with underscores, remove special chars
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
        sanitized = re.sub(r'_+', '_', sanitized)  # Remove duplicate underscores
        return sanitized.strip('_')
    
    def _infer_field_type(self, name: str) -> str:
        """Infer HTML input type from field name."""
        name_lower = name.lower()
        for keyword, field_type in self.FIELD_TYPE_MAP.items():
            if keyword in name_lower:
                return field_type
        return "text"
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert parsed fields to form schema format."""
        fields = []
        for f in self.fields:
            fields.append({
                "name": f.name,
                "id": f.name,
                "type": f.field_type,
                "label": f.display_name,
                "display_name": f.display_name,
                "required": False,
                "placeholder": f.placeholder_text,
                "source": "docx"
            })
        
        return {
            "success": True,
            "docx_id": str(uuid.uuid4()),
            "file_name": self.file_name,
            "total_fields": len(fields),
            "fields": fields
        }


def parse_docx_fields(file_source) -> Dict[str, Any]:
    """
    Convenience function to parse a Word document.
    
    Args:
        file_source: File path or bytes
        
    Returns:
        Schema dict with fields array
    """
    try:
        parser = DocxParser(file_source)
        parser.parse()
        return parser.to_schema()
    except Exception as e:
        logger.error(f"Failed to parse docx: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to parse Word document"
        }
