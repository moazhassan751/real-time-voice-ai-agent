from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import base64

import stt
import llm
import tts
import logging
from config import SYSTEM_PROMPT, APP_ACCESS_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Real-Time Voice AI Agent Backend")

# Allow Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://real-time-voice-ai-agent-eight.vercel.app", "https://real-time-voice-ai-agent-flax.vercel.app"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class TextRequest(BaseModel):
    text: str
    history: List[ChatMessage] = []

class AudioRequest(BaseModel):
    audio_base64: str
    history: List[ChatMessage] = []

def format_history(history: List[ChatMessage]) -> list:
    """Ensure history always starts with the system prompt."""
    if not history:
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    
    formatted = []
    for msg in history:
        if hasattr(msg, "model_dump"):
            formatted.append(msg.model_dump())
        else:
            formatted.append(msg)
            
    if not formatted or formatted[0].get("role") != "system":
        formatted.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    return formatted

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat/text")
async def process_text(req: TextRequest):
    text = req.text.strip()
    history = format_history(req.history)

    if not text:
        return {"reply": "", "history": history, "audio_base64": None}

    # Pass history to llm.chat. This modifies the history array in-place!
    reply_text = llm.chat(text, messages=history)

    # Synthesize audio
    audio_bytes = tts.synthesize(reply_text)
    
    audio_base64 = None
    if audio_bytes:
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {
        "reply": reply_text,
        "history": history, 
        "audio_base64": audio_base64
    }

@app.post("/api/chat/audio")
async def process_audio(req: AudioRequest):
    history = format_history(req.history)
    
    if not req.audio_base64:
        return {"reply": "", "history": history, "audio_base64": None}

    try:
        # Strip data URL prefix if present and detect format
        b64_string = req.audio_base64
        ext = "webm"  # default fallback
        if "," in b64_string:
            header, b64_string = b64_string.split(",", 1)
            if "audio/mp4" in header or "audio/m4a" in header:
                ext = "m4a"
            elif "audio/wav" in header:
                ext = "wav"
            elif "audio/webm" in header:
                ext = "webm"
        
        audio_bytes = base64.b64decode(b64_string)
        
        # Transcribe the audio
        transcription = stt.transcribe(audio_bytes, ext=ext)
        if not transcription:
             return {"reply": "", "history": history, "audio_base64": None}
             
        # Generate LLM response
        reply_text = llm.chat(transcription, messages=history)
        
        # Synthesize reply audio
        reply_audio_bytes = tts.synthesize(reply_text)
        
        reply_audio_base64 = None
        if reply_audio_bytes:
            reply_audio_base64 = base64.b64encode(reply_audio_bytes).decode("utf-8")
            
        return {
            "reply": reply_text,
            "transcription": transcription,
            "history": history,
            "audio_base64": reply_audio_base64
        }
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import threading

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: Optional[str] = None):
    await websocket.accept()
    
    # Auth Gate Check
    if APP_ACCESS_TOKEN and token != APP_ACCESS_TOKEN:
        logger.warning("Rejected WebSocket connection: Invalid or missing token")
        await websocket.send_json({"type": "error", "message": "Access denied — invalid or missing credentials"})
        await websocket.close(code=1008)
        return

    try:
        while True:
            data = await websocket.receive_json()
            history = format_history(data.get("history", []))
            
            audio_base64 = data.get("audio_base64")
            text_input = data.get("text")
            
            if not audio_base64 and not text_input:
                continue

            transcription = ""
            
            if audio_base64:
                # 1. Extract audio bytes
                b64_string = audio_base64
                ext = "webm"
                if "," in b64_string:
                    header, b64_string = b64_string.split(",", 1)
                    if "audio/mp4" in header or "audio/m4a" in header:
                        ext = "m4a"
                    elif "audio/wav" in header:
                        ext = "wav"
                    elif "audio/webm" in header:
                        ext = "webm"
                
                audio_bytes = base64.b64decode(b64_string)
                
                # 2. Transcribe (Blocking but fast)
                transcription = stt.transcribe(audio_bytes, ext=ext)
                if not transcription:
                     await websocket.send_json({"type": "error", "message": "Could not hear you. Please try again."})
                     continue
                     
                await websocket.send_json({"type": "transcription", "text": transcription})
            elif text_input:
                transcription = text_input

            # 3. Setup streaming pipeline using threads
            text_queue = asyncio.Queue()
            audio_queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def sync_pipeline():
                try:
                    def intercepted_text_gen():
                        for chunk in llm.stream_chat(transcription, messages=history):
                            # Pass text chunk to async queue safely
                            asyncio.run_coroutine_threadsafe(text_queue.put(chunk), loop)
                            yield chunk

                    # Feed the intercepted text generator to TTS
                    for audio_chunk in tts.stream_synthesize_sentences(intercepted_text_gen()):
                        asyncio.run_coroutine_threadsafe(audio_queue.put(audio_chunk), loop)
                except Exception as e:
                    logger.error(f"Pipeline error: {e}")
                finally:
                    asyncio.run_coroutine_threadsafe(text_queue.put(None), loop)
                    asyncio.run_coroutine_threadsafe(audio_queue.put(None), loop)

            threading.Thread(target=sync_pipeline, daemon=True).start()

            # 4. Drain queues and send to websocket
            async def send_text():
                while True:
                    chunk = await text_queue.get()
                    if chunk is None:
                        break
                    await websocket.send_json({"type": "text_chunk", "text": chunk})

            async def send_audio():
                while True:
                    chunk = await audio_queue.get()
                    if chunk is None:
                        break
                    b64 = base64.b64encode(chunk).decode("utf-8")
                    await websocket.send_json({"type": "audio_chunk", "audio": b64})

            await asyncio.gather(send_text(), send_audio())
            
            # 5. Signal completion and send updated history
            await websocket.send_json({"type": "done", "history": history})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
