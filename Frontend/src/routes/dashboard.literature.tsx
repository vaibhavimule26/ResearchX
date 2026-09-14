import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
  Check,
  Search,
  FileText,
  Filter,
  ArrowRight,
  Database,
  Lightbulb,
  FlaskConical,
  FileSpreadsheet,
  Quote,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { PaperSelectorCard } from "@/components/dashboard/paper-selector-card";
import { AIProcessingCard } from "@/components/dashboard/ai-processing-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { ErrorState } from "@/components/dashboard/error-state";
import { getPapers, runAnalysis, uploadPaper } from "@/lib/api";

export const Route = createFileRoute("/dashboard/literature")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
    topic: typeof search.topic === "string" ? search.topic : "",
  }),
  head: () => ({
    meta: [{ title: "Literature Survey Workspace — ResearchX" }],
  }),
  component: LiteratureSurveyPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

const SUGGESTED_TOPICS = [
  "Core Methodology & Technical Architecture",
  "Empirical Baselines & Benchmark Comparison",
  "Theoretical Foundations & Problem Scope",
  "Research Gaps & Future Directions",
];

const LITERATURE_STAGES = [
  {
    title: "Ingesting Corpus & Normalizing Citations",
    description: "Parsing document structure, citations, and taxonomies...",
  },
  {
    title: "Cross-Referencing Methodologies & Baselines",
    description: "Evaluating algorithmic lineage and architectural predecessors...",
  },
  {
    title: "Synthesizing Empirical Benchmarks & Datasets",
    description: "Organizing comparative metric tables and evaluation setups...",
  },
  {
    title: "Formatting Scholarly Literature Review",
    description: "Drafting peer-review-style literature review with critical analysis...",
  },
];

// Cleanly unwrap Markdown content while preserving all headings, lists, and tables
function extractMarkdown(raw: unknown): string {
  if (!raw) return "";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.results?.literature_survey?.output ||
      obj?.results?.literature?.output ||
      obj?.output ||
      obj?.data?.answer ||
      obj?.answer ||
      obj?.result ||
      "";

    if (!text && obj?.results && typeof obj.results === "object") {
      const first = Object.values(obj.results)[0] as any;
      if (first?.output) text = first.output;
      else if (first?.result) text = first.result;
    }
  } else if (typeof raw === "string") {
    const trimmed = raw.trim();
    try {
      const parsed = JSON.parse(trimmed);
      return extractMarkdown(parsed);
    } catch {
      const match = trimmed.match(
        /['"]output['"]\s*:\s*['"]([\s\S]*?)['"]\s*(?:,\s*['"]|\})/
      );
      text = match && match[1] ? match[1] : trimmed;
    }
  } else {
    text = String(raw);
  }

  return text
    .replace(/\\r\\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "")
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\0/g, "")
    .replace(/\ufffd/g, "—")
    .trim();
}

function LiteratureSurveyPage() {
  const search = useSearch({ from: "/dashboard/literature" });

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState(search.paper || "");
  const [topic, setTopic] = useState(search.topic || "");
  const [activeTopic, setActiveTopic] = useState("");
  const [survey, setSurvey] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const loadPapersList = async (preferFilename?: string) => {
    try {
      setLoadingPapers(true);
      setError("");

      const response = await getPapers();
      const uploadedPapers: Paper[] = response?.data?.papers || [];
      setPapers(uploadedPapers);

      if (preferFilename) {
        setSelectedPaper(preferFilename);
      } else if (search.paper) {
        const found = uploadedPapers.find(
          (p) => p.filename.toLowerCase() === search.paper.toLowerCase()
        );
        setSelectedPaper(found ? found.filename : search.paper);
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

  useEffect(() => {
    loadPapersList();
  }, [search.paper]);

  // If paper was provided in query param and selected, auto-run
  useEffect(() => {
    if (search.paper && !survey && !loading) {
      generateSurvey(search.paper, search.topic);
    }
  }, [search.paper]);

  const generateSurvey = async (targetPaper?: string, targetTopic?: string) => {
    const paperToUse = targetPaper || selectedPaper;
    if (!paperToUse || loading) return;

    const topicToUse = typeof targetTopic === "string" ? targetTopic : topic;

    try {
      setLoading(true);
      setError("");
      setSurvey("");
      setActiveTopic(topicToUse || "");

      const response = await runAnalysis(
        paperToUse,
        "literature",
        topicToUse ? topicToUse.trim() : undefined
      );

      const rawResult =
        (response as any)?.result ??
        (response as any)?.data ??
        response;

      if (!rawResult) {
        throw new Error("No literature survey received from backend");
      }

      setSurvey(extractMarkdown(rawResult));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Literature survey generation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copySurvey = async () => {
    if (!survey) return;
    try {
      await navigator.clipboard.writeText(survey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy literature survey");
    }
  };

  const downloadSurvey = () => {
    if (!survey) return;

    const header = [
      "ResearchX — Academic Literature Survey",
      "=".repeat(60),
      `Paper: ${selectedPaper}`,
      activeTopic ? `Focus: ${activeTopic}` : "Focus: Complete Comprehensive Survey",
      `Generated: ${new Date().toISOString()}`,
      "=".repeat(60),
      "",
      survey,
    ].join("\n");

    const blob = new Blob([header], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename || "paper"}-literature-survey.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  // Client-side text filter over existing survey output
  const displayedSurvey = searchTerm.trim()
    ? survey
        .split("\n\n")
        .filter((block) =>
          block.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .join("\n\n")
    : survey;

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Literature Survey Workspace"
        subtitle={
          selectedPaper
            ? `Comprehensive scholarly literature review, taxonomy classification, and benchmark comparison for '${selectedPaper}'.`
            : "Select an uploaded research paper to synthesize related academic literature."
        }
        action={
          survey ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copySurvey}
                disabled={!survey || loading}
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
                    <span>Copy Survey</span>
                  </>
                )}
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={downloadSurvey}
                disabled={!survey || loading}
                className="h-8 text-xs gap-1.5 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export Markdown</span>
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
          setSurvey("");
          setError("");
        }}
        loading={loading}
        loadingPapers={loadingPapers}
        subtitle="The Literature Survey Agent extracts taxonomic trees and comparative baselines."
        actionButton={
          <Button
            variant="hero"
            size="sm"
            onClick={() => generateSurvey()}
            disabled={loading || loadingPapers || !selectedPaper}
            className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>{loading ? "Synthesizing..." : "Run Literature Survey"}</span>
          </Button>
        }
      />

      {/* Focus Topic Bar with Quick Chips */}
      <div className="rounded-2xl border border-border/50 bg-secondary/20 p-3.5 backdrop-blur-md space-y-2">
        <div className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-primary" />
          <span className="text-xs font-semibold text-foreground">
            Optional Survey Focus / Research Aspect:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {SUGGESTED_TOPICS.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setTopic(item);
                generateSurvey(selectedPaper, item);
              }}
              disabled={loading}
              className={`rounded-lg border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                topic === item
                  ? "bg-primary/20 text-primary border-primary/40 font-semibold"
                  : "border-border/40 bg-secondary/40 text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
              }`}
            >
              {item}
            </button>
          ))}
          {topic && (
            <button
              type="button"
              onClick={() => setTopic("")}
              className="text-[11px] text-muted-foreground hover:text-destructive px-2 py-1"
            >
              Clear filter
            </button>
          )}
        </div>
      </div>

      {error && (
        <ErrorState
          title="Literature Survey Failed"
          error={error}
          onRetry={() => generateSurvey()}
        />
      )}

      {/* Multi-Stage AI Loading Component */}
      {loading && (
        <AIProcessingCard
          agentName="LITERATURE SYNTHESIS SPECIALIST"
          title={`Synthesizing academic literature for ${selectedPaper}`}
          stages={LITERATURE_STAGES}
          className="mt-6"
        />
      )}

      {/* Empty State before Running */}
      {!loading && !survey && !error && (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3">
              <BookOpen className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Taxonomy Classification
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Maps algorithmic families, theoretical lineages, and paradigms across peer-reviewed literature.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 border border-primary/20 text-primary mb-3">
              <Quote className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Citation Synthesis
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Analyzes core citations, comparative baseline setups, and benchmark empirical performance.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
              <Sparkles className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Critical Gap Identification
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Identifies overlooked research trajectories across surveyed literature for immediate thesis integration.
            </p>
          </div>
        </div>
      )}

      {/* Survey Results Layout */}
      {survey && !loading && (
        <div className="grid gap-6 lg:grid-cols-12 items-start">
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-2xl border border-border/50 bg-card/80 p-6 sm:p-8 backdrop-blur-xl shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border/40 pb-4 mb-6 gap-3">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-sm">
                    <BookOpen className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">
                      Synthesized Literature Survey
                    </h3>
                    <p className="text-xs text-muted-foreground truncate max-w-md">
                      {selectedPaper}
                      {activeTopic ? ` • Focus: ${activeTopic}` : ""}
                    </p>
                  </div>
                </div>

                {/* In-survey search bar */}
                <div className="relative max-w-xs w-full">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search in survey..."
                    className="w-full h-8 rounded-xl border border-border/60 bg-secondary/40 pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50"
                  />
                </div>
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
                        className="text-sm font-bold text-blue-400 mt-5 mb-1.5 flex items-center gap-2"
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
                        className="border-l-2 border-blue-500/60 bg-secondary/30 py-2 px-3 rounded-r-xl text-xs italic text-muted-foreground my-3"
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
                        className="border-b border-border/60 bg-secondary/60 px-3 py-2 text-xs font-semibold text-blue-400"
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
                  {displayedSurvey}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Context & Next Research Steps */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 via-card/80 to-background p-5 backdrop-blur-md shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <div className="grid h-7 w-7 place-items-center rounded-lg bg-blue-500/20 text-blue-400">
                  <BookOpen className="h-4 w-4" />
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400">
                  Literature Synthesis Metrics
                </h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Scholarly standards embedded in this survey:
              </p>
              <ul className="space-y-1.5 text-xs text-foreground/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
                  <span>Comprehensive architectural taxonomy</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
                  <span>Cross-paper empirical baseline tables</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
                  <span>Formal IEEE/ACM citation structure</span>
                </li>
              </ul>
            </div>

            <div className="rounded-2xl border border-border/50 bg-secondary/20 p-5 backdrop-blur-md shadow-sm space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Next Research Steps
              </h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Advance this literature survey into subsequent research phases:
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
                      Extract Research Gaps
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
                      Generate IEEE Report
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

export default LiteratureSurveyPage;