import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Analysis Error",
  error = "We were unable to complete this analysis stage. Please check your document format or try again.",
  onRetry,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`rounded-2xl border border-destructive/40 bg-destructive/10 p-6 backdrop-blur-md ${className}`}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="rounded-xl bg-destructive/20 p-2 text-destructive shrink-0 mt-0.5 sm:mt-0">
            <AlertCircle className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-foreground">{title}</h4>
            <p className="text-xs text-destructive/90 mt-0.5 break-words leading-relaxed">
              {error}
            </p>
          </div>
        </div>

        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="shrink-0 gap-1.5 text-xs h-8 border-destructive/30 hover:bg-destructive/20 text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Try Again</span>
          </Button>
        )}
      </div>
    </div>
  );
}
