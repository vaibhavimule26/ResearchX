import { useState, useRef, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import {
  FileText,
  ChevronDown,
  Upload,
  Check,
  Search,
  Clock,
  CheckCircle2,
} from "lucide-react";

export type PaperItem = {
  filename: string;
  uploaded_at?: string;
  title?: string;
};

interface PaperSelectorCardProps {
  papers: PaperItem[];
  selectedPaper: string;
  onSelectPaper: (filename: string) => void;
  loading?: boolean;
  loadingPapers?: boolean;
  actionButton?: React.ReactNode;
  subtitle?: string;
  className?: string;
}

export function PaperSelectorCard({
  papers,
  selectedPaper,
  onSelectPaper,
  loading = false,
  loadingPapers = false,
  actionButton,
  subtitle,
  className = "",
}: PaperSelectorCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click or Escape key
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const filteredPapers = papers.filter((p) =>
    p.filename.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const currentPaper = papers.find(
    (p) => p.filename.toLowerCase() === selectedPaper.toLowerCase()
  );

  return (
    <div
      ref={containerRef}
      className={`relative rounded-2xl border border-border/70 bg-card shadow-sm p-5 transition-all ${
        isOpen ? "z-30" : "z-10"
      } ${className}`}
    >
      {/* Top Header Row: Label & Status Indicator & Toggle Action */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-border/50">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <FileText className="h-4 w-4 text-primary" />
            <span>Target Research Paper</span>
          </div>

          {selectedPaper && !loadingPapers && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3 w-3" />
              <span>PDF uploaded • Ready for analysis</span>
            </span>
          )}
        </div>

        {papers.length > 0 && !loadingPapers && (
          <button
            type="button"
            onClick={() => !loading && setIsOpen(!isOpen)}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors cursor-pointer"
            aria-label="Change target research paper"
          >
            <span className="hidden sm:inline">{isOpen ? "Close" : "Change Paper"}</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform duration-200 ${
                isOpen ? "rotate-180 text-primary" : ""
              }`}
            />
          </button>
        )}
      </div>

      {/* Main Body: Loading / Empty / Selected Paper Trigger */}
      <div className="mt-3.5">
        {loadingPapers ? (
          <div className="flex items-center gap-3 py-3 px-3.5 rounded-xl border border-border/50 bg-secondary/20">
            <div className="h-9 w-9 rounded-lg bg-muted/50 animate-pulse shrink-0" />
            <div className="space-y-1.5 flex-1">
              <div className="h-4 w-52 rounded bg-muted/50 animate-pulse" />
              <div className="h-3 w-32 rounded bg-muted/40 animate-pulse" />
            </div>
          </div>
        ) : papers.length === 0 ? (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl border border-dashed border-border/70 bg-secondary/20">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-muted text-muted-foreground">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">
                  No research paper selected
                </p>
                <p className="text-xs text-muted-foreground">
                  Upload a research paper to generate an IEEE report.
                </p>
              </div>
            </div>
            <Link
              to="/dashboard/upload"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs transition-colors shrink-0"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>Upload PDF</span>
            </Link>
          </div>
        ) : (
          /* Clickable Paper Selector Trigger with relative container for dropdown */
          <div className={`relative ${isOpen ? "z-40" : "z-10"}`}>
            <button
              type="button"
              onClick={() => !loading && setIsOpen(!isOpen)}
              disabled={loading}
              className={`w-full text-left p-3.5 rounded-xl border transition-all duration-150 flex items-center justify-between gap-3 cursor-pointer ${
                isOpen
                  ? "border-primary/60 bg-secondary/80 ring-2 ring-primary/25 shadow-sm"
                  : "border-border/70 bg-secondary/30 hover:bg-secondary/50 hover:border-border"
              }`}
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary border border-primary/20">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <span
                    className="font-semibold text-sm text-foreground truncate block"
                    title={selectedPaper || "Select a research paper..."}
                  >
                    {selectedPaper || "Select a research paper..."}
                  </span>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                      <CheckCircle2 className="h-3 w-3" />
                      PDF uploaded • Ready for analysis
                    </span>
                    {currentPaper?.uploaded_at && (
                      <>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 text-[11px]">
                          <Clock className="h-3 w-3" />
                          {currentPaper.uploaded_at}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="shrink-0 pl-2">
                <ChevronDown
                  className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${
                    isOpen ? "rotate-180 text-primary" : ""
                  }`}
                />
              </div>
            </button>

            {/* Dropdown Popover */}
            {isOpen && (
              <div
                className="absolute left-0 right-0 top-full mt-2 w-full rounded-2xl border border-border/80 bg-popover text-popover-foreground shadow-2xl z-50 p-2.5 animate-in fade-in zoom-in-95 duration-150"
                style={{
                  backgroundColor: "var(--popover)",
                  boxShadow: "0 20px 40px -15px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--border)",
                }}
              >
                {/* Search Bar */}
                <div className="relative mb-2">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    value={filterQuery}
                    onChange={(e) => setFilterQuery(e.target.value)}
                    placeholder="Search uploaded papers..."
                    className="w-full rounded-xl border border-border/70 bg-secondary/50 pl-8 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    autoFocus
                  />
                </div>

                {/* List of uploaded papers */}
                <div className="max-h-60 overflow-y-auto space-y-1 scrollbar-thin">
                  {filteredPapers.length === 0 ? (
                    <div className="p-4 text-center text-xs text-muted-foreground">
                      No papers matching "{filterQuery}"
                    </div>
                  ) : (
                    filteredPapers.map((paper) => {
                      const isSelected =
                        paper.filename.toLowerCase() ===
                        selectedPaper.toLowerCase();
                      return (
                        <button
                          key={paper.filename}
                          type="button"
                          onClick={() => {
                            onSelectPaper(paper.filename);
                            setIsOpen(false);
                            setFilterQuery("");
                          }}
                          className={`flex w-full items-center justify-between gap-2.5 rounded-xl p-2.5 text-left text-xs transition-colors cursor-pointer ${
                            isSelected
                              ? "bg-primary/15 text-primary font-medium border border-primary/25"
                              : "text-foreground hover:bg-secondary/60 hover:text-foreground"
                          }`}
                        >
                          <div className="flex items-start gap-2.5 min-w-0 flex-1">
                            <FileText
                              className={`h-4 w-4 mt-0.5 shrink-0 ${
                                isSelected ? "text-primary" : "text-muted-foreground"
                              }`}
                            />
                            <div className="min-w-0 flex-1">
                              <span
                                className="truncate block font-medium"
                                title={paper.filename}
                              >
                                {paper.filename}
                              </span>
                              <span className="text-[11px] text-muted-foreground block mt-0.5">
                                {paper.uploaded_at
                                  ? `Uploaded ${paper.uploaded_at}`
                                  : "Uploaded recently"}
                              </span>
                            </div>
                          </div>
                          {isSelected && (
                            <Check className="h-4 w-4 text-primary shrink-0" />
                          )}
                        </button>
                      );
                    })
                  )}
                </div>

                {/* Footer link to upload */}
                <div className="mt-2 border-t border-border/50 pt-2 px-1 flex justify-between items-center text-[11px] text-muted-foreground">
                  <span>
                    {papers.length} {papers.length === 1 ? "paper" : "papers"} total
                  </span>
                  <Link
                    to="/dashboard/upload"
                    className="text-primary hover:underline inline-flex items-center gap-1 font-medium"
                    onClick={() => setIsOpen(false)}
                  >
                    <Upload className="h-3 w-3" /> + Upload new PDF
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Card Footer: Subtitle / Info & Action Button */}
      {(subtitle || actionButton) && (
        <div className="mt-4 pt-3 border-t border-border/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="text-xs text-muted-foreground leading-relaxed">
            {subtitle}
          </div>
          {actionButton && (
            <div className="shrink-0 self-end sm:self-auto">
              {actionButton}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
