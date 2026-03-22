import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="bg-state-error/10 border border-state-error/30 rounded-lg px-4 py-3 flex items-center gap-3">
      <AlertTriangle className="w-5 h-5 text-state-error shrink-0" />
      <span className="text-sm text-text flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 text-sm text-accent hover:text-accent-hover transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      )}
    </div>
  );
}
