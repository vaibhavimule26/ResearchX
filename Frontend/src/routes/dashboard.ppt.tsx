import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Download,
  Presentation,
  Sparkles,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

import {
  getPapers,
  runAnalysis,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/ppt")({
  head: () => ({
    meta: [
      {
        title: "PPT Generator — ResearchX",
      },
    ],
  }),
  component: PPTPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

function PPTPage() {
  const [papers, setPapers] =
    useState<Paper[]>([]);

  const [selectedPaper, setSelectedPaper] =
    useState("");

  const [presentation, setPresentation] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  useEffect(() => {
    const loadPapers = async () => {
      try {
        const response =
          await getPapers();

        const uploaded =
          response?.data?.papers || [];

        setPapers(uploaded);

        if (uploaded.length > 0) {
          setSelectedPaper(
            uploaded[0].filename
          );
        }
      } catch (err) {
        console.error(err);
      }
    };

    loadPapers();
  }, []);

  const generatePresentation =
    async () => {
      if (!selectedPaper) return;

      try {
        setLoading(true);
        setError("");
        setPresentation("");

        const response =
          await runAnalysis(
            selectedPaper,
            "ppt"
          );

        setPresentation(
          response.result
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Generation failed"
        );
      } finally {
        setLoading(false);
      }
    };
      return (
    <div>
      <PageHeader
        title="PPT Generator"
        subtitle={
          selectedPaper
            ? `Generate presentation for '${selectedPaper}'.`
            : "Select an uploaded research paper."
        }
        action={
          <div className="flex gap-2">
            <Button
              variant="hero"
              onClick={generatePresentation}
              disabled={
                loading ||
                !selectedPaper
              }
            >
              <Sparkles className="h-4 w-4" />

              {loading
                ? "Generating..."
                : "Generate PPT"}
            </Button>

            <Button
  variant="glass"
  disabled={!presentation}
  onClick={async () => {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/ppt/generate",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          paper_name: selectedPaper,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error(error);
      alert(error);
      return;
    }

    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = "ResearchX_Presentation.pptx";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    alert(String(err));
  }
}}
>
  <Download className="h-4 w-4" />
  Export PPTX
</Button>
          </div>
        }
      />

      <div className="rounded-2xl glass p-5">
        <div className="flex flex-col gap-3 md:flex-row">

          <select
            value={selectedPaper}
            onChange={(e) =>
              setSelectedPaper(
                e.target.value
              )
            }
            className="min-h-10 flex-1 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
          >
            {papers.length === 0 && (
              <option value="">
                No uploaded papers
              </option>
            )}

            {papers.map((paper) => (
              <option
                key={paper.filename}
                value={paper.filename}
              >
                {paper.filename}
              </option>
            ))}
          </select>

          <Button
            variant="hero"
            onClick={
              generatePresentation
            }
            disabled={
              loading ||
              !selectedPaper
            }
          >
            Generate Presentation
          </Button>

        </div>
      </div>

      {error && (
        <div className="mt-5 rounded-xl border border-red-500 bg-red-500/10 p-4 text-red-500">
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-6 rounded-2xl glass p-8 text-center">

          <Presentation className="mx-auto h-10 w-10 animate-pulse text-[var(--electric)]" />

          <h2 className="mt-4 text-lg font-semibold">
            ResearchX is creating
            your presentation...
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            Analyzing the paper,
            preparing slides,
            organizing content...
          </p>

        </div>
      )}

      {!loading &&
        presentation && (
                    <div className="mt-6 rounded-2xl glass p-6">

            <div className="flex items-center gap-3">

              <div className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg">
                <Presentation className="h-5 w-5 text-primary-foreground" />
              </div>

              <div>
                <h3 className="font-semibold">
                  AI Presentation
                </h3>

                <p className="text-xs text-muted-foreground">
                  {selectedPaper}
                </p>
              </div>

            </div>

            <div className="mt-6 rounded-xl border border-border/60 bg-secondary/30 p-5">

              <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans text-muted-foreground">

                {presentation}

              </pre>

            </div>

          </div>
      )}

      {!loading &&
        !presentation &&
        !error && (

          <div className="mt-6 rounded-2xl glass p-8">

            <Presentation className="mx-auto h-12 w-12 text-[var(--electric)]" />

            <h2 className="mt-4 text-center text-xl font-semibold">
              AI PowerPoint Generator
            </h2>

            <p className="mt-3 text-center text-sm text-muted-foreground">

              Select an uploaded paper and click
              <strong> Generate Presentation </strong>

              ResearchX will automatically generate:

            </p>

            <ul className="mt-6 space-y-2 text-sm text-muted-foreground">

              <li>• Title Slide</li>

              <li>• Abstract</li>

              <li>• Problem Statement</li>

              <li>• Objectives</li>

              <li>• Related Work</li>

              <li>• Methodology</li>

              <li>• Dataset</li>

              <li>• Experimental Setup</li>

              <li>• Results</li>

              <li>• Novel Contributions</li>

              <li>• Limitations</li>

              <li>• Future Work</li>

              <li>• Conclusion</li>

              <li>• References</li>

            </ul>

          </div>

      )}

    </div>
  );
}