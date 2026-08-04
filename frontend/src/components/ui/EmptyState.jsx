import { Inbox } from "lucide-react";

export default function EmptyState({ icon: Icon = Inbox, title = "Nothing here yet", message, action }) {
  return (
    <div className="bg-panel2 shadow-card rounded-xl p-10 flex flex-col items-center text-center gap-2 themed-transition">
      <Icon size={28} className="text-ink3 mb-1" />
      <p className="text-sm font-medium text-ink2">{title}</p>
      {message && <p className="text-xs text-ink3 max-w-sm">{message}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
