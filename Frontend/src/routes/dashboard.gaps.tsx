import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Lightbulb,
  Sparkles,
  Telescope,
  AlertCircle,
  Copy,
  Download,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

import {
  getPapers,
  runAnalysis,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/gaps")({
  head: () => ({
    meta: [
      {
        title: "Research Gaps — ResearchX",
      },
    ],
  }),
  component: GapPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

function GapPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [analysis, setAnalysis] = useState("");

  const [loadingPapers, setLoadingPapers] =
    useState(true);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  // ==========================
  // Load Uploaded Papers
  // ==========================
  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);
        setError("");

        const response = await getPapers();

        const uploadedPapers: Paper[] =
          response?.data?.papers || [];

        setPapers(uploadedPapers);

        if (uploadedPapers.length > 0) {
          setSelectedPaper(
            uploadedPapers[0].filename
          );
        }
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

    loadPapers();
  }, []);

  // ==========================
  // Run Dedicated Gap Analysis
  // ==========================
  const analyzeGaps = async () => {
    if (!selectedPaper || loading) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      setAnalysis("");

      const response = await runAnalysis(
        selectedPaper,
        "gaps"
      );

      if (!response?.result) {
        throw new Error(
          "No research gap analysis received from backend"
        );
      }

      setAnalysis(response.result);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Research gap analysis failed"
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================
  // Copy Analysis
  // ==========================
  const copyAnalysis = async () => {
    if (!analysis) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        analysis
      );
    } catch {
      setError(
        "Failed to copy analysis to clipboard"
      );
    }
  };

  // ==========================
  // Download Analysis
  // ==========================
  const downloadAnalysis = () => {
    if (!analysis) {
      return;
    }

    const content = [
      "ResearchX Research Gap Analysis",
      "",
      `Paper: ${selectedPaper}`,
      "",
      analysis,
    ].join("\n");

    const blob = new Blob(
      [content],
      {
        type: "text/plain;charset=utf-8",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const anchor =
      document.createElement("a");

    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;

    anchor.download =
      `${safeFilename}-research-gaps.txt`;

    document.body.appendChild(anchor);

    anchor.click();

    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0">
      <PageHeader
        title="Research Gap Analysis"
        subtitle={
          selectedPaper
            ? `Discover limitations and future opportunities in '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="glass"
              onClick={copyAnalysis}
              disabled={!analysis || loading}
            >
              <Copy className="h-4 w-4" />
              Copy
            </Button>

            <Button
              type="button"
              variant="hero"
              onClick={downloadAnalysis}
              disabled={!analysis || loading}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      {/* ==========================
          Paper Selection
      ========================== */}
      <div className="rounded-2xl glass p-5">
        <div className="grid min-w-0 gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">

          <select
            value={selectedPaper}
            onChange={(event) => {
              setSelectedPaper(
                event.target.value
              );

              setAnalysis("");
              setError("");
            }}
            disabled={
              loadingPapers || loading
            }
            className="min-h-10 w-full min-w-0 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
          >
            {loadingPapers && (
              <option value="">
                Loading papers...
              </option>
            )}

            {!loadingPapers &&
              papers.length === 0 && (
                <option value="">
                  No papers uploaded
                </option>
              )}

            {papers.map(
              (paper, index) => (
                <option
                  key={`${paper.filename}-${index}`}
                  value={paper.filename}
                >
                  {paper.filename}
                </option>
              )
            )}
          </select>

          <Button
            type="button"
            variant="hero"
            onClick={analyzeGaps}
            disabled={
              loading ||
              loadingPapers ||
              !selectedPaper
            }
            className="w-full whitespace-nowrap md:w-auto"
          >
            <Sparkles className="h-4 w-4" />

            {loading
              ? "Analyzing Gaps..."
              : "Analyze Gaps"}
          </Button>

        </div>
      </div>

      {/* ==========================
          Error State
      ========================== */}
      {error && (
        <div className="mt-4 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* ==========================
          Empty State Cards
      ========================== */}
      {!analysis &&
        !loading &&
        !error && (
          <div className="mt-6 grid gap-4 md:grid-cols-3">

            <div className="rounded-2xl glass p-5">
              <AlertCircle className="h-6 w-6 text-[var(--warning)]" />

              <h3 className="mt-3 font-semibold">
                Limitations
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Identify weaknesses, constraints,
                unresolved problems, and missing
                evaluations in the selected paper.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Lightbulb className="h-6 w-6 text-[var(--electric)]" />

              <h3 className="mt-3 font-semibold">
                Research Opportunities
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Discover meaningful opportunities
                where future research can extend
                or improve the existing work.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Telescope className="h-6 w-6 text-[var(--purple-glow)]" />

              <h3 className="mt-3 font-semibold">
                Future Scope
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Generate grounded future directions
                based on limitations and unresolved
                challenges found in the paper.
              </p>
            </div>

          </div>
        )}

      {/* ==========================
          Loading State
      ========================== */}
      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">

          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />

          <h3 className="mt-4 font-semibold">
            ResearchX is finding research gaps
          </h3>

          <p className="mt-2 text-sm text-muted-foreground">
            The Gap Detection Agent is analyzing
            limitations, weaknesses, unresolved
            problems, and future opportunities...
          </p>

        </div>
      )}

      {/* ==========================
          Analysis Result
      ========================== */}
      {analysis && !loading && (
        <div className="mt-6 rounded-2xl glass p-6">

          <div className="flex items-center gap-3">

            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg">
              <Lightbulb className="h-5 w-5 text-primary-foreground" />
            </div>

            <div className="min-w-0">
              <h3 className="font-semibold">
                AI Research Gap Analysis
              </h3>

              <p className="truncate text-xs text-muted-foreground">
                {selectedPaper}
              </p>
            </div>

          </div>

          <div className="mt-5 whitespace-pre-wrap break-words text-sm leading-relaxed text-muted-foreground">
            {analysis}
          </div>

        </div>
      )}
    </div>
  );
}