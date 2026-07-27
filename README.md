# Real-Time Voice AI Agent

This is a personal/academic project (built as part of an internship) demonstrating a full-stack, real-time conversational voice agent. It features near-instant speech-to-text, LLM reasoning with tool calling, and text-to-speech, all streamed seamlessly over WebSockets.

**Note:** The Google Workspace integrations (Calendar, Gmail, Drive, Sheets) in this project rely on a Google Cloud OAuth app configured in **Testing mode**. This means it only works with the developer's specific whitelisted test accounts. It is not a multi-tenant production app and cannot be used by the general public without creating your own Google Cloud project and supplying your own `credentials.json`.

## Features
- **Real-Time Voice Streaming:** Next.js frontend capturing microphone audio and streaming it via WebSockets.
- **Fast Reasoning:** Cerebras Cloud (gpt-oss-120b) powers the conversational engine with ultra-low latency.
- **Tools:**
  - **Time & Weather:** Live local time and Open-Meteo weather integrations.
  - **Reminders & Contacts:** Local JSON-backed reminder scheduling and contact management.
  - **Google Workspace:** Search Drive, create Calendar events, draft/send Gmails, and read/write Sheets.
- **Instant TTS:** edge-tts (Microsoft Edge Read-Aloud API) used for free, fast speech synthesis.
- **Instant STT:** Groq Whisper-large-v3-turbo for sub-second transcriptions.

## Architecture
- **Frontend:** Next.js, React, TailwindCSS, WebSockets.
- **Backend:** FastAPI, Python, Pytest.
- **AI Pipeline:** Groq (STT) -> Cerebras (LLM) -> edge-tts (TTS).

## Setup Instructions

1. **Clone or download** this repository.

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys** — copy the example env file and fill in your keys:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your API keys:
   ```
   GROQ_API_KEY=gsk_...
   CEREBRAS_API_KEY=csk_...
   ```

5. **Run the backend**:
   ```bash
   python -m uvicorn server:app --port 8000
   ```

6. **Run the frontend**:
   In a new terminal, navigate to `frontend/` and run:
   ```bash
   npm install
   npm run dev
   ```
   Then visit `http://localhost:3000` in your browser.
