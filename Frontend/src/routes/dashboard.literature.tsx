import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Sparkles,
  Copy,
  Download,
  CheckCircle2,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { getPapers, runAnalysis } from "@/lib/api";

export const Route = createFileRoute("/dashboard/literature")({
  head: () => ({
    meta: [{ title: "Literature Survey — ResearchX" }],
  }),
  component: LiteratureSurveyPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

// Client-side symbol cleaner
function stripAllSymbols(raw: unknown): string {
  if (!raw) return "";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.results?.literature_survey?.output ||
      obj?.results?.literature?.output ||
      obj?.results?.summary?.output ||
      obj?.results?.gaps?.output ||
      obj?.results?.datasets?.output ||
      obj?.results?.experiments?.output ||
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
      return stripAllSymbols(parsed);
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
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/^\s*[\*\-]\s+/gm, "• ")
    .replace(/`{1,3}(.*?)`{1,3}/g, "$1")
    .replace(/`+/g, "")
    .replace(/---+|___+/g, "")
    .replace(/\$\$(.*?)\$\$/g, "$1")
    .replace(/\$(.*?)\$/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function LiteratureSurveyPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [survey, setSurvey] = useState("");
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

  const generateSurvey = async () => {
    if (!selectedPaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setSurvey("");

      const response = await (runAnalysis as any)(selectedPaper, "literature_survey");
      const rawResult =
        response?.result ??
        response?.data ??
        response;

      if (!rawResult) {
        throw new Error("No literature survey received from backend");
      }

      setSurvey(stripAllSymbols(rawResult));
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

    const content = [
      "ResearchX — Academic Literature Survey",
      "",
      `Paper: ${selectedPaper}`,
      "",
      survey,
    ].join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeFilename = selectedPaper
      .replace(/\.pdf$/i, "")
      .replace(/[^a-zA-Z0-9-_]/g, "_");

    anchor.href = url;
    anchor.download = `${safeFilename}-literature-survey.txt`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-w-0">
      <PageHeader
        title="Literature Survey"
        subtitle={
          selectedPaper
            ? `Comprehensive related work and technical survey for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          <div className="flex gap-2">
            <Button
              variant="glass"
              onClick={copySurvey}
              disabled={!survey || loading}
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
              onClick={downloadSurvey}
              disabled={!survey || loading}
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
              setSurvey("");
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
            onClick={generateSurvey}
            disabled={loading || loadingPapers || !selectedPaper}
          >
            <Sparkles className="h-4 w-4" />
            {loading ? "Generating..." : "Generate Literature Survey"}
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
          <h3 className="mt-4 font-semibold">Synthesizing Literature Survey</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Mapping related work paradigms, baseline systems, on-device compute, and research gaps...
          </p>
        </div>
      )}

      {survey && !loading && (
        <div className="mt-6 rounded-2xl glass p-7">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl gradient-primary-bg">
              <BookOpen className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-semibold">Academic Literature Survey</h3>
              <p className="truncate text-xs text-muted-foreground">{selectedPaper}</p>
            </div>
          </div>

          <div className="mt-6 whitespace-pre-line text-sm leading-relaxed text-foreground/90 font-normal">
            {survey}
          </div>
        </div>
      )}
    </div>
  );
}