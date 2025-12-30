"""
Abbreviation Dictionaries for Text Compression.

Contains standard and domain-specific abbreviations for intelligent text fitting.
"""

from typing import Dict

# =============================================================================
# Standard Abbreviations (General Purpose)
# =============================================================================

ADDRESS_ABBREVIATIONS = {
    "Street": "St", "Avenue": "Ave", "Road": "Rd", "Boulevard": "Blvd",
    "Drive": "Dr", "Lane": "Ln", "Court": "Ct", "Place": "Pl", "Circle": "Cir",
    "Highway": "Hwy", "Parkway": "Pkwy", "Terrace": "Ter", "Trail": "Trl",
    "Way": "Way", "North": "N", "South": "S", "East": "E", "West": "W",
    "Northeast": "NE", "Northwest": "NW", "Southeast": "SE", "Southwest": "SW",
    "Apartment": "Apt", "Suite": "Ste", "Building": "Bldg", "Floor": "Fl",
    "Room": "Rm", "Unit": "Unit",
}

TITLE_ABBREVIATIONS = {
    "Doctor": "Dr", "Professor": "Prof", "Mister": "Mr", "Misses": "Mrs",
    "Miss": "Ms", "Junior": "Jr", "Senior": "Sr", "Incorporated": "Inc",
    "Corporation": "Corp", "Company": "Co", "Limited": "Ltd", 
    "Representative": "Rep", "Executive": "Exec", "Director": "Dir",
    "Manager": "Mgr", "Assistant": "Asst",
}

STATE_ABBREVIATIONS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}

MONTH_ABBREVIATIONS = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
}

COMMON_ABBREVIATIONS = {
    "Number": "No", "Numbers": "Nos", "Telephone": "Tel", "Extension": "Ext",
    "Department": "Dept", "Information": "Info", "Reference": "Ref",
    "International": "Intl", "Association": "Assn", "University": "Univ",
    "Institute": "Inst", "Foundation": "Fdn", "Organization": "Org",
    "Government": "Govt", "Approximately": "Approx", "Additional": "Addl",
    "Maximum": "Max", "Minimum": "Min", "Average": "Avg", "Estimated": "Est",
    "Continued": "Cont", "Certificate": "Cert", "Professional": "Prof",
}

# =============================================================================
# Domain Specific Abbreviations
# =============================================================================

MEDICAL_ABBREVIATIONS = {
    "Patient": "Pt", "Diagnosis": "Dx", "Prescription": "Rx", "Treatment": "Tx",
    "History": "Hx", "Symptoms": "Sx", "Complaint": "CC", "Emergency Room": "ER",
    "Intensive Care Unit": "ICU", "Blood Pressure": "BP", "Heart Rate": "HR",
    "Frequency": "Freq", "Tablet": "Tab", "Capsule": "Cap", "Solution": "Sol",
    "Appointment": "Appt", "Referral": "Ref", "Examination": "Exam",
    "Physician": "Phys", "Condition": "Cond",
}

LEGAL_ABBREVIATIONS = {
    "Plaintiff": "Pl", "Defendant": "Def", "Attorney": "Atty", "versus": "v.",
    "Agreement": "Agmt", "Contract": "K", "Regulation": "Reg", "Statute": "Stat",
    "Exhibit": "Ex", "Judgement": "Jmt", "Petition": "Pet", "Respondent": "Resp",
    "Appellant": "Appt", "Circuit": "Cir", "District": "Dist", "Evidence": "Evid",
    "Testimony": "Test", "Affidavit": "Aff",
}

BUSINESS_ABBREVIATIONS = {
    "Account": "Acct", "Amount": "Amt", "Balance": "Bal", "Invoice": "Inv",
    "Payment": "Pmt", "Received": "Recd", "Year to Date": "YTD", 
    "Return on Investment": "ROI", "Purchase Order": "PO", "Quarter": "Qtr",
    "Fiscal Year": "FY", "Meeting": "Mtg", "Manager": "Mgr", "Assistant": "Asst",
}


def get_abbreviations(domain: str = "general") -> Dict[str, str]:
    """
    Get combined dictionary of abbreviations for a specific domain.
    
    Args:
        domain: One of 'general', 'medical', 'legal', 'business'
        
    Returns:
        Dictionary of {full_word: abbreviation}
    """
    base = {
        **ADDRESS_ABBREVIATIONS,
        **TITLE_ABBREVIATIONS,
        **STATE_ABBREVIATIONS,
        **MONTH_ABBREVIATIONS,
        **COMMON_ABBREVIATIONS
    }
    
    if domain == "medical":
        base.update(MEDICAL_ABBREVIATIONS)
    elif domain == "legal":
        base.update(LEGAL_ABBREVIATIONS)
    elif domain == "business":
        base.update(BUSINESS_ABBREVIATIONS)
        
    return base
