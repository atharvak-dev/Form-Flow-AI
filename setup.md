# Form Wizard Pro - Setup Guide

## Quick Start

### Backend Setup
1. Navigate to backend directory:
   ```bash
   cd form-flow-backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Start the backend server:
   ```bash
   python main.py
   ```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd form-flow-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## API Keys Required

### Essential (for core functionality):
- **GOOGLE_API_KEY**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Used for: Form context analysis, voice processing, intelligent prompts

### Optional (for enhanced features):
- **OPENAI_API_KEY**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
  - Used for: Alternative LLM processing
- **DEEPGRAM_API_KEY**: Get from [Deepgram Console](https://console.deepgram.com/)
  - Used for: Enhanced speech-to-text
- **ELEVENLABS_API_KEY**: Get from [ElevenLabs](https://elevenlabs.io/)
  - Used for: Text-to-speech responses

## Features Implemented

✅ **Phase 1**: Voice input and STT pipeline (Web Speech API)
✅ **Phase 2**: Form parser using Playwright + BeautifulSoup
✅ **Phase 3**: LLM integration with form context analysis
✅ **Phase 4**: Pause handling, pronunciation correction, suggestions
✅ **Phase 5**: Form automation framework
⏳ **Phase 6**: Multilingual support and UI enhancements (future)

## Usage

1. **Paste Form URL**: Enter the URL of any online form
2. **Form Analysis**: The system analyzes form structure and creates context
3. **Voice Interaction**: Click the microphone and speak naturally
4. **Smart Processing**: AI processes your speech with context awareness
5. **Confirmation**: System asks for confirmation on unclear inputs
6. **Auto-Fill**: Completed data can be used to fill the actual form

## Browser Compatibility

- **Chrome/Edge**: Full support (Web Speech API)
- **Firefox**: Limited speech recognition support
- **Safari**: Partial support

## Troubleshooting

### Common Issues:
1. **Microphone not working**: Check browser permissions
2. **API errors**: Verify API keys in .env file
3. **Form not detected**: Some forms may use complex structures
4. **Speech recognition timeout**: Speak clearly and avoid long pauses

### Performance Tips:
- Use Chrome for best speech recognition
- Ensure stable internet connection
- Speak clearly and at moderate pace
- Use the pause suggestions when uncertain