import { createFileRoute, Link } from "@tanstack/react-router";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { AnimatedBackground } from "@/components/site/animated-background";
import { Button } from "@/components/ui/button";
import { Bot, Search, FileText, Sparkles, Lightbulb, Database, FlaskConical, BookOpen, FileSpreadsheet, Presentation, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/features")({
  head: () => ({
    meta: [
      { title: "Features — ResearchX" },
      { name: "description", content: "Explore every capability of the ResearchX multi-agent research platform." },
      { property: "og:title", content: "ResearchX Features" },
      { property: "og:description", content: "10 AI agents, semantic search, RAG, IEEE reports and more." },
    ],
  }),
  component: FeaturesPage,
});

const FEATURES = [
  { icon: Search, title: "Paper Retrieval", desc: "Semantic search across 5M+ papers from arXiv, IEEE, ACM, Springer with relevance ranking, filters and citation graph traversal." },
  { icon: FileText, title: "PDF Analysis", desc: "Multi-page parsing, structural chunking, table & figure extraction and citation parsing." },
  { icon: Sparkles, title: "Research Summarization", desc: "Section-aware summaries with grounded citations, key contributions and reproducible findings." },
  { icon: Lightbulb, title: "Research Gap Detection", desc: "Cross-paper analysis surfaces unaddressed problems and novel research directions." },
  { icon: Database, title: "Dataset Recommendation", desc: "Curated, task-matched datasets with licensing, size and benchmark history." },
  { icon: FlaskConical, title: "Experiment Recommendation", desc: "Suggested models, baselines, metrics, training strategies and hardware requirements." },
  { icon: BookOpen, title: "Literature Survey", desc: "Auto-generate comparison tables across N papers with methods, results and gaps." },
  { icon: FileSpreadsheet, title: "IEEE Report Generator", desc: "Format-perfect IEEE reports with references, figures and equations." },
  { icon: Presentation, title: "PPT Generator", desc: "Themed presentation decks generated from your research package." },
  { icon: Bot, title: "Multi-Agent Coordination", desc: "Specialized agents coordinated by a planner using LangGraph workflows." },
];

function FeaturesPage() {
  return (
    <div className="relative min-h-screen">
      <Navbar />
      <section className="relative pt-32 pb-20">
        <AnimatedBackground variant="subtle" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex rounded-full glass px-3 py-1 text-xs uppercase tracking-wide text-[var(--electric)]">Features</span>
            <h1 className="mt-4 font-display text-4xl font-bold sm:text-6xl">
              The complete <span className="gradient-text">research stack</span>
            </h1>
            <p className="mt-4 text-muted-foreground">
              Every capability you need to go from a topic idea to a publishable report — in one platform.
            </p>
          </div>

          <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="rounded-2xl glass p-6 transition-transform hover:-translate-y-1">
                <div className="grid h-12 w-12 place-items-center rounded-xl gradient-primary-bg">
                  <f.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-16 text-center">
            <Button asChild variant="hero" size="lg">
              <Link to="/dashboard">Try the Workspace <ArrowRight className="h-4 w-4" /></Link>
            </Button>
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
