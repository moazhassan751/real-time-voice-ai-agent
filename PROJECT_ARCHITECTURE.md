# Real-Time Voice AI Agent — Project Architecture & File Directory

This document provides a complete description of every file, script, data file, configuration, test file, and folder in the project.

---

## Directory Overview

```
voice-agent/
│
├── frontend/                   # Next.js React Web Application
│   ├── src/app/
│   │   ├── layout.tsx          # Next.js root layout
│   │   ├── page.tsx            # Main Chat Interface (WebSockets, MediaRecorder, AudioContext)
│   │   └── globals.css         # Tailwind & custom CSS variables
│   ├── tailwind.config.ts      # Tailwind CSS configuration
│   └── package.json            # Node.js dependencies
│
├── server.py                   # FastAPI WebSocket backend server
├── config.py                   # Global configuration, env validation & system prompt
├── stt.py                      # Speech-to-Text via Groq Whisper with prompt biasing
├── llm.py                      # Groq Llama 3.3 LLM (streaming), tool dispatch & error recovery
├── tts.py                      # Text-to-Speech via ElevenLabs API (streaming sentence generator)
│
├── main.py                     # Legacy: Command-line entry point & voice orchestration loop
├── audio_io.py                 # Legacy: Microphone audio capture & sounddevice stream
│
├── tools.py                    # Central tool registry (19 schemas + dispatch map)
│
├── time_tool.py                # Local time lookup tool
├── weather_tool.py             # Weather & forecast tool (Open-Meteo REST API)
├── reminders_tool.py           # Reminders manager (JSON-backed, fuzzy matching)
├── contacts_tool.py            # Contacts manager (JSON-backed, difflib matching)
├── google_auth.py              # Shared Google OAuth2 token & credential manager
├── calendar_tool.py            # Google Calendar integration (events + Meet links)
├── gmail_tool.py               # Gmail API integration (email sending)
├── drive_tool.py               # Google Drive integration (file search/read/create)
├── sheets_tool.py              # Google Sheets API integration (search/create/append)
│
├── contacts.json               # Persistent contact storage (name -> email mapping)
├── reminders.json              # Persistent reminder list storage
├── credentials.json            # Google Cloud OAuth2 Client Secrets (desktop app)
├── token.pickle                # Saved Google OAuth2 access & refresh tokens
├── .env                        # Local environment variables (API keys)
├── .env.example                # Example environment file template
├── .gitignore                  # Git ignore rules protecting secrets & runtime data
├── requirements.txt            # Python dependencies
├── README.md                   # Project summary, setup, and usage documentation
│
├── test_tools.py               # Direct tool function testing harness (no LLM/audio)
├── test_conversation.py        # Interactive CLI text harness (LLM + tools, no audio)
├── test_suite.py               # Automated edge case & multi-turn tool test suite
│
├── venv/                       # Isolated Python virtual environment
└── __pycache__/                # Python compiled bytecode cache files
```

---

## Detailed File Specifications

### 1. Web Application & Backend (Current Architecture)

#### [frontend/src/app/page.tsx](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/frontend/src/app/page.tsx)
- **What it is**: The main Next.js client-side React component.
- **Why it exists**: Provides a beautiful, dark-themed, glassmorphic UI for interacting with the AI.
- **How it works**: Uses the `MediaRecorder` API to capture microphone audio and send it as Base64 to the backend. Maintains a persistent `WebSocket` connection to the FastAPI server. Uses the `AudioContext` Web Audio API (`AudioStreamPlayer`) to dynamically queue and play streaming MP3 chunks from the backend without gaps. Also renders real-time streaming text (typewriter effect) for the LLM response.

#### [server.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/server.py)
- **What it is**: FastAPI server that handles WebSocket connections.
- **Why it exists**: Serves as the bridge between the Next.js frontend and the AI pipelines.
- **How it works**: Exposes a `/ws/chat` WebSocket endpoint. When base64 audio or text arrives, it runs `stt.py` to transcribe it, then pipes the text into `llm.py`'s streaming generator, and pipes *that* into `tts.py`'s streaming sentence synthesizer using `asyncio` Queues and Python `threading` to push audio and text chunks to the frontend simultaneously.

### 2. Core AI Pipeline

#### [config.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/config.py)
- **What it is**: Configuration hub loading environment variables and defining system settings.
- **Why it exists**: Prevents hardcoding of model names, sampling rates, API keys, or system instructions.
- **How it works**: Uses `python-dotenv` to load `.env`. Defines model constants (`whisper-large-v3-turbo`, `llama-3.3-70b-versatile`, `eleven_turbo_v2_5`) and the comprehensive `SYSTEM_PROMPT` instructing the AI on voice behavior, contact lookups, and confirmation rules.

#### [stt.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/stt.py)
- **What it is**: Speech-to-Text transcriber with dynamic prompt biasing.
- **Why it exists**: Converts spoken voice recordings into clean text transcriptions.
- **How it works**: Sends recorded WAV bytes to Groq's hosted Whisper API. Reads saved contact names from `contacts_tool.get_contact_names()` and dynamically injects them into Whisper's `prompt` parameter (e.g., `prompt="Names: Ahmed, Moaz, Usman"`). This biases the speech recognition model so non-English names are recognized accurately. Now features Python standard `logging`.

#### [llm.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/llm.py)
1. **Speech-to-Text (STT):**
   - We use Groq's `whisper-large-v3-turbo` because it provides near-instant transcription, essential for conversational flow.
2. **Large Language Model (LLM):**
   - **Cerebras Cloud** (running `llama3.3-70b`) provides extremely fast inference and natively supports OpenAI-compatible function calling. It orchestrates the tool calls and generates the final text.
3. **Text-to-Speech (TTS):**
   - **edge-tts** leverages Microsoft Edge's Read-Aloud API (like `en-US-AriaNeural`) to synthesize the response completely for free without API keys.

#### [tts.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/tts.py)
- **What it is**: Text-to-Speech synthesizer and audio streaming module.
- **Why it exists**: Converts the agent's text response into natural human speech.
- **How it works**: Exposes a `stream_synthesize_sentences(text_iterator)` function that groups incoming LLM text tokens into complete sentences using regex, and immediately synthesizes each sentence using `edge-tts`. Yields raw MP3 byte chunks for near-instant playback.

### 3. Central Tool Registry & Extensions

#### [tools.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/tools.py)
- **What it is**: The master tool registry containing 19 tool schemas and the dispatch dictionary.
- **Why it exists**: Provides a single source of truth for all tools available to the LLM.
- **How it works**: Imports tool functions from all dedicated tool modules. Exposes `TOOL_DISPATCH` (mapping tool names to Python callables) and `TOOL_SCHEMAS` (OpenAI-formatted JSON schemas describing parameters, descriptions, and required fields).

### 4. Dedicated Tool Modules

#### [time_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/time_tool.py)
- **Function**: `get_current_time(timezone="local")`
- **What & How**: Returns the current local date, day of the week, and time formatted as a natural spoken sentence using Python's `datetime.now()`.

#### [weather_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/weather_tool.py)
- **Functions**: `get_weather(city)`, `get_weather_forecast(city, days_ahead=1)`
- **What & How**: Uses the free Open-Meteo REST API (no API key required). Geocodes city names to latitude/longitude coordinates, queries real-time conditions or daily forecast data, maps WMO weather codes to English descriptions (e.g. "slight rain showers"), and formats the output for speech.

#### [reminders_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/reminders_tool.py)
- **Functions**: `add_reminder(task, due)`, `list_reminders()`, `complete_reminder(task_description)`
- **What & How**: Manages tasks stored in `reminders.json`. `complete_reminder` uses word overlap scoring to match spoken task descriptions (e.g., matching "milk" to "buy groceries and milk").

#### [contacts_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/contacts_tool.py)
- **Functions**: `lookup_contact(name)`, `add_contact(name, email, notes)`, `list_contacts()`, `get_contact_names()`
- **What & How**: Manages contacts in `contacts.json`. `lookup_contact` uses `difflib.get_close_matches(cutoff=0.6)` for fuzzy matching so STT misspellings (e.g., "Moas") successfully match saved contacts ("Moaz"). `get_contact_names()` supplies names to `stt.py` for Whisper prompt biasing.

#### [google_auth.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/google_auth.py)
- **Function**: `get_google_credentials()`
- **What & How**: Handles Google OAuth2 authentication flow across Google APIs (Calendar, Gmail, Drive, Sheets). Loads `credentials.json`, manages interactive browser authorization on first run, and caches tokens in `token.pickle` for automatic refresh.

#### [calendar_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/calendar_tool.py)
- **Functions**: `create_event(...)`, `list_events(...)`
- **What & How**: Interfaces with Google Calendar API v3. `create_event` creates events, invites attendees, and generates Google Meet video conference links (`hangoutsMeet`).

#### [gmail_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/gmail_tool.py)
- **Function**: `send_email(to, subject, body)`
- **What & How**: Interfaces with Gmail API v1. Constructs RFC 2822 MIME plain-text emails, encodes them in URL-safe base64, and sends them via `service.users().messages().send()`.

#### [drive_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/drive_tool.py)
- **Functions**: `search_files(query)`, `read_file_content(file_name)`, `create_file(name, content)`
- **What & How**: Interfaces with Google Drive API v3. Searches files by name, reads Google Docs content via export formats or Drive files API, and creates new Google Docs.

#### [sheets_tool.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/sheets_tool.py)
- **Functions**: `find_spreadsheet_by_name(name)`, `create_spreadsheet(title, headers)`, `read_range(...)`, `append_row(...)`
- **What & How**: Interfaces with Google Sheets API v4. Resolves spreadsheet names to spreadsheet IDs, creates new spreadsheets, reads A1-notation cell ranges, and appends data rows (e.g. logging expenses).

---

### 5. Data Storage & Environment Files

#### [contacts.json](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/contacts.json) & [reminders.json](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/reminders.json)
- **What they are**: Local JSON databases storing contact profiles and active user reminders.

#### [credentials.json](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/credentials.json) & [token.pickle](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/token.pickle)
- **What they are**: Google OAuth 2.0 credentials and binary serialized user session tokens.

#### [.env](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/.env) & [.env.example](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/.env.example)
- **What they are**: Private API keys (`GROQ_API_KEY`, `ELEVENLABS_API_KEY`) and template.

#### [requirements.txt](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/requirements.txt)
- **What they are**: Python dependencies for the backend.

---

### 6. Legacy & Testing Files

#### [main.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/main.py) & [audio_io.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/audio_io.py)
- **What they are**: Original command-line voice orchestrator and sounddevice microphone capture script. Superseded by the Next.js Web UI.

#### [test_tools.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/test_tools.py), [test_conversation.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/test_conversation.py), [test_suite.py](file:///c:/Users/ITSolutions/Desktop/Real%E2%80%91Time%20Voice%20AI%20Agent/voice-agent/test_suite.py)
- **What they are**: Direct tool testing script, interactive text-based CLI chat harness, and comprehensive automated testing suite. Validates edge cases and multi-turn LLM tool execution.
