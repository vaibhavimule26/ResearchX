import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Lightbulb,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
  Check,
  AlertTriangle,
  Compass,
  ArrowRight,
  BookOpen,
  FlaskConical,
  Database,
  Layers,
  FileSpreadsheet,
  Target,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { PaperSelectorCard } from "@/components/dashboard/paper-selector-card";
import { AIProcessingCard } from "@/components/dashboard/ai-processing-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { ErrorState } from "@/components/dashboard/error-state";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/gaps")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [{ title: "Research Gaps Analysis — ResearchX" }],
  }),
  component: ResearchGapsPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

// Cleanly unwrap API response without destroying Markdown formatting
function extractMarkdown(raw: unknown): string {
  if (!raw) return "";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.results?.gaps?.output ||
      obj?.results?.gap_analysis?.output ||
      obj?.results?.summary?.output ||
      obj?.gap_analysis ||
      obj?.output ||
      obj?.data?.answer ||
      obj?.answer ||
      obj?.result ||
      "";

    if (!text && obj?.results && typeof obj.results === "object") {
      const first = Object.values(obj.results)[0] as any;
      if (first?.output) text = first.output;
    }
  } else if (typeof raw === "string") {
    const trimmed = raw.trim();
    if (
      (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
      (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
      try {
        const parsed = JSON.parse(trimmed);
        return extractMarkdown(parsed);
      } catch {
        try {
          const parsed = JSON.parse(trimmed.replace(/'/g, '"'));
          return extractMarkdown(parsed);
        } catch {
          const match = trimmed.match(
            /['"]output['"]\s*:\s*['"]([\s\S]*?)['"]\s*(?:,\s*['"]|\})/
          );
          text = match && match[1] ? match[1] : trimmed;
        }
      }
    } else {
      text = trimmed;
    }
  } else {
    text = String(raw);
  }

  return text
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "")
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .trim();
}

const GAPS_PROCESSING_STAGES = [
  {
    title: "Reading Paper & Extracting Methodological Claims",
    description: "Parsing document structure, assumptions, and scope...",
  },
  {
    title: "Identifying Empirical & Theoretical Limitations",
    description: "Evaluating author-acknowledged constraints and boundary conditions...",
  },
  {
    title: "Analyzing Practical & Architectural Bottlenecks",
    description: "Detecting dataset bias, compute scaling, and missing baselines...",
  },
  {
    title: "Synthesizing High-Impact Future Research Directions",
    description: "Structuring actionable opportunities for follow-up publications...",
  },
];

function ResearchGapsPage() {
  const search = useSearch({ from: "/dashboard/gaps" });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState(search.paper || "");
  const [gaps, setGaps] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);
        setError("");

        const response = await getPapers();
        const uploadedPapers: Paper[] = response?.data?.papers || [];

        setPapers(uploadedPapers);

        if (search.paper) {
          const match = uploadedPapers.find(
            (p) => p.filename.toLowerCase() === search.paper.toLowerCase()
          );
          setSelectedPaper(match ? match.filename : search.paper);
        } else if (uploadedPapers.length > 0 && !selectedPaper) {
          setSelectedPaper(uploadedPapers[0].filename);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load papers"
        );
      } finally {
        setLoadingPapers(false);
      }
    };

    loadPapers();
  }, [search.paper]);

  // Auto-run if paper param exists
  useEffect(() => {
    if (search.paper && !gaps && !loading) {
      findGaps(search.paper);
    }
  }, [search.paper]);

  const findGaps = async (targetPaper?: string) => {
    const paperToRun = targetPaper || selectedPaper;
    if (!paperToRun || loading) return;

    try {
      setLoading(true);
      setError("");
      setGaps("");

      const response = await runAnalysis(paperToRun, "gaps");
      const rawResult =
        (response as any)?.result ??
        (response as any)?.data ??
        response;

      if (!rawResult) {
        throw new Error("No research gaps response received from backend");
      }

      setGaps(extractMarkdown(rawResult));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Research gap analysis failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyGaps = async () => {
    if (!gaps) return;
    try {
      await navigator.clipboard.writeText(gaps);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy research gaps");
    }
  };

  const downloadGaps = () => {
    if (!gaps) return;

    const content = [
      "ResearchX — Research Gaps & Limitations Report",
      "=".repeat(60),
      `Paper: ${selectedPaper}`,
      `Generated: ${new Date().toISOString()}`,
      "=".repeat(60),
      "",
      gaps,
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename || "paper"}-research-gaps.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Research Gaps & Future Directions"
        subtitle={
          selectedPaper
            ? `Deep critical analysis of methodological limitations, empirical bottlenecks, and future research scope for '${selectedPaper}'.`
            : "Select an uploaded research paper to identify unexplored gaps."
        }
        action={
          gaps ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copyGaps}
                disabled={!gaps || loading}
                className="h-8 text-xs gap-1.5 border-border/60 hover:bg-secondary/60"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>Copy Analysis</span>
                  </>
                )}
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={downloadGaps}
                disabled={!gaps || loading}
                className="h-8 text-xs gap-1.5 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export Report</span>
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Target Paper Selector Card */}
      <PaperSelectorCard
        papers={papers}
        selectedPaper={selectedPaper}
        onSelectPaper={(filename) => {
          setSelectedPaper(filename);
          setGaps("");
          setError("");
        }}
        loading={loading}
        loadingPapers={loadingPapers}
        subtitle="The AI Gap Specialist performs rigorous claim auditing on this document."
        actionButton={
          <Button
            variant="hero"
            size="sm"
            onClick={() => findGaps()}
            disabled={loading || loadingPapers || !selectedPaper}
            className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>{loading ? "Analyzing Gaps..." : "Identify Research Gaps"}</span>
          </Button>
        }
      />

      {error && (
        <ErrorState
          title="Gap Analysis Failed"
          error={error}
          onRetry={() => findGaps()}
        />
      )}

      {/* Reusable AI Multi-Stage Processing Experience */}
      {loading && (
        <AIProcessingCard
          agentName="RESEARCH GAP SPECIALIST"
          title={`Evaluating research limitations in ${selectedPaper}`}
          stages={GAPS_PROCESSING_STAGES}
          className="mt-6"
        />
      )}

      {/* Empty State before Running Analysis */}
      {!loading && !gaps && !error && (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mb-3">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Methodological Limitations
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Detect boundary conditions, unproven assumptions, and constraints in the proposed system design.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mb-3">
              <Layers className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Practical Bottlenecks
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Examine compute bottlenecks, missing baseline comparisons, and real-world scalability barriers.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3">
              <Compass className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Future Research Scope
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Extract high-impact research trajectories suitable for thesis projects, novel papers, and extensions.
            </p>
          </div>
        </div>
      )}

      {/* Analysis Results: Two-Column Academic Layout */}
      {gaps && !loading && (
        <div className="grid gap-6 lg:grid-cols-12 items-start">
          {/* Main Content Column (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-2xl border border-border/50 bg-card/80 p-6 sm:p-8 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between border-b border-border/40 pb-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                    <Lightbulb className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">
                      Critical Gap Analysis &amp; Academic Findings
                    </h3>
                    <p className="text-xs text-muted-foreground truncate max-w-md">
                      {selectedPaper}
                    </p>
                  </div>
                </div>

                <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-primary/15 px-3 py-1 text-[11px] font-semibold text-primary border border-primary/25">
                  <Target className="h-3 w-3" />
                  Actionable Scope
                </span>
              </div>

              {/* Enhanced Markdown Report with Visual Classification Badges */}
              <div className="text-sm leading-relaxed text-foreground/90 space-y-4">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => (
                      <h1
                        className="text-xl font-bold tracking-tight text-foreground border-b border-border/40 pb-2 mt-6 mb-3"
                        {...props}
                      />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2
                        className="text-lg font-bold tracking-tight text-foreground border-b border-border/30 pb-1.5 mt-6 mb-2"
                        {...props}
                      />
                    ),
                    h3: ({ node, children, ...props }) => {
                      const text = String(children);
                      const isLimitation = /limitation|constraint|weakness/i.test(text);
                      const isBottleneck = /bottleneck|barrier|challenge/i.test(text);
                      const isFuture = /future|direction|scope|extension/i.test(text);
                      const isOpportunity = /opportunity|impact|potential/i.test(text);

                      return (
                        <div className="mt-6 mb-2 pt-2 border-t border-border/20">
                          <div className="flex items-center gap-2 mb-1">
                            {isLimitation ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30">
                                <AlertTriangle className="h-3 w-3" /> Limitation
                              </span>
                            ) : isBottleneck ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                                <Layers className="h-3 w-3" /> Bottleneck
                              </span>
                            ) : isFuture ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/30">
                                <Compass className="h-3 w-3" /> Future Direction
                              </span>
                            ) : isOpportunity ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                                <Sparkles className="h-3 w-3" /> Opportunity
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-primary/15 text-primary border border-primary/30">
                                <Lightbulb className="h-3 w-3" /> Research Gap
                              </span>
                            )}
                          </div>
                          <h3
                            className="text-sm font-bold text-foreground"
                            {...props}
                          >
                            {children}
                          </h3>
                        </div>
                      );
                    },
                    h4: ({ node, ...props }) => (
                      <h4
                        className="text-xs font-semibold text-foreground/90 uppercase tracking-wide mt-3 mb-1"
                        {...props}
                      />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul
                        className="list-disc pl-5 space-y-1.5 text-xs text-foreground/80 my-2"
                        {...props}
                      />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol
                        className="list-decimal pl-5 space-y-1.5 text-xs text-foreground/80 my-2"
                        {...props}
                      />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="leading-relaxed" {...props} />
                    ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote
                        className="border-l-2 border-primary/60 bg-secondary/30 py-2 px-3 rounded-r-xl text-xs italic text-muted-foreground my-3"
                        {...props}
                      />
                    ),
                    table: ({ node, ...props }) => (
                      <div className="overflow-x-auto my-4 rounded-xl border border-border/50">
                        <table
                          className="w-full text-xs text-left border-collapse"
                          {...props}
                        />
                      </div>
                    ),
                    th: ({ node, ...props }) => (
                      <th
                        className="border-b border-border/60 bg-secondary/60 px-3 py-2 text-xs font-semibold text-primary"
                        {...props}
                      />
                    ),
                    td: ({ node, ...props }) => (
                      <td
                        className="border-b border-border/30 px-3 py-2 text-xs text-foreground/80"
                        {...props}
                      />
                    ),
                  }}
                >
                  {gaps}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Research Opportunity Radar & Workflow (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Visual Research Opportunity Card */}
            <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 via-card/80 to-background p-5 backdrop-blur-md shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <div className="grid h-7 w-7 place-items-center rounded-lg bg-emerald-500/20 text-emerald-400">
                  <Sparkles className="h-4 w-4" />
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                  Research Opportunity Radar
                </h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                The gaps identified in this paper reveal clear niches for high-yield investigations:
              </p>
              <ul className="space-y-1.5 text-xs text-foreground/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Cross-domain architectural generalization</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Ablation studies on unverified sub-modules</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Evaluating alternative benchmark datasets</span>
                </li>
              </ul>
            </div>

            {/* Next Research Steps */}
            <div className="rounded-2xl border border-border/50 bg-secondary/20 p-5 backdrop-blur-md shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Carry forward these gap insights into dedicated workflow stages:
              </p>

              <div className="space-y-2 pt-1">
                <Link
                  to="/dashboard/datasets"
                  search={{ paper: selectedPaper }}
                  className="block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                  >
                    <span className="flex items-center gap-1.5">
                      <Database className="h-3.5 w-3.5 text-primary" />
                      Find Benchmark Datasets
                    </span>
                    <ArrowRight className="h-3 w-3 opacity-50" />
                  </Button>
                </Link>

                <Link
                  to="/dashboard/experiments"
                  search={{ paper: selectedPaper }}
                  className="block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                  >
                    <span className="flex items-center gap-1.5">
                      <FlaskConical className="h-3.5 w-3.5 text-purple-400" />
                      Design Experiments
                    </span>
                    <ArrowRight className="h-3 w-3 opacity-50" />
                  </Button>
                </Link>

                <Link
                  to="/dashboard/report"
                  search={{ paper: selectedPaper }}
                  className="block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                  >
                    <span className="flex items-center gap-1.5">
                      <FileSpreadsheet className="h-3.5 w-3.5 text-blue-400" />
                      Draft IEEE Report
                    </span>
                    <ArrowRight className="h-3 w-3 opacity-50" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResearchGapsPage;