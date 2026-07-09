import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { Download, Play, Palette } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/ppt")({
  head: () => ({ meta: [{ title: "PPT Generator — ResearchX" }] }),
  component: PptPage,
});

const SLIDES = [
  { t: "Multimodal RAG for Scientific QA", s: "Ada Lovelace · Alan Turing · ResearchX Labs", kind: "title" },
  { t: "Motivation", s: "Scientific reasoning needs more than text.", kind: "content" },
  { t: "Background: RAG", s: "Retrieve → augment → generate.", kind: "content" },
  { t: "Our Method", s: "Modality-aware retrieval + grounded decoding.", kind: "content" },
  { t: "Architecture", s: "SigLIP retriever · LLaVA-NeXT generator.", kind: "diagram" },
  { t: "Datasets", s: "ScienceQA · OK-VQA · MMLU-Pro.", kind: "content" },
  { t: "Results", s: "+7.2 EM over text-only baseline.", kind: "chart" },
  { t: "Ablations", s: "Each component contributes 2–4 points.", kind: "chart" },
  { t: "Limitations", s: "Latency 1.8×; visual OOD hallucinations.", kind: "content" },
  { t: "Conclusion & Future Work", s: "Toward grounded scientific copilots.", kind: "content" },
];

const THEMES = [
  { name: "Aurora", colors: ["oklch(0.62 0.23 295)", "oklch(0.7 0.2 240)"] },
  { name: "Midnight", colors: ["oklch(0.2 0.04 270)", "oklch(0.4 0.1 270)"] },
  { name: "Sunset", colors: ["oklch(0.7 0.2 30)", "oklch(0.78 0.16 75)"] },
  { name: "Forest", colors: ["oklch(0.55 0.15 160)", "oklch(0.7 0.2 200)"] },
];

function PptPage() {
  const [active, setActive] = useState(0);
  const [theme, setTheme] = useState(0);
  const t = THEMES[theme];
  const gradient = `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})`;

  return (
    <div>
      <PageHeader
        title="Presentation Generator"
        subtitle="Auto-generated deck from your IEEE report."
        action={
          <div className="flex gap-2">
            <Button variant="glass"><Play className="h-4 w-4" /> Present</Button>
            <Button variant="hero"><Download className="h-4 w-4" /> Export PPTX</Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          <motion.div
            key={active}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="aspect-video w-full overflow-hidden rounded-2xl shadow-2xl"
            style={{ background: gradient }}
          >
            <div className="relative h-full w-full p-10 text-white">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.2),transparent_50%)]" />
              <div className="relative flex h-full flex-col justify-center">
                <div className="text-xs uppercase tracking-[0.3em] opacity-70">Slide {active + 1} / {SLIDES.length}</div>
                <h2 className="mt-3 font-display text-4xl font-bold sm:text-5xl">{SLIDES[active].t}</h2>
                <p className="mt-3 text-lg opacity-90">{SLIDES[active].s}</p>
              </div>
              <div className="absolute bottom-6 right-6 text-xs opacity-60">ResearchX</div>
            </div>
          </motion.div>

          <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
            {SLIDES.map((s, i) => (
              <button
                key={i}
                onClick={() => setActive(i)}
                className={`aspect-video overflow-hidden rounded-xl border text-left transition ${
                  i === active ? "border-[var(--electric)] ring-2 ring-[var(--electric)]/30" : "border-border/60"
                }`}
                style={{ background: gradient }}
              >
                <div className="flex h-full flex-col justify-end p-2 text-white">
                  <div className="text-[9px] opacity-70">#{i + 1}</div>
                  <div className="line-clamp-2 text-[10px] font-medium">{s.t}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <aside className="space-y-4">
          <div className="rounded-2xl glass p-5">
            <div className="flex items-center gap-2"><Palette className="h-4 w-4 text-[var(--electric)]" /><h3 className="font-semibold">Theme</h3></div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {THEMES.map((th, i) => (
                <button
                  key={th.name}
                  onClick={() => setTheme(i)}
                  className={`rounded-xl border p-3 text-left text-xs ${i === theme ? "border-[var(--electric)]" : "border-border/60"}`}
                >
                  <div className="h-10 w-full rounded-md" style={{ background: `linear-gradient(135deg, ${th.colors[0]}, ${th.colors[1]})` }} />
                  <div className="mt-2 font-medium">{th.name}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl glass p-5">
            <h3 className="font-semibold">Outline</h3>
            <ol className="mt-3 space-y-1 text-sm text-muted-foreground">
              {SLIDES.map((s, i) => (
                <li
                  key={i}
                  onClick={() => setActive(i)}
                  className={`cursor-pointer rounded-md px-2 py-1 ${i === active ? "bg-accent text-foreground" : "hover:text-foreground"}`}
                >
                  {i + 1}. {s.t}
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </div>
  );
}
