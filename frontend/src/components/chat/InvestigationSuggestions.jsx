const DEFAULT_SUGGESTIONS = [
  "Find root cause",
  "Compare with previous period",
  "Show affected publishers",
  "Check other regions",
];


export default function InvestigationSuggestions({ suggestions = DEFAULT_SUGGESTIONS, onSelect, disabled }) {
  return (
    <div className="flex flex-wrap gap-2">
      {suggestions.map((s) => (
        <button
          key={s}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s)}
          className="text-xs bg-accent/10 text-accent px-3 py-1.5 rounded-full hover:bg-accent/20 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {s}
        </button>
      ))}
    </div>
  );
}

export { DEFAULT_SUGGESTIONS };
