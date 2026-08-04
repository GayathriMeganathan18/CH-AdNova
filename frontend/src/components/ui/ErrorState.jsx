import { AlertTriangle, RotateCw } from "lucide-react";

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="bg-bad/10 border border-bad/30 rounded-xl p-6 flex flex-col items-center text-center gap-2 themed-transition">
      <AlertTriangle size={22} className="text-bad" />
      <p className="text-sm text-bad">{message || "Something went wrong."}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-1.5 text-xs font-medium bg-bad/15 text-bad px-3 py-1.5 rounded-md hover:bg-bad/25 transition-colors duration-150"
        >
          <RotateCw size={12} />
          Retry
        </button>
      )}
    </div>
  );
}
