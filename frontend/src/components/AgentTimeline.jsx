import { useEffect, useRef, useState } from "react";

export default function AgentTimeline({ agentLog = [] }) {
  const [step, setStep] = useState(agentLog.length); 
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (playing) {
      timerRef.current = setInterval(() => {
        setStep((s) => {
          if (s >= agentLog.length) {
            setPlaying(false);
            return s;
          }
          return s + 1;
        });
      }, 700);
    }
    return () => clearInterval(timerRef.current);
  }, [playing, agentLog.length]);

  const replay = () => {
    setStep(0);
    setPlaying(true);
  };

  const visible = agentLog.slice(0, step);

  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-ink2">Investigation Replay</h3>
        <div className="flex gap-2">
          <button
            onClick={replay}
            className="text-xs bg-accent/20 text-accent px-3 py-1 rounded-md hover:bg-accent/30"
          >
            ▶ Replay
          </button>
          <button
            onClick={() => setStep(agentLog.length)}
            className="text-xs bg-ink/5 text-ink2 px-3 py-1 rounded-md hover:bg-ink/10"
          >
            Show all
          </button>
        </div>
      </div>

      <ol className="relative border-l border-line ml-2 space-y-4">
        {visible.map((entry, i) => (
          <li key={i} className="ml-4">
            <span className="absolute -left-[5px] w-2.5 h-2.5 rounded-full bg-accent" />
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-ink">{entry.agent}</span>
              <span className="text-xs text-ink3">{entry.duration_ms.toFixed(2)} ms</span>
            </div>
            <p className="text-xs text-ink3 mt-0.5">{entry.reasoning}</p>
            {entry.confidence !== null && entry.confidence !== undefined && (
              <span className="text-xs text-ink3">confidence: {(entry.confidence * 100).toFixed(0)}%</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
