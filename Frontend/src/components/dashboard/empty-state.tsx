import { Link } from "@tanstack/react-router";
import { Upload, Sparkles, FileText, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title?: string;
  description?: string;
  actionText?: string;
  actionHref?: string;
  onAction?: () => void;
  secondaryActionText?: string;
  secondaryActionHref?: string;
  className?: string;
}

export function EmptyState({
  icon: Icon = FileText,
  title = "No research paper selected",
  description = "Select or upload a research paper to begin this analysis stage.",
  actionText = "Upload Research Paper",
  actionHref = "/dashboard/upload",
  onAction,
  secondaryActionText,
  secondaryActionHref,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-2xl border border-dashed border-border/70 bg-gradient-to-b from-secondary/15 to-transparent p-12 text-center backdrop-blur-sm ${className}`}
    >
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-primary shadow-inner">
        <Icon className="h-7 w-7" />
      </div>

      <h3 className="mt-4 text-base font-semibold text-foreground tracking-tight">
        {title}
      </h3>
      <p className="mt-1.5 mx-auto max-w-sm text-xs text-muted-foreground leading-relaxed">
        {description}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {actionHref ? (
          <Link to={actionHref}>
            <Button variant="hero" size="sm" className="gap-2 text-xs h-9">
              <Upload className="h-3.5 w-3.5" />
              {actionText}
            </Button>
          </Link>
        ) : onAction ? (
          <Button
            variant="hero"
            size="sm"
            onClick={onAction}
            className="gap-2 text-xs h-9"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {actionText}
          </Button>
        ) : null}

        {secondaryActionHref && secondaryActionText && (
          <Link to={secondaryActionHref}>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-xs h-9 border-border/60 hover:bg-secondary/60"
            >
              <span>{secondaryActionText}</span>
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
