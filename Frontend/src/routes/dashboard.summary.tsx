import { createFileRoute, useSearch } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Download,
  Copy,
  Check,
  Sparkles,
  FileText,
  Search,
  RotateCcw,
  ArrowRight,
  FileCheck2,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/summary")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),

  head: () => ({
    meta: [
      {
        title: "Research Summary — ResearchX",
      },
    ],
  }),

  component: SummaryPage,
});

type Paper = {
  filename: string;
  title?: string;
  uploaded_at?: string;
};

const SUGGESTED_QUERIES = [
  "Full Executive Summary",
  "Methodology & Architecture",
  "Core Contributions & Innovations",
  "Experimental Benchmarks & Results",
];

function SummaryPage() {
  const search = useSearch({
    from: "/dashboard/summary",
  });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  // ==========================
  // Load Uploaded Papers
  // ==========================
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
        } else if (uploadedPapers.length > 0) {
          setSelectedPaper(uploadedPapers[0].filename);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load uploaded papers"
        );
      } finally {
        setLoadingPapers(false);
      }
    };

    loadPapers();
  }, [search.paper]);

  // ==========================
  // Generate Summary Action
  // ==========================
  const handleGenerateSummary = async (customQuery?: string) => {
    const queryToExecute = (customQuery !== undefined ? customQuery : query).trim();

    if (!selectedPaper) {
      setError("Please select an uploaded research paper.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setActiveQuery(queryToExecute);

      const response = await runAnalysis(
        selectedPaper,
        "summary",
        queryToExecute || "summary"
      );

      const resultText = response?.result || (response as any)?.data || "";

      if (!resultText) {
        throw new Error("No summary generated. Please verify the paper content.");
      }

      setSummary(resultText);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate summary"
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================
  // Copy Summary
  // ==========================
  const copySummary = async () => {
    if (!summary) return;

    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy summary to clipboard");
    }
  };

  // ==========================
  // Download Summary
  // ==========================
  const downloadSummary = () => {
    if (!summary) return;

    const content = [
      `# ResearchX AI Summary: ${selectedPaper}`,
      activeQuery ? `Query: ${activeQuery}` : "Analysis: Executive Summary",
      `Generated: ${new Date().toLocaleString()}`,
      "",
      "---",
      "",
      summary,
    ].join("\n");

    const blob = new Blob([content], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename}-summary.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0 space-y-6 pb-12">
      <PageHeader
        title="Research Summary Agent"
        subtitle={
          selectedPaper
            ? `Run query-grounded synthesis on '${selectedPaper}'.`
            : "Select an uploaded research paper to generate grounded AI summaries."
        }
        action={
          <div className="flex flex-wrap items-center gap-2">
            {summary && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={copySummary}
                  disabled={loading}
                  className="h-9 gap-1.5 border-border/60"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy Output
                    </>
                  )}
                </Button>

                <Button
                  type="button"
                  variant="hero"
                  size="sm"
                  onClick={downloadSummary}
                  disabled={loading}
                  className="h-9 gap-1.5"
                >
                  <Download className="h-4 w-4" />
                  Export Markdown
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* ==========================
          Paper & Query Control Card
      ========================== */}
      <div className="rounded-2xl glass p-6 space-y-5 border border-border/40 shadow-sm">
        {/* Paper Selector Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl gradient-primary-bg text-primary-foreground shadow-sm">
              <FileCheck2 className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">Target Research Paper</h3>
              <p className="text-xs text-muted-foreground">
                Select the specific uploaded PDF for analysis
              </p>
            </div>
          </div>

          <div className="min-w-[280px] max-w-full sm:max-w-md">
            <select
              value={selectedPaper}
              onChange={(e) => {
                setSelectedPaper(e.target.value);
                setSummary("");
                setError("");
              }}
              disabled={loadingPapers || loading}
              className="min-h-10 w-full rounded-xl border border-border/60 bg-secondary/50 px-3.5 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              {loadingPapers && <option value="">Loading uploaded papers...</option>}
              {!loadingPapers && papers.length === 0 && (
                <option value="">No papers uploaded yet</option>
              )}
              {papers.map((paper, index) => (
                <option key={`${paper.filename}-${index}`} value={paper.filename}>
                  📄 {paper.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Query Input Area (Works just like AI Workspace) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Search className="h-3.5 w-3.5 text-primary" />
              Research Query / Focus (Optional)
            </label>
            <span className="text-[11px] text-muted-foreground">
              Leave blank for a full executive summary
            </span>
          </div>

          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) {
                  e.preventDefault();
                  handleGenerateSummary();
                }
              }}
              placeholder="e.g. Summarize the core methodology, architecture, and empirical benchmarks..."
              disabled={loading || !selectedPaper}
              className="w-full rounded-xl border border-border/60 bg-secondary/30 px-4 py-3 text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            />
          </div>

          {/* Quick Suggestion Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-muted-foreground font-medium">Quick Prompts:</span>
            {SUGGESTED_QUERIES.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => {
                  setQuery(chip);
                  handleGenerateSummary(chip);
                }}
                disabled={loading || !selectedPaper}
                className="text-xs px-3 py-1 rounded-full border border-border/50 bg-secondary/30 hover:bg-secondary/70 hover:border-primary/40 text-foreground transition-all flex items-center gap-1 cursor-pointer"
              >
                <span>{chip}</span>
                <ArrowRight className="h-2.5 w-2.5 opacity-60" />
              </button>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end pt-2">
          <Button
            type="button"
            variant="hero"
            onClick={() => handleGenerateSummary()}
            disabled={loading || loadingPapers || !selectedPaper}
            className="min-w-[180px] gap-2 shadow-sm font-medium"
          >
            {loading ? (
              <>
                <RotateCcw className="h-4 w-4 animate-spin" />
                Analyzing Paper...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Run Summary Agent
              </>
            )}
          </Button>
        </div>
      </div>

      {/* ==========================
          Error State
      ========================== */}
      {error && (
        <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-destructive" />
          <span>{error}</span>
        </div>
      )}

      {/* ==========================
          Loading State
      ========================== */}
      {loading && (
        <div className="rounded-2xl glass p-12 text-center space-y-4 border border-border/40">
          <div className="grid h-12 w-12 place-items-center rounded-2xl gradient-primary-bg glow-primary mx-auto">
            <Sparkles className="h-6 w-6 text-primary-foreground animate-pulse" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-base">Grounding Summary Agent on Uploaded PDF</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Extracting document sections, retrieving RAG evidence, and synthesizing scholarly analysis for{" "}
              <span className="font-medium text-foreground">{selectedPaper}</span>...
            </p>
          </div>
        </div>
      )}

      {/* ==========================
          Empty State
      ========================== */}
      {!summary && !loading && !error && (
        <div className="rounded-2xl glass p-12 text-center space-y-3 border border-border/30">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-secondary/50 text-primary mx-auto">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-base">Ready to Analyze</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Select an uploaded research paper above, specify your query or prompt, and click{" "}
            <span className="font-medium text-foreground">Run Summary Agent</span> to generate a grounded analysis.
          </p>
        </div>
      )}

      {/* ==========================
          Summary Result Card
      ========================== */}
      {summary && !loading && (
        <div className="rounded-2xl glass p-6 space-y-5 border border-border/40 shadow-sm">
          {/* Card Top Info */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border/40">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                <Sparkles className="h-5 w-5 text-primary-foreground" />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-base">AI Generated Summary</h3>
                <p className="truncate text-xs text-muted-foreground flex items-center gap-2">
                  <span>📄 {selectedPaper}</span>
                  {activeQuery && (
                    <>
                      <span>•</span>
                      <span className="text-primary font-medium">Focus: {activeQuery}</span>
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copySummary}
                className="h-8 text-xs border-border/40"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 mr-1 text-emerald-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 mr-1" />
                    Copy
                  </>
                )}
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => handleGenerateSummary()}
                className="h-8 text-xs gap-1"
              >
                <RotateCcw className="h-3 w-3" />
                Rerun Agent
              </Button>
            </div>
          </div>

          {/* Formatted Markdown Output */}
          <div className="overflow-x-auto text-sm leading-relaxed space-y-4">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ node, ...props }) => (
                  <h1 className="text-xl font-bold mt-5 mb-2.5 text-foreground font-display tracking-tight" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-lg font-bold mt-4 mb-2 text-foreground font-display tracking-tight" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-base font-semibold mt-4 mb-2 text-primary font-display border-b border-border/30 pb-1" {...props} />
                ),
                p: ({ node, ...props }) => (
                  <p className="leading-relaxed mb-3 text-foreground/90" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-inside space-y-2 mb-4 text-foreground/90 pl-1" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal list-inside space-y-2 mb-4 text-foreground/90 pl-1" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="leading-relaxed" {...props} />
                ),
                strong: ({ node, ...props }) => (
                  <strong className="font-semibold text-foreground" {...props} />
                ),
                blockquote: ({ node, ...props }) => (
                  <blockquote className="border-l-4 border-primary/50 pl-4 py-1 italic my-3 text-muted-foreground bg-secondary/20 rounded-r-lg" {...props} />
                ),
                table: ({ node, ...props }) => (
                  <div className="my-4 w-full overflow-x-auto rounded-xl border border-border/60 shadow-sm">
                    <table className="w-full text-left text-xs border-collapse" {...props} />
                  </div>
                ),
                thead: ({ node, ...props }) => (
                  <thead className="bg-secondary/80 text-foreground font-semibold border-b border-border/60" {...props} />
                ),
                th: ({ node, ...props }) => (
                  <th className="px-4 py-3 font-semibold text-foreground tracking-wide whitespace-nowrap" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="px-4 py-2.5 border-t border-border/30 text-muted-foreground align-top" {...props} />
                ),
                hr: () => <hr className="my-5 border-border/40" />,
              }}
            >
              {summary}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}