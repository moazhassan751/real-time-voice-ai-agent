"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mic, Send, Square, Trash2, Volume2 } from "lucide-react";

type Message = {
  role: "system" | "user" | "assistant" | "tool";
  content: string | null;
  tool_calls?: any[];
  tool_call_id?: string;
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  const wsRef = useRef<WebSocket | null>(null);
  const audioPlayerRef = useRef<any>(null);

  // Audio Stream Player using HTMLAudioElement for better compatibility
  const initAudioPlayer = () => {
    if (!audioPlayerRef.current) {
      audioPlayerRef.current = {
        queue: [],
        isPlaying: false,
        playChunk(base64Audio: string) {
          // ElevenLabs returns mp3 chunks
          const audio = new Audio("data:audio/mpeg;base64," + base64Audio);
          this.queue.push(audio);
          if (!this.isPlaying) {
            this.playNext();
          }
        },
        playNext() {
          if (this.queue.length === 0) {
            this.isPlaying = false;
            return;
          }
          this.isPlaying = true;
          const nextAudio = this.queue.shift();
          if (nextAudio) {
            nextAudio.onended = () => this.playNext();
            nextAudio.onerror = (e: any) => {
              console.error("Audio playback error", e);
              this.playNext();
            };
            nextAudio.play().catch((e: any) => {
              console.error("Audio play promise rejected:", e);
              this.playNext();
            });
          }
        }
      };
    }
  };

  useEffect(() => {
    const WS_URL = process.env.NEXT_PUBLIC_BACKEND_WS_URL || "ws://127.0.0.1:8000/ws/chat";
    const token = process.env.NEXT_PUBLIC_APP_ACCESS_TOKEN || "";
    
    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "transcription") {
        setMessages((prev) => [...prev, { role: "user", content: data.text }]);
      } 
      else if (data.type === "text_chunk") {
        setIsProcessing(false);
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMsg = newMessages[newMessages.length - 1];
          if (lastMsg && lastMsg.role === "assistant") {
            newMessages[newMessages.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + data.text
            };
          } else {
            newMessages.push({ role: "assistant", content: data.text });
          }
          return newMessages;
        });
      }
      else if (data.type === "audio_chunk") {
        if (audioPlayerRef.current) {
          audioPlayerRef.current.playChunk(data.audio);
        }
      }
      else if (data.type === "done") {
        setIsProcessing(false);
        if (data.history) {
            // Keep tool messages hidden by filtering out tool roles in rendering, 
            // but we must store the full history to send back on the next turn.
            setMessages(data.history);
        }
      }
      else if (data.type === "error") {
        setIsProcessing(false);
        if (data.message.includes("Access denied")) {
            setAuthError(data.message);
        } else {
            alert(data.message);
        }
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleSendText = useCallback(() => {
    if (!inputText.trim() || !wsRef.current) return;
    initAudioPlayer();

    setIsProcessing(true);
    const textToSend = inputText;
    setInputText("");

    const updatedHistory = [...messages, { role: "user" as const, content: textToSend }];
    setMessages(updatedHistory);

    // To process text only via WS, we simulate audio empty and pass history.
    // However, our backend WS endpoint currently expects audio_base64 to trigger.
    // Let's modify the backend call to support text-only if needed, or we just send empty audio.
    // Since our backend requires `audio_base64` to continue the loop in the current implementation,
    // wait, we should just use the REST endpoint for text?
    // Actually, sending text over WS is better. 
    // Let's send it as a JSON message. We'll update the backend to handle text.
    wsRef.current.send(JSON.stringify({ text: textToSend, history: updatedHistory }));
  }, [inputText, messages]);

  const startRecording = async () => {
    try {
      initAudioPlayer();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        setIsProcessing(true);
        const audioBlob = new Blob(audioChunksRef.current);
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          if (wsRef.current) {
             wsRef.current.send(JSON.stringify({ 
                 audio_base64: reader.result as string, 
                 history: messages 
             }));
          }
        };
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied or unavailable.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  const visibleMessages = (messages || []).filter(
    m => m.role !== "system" && m.role !== "tool" && m.content && m.content.trim() !== ""
  );

  if (!mounted) return null;

  if (authError) {
    return (
      <div className="flex flex-col h-screen bg-[#09090b] text-white overflow-hidden items-center justify-center">
         <div className="max-w-md p-6 bg-red-500/10 border border-red-500/20 rounded-2xl flex flex-col items-center text-center">
            <h2 className="text-xl font-semibold text-red-400 mb-2">Connection Rejected</h2>
            <p className="text-sm text-red-300/80">{authError}</p>
         </div>
      </div>
    );
  }

  return (
    <div suppressHydrationWarning className="flex flex-col h-screen bg-[#09090b] text-white overflow-hidden relative">
      {/* Ambient background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-violet-600/[0.07] blur-[120px] animate-float" />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-cyan-500/[0.05] blur-[120px] animate-float" style={{ animationDelay: "3s" }} />
      </div>

      {/* Main container */}
      <div className="relative z-10 flex flex-col h-full max-w-3xl w-full mx-auto">
        {/* ── Header ── */}
        <header className="flex items-center justify-between px-6 py-5 shrink-0">
          <div className="flex items-center gap-3">
            {/* Logo mark */}
            <div className="relative w-9 h-9">
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 opacity-80" />
              <div className="absolute inset-[2px] rounded-[10px] bg-[#09090b] flex items-center justify-center">
                <Volume2 className="w-4 h-4 text-violet-400" />
              </div>
            </div>
            <div>
              <h1 className="text-[15px] font-semibold tracking-tight text-white/90">Voice AI Agent</h1>
              <p className="text-[11px] text-white/30 font-medium tracking-wide uppercase">Real-time Assistant</p>
            </div>
          </div>

          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMessages([])}
              className="text-white/30 hover:text-white/60 hover:bg-white/5 rounded-lg text-xs gap-1.5 transition-all duration-200"
              data-testid="clear-button"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </Button>
          )}
        </header>

        {/* Subtle separator */}
        <div className="mx-6 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />

        {/* ── Chat area ── */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar"
          data-testid="chat-container"
        >
          {/* Empty state */}
          {visibleMessages.length === 0 && !isProcessing && (
            <div className="flex flex-col items-center justify-center h-full animate-fade-up">
              {/* Orb */}
              <div className="relative mb-8">
                <div className="absolute inset-0 w-24 h-24 rounded-full bg-gradient-to-br from-violet-500/20 to-cyan-400/20 blur-xl animate-float" />
                <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-violet-500/10 to-cyan-400/10 border border-white/[0.06] flex items-center justify-center">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-violet-500/20 to-cyan-400/20 flex items-center justify-center">
                    <Mic className="w-6 h-6 text-white/40" />
                  </div>
                </div>
              </div>
              <h2 className="text-lg font-medium text-white/70 mb-2">How can I help you?</h2>
              <p className="text-sm text-white/25 max-w-xs text-center leading-relaxed">
                Type a message or tap the microphone to start a voice conversation.
              </p>

              {/* Quick suggestion chips */}
              <div className="flex flex-wrap gap-2 mt-8 justify-center max-w-md">
                {["What's the weather?", "Set a reminder", "Check my calendar", "Send an email"].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => { setInputText(suggestion); }}
                    className="px-4 py-2 rounded-full text-[13px] text-white/35 border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.05] hover:text-white/50 hover:border-white/[0.1] transition-all duration-200 cursor-pointer"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {visibleMessages.length > 0 && (
            <div className="flex flex-col gap-4">
              {visibleMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex msg-enter ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  style={{ animationDelay: `${i * 0.05}s` }}
                  data-testid={`chat-message-${msg.role}`}
                >
                  {msg.role === "assistant" && (
                    <div className="shrink-0 mr-3 mt-1">
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-400/20 border border-white/[0.06] flex items-center justify-center">
                        <Volume2 className="w-3.5 h-3.5 text-violet-400/70" />
                      </div>
                    </div>
                  )}

                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed ${
                      msg.role === "user"
                        ? "bg-violet-600/90 text-white rounded-br-md shadow-lg shadow-violet-600/10"
                        : "bg-white/[0.04] text-white/80 rounded-bl-md border border-white/[0.06]"
                    }`}
                  >
                    {msg.content}
                  </div>

                  {msg.role === "user" && (
                    <div className="shrink-0 ml-3 mt-1">
                      <div className="w-7 h-7 rounded-lg bg-white/[0.06] border border-white/[0.06] flex items-center justify-center">
                        <span className="text-[11px] font-medium text-white/40">You</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Processing indicator */}
              {isProcessing && (
                <div className="flex justify-start msg-enter">
                  <div className="shrink-0 mr-3 mt-1">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-400/20 border border-white/[0.06] flex items-center justify-center">
                      <Volume2 className="w-3.5 h-3.5 text-violet-400/70" />
                    </div>
                  </div>
                  <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl rounded-bl-md px-5 py-4 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-violet-400/60 typing-dot" />
                    <span className="w-2 h-2 rounded-full bg-violet-400/60 typing-dot" />
                    <span className="w-2 h-2 rounded-full bg-violet-400/60 typing-dot" />
                  </div>
                </div>
              )}

              <div ref={endOfMessagesRef} />
            </div>
          )}
        </div>

        {/* Subtle separator */}
        <div className="mx-6 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />

        {/* ── Input bar ── */}
        <div className="px-6 py-5 shrink-0">
          <div className="relative flex items-center gap-2">
            {/* Mic button */}
            <div className="relative">
              {isRecording && (
                <div className="absolute inset-0 rounded-xl animate-pulse-ring bg-red-500/30" />
              )}
              <Button
                size="icon"
                variant="ghost"
                className={`relative rounded-xl h-11 w-11 transition-all duration-300 cursor-pointer ${
                  isRecording
                    ? "bg-red-500/15 text-red-400 hover:bg-red-500/25 hover:text-red-300 animate-recording-pulse"
                    : "bg-white/[0.04] text-white/30 hover:text-white/60 hover:bg-white/[0.08] border border-white/[0.06]"
                }`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                data-testid="mic-button"
              >
                {isRecording ? <Square className="h-4 w-4 fill-current" /> : <Mic className="h-4.5 w-4.5" />}
              </Button>
            </div>

            {/* Text input */}
            <div className="flex-1 relative">
              <Input
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendText()}
                placeholder="Type your message…"
                className="w-full border border-white/[0.06] bg-white/[0.03] focus-visible:ring-1 focus-visible:ring-violet-500/30 focus-visible:border-violet-500/20 rounded-xl px-5 h-11 text-white/80 text-[14px] placeholder:text-white/20 transition-all duration-200"
                disabled={isRecording || isProcessing}
                data-testid="chat-input"
              />
            </div>

            {/* Send button */}
            <Button
              size="icon"
              className={`rounded-xl h-11 w-11 transition-all duration-300 cursor-pointer ${
                inputText.trim() && !isRecording && !isProcessing
                  ? "bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-600/20"
                  : "bg-white/[0.04] text-white/15 border border-white/[0.04] cursor-not-allowed"
              }`}
              onClick={handleSendText}
              disabled={!inputText.trim() || isRecording || isProcessing}
              data-testid="send-button"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>

          {/* Recording status bar */}
          {isRecording && (
            <div className="flex items-center justify-center gap-2 mt-3 animate-fade-up">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[12px] text-red-400/80 font-medium tracking-wide">Recording… tap to stop</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
