/**
 * ChatAgent — interfaz conversacional del agente sobre la sesión.
 * El docente puede preguntar cualquier cosa sobre su clase específica.
 */
import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { apiBase } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  sessionId: string;
}

export default function ChatAgent({ sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hola 👋 Soy tu coach de esta clase. Puedes preguntarme sobre cualquier aspecto de tu sesión: scores, momentos específicos, citas del transcript o sugerencias concretas.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    setError(null);

    // Historial para el backend (excluye el mensaje inicial del sistema)
    const history = newMessages
      .slice(1)
      .slice(-10) // últimos 10 turnos para no exceder tokens
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await fetch(`${apiBase}/sessions/${sessionId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
        throw new Error(err.detail || `Error ${res.status}`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error de conexión";
      setError(msg);
      setMessages((prev) => prev.slice(0, -1)); // quita el mensaje del usuario si falla
      setInput(text); // restaura el input
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex flex-col h-[520px] rounded-2xl border border-line bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-line bg-paper">
        <Bot className="h-5 w-5 text-evidence" />
        <span className="font-medium text-ink text-sm">
          Coach IA — esta clase
        </span>
        <span className="ml-auto text-xs text-inkSoft">
          Solo responde sobre esta sesión
        </span>
      </div>

      {/* Messages */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div
              className={`flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center ${
                msg.role === "user"
                  ? "bg-ink text-white"
                  : "bg-evidence/10 text-evidence"
              }`}
            >
              {msg.role === "user" ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </div>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-ink text-white rounded-tr-sm"
                  : "bg-paper text-ink rounded-tl-sm"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="h-7 w-7 rounded-full bg-evidence/10 text-evidence flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-paper rounded-2xl rounded-tl-sm px-4 py-2.5">
              <Loader2 className="h-4 w-4 animate-spin text-inkSoft" />
            </div>
          </div>
        )}

        {error && (
          <p className="text-xs text-red-500 text-center">{error}</p>
        )}

        <div />
      </div>

      {/* Input */}
      <div className="border-t border-line px-3 py-3 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Pregunta sobre tu clase… (Enter para enviar)"
          rows={1}
          className="flex-1 resize-none rounded-xl border border-line bg-paper px-3 py-2 text-sm text-ink placeholder:text-inkSoft focus:outline-none focus:ring-2 focus:ring-evidence/30"
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="flex-shrink-0 h-9 w-9 rounded-xl bg-evidence text-white flex items-center justify-center disabled:opacity-40 hover:bg-evidence/90 transition-colors"
          aria-label="Enviar"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
