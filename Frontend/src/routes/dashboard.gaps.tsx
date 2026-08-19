import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Lightbulb,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/gaps")({
  head: () => ({
    meta: [{ title: "Research Gaps — ResearchX" }],
  }),
  component: ResearchGapsPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

// Cleanly unwrap API response without destroying Markdown formatting
function extractMarkdown(raw: unknown): string {
  if (!raw) return "";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.results?.gaps?.output ||
      obj?.results?.gap_analysis?.output ||
      obj?.results?.summary?.output ||
      obj?.gap_analysis ||
      obj?.output ||
      obj?.data?.answer ||
      obj?.answer ||
      obj?.result ||
      "";

    if (!text && obj?.results && typeof obj.results === "object") {
      const first = Object.values(obj.results)[0] as any;
      if (first?.output) text = first.output;
    }
  } else if (typeof raw === "string") {
    const trimmed = raw.trim();
    try {
      const parsed = JSON.parse(trimmed.replace(/'/g, '"'));
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
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "")
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .trim();
}

function ResearchGapsPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [gaps, setGaps] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);
        setError("");

        const response = await getPapers();
        const uploadedPapers: Paper[] = response?.data?.papers || [];

        setPapers(uploadedPapers);

        if (uploadedPapers.length > 0) {
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
  }, []);

  const findGaps = async () => {
    if (!selectedPaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setGaps("");

      const response = await runAnalysis(selectedPaper, "gaps");
      const rawResult =
        (response as any)?.result ??
        (response as any)?.data ??
        response;

      if (!rawResult) {
        throw new Error("No research gaps response received from backend");
      }

      setGaps(extractMarkdown(rawResult));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Research gap analysis failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyGaps = async () => {
    if (!gaps) return;
    try {
      await navigator.clipboard.writeText(gaps);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy research gaps");
    }
  };

  const downloadGaps = () => {
    if (!gaps) return;

    const content = [
      "ResearchX — Research Gaps & Limitations Report",
      "",
      `Paper: ${selectedPaper}`,
      "",
      gaps,
    ].join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename}-research-gaps.txt`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0">
      <PageHeader
        title="Research Gaps"
        subtitle={
          selectedPaper
            ? `Identify limitations and future research scope for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          <div className="flex gap-2">
            <Button
              variant="glass"
              onClick={copyGaps}
              disabled={!gaps || loading}
            >
              {copied ? (
                <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>

            <Button
              variant="hero"
              onClick={downloadGaps}
              disabled={!gaps || loading}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      <div className="rounded-2xl glass p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <select
            value={selectedPaper}
            onChange={(event) => {
              setSelectedPaper(event.target.value);
              setGaps("");
              setError("");
            }}
            disabled={loadingPapers || loading}
            className="min-h-10 flex-1 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
          >
            {loadingPapers && <option value="">Loading papers...</option>}
            {!loadingPapers && papers.length === 0 && (
              <option value="">No papers uploaded</option>
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
            variant="hero"
            onClick={findGaps}
            disabled={loading || loadingPapers || !selectedPaper}
          >
            <Sparkles className="h-4 w-4" />
            {loading ? "Analyzing..." : "Find Research Gaps"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">
          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />
          <h3 className="mt-4 font-semibold">Analyzing Research Gaps</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Evaluating author limitations, bottlenecks, and research directions...
          </p>
        </div>
      )}

      {gaps && !loading && (
        <div className="mt-6 rounded-2xl glass p-7">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg">
              <Lightbulb className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-semibold">Identified Research Gaps & Scope</h3>
              <p className="truncate text-xs text-muted-foreground">{selectedPaper}</p>
            </div>
          </div>

          <div className="mt-6 text-sm leading-relaxed text-foreground/90 font-normal space-y-4 [&_h3]:text-base [&_h3]:font-bold [&_h3]:mt-6 [&_h3]:mb-2 [&_h3]:text-primary [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1.5 [&_hr]:my-6 [&_hr]:border-border/60 [&_blockquote]:border-l-4 [&_blockquote]:border-primary [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:bg-secondary/20 [&_blockquote]:py-2 [&_blockquote]:rounded-r-lg [&_table]:w-full [&_table]:my-4 [&_table]:border-collapse [&_table]:rounded-xl [&_table]:overflow-hidden [&_table]:border [&_table]:border-border/60 [&_th]:border [&_th]:border-border/60 [&_th]:bg-secondary/60 [&_th]:p-3 [&_th]:text-left [&_th]:font-semibold [&_th]:text-primary [&_td]:border [&_td]:border-border/40 [&_td]:p-3 [&_tr:nth-child(even)]:bg-secondary/20">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {gaps}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}