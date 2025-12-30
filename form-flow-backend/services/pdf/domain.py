"""
Domain Models for Enterprise PDF Services.

This module defines the core data structures used for intelligent form processing,
including field grouping, validation reports, and advanced field metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict, Union

# =============================================================================
# Field Grouping & Relationships
# =============================================================================

class GroupType(Enum):
    """Types of logic groupings for form fields."""
    LOGICAL = "logical"          # semantic grouping (e.g. all personal info)
    VISUAL = "visual"            # spatially grouped (e.g. inside a box)
    REPEATING = "repeating"      # e.g. Dependents list
    CONDITIONAL = "conditional"  # e.g. "If Yes, answer below"
    ADDRESS = "address"          # Specific address block
    NAME = "name"                # Generic name block (first/middle/last)


@dataclass
class FieldGroup:
    """
    Represents a logical grouping of fields.
    
    Useful for:
    - Filling complex data structures (Address objects -> Address fields)
    - Handling repeating sections (Employee history)
    - Understanding form structure
    """
    id: str
    group_type: GroupType
    fields: List[str]  # List of field IDs belonging to this group
    label: Optional[str] = None
    parent_group: Optional[str] = None
    
    # For repeating groups
    is_repeating: bool = False
    min_indices: int = 1
    max_indices: int = 1
    
    # Logic
    trigger_field: Optional[str] = None  # For conditional groups
    trigger_value: Optional[Any] = None


# =============================================================================
# Validation & Reporting
# =============================================================================

class Severity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Blocking issue
    WARNING = "warning"  # Non-blocking optimization/quality issue
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """Single validation finding."""
    field_id: str
    message: str
    severity: Severity
    code: str
    suggested_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "suggested_value": self.suggested_value
        }


@dataclass
class ValidationReport:
    """
    Comprehensive report on data readiness for form filling.
    """
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]
        
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]
        
    def add_error(self, field_id: str, message: str, code: str = "invalid_data"):
        self.is_valid = False
        self.issues.append(ValidationIssue(field_id, message, Severity.ERROR, code))
        
    def add_warning(self, field_id: str, message: str, code: str = "quality_check", suggestion: Any = None):
        self.issues.append(ValidationIssue(field_id, message, Severity.WARNING, code, suggestion))


# =============================================================================
# Advanced Field Metadata helper
# =============================================================================

@dataclass
class FieldContext:
    """
    Rich context about a field derived from its surroundings.
    """
    nearby_text: str = ""
    section_header: Optional[str] = None
    instructions: str = ""
    is_required_visually: bool = False  # e.g., marked with *
    format_hint: Optional[str] = None   # e.g., (MM/DD/YYYY)
