# Backend Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Step 1: Navigate to Backend Directory
```bash
cd form-flow-backend
```

## Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Install Playwright Browsers
```bash
playwright install
```

## Step 5: Configure Environment Variables
1. Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

2. Edit `.env` and add your API keys:
```env
# Required for AI features
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional (for enhanced features)
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### Getting API Keys:
- **Google Gemini API**: https://makersuite.google.com/app/apikey
- **OpenAI API** (optional): https://platform.openai.com/api-keys
- **ElevenLabs API** (optional): https://elevenlabs.io/

## Step 6: Run the Backend Server
```bash
python main.py
```

The backend will start on `http://localhost:8000`

## Verify Setup
Open your browser and visit:
- `http://localhost:8000` - Should show: `{"Hello": "Form Wizard Pro Backend is running"}`
- `http://localhost:8000/docs` - FastAPI interactive documentation

## Troubleshooting

### Port Already in Use
If port 8000 is busy, edit `main.py` and change:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```
to a different port like 8001.

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Playwright Issues
```bash
playwright install --force
```

## Running Both Frontend and Backend

### Terminal 1 (Backend):
```bash
cd form-flow-backend
python main.py
```

### Terminal 2 (Frontend):
```bash
cd form-flow-frontend
npm run dev
```

Now visit `http://localhost:5173` to use the application!
