
import pytest
from unittest.mock import MagicMock, patch
from services.pdf.text_fitter import TextFitter, FitResult, LLMTextCompressor, fit_text

@pytest.fixture
def text_fitter():
    return TextFitter(domain="general")

class TestTextFitter:
    
    def test_direct_fit(self, text_fitter):
        """Should return direct fit if text is short enough."""
        res = text_fitter.fit("Short text", 20)
        assert res.strategy_used == "direct_fit"
        assert res.fitted == "Short text"
        assert res.truncated is False

    def test_abbreviation_strategy(self, text_fitter):
        """Should use abbreviations to fit text."""
        # "Street" -> "St", "Avenue" -> "Ave"
        long_text = "123 Main Street, Fifth Avenue"
        # Length 29. Max 25.
        # "123 Main St, Fifth Ave" -> Length 22.
        res = text_fitter.fit(long_text, 25)
        
        assert "St" in res.fitted
        assert "Ave" in res.fitted
        assert len(res.fitted) <= 25
        assert res.strategy_used == "abbreviations"

    def test_address_compression_structured(self, text_fitter):
        """Should apply specific address rules."""
        long_address = "1234 Longname Boulevard, Apartment 405, Springfield, Illinois, 62704-1234"
        # This is very long.
        # Goal: compact it.
        # "1234 Longname Blvd, Apt 405, Springfield, IL, 62704" (no zip ext)
        
        context = {"type": "address"}
        res = text_fitter.fit(long_address, 55, field_context=context)
        
        assert len(res.fitted) <= 55
        assert "Blvd" in res.fitted
        assert "Apt" in res.fitted
        assert "-1234" not in res.fitted # Zip extension removed
        assert res.strategy_used == "structured_address"

    @patch('services.pdf.text_fitter.get_local_llm_service')
    def test_llm_compression_integration(self, mock_get_service, text_fitter):
        """Should fallback to LLM if heuristics fail."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Setup mock to return a compressed string
        mock_service.extract_field_value.return_value = {
            "value": "Very long descriptive sentence",
            "confidence": 0.9
        }
        
        long_text = "This is a very long descriptive sentence that simply will not fit using standard abbreviations because it lacks them."
        # max_chars=30
        
        res = text_fitter.fit(long_text, 35, field_context={"label": "Description"})
        
        assert res.strategy_used == "llm_compression"
        assert res.fitted == "Very long descriptive sentence"
        assert len(res.fitted) <= 35
    
    @patch('services.pdf.text_fitter.get_local_llm_service')
    def test_hard_truncation_fallback(self, mock_get_service, text_fitter):
        """Should truncate if even LLM fails."""
        mock_get_service.return_value = None # LLM unavailable
        
        text = "Impossible to fit content"
        res = text_fitter.fit(text, 5, allow_truncation=True)
        
        assert res.truncated is True
        assert res.fitted.endswith("...")
