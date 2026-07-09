import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Download,
  Printer,
  Share2,
  FileText,
  Sparkles,
  Copy,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

import {
  getPapers,
  searchPaper,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/report")({
  head: () => ({
    meta: [{ title: "Research Report — ResearchX" }],
  }),
  component: ReportPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

function ReportPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [report, setReport] = useState("");

  const [loadingPapers, setLoadingPapers] =
    useState(true);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);

        const response = await getPapers();

        const uploadedPapers =
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

  const generateReport = async () => {
    if (!selectedPaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setReport("");

      const response = await searchPaper(
        "Generate a complete analysis and detailed analysis report for this research paper",
        `report_${Date.now()}`,
        selectedPaper
      );

      const answer =
        response?.data?.answer;

      if (!answer) {
        throw new Error(
          "No research report received"
        );
      }

      setReport(answer);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Report generation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyReport = async () => {
    if (!report) return;

    try {
      await navigator.clipboard.writeText(
        report
      );
    } catch {
      setError("Failed to copy report");
    }
  };

  const downloadReport = () => {
    if (!report) return;

    const blob = new Blob(
      [report],
      {
        type: "text/plain;charset=utf-8",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const anchor =
      document.createElement("a");

    const safeFilename =
      selectedPaper
        .replace(/\.pdf$/i, "")
        .replace(/[<>:"/\\|?*]+/g, "_");

    anchor.href = url;

    anchor.download =
      `${safeFilename}-research-report.txt`;

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
          title: `Research Report - ${selectedPaper}`,
          text: report,
        });

        return;
      }

      await navigator.clipboard.writeText(
        report
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setError("Failed to share report");
    }
  };

  return (
    <div>
      <PageHeader
        title="Research Report"
        subtitle={
          selectedPaper
            ? `Generate a complete multi-agent analysis for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          report ? (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="glass"
                onClick={copyReport}
              >
                <Copy className="h-4 w-4" />
                Copy
              </Button>

              <Button
                variant="glass"
                onClick={shareReport}
              >
                <Share2 className="h-4 w-4" />
                Share
              </Button>

              <Button
                variant="glass"
                onClick={printReport}
              >
                <Printer className="h-4 w-4" />
                Print
              </Button>

              <Button
                variant="hero"
                onClick={downloadReport}
              >
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>
          ) : undefined
        }
      />

      <div className="rounded-2xl glass p-5">
  <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
    <select
      value={selectedPaper}
      onChange={(event) => {
        setSelectedPaper(event.target.value);
        setReport("");
        setError("");
      }}
      disabled={loadingPapers || loading}
      className="min-h-10 w-full min-w-0 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
    >
      {papers.length === 0 && (
        <option value="">
          No papers uploaded
        </option>
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
      type="button"
      variant="hero"
      onClick={generateReport}
      disabled={
        loading ||
        loadingPapers ||
        !selectedPaper
      }
      className="w-full whitespace-nowrap md:w-auto"
    >
      <Sparkles className="h-4 w-4" />

      {loading
        ? "Running Multi-Agent Analysis..."
        : "Generate Complete Report"}
    </Button>
  </div>
</div>
      {error && (
        <div className="mt-4 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {!report &&
        !loading &&
        !error && (
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl glass p-5">
              <FileText className="h-7 w-7 text-[var(--electric)]" />

              <h3 className="mt-3 font-semibold">
                Complete Analysis
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Generate a structured analysis
                of the selected research paper.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Sparkles className="h-7 w-7 text-[var(--purple-glow)]" />

              <h3 className="mt-3 font-semibold">
                Multi-Agent Pipeline
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Run summary, gaps, datasets,
                experiments, literature and novelty
                analysis.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Download className="h-7 w-7 text-[var(--success)]" />

              <h3 className="mt-3 font-semibold">
                Export Report
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Copy, print, share or save the
                generated analysis.
              </p>
            </div>
          </div>
        )}

      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">
          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />

          <h3 className="mt-4 font-semibold">
            ResearchX multi-agent system is working
          </h3>

          <p className="mt-2 text-sm text-muted-foreground">
            Running summary, research gaps,
            dataset recommendations, experiments,
            literature survey and novelty analysis.
            This may take longer than a normal query.
          </p>
        </div>
      )}

      {report && !loading && (
        <div className="mt-6 grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="h-fit rounded-2xl glass p-5 lg:sticky lg:top-20">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">
              Report Information
            </div>

            <div className="mt-4 space-y-4 text-sm">
              <div>
                <div className="text-xs text-muted-foreground">
                  Paper
                </div>

                <div className="mt-1 break-words font-medium">
                  {selectedPaper}
                </div>
              </div>

              <div>
                <div className="text-xs text-muted-foreground">
                  Analysis Type
                </div>

                <div className="mt-1">
                  Complete Multi-Agent Report
                </div>
              </div>

              <div>
                <div className="text-xs text-muted-foreground">
                  Generated
                </div>

                <div className="mt-1">
                  {new Date().toLocaleString()}
                </div>
              </div>
            </div>
          </aside>

          <article className="rounded-2xl bg-white text-zinc-900 shadow-2xl">
            <div className="mx-auto max-w-4xl p-8 sm:p-12">
              <header className="border-b border-zinc-200 pb-6 text-center">
                <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                  ResearchX Multi-Agent Analysis
                </div>

                <h1 className="mt-3 font-display text-2xl font-bold sm:text-3xl">
                  Complete Research Analysis Report
                </h1>

                <p className="mt-3 break-words text-sm text-zinc-600">
                  {selectedPaper}
                </p>

                <p className="mt-1 text-xs text-zinc-500">
                  Generated by ResearchX ·{" "}
                  {new Date().getFullYear()}
                </p>
              </header>

              <section className="mt-8">
                <div className="whitespace-pre-wrap text-[13.5px] leading-7 text-zinc-700">
                  {report}
                </div>
              </section>
            </div>
          </article>
        </div>
      )}
    </div>
  );
}