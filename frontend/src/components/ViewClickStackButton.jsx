import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { api } from "../api/client.js";

const LINK_CLASS = "inline-flex items-center gap-1.5 text-xs text-accent hover:underline";
const LINK_DISABLED_CLASS = "inline-flex items-center gap-1.5 text-xs text-ink3 opacity-50 cursor-not-allowed";
const BUTTON_CLASS =
  "inline-flex items-center gap-1.5 text-xs font-medium bg-accent/20 text-accent px-2.5 py-1.5 rounded-md hover:bg-accent/30 transition-colors duration-150";
const BUTTON_DISABLED_CLASS =
  "inline-flex items-center gap-1.5 text-xs font-medium bg-ink/5 text-ink3 px-2.5 py-1.5 rounded-md opacity-50 cursor-not-allowed";

export default function ViewClickStackButton({ url, variant = "button", className = "" }) {
  const [fetchedUrl, setFetchedUrl] = useState(undefined);

  useEffect(() => {
    if (url !== undefined) return; 
    api
      .systemHealth()
      .then((h) => setFetchedUrl(h.components?.clickstack?.url || null))
      .catch(() => setFetchedUrl(null));
  }, [url]);

  const resolvedUrl = url !== undefined ? url : fetchedUrl;

  if (resolvedUrl === undefined) return null; 

  if (!resolvedUrl) {
    return (
      <span
        title="ClickStack URL is not configured"
        className={`${variant === "link" ? LINK_DISABLED_CLASS : BUTTON_DISABLED_CLASS} ${className}`}
      >
        <ExternalLink size={12} />
        View ClickStack
      </span>
    );
  }

  return (
    <a
      href={resolvedUrl}
      target="_blank"
      rel="noreferrer"
      className={`${variant === "link" ? LINK_CLASS : BUTTON_CLASS} ${className}`}
    >
      <ExternalLink size={12} />
      View ClickStack
    </a>
  );
}
