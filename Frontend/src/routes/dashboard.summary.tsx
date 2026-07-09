import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Download,
  Share2,
  Sparkles,
  FileText,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import {
  getPapers,
  runAnalysis,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/summary")({
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
  uploaded_at?: string;
};

function SummaryPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
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
  // Generate Summary
  // ==========================
  const generateSummary = async () => {
    if (!selectedPaper || loading) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSummary("");

      const response = await runAnalysis(
        selectedPaper,
        "summary"
      );

      if (!response?.result) {
        throw new Error(
          "No summary received from backend"
        );
      }

      setSummary(response.result);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to generate summary"
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================
  // Copy Summary
  // ==========================
  const copySummary = async () => {
    if (!summary) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        summary
      );
    } catch {
      setError(
        "Failed to copy summary to clipboard"
      );
    }
  };

  // ==========================
  // Download Summary
  // ==========================
  const downloadSummary = () => {
    if (!summary) {
      return;
    }

    const content = [
      "ResearchX AI Generated Summary",
      "",
      `Paper: ${selectedPaper}`,
      "",
      summary,
    ].join("\n");

    const blob = new Blob(
      [content],
      {
        type: "text/plain;charset=utf-8",
      }
    );

    const url = URL.createObjectURL(blob);

    const anchor =
      document.createElement("a");

    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download =
      `${safeFilename}-summary.txt`;

    document.body.appendChild(anchor);

    anchor.click();

    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0">
      <PageHeader
        title="Research Summary"
        subtitle={
          selectedPaper
            ? `Generate a structured AI summary for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="glass"
              onClick={copySummary}
              disabled={!summary || loading}
            >
              <Share2 className="h-4 w-4" />
              Copy
            </Button>

            <Button
              type="button"
              variant="hero"
              onClick={downloadSummary}
              disabled={!summary || loading}
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

              setSummary("");
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
            onClick={generateSummary}
            disabled={
              loading ||
              loadingPapers ||
              !selectedPaper
            }
            className="w-full whitespace-nowrap md:w-auto"
          >
            <Sparkles className="h-4 w-4" />

            {loading
              ? "Analyzing Paper..."
              : "Generate Summary"}
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
          Empty State
      ========================== */}
      {!summary &&
        !loading &&
        !error && (
          <div className="mt-6 rounded-2xl glass p-10 text-center">

            <FileText className="mx-auto h-10 w-10 text-[var(--electric)]" />

            <h3 className="mt-4 font-semibold">
              No summary generated yet
            </h3>

            <p className="mt-2 text-sm text-muted-foreground">
              Select a paper and click
              Generate Summary.
            </p>

          </div>
        )}

      {/* ==========================
          Loading State
      ========================== */}
      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">

          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />

          <h3 className="mt-4 font-semibold">
            Analyzing research paper
          </h3>

          <p className="mt-2 text-sm text-muted-foreground">
            ResearchX is retrieving relevant
            paper sections and running the
            Summary Agent...
          </p>

        </div>
      )}

      {/* ==========================
          Summary Result
      ========================== */}
      {summary && !loading && (
        <div className="mt-6 rounded-2xl glass p-6">

          <div className="flex items-center gap-3">

            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>

            <div className="min-w-0">
              <h3 className="font-semibold">
                AI Generated Summary
              </h3>

              <p className="truncate text-xs text-muted-foreground">
                {selectedPaper}
              </p>
            </div>

          </div>

          <div className="mt-5 whitespace-pre-wrap break-words text-sm leading-relaxed text-muted-foreground">
            {summary}
          </div>

        </div>
      )}
    </div>
  );
}