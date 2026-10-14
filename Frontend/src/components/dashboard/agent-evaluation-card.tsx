import React, { useState } from "react";
import { ShieldCheck, Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  evaluateAgentOutput,
  EvaluationResult,
} from "@/lib/api";
import { toast } from "sonner";

interface AgentEvaluationCardProps {
  agentName: string;
  agentTitle?: string;
  outputText: string;
  paperName?: string;
  context?: string;
  query?: string;
  papers?: any[];
  isWorkspace?: boolean;
  className?: string;
}

const CANONICAL_AGENT_NAMES: Record<string, string> = {
  summary: "Summary Agent",
  summarization: "Summary Agent",
  gaps: "Research Gap Agent",
  gap: "Research Gap Agent",
  research_gap: "Research Gap Agent",
  datasets: "Dataset Recommendation Agent",
  dataset: "Dataset Recommendation Agent",
  dataset_recommendation: "Dataset Recommendation Agent",
  experiments: "Experiment Recommendation Agent",
  experiment: "Experiment Recommendation Agent",
  experiment_recommendation: "Experiment Recommendation Agent",
  literature: "Literature Survey Agent",
  literature_survey: "Literature Survey Agent",
  retrieval: "Literature Survey Agent",
  novelty: "Novelty Analysis Agent",
  novelty_analysis: "Novelty Analysis Agent",
  comparison: "Paper Comparison Agent",
  paper_comparison: "Paper Comparison Agent",
  comparative_analysis: "Paper Comparison Agent",
  report: "IEEE Report Agent",
  ieee_report: "IEEE Report Agent",
  ppt: "PPT Generator Agent",
  presentation: "PPT Generator Agent",
  chat: "AI Chat / RAG Agent",
  idea: "AI Chat / RAG Agent",
  research_idea: "AI Chat / RAG Agent",
  workspace: "AI Workspace Agent",
  ai_workspace: "AI Workspace Agent",
};

interface CacheEntry {
  result: EvaluationResult;
  outputText: string;
}

export function AgentEvaluationCard({
  agentName,
  agentTitle,
  outputText,
  paperName,
  context,
  query,
  papers,
  isWorkspace = false,
  className = "",
}: AgentEvaluationCardProps) {
  const [loading, setLoading] = useState(false);
  const [evalCache, setEvalCache] = useState<Record<string, CacheEntry>>({});

  const rawKey = agentName ? String(agentName).toLowerCase().trim().replace(/-/g, "_") : "summary";
  const cleanKey = rawKey;
  const displayTitle =
    CANONICAL_AGENT_NAMES[cleanKey] ||
    agentTitle ||
    `${agentName ? agentName.toUpperCase() : "Agent"} Agent`;

  // Retrieve cached evaluation for this specific agent only if outputText matches
  const cachedEntry = evalCache[cleanKey];
  const evaluation =
    cachedEntry && cachedEntry.outputText === outputText ? cachedEntry.result : null;

  const calculateOverallScore = (evalData: EvaluationResult | null): number | null => {
    if (!evalData) return null;
    if (
      typeof evalData.overall_score === "number" &&
      !isNaN(evalData.overall_score) &&
      evalData.overall_score >= 0
    ) {
      return Math.round(evalData.overall_score);
    }
    if (!evalData.metrics || typeof evalData.metrics !== "object") return null;
    const values = Object.values(evalData.metrics).filter(
      (v): v is number => typeof v === "number" && !isNaN(v) && v >= 0
    );
    if (values.length === 0) return null;
    return Math.round(values.reduce((sum, v) => sum + v, 0) / values.length);
  };

  const overallScore = calculateOverallScore(evaluation);

  const handleRunEvaluation = async () => {
    if (!outputText || !outputText.trim()) {
      toast.error("No generated content available to evaluate.");
      return;
    }

    setLoading(true);
    try {
      const res = await evaluateAgentOutput(agentName, {
        output_text: outputText,
        paper_name: paperName,
        context: context,
        query: query,
        papers: papers,
        is_workspace: isWorkspace,
      });

      if (res?.success && res.data) {
        setEvalCache((prev) => ({
          ...prev,
          [cleanKey]: {
            result: res.data,
            outputText: outputText,
          },
        }));
        toast.success(`${displayTitle} evaluation completed.`);
      } else {
        toast.error(res?.message || "Failed to complete evaluation.");
      }
    } catch (err: any) {
      console.error("Evaluation error:", err);
      toast.error(err?.message || "Error running evaluation.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 85) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 70) return "text-blue-600 dark:text-blue-400";
    if (score >= 50) return "text-amber-600 dark:text-amber-400";
    return "text-rose-600 dark:text-rose-400";
  };

  return (
    <div
      className={`rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm px-4 py-3 sm:px-5 sm:py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs mt-4 ${className}`}
    >
      <div className="flex items-center space-x-3 min-w-0">
        <div className="p-2 rounded-lg bg-primary/10 text-primary shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm sm:text-base font-bold text-foreground tracking-tight">
            {displayTitle} —{" "}
            {loading ? (
              <span className="text-muted-foreground font-medium animate-pulse">Evaluating...</span>
            ) : overallScore !== null ? (
              <span>
                Overall Score:{" "}
                <span className={getScoreColorClass(overallScore)}>{overallScore}%</span>
              </span>
            ) : (
              <span className="text-muted-foreground font-medium">
                {evaluation ? "Score Unavailable" : "Not Evaluated"}
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
        {!evaluation ? (
          <Button
            size="sm"
            onClick={handleRunEvaluation}
            disabled={loading}
            className="gap-1.5 shadow-xs text-xs h-8 px-3"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Evaluate Output</span>
              </>
            )}
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunEvaluation}
            disabled={loading}
            className="gap-1.5 shadow-xs text-xs h-8 px-3 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>{loading ? "Evaluating..." : "Re-Evaluate"}</span>
          </Button>
        )}
      </div>
    </div>
  );
}
