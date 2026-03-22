import { useRef, useEffect } from "react";
import { Search } from "lucide-react";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
}

export default function SearchInput({ value, onChange, onKeyDown }: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
      <Search className="w-5 h-5 text-text-dim shrink-0" />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Search resources..."
        className="flex-1 bg-transparent text-text placeholder:text-text-dim outline-none text-sm"
        spellCheck={false}
        autoComplete="off"
      />
      <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono text-text-dim bg-surface-hover rounded border border-border">
        ESC
      </kbd>
    </div>
  );
}
