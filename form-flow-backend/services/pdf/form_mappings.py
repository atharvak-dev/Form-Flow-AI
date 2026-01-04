"""
Field mappings for common government/tax forms.

These mappings translate XFA field IDs to human-readable labels,
form lines, and sections. This is necessary because XFA forms
often have dummy field positions that prevent proximity-based
label extraction.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class FieldMapping:
    """Mapping for a single form field."""
    display_name: str
    form_line: Optional[str] = None
    section: Optional[str] = None
    input_type: Optional[str] = None
    help_text: Optional[str] = None


# IRS Form 1040 (2025) Field Mappings
# Field IDs are the leaf node names (e.g., "f1_01" from "topmostSubform[0].Page1[0].f1_01[0]")
IRS_1040_2025_FIELDS: Dict[str, FieldMapping] = {
    # Personal Information
    "f1_01": FieldMapping("Your first name and middle initial", None, "Personal Information", "text"),
    "f1_02": FieldMapping("Your last name", None, "Personal Information", "text"),
    "f1_03": FieldMapping("Your social security number", None, "Personal Information", "ssn"),
    "f1_04": FieldMapping("Spouse's first name and middle initial", None, "Personal Information", "text"),
    "f1_05": FieldMapping("Spouse's last name", None, "Personal Information", "text"),
    "f1_06": FieldMapping("Spouse's social security number", None, "Personal Information", "ssn"),
    "f1_07": FieldMapping("Home address (number and street)", None, "Personal Information", "text"),
    "f1_08": FieldMapping("Apartment number", None, "Personal Information", "text"),
    "f1_09": FieldMapping("City, town, or post office", None, "Personal Information", "text"),
    "f1_10": FieldMapping("State", None, "Personal Information", "text"),
    "f1_11": FieldMapping("ZIP code", None, "Personal Information", "text"),
    "f1_12": FieldMapping("Foreign country name", None, "Personal Information", "text"),
    "f1_13": FieldMapping("Foreign province/state/county", None, "Personal Information", "text"),
    "f1_14": FieldMapping("Foreign postal code", None, "Personal Information", "text"),
    
    # Filing Status checkboxes
    "c1_1": FieldMapping("Single", None, "Filing Status", "checkbox"),
    "c1_2": FieldMapping("Married filing jointly", None, "Filing Status", "checkbox"),
    "c1_3": FieldMapping("Married filing separately", None, "Filing Status", "checkbox"),
    "c1_4": FieldMapping("Head of household", None, "Filing Status", "checkbox"),
    "c1_5": FieldMapping("Qualifying surviving spouse", None, "Filing Status", "checkbox"),
    
    # Presidential Election Campaign
    "c1_6": FieldMapping("Presidential Election Campaign - You", None, "Personal Information", "checkbox"),
    "c1_7": FieldMapping("Presidential Election Campaign - Spouse", None, "Personal Information", "checkbox"),
    
    # Digital Assets
    "c1_8": FieldMapping("Digital assets - Yes", None, "Digital Assets", "checkbox"),
    "c1_9": FieldMapping("Digital assets - No", None, "Digital Assets", "checkbox"),
    
    # Dependents - Row 1
    "f1_31": FieldMapping("Dependent 1 - First name", None, "Dependents", "text"),
    "f1_32": FieldMapping("Dependent 1 - Last name", None, "Dependents", "text"),
    "f1_33": FieldMapping("Dependent 1 - SSN", None, "Dependents", "ssn"),
    "f1_34": FieldMapping("Dependent 1 - Relationship", None, "Dependents", "text"),
    
    # Income section
    "f1_47": FieldMapping("W-2 wages and salaries", "1a", "Income", "currency", "Total from Form(s) W-2, box 1"),
    "f1_48": FieldMapping("Household employee wages", "1b", "Income", "currency"),
    "f1_49": FieldMapping("Tip income", "1c", "Income", "currency"),
    "f1_50": FieldMapping("Medicaid waiver payments", "1d", "Income", "currency"),
    "f1_51": FieldMapping("Dependent care benefits", "1e", "Income", "currency"),
    "f1_52": FieldMapping("Adoption benefits", "1f", "Income", "currency"),
    "f1_53": FieldMapping("Form 8919 wages", "1g", "Income", "currency"),
    "f1_54": FieldMapping("Other earned income", "1h", "Income", "currency"),
    "f1_55": FieldMapping("Nontaxable combat pay", "1i", "Income", "currency"),
    "f1_56": FieldMapping("Total wages (add lines 1a-1h)", "1z", "Income", "currency"),
    
    # Interest and dividends
    "f1_57": FieldMapping("Tax-exempt interest", "2a", "Income", "currency"),
    "f1_58": FieldMapping("Taxable interest", "2b", "Income", "currency"),
    "f1_59": FieldMapping("Qualified dividends", "3a", "Income", "currency"),
    "f1_60": FieldMapping("Ordinary dividends", "3b", "Income", "currency"),
    
    # IRA and pensions  
    "f1_61": FieldMapping("IRA distributions", "4a", "Income", "currency"),
    "f1_62": FieldMapping("IRA taxable amount", "4b", "Income", "currency"),
    "f1_63": FieldMapping("Pensions and annuities", "5a", "Income", "currency"),
    "f1_64": FieldMapping("Pensions taxable amount", "5b", "Income", "currency"),
    
    # Social Security
    "f1_65": FieldMapping("Social security benefits", "6a", "Income", "currency"),
    "f1_66": FieldMapping("Social security taxable amount", "6b", "Income", "currency"),
    
    # Capital gains
    "f1_67": FieldMapping("Capital gain or (loss)", "7a", "Income", "currency"),
    
    # Schedule 1 income
    "f1_68": FieldMapping("Additional income", "8", "Income", "currency"),
    "f1_69": FieldMapping("Total income", "9", "Income", "currency"),
    "f1_70": FieldMapping("Adjustments to income", "10", "Income", "currency"),
    "f1_71": FieldMapping("Adjusted gross income", "11a", "Income", "currency"),
    
    # Page 2 fields
    "f2_01": FieldMapping("Adjusted gross income (from page 1)", "11a", "Tax Computation", "currency"),
    "f2_02": FieldMapping("Standard deduction or itemized deductions", "12", "Tax Computation", "currency"),
    "f2_03": FieldMapping("Qualified business income deduction", "13", "Tax Computation", "currency"),
    "f2_04": FieldMapping("Add lines 12 and 13", "14", "Tax Computation", "currency"),
    "f2_05": FieldMapping("Taxable income", "15", "Tax Computation", "currency"),
    
    # Tax
    "f2_06": FieldMapping("Tax", "16", "Tax and Credits", "currency"),
    "f2_07": FieldMapping("Schedule 2, line 3", "17", "Tax and Credits", "currency"),
    "f2_08": FieldMapping("Add lines 16 and 17", "18", "Tax and Credits", "currency"),
    
    # Credits
    "f2_09": FieldMapping("Child tax credit / credit for other dependents", "19", "Tax and Credits", "currency"),
    "f2_10": FieldMapping("Schedule 3, line 8", "20", "Tax and Credits", "currency"),
    "f2_11": FieldMapping("Add lines 19 and 20", "21", "Tax and Credits", "currency"),
    "f2_12": FieldMapping("Subtract line 21 from line 18", "22", "Tax and Credits", "currency"),
    "f2_13": FieldMapping("Other taxes", "23", "Tax and Credits", "currency"),
    "f2_14": FieldMapping("Total tax", "24", "Tax and Credits", "currency"),
    
    # Payments
    "f2_15": FieldMapping("Federal income tax withheld", "25a", "Payments", "currency"),
    "f2_16": FieldMapping("Estimated tax payments", "26", "Payments", "currency"),
    "f2_17": FieldMapping("Earned income credit (EIC)", "27", "Payments", "currency"),
    "f2_18": FieldMapping("Additional child tax credit", "28", "Payments", "currency"),
    "f2_19": FieldMapping("American opportunity credit", "29", "Payments", "currency"),
    
    # Refund
    "f2_31": FieldMapping("Refund amount", "35a", "Refund", "currency"),
    "f2_32": FieldMapping("Routing number", "35b", "Refund", "text"),
    "f2_33": FieldMapping("Account number", "35d", "Refund", "text"),
    
    # Amount owed
    "f2_34": FieldMapping("Amount you owe", "37", "Amount You Owe", "currency"),
    "f2_35": FieldMapping("Estimated tax penalty", "38", "Amount You Owe", "currency"),
}


def get_field_mapping(field_id: str, form_type: str = "irs_1040") -> Optional[FieldMapping]:
    """
    Get field mapping for a given field ID.
    
    Args:
        field_id: Full XFA field ID or leaf node name
        form_type: Type of form (currently only 'irs_1040' supported)
    
    Returns:
        FieldMapping if found, None otherwise
    """
    import re
    
    # Extract leaf node: "topmostSubform[0].Page1[0].f1_01[0]" -> "f1_01"
    leaf = field_id.split('.')[-1]
    leaf = re.sub(r'\[\d+\]', '', leaf)
    
    if form_type == "irs_1040":
        return IRS_1040_2025_FIELDS.get(leaf)
    
    return None


def detect_form_type(metadata: dict) -> Optional[str]:
    """
    Detect form type from PDF metadata.
    """
    title = str(metadata.get("title", "")).lower()
    
    if "1040" in title and ("tax" in title or "income" in title):
        return "irs_1040"
    
    return None
