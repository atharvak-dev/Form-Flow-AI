import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.captcha.solver import CaptchaSolverService, CaptchaType, SolveStrategy, CaptchaSolveResult

@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "http://example.com/form"
    return page

@pytest.fixture
def mock_twocaptcha():
    with patch('services.captcha.solver.TwoCaptchaClient') as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client

@pytest.mark.asyncio
async def test_solve_no_captcha(mock_page):
    solver = CaptchaSolverService()
    info = {"hasCaptcha": False}
    result = await solver.solve(mock_page, info)
    
    assert result.success
    assert result.strategy_used == SolveStrategy.NONE_REQUIRED

@pytest.mark.asyncio
async def test_solve_turnstile_auto_wait(mock_page):
    solver = CaptchaSolverService()
    info = {"hasCaptcha": True, "type": "cloudflare-turnstile"}
    
    # Mock auto-wait success
    mock_page.evaluate.return_value = "turnstile-token-123"
    
    result = await solver.solve(mock_page, info)
    
    assert result.success
    assert result.strategy_used == SolveStrategy.AUTO_WAIT
    assert result.token == "turnstile-token-123"

@pytest.mark.asyncio
async def test_solve_generic_image_captcha(mock_page, mock_twocaptcha):
    # Setup solver with API key
    solver = CaptchaSolverService(twocaptcha_key="dummy_key")
    info = {"hasCaptcha": True, "type": "generic-captcha", "selector": "#captcha_img"}
    
    # Mock image extraction
    # Since we can't easily mock inner helper methods without object patching, 
    # we'll rely on mocking page queries
    element = AsyncMock()
    element.evaluate.return_value = "IMG" # tagName
    element.screenshot.return_value = b"fake_image_bytes"
    mock_page.query_selector.return_value = element
    
    # Mock 2Captcha response
    mock_twocaptcha.solve_normal.return_value = MagicMock(
        success=True, 
        token="solved_text_123", 
        solve_time_seconds=1.5
    )
    
    result = await solver.solve(mock_page, info)
    
    assert result.success
    assert result.strategy_used == SolveStrategy.API_SOLVE
    assert result.captcha_type == CaptchaType.GENERIC
    assert result.token == "solved_text_123"
    
    # Verify image extraction was called
    mock_page.query_selector.assert_called_with("#captcha_img")
    element.screenshot.assert_called_once()
    
    # Verify API called with base64
    mock_twocaptcha.solve_normal.assert_called_once()
    
    # Verify token injection (typing into input)
    # The solver calls page.evaluate to find input and type
    assert mock_page.evaluate.call_count >= 1

@pytest.mark.asyncio
async def test_solve_fallback_manual(mock_page):
    # No API key configured
    solver = CaptchaSolverService(twocaptcha_key=None)
    info = {"hasCaptcha": True, "type": "recaptcha-v2"}
    
    result = await solver.solve(mock_page, info)
    
    assert not result.success
    assert result.strategy_used == SolveStrategy.MANUAL_FALLBACK
    assert result.requires_user_action
