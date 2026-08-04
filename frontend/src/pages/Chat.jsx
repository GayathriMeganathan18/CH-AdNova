import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, RotateCw, Send } from "lucide-react";
import { api } from "../api/client.js";
import AnomalyContextCard from "../components/chat/AnomalyContextCard.jsx";
import InvestigationSuggestions from "../components/chat/InvestigationSuggestions.jsx";
import ChatMessageBubble from "../components/chat/ChatMessageBubble.jsx";


function buildKickoffText(anomaly) {
  const metricLabel = anomaly.metric.replace(/_/g, " ");
  const pct = anomaly.baseline?.deviation_pct ?? anomaly.score;
  const changeLine =
    typeof pct === "number" ? `Observed change: ${pct > 0 ? "+" : ""}${pct.toFixed(1)}%` : "Observed change: n/a";
  return [
    "Investigate the following anomaly and determine the most likely root cause.",
    "",
    `Metric: ${metricLabel}`,
    changeLine,
    `Date: ${anomaly.target_date}`,
    `Severity: ${anomaly.severity || "unknown"}`,
    "",
    "Analyze related metrics and identify what changed around the anomaly. Check factors such "
      + "as requests, fills, impressions, clicks, fill rate, CTR, eCPM or other relevant metrics "
      + "available in the system.",
    "",
    "Explain the likely root cause using evidence from the available data.",
  ].join("\n");
}

export default function Chat() {
  const location = useLocation();
  const navigate = useNavigate();

  const anomaly = location.state?.mode === "anomaly-investigation" ? location.state.anomaly : null;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [lastFailedMessages, setLastFailedMessages] = useState(null);

  const handledAnomalyId = useRef(null);
  const bottomRef = useRef(null);

  const sendConversation = useCallback(
    async (nextMessages) => {
      setSending(true);
      setError(null);
      try {
        const res = await api.chat({ messages: nextMessages, anomaly });
        setMessages([...nextMessages, { role: "assistant", content: res.reply }]);
        setLastFailedMessages(null);
      } catch (e) {
        setError(e.response?.data?.detail || e.message || "Failed to reach the AI assistant.");
        setLastFailedMessages(nextMessages);
      } finally {
        setSending(false);
      }
    },
    [anomaly]
  );

  useEffect(() => {
    if (!anomaly || handledAnomalyId.current === anomaly.id) return;
    handledAnomalyId.current = anomaly.id;
    const kickoff = { role: "user", content: buildKickoffText(anomaly) };
    setMessages([kickoff]);
    setError(null);
    sendConversation([kickoff]);
  }, [anomaly?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  const send = (text) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    const next = [...messages, { role: "user", content: trimmed }];
    setMessages(next);
    setInput("");
    sendConversation(next);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    send(input);
  };

  const retry = () => {
    if (lastFailedMessages) sendConversation(lastFailedMessages);
  };

  const showSuggestions = !!anomaly && messages.length <= 2 && !sending && !error;

  return (
    <div className="flex flex-col gap-4 max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">AI Chat</h2>
          <p className="text-xs text-ink3">
            {anomaly ? "Investigating an anomaly with AI assistance." : "Ask about your ad metrics."}
          </p>
        </div>
        {anomaly && (
          <button
            type="button"
            onClick={() => navigate("/alerts")}
            className="inline-flex items-center gap-1.5 text-xs text-ink3 hover:text-ink transition-colors duration-150 shrink-0"
          >
            <ArrowLeft size={14} />
            Back to Anomalies
          </button>
        )}
      </div>

      {anomaly && <AnomalyContextCard anomaly={anomaly} />}

      <div className="bg-panel2 shadow-card rounded-xl themed-transition flex flex-col min-h-[420px] max-h-[65vh]">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && !sending && (
            <div className="h-full flex items-center justify-center text-center text-sm text-ink3 py-10">
              Ask a question about revenue, fill rate, CTR, eCPM or any anomaly you're investigating.
            </div>
          )}

          {messages.map((m, i) => (
            <ChatMessageBubble key={i} role={m.role} content={m.content} />
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-panel2 shadow-card rounded-xl px-3.5 py-2.5 text-sm text-ink3 flex items-center gap-2 themed-transition">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                {anomaly && messages.length <= 1 ? "Investigating anomaly…" : "Thinking…"}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-bad/10 border border-bad/30 rounded-xl p-3 flex items-center justify-between gap-3 text-xs text-bad themed-transition">
              <span>{error}</span>
              <button
                type="button"
                onClick={retry}
                className="inline-flex items-center gap-1 font-medium bg-bad/15 px-2 py-1 rounded-md hover:bg-bad/25 transition-colors duration-150 shrink-0"
              >
                <RotateCw size={12} />
                Retry
              </button>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {showSuggestions && (
          <div className="px-4 pb-2">
            <InvestigationSuggestions onSelect={send} disabled={sending} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="border-t border-line p-3 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={anomaly ? "Ask a follow-up question…" : "Ask about your ad metrics…"}
            className="flex-1 bg-surface border border-line rounded-md px-3 py-2 text-sm text-ink placeholder:text-ink3 focus:outline-none focus:border-accent transition-colors duration-150"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="inline-flex items-center gap-1.5 bg-accent text-black font-medium text-sm px-3 py-2 rounded-md hover:bg-accent/80 disabled:opacity-50 transition-colors duration-150 shrink-0"
          >
            <Send size={14} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
