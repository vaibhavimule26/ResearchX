import { useEffect, useState } from "react";
import { Sparkles, CheckCircle2, Loader2, Circle } from "lucide-react";

export interface ProcessingStage {
  title: string;
  description?: string;
}

interface AIProcessingCardProps {
  title?: string;
  subtitle?: string;
  agentName?: string;
  stages: ProcessingStage[];
  currentStageIndex?: number;
  stageIntervalMs?: number;
  className?: string;
}

export function AIProcessingCard({
  title = "Analyzing your research paper",
  subtitle,
  agentName = "AI RESEARCH ENGINE",
  stages,
  currentStageIndex: controlledIndex,
  stageIntervalMs = 2800,
  className = "",
}: AIProcessingCardProps) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    if (controlledIndex !== undefined) {
      setActiveStage(controlledIndex);
      return;
    }

    const interval = setInterval(() => {
      setActiveStage((prev) => {
        if (prev < stages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, stageIntervalMs);

    return () => clearInterval(interval);
  }, [controlledIndex, stages.length, stageIntervalMs]);

  const progressPercent = Math.min(
    Math.round(((activeStage + 0.6) / stages.length) * 100),
    95
  );

  return (
    <div
      className={`rounded-2xl border border-primary/25 bg-gradient-to-b from-primary/10 via-card/80 to-background/95 p-8 shadow-xl backdrop-blur-xl ${className}`}
    >
      <div className="mx-auto max-w-xl text-center">
        {/* Glowing Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/15 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-primary shadow-sm">
          <Sparkles className="h-3.5 w-3.5 animate-pulse text-primary" />
          <span>{agentName}</span>
        </div>

        {/* Title */}
        <h3 className="mt-4 text-xl font-bold tracking-tight text-foreground sm:text-2xl">
          {title}
        </h3>
        <p className="mt-1.5 text-xs text-muted-foreground">
          {subtitle || "Deep academic synthesis in progress. Please do not close or refresh this tab."}
        </p>

        {/* Stages Timeline */}
        <div className="mt-8 space-y-3.5 text-left rounded-xl border border-border/40 bg-secondary/30 p-5">
          {stages.map((stage, idx) => {
            const isDone = idx < activeStage;
            const isCurrent = idx === activeStage;

            return (
              <div
                key={idx}
                className={`flex items-start gap-3.5 transition-all duration-300 ${
                  isCurrent
                    ? "opacity-100 scale-[1.01]"
                    : isDone
                    ? "opacity-80"
                    : "opacity-40"
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground/40" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-xs font-medium ${
                        isCurrent
                          ? "text-primary font-semibold"
                          : isDone
                          ? "text-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      {stage.title}
                    </span>
                    {isCurrent && (
                      <span className="text-[10px] font-mono font-medium text-primary uppercase tracking-wider animate-pulse">
                        In progress
                      </span>
                    )}
                    {isDone && (
                      <span className="text-[10px] font-mono text-emerald-400/80 uppercase tracking-wider">
                        Complete
                      </span>
                    )}
                  </div>
                  {stage.description && (
                    <p className="text-[11px] text-muted-foreground/80 mt-0.5">
                      {stage.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground mb-1.5">
            <span>Synthesis pipeline</span>
            <span className="text-primary font-medium">{progressPercent}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary/60">
            <div
              className="h-full rounded-full gradient-primary-bg transition-all duration-700 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Shimmer Academic Skeleton Preview */}
        <div className="mt-6 space-y-2.5 rounded-xl border border-border/30 bg-background/40 p-4">
          <div className="h-3 w-2/5 rounded bg-muted/40 animate-pulse" />
          <div className="h-2.5 w-full rounded bg-muted/25 animate-pulse" />
          <div className="h-2.5 w-4/5 rounded bg-muted/25 animate-pulse" />
          <div className="h-2.5 w-3/4 rounded bg-muted/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
