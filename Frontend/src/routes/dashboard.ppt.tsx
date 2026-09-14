import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import {
  Download,
  Presentation,
  Sparkles,
  CheckCircle2,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Layers,
  ArrowRight,
  FileSpreadsheet,
  RotateCcw,
  Mic,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { PaperSelectorCard } from "@/components/dashboard/paper-selector-card";
import { AIProcessingCard } from "@/components/dashboard/ai-processing-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { ErrorState } from "@/components/dashboard/error-state";
import {
  getPapers,
  generatePresentation as generatePresentationAPI,
  exportPPTX,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/ppt")({
  head: () => ({
    meta: [
      {
        title: "AI Presentation Builder — ResearchX",
      },
    ],
  }),
  component: PPTPage,
});

type Paper = {
  filename: string;
  uploaded_at?: string;
};

type ParsedSlide = {
  id: number;
  title: string;
  category: string;
  takeaway: string;
  content: string[];
  speakerNotes: string;
  raw: string;
};

const PPT_STAGES = [
  {
    title: "Ingesting Paper Architecture & Key Claims",
    description: "Extracting research problem, core methodology, and novel contributions...",
  },
  {
    title: "Drafting Title, Problem Statement & Objectives",
    description: "Formulating compelling slide headlines and presentation pacing...",
  },
  {
    title: "Structuring Methodology, Datasets & Results",
    description: "Organizing empirical tables, baseline comparisons, and architecture diagrams...",
  },
  {
    title: "Compiling Slide Deck & Presentation Layout",
    description: "Applying IEEE conference styling and preparing downloadable slide assets...",
  },
];

// Helper to render bold lead-ins for bullet points
function renderBulletText(bullet: string) {
  // Check for markdown **Lead-in:** body
  const match = bullet.match(/^\*\*(.*?)\*\*:?\s*(.*)$/);
  if (match) {
    return (
      <span>
        <strong className="text-foreground font-semibold">{match[1]}: </strong>
        <span className="text-foreground/90">{match[2]}</span>
      </span>
    );
  }

  // Check for standard 'Lead-in: body'
  const colonIndex = bullet.indexOf(":");
  if (colonIndex > 0 && colonIndex < 35 && !bullet.slice(0, colonIndex).includes(".")) {
    return (
      <span>
        <strong className="text-foreground font-semibold">{bullet.slice(0, colonIndex + 1)} </strong>
        <span className="text-foreground/90">{bullet.slice(colonIndex + 1)}</span>
      </span>
    );
  }

  return <span>{bullet}</span>;
}

// Intelligently parse raw presentation text into structured slides
function parseSlides(rawText: string): ParsedSlide[] {
  if (!rawText || !rawText.trim()) return [];

  // Strip any preamble before the first slide header
  const firstMatch = rawText.match(/(?:={4,}\s*)?###\s*Slide\s*\d+\b/i);
  let textToParse = rawText;
  if (firstMatch && firstMatch.index !== undefined) {
    textToParse = rawText.slice(firstMatch.index);
  }

  // Match lines like ### Slide 1: Title or Slide 1 - Title
  const slideRegex = /(?:={4,}\s*)?###\s*Slide\s*(\d+)[:\-—]?\s*(.*?)(?=\n|$)/gi;
  const matches = [...textToParse.matchAll(slideRegex)];

  if (matches.length > 0) {
    const parsed: ParsedSlide[] = [];

    for (let i = 0; i < matches.length; i++) {
      const match = matches[i];
      const slideNum = parseInt(match[1] || String(i + 1), 10);
      const headerTitle = (match[2] || "").trim();

      const startIndex = match.index! + match[0].length;
      const endIndex =
        i + 1 < matches.length ? matches[i + 1].index! : textToParse.length;

      const bodyChunk = textToParse.slice(startIndex, endIndex).trim();

      let title = headerTitle;
      let category = "ACADEMIC PRESENTATION";
      let takeaway = "";
      const bullets: string[] = [];
      let notes = "";

      let inBullets = false;
      let inNotes = false;

      for (const rawLine of bodyChunk.split("\n")) {
        const line = rawLine.trim();
        if (!line || line.startsWith("===")) continue;

        if (line.startsWith("**Category:**")) {
          category = line.replace("**Category:**", "").replace(/\*\*/g, "").trim().toUpperCase();
          inBullets = false;
          inNotes = false;
          continue;
        }

        if (line.startsWith("**Slide Title:**")) {
          title = line.replace("**Slide Title:**", "").replace(/\*\*/g, "").trim();
          inBullets = false;
          inNotes = false;
          continue;
        }

        if (line.startsWith("**Takeaway:**")) {
          takeaway = line.replace("**Takeaway:**", "").replace(/\*\*/g, "").trim();
          inBullets = false;
          inNotes = false;
          continue;
        }

        if (line.includes("Bullet Points")) {
          inBullets = true;
          inNotes = false;
          continue;
        }

        if (line.includes("Speaker Notes")) {
          inBullets = false;
          inNotes = true;
          continue;
        }

        if (inBullets) {
          const cleanBullet = line.replace(/^[\*\-•]\s*/, "").trim();
          if (cleanBullet && !cleanBullet.startsWith("#")) {
            bullets.push(cleanBullet);
          }
        } else if (inNotes) {
          if (!line.toLowerCase().startsWith("please note that") && !line.toLowerCase().startsWith("feel free to")) {
            notes += (notes ? " " : "") + line;
          }
        } else {
          // If title not established yet and not a meta tag
          if (!title && !line.startsWith("**") && !line.startsWith("#")) {
            title = line;
          }
        }
      }

      parsed.push({
        id: slideNum,
        title: title || `Slide ${slideNum}`,
        category: category || "ACADEMIC PRESENTATION",
        takeaway,
        content: bullets.length > 0 ? bullets : [bodyChunk],
        speakerNotes: notes,
        raw: bodyChunk,
      });
    }

    return parsed;
  }

  // Fallback: split by double line breaks into paragraphs
  const chunks = rawText
    .split(/\n{2,}/)
    .map((c) => c.trim())
    .filter((c) => c.length > 0);

  return chunks.map((chunk, idx) => {
    const lines = chunk.split("\n").filter((l) => l.trim().length > 0);
    const title = lines[0] ? lines[0].replace(/^[#\*\-•\s]+/, "") : `Slide ${idx + 1}`;
    const body = lines.slice(1);

    return {
      id: idx + 1,
      title: title.slice(0, 60),
      category: "OVERVIEW",
      takeaway: "",
      content: body.length > 0 ? body : [chunk],
      speakerNotes: "",
      raw: chunk,
    };
  });
}

function PPTPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [presentation, setPresentation] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [downloadingPPTX, setDownloadingPPTX] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoadingPapers(true);
        const response = await getPapers();
        const uploaded = response?.data?.papers || [];
        setPapers(uploaded);

        if (uploaded.length > 0) {
          setSelectedPaper(uploaded[0].filename);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingPapers(false);
      }
    };

    loadPapers();
  }, []);

  const handleGeneratePresentation = async () => {
    if (!selectedPaper || loading) return;

    try {
      setLoading(true);
      setError("");
      setPresentation("");
      setCurrentSlideIndex(0);

      const response = await generatePresentationAPI(selectedPaper);

      if (!response?.presentation) {
        throw new Error("No presentation text received from backend");
      }

      setPresentation(response.presentation);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Presentation generation failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExportPPTX = async () => {
    if (!selectedPaper || downloadingPPTX) return;

    try {
      setDownloadingPPTX(true);
      setError("");

      const blob = await exportPPTX(selectedPaper, presentation);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const safeName = selectedPaper
        .replace(/\.pdf$/i, "")
        .replace(/[^a-zA-Z0-9-_]/g, "_");

      link.href = url;
      link.download = `${safeName || "ResearchX"}_Presentation.pptx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "PPTX export failed"
      );
    } finally {
      setDownloadingPPTX(false);
    }
  };

  const copySlideText = async () => {
    if (!presentation) return;
    try {
      await navigator.clipboard.writeText(presentation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy presentation content");
    }
  };

  const parsedSlides = useMemo(
    () => parseSlides(presentation),
    [presentation]
  );

  const activeSlide = parsedSlides[currentSlideIndex] || parsedSlides[0];

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="AI Presentation Builder"
        subtitle={
          selectedPaper
            ? `Conference-ready PowerPoint presentation deck generated from '${selectedPaper}'.`
            : "Select an uploaded research paper to generate a presentation deck."
        }
        action={
          presentation ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copySlideText}
                className="h-8 text-xs gap-1.5 border-border/60 hover:bg-secondary/60"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>Copy Text</span>
                  </>
                )}
              </Button>

              <Button
                variant="hero"
                size="sm"
                onClick={handleExportPPTX}
                disabled={downloadingPPTX}
                className="h-8 text-xs gap-1.5 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>{downloadingPPTX ? "Exporting..." : "Export .PPTX"}</span>
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Paper Selector Card */}
      <PaperSelectorCard
        papers={papers}
        selectedPaper={selectedPaper}
        onSelectPaper={(filename) => {
          setSelectedPaper(filename);
          setPresentation("");
          setError("");
        }}
        loading={loading}
        loadingPapers={loadingPapers}
        subtitle="Generates conference slide decks with title, problem, method, results, and conclusion."
        actionButton={
          <Button
            variant="hero"
            size="sm"
            onClick={handleGeneratePresentation}
            disabled={loading || loadingPapers || !selectedPaper}
            className="h-9 px-4 text-xs font-semibold gap-2 shadow-sm transition-all hover:scale-[1.02]"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>
              {loading
                ? "Designing Deck..."
                : presentation
                ? "Regenerate Slides"
                : "Generate Presentation"}
            </span>
          </Button>
        }
      />

      {error && (
        <ErrorState
          title="Presentation Generation Failed"
          error={error}
          onRetry={handleGeneratePresentation}
          className="relative z-0"
        />
      )}

      {/* Multi-Stage Loading Experience */}
      {loading && (
        <AIProcessingCard
          agentName="PRESENTATION BUILDER SPECIALIST"
          title={`Drafting slide deck for ${selectedPaper}`}
          stages={PPT_STAGES}
          className="relative z-0 mt-6"
        />
      )}

      {/* Empty State before Running */}
      {!loading && !presentation && !error && (
        <div className="relative z-0 mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 mb-3">
              <Presentation className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              16:9 Conference Deck
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Standardized widescreen layout tailored for defense presentations, lab meetings, and academic conferences.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3">
              <Layers className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Concise Slide Architecture
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Formulates slides: Title, Problem Statement, Objectives, Methodology, Results, and Limitations.
            </p>
          </div>

          <div className="rounded-2xl border border-border/40 bg-secondary/20 p-5 backdrop-blur-sm">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
              <Download className="h-4 w-4" />
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              Native PowerPoint (.pptx)
            </h4>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Downloads as an editable `.pptx` file compatible with Microsoft PowerPoint, Google Slides, and Apple Keynote.
            </p>
          </div>
        </div>
      )}

      {/* Presentation Deck Workspace */}
      {presentation && !loading && parsedSlides.length > 0 && (
        <div className="space-y-6">
          {/* Deck Status Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/50 bg-card/80 p-4 backdrop-blur-xl shadow-sm">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-xl gradient-primary-bg text-primary-foreground">
                <Presentation className="h-4 w-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-foreground block">
                  Presentation Deck Preview
                </span>
                <span className="text-[11px] text-muted-foreground font-mono">
                  {parsedSlides.length} Total Slides • 16:9 Standard Deck
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCurrentSlideIndex((prev) => Math.max(0, prev - 1))
                }
                disabled={currentSlideIndex === 0}
                className="h-8 w-8 p-0 rounded-xl"
                title="Previous slide"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <span className="text-xs font-mono text-muted-foreground px-2">
                Slide {currentSlideIndex + 1} of {parsedSlides.length}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setCurrentSlideIndex((prev) =>
                    Math.min(parsedSlides.length - 1, prev + 1)
                  )
                }
                disabled={currentSlideIndex === parsedSlides.length - 1}
                className="h-8 w-8 p-0 rounded-xl"
                title="Next slide"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Two-Column Deck Interface: Thumbnails + Active Slide Canvas */}
          <div className="grid gap-6 lg:grid-cols-12 items-start">
            {/* Left Column: Slide Thumbnails (4 cols) */}
            <div className="lg:col-span-4 space-y-2.5 max-h-[660px] overflow-y-auto pr-1 scrollbar-thin">
              {parsedSlides.map((slide, idx) => {
                const isActive = idx === currentSlideIndex;
                return (
                  <button
                    key={slide.id}
                    type="button"
                    onClick={() => setCurrentSlideIndex(idx)}
                    className={`w-full text-left rounded-xl p-3.5 border transition-all cursor-pointer ${
                      isActive
                        ? "border-primary/60 bg-primary/15 shadow-md scale-[1.01]"
                        : "border-border/40 bg-secondary/20 hover:bg-secondary/50 hover:border-border/60"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-primary">
                        {slide.category || `Slide ${String(idx + 1).padStart(2, "0")}`}
                      </span>
                      {isActive ? (
                        <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-primary text-primary-foreground">
                          Active
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono text-muted-foreground/70">
                          #{String(idx + 1).padStart(2, "0")}
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-semibold text-foreground truncate">
                      {slide.title}
                    </div>
                    <div className="text-[11px] text-muted-foreground line-clamp-1 mt-0.5">
                      {slide.takeaway || slide.content[0] || "Slide contents..."}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right Column: Active 16:9 Presentation Canvas (8 cols) */}
            {activeSlide && (
              <div className="lg:col-span-8 space-y-4">
                <div className="relative aspect-[16/9] w-full rounded-2xl border border-border/70 bg-card dark:bg-gradient-to-br dark:from-[#0F1420] dark:via-[#0B0F17] dark:to-[#121927] p-6 sm:p-10 shadow-2xl backdrop-blur-xl flex flex-col justify-between overflow-hidden">
                  {/* IEEE Top Header Accent Bar */}
                  <div className="absolute top-0 left-0 right-0 h-1.5 gradient-primary-bg" />

                  {/* Header info */}
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground/70 mb-2 border-b border-border/40 pb-2">
                      <span className="inline-flex items-center gap-1.5 font-bold uppercase tracking-wider text-primary text-[10px] bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                        {activeSlide.category || "Academic Presentation"}
                      </span>
                      <span>
                        Slide {String(currentSlideIndex + 1).padStart(2, "0")} /{" "}
                        {String(parsedSlides.length).padStart(2, "0")}
                      </span>
                    </div>

                    <h3 className="text-lg sm:text-2xl font-display font-bold text-foreground tracking-tight">
                      {activeSlide.title}
                    </h3>

                    {activeSlide.takeaway && (
                      <p className="mt-1 text-xs sm:text-sm text-muted-foreground italic line-clamp-2">
                        <span className="font-semibold text-primary not-italic">Key Takeaway: </span>
                        {activeSlide.takeaway}
                      </p>
                    )}
                  </div>

                  {/* Slide Content Bullets */}
                  <div className="my-auto space-y-3 py-3">
                    {activeSlide.content.map((point, pIdx) => (
                      <div
                        key={pIdx}
                        className="flex items-start gap-3 text-xs sm:text-sm text-foreground/90 leading-relaxed"
                      >
                        <span className="h-2 w-2 rounded-full gradient-primary-bg shrink-0 mt-1.5 shadow-sm" />
                        <div className="flex-1 leading-normal">{renderBulletText(point)}</div>
                      </div>
                    ))}
                  </div>

                  {/* Slide Footer */}
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground/60 border-t border-border/30 pt-3">
                    <span className="truncate max-w-[280px]">
                      {selectedPaper}
                    </span>
                    <span>IEEE Presentation Standard • 16:9 Widescreen</span>
                  </div>
                </div>

                {/* Speaker Notes / Presenter View Section */}
                {activeSlide.speakerNotes && (
                  <div className="rounded-xl border border-border/50 bg-secondary/30 p-4 backdrop-blur-sm space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                        <Mic className="h-3.5 w-3.5" />
                        <span>Presenter View &amp; Speaker Notes</span>
                      </div>
                      <span className="text-[10px] font-mono text-muted-foreground">Slide {currentSlideIndex + 1} Spoken Script</span>
                    </div>
                    <p className="text-xs sm:text-sm text-foreground/80 leading-relaxed font-sans bg-background/60 p-3 rounded-lg border border-border/40">
                      {activeSlide.speakerNotes}
                    </p>
                  </div>
                )}

                {/* Bottom Navigator Controls */}
                <div className="flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentSlideIndex((prev) => Math.max(0, prev - 1))
                    }
                    disabled={currentSlideIndex === 0}
                    className="gap-1 text-xs h-8 cursor-pointer"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                    <span>Previous Slide</span>
                  </Button>

                  <Button
                    variant="hero"
                    size="sm"
                    onClick={handleExportPPTX}
                    disabled={downloadingPPTX}
                    className="gap-1 text-xs h-8 shadow-sm cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>{downloadingPPTX ? "Exporting..." : "Export PowerPoint Deck (.pptx)"}</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentSlideIndex((prev) =>
                        Math.min(parsedSlides.length - 1, prev + 1)
                      )
                    }
                    disabled={currentSlideIndex === parsedSlides.length - 1}
                    className="gap-1 text-xs h-8 cursor-pointer"
                  >
                    <span>Next Slide</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default PPTPage;