"""
PDF Writer - Form Filling Engine

Fills PDF forms with user data, handling:
- Text fields with dynamic sizing
- Checkboxes and radio buttons
- Dropdowns and listboxes
- Multi-line text wrapping
- Font size adjustment for space constraints

Uses reportlab for PDF generation and pypdf for form manipulation.
"""

import logging
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import tempfile
import shutil
import re
import difflib
from datetime import datetime

# Enterprise Infrastructure
from .exceptions import PdfFillingError, PdfResourceError
from .utils import get_logger, benchmark, PerformanceTimer
from .text_fitter import TextFitter, FitResult

logger = get_logger(__name__)

# PDF Libraries
try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (
        NameObject, TextStringObject, ArrayObject, 
        DictionaryObject, BooleanObject, NumberObject
    )
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None
    PdfWriter = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    canvas = None


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class FieldFillResult:
    """Result of filling a single field."""
    field_name: str
    success: bool
    original_value: str
    filled_value: str
    error: Optional[str] = None
    fit_result: Optional[FitResult] = None


@dataclass
class FilledPdf:
    """Result of filling a PDF form."""
    success: bool
    output_path: Optional[str] = None
    output_bytes: Optional[bytes] = None
    field_results: List[FieldFillResult] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.field_results is None:
            self.field_results = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def fields_filled(self) -> int:
        return sum(1 for r in self.field_results if r.success)
    
    @property
    def fields_failed(self) -> int:
        return sum(1 for r in self.field_results if not r.success)


class ValueTransformer:
    """
    Transforms and formats values based on field purpose/type.
    """
    
    @staticmethod
    def transform(value: str, purpose: Optional[str] = None) -> str:
        if not value or not purpose:
            return value
            
        purpose = purpose.lower()
        
        if purpose == "phone":
            return ValueTransformer._format_phone(value)
        elif purpose == "date":
            return ValueTransformer._format_date(value)
        elif purpose == "ssn":
            return ValueTransformer._format_ssn(value)
            
        return value

    @staticmethod
    def _format_phone(value: str) -> str:
        # Standardize to (XXX) XXX-XXXX if 10 digits
        digits = re.sub(r'\D', '', value)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return value

    @staticmethod
    def _format_date(value: str) -> str:
        # Try to standardize to MM/DD/YYYY
        # This assumes input might be YYYY-MM-DD or other standard formats
        if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            try:
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.strftime("%m/%d/%Y")
            except ValueError:
                pass
        return value

    @staticmethod
    def _format_ssn(value: str) -> str:
        # Standardize to XXX-XX-XXXX
        digits = re.sub(r'\D', '', value)
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        return value


# =============================================================================
# PDF Writer Class
# =============================================================================

class PdfFormWriter:
    """
    PDF form filling engine.
    
    Supports multiple strategies for form filling:
    1. Direct AcroForm field manipulation (preferred)
    2. Overlay text on specific coordinates (fallback)
    """
    
    def __init__(
        self,
        text_fitter: Optional[TextFitter] = None,
        default_font_size: float = 12.0,
        min_font_size: float = 6.0,
    ):
        """
        Initialize PDF writer.
        
        Args:
            text_fitter: TextFitter instance for text compression
            default_font_size: Default font size for text
            min_font_size: Minimum font size for auto-sizing
        """
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required. Install with: pip install pypdf")
        
        self.text_fitter = text_fitter or TextFitter()
        self.default_font_size = default_font_size
        self.min_font_size = min_font_size
    

    @benchmark("fill_pdf_form")
    def fill(
        self,
        template_path: Union[str, Path, bytes],
        data: Dict[str, str],
        output_path: Optional[Union[str, Path]] = None,
        flatten: bool = False,
        fit_text: bool = True,
    ) -> FilledPdf:
        """
        Fill a PDF form with data.
        """
        result = FilledPdf(success=True)
        
        try:
            # Open template
            if isinstance(template_path, bytes):
                reader = PdfReader(io.BytesIO(template_path))
            else:
                reader = PdfReader(str(template_path))
            
            writer = PdfWriter()
            
            # Get form fields
            fields = reader.get_fields() or {}
            
            # --- PHASE 1: PRIMARY FILLING ---
            if not fields:
                # No AcroForm fields - use visual overlay directly
                logger.warning("No AcroForm fields found. Attempting visual filling.")
                result.warnings.append("No AcroForm fields found. Attempting visual filling.")
                self._fill_overlay(reader, writer, data, result)
            else:
                # Fill each AcroForm field first
                for field_name, value in data.items():
                    field_result = self._fill_field(
                        writer=writer,
                        field_name=field_name,
                        value=value,
                        fields=fields,
                        fit_text=fit_text,
                    )
                    result.field_results.append(field_result)
                    
                    if not field_result.success:
                        result.warnings.append(
                            f"Field '{field_name}': {field_result.error}"
                        )
                
                # --- PHASE 2: HYBRID FILLING ---
                # Identify fields that failed AcroForm filling and try Visual Overlay
                failed_fields_map = {}
                for res in result.field_results:
                    if not res.success:
                        failed_fields_map[res.field_name] = res.original_value
                
                if failed_fields_map:
                    logger.info(f"Hybrid Filling: {len(failed_fields_map)} fields failed AcroForm. Attempting Visual Overlay.")
                    self._fill_overlay(reader, writer, failed_fields_map, result)
            
            # --- PHASE 3: FINALIZATION ---
            # NOW add pages to writer AFTER all overlay modifications
            for page in reader.pages:
                writer.add_page(page)

            # Force NeedAppearances to ensure visibility
            try:
                if "/AcroForm" not in writer.root_object:
                    writer.root_object[NameObject("/AcroForm")] = DictionaryObject()
                
                acro_form = writer.root_object["/AcroForm"]
                if isinstance(acro_form, dict) or isinstance(acro_form, DictionaryObject):
                     acro_form[NameObject("/NeedAppearances")] = BooleanObject(True)
            except Exception as e:
                logger.warning(f"Failed to set NeedAppearances: {e}")
            
            # Flatten if requested
            if flatten:
                try:
                    # Create flattened version by removing form fields
                    # This is a simplified approach
                    for page in writer.pages:
                        if "/Annots" in page:
                            annots = page["/Annots"]
                            # Keep non-widget annotations
                            new_annots = []
                            for annot in annots:
                                annot_obj = annot.get_object() if hasattr(annot, 'get_object') else annot
                                if annot_obj.get("/Subtype") != "/Widget":
                                    new_annots.append(annot)
                            if new_annots:
                                page[NameObject("/Annots")] = ArrayObject(new_annots)
                            else:
                                del page["/Annots"]
                except Exception as e:
                    logger.warning(f"Flattening partially failed: {e}")
                    result.warnings.append(f"Flattening partially failed: {e}")
            
            # Output
            if output_path:
                with open(str(output_path), "wb") as f:
                    writer.write(f)
                result.output_path = str(output_path)
            else:
                output_buffer = io.BytesIO()
                writer.write(output_buffer)
                result.output_bytes = output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error filling PDF: {e}")
            result.success = False
            result.errors.append(str(e))
            # Raise dedicated error if it's a critical failure that acts as a stopper
            # But here we want to return the result object even on failure usually.
            # However, if it crashed completely, maybe we should raise?
            # The current contract returns FilledPdf with success=False. I will keep that.
        
        return result

    def _find_data_for_field(self, field: Any, data: Dict[str, str]) -> Optional[str]:
        """Find data value for a PdfField using smart matching."""
        # 1. Direct Name Match
        if field.name in data: return data[field.name]
        
        # 2. Label Match
        if field.label and field.label in data: return data[field.label]
        
        # 3. Robust Slug/Base Match (Ignore "field_123_" prefix)
        # This handles case where field IDs shift between parse runs
        import re
        field_base = re.sub(r'^field_\d+_', '', field.name)
        
        # Check against all data keys
        for key, value in data.items():
            key_base = re.sub(r'^field_\d+_', '', key)
            if key_base == field_base:
                return value
        
        # 4. Clean/Fuzzy Match (Fallback)
        # Match field label against data keys
        matcher = difflib.get_close_matches
        keys = list(data.keys())
        
        if field.label:
            matches = matcher(field.label, keys, n=1, cutoff=0.7)
            if matches: return data[matches[0]]
            
        return None

    def _fill_overlay(
        self,
        reader: PdfReader,
        writer: PdfWriter,
        data: Dict[str, str],
        result: FilledPdf,
    ):
        """Fill visual form by overlaying text."""
        import traceback
        if not REPORTLAB_AVAILABLE:
            result.warnings.append("ReportLab required for visual form filling")
            return

        try:
            logger.info("Starting visual overlay fill...")
            
            # Re-parse to get field coordinates
            from .pdf_parser import parse_pdf
            
            # Create a bytes buffer from the reader content for parsing
            pdf_bytes_io = io.BytesIO()
            tmp_writer = PdfWriter()
            for page in reader.pages:
                tmp_writer.add_page(page)
            tmp_writer.write(pdf_bytes_io)
            pdf_bytes = pdf_bytes_io.getvalue()
            
            logger.info("Re-parsing PDF for visual structure...")
            schema = parse_pdf(pdf_bytes, use_ocr=False)
            logger.info(f"Visual parser found {len(schema.fields)} fields")
            
            filled_fields = 0
            
            # Create overlay for specific pages
            for i, page in enumerate(reader.pages):
                # Check for matching fields on this page first to avoid empty work
                page_fields = [f for f in schema.fields if f.position.page == i]
                if not page_fields:
                    continue
                    
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(
                    float(page.mediabox.width), 
                    float(page.mediabox.height)
                ))
                
                logger.info(f"Processing Page {i+1} with {len(page_fields)} fields")
                
                has_content = False
                for field in page_fields:
                    # Strategy: Intelligent Data Lookup
                    val = self._find_data_for_field(field, data)
                    
                    if val:
                        logger.info(f"Field match: '{field.name}' -> '{val}'")
                        
                        # Value Transformation (formatting)
                        val = ValueTransformer.transform(val, field.purpose)
                        
                        # Text Fitting (Capacity check)
                        if field.text_capacity and len(val) > field.text_capacity:
                             # Use simple fit logic as we know capacity
                             fit_res = self.text_fitter.fit(val, field.text_capacity)
                             val = fit_res.fitted

                        # Use field height to estimate font size if dynamic
                        # Simple heuristic: 70% of field height relative to baseline
                        font_size_to_use = self.default_font_size
                        if field.position.height > 5:
                            estimated_size = field.position.height * 0.75 # bumped slightly
                            font_size_to_use = max(self.min_font_size, min(estimated_size, 14.0))

                        # Coordinates
                        x = field.position.x + 2 # Slight X padding
                        
                        # ReportLab Y is from bottom.
                        # Field Y from parser is from top to top-of-field.
                        # To align baseline: PageHeight - (y_from_top + height)
                        # We add a small padding for visual lift off the underline
                        y = float(page.mediabox.height) - (field.position.y + field.position.height) + 3.0 # Lifted +3
                        
                        try:
                            can.setFont("Helvetica", font_size_to_use)
                            can.drawString(x, y, str(val))
                            has_content = True
                            
                            result.field_results.append(FieldFillResult(
                                field_name=field.name,
                                success=True,
                                original_value=val,
                                filled_value=val
                            ))
                            filled_fields += 1
                        except Exception as e:
                             logger.error(f"Error drawing string for field {field.name}: {e}")
                
                can.save()
                
                if has_content:
                    # Merge overlay
                    packet.seek(0)
                    overlay_pdf = PdfReader(packet)
                    if len(overlay_pdf.pages) > 0:
                        page.merge_page(overlay_pdf.pages[0])
                        logger.info(f"Merged overlay onto Page {i+1}")
            
            if filled_fields == 0:
                result.warnings.append("No matching fields found for visual filling")
                logger.warning("Visual filling completed but no fields were filled.")
            else:
                logger.info(f"Visual filling completed. Filled {filled_fields} fields.")
                
        except Exception as e:
            logger.error(f"Error in overlay fill: {e}")
            logger.error(traceback.format_exc())
            result.warnings.append(f"Visual filling failed: {e}")
    
    def _smart_match_field(self, target_name: str, available_fields: List[str]) -> Optional[str]:
        """Find best matching field name using fuzzy logic."""
        # Clean the target name (remove auto-generated prefixes)
        import re
        target_clean_base = re.sub(r'^field_\d+_', '', target_name).lower()

        # Helper to strip index brackets e.g., [0] from XFA paths
        def strip_index(s): return re.sub(r'\[\d+\]', '', s)
        
        # Helper to get leaf node from XFA path (last segment after `.`)
        def get_leaf(s): return strip_index(s.split('.')[-1]).lower()

        # 1. Exact match
        if target_name in available_fields:
            return target_name
            
        # 2. Case-insensitive
        lower_map = {f.lower(): f for f in available_fields}
        if target_name.lower() in lower_map:
            return lower_map[target_name.lower()]
            
        # 3. Clean matching (remove special chars from both)
        def clean(s): return re.sub(r'[^a-z0-9]', '', s.lower())
        target_clean = clean(target_name)
        
        # Extended map including base name matching
        for f in available_fields:
            f_clean = clean(f)
            if f_clean == target_clean: return f
            # Match base name (e.g. "fullname" in "field_3_fullname" matches "FullName" in PDF)
            if f_clean == clean(target_clean_base): return f
        
        # 4. XFA Leaf-Node Match: Match target against the leaf segment of each field path
        # This handles cases like 'f1_01' matching 'topmostSubform[0].Page1[0].f1_01[0]'
        target_leaf_clean = clean(strip_index(target_name))
        for f in available_fields:
            if clean(get_leaf(f)) == target_leaf_clean:
                return f
            
        # 5. Fuzzy Match (difflib)
        matches = difflib.get_close_matches(target_name, available_fields, n=1, cutoff=0.7)
        if matches: return matches[0]
        
        # Fuzzy match on BASE name
        matches_base = difflib.get_close_matches(target_clean_base, [clean(f) for f in available_fields], n=1, cutoff=0.8)
        if matches_base:
            # Find original key for the matched base
            for f in available_fields:
                if clean(f) == matches_base[0]: return f

        # 6. Fallback: Check containment in base name
        for f in available_fields:
            f_clean = clean(f)
            if target_clean_base in f_clean or f_clean in target_clean_base:
                return f
            
        return None

    def _fill_field(
        self,
        writer: PdfWriter,
        field_name: str,
        value: str,
        fields: Dict[str, Any],
        fit_text: bool = True,
    ) -> FieldFillResult:
        """Fill a single form field with intelligent matching and fallback."""
        original_value = value
        fit_result = None
        
        try:
            # 1. Smart Match Field Name
            matched_field_name = self._smart_match_field(field_name, list(fields.keys()))
            
            if not matched_field_name:
                return FieldFillResult(
                    field_name=field_name,
                    success=False,
                    original_value=original_value,
                    filled_value="",
                    error=f"Field not found in PDF (tried fuzzy match)"
                )
            
            field_name = matched_field_name
            field_info = fields[field_name]
            field_type = field_info.get("/FT", "")
            
            # 2. Limit Check & Validation (Pre-fill)
            max_length = field_info.get("/MaxLen")
            
            # Detect subtle purpose from name for transformation
            # (In a full implementation, we'd use the parser's context, but here we have raw writer fields)
            purpose = "text"
            fname_lower = field_name.lower()
            if "phone" in fname_lower or "mobile" in fname_lower: purpose = "phone"
            elif "date" in fname_lower or "dob" in fname_lower: purpose = "date"
            elif "ssn" in fname_lower: purpose = "ssn"
            
            # 3. Value Transformation
            value = ValueTransformer.transform(value, purpose)
            
            # 4. Text Fitting (if applicable)
            if fit_text and field_type == "/Tx" and max_length:
                # If value is still too long after transformation, use key-value text compression
                if len(value) > max_length:
                    field_context = {
                        "name": field_name,
                        "type": "text",
                        "max_length": max_length,
                        "purpose": purpose
                    }
                    fit_result = self.text_fitter.fit(
                        value, 
                        max_length, 
                        field_context
                    )
                    value = fit_result.fitted
            
            # Fill based on field type
            if field_type == "/Tx":  # Text field
                self._fill_text_field(writer, field_name, value)
            
            elif field_type == "/Btn":  # Button (checkbox/radio)
                flags = field_info.get("/Ff", 0)
                if flags & (1 << 15):  # Radio
                    self._fill_radio_button(writer, field_name, value, field_info)
                else:  # Checkbox
                    self._fill_checkbox(writer, field_name, value)
            
            elif field_type == "/Ch":  # Choice (dropdown/listbox)
                self._fill_choice_field(writer, field_name, value.strip(), field_info)
            
            else:
                # Generic fill attempt
                self._fill_text_field(writer, field_name, value)
            
            return FieldFillResult(
                field_name=field_name,
                success=True,
                original_value=original_value,
                filled_value=value,
                fit_result=fit_result,
            )
            
        except Exception as e:
            logger.error(f"Error filling field {field_name}: {e}")
            return FieldFillResult(
                field_name=field_name,
                success=False,
                original_value=original_value,
                filled_value="",
                error=str(e),
            )
    
    def _fill_text_field(
        self,
        writer: PdfWriter,
        field_name: str,
        value: str,
    ):
        """Fill a text field."""
        writer.update_page_form_field_values(
            writer.pages[0],  # Update all pages
            {field_name: value},
            auto_regenerate=True,
        )
    
    def _fill_checkbox(
        self,
        writer: PdfWriter,
        field_name: str,
        value: str,
    ):
        """Fill a checkbox field."""
        # Determine checked state
        checked = value.lower() in ('yes', 'true', '1', 'checked', 'on', 'x')
        check_value = "/Yes" if checked else "/Off"
        
        writer.update_page_form_field_values(
            writer.pages[0],
            {field_name: check_value},
        )
    
    def _fill_radio_button(
        self,
        writer: PdfWriter,
        field_name: str,
        value: str,
        field_info: Dict[str, Any],
    ):
        """Fill a radio button group."""
        # Find matching option
        kids = field_info.get("/Kids", [])
        for kid in kids:
            kid_obj = kid.get_object() if hasattr(kid, 'get_object') else kid
            ap = kid_obj.get("/AP", {})
            if "/N" in ap:
                # Get option names
                for opt_name in ap["/N"].keys():
                    if opt_name != "/Off" and value.lower() in str(opt_name).lower():
                        writer.update_page_form_field_values(
                            writer.pages[0],
                            {field_name: opt_name},
                        )
                        return
        
        # Fallback: try direct value
        writer.update_page_form_field_values(
            writer.pages[0],
            {field_name: f"/{value}"},
        )
    
    def _fill_choice_field(
        self,
        writer: PdfWriter,
        field_name: str,
        value: str,
        field_info: Dict[str, Any],
    ):
        """Fill a dropdown or listbox field."""
        # Get available options
        options = field_info.get("/Opt", [])
        
        # Find best matching option
        best_match = value
        for opt in options:
            if isinstance(opt, list) and len(opt) >= 2:
                opt_value = str(opt[1])
            else:
                opt_value = str(opt)
            
            if value.lower() == opt_value.lower():
                best_match = opt_value
                break
            elif value.lower() in opt_value.lower():
                best_match = opt_value
        
        writer.update_page_form_field_values(
            writer.pages[0],
            {field_name: best_match},
        )


# =============================================================================
# Main Functions
# =============================================================================

def fill_pdf(
    template_path: Union[str, Path, bytes],
    data: Dict[str, str],
    output_path: Optional[Union[str, Path]] = None,
    flatten: bool = False,
) -> FilledPdf:
    """
    Fill a PDF form with data.
    
    Args:
        template_path: Path to template PDF or PDF bytes
        data: Dictionary of {field_name: value}
        output_path: Path to save filled PDF (None for bytes output)
        flatten: Whether to flatten form fields
        
    Returns:
        FilledPdf with results
    """
    writer = PdfFormWriter()
    return writer.fill(template_path, data, output_path, flatten)


def preview_fill(
    template_path: Union[str, Path, bytes],
    data: Dict[str, str],
) -> Dict[str, Any]:
    """
    Preview how data would be filled without actually creating PDF.
    
    Returns what values would be used for each field after text fitting.
    """
    fitter = TextFitter()
    
    # Open template to get field info
    if isinstance(template_path, bytes):
        reader = PdfReader(io.BytesIO(template_path))
    else:
        reader = PdfReader(str(template_path))
    
    fields = reader.get_fields() or {}
    
    preview = {}
    for field_name, value in data.items():
        field_info = fields.get(field_name, {})
        max_length = field_info.get("/MaxLen")
        
        if max_length:
            fit_result = fitter.fit(value, max_length)
            preview[field_name] = {
                "original": value,
                "fitted": fit_result.fitted,
                "strategy": fit_result.strategy_used,
                "truncated": fit_result.truncated,
            }
        else:
            preview[field_name] = {
                "original": value,
                "fitted": value,
                "strategy": "direct_fit",
                "truncated": False,
            }
    
    return preview


def get_pdf_field_names(
    pdf_path: Union[str, Path, bytes],
) -> List[str]:
    """Get list of fillable field names from a PDF."""
    if isinstance(pdf_path, bytes):
        reader = PdfReader(io.BytesIO(pdf_path))
    else:
        reader = PdfReader(str(pdf_path))
    
    fields = reader.get_fields() or {}
    return list(fields.keys())
