import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import {
  Download,
  Printer,
  Share2,
  FileText,
  FileDown,
  Sparkles,
  Copy,
  Check,
  CheckCircle2,
  BookOpen,
  FileSpreadsheet,
  RotateCcw,
  Layers,
  ArrowRight,
  ExternalLink,
  Search,
  Columns,
  AlignLeft,
  Loader2,
  ShieldCheck,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { PaperSelectorCard } from "@/components/dashboard/paper-selector-card";
import { AIProcessingCard } from "@/components/dashboard/ai-processing-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { ErrorState } from "@/components/dashboard/error-state";
import {
  getPapers,
  generateIEEEReport,
  downloadIEEEReportPDF,
  agentExecutionManager,
  AgentCancelledError,
  API_BASE_URL,
  type PlagiarismAudit,
} from "@/lib/api";
import { AgentEvaluationCard } from "@/components/dashboard/agent-evaluation-card";

export const Route = createFileRoute("/dashboard/report")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [{ title: "IEEE Research Report Generator — ResearchX" }],
  }),
  component: ReportPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

const REPORT_STAGES = [
  {
    title: "Compiling Multi-Agent Findings & Citations",
    description: "Aggregating summary, literature review, gaps, and experimental setup...",
  },
  {
    title: "Drafting Academic Abstract & Index Terms",
    description: "Synthesizing formal problem formulation, scope, and technical keywords...",
  },
  {
    title: "Structuring Methodology & Empirical Results",
    description: "Formatting mathematical descriptions, comparative tables, and ablation analysis...",
  },
  {
    title: "Formatting IEEE Manuscript & Bibliography",
    description: "Applying IEEE Transactions typography, section numbering, and citation conventions...",
  },
];

function ReportPage() {
  const search = useSearch({ from: "/dashboard/report" });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState(search.paper || "");
  const [query, setQuery] = useState("");
  const [report, setReport] = useState("");
  const [plagiarismData, setPlagiarismData] = useState<PlagiarismAudit | null>(null);
  const [editSummary, setEditSummary] = useState<string>("");
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [viewMode, setViewMode] = useState<"ieee" | "markdown">("ieee");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);
        setError("");

        const response = await getPapers();
        const uploadedPapers = response?.data?.papers || [];
        setPapers(uploadedPapers);

        if (search.paper) {
          const match = uploadedPapers.find(
            (p: Paper) => p.filename.toLowerCase() === search.paper.toLowerCase()
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

  // Auto-run if paper search query exists and no report loaded
  useEffect(() => {
    if (search.paper && !report && !loading) {
      handleGenerateReport(search.paper);
    }
  }, [search.paper]);

  const parsedIEEE = useMemo(() => {
    if (!report) return { header: null, body: "" };

    const lines = report.split("\n");
    let title = "";
    let authors = "";
    let affiliation = "";
    let correspondence = "";
    let bodyStartIndex = 0;

    for (let i = 0; i < Math.min(lines.length, 35); i++) {
      const l = lines[i].trim();
      if (l.startsWith("# ") && !title) {
        title = l.replace(/^#\s*/, "").replace(/\*\*/g, "").trim();
      } else if (l.startsWith("**Authors:**") || l.startsWith("Authors:")) {
        authors = l.replace(/\*\*Authors:\*\*/, "").replace(/Authors:/, "").trim();
      } else if (l.startsWith("**Affiliation:**") || l.startsWith("Affiliation:")) {
        affiliation = l.replace(/\*\*Affiliation:\*\*/, "").replace(/Affiliation:/, "").trim();
      } else if (l.startsWith("**Correspondence:**") || l.startsWith("Correspondence:")) {
        correspondence = l.replace(/\*\*Correspondence:\*\*/, "").replace(/Correspondence:/, "").trim();
      } else if (
        l === "---" ||
        l.startsWith("### ABSTRACT") ||
        l.startsWith("## ABSTRACT") ||
        l.startsWith("Abstract") ||
        l.startsWith("**Abstract**") ||
        l.toUpperCase() === "ABSTRACT"
      ) {
        if (title || authors) {
          bodyStartIndex = l === "---" ? i + 1 : i;
          while (
            bodyStartIndex < lines.length &&
            (lines[bodyStartIndex].trim() === "---" || !lines[bodyStartIndex].trim())
          ) {
            bodyStartIndex++;
          }
          break;
        }
      }
    }

    if (title || authors) {
      return {
        header: { title, authors, affiliation, correspondence },
        body: lines.slice(bodyStartIndex).join("\n"),
      };
    }

    return { header: null, body: report };
  }, [report]);

  const handleGenerateReport = async (targetPaper?: string, customQuery?: string) => {
    const queryToUse = customQuery !== undefined ? customQuery : query;
    const paperToUse = targetPaper !== undefined ? targetPaper : selectedPaper;
    const effectivePaper = paperToUse || (queryToUse.trim() ? "query_focus" : "");
    if (!effectivePaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setReport("");
      setPlagiarismData(null);
      setEditSummary("");

      const response = await generateIEEEReport(effectivePaper, queryToUse);
      const result = response?.result;

      if (!result) {
        throw new Error("No IEEE report received from backend");
      }

      setReport(result);
      if (response.plagiarism) {
        setPlagiarismData(response.plagiarism);
      }
      if (response.edit_summary) {
        setEditSummary(response.edit_summary);
      }
    } catch (err: any) {
      if (err instanceof AgentCancelledError || err?.name === "AbortError") {
        return;
      }
      setError(
        err instanceof Error ? err.message : "Report generation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if ((!selectedPaper && !query.trim()) || downloadingPdf) return;
    try {
      setDownloadingPdf(true);
      setError("");

      const effectivePaper = selectedPaper || "query_focus";
      const blob = await downloadIEEEReportPDF(effectivePaper, query, report);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const baseName = selectedPaper || query.trim() || "IEEE_Research_Report";
      const safeFilename = baseName
        .replace(/\.pdf$/i, "")
        .replace(/[<>:"/\\|?*]+/g, "_");

      anchor.href = url;
      anchor.download = `${safeFilename}_IEEE_Transactions_Paper.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to export IEEE PDF"
      );
    } finally {
      setDownloadingPdf(false);
    }
  };

  const copyReport = async () => {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy report");
    }
  };

  const downloadReport = (format: "md" | "txt") => {
    if (!report) return;

    const blob = new Blob([report], {
      type: format === "md" ? "text/markdown;charset=utf-8" : "text/plain;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const baseName = selectedPaper || query.trim() || "IEEE_Research_Report";
    const safeFilename = baseName
      .replace(/\.pdf$/i, "")
      .replace(/[<>:"/\\|?*]+/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename}-IEEE-Research-Report.${format}`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    if (!report) return;
    window.print();
  };

  const shareReport = async () => {
    if (!report) return;
    try {
      if (navigator.share) {
        await navigator.share({
          title: `IEEE Research Report - ${selectedPaper}`,
          text: report,
        });
        return;
      }
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError("Failed to share report");
    }
  };

  // Word count estimate
  const wordCount = useMemo(() => {
    if (!report) return 0;
    return report.trim().split(/\s+/).length;
  }, [report]);

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="IEEE Research Report Workspace"
        subtitle={
          selectedPaper
            ? `Comprehensive academic paper manuscript formatted according to IEEE Transactions standards for '${selectedPaper}'.`
            : "Select an uploaded research paper to compile an IEEE research report."
        }
        action={
          report ? (
            <div className="flex flex-wrap items-center gap-2">
              {/* View Mode Toggle */}
              <div className="flex items-center rounded-lg border border-border/60 bg-secondary/40 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setViewMode("ieee")}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                    viewMode === "ieee"
                      ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Official Two-Column IEEE Layout"
                >
                  <Columns className="h-3 w-3" />
                  <span className="hidden sm:inline">IEEE Two-Column</span>
                  <span className="sm:hidden">IEEE</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("markdown")}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                    viewMode === "markdown"
                      ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Single Column Standard View"
                >
                  <AlignLeft className="h-3 w-3" />
                  <span className="hidden sm:inline">Article View</span>
                  <span className="sm:hidden">Article</span>
                </button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={copyReport}
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
                    <span>Copy</span>
                  </>
                )}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={printReport}
                className="h-8 text-xs gap-1.5 border-border/60 hover:bg-secondary/60"
              >
                <Printer className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="hidden sm:inline">Print</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={shareReport}
                className="h-8 text-xs gap-1.5 border-border/60 hover:bg-secondary/60"
              >
                <Share2 className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="hidden sm:inline">Share</span>
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={handleExportPDF}
                disabled={downloadingPdf || (!selectedPaper && !query.trim())}
                className="h-8 text-xs gap-1.5 shadow-sm font-semibold"
              >
                {downloadingPdf ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Exporting PDF...</span>
                  </>
                ) : (
                  <>
                    <FileDown className="h-3.5 w-3.5" />
                    <span>Export IEEE PDF</span>
                  </>
                )}
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
          setReport("");
          setError("");
        }}
        loading={loading}
        loadingPapers={loadingPapers}
        subtitle="Generates Title, Abstract, Index Terms, Methodology, Results, and References."
        actionButton={
          <Button
            variant="hero"
            size="sm"
            onClick={() => handleGenerateReport()}
            disabled={loading || loadingPapers || (!selectedPaper && !query.trim())}
            className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>
              {loading
                ? "Compiling IEEE Report..."
                : report
                ? "Regenerate Report"
                : selectedPaper
                ? "Generate Complete Report"
                : "Generate Topic Report"}
            </span>
          </Button>
        }
      />

      {/* Research Query & Direct Paper Edit Request Card */}
      <div className="relative z-0 rounded-2xl border border-border/60 bg-card/80 p-5 backdrop-blur-sm shadow-xs space-y-3.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold text-foreground">
              Research Query &amp; Direct Paper Edit Request
            </span>
          </div>
          <span className="text-[11px] text-muted-foreground">
            Directly edits paper sections (e.g. adds sections, updates abstract, refines methodology) or guides focus
          </span>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loading && (selectedPaper || query.trim())) {
                handleGenerateReport();
              }
            }}
            placeholder="e.g. Add an Ethical Considerations section before the conclusion, or update abstract..."
            className="flex-1 rounded-xl border border-border/70 bg-background px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleGenerateReport()}
            disabled={loading || (!selectedPaper && !query.trim())}
            className="h-9 px-4 text-xs font-medium shrink-0"
          >
            <Sparkles className="h-3.5 w-3.5 mr-1.5 text-primary" />
            {selectedPaper && query.trim()
              ? "Apply Edit & Update Paper"
              : selectedPaper
              ? "Regenerate Paper"
              : "Generate Report"}
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[10px] uppercase font-mono text-muted-foreground/70 mr-1">
            Edit &amp; Focus Presets:
          </span>
          {[
            "Add Ethical Considerations Section",
            "Expand Methodology & Algorithmic Formulations",
            "Update Conclusion & Future Research Directions",
            "Add Benchmarks & Comparative Analysis",
            "Revise Abstract & Empirical Findings",
          ].map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => {
                setQuery(preset);
                if (!loading) {
                  handleGenerateReport(selectedPaper, preset);
                }
              }}
              className="text-[10px] px-2.5 py-1 rounded-lg border border-border/40 bg-secondary/40 hover:bg-secondary/80 text-foreground/80 hover:text-foreground transition-all cursor-pointer"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <ErrorState
          title="Unable to load research paper"
          error={
            error.toLowerCase().includes("failed to load") || error.toLowerCase().includes("unable")
              ? "Please try selecting the PDF again."
              : error
          }
          onRetry={() => handleGenerateReport()}
          className="relative z-0"
        />
      )}

      {/* Multi-Stage AI Loading Component */}
      {loading && (
        <AIProcessingCard
          agentName="IEEE DOCUMENT GENERATION ENGINE"
          title="Processing Research Paper"
          subtitle="Preparing the document for IEEE report generation..."
          stages={REPORT_STAGES}
          className="relative z-0 mt-6"
        />
      )}

      {/* Empty State before Running */}
      {!loading && !report && !error && (
        <div className="relative z-0 mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3">
              <FileSpreadsheet className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              IEEE Transactions Structure
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Standardized academic format: Abstract, Index Terms, Roman numeral sections (I to VII), equations, and references.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 border border-primary/20 text-primary mb-3">
              <Layers className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Cross-Agent Synthesis
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Combines empirical evidence, literature context, ablation experiments, and limitations into a cohesive manuscript.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
              <Download className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Publication Ready
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Export to Markdown or Plain Text for rapid importing into Overleaf LaTeX or Microsoft Word.
            </p>
          </div>
        </div>
      )}

      {/* IEEE Document Preview Workspace */}
      {report && !loading && (
        <div className="grid gap-6 lg:grid-cols-12 items-start">
          {/* Left Metadata & Navigation Sidebar (4 cols) */}
          <aside className="lg:col-span-4 space-y-4 lg:sticky lg:top-20">
            <div className="rounded-2xl border border-border/50 bg-card/80 p-5 backdrop-blur-xl shadow-md space-y-4">
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Manuscript Details
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 text-[10px] font-mono font-semibold border border-blue-500/25">
                  IEEE Format
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-[11px] text-muted-foreground/70 block">
                    Source Research Paper
                  </span>
                  <span className="font-medium text-foreground break-words mt-0.5 block">
                    {selectedPaper || (query.trim() ? `Topic Focus: "${query.trim()}"` : "Query-Based Synthesis")}
                  </span>
                </div>

                {editSummary && (
                  <div className="p-2.5 rounded-xl border border-primary/30 bg-primary/10">
                    <span className="text-[10px] font-semibold text-primary uppercase block">
                      Direct Edit Applied
                    </span>
                    <span className="text-xs text-foreground/90 font-medium block mt-0.5">
                      {editSummary}
                    </span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border/30">
                  <div>
                    <span className="text-[10px] text-muted-foreground/70 block">
                      Word Count
                    </span>
                    <span className="font-mono font-semibold text-foreground">
                      ~{wordCount.toLocaleString()} words
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted-foreground/70 block">
                      Generated
                    </span>
                    <span className="font-mono text-muted-foreground">
                      {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border/40">
                <Button
                  variant="hero"
                  size="sm"
                  onClick={handleExportPDF}
                  disabled={downloadingPdf || (!selectedPaper && !query.trim())}
                  className="w-full justify-between h-9 text-xs font-semibold shadow-xs"
                >
                  <span className="flex items-center gap-1.5">
                    {downloadingPdf ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <FileDown className="h-3.5 w-3.5" />
                    )}
                    <span>
                      {downloadingPdf
                        ? "Exporting IEEE PDF..."
                        : "Export Official IEEE PDF (.pdf)"}
                    </span>
                  </span>
                  <span className="text-[10px] opacity-75 font-mono">2-Col</span>
                </Button>
              </div>
            </div>

            {/* Plagiarism & Originality Audit Card */}
            {plagiarismData && (
              <div className="rounded-2xl border border-border/50 bg-card/80 p-5 backdrop-blur-xl shadow-md space-y-3.5">
                <div className="flex items-center justify-between border-b border-border/40 pb-2.5">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Originality &amp; Plagiarism Audit
                    </span>
                  </div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${
                      plagiarismData.risk_level === "Low"
                        ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/25"
                        : plagiarismData.risk_level === "Moderate"
                        ? "bg-amber-500/15 text-amber-400 border-amber-500/25"
                        : "bg-red-500/15 text-red-400 border-red-500/25"
                    }`}
                  >
                    {plagiarismData.risk_level} Risk
                  </span>
                </div>

                {/* Score Gauges */}
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2.5 rounded-xl border border-emerald-500/25 bg-emerald-500/5">
                    <span className="text-[10px] text-muted-foreground block">Originality Score</span>
                    <span className="text-xl font-bold font-mono text-emerald-400">
                      {plagiarismData.originality_score}%
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl border border-border/40 bg-secondary/30">
                    <span className="text-[10px] text-muted-foreground block">Similarity Index</span>
                    <span className="text-xl font-bold font-mono text-foreground">
                      {plagiarismData.similarity_score}%
                    </span>
                  </div>
                </div>

                {/* Verdict */}
                <div className="text-xs space-y-1">
                  <span className="text-[10px] uppercase font-mono text-muted-foreground/70 block">
                    Academic Integrity Verdict
                  </span>
                  <p className="text-xs text-foreground/90 font-medium leading-relaxed">
                    {plagiarismData.verdict}
                  </p>
                </div>

                {/* Analyzed Metrics */}
                <div className="pt-2 border-t border-border/30 grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-[10px] text-muted-foreground block">Analyzed Words</span>
                    <span className="font-mono text-foreground">
                      {plagiarismData.total_words_analyzed?.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted-foreground block">Corpus Compared</span>
                    <span className="font-mono text-foreground truncate block" title={plagiarismData.comparison_corpus}>
                      {plagiarismData.comparison_corpus}
                    </span>
                  </div>
                </div>

                {/* Matched Passages if any */}
                {plagiarismData.matches && plagiarismData.matches.length > 0 && (
                  <div className="pt-2 border-t border-border/30 space-y-1.5">
                    <span className="text-[10px] uppercase font-mono text-muted-foreground/70 block">
                      Detected Similar Passages ({plagiarismData.matches.length})
                    </span>
                    <div className="max-h-32 overflow-y-auto space-y-1 pr-1">
                      {plagiarismData.matches.map((m, idx) => (
                        <div key={idx} className="p-1.5 rounded-lg bg-secondary/40 text-[10px] border border-border/30">
                          <div className="flex justify-between font-mono font-medium text-foreground">
                            <span className="truncate max-w-[140px]">{m.matched_source}</span>
                            <span className="text-amber-400">{m.similarity}%</span>
                          </div>
                          <p className="text-muted-foreground mt-0.5 line-clamp-2 italic">
                            "{m.snippet}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Next Step: Presentation */}
            <div className="rounded-2xl border border-border/50 bg-secondary/20 p-5 backdrop-blur-md shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Generate presentation slides based on this report:
              </p>

              <Link
                to="/dashboard/ppt"
                search={{ paper: selectedPaper }}
                className="block"
              >
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-between h-8 text-xs border-border/50 hover:border-primary/40 font-medium"
                >
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                    Create Presentation Slides
                  </span>
                  <ArrowRight className="h-3 w-3 opacity-50" />
                </Button>
              </Link>
            </div>
          </aside>

          {/* Right Document Preview Workspace (8 cols) */}
          <article className="lg:col-span-8 rounded-2xl border border-border/70 bg-card/95 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
            {/* Academic Header Banner */}
            <div className="border-b border-border/60 pb-5 mb-6 text-center space-y-2">
              <div className="flex items-center justify-between text-[9px] font-mono uppercase tracking-[0.2em] text-muted-foreground/80 border-b border-border/30 pb-2">
                <span>IEEE Transactions on Advanced Research Automation</span>
                <span>Vol. 14, No. 8</span>
              </div>

              <div className="pt-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-mono font-medium">
                  Artifact: {selectedPaper || query.trim() || "IEEE Report"}
                </span>
              </div>
            </div>

            {/* Two-Column IEEE Paper View */}
            {viewMode === "ieee" ? (
              <div className="space-y-6">
                {/* Full-width Title and Author Metadata Header */}
                {parsedIEEE.header ? (
                  <header className="w-full text-center space-y-2 pb-6 border-b border-border/40">
                    <h1 className="text-xl sm:text-2xl md:text-3xl font-serif font-bold text-foreground tracking-tight leading-tight max-w-4xl mx-auto">
                      {parsedIEEE.header.title}
                    </h1>
                    {parsedIEEE.header.authors && (
                      <p className="text-xs sm:text-sm font-serif font-medium text-foreground/90 max-w-3xl mx-auto pt-1">
                        {parsedIEEE.header.authors}
                      </p>
                    )}
                    {parsedIEEE.header.affiliation && (
                      <p className="text-[11px] sm:text-xs font-serif italic text-muted-foreground max-w-3xl mx-auto">
                        {parsedIEEE.header.affiliation}
                      </p>
                    )}
                    {parsedIEEE.header.correspondence && (
                      <p className="text-[10px] sm:text-[11px] font-mono text-muted-foreground/75">
                        {parsedIEEE.header.correspondence}
                      </p>
                    )}
                  </header>
                ) : null}

                <div className="md:columns-2 gap-8 [column-rule:1px_solid_rgba(148,163,184,0.2)] text-justify font-serif text-[12px] sm:text-[13px] leading-relaxed text-foreground/90 space-y-4">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ node, ...props }) => (
                        <h1
                          className="text-sm font-bold uppercase tracking-wider text-primary text-center mt-6 mb-2 border-b border-border/40 pb-1 break-inside-avoid"
                          {...props}
                        />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2
                          className="text-xs font-bold uppercase tracking-wider text-primary text-center mt-6 mb-2 border-b border-border/40 pb-1 break-inside-avoid"
                          {...props}
                        />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3
                          className="text-xs font-semibold italic text-foreground mt-4 mb-1.5 break-inside-avoid"
                          {...props}
                        />
                      ),
                      h4: ({ node, ...props }) => (
                        <h4
                          className="text-[11px] font-bold text-muted-foreground mt-3 mb-1 break-inside-avoid"
                          {...props}
                        />
                      ),
                      p: ({ node, children, ...props }: any) => {
                        const text = Array.isArray(children)
                          ? children.map((c) => (typeof c === "string" ? c : "")).join("")
                          : typeof children === "string"
                          ? children
                          : "";
                        const isRef = /^\[\d+\]/.test(text.trim());
                        if (isRef) {
                          return (
                            <p
                              className="pl-5 -indent-5 text-[11px] leading-snug text-foreground/85 my-1.5 break-inside-avoid font-serif"
                              {...props}
                            >
                              {children}
                            </p>
                          );
                        }
                        const isFig = /^\*?\*?(?:Fig\.|Figure)\s*\d+/i.test(text.trim());
                        if (isFig) {
                          return (
                            <p
                              className="text-center font-serif italic text-[11px] leading-snug text-muted-foreground my-2.5 break-inside-avoid"
                              {...props}
                            >
                              {children}
                            </p>
                          );
                        }
                        const isAbstract = /^\*?\*?Abstract\*?\*?[—–\-:]/i.test(text.trim());
                        const isIndexTerms = /^\*?\*?Index Terms\*?\*?[—–\-:]/i.test(text.trim());
                        if (isAbstract || isIndexTerms) {
                          return (
                            <p
                              className="text-justify italic font-serif leading-relaxed text-foreground/95 my-2.5 break-inside-avoid"
                              {...props}
                            >
                              {children}
                            </p>
                          );
                        }
                        return (
                          <p
                            className="indent-3 text-justify leading-relaxed text-foreground/90 my-2 font-serif"
                            {...props}
                          >
                            {children}
                          </p>
                        );
                      },
                      img: ({ node, src, alt, ...props }: any) => {
                        const imgSrc =
                          src && src.startsWith("/") && !src.startsWith("//")
                            ? `${API_BASE_URL}${src}`
                            : src;
                        return (
                          <span className="block my-3 break-inside-avoid text-center">
                            <img
                              src={imgSrc}
                              alt={alt || "System Architecture Diagram"}
                              className="w-full max-w-full rounded-md border border-border/60 shadow-sm bg-white p-1"
                              loading="lazy"
                              {...props}
                            />
                          </span>
                        );
                      },
                      ul: ({ node, ...props }) => (
                        <ul
                          className="list-disc pl-4 space-y-1 my-2 text-[12px] text-foreground/85 break-inside-avoid"
                          {...props}
                        />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol
                          className="list-decimal pl-4 space-y-1 my-2 text-[12px] text-foreground/85 break-inside-avoid"
                          {...props}
                        />
                      ),
                      li: ({ node, children, ...props }: any) => (
                        <li className="leading-snug pl-1 [&>p]:inline [&>p]:mb-0 [&>p]:leading-snug [&>p+p]:block [&>p+p]:mt-1" {...props}>
                          {children}
                        </li>
                      ),
                      blockquote: ({ node, ...props }) => (
                        <blockquote
                          className="border-l-2 border-primary/70 bg-secondary/30 py-2 px-3 rounded-r text-[12px] italic text-foreground/90 my-3 break-inside-avoid"
                          {...props}
                        />
                      ),
                      pre: ({ node, ...props }) => (
                        <pre
                          className="rounded-lg border border-border/60 bg-black/40 p-3 text-[10px] font-mono overflow-x-auto my-3 text-foreground/90 break-inside-avoid"
                          {...props}
                        />
                      ),
                      code: ({ node, ...props }) => (
                        <code
                          className="rounded bg-secondary/80 px-1 py-0.5 text-[11px] font-mono text-primary"
                          {...props}
                        />
                      ),
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-4 rounded border border-border/50 break-inside-avoid">
                          <table
                            className="w-full text-[10.5px] text-left border-collapse"
                            {...props}
                          />
                        </div>
                      ),
                      th: ({ node, ...props }) => (
                        <th
                          className="border-b border-border/60 bg-secondary/70 px-2.5 py-1.5 font-bold text-primary text-[10.5px]"
                          {...props}
                        />
                      ),
                      td: ({ node, ...props }) => (
                        <td
                          className="border-b border-border/30 px-2.5 py-1 text-foreground/85 text-[10px]"
                          {...props}
                        />
                      ),
                    }}
                  >
                    {parsedIEEE.body}
                  </ReactMarkdown>
                </div>
              </div>
            ) : (
              /* Single-Column Standard Article View */
              <div className="text-sm leading-relaxed text-foreground/90 space-y-5 font-sans">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => (
                      <h1
                        className="text-lg font-serif font-bold text-foreground border-b border-border/50 pb-2 mt-8 mb-3"
                        {...props}
                      />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2
                        className="text-base font-serif font-bold text-primary border-b border-border/30 pb-1.5 mt-7 mb-2 tracking-wide"
                        {...props}
                      />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3
                        className="text-sm font-semibold text-foreground mt-5 mb-2 uppercase tracking-wider"
                        {...props}
                      />
                    ),
                    h4: ({ node, ...props }) => (
                      <h4
                        className="text-xs font-bold text-muted-foreground mt-4 mb-1.5"
                        {...props}
                      />
                    ),
                    p: ({ node, children, ...props }: any) => {
                      const text = Array.isArray(children)
                        ? children.map((c) => (typeof c === "string" ? c : "")).join("")
                        : typeof children === "string"
                        ? children
                        : "";
                      const isFig = /^\*?\*?(?:Fig\.|Figure)\s*\d+/i.test(text.trim());
                      if (isFig) {
                        return (
                          <p
                            className="text-center font-serif italic text-xs leading-normal text-muted-foreground my-2.5"
                            {...props}
                          >
                            {children}
                          </p>
                        );
                      }
                      return <p className="leading-7 text-foreground/85 text-xs sm:text-sm" {...props}>{children}</p>;
                    },
                    img: ({ node, src, alt, ...props }: any) => {
                      const imgSrc =
                        src && src.startsWith("/") && !src.startsWith("//")
                          ? `${API_BASE_URL}${src}`
                          : src;
                      return (
                        <span className="block my-5 text-center">
                          <img
                            src={imgSrc}
                            alt={alt || "System Architecture Diagram"}
                            className="w-full max-w-2xl mx-auto rounded-xl border border-border/60 shadow-md bg-white p-2"
                            loading="lazy"
                            {...props}
                          />
                        </span>
                      );
                    },
                    ul: ({ node, ...props }) => (
                      <ul
                        className="list-disc pl-5 space-y-1.5 text-xs sm:text-sm text-foreground/80 my-3"
                        {...props}
                      />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol
                        className="list-decimal pl-5 space-y-1.5 text-xs sm:text-sm text-foreground/80 my-3"
                        {...props}
                      />
                    ),
                    li: ({ node, children, ...props }: any) => (
                      <li className="leading-relaxed pl-1 [&>p]:inline [&>p]:mb-0 [&>p]:leading-relaxed [&>p+p]:block [&>p+p]:mt-1" {...props}>
                        {children}
                      </li>
                    ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote
                        className="border-l-2 border-primary/70 bg-secondary/30 py-3 px-4 rounded-r-xl text-xs sm:text-sm italic text-foreground/90 my-4 shadow-sm"
                        {...props}
                      />
                    ),
                    pre: ({ node, ...props }) => (
                      <pre
                        className="rounded-xl border border-border/60 bg-black/40 p-4 text-xs font-mono overflow-x-auto my-4 text-foreground/90"
                        {...props}
                      />
                    ),
                    code: ({ node, ...props }) => (
                      <code
                        className="rounded bg-secondary/80 px-1.5 py-0.5 text-xs font-mono text-primary"
                        {...props}
                      />
                    ),
                    table: ({ node, ...props }) => (
                      <div className="overflow-x-auto my-6 rounded-xl border border-border/50">
                        <table
                          className="w-full text-xs text-left border-collapse"
                          {...props}
                        />
                      </div>
                    ),
                    th: ({ node, ...props }) => (
                      <th
                        className="border-b border-border/60 bg-secondary/70 px-3.5 py-2.5 text-xs font-bold text-primary"
                        {...props}
                      />
                    ),
                    td: ({ node, ...props }) => (
                      <td
                        className="border-b border-border/30 px-3.5 py-2 text-xs text-foreground/80"
                        {...props}
                      />
                    ),
                  }}
                >
                  {report}
                </ReactMarkdown>
              </div>
            )}
          </article>

          {/* Scholarly Accuracy & Factuality Evaluation Card */}
          <div className="lg:col-span-12">
            <AgentEvaluationCard
              agentName="report"
              agentTitle="IEEE Report Agent"
              outputText={report}
              paperName={selectedPaper}
              query={query}
            />
          </div>
        </div>
      )}

    </div>
  );
}

export default ReportPage;