import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Search, Filter, Bookmark, Download, Sparkles, FileText } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { searchDashboard, runAnalysis } from "@/lib/api";
import { useSearch, useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/papers")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: typeof search.paper === "string" ? search.paper : "",
  }),
  head: () => ({
    meta: [{ title: "Paper Search — ResearchX" }],
  }),
  component: PaperSearch,
});

const PAPERS = [
  { title: "Attention Is All You Need", authors: "Ashish Vaswani, Noam Shazeer, et al.", year: 2017, venue: "NeurIPS", citations: 121340, abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple architecture, the Transformer, based solely on attention mechanisms…", tags: ["Transformer", "Attention", "NLP"] },
  { title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", authors: "Patrick Lewis et al.", year: 2020, venue: "NeurIPS", citations: 8421, abstract: "We introduce RAG models which combine pre-trained parametric and non-parametric memory for language generation…", tags: ["RAG", "Retrieval", "Generation"] },
  { title: "LLaMA: Open and Efficient Foundation Language Models", authors: "Hugo Touvron et al.", year: 2023, venue: "arXiv", citations: 5210, abstract: "We introduce LLaMA, a collection of foundation language models ranging from 7B to 65B parameters trained on trillions of tokens…", tags: ["LLM", "Open Source"] },
  { title: "Toolformer: Language Models Can Teach Themselves to Use Tools", authors: "Timo Schick et al.", year: 2023, venue: "NeurIPS", citations: 1845, abstract: "We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass…", tags: ["Tools", "Agents"] },
  { title: "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", authors: "Jason Wei et al.", year: 2022, venue: "NeurIPS", citations: 9821, abstract: "We explore how generating a chain of thought significantly improves the ability of large language models to perform reasoning…", tags: ["Reasoning", "Prompting"] },
  { title: "Mistral 7B", authors: "Mistral AI Team", year: 2023, venue: "arXiv", citations: 1320, abstract: "Mistral 7B leverages grouped-query attention and sliding window attention to achieve strong performance at modest scale…", tags: ["LLM", "Efficient"] },
];

function PaperSearch() {
  const search = useSearch({ from: "/dashboard/papers" });
  const navigate = useNavigate();

  const [q, setQ] = useState(search.paper ?? "");
  const [papers, setPapers] = useState<any[]>([]);
  const [loadingPaper, setLoadingPaper] = useState<string | null>(null);

  useEffect(() => {
    if (search.paper) {
      setQ(search.paper);
    }
  }, [search.paper]);

  useEffect(() => {
    if (!q.trim()) {
      setPapers([]);
      return;
    }

    async function loadPapers() {
      try {
        const data = await searchDashboard(q);
        setPapers(data.results);
      } catch (err) {
        console.error(err);
      }
    }

    loadPapers();
  }, [q]);

  const handleSummary = async (paperName: string) => {
    try {
      setLoadingPaper(paperName);
      await runAnalysis(paperName, "summary");
      navigate({
        to: "/dashboard/summary",
        search: {
          paper: paperName,
        },
      });
    } catch (err) {
      console.error(err);
    } {
      setLoadingPaper(null);
    }
  };

  const filteredPapers =
    papers.length > 0
      ? papers
      : PAPERS.filter((paper) =>
          paper.title.toLowerCase().includes(q.toLowerCase())
        );

  return (
    <div>
      <PageHeader
        title="Paper Search"
        subtitle="Semantic search across 5M+ academic papers."
      />

      <div className="rounded-2xl glass p-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-1 min-w-[240px] items-center gap-2 rounded-xl bg-secondary/60 px-3">
            <Search className="h-4 w-4 text-muted-foreground" />

            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search papers..."
              className="border-0 bg-transparent focus-visible:ring-0"
            />
          </div>

          <Button variant="hero">Search</Button>

          <Button variant="glass">
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        </div>

        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {[
            "2024",
            "2023",
            "NeurIPS",
            "ICML",
            "Open Access",
            "Cited 1k+",
          ].map((c) => (
            <span
              key={c}
              className="rounded-full border border-border/60 bg-secondary/50 px-3 py-1 text-muted-foreground"
            >
              {c}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[200px_1fr]">
        <aside className="rounded-2xl glass p-4 text-sm h-fit">
          <div className="font-semibold">Refine</div>

          {[
            {
              l: "Year",
              o: ["2024", "2023", "2022", "2021"],
            },
            {
              l: "Venue",
              o: ["NeurIPS", "ICML", "ICLR", "ACL"],
            },
            {
              l: "Domain",
              o: ["NLP", "CV", "RL", "Theory"],
            },
          ].map((g) => (
            <div key={g.l} className="mt-4">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">
                {g.l}
              </div>

              <div className="mt-2 space-y-1">
                {g.o.map((o) => (
                  <label
                    key={o}
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                  >
                    <input type="checkbox" className="h-3.5 w-3.5 rounded" />
                    {o}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </aside>

        <div className="space-y-4">
          {filteredPapers.map((p: any) => (
            <div
              key={p.title}
              className="rounded-2xl glass p-5 hover:border-[oklch(0.62_0.23_295_/_0.4)]"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold leading-tight">
                    {p.title}
                  </h3>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {"uploaded_at" in p
                      ? `Uploaded: ${p.uploaded_at}`
                      : `${p.authors} · ${p.venue} ${p.year}`}
                  </p>
                </div>

                <Button variant="ghost" size="icon">
                  <Bookmark className="h-4 w-4" />
                </Button>
              </div>

              <p className="mt-3 text-sm text-muted-foreground">
                {"abstract" in p
                  ? p.abstract
                  : "Uploaded research paper"}
              </p>

              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-1.5">
                  {"tags" in p ? (
                    p.tags.map((tag: string) => (
                      <span
                        key={tag}
                        className="rounded-full bg-[var(--electric)]/10 px-2 py-0.5 text-[10px] text-[var(--electric)]"
                      >
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="rounded-full bg-[var(--electric)]/10 px-2 py-0.5 text-[10px] text-[var(--electric)]">
                      PDF
                    </span>
                  )}
                </div>

                <div className="flex gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={loadingPaper === p.title}
                    onClick={() => handleSummary(p.title)}
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    {loadingPaper === p.title ? "Generating..." : "Summarize"}
                  </Button>

                  

                  <Button
  variant="glass"
  size="sm"
  onClick={() =>
    window.open(
      `http://127.0.0.1:8000/papers/${encodeURIComponent(p.title)}`,
      "_blank"
    )
  }
>
  <Download className="h-3.5 w-3.5" />
  PDF
</Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}