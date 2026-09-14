import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Database,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
  FileText,
  Search,
  Layers,
  ArrowRight,
  ShieldCheck,
  Check,
  FlaskConical,
  BookOpen,
  FileSpreadsheet,
  ExternalLink,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { PaperSelectorCard } from "@/components/dashboard/paper-selector-card";
import { AIProcessingCard } from "@/components/dashboard/ai-processing-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { ErrorState } from "@/components/dashboard/error-state";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/datasets")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [
      {
        title: "Dataset Intelligence & Benchmarks — ResearchX",
      },
    ],
  }),
  component: DatasetsPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

type InputMode = "paper" | "query";

const PRESET_QUERIES = [
  "Medical Chest X-Ray Multi-label Pathology Classification",
  "Multi-Hop Question Answering & RAG Retrieval Benchmarks",
  "Multimodal Vision-Language Reasoning & Visual QA",
  "Autonomous Driving Multi-Sensor 3D Object Detection",
  "Financial Fraud & Tabular Transaction Anomaly Detection",
];

const DATASET_STAGES = [
  {
    title: "Analyzing Research Domain & Modality",
    description: "Extracting problem domain, task formulation, and input-output schemas...",
  },
  {
    title: "Understanding Dataset Requirements & Constraints",
    description: "Verifying size, ground-truth quality, and licensing constraints...",
  },
  {
    title: "Finding Relevant Benchmarks & Baselines",
    description: "Curating high-similarity gold-standard evaluation datasets...",
  },
  {
    title: "Ranking Candidates & Synthesizing Recommendations",
    description: "Structuring technical selection justifications and access links...",
  },
];

// Clean and extract standard markdown content safely
function extractMarkdown(raw: unknown): string {
  if (!raw) return "";

  let content = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    content =
      obj?.results?.datasets?.output ||
      obj?.output ||
      obj?.result ||
      obj?.data?.answer ||
      obj?.answer ||
      JSON.stringify(obj, null, 2);
  } else if (typeof raw === "string") {
    const trimmed = raw.trim();
    try {
      const parsed = JSON.parse(trimmed);
      return extractMarkdown(parsed);
    } catch {
      const outputMatch = trimmed.match(
        /['"]output['"]\s*:\s*['"]([\s\S]*?)['"]\s*(?:,\s*['"]|\})/
      );
      if (outputMatch && outputMatch[1]) {
        content = outputMatch[1]
          .replace(/\\n/g, "\n")
          .replace(/\\"/g, '"')
          .replace(/\\'/g, "'");
      } else {
        content = trimmed;
      }
    }
  } else {
    content = String(raw);
  }

  return content.replace(/\r\n/g, "\n").trim();
}

function DatasetsPage() {
  const search = useSearch({ from: "/dashboard/datasets" });

  const [mode, setMode] = useState<InputMode>("paper");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState(search.paper || "");
  const [customQuery, setCustomQuery] = useState("");
  const [recommendations, setRecommendations] = useState("");

  const [loadingPapers, setLoadingPapers] = useState(true);
  const [loading, setLoading] = useState(false);
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

  const handleRecommend = async () => {
    if (loading) return;

    if (mode === "paper" && !selectedPaper) {
      setError("Please select an uploaded research paper.");
      return;
    }

    if (mode === "query" && !customQuery.trim()) {
      setError("Please enter a research query or topic.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setRecommendations("");

      const response = await runAnalysis(
        mode === "paper" ? selectedPaper : null,
        "datasets",
        mode === "query" ? customQuery.trim() : undefined
      );

      const rawResult =
        (response as any)?.result ??
        (response as any)?.data ??
        response;

      if (!rawResult) {
        throw new Error("No dataset recommendations received from backend");
      }

      setRecommendations(extractMarkdown(rawResult));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Dataset recommendation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyRecommendations = async () => {
    if (!recommendations) return;
    try {
      await navigator.clipboard.writeText(recommendations);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy dataset recommendations");
    }
  };

  const downloadRecommendations = () => {
    if (!recommendations) return;

    const targetTitle =
      mode === "paper"
        ? `Paper: ${selectedPaper}`
        : `Research Query: ${customQuery}`;

    const content = [
      "ResearchX Dataset Intelligence & Benchmark Report",
      "=".repeat(60),
      targetTitle,
      `Generated At: ${new Date().toISOString()}`,
      "=".repeat(60),
      "",
      recommendations,
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeName = (mode === "paper" ? selectedPaper : customQuery)
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_")
      .slice(0, 30);

    anchor.href = url;
    anchor.download = `${safeName || "benchmark"}_dataset_recommendations.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Dataset Intelligence & Benchmarks"
        subtitle={
          mode === "paper"
            ? selectedPaper
              ? `Discover high-similarity gold-standard benchmark datasets for '${selectedPaper}'.`
              : "Select an uploaded research paper to extract task requirements and match benchmarks."
            : "Enter a research query or domain to find authoritative, peer-reviewed benchmark datasets."
        }
        action={
          recommendations ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copyRecommendations}
                disabled={!recommendations || loading}
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
                    <span>Copy Report</span>
                  </>
                )}
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={downloadRecommendations}
                disabled={!recommendations || loading}
                className="h-8 text-xs gap-1.5 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export Report</span>
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Mode Switcher Banner */}
      <div className="flex items-center justify-between flex-wrap gap-3 rounded-2xl border border-border/50 bg-secondary/20 p-2.5 backdrop-blur-md">
        <div className="inline-flex rounded-xl bg-secondary/50 p-1 border border-border/40">
          <button
            type="button"
            onClick={() => {
              setMode("paper");
              setError("");
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === "paper"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Target Paper (PDF)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setMode("query");
              setError("");
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === "query"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Search className="h-3.5 w-3.5" />
            <span>Custom Topic / Query</span>
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground pr-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span className="hidden sm:inline">Authoritative peer-reviewed benchmark datasets</span>
        </div>
      </div>

      {/* Context Card: Paper Mode vs Query Mode */}
      {mode === "paper" ? (
        <PaperSelectorCard
          papers={papers}
          selectedPaper={selectedPaper}
          onSelectPaper={(filename) => {
            setSelectedPaper(filename);
            setRecommendations("");
            setError("");
          }}
          loading={loading}
          loadingPapers={loadingPapers}
          subtitle="Extracts modal constraints, evaluation metrics, and task schemas directly from this paper."
          actionButton={
            <Button
              variant="hero"
              size="sm"
              onClick={handleRecommend}
              disabled={loading || loadingPapers || !selectedPaper}
              className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{loading ? "Matching..." : "Recommend Datasets"}</span>
            </Button>
          }
        />
      ) : (
        <div className="rounded-2xl border border-border/50 bg-gradient-to-r from-secondary/30 via-card/50 to-secondary/20 p-4 shadow-sm backdrop-blur-md space-y-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Enter research topic, architecture, or domain (e.g. Multimodal medical image segmentation)..."
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRecommend();
                }}
                disabled={loading}
                className="w-full h-10 rounded-xl border border-border/60 bg-secondary/40 pl-10 pr-4 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50"
              />
            </div>

            <Button
              variant="hero"
              size="sm"
              onClick={handleRecommend}
              disabled={loading || !customQuery.trim()}
              className="h-10 px-4 text-xs font-semibold gap-2 shadow-sm shrink-0"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{loading ? "Searching..." : "Find Datasets"}</span>
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] text-muted-foreground mr-1">Suggested:</span>
            {PRESET_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setCustomQuery(preset)}
                className="rounded-lg border border-border/40 bg-secondary/30 px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-secondary/70 hover:text-foreground transition-colors"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <ErrorState
          title="Dataset Recommendation Failed"
          error={error}
          onRetry={handleRecommend}
        />
      )}

      {/* Reusable Multi-Stage Processing Experience */}
      {loading && (
        <AIProcessingCard
          agentName="DATASET SPECIALIST"
          title={
            mode === "paper"
              ? `Finding high-similarity benchmarks for ${selectedPaper}`
              : `Matching benchmark datasets for "${customQuery}"`
          }
          stages={DATASET_STAGES}
          className="mt-6"
        />
      )}

      {/* Empty State before Running */}
      {!loading && !recommendations && !error && (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 border border-primary/20 text-primary mb-3">
              <Database className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">High-Similarity Benchmarks</h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Curated peer-reviewed datasets matching your research formulation, domain constraints, and input modality.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 mb-3">
              <Sparkles className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">Selection Rationale</h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Every dataset includes technical justifications explaining why it serves as the authoritative baseline for your paper.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
              <Layers className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">Standardized Benchmark Matrix</h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Standardized comparison tables with licensing integrity, split counts, and direct loading snippets.
            </p>
          </div>
        </div>
      )}

      {/* Dataset Results Layout */}
      {recommendations && !loading && (
        <div className="grid gap-6 lg:grid-cols-12 items-start">
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-2xl border border-border/50 bg-card/80 p-6 sm:p-8 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between border-b border-border/40 pb-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                    <Database className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">
                      Authoritative Benchmark Recommendations
                    </h3>
                    <p className="text-xs text-muted-foreground truncate max-w-md">
                      {mode === "paper" ? selectedPaper : customQuery}
                    </p>
                  </div>
                </div>

                <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-3 py-1 text-[11px] font-semibold text-emerald-400 border border-emerald-500/25">
                  <ShieldCheck className="h-3 w-3" />
                  Gold Standards
                </span>
              </div>

              {/* Formatted Markdown Content */}
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
                    h3: ({ node, ...props }) => (
                      <h3
                        className="text-sm font-bold text-primary mt-5 mb-1.5 flex items-center gap-2"
                        {...props}
                      />
                    ),
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
                    td: ({ node, children, ...props }) => {
                      const text = String(children);
                      const isHighMatch = /(\d{2,3})%/.test(text);

                      return (
                        <td
                          className="border-b border-border/30 px-3 py-2 text-xs text-foreground/80"
                          {...props}
                        >
                          {isHighMatch ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-mono font-semibold text-[11px] border border-emerald-500/25">
                              {children}
                            </span>
                          ) : (
                            children
                          )}
                        </td>
                      );
                    },
                  }}
                >
                  {recommendations}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Dataset Context & Next Actions */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 via-card/80 to-background p-5 backdrop-blur-md shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <div className="grid h-7 w-7 place-items-center rounded-lg bg-primary/20 text-primary">
                  <Database className="h-4 w-4" />
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-primary">
                  Benchmark Quality Check
                </h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                All matched benchmarks meet standard scholarly evaluation criteria:
              </p>
              <ul className="space-y-1.5 text-xs text-foreground/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Publicly reproducible ground-truth test splits</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Documented licensing (CC-BY, MIT, Academic)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Established SOTA baselines for comparison</span>
                </li>
              </ul>
            </div>

            <div className="rounded-2xl border border-border/50 bg-secondary/20 p-5 backdrop-blur-md shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Wire these benchmark datasets into your experimental protocol:
              </p>

              <div className="space-y-2 pt-1">
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

export default DatasetsPage;