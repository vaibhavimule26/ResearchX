import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Copy,
  Check,
  Sparkles,
  FileText,
  Search,
  RotateCcw,
  ArrowRight,
  Upload,
  ChevronDown,
  Layers,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  FlaskConical,
  BookOpen,
  Lightbulb,
  FileSpreadsheet,
  Clock,
  Compass,
  MessageSquare,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { getPapers, runAnalysis, agentExecutionManager, AgentCancelledError } from "@/lib/api";
import { AgentEvaluationCard } from "@/components/dashboard/agent-evaluation-card";

export const Route = createFileRoute("/dashboard/summary")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [
      {
        title: "Research Summary Command Center — ResearchX",
      },
    ],
  }),
  component: SummaryCommandCenterPage,
});

type Paper = {
  filename: string;
  title?: string;
  uploaded_at?: string;
};

const SUGGESTED_QUERIES = [
  "Full Executive Summary",
  "Methodology & Architecture",
  "Key Findings & Baselines",
  "Core Contributions & Innovations",
];

// Helper to safely extract markdown text from any response structure
function extractTextContent(resultData: any): string {
  if (!resultData) return "";
  if (typeof resultData === "string") return resultData;
  if (Array.isArray(resultData)) {
    return resultData
      .map((item) => {
        if (typeof item === "string") return item;
        const pName = item?.paper_name;
        const res = item?.result || item?.output || "";
        return pName ? `### ${pName}\n\n${res}` : res;
      })
      .join("\n\n---\n\n");
  }
  if (typeof resultData === "object") {
    if (resultData.output && typeof resultData.output === "string") return resultData.output;
    if (resultData.result && typeof resultData.result === "string") return resultData.result;
    if (resultData.summary && typeof resultData.summary === "string") return resultData.summary;
    if (resultData.data && typeof resultData.data === "string") return resultData.data;
    if (resultData.results && typeof resultData.results === "object") {
      const first = resultData.results.summary || Object.values(resultData.results)[0];
      if (typeof first === "string") return first;
      if (first && typeof first === "object") return first.output || first.result || "";
    }
    return JSON.stringify(resultData, null, 2);
  }
  return String(resultData);
}

// Normalize markdown spacing and line endings
function normalizeMarkdown(content: string): string {
  if (!content) return "";
  let text = content
    .replace(/\0/g, "")
    .replace(/\r\n/g, "\n")
    .replace(/\ufffd/g, "—");

  // Strip any Plagiarism & Originality Audit section from summary display
  text = text.replace(
    /###\s*\d*\.?\s*(?:Plagiarism|Originality|Similarity|Academic\s*Integrity)\b[^\n]*\n[\s\S]*?(?=(?:\n###|\Z))/gi,
    ""
  );
  text = text.replace(
    /^\s*[-*]\s+\*\*(?:Estimated\s+Originality|Similarity\s+Risk|Novelty\s+vs|Academic\s+Integrity\s+Verdict|Textual\s+(?:&|and)\s+Conceptual\s+Authenticity|Textual\s+Uniqueness|Attribution\s+(?:&|and)\s+Paraphrasing)[^*]*\*\*:[^\n]*\n?/gim,
    ""
  );

  text = text.replace(/([^\n])\n(#{1,6}\s+[^\n]+)/g, "$1\n\n$2");
  text = text.replace(/([^\n\-\*\d])\n([*-]\s+)/g, "$1\n\n$2");
  return text.trim();
}

function SummaryCommandCenterPage() {
  const search = useSearch({ from: "/dashboard/summary" });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [showPaperSelector, setShowPaperSelector] = useState(false);

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
          err instanceof Error ? err.message : "Failed to load uploaded research papers"
        );
      } finally {
        setLoadingPapers(false);
      }
    };

    loadPapers();
  }, [search.paper]);

  useEffect(() => {
    return () => {
      agentExecutionManager.stop("summary");
    };
  }, []);

  // ==========================
  // Execute Summary Agent
  // ==========================
  const handleGenerateSummary = async (customQuery?: string) => {
    if (!selectedPaper) {
      setError("Please select an uploaded research paper first.");
      return;
    }

    const queryToExecute = typeof customQuery === "string" ? customQuery : query;

    try {
      setLoading(true);
      setError("");
      setActiveQuery(queryToExecute);

      const response = await runAnalysis(
        selectedPaper,
        "summary",
        queryToExecute || "summary"
      );

      const raw = response?.result ?? (response as any)?.data ?? (response as any)?.results ?? "";
      const resultText = extractTextContent(raw);

      if (!resultText) {
        throw new Error("Unable to generate the summary. The research paper could not be processed.");
      }

      setSummary(resultText);
    } catch (err: any) {
      if (err instanceof AgentCancelledError || err?.name === "AbortError") {
        return;
      }
      setError(
        err instanceof Error
          ? err.message
          : "Unable to generate the summary. The research paper could not be processed."
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================
  // Clipboard Copy
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

  const selectedPaperObj = papers.find((p) => p.filename === selectedPaper);

  return (
    <div className="min-w-0 space-y-6 pb-16">
      {/* ==========================
          Header Bar
      ========================== */}
      <PageHeader
        title="Research Summary"
        subtitle="Generate an AI-powered summary of your selected research paper."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Link to="/dashboard/upload">
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-1.5 border-border/50 bg-secondary/30 text-xs font-medium hover:bg-secondary/60"
              >
                <Upload className="h-3.5 w-3.5 text-primary" />
                Upload PDF
              </Button>
            </Link>

            {summary && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copySummary}
                disabled={loading}
                className="h-9 gap-1.5 border-border/60 text-xs font-medium"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    Copy Summary
                  </>
                )}
              </Button>
            )}
          </div>
        }
      />

      {/* ==========================
          Paper Selector Card
      ========================== */}
      <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 sm:p-6 shadow-sm backdrop-blur-sm space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center gap-3.5 min-w-0">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl gradient-primary-bg shadow-sm">
              <FileText className="h-6 w-6 text-primary-foreground" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                  Selected Research Paper
                </span>
                {selectedPaper && (
                  <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400">
                    <CheckCircle2 className="h-2.5 w-2.5" /> Ready
                  </span>
                )}
              </div>
              <h2 className="text-base sm:text-lg font-semibold truncate text-foreground font-display">
                {selectedPaper || "No research paper selected"}
              </h2>
              {selectedPaperObj?.uploaded_at && (
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                  <Clock className="h-3 w-3" />
                  Uploaded: {selectedPaperObj.uploaded_at}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 self-start lg:self-center">
            {/* Paper Switcher Drawer/Dropdown Trigger */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowPaperSelector((prev) => !prev)}
                disabled={loadingPapers || papers.length === 0}
                className="flex items-center gap-2 rounded-xl border border-border/60 bg-secondary/40 hover:bg-secondary/70 px-3.5 py-2 text-xs font-medium text-foreground transition-all cursor-pointer"
              >
                <span>Select another paper</span>
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
              </button>

              {/* Selector Popover */}
              {showPaperSelector && (
                <div className="absolute right-0 top-full mt-2 w-80 max-h-72 overflow-y-auto rounded-2xl border border-border/60 bg-card p-2 shadow-2xl z-50 backdrop-blur-xl scrollbar-thin">
                  <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70 border-b border-border/30 mb-1">
                    Uploaded Research Papers ({papers.length})
                  </div>
                  {papers.map((p) => (
                    <button
                      key={p.filename}
                      type="button"
                      onClick={() => {
                        setSelectedPaper(p.filename);
                        setShowPaperSelector(false);
                        setSummary("");
                        setError("");
                      }}
                      className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-xs transition-colors ${
                        selectedPaper === p.filename
                          ? "bg-primary/20 text-primary border border-primary/30 font-medium"
                          : "text-foreground hover:bg-secondary/50"
                      }`}
                    >
                      <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      <span className="truncate flex-1">{p.filename}</span>
                      {selectedPaper === p.filename && (
                        <Check className="h-3.5 w-3.5 text-primary shrink-0" />
                      )}
                    </button>
                  ))}
                  <div className="pt-2 mt-1 border-t border-border/30">
                    <Link
                      to="/dashboard/upload"
                      className="flex items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs text-primary font-medium hover:underline"
                    >
                      <Upload className="h-3 w-3" /> Upload new research PDF
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Primary Action Button */}
            <Button
              type="button"
              variant="hero"
              onClick={() => handleGenerateSummary()}
              disabled={loading || loadingPapers || !selectedPaper}
              className="min-w-[170px] h-9 gap-2 shadow-sm font-medium text-xs cursor-pointer"
            >
              {loading ? (
                <>
                  <RotateCcw className="h-3.5 w-3.5 animate-spin" />
                  Analyzing Paper...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  {summary ? "Rerun Summary" : "Generate Summary"}
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Optional Research Focus & Quick Suggestions */}
        <div className="pt-3 border-t border-border/30 space-y-2.5">
          <div className="flex items-center justify-between">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/80 flex items-center gap-1.5">
              <Search className="h-3 w-3 text-primary" />
              Research Focus / Inquiry (Optional)
            </label>
            <span className="text-[10px] text-muted-foreground/60">
              Press Enter or click quick focus to run
            </span>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading && selectedPaper) {
                  e.preventDefault();
                  handleGenerateSummary();
                }
              }}
              placeholder="e.g. Focus on proposed framework, quantitative benchmarks, and plagiarism check..."
              disabled={loading || !selectedPaper}
              className="flex-1 rounded-xl border border-border/60 bg-secondary/30 px-3.5 py-2 text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            />
          </div>

          {/* Quick Prompts */}
          <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
            <span className="text-[11px] text-muted-foreground mr-1">Focus Mode:</span>
            {SUGGESTED_QUERIES.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => {
                  setQuery(chip);
                  handleGenerateSummary(chip);
                }}
                disabled={loading || !selectedPaper}
                className={`text-[11px] px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 cursor-pointer ${
                  query === chip
                    ? "bg-primary/20 border-primary text-primary font-medium"
                    : "bg-secondary/40 border-border/40 text-muted-foreground hover:text-foreground hover:bg-secondary/70"
                }`}
              >
                <span>{chip}</span>
                <ArrowRight className="h-2 w-2 opacity-50" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ==========================
          Error State
      ========================== */}
      {error && !loading && (
        <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-5 text-sm text-destructive flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold text-sm">Unable to generate the summary.</p>
              <p className="text-xs text-destructive/80 mt-0.5">{error}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleGenerateSummary()}
              className="h-8 text-xs border-destructive/40 hover:bg-destructive/20"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Retry Analysis
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowPaperSelector(true)}
              className="h-8 text-xs border-destructive/40 hover:bg-destructive/20"
            >
              Select Another Paper
            </Button>
          </div>
        </div>
      )}

      {/* ==========================
          Analysis / Loading State
      ========================== */}
      {loading && (
        <div className="rounded-2xl bg-secondary/15 border border-border/40 p-8 sm:p-10 text-center space-y-6 backdrop-blur-sm">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-primary">
            <RotateCcw className="h-8 w-8 animate-spin text-primary" />
          </div>

          <div className="space-y-1.5 max-w-md mx-auto">
            <div className="inline-flex items-center gap-1.5 rounded-md bg-primary/15 border border-primary/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
              AI Summary Engine Active
            </div>
            <h3 className="text-lg font-semibold font-display">
              Analyzing Research Paper
            </h3>
            <p className="text-xs text-muted-foreground font-mono truncate">
              {selectedPaper}
            </p>
          </div>

          {/* Realistic Active Analysis Steps */}
          <div className="max-w-lg mx-auto grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left pt-2">
            <div className="rounded-xl border border-border/40 bg-secondary/30 p-3 flex items-center gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <div className="min-w-0 text-xs">
                <span className="font-semibold text-foreground">Document Loaded</span>
                <p className="text-[10px] text-muted-foreground truncate">PDF text context verified</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/40 bg-secondary/30 p-3 flex items-center gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <div className="min-w-0 text-xs">
                <span className="font-semibold text-foreground">Content Identified</span>
                <p className="text-[10px] text-muted-foreground truncate">Methodology & findings</p>
              </div>
            </div>

            <div className="rounded-xl border border-primary/30 bg-primary/5 p-3 flex items-center gap-2.5">
              <RotateCcw className="h-4 w-4 text-primary animate-spin shrink-0" />
              <div className="min-w-0 text-xs">
                <span className="font-semibold text-primary">Generating Summary</span>
                <p className="text-[10px] text-muted-foreground truncate">Scholarly synthesis running</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/30 bg-secondary/20 p-3 flex items-center gap-2.5 opacity-60">
              <div className="h-4 w-4 rounded-full border border-muted-foreground/40 shrink-0" />
              <div className="min-w-0 text-xs">
                <span className="font-medium text-muted-foreground">Structuring Output</span>
                <p className="text-[10px] text-muted-foreground truncate">Executive sections</p>
              </div>
            </div>
          </div>

          {/* Skeleton Shimmering Bars */}
          <div className="max-w-md mx-auto space-y-2 pt-2 opacity-50 animate-pulse">
            <div className="h-2 rounded bg-secondary/70 w-full" />
            <div className="h-2 rounded bg-secondary/60 w-5/6 mx-auto" />
            <div className="h-2 rounded bg-secondary/50 w-2/3 mx-auto" />
          </div>
        </div>
      )}

      {/* ==========================
          Empty State (No Paper Uploaded)
      ========================== */}
      {!selectedPaper && !loading && !loadingPapers && (
        <div className="rounded-2xl border border-dashed border-border/60 bg-secondary/10 p-12 text-center space-y-4">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-secondary/40 text-muted-foreground">
            <FileText className="h-7 w-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold font-display">No research paper selected</h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto">
              Upload or select a research paper to generate an AI-powered research summary.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link to="/dashboard/upload">
              <Button variant="hero" size="sm" className="gap-1.5 text-xs">
                <Upload className="h-3.5 w-3.5" />
                Upload Research Paper
              </Button>
            </Link>
            <Link to="/dashboard/papers">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs border-border/50">
                <Search className="h-3.5 w-3.5" />
                Select from Library
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* ==========================
          Two-Column Research Command Center Layout
      ========================== */}
      {summary && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* LEFT: Main Summary Column (8 cols) */}
          <div className="lg:col-span-8 space-y-5">
            <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 sm:p-7 shadow-sm backdrop-blur-sm space-y-5">
              {/* Summary Top Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border/30">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                    <Sparkles className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-base font-display">
                      Executive Research Summary
                    </h3>
                    <p className="truncate text-xs text-muted-foreground font-mono">
                      {selectedPaper}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-center">
                  {activeQuery && (
                    <span className="inline-flex items-center gap-1 rounded-lg bg-primary/10 border border-primary/20 px-2.5 py-1 text-xs text-primary font-medium">
                      Focus: {activeQuery}
                    </span>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerateSummary()}
                    className="h-8 text-xs gap-1 border-border/40"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Rerun
                  </Button>
                </div>
              </div>

              {/* Formatted Markdown Content */}
              <div className="overflow-x-auto text-sm leading-relaxed text-foreground/90">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => (
                      <h1 className="text-xl font-bold mt-5 mb-3 text-foreground font-display tracking-tight border-b border-border/30 pb-2" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2 className="text-lg font-bold mt-5 mb-2.5 text-foreground font-display tracking-tight" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3
                        className="text-base font-semibold mt-5 mb-2 font-display border-b pb-1 tracking-tight flex items-center gap-2 text-primary border-border/30"
                        {...props}
                      />
                    ),
                    h4: ({ node, ...props }) => (
                      <h4 className="text-sm font-semibold mt-3 mb-1 text-foreground font-display tracking-tight" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                      <p className="leading-relaxed mb-3 text-foreground/90 text-sm" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc pl-5 space-y-1.5 mb-3 text-foreground/90" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal pl-5 space-y-1.5 mb-3 text-foreground/90" {...props} />
                    ),
                    li: ({ node, children, ...props }: any) => (
                      <li className="leading-relaxed pl-1 [&>p]:inline [&>p]:mb-0 [&>p]:leading-relaxed [&>p+p]:block [&>p+p]:mt-1" {...props}>
                        {children}
                      </li>
                    ),
                    strong: ({ node, ...props }) => (
                      <strong className="font-semibold text-foreground" {...props} />
                    ),
                    code: ({ node, inline, ...props }: any) => (
                      <code className="rounded bg-secondary/80 px-1.5 py-0.5 text-xs font-mono text-primary font-medium border border-border/40" {...props} />
                    ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote className="border-l-4 border-primary/50 pl-4 py-1 italic my-3 text-muted-foreground bg-secondary/20 rounded-r-xl" {...props} />
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
                    hr: () => <hr className="my-4 border-border/40" />,
                  }}
                >
                  {normalizeMarkdown(summary)}
                </ReactMarkdown>
              </div>
            </div>

            {/* Scholarly Accuracy & Factuality Evaluation Card */}
            <AgentEvaluationCard
              agentName="summary"
              agentTitle="Summary Agent"
              outputText={normalizeMarkdown(summary)}
              paperName={selectedPaper}
            />
          </div>


          {/* RIGHT: Insight & Context Column (4 cols) */}
          <div className="lg:col-span-4 space-y-5">
            {/* Card 1: Paper Information */}
            <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 pb-2.5 border-b border-border/30">
                <FileText className="h-4 w-4 text-primary" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Paper Information
                </h4>
              </div>

              <div className="space-y-2.5 text-xs">
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                    Filename
                  </span>
                  <p className="font-mono text-foreground font-medium truncate mt-0.5" title={selectedPaper}>
                    {selectedPaper}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-muted-foreground">Format:</span>
                  <span className="font-medium text-foreground">PDF Document</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Analysis Status:</span>
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3 w-3" /> Grounded & Verified
                  </span>
                </div>

                {selectedPaperObj?.uploaded_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Uploaded:</span>
                    <span className="text-foreground">{selectedPaperObj.uploaded_at}</span>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-border/30 flex items-center justify-between gap-2">
                <Link
                  to="/dashboard/papers"
                  search={{ paper: selectedPaper }}
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                >
                  <Search className="h-3 w-3" /> Open Search
                </Link>
                <Link
                  to="/dashboard/history"
                  className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground font-medium"
                >
                  <Clock className="h-3 w-3" /> History
                </Link>
              </div>
            </div>

            {/* Card 2: Research Workflow Navigator ("Research Journey") */}
            <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 pb-2.5 border-b border-border/30">
                <Compass className="h-4 w-4 text-primary" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Research Journey
                </h4>
              </div>

              <div className="space-y-2 text-xs">
                <Link
                  to="/dashboard/papers"
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    1. Paper Search
                  </span>
                  <ExternalLink className="h-3 w-3 opacity-40" />
                </Link>

                <Link
                  to="/dashboard/upload"
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    2. Paper Upload
                  </span>
                  <ExternalLink className="h-3 w-3 opacity-40" />
                </Link>

                <Link
                  to="/dashboard/chat"
                  search={{ paper: selectedPaper }}
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <MessageSquare className="h-3.5 w-3.5 text-primary" />
                    3. AI Chat
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Link>

                <div className="flex items-center justify-between p-1.5 rounded-lg bg-primary/15 text-primary font-medium border border-primary/25">
                  <span className="flex items-center gap-2">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    4. Research Summary
                  </span>
                  <span className="text-[10px] font-bold uppercase">Active</span>
                </div>

                <Link
                  to="/dashboard/gaps"
                  search={{ paper: selectedPaper }}
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Lightbulb className="h-3.5 w-3.5" />
                    5. Research Gaps
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Link>

                <Link
                  to="/dashboard/literature"
                  search={{ paper: selectedPaper }}
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <BookOpen className="h-3.5 w-3.5" />
                    6. Literature Survey
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Link>

                <Link
                  to="/dashboard/experiments"
                  search={{ paper: selectedPaper }}
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <FlaskConical className="h-3.5 w-3.5" />
                    7. Experiments
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Link>

                <Link
                  to="/dashboard/report"
                  className="flex items-center justify-between p-1.5 rounded-lg text-muted-foreground hover:bg-secondary/40 hover:text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <FileSpreadsheet className="h-3.5 w-3.5" />
                    8. IEEE Report
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Link>
              </div>
            </div>

            {/* Card 3: AI Research Pipeline */}
            <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 shadow-sm space-y-3.5">
              <div className="flex items-center gap-2 pb-2.5 border-b border-border/30">
                <Layers className="h-4 w-4 text-primary" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  AI Research Pipeline
                </h4>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-start gap-2.5">
                  <div className="h-5 w-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400 font-bold text-[10px]">
                    1
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Document Ingestion</span>
                    <p className="text-[11px] text-muted-foreground">PDF text extracted & parsed</p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <div className="h-5 w-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400 font-bold text-[10px]">
                    2
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Content Retrieval</span>
                    <p className="text-[11px] text-muted-foreground">Multi-tier evidence extraction</p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <div className="h-5 w-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400 font-bold text-[10px]">
                    3
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Summary Synthesis</span>
                    <p className="text-[11px] text-muted-foreground">Methodology, metrics & takeaways</p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <div className="h-5 w-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400 font-bold text-[10px]">
                    4
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Integrity & Authenticity</span>
                    <p className="text-[11px] text-muted-foreground">Scholarly originality verified</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Card 4: Next Quick Actions */}
            <div className="rounded-2xl bg-secondary/20 border border-border/40 p-5 shadow-sm space-y-2.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Seamlessly transfer this paper to other specialized AI agents:
              </p>

              <div className="space-y-2 pt-1">
                <Link
                  to="/dashboard/gaps"
                  search={{ paper: selectedPaper }}
                  className="block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                  >
                    <span className="flex items-center gap-1.5">
                      <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
                      Identify Research Gaps
                    </span>
                    <ArrowRight className="h-3 w-3 opacity-50" />
                  </Button>
                </Link>

                <Link
                  to="/dashboard/literature"
                  search={{ paper: selectedPaper }}
                  className="block"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                  >
                    <span className="flex items-center gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-blue-400" />
                      Run Literature Survey
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
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
export default SummaryCommandCenterPage;