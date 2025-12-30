
import logging
import sys
from unittest.mock import MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Mock the dependency BEFORE importing the module if possible, 
# or import and then replace.
from services.pdf import text_fitter
from services.pdf.text_fitter import TextFitter

def test_debug():
    print("WARNING: Starting Debug")
    
    # Mock LLM Service
    mock_service = MagicMock()
    mock_service.extract_field_value.return_value = {
        "value": "Very long descriptive sentence",
        "confidence": 0.9
    }
    
    # Manually Replace the function in the module
    original_get = text_fitter.get_local_llm_service
    text_fitter.get_local_llm_service = lambda: mock_service
    
    try:
        fitter = TextFitter()
        long_text = "This is a very long descriptive sentence that simply will not fit using standard abbreviations because it lacks them."
        
        print(f"Input: {long_text}")
        
        # Call fit
        res = fitter.fit(long_text, 35, field_context={"label": "Description"})
        
        print(f"Result Strategy: {res.strategy_used}")
        print(f"Result Fitted: {res.fitted}")
        
        if res.strategy_used != "llm_compression":
            print("FAILURE: Strategy was not llm_compression")
        else:
            print("SUCCESS: Strategy matches")
            
    finally:
        # Restore
        text_fitter.get_local_llm_service = original_get

if __name__ == "__main__":
    test_debug()
