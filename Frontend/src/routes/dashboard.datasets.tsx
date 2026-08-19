import { createFileRoute } from "@tanstack/react-router";
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
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/datasets")({
  head: () => ({
    meta: [
      {
        title: "Dataset Recommendations — ResearchX",
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
  const [mode, setMode] = useState<InputMode>("paper");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
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

        if (uploadedPapers.length > 0) {
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
  }, []);

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
      "=" .repeat(60),
      targetTitle,
      `Generated At: ${new Date().toISOString()}`,
      "=" .repeat(60),
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
    <div className="min-w-0">
      <PageHeader
        title="Dataset Intelligence & Benchmarks"
        subtitle={
          mode === "paper"
            ? selectedPaper
              ? `Discover highly similar benchmark datasets for '${selectedPaper}'.`
              : "Select an uploaded research paper to extract and match datasets."
            : "Enter a research query or topic to find authoritative, peer-reviewed benchmark datasets."
        }
        action={
          <div className="flex gap-2">
            <Button
              variant="glass"
              onClick={copyRecommendations}
              disabled={!recommendations || loading}
              className="gap-1.5"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy Report
                </>
              )}
            </Button>

            <Button
              variant="hero"
              onClick={downloadRecommendations}
              disabled={!recommendations || loading}
              className="gap-1.5"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      {/* Mode Switcher & Input Control */}
      <div className="rounded-2xl glass p-5 space-y-4">
        {/* Toggle Mode */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
          <div className="flex items-center gap-2">
            <div className="inline-flex rounded-xl bg-secondary/50 p-1 border border-border/50">
              <button
                type="button"
                onClick={() => {
                  setMode("paper");
                  setError("");
                }}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  mode === "paper"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                Uploaded Paper (PDF)
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("query");
                  setError("");
                }}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  mode === "query"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Search className="h-3.5 w-3.5" />
                Custom Research Query
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-[var(--success)]" />
            <span>High-similarity benchmark verification (&gt;90% match)</span>
          </div>
        </div>

        {/* Dynamic Input Control */}
        {mode === "paper" ? (
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <select
              value={selectedPaper}
              onChange={(event) => {
                setSelectedPaper(event.target.value);
                setRecommendations("");
                setError("");
              }}
              disabled={loadingPapers || loading}
              className="min-h-10 flex-1 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              {loadingPapers && <option value="">Loading uploaded papers...</option>}
              {!loadingPapers && papers.length === 0 && (
                <option value="">No papers uploaded yet — switch to Custom Query</option>
              )}
              {papers.map((paper, index) => (
                <option
                  key={`${paper.filename}-${index}`}
                  value={paper.filename}
                >
                  {paper.filename}
                </option>
              ))}
            </select>

            <Button
              variant="hero"
              onClick={handleRecommend}
              disabled={loading || loadingPapers || !selectedPaper}
              className="gap-2 min-w-[200px]"
            >
              <Sparkles className="h-4 w-4" />
              {loading ? "Finding Benchmarks..." : "Recommend Datasets"}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
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
                  className="w-full min-h-10 rounded-xl border border-border/60 bg-secondary/40 pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              <Button
                variant="hero"
                onClick={handleRecommend}
                disabled={loading || !customQuery.trim()}
                className="gap-2 min-w-[200px]"
              >
                <Sparkles className="h-4 w-4" />
                {loading ? "Searching Benchmarks..." : "Find Datasets"}
              </Button>
            </div>

            {/* Quick Preset Queries */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-xs text-muted-foreground mr-1">Try:</span>
              {PRESET_QUERIES.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setCustomQuery(preset);
                  }}
                  className="rounded-lg border border-border/40 bg-secondary/30 px-2.5 py-1 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-2">
          <span>{error}</span>
        </div>
      )}

      {!recommendations && !loading && !error && (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl glass p-5">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary mb-3">
              <Database className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">High-Similarity Datasets</h3>
            <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
              Curated peer-reviewed benchmark datasets matching your exact domain, task modality, and schema with &gt;90% accuracy.
            </p>
          </div>

          <div className="rounded-2xl glass p-5">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-purple-500/10 text-purple-400 mb-3">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">Detailed Selection Rationale</h3>
            <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
              Every recommended dataset includes deep technical reasons explaining why it was chosen, baseline utility, and ground-truth quality.
            </p>
          </div>

          <div className="rounded-2xl glass p-5">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-500/10 text-emerald-400 mb-3">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">Standardized Benchmark Matrix</h3>
            <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
              Standardized comparison table with license integrity, evaluation metrics, and direct Python/HuggingFace loading snippets.
            </p>
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">
          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-primary" />
          <h3 className="mt-4 font-semibold text-foreground">ResearchX Dataset Specialist is Working</h3>
          <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
            Analyzing domain constraints, filtering high-similarity benchmark datasets, and synthesizing technical selection justifications...
          </p>
        </div>
      )}

      {recommendations && !loading && (
        <div className="mt-6 rounded-2xl glass p-7">
          <div className="flex items-center justify-between border-b border-border/50 pb-4">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg">
                <Database className="h-5 w-5 text-primary-foreground" />
              </div>
              <div className="min-w-0">
                <h3 className="text-base font-semibold text-foreground">
                  Dataset Recommendation &amp; Benchmark Report
                </h3>
                <p className="truncate text-xs text-muted-foreground">
                  {mode === "paper" ? `Target Paper: ${selectedPaper}` : `Query: ${customQuery}`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="h-3 w-3" />
                Verified Benchmarks
              </span>
            </div>
          </div>

          {/* Standardized Markdown Content Rendering */}
          <div
            className="mt-6 text-sm text-foreground/90 leading-relaxed
            [&_h3]:text-base [&_h3]:font-bold [&_h3]:text-foreground [&_h3]:mt-6 [&_h3]:mb-3 [&_h3]:flex [&_h3]:items-center [&_h3]:gap-2
            [&_h4]:text-sm [&_h4]:font-semibold [&_h4]:text-foreground [&_h4]:mt-4 [&_h4]:mb-2
            [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:my-3 [&_ul]:space-y-1.5
            [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:my-3 [&_ol]:space-y-1.5
            [&_li]:leading-relaxed
            [&_strong]:text-foreground [&_strong]:font-semibold
            [&_hr]:my-6 [&_hr]:border-border/50
            [&_pre]:my-3 [&_pre]:p-3.5 [&_pre]:rounded-xl [&_pre]:bg-secondary/60 [&_pre]:border [&_pre]:border-border/60 [&_pre]:overflow-x-auto [&_pre]:text-xs
            [&_code]:rounded [&_code]:bg-secondary/80 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-xs [&_code]:font-mono
            [&_table]:w-full [&_table]:my-6 [&_table]:border-collapse [&_table]:rounded-xl [&_table]:border [&_table]:border-border/60 [&_table]:overflow-hidden
            [&_thead]:bg-secondary/70
            [&_th]:border [&_th]:border-border/60 [&_th]:p-3 [&_th]:text-left [&_th]:font-semibold [&_th]:text-xs [&_th]:text-foreground
            [&_td]:border [&_td]:border-border/40 [&_td]:p-3 [&_td]:text-xs [&_td]:leading-relaxed
            [&_p]:leading-relaxed [&_p]:mb-3"
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {recommendations}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}