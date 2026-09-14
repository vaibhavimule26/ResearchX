import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  FlaskConical,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
  Check,
  Target,
  ArrowRight,
  Database,
  FileSpreadsheet,
  Layers,
  BarChart2,
  ListOrdered,
  ChevronDown,
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

export const Route = createFileRoute("/dashboard/experiments")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [{ title: "Experiment Recommendations — ResearchX" }],
  }),
  component: ExperimentsPage,
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
      obj?.results?.experiments?.output ||
      obj?.results?.experiment?.output ||
      obj?.results?.summary?.output ||
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

const EXPERIMENT_STAGES = [
  {
    title: "Understanding Research Problem & Baseline Claims",
    description: "Analyzing core hypothesis, variables, and experimental context...",
  },
  {
    title: "Selecting Evaluation Strategy & Metrics",
    description: "Determining statistical significance tests, benchmarks, and loss targets...",
  },
  {
    title: "Designing Experimental Protocol & Architecture",
    description: "Structuring ablation controls, hyperparameter spaces, and dataset splits...",
  },
  {
    title: "Preparing Validation Setup & Expected Outcomes",
    description: "Compiling execution steps and empirical validation matrices...",
  },
];

function ExperimentsPage() {
  const search = useSearch({ from: "/dashboard/experiments" });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState(search.paper || "");
  const [protocol, setProtocol] = useState("");
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
    if (search.paper && !protocol && !loading) {
      generateExperiments(search.paper);
    }
  }, [search.paper]);

  const generateExperiments = async (targetPaper?: string) => {
    const paperToRun = targetPaper || selectedPaper;
    if (!paperToRun || loading) return;

    try {
      setLoading(true);
      setError("");
      setProtocol("");

      const response = await runAnalysis(paperToRun, "experiments");
      const rawResult =
        (response as any)?.result ??
        (response as any)?.data ??
        response;

      if (!rawResult) {
        throw new Error("No experiment protocol received from backend");
      }

      setProtocol(extractMarkdown(rawResult));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Experiment generation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyProtocol = async () => {
    if (!protocol) return;
    try {
      await navigator.clipboard.writeText(protocol);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy experimental protocol");
    }
  };

  const downloadProtocol = () => {
    if (!protocol) return;

    const content = [
      "ResearchX — Experimental Replication & Validation Protocol",
      "=".repeat(60),
      `Paper: ${selectedPaper}`,
      `Generated: ${new Date().toISOString()}`,
      "=".repeat(60),
      "",
      protocol,
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename || "paper"}-experimental-protocol.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Experimental Protocol & Recommendations"
        subtitle={
          selectedPaper
            ? `Structured experimental design, ablation studies, baseline setups, and validation matrices for '${selectedPaper}'.`
            : "Select an uploaded research paper to generate an experimental protocol."
        }
        action={
          protocol ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copyProtocol}
                disabled={!protocol || loading}
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
                    <span>Copy Protocol</span>
                  </>
                )}
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={downloadProtocol}
                disabled={!protocol || loading}
                className="h-8 text-xs gap-1.5 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export Protocol</span>
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Target Paper Selector */}
      <PaperSelectorCard
        papers={papers}
        selectedPaper={selectedPaper}
        onSelectPaper={(filename) => {
          setSelectedPaper(filename);
          setProtocol("");
          setError("");
        }}
        loading={loading}
        loadingPapers={loadingPapers}
        subtitle="Formulates reproducible scientific hypotheses and evaluation pipelines from this paper."
        actionButton={
          <Button
            variant="hero"
            size="sm"
            onClick={() => generateExperiments()}
            disabled={loading || loadingPapers || !selectedPaper}
            className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>{loading ? "Designing..." : "Design Experiments"}</span>
          </Button>
        }
      />

      {error && (
        <ErrorState
          title="Experiment Design Failed"
          error={error}
          onRetry={() => generateExperiments()}
        />
      )}

      {/* Multi-Stage AI Workflow */}
      {loading && (
        <AIProcessingCard
          agentName="EXPERIMENT PROTOCOL ENGINE"
          title={`Formulating experimental protocol for ${selectedPaper}`}
          stages={EXPERIMENT_STAGES}
          className="mt-6"
        />
      )}

      {/* Empty State before Running */}
      {!loading && !protocol && !error && (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 mb-3">
              <FlaskConical className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Ablation &amp; Control Setup
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Define isolated test conditions to isolate variables, measure module contributions, and eliminate confounding factors.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3">
              <BarChart2 className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Evaluation Metrics
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Select standardized scholarly metrics (F1, BLEU, mAP, latency, throughput) tailored to your experimental hypothesis.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
              <ListOrdered className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Step-by-Step Execution Plan
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Numbered sequence of actionable implementation tasks from environment configuration to baseline comparisons.
            </p>
          </div>
        </div>
      )}

      {/* Structured Results */}
      {protocol && !loading && (
        <div className="grid gap-6 lg:grid-cols-12 items-start">
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-2xl border border-border/50 bg-card/80 p-6 sm:p-8 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between border-b border-border/40 pb-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                    <FlaskConical className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">
                      Structured Experimental Protocol
                    </h3>
                    <p className="text-xs text-muted-foreground truncate max-w-md">
                      {selectedPaper}
                    </p>
                  </div>
                </div>

                <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-purple-500/15 px-3 py-1 text-[11px] font-semibold text-purple-400 border border-purple-500/25">
                  <Target className="h-3 w-3" />
                  Peer-Review Ready
                </span>
              </div>

              {/* Enhanced Markdown Report with Visual Experiment Cards */}
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
                      const isExperimentHeading = /experiment\s*\d+|protocol\s*\d+|setup\s*\d+/i.test(text);

                      return (
                        <div className="mt-6 mb-2 pt-3 border-t border-border/20">
                          {isExperimentHeading && (
                            <div className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/30 mb-1.5">
                              <FlaskConical className="h-3 w-3" /> Structured Experiment
                            </div>
                          )}
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
                        className="border-l-2 border-purple-500/60 bg-secondary/30 py-2 px-3 rounded-r-xl text-xs italic text-muted-foreground my-3"
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
                        className="border-b border-border/60 bg-secondary/60 px-3 py-2 text-xs font-semibold text-purple-400"
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
                  {protocol}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Execution Checklist & Navigation */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 via-card/80 to-background p-5 backdrop-blur-md shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <div className="grid h-7 w-7 place-items-center rounded-lg bg-purple-500/20 text-purple-400">
                  <Target className="h-4 w-4" />
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400">
                  Validation Best Practices
                </h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Ensure rigor during experimental replication:
              </p>
              <ul className="space-y-1.5 text-xs text-foreground/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Fix random seeds across all training runs</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Report 5-fold cross-validation standard error</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Log GPU compute footprint &amp; inference latency</span>
                </li>
              </ul>
            </div>

            <div className="rounded-2xl border border-border/50 bg-secondary/20 p-5 backdrop-blur-md shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Transition experimental results into academic publication:
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
                      Cross-Check Datasets
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
                      Include in IEEE Report
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

export default ExperimentsPage;