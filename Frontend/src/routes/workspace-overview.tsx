import { createFileRoute, Link } from "@tanstack/react-router";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { AnimatedBackground } from "@/components/site/animated-background";
import { Button } from "@/components/ui/button";
import { ArrowRight, MessageSquare, Search, Upload, FileText, BookOpen, Presentation } from "lucide-react";

export const Route = createFileRoute("/workspace-overview")({
  head: () => ({
    meta: [
      { title: "Workspace — ResearchX" },
      { name: "description", content: "Tour the ResearchX AI workspace: research, chat, papers, reports and presentations." },
      { property: "og:title", content: "ResearchX Workspace" },
      { property: "og:description", content: "Your AI research operating system, fully visualized." },
    ],
  }),
  component: WorkspaceOverview,
});

function WorkspaceOverview() {
  const blocks = [
    { icon: MessageSquare, title: "AI Workspace", desc: "ChatGPT-style research console with multi-agent execution." },
    { icon: Search, title: "Paper Search", desc: "Semantic search across millions of papers with rich filters." },
    { icon: Upload, title: "PDF Analysis", desc: "Drag, drop and analyze any research PDF in seconds." },
    { icon: FileText, title: "Summaries & Gaps", desc: "Auto-extracted summaries and research gap analysis." },
    { icon: BookOpen, title: "Literature Surveys", desc: "Comparison tables across N papers — exportable." },
    { icon: Presentation, title: "Reports & PPTs", desc: "IEEE reports and slide decks generated end-to-end." },
  ];
  return (
    <div className="relative min-h-screen">
      <Navbar />
      <section className="relative pt-32 pb-20">
        <AnimatedBackground variant="subtle" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-bold sm:text-6xl">
              A workspace built like an <span className="gradient-text">operating system</span>
            </h1>
            <p className="mt-4 text-muted-foreground">
              ResearchX is a full research OS — every tool in one place, every agent at your command.
            </p>
            <div className="mt-8">
              <Button asChild variant="hero" size="lg">
                <Link to="/dashboard">Open Workspace <ArrowRight className="h-4 w-4" /></Link>
              </Button>
            </div>
          </div>
          <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {blocks.map((b) => (
              <div key={b.title} className="rounded-2xl glass p-6">
                <div className="grid h-12 w-12 place-items-center rounded-xl gradient-primary-bg">
                  <b.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="mt-4 font-semibold">{b.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
