import { createFileRoute } from "@tanstack/react-router";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { AnimatedBackground } from "@/components/site/animated-background";

export const Route = createFileRoute("/docs")({
  head: () => ({
    meta: [
      { title: "Documentation — ResearchX" },
      { name: "description", content: "ResearchX developer and researcher documentation." },
      { property: "og:title", content: "ResearchX Docs" },
      { property: "og:description", content: "Learn how to use every ResearchX agent and capability." },
    ],
  }),
  component: DocsPage,
});

const SECTIONS = [
  {
    title: "Getting Started",
    items: ["Quickstart", "Create your first research session", "Connecting your library", "Keyboard shortcuts"],
  },
  {
    title: "Agents",
    items: ["Coordinator Agent", "Paper Retrieval Agent", "PDF Analysis Agent", "Summary Agent", "Gap Detection Agent"],
  },
  {
    title: "Outputs",
    items: ["IEEE Report Format", "Presentation Themes", "Exporting Surveys", "Citations & References"],
  },
  {
    title: "API",
    items: ["Authentication", "Sessions", "Streaming responses", "Webhooks"],
  },
];

function DocsPage() {
  return (
    <div className="relative min-h-screen">
      <Navbar />
      <section className="relative pt-32 pb-20">
        <AnimatedBackground variant="subtle" />
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-display text-4xl font-bold sm:text-5xl">Documentation</h1>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            Everything you need to build with ResearchX — agents, outputs and APIs.
          </p>
          <div className="mt-12 grid gap-5 sm:grid-cols-2">
            {SECTIONS.map((s) => (
              <div key={s.title} className="rounded-2xl glass p-6">
                <h3 className="font-semibold">{s.title}</h3>
                <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                  {s.items.map((i) => (
                    <li key={i} className="cursor-pointer hover:text-foreground">{i} →</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
