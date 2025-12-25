
import pytest
from unittest.mock import Mock, patch
from services.ai.conversation_agent import ConversationAgent, ConversationSession
from services.ai.voice_processor import VoiceInputProcessor

class TestConversationAgentPhase1:
    
    @pytest.fixture
    def agent(self):
        return ConversationAgent(api_key=None)

    @pytest.fixture
    def session(self):
        return ConversationSession(
            id="test-session",
            form_schema=[{"name": "email", "type": "email"}],
            form_url="http://test.com"
        )

    def test_detect_input_mode_metadata(self, agent):
        """Test detection from input metadata."""
        # Explicit voice mode
        assert agent._detect_input_mode({'input_mode': 'voice'}, 's1') is True
        assert agent.input_mode_by_session['s1'] == 'voice'
        
        # Explicit text mode
        assert agent._detect_input_mode({'input_mode': 'text'}, 's2') is False
        assert agent.input_mode_by_session['s2'] == 'text'
        
        # Inferred from signals
        assert agent._detect_input_mode({'stt_provider': 'google'}, 's3') is True
        
        # Fallback to history
        assert agent._detect_input_mode(None, 's1') is True  # Remembers voice

    @pytest.mark.asyncio
    async def test_process_input_with_voice_metadata(self, agent, session):
        """Test that voice metadata triggers detection."""
        from unittest.mock import AsyncMock
        
        # Setup session in agent
        agent._local_sessions[session.id] = session
        
        with patch.object(VoiceInputProcessor, 'normalize_voice_input') as mock_norm:
            mock_norm.return_value = "normalized text"
            
            # Mock intent recognizer to avoid side effects
            with patch('services.ai.conversation_agent.IntentRecognizer') as MockIntent:
                MockIntent.return_value.detect_intent.return_value = (None, 0.0)
                
                # Mock methods that interact with LLM/external services
                agent._process_with_llm = AsyncMock(return_value=None)
                agent._process_with_fallback = Mock(return_value=Mock(
                    message="test",
                    extracted_values={},
                    confidence_scores={},
                    needs_confirmation=[],
                    remaining_fields=[],
                    is_complete=False,
                    next_questions=[]
                ))
                
                try:
                    await agent.process_user_input(
                        session.id, 
                        "raw voice input",
                        input_metadata={'input_mode': 'voice'}
                    )
                except Exception:
                    pass  # We only care about input mode detection
                
                # Verify input mode was tracked
                assert agent.input_mode_by_session[session.id] == 'voice'

    def test_fuzzy_field_matching(self, agent, session):
        """Test fuzzy field matching logic."""
        # Direct match
        fields = ['email', 'phone', 'address']
        assert agent._fuzzy_match_field('email', fields, session) == 'email'
        
        # Case insensitive
        assert agent._fuzzy_match_field('Email', fields, session) == 'email'
        
        # Fuzzy match
        assert agent._fuzzy_match_field('emial', fields, session) == 'email'
        assert agent._fuzzy_match_field('adress', fields, session) == 'address'
        
        # Label match (if session provided)
        # Assuming schema has label "Email Address" for 'email'
        # But my fixture has labels? No, added in fixture below
        session.form_schema = [
            {"name": "email", "label": "Email Address", "type": "email"},
            {"name": "phone", "label": "Phone Number", "type": "tel"}
        ]
        
        assert agent._fuzzy_match_field('phone number', fields, session) == 'phone'
        
    def test_should_confirm_integration(self, agent, session):
        """Test _should_confirm delegates correctly."""
        # Force voice mode
        agent.input_mode_by_session[session.id] = 'voice'
        
        with patch('services.ai.voice_processor.ConfidenceCalibrator.should_confirm') as mock_confirm:
            mock_confirm.return_value = True
            
            result = agent._should_confirm('email', 'val', 0.8, session)
            
            assert result is True
            mock_confirm.assert_called_with(
                field={"name": "email", "type": "email"},
                confidence=0.8,
                context=session.conversation_context,
                stt_confidence=1.0,
                is_voice=True
            )
