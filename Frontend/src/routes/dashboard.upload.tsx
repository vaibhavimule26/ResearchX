import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  MessageSquare,
  BookOpen,
  FileSearch,
  Compass,
  Database,
  FlaskConical,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Loader2,
  RefreshCw,
  FileCheck2,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  getPapers,
  uploadPaper,
  checkPlagiarism,
  type PlagiarismResult,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/upload")({
  head: () => ({
    meta: [
      {
        title: "Upload PDF — ResearchX",
      },
    ],
  }),
  component: UploadPage,
});

const STEPS = [
  { label: "Parsing", done: true },
  { label: "OCR", done: true },
  { label: "Chunking", done: true },
  { label: "Embedding", done: true },
  { label: "Indexing", done: true },
];

function UploadPage() {
  const [drag, setDrag] = useState(false);
  const [papers, setPapers] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [lastUploadedFilename, setLastUploadedFilename] = useState("");

  // Plagiarism Checker State
  const [selectedPlagiarismPaper, setSelectedPlagiarismPaper] = useState<any | null>(null);
  const [plagiarismModalOpen, setPlagiarismModalOpen] = useState(false);
  const [loadingPlagiarism, setLoadingPlagiarism] = useState(false);
  const [plagiarismResult, setPlagiarismResult] = useState<PlagiarismResult | null>(null);
  const [plagiarismError, setPlagiarismError] = useState("");
  const [analyzingPaperId, setAnalyzingPaperId] = useState<string | null>(null);

  const handleOpenPlagiarismChecker = async (paper: any, forceRefresh: boolean = false) => {
    const pdfId = paper.id || paper.paper_id || paper.filename;
    if (!pdfId || analyzingPaperId === pdfId) return;

    setSelectedPlagiarismPaper(paper);
    setPlagiarismModalOpen(true);
    setLoadingPlagiarism(true);
    setPlagiarismError("");
    setAnalyzingPaperId(pdfId);

    try {
      const resp = await checkPlagiarism(pdfId, forceRefresh);
      if (resp && resp.data) {
        setPlagiarismResult(resp.data);
      } else {
        throw new Error(resp?.message || "Failed to analyze document");
      }
    } catch (err: any) {
      setPlagiarismError(err?.message || "Failed to complete similarity analysis");
    } finally {
      setLoadingPlagiarism(false);
      setAnalyzingPaperId(null);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPapers = async () => {
    try {
      setLoadingPapers(true);
      setError("");

      const response = await getPapers();

      setPapers(
        response?.data?.papers || []
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load papers"
      );
    } finally {
      setLoadingPapers(false);
    }
  };

  const uploadSelectedFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setMessage("");

      const response = await uploadPaper(file);

      setMessage(
        response?.message ||
          "PDF uploaded successfully"
      );
      setLastUploadedFilename(file.name);
      try {
        localStorage.setItem("researchx-active-paper", file.name);
      } catch (err) {
        console.error("Failed to set active paper:", err);
      }

      await fetchPapers();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Upload failed"
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };


  const handleUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) return;

    await uploadSelectedFile(file);
  };

  const handleDrop = async (
    event: React.DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    setDrag(false);

    const file = event.dataTransfer.files?.[0];

    if (!file) return;

    await uploadSelectedFile(file);
  };

  useEffect(() => {
    fetchPapers();
  }, []);

  return (
    <div>
      <PageHeader
        title="Upload PDFs"
        subtitle="Drop research PDFs to parse, embed and analyze."
      />

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        className={`rounded-3xl border-2 border-dashed p-12 text-center transition-colors ${
          drag
            ? "border-[var(--electric)] bg-[var(--electric)]/5"
            : "border-border/60 bg-secondary/30"
        }`}
      >
        <UploadCloud className="mx-auto h-12 w-12 text-[var(--electric)]" />

        <h3 className="mt-4 font-display text-xl font-semibold">
          Drag & Drop your PDFs here
        </h3>

        <p className="mt-1 text-sm text-muted-foreground">
          or click to browse • up to 50 MB each
        </p>

        <Button
          variant="hero"
          className="mt-5"
          onClick={() =>
            fileInputRef.current?.click()
          }
          disabled={uploading}
        >
          {uploading
            ? "Uploading..."
            : "Browse Files"}
        </Button>

        <input
          type="file"
          accept=".pdf,application/pdf"
          ref={fileInputRef}
          onChange={handleUpload}
          hidden
        />
      </div>

      {message && lastUploadedFilename && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-2xl glass p-6 border border-border/60 bg-gradient-to-br from-primary/5 via-background to-secondary/30"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-500">
                    PDF Uploaded ✓
                  </span>
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground font-medium">Ready for analysis</span>
                </div>
                <h4 className="mt-1 text-base font-semibold text-foreground truncate max-w-xl" title={lastUploadedFilename}>
                  {lastUploadedFilename}
                </h4>
              </div>
            </div>

            <Link
              to="/dashboard/chat"
              search={{ paper: lastUploadedFilename }}
              className="shrink-0"
            >
              <Button variant="hero" className="gap-2 shadow-lg shadow-primary/20 cursor-pointer">
                <MessageSquare className="h-4 w-4" />
                AI Chat
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="mt-5 pt-4 border-t border-border/40">
            <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3">
              Available Actions:
            </div>
            <div className="flex flex-wrap gap-2">
              <Link to="/dashboard/chat" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-primary/50 bg-primary/10 text-primary font-medium hover:bg-primary/20 cursor-pointer">
                  <MessageSquare className="h-3.5 w-3.5" />
                  AI Chat
                </Button>
              </Link>
              <Link to="/dashboard/literature" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer">
                  <BookOpen className="h-3.5 w-3.5 text-primary" />
                  Literature Survey
                </Button>
              </Link>
              <Link to="/dashboard/summary" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer">
                  <FileSearch className="h-3.5 w-3.5 text-primary" />
                  Research Summary
                </Button>
              </Link>
              <Link to="/dashboard/gaps" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer">
                  <Compass className="h-3.5 w-3.5 text-primary" />
                  Research Gaps
                </Button>
              </Link>
              <Link to="/dashboard/datasets" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer">
                  <Database className="h-3.5 w-3.5 text-primary" />
                  Dataset Recommendations
                </Button>
              </Link>
              <Link to="/dashboard/experiments" search={{ paper: lastUploadedFilename }}>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer">
                  <FlaskConical className="h-3.5 w-3.5 text-primary" />
                  Experiment Recommendations
                </Button>
              </Link>
            </div>
          </div>
        </motion.div>
      )}

      {message && !lastUploadedFilename && (
        <div className="mt-4 rounded-xl border border-border/40 bg-secondary/30 p-4 flex items-center gap-2 text-sm text-foreground font-medium">
          <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">
            Uploaded Files
          </h3>

          {loadingPapers ? (
            <p className="mt-4 text-sm text-muted-foreground">
              Loading papers...
            </p>
          ) : papers.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No papers uploaded yet.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {papers.map((paper, index) => (
                <li
                  key={`${paper.filename}-${paper.uploaded_at}-${index}`}
                  className="rounded-xl border border-border/40 bg-secondary/30 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <FileText className="h-5 w-5 text-[var(--electric)] shrink-0" />

                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {paper.filename}
                      </div>

                      <div className="text-xs text-muted-foreground">
                        Uploaded:{" "}
                        {paper.uploaded_at || "Unknown"}
                      </div>
                    </div>

                    <CheckCircle2 className="h-5 w-5 text-[var(--success)] shrink-0 hidden sm:block" />
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      to="/dashboard/chat"
                      search={{ paper: paper.filename }}
                    >
                      <Button
                        type="button"
                        size="sm"
                        variant="hero"
                        className="h-8 text-xs gap-1.5 cursor-pointer"
                      >
                        <MessageSquare className="h-3.5 w-3.5" />
                        AI Chat
                      </Button>
                    </Link>

                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenPlagiarismChecker(paper)}
                      disabled={analyzingPaperId === (paper.id || paper.paper_id || paper.filename)}
                      className="h-8 text-xs gap-1.5 border-border/60 hover:border-primary/50 cursor-pointer"
                      title="Run plagiarism & similarity check against ResearchX repository"
                    >
                      {analyzingPaperId === (paper.id || paper.paper_id || paper.filename) ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                          <span>Checking...</span>
                        </>
                      ) : (
                        <>
                          <ShieldAlert className="h-3.5 w-3.5 text-primary" />
                          <span>Plagiarism Checker</span>
                        </>
                      )}
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>


        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">
            Analysis Pipeline
          </h3>

          <ul className="mt-4 space-y-3">
            {STEPS.map((step, index) => (
              <motion.li
                key={step.label}
                initial={{
                  opacity: 0,
                  x: -10,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                transition={{
                  delay: index * 0.06,
                }}
                className="flex items-center gap-3"
              >
                <span
                  className={`grid h-7 w-7 place-items-center rounded-full text-xs ${
                    step.done
                      ? "bg-[var(--success)] text-background"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {index + 1}
                </span>

                <span
                  className={`text-sm ${
                    step.done
                      ? "text-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  {step.label}
                </span>
              </motion.li>
            ))}
          </ul>

          <div className="mt-6 text-xs text-muted-foreground">
            Uploaded papers:{" "}
            <span className="text-foreground">
              {papers.length}
            </span>
          </div>
        </div>
      </div>

      {/* Plagiarism & Similarity Checker Modal */}
      <Dialog open={plagiarismModalOpen} onOpenChange={setPlagiarismModalOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col p-0 overflow-hidden bg-background border border-border/80 shadow-2xl">
          <DialogHeader className="p-6 pb-4 border-b border-border/40 shrink-0 bg-secondary/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <ShieldAlert className="h-5 w-5" />
                </div>
                <div>
                  <DialogTitle className="text-lg font-semibold tracking-tight">
                    Plagiarism & Similarity Checker
                  </DialogTitle>
                  <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                    Analyzing text similarity and potential matching passages in your research document
                  </DialogDescription>
                </div>
              </div>
            </div>

            {selectedPlagiarismPaper && (
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs bg-secondary/40 border border-border/40 px-3 py-1.5 rounded-lg text-muted-foreground">
                <span className="flex items-center gap-1.5 font-medium text-foreground">
                  <FileText className="h-3.5 w-3.5 text-primary" />
                  {selectedPlagiarismPaper.filename}
                </span>
                <span className="text-border">•</span>
                <span>Scope: Compared against uploaded papers in ResearchX repository</span>
              </div>
            )}
          </DialogHeader>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {loadingPlagiarism ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
                <div className="relative">
                  <div className="h-14 w-14 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                  <div className="absolute inset-0 grid place-items-center">
                    <FileSearch className="h-6 w-6 text-primary animate-pulse" />
                  </div>
                </div>
                <div className="space-y-1">
                  <h4 className="text-base font-semibold text-foreground">
                    Calculating Lexical & Token Overlap...
                  </h4>
                  <p className="text-xs text-muted-foreground max-w-sm">
                    Extracting per-page text passages and cross-referencing with all indexed repository papers.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono bg-secondary/30 px-3 py-1.5 rounded-full">
                  <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
                  Running algorithmic similarity analysis (0% LLM hallucination)
                </div>
              </div>
            ) : plagiarismError ? (
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
                <div className="p-3 rounded-full bg-destructive/10 text-destructive">
                  <AlertCircle className="h-8 w-8" />
                </div>
                <h4 className="text-base font-semibold text-foreground">
                  Analysis Failed
                </h4>
                <p className="text-xs text-muted-foreground max-w-md">
                  {plagiarismError}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => selectedPlagiarismPaper && handleOpenPlagiarismChecker(selectedPlagiarismPaper, true)}
                  className="mt-2"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                  Retry Analysis
                </Button>
              </div>
            ) : plagiarismResult ? (
              <div className="space-y-6">
                {/* Metric Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                    <div className="text-xs font-medium text-muted-foreground flex items-center justify-between">
                      <span>Similarity Score</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground">
                        Algorithmic
                      </span>
                    </div>
                    <div
                      className={`text-2xl font-bold mt-1.5 ${
                        plagiarismResult.similarity_score < 15
                          ? "text-[var(--success)]"
                          : plagiarismResult.similarity_score < 30
                          ? "text-amber-500"
                          : "text-destructive"
                      }`}
                    >
                      {plagiarismResult.similarity_score}%
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      {plagiarismResult.similarity_score < 15
                        ? "Low overlap detected"
                        : plagiarismResult.similarity_score < 30
                        ? "Moderate overlap detected"
                        : "High overlap detected"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                    <div className="text-xs font-medium text-muted-foreground">
                      Original Content
                    </div>
                    <div className="text-2xl font-bold mt-1.5 text-primary">
                      {plagiarismResult.originality_score}%
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      Unique non-matching text
                    </p>
                  </div>

                  <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                    <div className="text-xs font-medium text-muted-foreground">
                      Potential Matches
                    </div>
                    <div className="text-2xl font-bold mt-1.5 text-foreground">
                      {plagiarismResult.matches_count}
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      {plagiarismResult.matches_count === 1
                        ? "Passage flagged"
                        : "Passages flagged"}
                    </p>
                  </div>
                </div>

                {/* Scope Notice */}
                <div className="flex items-start gap-2.5 rounded-xl border border-border/40 bg-secondary/10 p-3 text-xs text-muted-foreground">
                  <FileCheck2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  <div>
                    <span className="font-medium text-foreground">Comparison Scope: </span>
                    {plagiarismResult.comparison_corpus} ({plagiarismResult.total_compared_documents} repository documents indexed).
                  </div>
                </div>

                {/* Matches List */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-foreground">
                      Potential Matching Passages ({plagiarismResult.matches_count})
                    </h4>
                    <span className="text-xs text-muted-foreground">
                      Categorized by similarity strength
                    </span>
                  </div>

                  {plagiarismResult.matches.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-border/60 p-8 text-center space-y-2">
                      <ShieldCheck className="h-8 w-8 text-[var(--success)] mx-auto" />
                      <h5 className="text-sm font-medium text-foreground">
                        No Potential Matching Passages Found
                      </h5>
                      <p className="text-xs text-muted-foreground max-w-md mx-auto">
                        No significant overlapping text or duplicate passages were detected against the existing research papers in the ResearchX repository.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {plagiarismResult.matches.map((match, idx) => (
                        <div
                          key={`match-${match.match_id}-${idx}`}
                          className="rounded-xl border border-border/60 bg-secondary/15 p-4 space-y-3"
                        >
                          {/* Match Header */}
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-2.5">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-xs text-foreground">
                                Match #{match.match_id}
                              </span>
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary border border-primary/20">
                                Page {match.page}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                                  match.match_type === "exact_match"
                                    ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                                    : match.match_type === "near_exact"
                                    ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                                    : "bg-blue-500/10 text-blue-500 border-blue-500/20"
                                }`}
                              >
                                {match.match_type === "exact_match"
                                  ? "Exact Match (100%)"
                                  : match.match_type === "near_exact"
                                  ? "Near-Exact Match"
                                  : "Similar Text"}
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                              <span className="text-muted-foreground font-normal">Overlap:</span>
                              <span
                                className={
                                  match.similarity_percentage >= 90
                                    ? "text-rose-500"
                                    : match.similarity_percentage >= 75
                                    ? "text-amber-500"
                                    : "text-blue-500"
                                }
                              >
                                {match.similarity_percentage}%
                              </span>
                            </div>
                          </div>

                          {/* Passage in this paper */}
                          <div className="space-y-1">
                            <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
                              <span>Passage in Analyzed Paper:</span>
                            </div>
                            <blockquote className="text-xs bg-background/80 border-l-2 border-primary p-3 rounded-r-md leading-relaxed text-foreground font-mono whitespace-pre-wrap select-text">
                              "{match.matched_text}"
                            </blockquote>
                          </div>

                          {/* Source passage in repository */}
                          <div className="space-y-1">
                            <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
                              <span>Matching Source:</span>
                              <span className="text-foreground font-semibold">
                                {match.source_document}
                              </span>
                              {match.source_page && (
                                <span>(Page {match.source_page})</span>
                              )}
                            </div>
                            <blockquote className="text-xs bg-muted/40 border-l-2 border-muted-foreground/40 p-2.5 rounded-r-md leading-relaxed text-muted-foreground font-mono whitespace-pre-wrap select-text">
                              "{match.source_passage}"
                            </blockquote>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>

          <DialogFooter className="p-4 border-t border-border/40 shrink-0 bg-secondary/10 flex items-center justify-between sm:justify-between">
            <div className="text-[11px] text-muted-foreground">
              {plagiarismResult?.analyzed_at && (
                <span>
                  Analyzed at{" "}
                  {new Date(plagiarismResult.analyzed_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => selectedPlagiarismPaper && handleOpenPlagiarismChecker(selectedPlagiarismPaper, true)}
                disabled={loadingPlagiarism}
                className="h-8 text-xs gap-1.5"
              >
                <RefreshCw className={`h-3 w-3 ${loadingPlagiarism ? "animate-spin" : ""}`} />
                <span>Re-analyze</span>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="default"
                onClick={() => setPlagiarismModalOpen(false)}
                className="h-8 text-xs"
              >
                Close
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}