function formatInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-ink">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

function AssistantContent({ content }) {
  const lines = content.split("\n");
  const blocks = [];
  let bulletBuffer = [];

  const flushBullets = (key) => {
    if (bulletBuffer.length) {
      blocks.push(
        <ul key={`ul-${key}`} className="my-1 space-y-0.5">
          {bulletBuffer.map((line, i) => (
            <li key={i} className="ml-4 list-disc text-sm text-ink2">
              {formatInline(line.replace(/^[-•]\s+/, ""))}
            </li>
          ))}
        </ul>
      );
      bulletBuffer = [];
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (/^[-•]\s+/.test(trimmed)) {
      bulletBuffer.push(trimmed);
      return;
    }
    flushBullets(i);

    const headingMatch = /^(#{1,3})\s+(.*)$/.exec(trimmed);
    if (headingMatch) {
      const level = headingMatch[1].length;
      blocks.push(
        <p key={i} className={`font-semibold text-ink ${level === 1 ? "text-sm mt-1" : "text-sm mt-0.5"}`}>
          {formatInline(headingMatch[2])}
        </p>
      );
      return;
    }

    if (/^-{3,}$/.test(trimmed)) {
      blocks.push(<hr key={i} className="my-1.5 border-line/60" />);
      return;
    }

    if (!trimmed) {
      blocks.push(<div key={i} className="h-1.5" />);
    } else {
      blocks.push(
        <p key={i} className="text-sm leading-relaxed text-ink2">
          {formatInline(trimmed)}
        </p>
      );
    }
  });
  flushBullets("end");

  return <div>{blocks}</div>;
}

export default function ChatMessageBubble({ role, content }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-3.5 py-2.5 themed-transition ${
          isUser ? "bg-accent/20" : "bg-panel2 shadow-card"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm text-ink">{content}</p>
        ) : (
          <AssistantContent content={content} />
        )}
      </div>
    </div>
  );
}
