import { createFileRoute } from "@tanstack/react-router";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { AnimatedBackground } from "@/components/site/animated-background";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — ResearchX" },
      { name: "description", content: "Why we are building ResearchX, the multi-agent AI research OS." },
      { property: "og:title", content: "About ResearchX" },
      { property: "og:description", content: "Our mission: give every researcher a team of AI collaborators." },
    ],
  }),
  component: AboutPage,
});

function AboutPage() {
  return (
    <div className="relative min-h-screen">
      <Navbar />
      <section className="relative pt-32 pb-20">
        <AnimatedBackground variant="subtle" />
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-display text-5xl font-bold">
            We're building the <span className="gradient-text">research OS</span> of the next decade.
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            ResearchX is a multi-agent platform that gives every researcher a team of AI collaborators —
            from discovering papers to drafting publication-ready reports. Our mission is to compress
            the cycle time of human knowledge.
          </p>
          <div className="mt-12 grid gap-5 sm:grid-cols-3">
            {[
              { k: "2024", v: "Founded in a research lab, for research labs." },
              { k: "10", v: "Specialized agents shipping in production." },
              { k: "1,000+", v: "Researchers across 40 countries." },
            ].map((b) => (
              <div key={b.k} className="rounded-2xl glass p-6">
                <div className="font-display text-3xl font-bold gradient-text">{b.k}</div>
                <p className="mt-2 text-sm text-muted-foreground">{b.v}</p>
              </div>
            ))}
          </div>
          <h2 className="mt-16 font-display text-3xl font-bold">Our principles</h2>
          <ul className="mt-6 space-y-4 text-muted-foreground">
            <li><strong className="text-foreground">Grounded in citations.</strong> Every claim our agents make is traceable to a source.</li>
            <li><strong className="text-foreground">Private by default.</strong> Your library is yours. We never train on user content.</li>
            <li><strong className="text-foreground">Designed for depth.</strong> ResearchX optimizes for understanding, not just summaries.</li>
            <li><strong className="text-foreground">Open ecosystem.</strong> First-class APIs and self-hosting for enterprise teams.</li>
          </ul>
        </div>
      </section>
      <Footer />
    </div>
  );
}
