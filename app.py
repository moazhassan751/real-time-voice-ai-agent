"""
Gradio Web Interface for the Real-Time Voice AI Agent.
Prepared for deployment on Hugging Face Spaces.
"""

import os
import gradio as gr
from dotenv import load_dotenv

import stt
import llm
import tts
from config import SYSTEM_PROMPT

# Load environment variables
load_dotenv()


def init_state():
    """Initialize the conversation history for a new user session."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def process_audio(audio_path: str, history: list) -> tuple:
    """Handle voice input from the microphone."""
    if not audio_path:
        return history, history[1:], None

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    transcription = stt.transcribe(audio_bytes)
    if not transcription:
        return history, history[1:], None

    return process_text(transcription, history)


import base64
import tempfile

def process_base64_audio(base64_audio: str, history: list) -> tuple:
    """Handle voice input from the custom JS microphone."""
    if not base64_audio or not base64_audio.startswith("data:audio"):
        return history, history[1:], None

    try:
        header, encoded = base64_audio.split(",", 1)
        audio_bytes = base64.b64decode(encoded)
        
        transcription = stt.transcribe(audio_bytes)
        if not transcription:
            return history, history[1:], None
            
        return process_text(transcription, history)
    except Exception as e:
        print(f"  [Base64 decoding error] {e}")
        return history, history[1:], None


def process_text(text: str, history: list) -> tuple:
    """Handle text input (either transcribed from voice, or typed directly)."""
    if not text or not str(text).strip():
        return history, history[1:], None

    # Pass the per-user history to llm.chat to maintain thread safety across concurrent users
    reply_text = llm.chat(str(text), messages=history)

    # Synthesize the audio reply
    audio_bytes = tts.synthesize(reply_text)

    # Convert audio bytes directly to a Base64 string for native JS playback, prefixed with timestamp
    base64_audio = ""
    if audio_bytes:
        import time
        encoded = base64.b64encode(audio_bytes).decode('utf-8')
        base64_audio = f"{time.time()}|data:audio/mp3;base64,{encoded}"

    # Return updated full history (for State), sliced history (for Chatbot), and base64 audio string
    return history, history[1:], base64_audio


def clear_conversation() -> tuple:
    """Reset the conversation state and UI."""
    return init_state(), [], None


# Explicit professional theme (slate/charcoal + indigo)
custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="#0f172a",
    body_text_color="#f1f5f9",
    block_background_fill="#1e293b",
    block_border_width="1px",
    block_border_color="#334155",
    block_label_text_color="#94a3b8",
    block_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    button_primary_background_fill="#4f46e5",
    button_primary_background_fill_hover="#4338ca",
    button_primary_text_color="white",
    border_color_primary="#334155",
    panel_background_fill="#1e293b",
)

# Custom CSS to hide Gradio chrome and style the pill bar
custom_css = """
/* Hide Gradio Footer and APIs */
footer { display: none !important; }
.gradio-container-4-43-0 .footer { display: none !important; }
.api-logo { display: none !important; }

/* Hidden Audio Player for Autoplay */
.hidden-audio {
    position: absolute !important;
    left: -9999px !important;
    top: -9999px !important;
}

/* Contained layout */
.gradio-container { max-width: 960px !important; margin: 0 auto; padding: 2rem 1rem !important; }

/* Hide redundant action buttons on components globally, except chatbot */
.form-action-buttons { display: none !important; }
.message-wrap .form-action-buttons { display: flex !important; }

/* Custom Header Block */
.custom-header {
    padding: 1.5rem;
    background: #1e293b;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border: 1px solid #334155;
    position: relative;
}
.custom-header h1 { margin: 0 0 0.5rem 0; color: #f8fafc; font-weight: 600; font-size: 1.5rem; }
.custom-header p { margin: 0; color: #94a3b8; font-size: 0.95rem; }

/* Link-style clear button */
#clear-btn {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    background: transparent;
    border: none;
    color: #64748b;
    text-decoration: underline;
    box-shadow: none;
    font-size: 0.9rem;
    width: auto;
    padding: 0;
}
#clear-btn:hover { color: #f8fafc; background: transparent; }

/* Conversation Chatbot container */
#chat-card {
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1rem;
}

/* Pill-shaped Input Bar */
#pill-bar {
    display: flex;
    align-items: stretch;
    background: #1e293b;
    border-radius: 999px;
    padding: 6px 12px;
    border: 1px solid #334155;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-top: 1rem;
    overflow: hidden;
}
#pill-bar > div {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
#pill-bar textarea {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    resize: none !important;
    color: #f1f5f9;
}
#pill-bar button.primary {
    border-radius: 999px !important;
    margin-left: 8px;
    padding: 0 24px;
}

/* Custom Mic Button */
#custom-mic-btn { background: transparent; border: none; cursor: pointer; padding: 8px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: all 0.2s; color: #4f46e5; margin: 0 4px; }
#custom-mic-btn:hover { background: #334155; }
#custom-mic-btn svg { width: 24px; height: 24px; fill: currentColor; }
#custom-mic-btn.recording { color: #ef4444; animation: pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite; }
#custom-mic-btn.thinking { color: #94a3b8; animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse-ring { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
#hidden-process-btn { display: none !important; }
"""

mic_html = """
<button id="custom-mic-btn" type="button" title="Toggle Recording">
    <svg viewBox="0 0 24 24">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
    </svg>
</button>
"""

custom_js = """
<script>
(function() {
    if (window.micInitialized) return;
    window.micInitialized = true;
    
    let mediaRecorder = null;
    let audioChunks = [];
    
    const setupMic = setInterval(() => {
        const btn = document.getElementById('custom-mic-btn');
        if (btn) {
            clearInterval(setupMic);
            btn.addEventListener('click', async () => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    btn.classList.remove('recording');
                } else {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        mediaRecorder = new MediaRecorder(stream);
                        audioChunks = [];
                        
                        mediaRecorder.ondataavailable = e => {
                            if (e.data.size > 0) audioChunks.push(e.data);
                        };
                        
                        mediaRecorder.onstop = () => {
                            const audioBlob = new Blob(audioChunks);
                            const reader = new FileReader();
                            reader.readAsDataURL(audioBlob);
                            reader.onloadend = () => {
                                window.latestAudioData = reader.result;
                                btn.classList.add('thinking');
                                const hiddenBtn = document.querySelector('#hidden-process-btn button');
                                if (hiddenBtn) hiddenBtn.click();
                            };
                        };
                        
                        mediaRecorder.start();
                        btn.classList.add('recording');
                    } catch (err) {
                        alert("Microphone access unavailable or denied. Use text input instead.");
                        console.error(err);
                    }
                }
            });
        }
    }, 500);
})();
</script>
"""

with gr.Blocks(title="Real-Time Voice AI Agent") as demo:
    session_history = gr.State(init_state)

    with gr.Column(elem_classes="custom-header"):
        gr.HTML(
            "<h1>Real-Time Voice AI Agent</h1>"
            "<p>A voice-driven assistant for scheduling, communication, and everyday tasks.</p>"
        )
        clear_btn = gr.Button("Clear Conversation", elem_id="clear-btn")

    with gr.Column(elem_id="chat-card"):
        chatbot = gr.Chatbot(
            label="Conversation",
            show_label=False,
            height=550,
            avatar_images=(None, None),
        )

    with gr.Row(elem_id="pill-bar"):
        text_input = gr.Textbox(
            show_label=False,
            container=False,
            placeholder="Ask anything...",
            scale=8,
        )
        gr.HTML(mic_html)
        send_btn = gr.Button("Send", variant="primary", scale=1)
        hidden_process_btn = gr.Button("Hidden", elem_id="hidden-process-btn", visible=True, elem_classes="hidden-btn")

    audio_output = gr.Textbox(
        visible=False,
        elem_id="audio-response-data"
    )

    # --- Event Handlers ---
    
    # 1. Voice input (triggered by JS hidden button)
    hidden_process_btn.click(
        fn=process_base64_audio,
        inputs=[text_input, session_history],
        outputs=[session_history, chatbot, audio_output],
        js="(text, history) => { return [window.latestAudioData, history]; }"
    )

    # 2. Text input via Send button
    send_btn.click(
        fn=process_text,
        inputs=[text_input, session_history],
        outputs=[session_history, chatbot, audio_output],
    ).then(
        fn=lambda: "",
        inputs=None,
        outputs=[text_input],
    )

    # 3. Text input via Enter key
    text_input.submit(
        fn=process_text,
        inputs=[text_input, session_history],
        outputs=[session_history, chatbot, audio_output],
    ).then(
        fn=lambda: "",
        inputs=None,
        outputs=[text_input],
    )

    # 4. Clear button
    clear_btn.click(
        fn=clear_conversation,
        inputs=None,
        outputs=[session_history, chatbot, audio_output],
    )

    # 5. Play audio via Native JS when Base64 data arrives
    audio_output.change(
        fn=None,
        inputs=[audio_output],
        outputs=None,
        js="(b64) => { const btn = document.getElementById('custom-mic-btn'); if(btn) btn.classList.remove('thinking'); if(b64 && b64.includes('|')) { let a = new Audio(b64.split('|')[1]); a.play(); } }"
    )

if __name__ == "__main__":
    demo.launch(theme=custom_theme, css=custom_css, head=custom_js)
