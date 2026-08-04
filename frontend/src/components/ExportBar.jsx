import { api } from "../api/client.js";

export default function ExportBar({ investigationId }) {
  return (
    <div className="export-bar flex items-center gap-2 justify-end">
      <a
        href={api.exportUrl(investigationId, "markdown")}
        className="text-xs bg-ink/5 text-ink2 px-3 py-1.5 rounded-md hover:bg-ink/10"
      >
        Download Markdown
      </a>
      <a
        href={api.exportUrl(investigationId, "json")}
        className="text-xs bg-ink/5 text-ink2 px-3 py-1.5 rounded-md hover:bg-ink/10"
      >
        Download JSON
      </a>
      <button
        onClick={() => window.print()}
        className="text-xs bg-accent/20 text-accent px-3 py-1.5 rounded-md hover:bg-accent/30"
      >
        Print / Save as PDF
      </button>
    </div>
  );
}
