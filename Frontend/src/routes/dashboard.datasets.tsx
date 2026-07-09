import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Database,
  Sparkles,
  Copy,
  Download,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

import {
  getPapers,
  searchPaper,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/datasets")({
  head: () => ({
    meta: [{ title: "Datasets — ResearchX" }],
  }),
  component: DatasetsPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

function DatasetsPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [recommendations, setRecommendations] = useState("");

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

  const recommendDatasets = async () => {
    if (!selectedPaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setRecommendations("");

      const response = await searchPaper(
        "Recommend suitable datasets for this research paper. Explain why each dataset is relevant, its task, expected use, and possible evaluation purpose.",
        `dataset_${Date.now()}`,
        selectedPaper
      );

      const answer =
        response?.data?.answer;

      if (!answer) {
        throw new Error(
          "No dataset recommendations received"
        );
      }

      setRecommendations(answer);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Dataset recommendation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const copyRecommendations = async () => {
    if (!recommendations) return;

    await navigator.clipboard.writeText(
      recommendations
    );
  };

  const downloadRecommendations = () => {
    if (!recommendations) return;

    const blob = new Blob(
      [recommendations],
      {
        type: "text/plain;charset=utf-8",
      }
    );

    const url = URL.createObjectURL(blob);

    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download =
      `${selectedPaper}-dataset-recommendations.txt`;

    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <PageHeader
        title="Dataset Recommendations"
        subtitle={
          selectedPaper
            ? `Discover suitable datasets for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          recommendations ? (
            <div className="flex gap-2">
              <Button
                variant="glass"
                onClick={copyRecommendations}
              >
                <Copy className="h-4 w-4" />
                Copy
              </Button>

              <Button
                variant="hero"
                onClick={downloadRecommendations}
              >
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>
          ) : undefined
        }
      />

      <div className="rounded-2xl glass p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <select
            value={selectedPaper}
            onChange={(event) => {
              setSelectedPaper(event.target.value);
              setRecommendations("");
              setError("");
            }}
            disabled={
              loadingPapers || loading
            }
            className="min-h-10 flex-1 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
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
            variant="hero"
            onClick={recommendDatasets}
            disabled={
              loading ||
              loadingPapers ||
              !selectedPaper
            }
          >
            <Sparkles className="h-4 w-4" />

            {loading
              ? "Finding Datasets..."
              : "Recommend Datasets"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {!recommendations &&
        !loading &&
        !error && (
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl glass p-5">
              <Database className="h-7 w-7 text-[var(--electric)]" />

              <h3 className="mt-3 font-semibold">
                Relevant Datasets
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Find datasets aligned with the
                selected paper's research domain.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Sparkles className="h-7 w-7 text-[var(--purple-glow)]" />

              <h3 className="mt-3 font-semibold">
                AI Recommendations
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Use your specialized dataset agent
                to recommend suitable resources.
              </p>
            </div>

            <div className="rounded-2xl glass p-5">
              <Download className="h-7 w-7 text-[var(--success)]" />

              <h3 className="mt-3 font-semibold">
                Export Results
              </h3>

              <p className="mt-2 text-sm text-muted-foreground">
                Save dataset recommendations for
                later experiment planning.
              </p>
            </div>
          </div>
        )}

      {loading && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">
          <Sparkles className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />

          <h3 className="mt-4 font-semibold">
            ResearchX is finding datasets
          </h3>

          <p className="mt-2 text-sm text-muted-foreground">
            Matching research context with suitable
            datasets...
          </p>
        </div>
      )}

      {recommendations && !loading && (
        <div className="mt-6 rounded-2xl glass p-6">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg">
              <Database className="h-5 w-5 text-primary-foreground" />
            </div>

            <div>
              <h3 className="font-semibold">
                AI Dataset Recommendations
              </h3>

              <p className="text-xs text-muted-foreground">
                {selectedPaper}
              </p>
            </div>
          </div>

          <div className="mt-5 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
            {recommendations}
          </div>
        </div>
      )}
    </div>
  );
}