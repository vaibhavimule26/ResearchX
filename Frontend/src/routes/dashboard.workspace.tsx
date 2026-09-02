import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Search,
  Sparkles,
  Paperclip,
  FileText,
  Lightbulb,
  HelpCircle,
  Bot,
  Database,
  FlaskConical,
  Scale,
  ShieldCheck,
  BookOpen,
  Trash2,
  Plus,
  CheckCircle2,
  Clock,
  ArrowRight,
  Copy,
  Check,
  Filter,
  ExternalLink,
  Layers,
  Play,
  RotateCcw,
  Tag,
  Calendar,
  Award,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  searchResearchPapers,
  runAllWorkspaceAgents,
  deleteWorkspaceSession,
  ResearchPaper,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/workspace")({
  head: () => ({ meta: [{ title: "AI Workspace — ResearchX" }] }),
  component: WorkspacePage,
});

interface AgentDef {
  name: string;
  key: string;
  icon: any;
  description: string;
}

const WORKSPACE_AGENT_DEFS: AgentDef[] = [
  {
    name: "Summary",
    key: "summary",
    icon: FileText,
    description: "Factual executive synthesis, snapshot, and core takeaways",
  },
  {
    name: "Literature Survey",
    key: "literature",
    icon: BookOpen,
    description: "Structured taxonomic literature matrix table across all papers",
  },
  {
    name: "Research Gap",
    key: "gaps",
    icon: Lightbulb,
    description: "Evidence-backed research gap and limitation breakdown table",
  },
  {
    name: "Novelty Analysis",
    key: "novelty",
    icon: ShieldCheck,
    description: "Novelty assessment matrix, claimed innovations & differentiators",
  },
  {
    name: "Dataset Recommendation",
    key: "datasets",
    icon: Database,
    description: "Identifies and recommends relevant datasets based on problem statement, objectives, and experimental requirements",
  },
  {
    name: "Experiment Recommendation",
    key: "experiments",
    icon: FlaskConical,
    description: "Recommends appropriate experiments and evaluation techniques to investigate, validate, and evaluate the proposed approach",
  },
  {
    name: "Comparative Analysis",
    key: "comparison",
    icon: Scale,
    description: "Comprehensive cross-paper comparative evaluation matrix table",
  },
];

function WorkspacePage() {
  const [prompt, setPrompt] = useState("");
  const [originalQuery, setOriginalQuery] = useState("");
  const [correctedQuery, setCorrectedQuery] = useState("");
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState("all");
  const [selectedSource, setSelectedSource] = useState("all");
  const [sortBy, setSortBy] = useState("relevance");

  const [sessionId, setSessionId] = useState("");
  const [activeSessionId, setActiveSessionId] = useState("");
  const [agentResults, setAgentResults] = useState<Record<string, any>>({});
  const [agents, setAgents] = useState<any[]>(
    WORKSPACE_AGENT_DEFS.map((def) => ({
      agent: def.name,
      key: def.key,
      status: "Pending",
      progress: 0,
    }))
  );

  const [recentResearch, setRecentResearch] = useState<any[]>([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [runningAll, setRunningAll] = useState(false);
  const [runningAgentKey, setRunningAgentKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [activeAgentTab, setActiveAgentTab] = useState<string>("summary");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadRecentResearch = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/analysis/recent");
      if (!response.ok) {
        setRecentResearch([]);
        return;
      }
      const data = await response.json();
      setRecentResearch(Array.isArray(data?.data) ? data.data : []);
    } catch (error) {
      console.error("Failed to load recent research:", error);
      setRecentResearch([]);
    }
  };

  useEffect(() => {
    loadRecentResearch();
  }, []);

  // ----------------------------------------------------
  // Paper Selection Handlers
  // ----------------------------------------------------
  const togglePaperSelection = (index: number) => {
    setSelectedPapers((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const handleSelectAllPapers = () => {
    if (selectedPapers.length === papers.length) {
      setSelectedPapers([]);
    } else {
      setSelectedPapers(papers.map((_, i) => i));
    }
  };

  // ----------------------------------------------------
  // Paper Search with Autocorrect & Filtering
  // ----------------------------------------------------
  const handleSearchPapers = async (overrideQuery?: string) => {
    const queryToSearch = (overrideQuery || prompt).trim();
    if (!queryToSearch) {
      alert("Please enter a research topic or query.");
      return;
    }

    try {
      setLoadingSearch(true);
      setOriginalQuery(queryToSearch);

      const data = await searchResearchPapers(
        queryToSearch,
        sortBy,
        selectedYear,
        selectedSource
      );

      const results = data.results || [];
      setPapers(results);

      // Select top 3-5 papers by default
      const defaultSelected = results.slice(0, Math.min(results.length, 5)).map((_, i) => i);
      setSelectedPapers(defaultSelected);

      if (data.corrected_query && data.corrected_query.trim().toLowerCase() !== queryToSearch.toLowerCase()) {
        setCorrectedQuery(data.corrected_query.trim());
      } else {
        setCorrectedQuery("");
      }
    } catch (error) {
      console.error("Search failed:", error);
      alert("Failed to search papers. Please verify your connection.");
    } finally {
      setLoadingSearch(false);
    }
  };

  // ----------------------------------------------------
  // Run All AI Agents Smoothly
  // ----------------------------------------------------
  const handleRunAllAgents = async () => {
    if (!prompt.trim()) {
      alert("Please enter a research topic.");
      return;
    }

    if (selectedPapers.length === 0) {
      alert("Please select at least one research paper.");
      return;
    }

    try {
      setRunningAll(true);
      const currentSessionId = sessionId || `session_${Date.now()}`;
      setSessionId(currentSessionId);
      setActiveSessionId(currentSessionId);

      const chosenPapers = selectedPapers.map((idx) => {
        const p = papers[idx];
        return {
          title: p.title || "Untitled Paper",
          paper_name: p.title || "Untitled Paper",
          authors: Array.isArray(p.authors) ? p.authors.join(", ") : p.authors || "",
          summary: p.summary || p.abstract || "",
          abstract: p.abstract || p.summary || "",
          published: p.published || (p.year ? String(p.year) : ""),
          pdf_url: p.pdf_url || p.url || "",
          url: p.url || p.pdf_url || "",
          source: p.source || "",
          venue: p.venue || "",
          why_chosen: p.why_chosen || "",
          key_contribution: p.key_contribution || "",
          citations: p.citations || p.citation_count || 0,
        };
      });

      // Mark all agents as Running in UI
      setAgents((prev) =>
        prev.map((a) => ({
          ...a,
          status: "Running",
          progress: 40,
        }))
      );

      const data = await runAllWorkspaceAgents(
        prompt.trim(),
        currentSessionId,
        chosenPapers
      );

      if (data.agent_results) {
        setAgentResults(data.agent_results);
      }

      setAgents((prev) =>
        prev.map((a) => ({
          ...a,
          status: "Completed",
          progress: 100,
        }))
      );

      await loadRecentResearch();
    } catch (error) {
      console.error("Run All Agents Error:", error);
      alert("Error running AI Research. Please check backend status.");
      setAgents((prev) =>
        prev.map((a) => ({
          ...a,
          status: a.status === "Completed" ? "Completed" : "Pending",
          progress: a.status === "Completed" ? 100 : 0,
        }))
      );
    } finally {
      setRunningAll(false);
    }
  };

  // ----------------------------------------------------
  // Run Individual Agent
  // ----------------------------------------------------
  const handleRunSingleAgent = async (agentDef: AgentDef) => {
    if (selectedPapers.length === 0) {
      alert("Please select at least one paper.");
      return;
    }

    const currentSessionId = sessionId || `session_${Date.now()}`;
    setSessionId(currentSessionId);
    setActiveSessionId(currentSessionId);

    const chosenPapers = selectedPapers.map((idx) => {
      const p = papers[idx];
      return {
        title: p.title || "Untitled Paper",
        paper_name: p.title || "Untitled Paper",
        authors: Array.isArray(p.authors) ? p.authors.join(", ") : p.authors || "",
        summary: p.summary || p.abstract || "",
        abstract: p.abstract || p.summary || "",
        published: p.published || (p.year ? String(p.year) : ""),
        pdf_url: p.pdf_url || p.url || "",
        url: p.url || p.pdf_url || "",
        source: p.source || "",
        venue: p.venue || "",
        why_chosen: p.why_chosen || "",
        key_contribution: p.key_contribution || "",
        citations: p.citations || p.citation_count || 0,
      };
    });

    try {
      setRunningAgentKey(agentDef.key);

      setAgents((prev) =>
        prev.map((a) =>
          a.key === agentDef.key ? { ...a, status: "Running", progress: 50 } : a
        )
      );

      const response = await fetch("http://127.0.0.1:8000/analysis/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          papers: chosenPapers,
          query: prompt,
          analysis_type: agentDef.key,
          session_id: currentSessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to run ${agentDef.name}`);
      }

      const data = await response.json();
      const resultPayload = data.results !== undefined ? data.results : data.result || data.data;

      setAgentResults((prev) => ({
        ...prev,
        [agentDef.key]: resultPayload,
      }));

      setAgents((prev) =>
        prev.map((a) =>
          a.key === agentDef.key ? { ...a, status: "Completed", progress: 100 } : a
        )
      );

      setActiveAgentTab(agentDef.key);
      await loadRecentResearch();
    } catch (err) {
      console.error(err);
      alert(`Error running ${agentDef.name}`);
      setAgents((prev) =>
        prev.map((a) =>
          a.key === agentDef.key ? { ...a, status: "Pending", progress: 0 } : a
        )
      );
    } finally {
      setRunningAgentKey(null);
    }
  };

  // ----------------------------------------------------
  // Restore Past Research Session
  // ----------------------------------------------------
  const handleLoadWorkspace = async (sessId: string) => {
    try {
      setLoadingSearch(true);
      const response = await fetch(`http://127.0.0.1:8000/analysis/workspace/${sessId}`);
      const data = await response.json();

      if (!data.success) {
        alert("Failed to restore workspace session.");
        return;
      }

      setPrompt(data.topic || "");
      setSessionId(data.session_id);
      setActiveSessionId(data.session_id);

      const restoredPapers = data.papers || [];
      setPapers(restoredPapers);
      setSelectedPapers(restoredPapers.map((_: any, i: number) => i));

      const restoredResults = data.agent_results || {};
      setAgentResults(restoredResults);

      const restoredAgents = WORKSPACE_AGENT_DEFS.map((def) => {
        const res = restoredResults[def.key];
        const isDone = res && (Array.isArray(res) ? res.length > 0 : Boolean(res));
        return {
          agent: def.name,
          key: def.key,
          status: isDone ? "Completed" : "Pending",
          progress: isDone ? 100 : 0,
        };
      });
      setAgents(restoredAgents);

      // Find first completed agent to set as active tab
      const firstDone = WORKSPACE_AGENT_DEFS.find((d) => restoredResults[d.key]);
      if (firstDone) {
        setActiveAgentTab(firstDone.key);
      }
    } catch (err) {
      console.error("Workspace restore error:", err);
      alert("Failed to restore research session.");
    } finally {
      setLoadingSearch(false);
    }
  };

  // ----------------------------------------------------
  // Delete Session
  // ----------------------------------------------------
  const handleDeleteSession = async (e: React.MouseEvent, sessId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this research session?")) return;

    try {
      await deleteWorkspaceSession(sessId);
      if (activeSessionId === sessId) {
        handleStartNewResearch();
      }
      await loadRecentResearch();
    } catch (err) {
      console.error("Delete session error:", err);
    }
  };

  // ----------------------------------------------------
  // Start New Clean Research
  // ----------------------------------------------------
  const handleStartNewResearch = () => {
    setPrompt("");
    setOriginalQuery("");
    setCorrectedQuery("");
    setPapers([]);
    setSelectedPapers([]);
    setSessionId("");
    setActiveSessionId("");
    setAgentResults({});
    setAgents(
      WORKSPACE_AGENT_DEFS.map((def) => ({
        agent: def.name,
        key: def.key,
        status: "Pending",
        progress: 0,
      }))
    );
  };

  const handleCopyResult = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleAttachPDF = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload/pdf", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (data.success) {
        alert("PDF uploaded and indexed into research knowledge graph.");
        if (data.filename && !prompt) {
          setPrompt(data.filename.replace(/\.pdf$/i, ""));
        }
      } else {
        alert("Upload failed.");
      }
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0 space-y-6">
        {/* Workspace Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              <span>AI Research Workspace</span>
            </div>
            <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
              Autonomous Academic Research
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Search IEEE & global academic literature, dispatch specialized AI agents, and generate structured research matrices.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleStartNewResearch}
            className="flex items-center gap-1.5 border-border/50 text-xs hover:bg-secondary/50"
          >
            <Plus className="h-3.5 w-3.5" />
            New Research
          </Button>
        </div>

        {/* Search & Prompt Box */}
        <div className="rounded-3xl glass-strong p-5 shadow-lg border border-border/40">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSearchPapers();
              }
            }}
            placeholder="Enter a research topic, sentence query, or keywords… e.g. 'Recent advances in vision-language models for chest X-ray diagnosis from IEEE and arXiv'"
            rows={3}
            className="resize-none border-0 bg-transparent text-base focus-visible:ring-0 placeholder:text-muted-foreground/60"
          />

          {/* Autocorrect Notice Badge */}
          {correctedQuery && (
            <div className="mt-2 flex items-center justify-between rounded-xl bg-primary/10 px-3 py-2 text-xs text-primary border border-primary/20">
              <div className="flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                <span>
                  Showing results for: <strong>"{correctedQuery}"</strong>
                  <span className="ml-1 text-muted-foreground line-through">({originalQuery})</span>
                </span>
              </div>
              <button
                onClick={() => {
                  setPrompt(originalQuery);
                  handleSearchPapers(originalQuery);
                  setCorrectedQuery("");
                }}
                className="text-xs underline hover:text-foreground ml-2 shrink-0"
              >
                Search original instead
              </button>
            </div>
          )}

          {/* Action & Filter Bar */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/30">
            <div className="flex flex-wrap items-center gap-3">
              {/* Publisher / Source Filter */}
              <div className="flex items-center gap-1.5">
                <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground font-medium">Source:</span>
                <select
                  value={selectedSource}
                  onChange={(e) => {
                    setSelectedSource(e.target.value);
                  }}
                  className="rounded-lg border border-border/50 bg-secondary/40 px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Sources (Global)</option>
                  <option value="ieee">IEEE Publications Only</option>
                  <option value="arxiv">arXiv Preprints</option>
                  <option value="semantic_scholar">Semantic Scholar</option>
                  <option value="openalex">OpenAlex</option>
                  <option value="crossref">Crossref</option>
                </select>
              </div>

              {/* Year Filter */}
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground font-medium">Year:</span>
                <select
                  value={selectedYear}
                  onChange={(e) => {
                    setSelectedYear(e.target.value);
                  }}
                  className="rounded-lg border border-border/50 bg-secondary/40 px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Years</option>
                  <option value="last_3_years">Last 3 Years (2023–2026)</option>
                  <option value="last_5_years">Last 5 Years (2021–2026)</option>
                  <option value="2026">2026</option>
                  <option value="2025">2025</option>
                  <option value="2024">2024</option>
                  <option value="2023">2023</option>
                  <option value="2022">2022</option>
                  <option value="foundational">Foundational (≤2020)</option>
                </select>
              </div>

              {/* Sort By */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-muted-foreground font-medium">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value);
                  }}
                  className="rounded-lg border border-border/50 bg-secondary/40 px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="relevance">Most Relevant</option>
                  <option value="year_desc">Latest First</option>
                  <option value="citations_desc">Most Cited</option>
                  <option value="year_asc">Oldest First</option>
                </select>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept=".pdf"
                ref={fileInputRef}
                className="hidden"
                onChange={handleFileChange}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAttachPDF}
                className="text-xs border-border/50"
              >
                <Paperclip className="h-3.5 w-3.5 mr-1" />
                Attach PDF
              </Button>

              <Button
                variant="default"
                size="sm"
                onClick={() => handleSearchPapers()}
                disabled={loadingSearch}
                className="bg-primary text-primary-foreground font-medium shadow-md hover:bg-primary/90"
              >
                {loadingSearch ? "Searching Literature..." : "Search Papers"}
                <Search className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Top Research Papers Section */}
        <div className="rounded-3xl glass p-5 border border-border/40">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border/30">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-base">Retrieved Academic Papers</h3>
              {papers.length > 0 && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {selectedPapers.length} of {papers.length} selected
                </span>
              )}
            </div>

            {papers.length > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSelectAllPapers}
                  className="text-xs h-7 text-muted-foreground hover:text-foreground hover:bg-secondary/40"
                >
                  {selectedPapers.length === papers.length ? "Deselect All" : "Select All"}
                </Button>
              </div>
            )}
          </div>

          {papers.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/40 py-12 text-center my-3">
              <Search className="mb-3 h-10 w-10 text-muted-foreground/40" />
              <h4 className="text-base font-semibold">No Research Papers Yet</h4>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                Enter your research topic above and click <span className="font-medium text-foreground">Search Papers</span> to retrieve relevant peer-reviewed papers.
              </p>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <div className="max-h-[380px] overflow-y-auto space-y-3 pr-1">
                {papers.map((paper, index) => {
                  const isSelected = selectedPapers.includes(index);
                  const isIEEE = paper.is_ieee || paper.publication_type === "IEEE" || paper.venue?.toLowerCase().includes("ieee") || paper.source?.toLowerCase().includes("ieee");

                  return (
                    <div
                      key={paper.id || `${paper.title}-${index}`}
                      onClick={() => togglePaperSelection(index)}
                      className={`cursor-pointer rounded-2xl p-4 transition-all border ${
                        isSelected
                          ? "bg-primary/10 border-primary/50 shadow-sm"
                          : "bg-secondary/15 border-border/30 hover:border-border/60 hover:bg-secondary/25"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          onClick={(e) => {
                            e.stopPropagation();
                            togglePaperSelection(index);
                          }}
                          className="pt-0.5"
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            readOnly
                            className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="font-medium text-sm leading-snug">{paper.title}</h4>
                            {isIEEE && (
                              <span className="inline-flex items-center gap-1 rounded-md bg-blue-500/10 px-2 py-0.5 text-[11px] font-semibold text-blue-400 border border-blue-500/20">
                                <Award className="h-3 w-3" />
                                IEEE
                              </span>
                            )}
                            {paper.source && (
                              <span className="rounded-md bg-secondary/80 px-2 py-0.5 text-[10px] text-muted-foreground font-mono">
                                {paper.source}
                              </span>
                            )}
                          </div>

                          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
                            {Array.isArray(paper.authors)
                              ? paper.authors.join(", ")
                              : paper.authors || "Unknown authors"}
                          </p>

                          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                            {paper.venue && (
                              <span className="truncate max-w-[280px]">
                                <strong>Venue:</strong> {paper.venue}
                              </span>
                            )}
                            {paper.published && (
                              <span>
                                <strong>Published:</strong> {paper.published}
                              </span>
                            )}
                            {paper.citations !== undefined && paper.citations > 0 && (
                              <span>
                                <strong>Citations:</strong> {paper.citations}
                              </span>
                            )}
                            {paper.relevance_score !== undefined && paper.relevance_score > 0 && (
                              <span className="font-medium text-emerald-400">
                                Match: {(paper.relevance_score * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>

                          {paper.summary && (
                            <p className="mt-2 text-xs text-muted-foreground/80 line-clamp-2">
                              {paper.summary}
                            </p>
                          )}

                          {(() => {
                            const pdfTargetUrl =
                              paper.pdf_url ||
                              paper.url ||
                              (paper.doi ? `https://doi.org/${paper.doi.replace(/^https?:\/\/doi\.org\//, '')}` : undefined) ||
                              `https://scholar.google.com/scholar?q=${encodeURIComponent(paper.title)}`;

                            return (
                              <div className="mt-3 flex items-center gap-2">
                                <a
                                  href={pdfTargetUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary transition-all hover:bg-primary/20 border border-primary/25 shadow-xs"
                                >
                                  <FileText className="h-3.5 w-3.5" />
                                  {isIEEE ? "View IEEE PDF / Paper" : "View PDF Document"}
                                  <ExternalLink className="h-3 w-3 opacity-70 ml-0.5" />
                                </a>
                              </div>
                            );
                          })()}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Run AI Research Execution Trigger */}
              <div className="pt-3 flex items-center justify-between border-t border-border/30">
                <div className="text-xs text-muted-foreground">
                  {selectedPapers.length === 0
                    ? "Select papers above to execute multi-agent analysis"
                    : `${selectedPapers.length} papers selected for deep analysis`}
                </div>

                <Button
                  onClick={handleRunAllAgents}
                  disabled={runningAll || selectedPapers.length === 0}
                  className="bg-gradient-to-r from-primary via-indigo-500 to-purple-600 text-primary-foreground font-semibold px-5 shadow-lg hover:opacity-95"
                >
                  {runningAll ? (
                    <>
                      <RotateCcw className="mr-2 h-4 w-4 animate-spin" />
                      Executing All Agents...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Run AI Research ({selectedPapers.length} Papers)
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Multi-Agent Research Results Suite */}
        <div className="rounded-3xl glass p-5 border border-border/40 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/30">
            <div>
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-base">Multi-Agent Intelligence Suite</h3>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Structured Markdown tables, comparative taxonomies, and low-plagiarism synthesis
              </p>
            </div>

            {/* Run Status Badge */}
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  runningAll
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                    : Object.keys(agentResults).length > 0
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                {runningAll
                  ? "Agents Running..."
                  : Object.keys(agentResults).length > 0
                  ? `${Object.keys(agentResults).length} Agents Completed`
                  : "Idle"}
              </span>
            </div>
          </div>

          {/* Agent Navigation Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-2xl bg-secondary/30 border border-border/30">
            {WORKSPACE_AGENT_DEFS.map((def) => {
              const Icon = def.icon;
              const hasResult = Boolean(agentResults[def.key]);
              const isRunning = runningAgentKey === def.key || (runningAll && !hasResult);
              const isActive = activeAgentTab === def.key;

              return (
                <button
                  key={def.key}
                  onClick={() => setActiveAgentTab(def.key)}
                  className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-all ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{def.name}</span>
                  {hasResult && (
                    <CheckCircle2
                      className={`h-3 w-3 ${
                        isActive ? "text-primary-foreground" : "text-emerald-400"
                      }`}
                    />
                  )}
                  {isRunning && (
                    <RotateCcw className="h-3 w-3 animate-spin text-amber-400" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Active Agent Tab Content */}
          <div className="min-h-[260px]">
            {(() => {
              const currentDef =
                WORKSPACE_AGENT_DEFS.find((d) => d.key === activeAgentTab) ||
                WORKSPACE_AGENT_DEFS[0];
              const resultData = agentResults[currentDef.key];
              const isAgentRunning = runningAgentKey === currentDef.key || (runningAll && !resultData);

              let rawContent = "";
              if (Array.isArray(resultData)) {
                rawContent = resultData
                  .map((item) => {
                    if (typeof item === "string") return item;
                    const pName = item?.paper_name;
                    const res = item?.result || item?.output || "";
                    return pName && pName !== currentDef.name ? `### ${pName}\n\n${res}` : res;
                  })
                  .join("\n\n---\n\n");
              } else if (typeof resultData === "string") {
                rawContent = resultData;
              } else if (resultData && typeof resultData === "object") {
                rawContent = resultData.output || resultData.result || JSON.stringify(resultData, null, 2);
              }

              return (
                <div className="space-y-4">
                  {/* Tab Top Bar */}
                  <div className="flex items-center justify-between p-3 rounded-2xl bg-secondary/20 border border-border/30">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-primary/10 text-primary">
                        <currentDef.icon className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm">{currentDef.name}</h4>
                        <p className="text-xs text-muted-foreground">{currentDef.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {rawContent && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCopyResult(rawContent, currentDef.key)}
                          className="h-8 text-xs border-border/40"
                        >
                          {copiedKey === currentDef.key ? (
                            <>
                              <Check className="h-3.5 w-3.5 mr-1 text-emerald-400" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5 mr-1" />
                              Copy Output
                            </>
                          )}
                        </Button>
                      )}

                      <Button
                        variant="default"
                        size="sm"
                        disabled={isAgentRunning || selectedPapers.length === 0}
                        onClick={() => handleRunSingleAgent(currentDef)}
                        className="h-8 text-xs bg-primary text-primary-foreground font-medium"
                      >
                        {isAgentRunning ? (
                          <>
                            <RotateCcw className="h-3.5 w-3.5 mr-1 animate-spin" />
                            Running...
                          </>
                        ) : (
                          <>
                            <Play className="h-3.5 w-3.5 mr-1" />
                            {rawContent ? "Rerun Agent" : "Run Agent"}
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Output Display Area */}
                  {isAgentRunning ? (
                    <div className="flex flex-col items-center justify-center py-16 text-center space-y-3 rounded-2xl border border-border/30 bg-secondary/10">
                      <RotateCcw className="h-8 w-8 text-primary animate-spin" />
                      <p className="text-sm font-medium text-foreground">
                        Agent is synthesizing evidence and generating analysis...
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Grounding findings against selected papers with zero plagiarism
                      </p>
                    </div>
                  ) : rawContent ? (
                    <div className="rounded-2xl border border-border/40 bg-secondary/10 p-5 overflow-x-auto text-sm">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
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
                          h1: ({ node, ...props }) => (
                            <h1 className="text-xl font-bold mt-4 mb-2 text-foreground font-display" {...props} />
                          ),
                          h2: ({ node, ...props }) => (
                            <h2 className="text-lg font-bold mt-4 mb-2 text-foreground font-display" {...props} />
                          ),
                          h3: ({ node, ...props }) => (
                            <h3 className="text-base font-semibold mt-3 mb-1.5 text-primary font-display" {...props} />
                          ),
                          p: ({ node, ...props }) => (
                            <p className="leading-relaxed mb-3 text-foreground/90" {...props} />
                          ),
                          ul: ({ node, ...props }) => (
                            <ul className="list-disc list-inside space-y-1.5 mb-3 text-foreground/90" {...props} />
                          ),
                          ol: ({ node, ...props }) => (
                            <ol className="list-decimal list-inside space-y-1.5 mb-3 text-foreground/90" {...props} />
                          ),
                          li: ({ node, ...props }) => (
                            <li className="leading-relaxed" {...props} />
                          ),
                          hr: ({ node, ...props }) => (
                            <hr className="my-4 border-border/40" {...props} />
                          ),
                          strong: ({ node, ...props }) => (
                            <strong className="font-semibold text-foreground" {...props} />
                          ),
                        }}
                      >
                        {rawContent}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-center rounded-2xl border border-dashed border-border/40 bg-secondary/5">
                      <currentDef.icon className="h-8 w-8 text-muted-foreground/40 mb-2" />
                      <h4 className="text-sm font-semibold">No Output Generated Yet</h4>
                      <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                        Click <span className="font-medium text-foreground">Run Agent</span> above or <span className="font-medium text-foreground">Run AI Research</span> to execute all agents.
                      </p>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      </div>

      {/* Sidebar: Recent Research History */}
      <aside className="space-y-4">
        <div className="rounded-3xl glass p-5 border border-border/40">
          <div className="flex items-center justify-between pb-3 border-b border-border/30">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-sm">Recent Research</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleStartNewResearch}
              className="h-7 text-xs px-2 text-primary hover:text-primary hover:bg-primary/10"
            >
              <Plus className="h-3 w-3 mr-1" />
              New
            </Button>
          </div>

          {recentResearch.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground italic">
              No previous research sessions recorded.
            </div>
          ) : (
            <ul className="mt-3 space-y-2 max-h-[580px] overflow-y-auto pr-1">
              {recentResearch.map((r: any, idx: number) => {
                const isSelected = activeSessionId === r.session_id;
                const formattedDate = r.created_at
                  ? new Date(r.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "";

                return (
                  <li
                    key={r.session_id || idx}
                    onClick={() => {
                      if (r.session_id) {
                        handleLoadWorkspace(r.session_id);
                      }
                    }}
                    className={`group cursor-pointer rounded-2xl p-3 text-xs transition-all border ${
                      isSelected
                        ? "bg-primary/15 border-primary/40 text-foreground shadow-sm"
                        : "bg-secondary/20 border-border/30 text-muted-foreground hover:bg-secondary/40 hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-foreground truncate">{r.topic || "Untitled Topic"}</div>
                        <div className="mt-1 flex items-center gap-2 text-[10px] text-muted-foreground">
                          {formattedDate && <span>{formattedDate}</span>}
                          {r.papers && <span>• {r.papers.length} papers</span>}
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteSession(e, r.session_id)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                        title="Delete Session"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>
    </div>
  );
}