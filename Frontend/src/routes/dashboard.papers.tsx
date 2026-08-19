import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Search,
  Bookmark,
  ExternalLink,
  Sparkles,
  Award,
  Calendar,
  Layers,
  Lightbulb,
  CheckCircle2,
  Copy,
  ArrowUpDown,
  BookOpen,
} from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { searchResearchPapers, runAnalysis, ResearchPaper } from "@/lib/api";
import { useSearch, useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/papers")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [{ title: "Paper Search & Year-wise Discovery — ResearchX" }],
  }),
  component: PaperSearch,
});

const PRESET_TOPICS = [
  "Retrieval Augmented Generation",
  "Vision Transformers",
  "Graph Neural Networks",
  "Chain-of-Thought Reasoning",
  "Diffusion Models",
  "Medical Image Segmentation",
];

const YEAR_TABS = [
  { id: "all", label: "All Years" },
  { id: "2025", label: "2025-2026" },
  { id: "2024", label: "2024" },
  { id: "2023", label: "2023" },
  { id: "2022", label: "2022" },
  { id: "foundational", label: "Foundational (≤2021)" },
];

const SORT_OPTIONS = [
  { id: "year_desc", label: "Chronological (Latest First)" },
  { id: "citations_desc", label: "Most Cited / Landmark Impact" },
  { id: "year_asc", label: "Evolution Timeline (Oldest First)" },
];

function PaperSearch() {
  const search = useSearch({ from: "/dashboard/papers" });
  const navigate = useNavigate();

  const [q, setQ] = useState(search.paper ?? "Retrieval Augmented Generation");
  const [activeQuery, setActiveQuery] = useState(search.paper ?? "Retrieval Augmented Generation");
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [selectedYear, setSelectedYear] = useState("all");
  const [sortBy, setSortBy] = useState("year_desc");
  const [loading, setLoading] = useState(false);
  const [loadingPaper, setLoadingPaper] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (search.paper) {
      setQ(search.paper);
      setActiveQuery(search.paper);
    }
  }, [search.paper]);

  // Execute deterministic search
  useEffect(() => {
    if (!activeQuery.trim()) {
      setPapers([]);
      return;
    }

    let isMounted = true;

    async function loadPapers() {
      try {
        setLoading(true);
        setError("");
        const data = await searchResearchPapers(activeQuery, sortBy, selectedYear);
        if (isMounted) {
          setPapers(data.results || []);
        }
      } catch (err) {
        if (isMounted) {
          console.error(err);
          setError(err instanceof Error ? err.message : "Failed to search papers");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadPapers();

    return () => {
      isMounted = false;
    };
  }, [activeQuery, sortBy, selectedYear]);

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (q.trim()) {
      setActiveQuery(q.trim());
    }
  };

  const handlePresetClick = (topic: string) => {
    setQ(topic);
    setActiveQuery(topic);
  };

  const handleSummary = async (paperTitle: string) => {
    try {
      setLoadingPaper(paperTitle);
      await runAnalysis(paperTitle, "summary");
      navigate({
        to: "/dashboard/summary",
        search: {
          paper: paperTitle,
        },
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPaper(null);
    }
  };

  const handleCopyCitation = async (paper: ResearchPaper) => {
    const authorsText = Array.isArray(paper.authors)
      ? paper.authors.join(", ")
      : paper.authors || "Authors";
    const citation = `${authorsText} (${paper.year || paper.published || "2024"}). "${paper.title}". ${paper.venue || "Academic Proceedings"}.`;

    try {
      await navigator.clipboard.writeText(citation);
      setCopiedId(paper.id || paper.title);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error("Failed to copy citation", err);
    }
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Year-Wise Academic Paper Discovery"
        subtitle="Authoritative landmark papers and latest preprints with verified relevance rationales."
      />

      {/* Search Header Bar */}
      <div className="rounded-2xl glass p-5 space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col gap-3 md:flex-row md:items-center">
          <div className="flex flex-1 items-center gap-2.5 rounded-xl border border-border/60 bg-secondary/40 px-3.5 py-1.5 focus-within:ring-2 focus-within:ring-primary/40">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search research papers, topics, methods (e.g. Graph Neural Networks, RAG)..."
              className="border-0 bg-transparent p-0 text-sm focus-visible:ring-0 shadow-none placeholder:text-muted-foreground/60"
            />
          </div>

          <Button type="submit" variant="hero" disabled={loading || !q.trim()} className="gap-2 min-w-[140px]">
            <Sparkles className="h-4 w-4" />
            {loading ? "Searching..." : "Search Papers"}
          </Button>
        </form>

        {/* Preset Topic Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-border/40">
          <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            Topics:
          </span>
          {PRESET_TOPICS.map((topic) => (
            <button
              key={topic}
              type="button"
              onClick={() => handlePresetClick(topic)}
              className={`rounded-lg border px-2.5 py-1 text-xs transition-colors ${
                activeQuery.toLowerCase() === topic.toLowerCase()
                  ? "border-primary bg-primary/10 text-primary font-medium"
                  : "border-border/40 bg-secondary/30 text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              {topic}
            </button>
          ))}
        </div>
      </div>

      {/* Year-Wise Filter Tabs & Sorting Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl glass p-4">
        {/* Year Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          <div className="flex items-center gap-1 text-xs text-muted-foreground mr-1.5 font-medium">
            <Calendar className="h-3.5 w-3.5" />
            Year:
          </div>
          {YEAR_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setSelectedYear(tab.id)}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition-all ${
                selectedYear === tab.id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-secondary/40 text-muted-foreground hover:bg-secondary hover:text-foreground border border-border/40"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground font-medium">
            <ArrowUpDown className="h-3.5 w-3.5" />
            Sort:
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            disabled={loading}
            className="rounded-xl border border-border/60 bg-secondary/40 px-3 py-1.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="rounded-2xl glass p-10 text-center space-y-3">
          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-primary" />
          <h3 className="text-base font-semibold">Indexing Year-Wise Research Papers</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Retrieving landmark peer-reviewed publications and verified preprints for &apos;{activeQuery}&apos;...
          </p>
        </div>
      )}

      {/* Paper Results List */}
      {!loading && papers.length === 0 && !error && (
        <div className="rounded-2xl glass p-10 text-center space-y-3">
          <Layers className="mx-auto h-10 w-10 text-muted-foreground/60" />
          <h3 className="text-base font-semibold">No Research Papers Found</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Try adjusting your search query or selecting &apos;All Years&apos; to view foundational milestones.
          </p>
        </div>
      )}

      {!loading && papers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span>
              Showing <strong className="text-foreground font-semibold">{papers.length}</strong> papers for &apos;{activeQuery}&apos;
            </span>
            <span>Deterministic Year-Wise Order</span>
          </div>

          {papers.map((p, idx) => {
            const authorsDisplay = Array.isArray(p.authors)
              ? p.authors.join(", ")
              : p.authors || "Primary Investigators";

            const yearDisplay = p.year || p.published || "2024";
            const citationCount = p.citations ?? p.citation_count ?? 0;
            const whyChosen = p.why_chosen || p.relevance_reason || p.key_contribution;

            return (
              <div
                key={p.id || `${p.title}-${idx}`}
                className="rounded-2xl glass p-6 transition-all duration-200 hover:border-primary/40 space-y-4 relative group"
              >
                {/* Header: Title & Badges */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {/* Year Badge */}
                      <span className="inline-flex items-center gap-1 rounded-md bg-primary/15 border border-primary/30 px-2 py-0.5 text-xs font-bold text-primary">
                        <Calendar className="h-3 w-3" />
                        {yearDisplay}
                      </span>

                      {/* Venue Badge */}
                      <span className="rounded-md bg-secondary/80 border border-border/60 px-2 py-0.5 text-xs font-medium text-foreground">
                        {p.venue || "Academic Venue"}
                      </span>

                      {/* Citations Badge */}
                      {citationCount > 0 && (
                        <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 text-xs font-semibold text-amber-400">
                          <Award className="h-3 w-3" />
                          {citationCount.toLocaleString()} Citations
                        </span>
                      )}

                      {/* Relevance Badge */}
                      {p.relevance_badge && (
                        <span className="rounded-md bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-xs font-medium text-emerald-400">
                          {p.relevance_badge}
                        </span>
                      )}
                    </div>

                    <h3 className="text-base font-bold text-foreground leading-snug">
                      {p.title}
                    </h3>

                    <p className="text-xs text-muted-foreground">
                      {authorsDisplay}
                    </p>
                  </div>
                </div>

                {/* Explicit "Why This Paper is Recommended & Showing" Callout */}
                {whyChosen && (
                  <div className="rounded-xl border border-primary/25 bg-primary/5 p-3.5 text-xs leading-relaxed space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold text-primary">
                      <Lightbulb className="h-3.5 w-3.5" />
                      <span>Why This Paper is Recommended &amp; Showing:</span>
                    </div>
                    <p className="text-foreground/90 pl-5">
                      {whyChosen}
                    </p>
                  </div>
                )}

                {/* Abstract Text */}
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                  {p.abstract || p.summary || "Technical abstract available."}
                </p>

                {/* Actions Footer */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/40">
                  <div className="flex items-center gap-2">
                    {p.key_contribution && (
                      <span className="text-[11px] text-muted-foreground/80 italic line-clamp-1">
                        Breakthrough: {p.key_contribution}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyCitation(p)}
                      className="h-8 gap-1.5 text-xs"
                    >
                      {copiedId === (p.id || p.title) ? (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          <span>Cite</span>
                        </>
                      )}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={loadingPaper === p.title}
                      onClick={() => handleSummary(p.title)}
                      className="h-8 gap-1.5 text-xs"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      {loadingPaper === p.title ? "Analyzing..." : "Summarize"}
                    </Button>

                    <Button
                      variant="glass"
                      size="sm"
                      onClick={() =>
                        window.open(
                          p.pdf_url || p.url || `https://scholar.google.com/scholar?q=${encodeURIComponent(p.title)}`,
                          "_blank"
                        )
                      }
                      className="h-8 gap-1.5 text-xs"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      View Paper
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}