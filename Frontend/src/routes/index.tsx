import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  Search, FileText, Sparkles, Lightbulb, Database, FlaskConical,
  BookOpen, FileSpreadsheet, Presentation, Network, GitBranch, Workflow as WorkflowIcon,
  Bot, Brain, Layers, ArrowRight, Play, Calendar, Check, X,
  Zap, Clock, Target, Shield, Globe, Cpu, ChevronDown, Quote, Star,
} from "lucide-react";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { AnimatedBackground, FloatingParticles } from "@/components/site/animated-background";
import { Button } from "@/components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ResearchX —AI Multi-Agent Research Assistant" },
      {
        name: "description",
        content:
          "Upload research papers, analyze them using specialized AI agents, discover research gaps, generate IEEE reports, and create professional presentations—all from one intelligent platform",
      },
      { property: "og:title", content: "ResearchX — AI Research OS" },
      {
        property: "og:description",
        content: "From paper discovery to IEEE reports — fully automated with multi-agent AI.",
      },
    ],
  }),
  component: LandingPage,
});

function LandingPage() {
  
  return (
  <div className="relative min-h-screen overflow-x-hidden">
    <Navbar />
      
      <Hero />
      <Stats />
      <Features />
      <Workflow />
      <AgentShowcase />
      <Comparison />
      <Testimonials />
      <FAQ />
      <CTA />
      <Footer />
    </div>
  );
}

/* ---------------- HERO ---------------- */
function Hero() {
  return (
    <section className="relative isolate overflow-hidden pt-32 pb-24 sm:pt-40">
      <AnimatedBackground />
      <FloatingParticles />
      <div className="mx-auto grid max-w-7xl gap-16 px-4 sm:px-6 lg:grid-cols-2 lg:items-center lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 rounded-full glass px-3 py-1.5 text-xs">
            <span className="flex h-2 w-2">
              <span className="absolute h-2 w-2 animate-ping rounded-full bg-[var(--electric)]/60" />
              <span className="h-2 w-2 rounded-full bg-[var(--electric)]" />
            </span>
            <span className="text-muted-foreground">Powered by 10 specialized AI agents</span>
          </div>
          <h1 className="mt-6 font-display text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
            AI Multi-Agent <br />
<span className="gradient-text">
Research Assistant
</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted-foreground">
            ResearchX automates the complete research workflow — from paper discovery and
            PDF analysis to gap detection, experiment planning, IEEE report generation
            and presentation creation. One platform. Ten agents. Endless research.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
  <span className="rounded-full border border-border/60 px-4 py-2 text-sm">
    ✓ 10 AI Agents
  </span>

  <span className="rounded-full border border-border/60 px-4 py-2 text-sm">
    ✓ RAG Powered
  </span>

  <span className="rounded-full border border-border/60 px-4 py-2 text-sm">
    ✓ IEEE Reports
  </span>

  <span className="rounded-full border border-border/60 px-4 py-2 text-sm">
    ✓ PPT Generator
  </span>
</div>
          <div className="mt-6 flex flex-wrap gap-3">
  <Button asChild variant="hero" size="lg">
    <Link to="/register">
      Get Started Free
    </Link>
  </Button>

  <Button asChild variant="outline" size="lg">
    <a href="#features">
      Learn More
    </a>
  </Button>

  <Button variant="glass" size="lg">
    <Play className="h-4 w-4" />
    Watch Demo
  </Button>

  <Button variant="ghost" size="lg">
    <Calendar className="h-4 w-4" />
    Book Demo
  </Button>
</div>
          <div className="mt-10 flex items-center gap-6 text-xs text-muted-foreground">
            <div>
              <div className="flex">
                {[0, 1, 2, 3, 4].map((i) => (
                  <Star key={i} className="h-3 w-3 fill-[var(--warning)] text-[var(--warning)]" />
                ))}
              </div>
              <p className="mt-1">4.9 / 5 from 1,200+ researchers</p>
            </div>
            <div className="h-8 w-px bg-border" />
            Built for students, researchers and academic professionals.
          </div>
        </motion.div>

        <HeroVisual />
      </div>
    </section>
  );
}

function HeroVisual() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9, delay: 0.2 }}
      className="relative mx-auto aspect-square w-full max-w-lg"
    >
      {/* Central brain */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <div className="relative">
          <div className="absolute -inset-16 rounded-full bg-[radial-gradient(circle,oklch(0.62_0.23_295_/_0.4),transparent_70%)] animate-pulse-glow" />
          <div className="relative grid h-32 w-32 place-items-center rounded-3xl gradient-primary-bg glow-primary">
            <Brain className="h-14 w-14 text-primary-foreground" />
          </div>
        </div>
      </div>

      {/* Orbit nodes */}
      {[
        { icon: Search, angle: 0, label: "Search" },
        { icon: FileText, angle: 60, label: "PDF" },
        { icon: Database, angle: 120, label: "Data" },
        { icon: FlaskConical, angle: 180, label: "Lab" },
        { icon: BookOpen, angle: 240, label: "Survey" },
        { icon: Presentation, angle: 300, label: "PPT" },
      ].map((n, i) => {
        const r = 180;
        const rad = (n.angle * Math.PI) / 180;
        const x = Math.cos(rad) * r;
        const y = Math.sin(rad) * r;
        return (
          <motion.div
            key={i}
            className="absolute left-1/2 top-1/2"
            style={{ x, y }}
            animate={{ y: [y - 6, y + 6, y - 6] }}
            transition={{ duration: 4 + i, repeat: Infinity, ease: "easeInOut" }}
          >
            <div className="-translate-x-1/2 -translate-y-1/2">
              <div className="glass-strong grid h-14 w-14 place-items-center rounded-2xl">
                <n.icon className="h-6 w-6 text-[var(--electric)]" />
              </div>
            </div>
          </motion.div>
        );
      })}

      {/* Floating research cards */}
      <motion.div
        className="absolute -left-4 top-4 w-44 rounded-2xl glass p-3 animate-float-slow"
        animate={{ rotate: [-2, 2, -2] }}
        transition={{ duration: 8, repeat: Infinity }}
      >
        <div className="text-[10px] uppercase tracking-wide text-[var(--electric)]">Paper</div>
        <div className="mt-1 text-xs font-medium">Attention Is All You Need</div>
        <div className="mt-1 text-[10px] text-muted-foreground">Vaswani et al. · 2017</div>
      </motion.div>
      <motion.div
        className="absolute -right-2 bottom-12 w-48 rounded-2xl glass p-3"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 6, repeat: Infinity }}
      >
        <div className="text-[10px] uppercase tracking-wide text-[var(--purple-glow)]">Summary</div>
        <div className="mt-1 text-xs font-medium">Transformer architecture replaces recurrence with attention…</div>
      </motion.div>
      <motion.div
        className="absolute bottom-0 left-8 w-40 rounded-2xl glass p-3"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 7, repeat: Infinity }}
      >
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
          <span className="text-[10px] text-muted-foreground">Agent active</span>
        </div>
        <div className="mt-1 text-xs font-medium">Gap detection · 67%</div>
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-2/3 gradient-primary-bg" />
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ---------------- STATS ---------------- */
function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  useEffect(() => {
    if (!inView) return;
    const start = performance.now();
    const dur = 1600;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / dur);
      setVal(Math.floor(p * to));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [inView, to]);
  return (
    <span ref={ref}>
      {val.toLocaleString()}
      {suffix}
    </span>
  );
}

function Stats() {
  const items = [
    { value: 5_000_000, suffix: "+", label: "Research Papers" },
    { value: 100_000, suffix: "+", label: "Datasets" },
    { value: 10, suffix: "", label: "AI Agents" },
    { value: 5_000, suffix: "+", label: "Reports Generated" },
    { value: 1_000, suffix: "+", label: "Active Users" },
  ];
  return (
    <section className="relative py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-6 rounded-3xl glass-strong p-8 sm:grid-cols-2 lg:grid-cols-5">
          {items.map((it) => (
            <div key={it.label} className="text-center">
              <div className="font-display text-3xl font-bold gradient-text sm:text-4xl">
                <Counter to={it.value} suffix={it.suffix} />
              </div>
              <div className="mt-1 text-sm text-muted-foreground">{it.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- FEATURES ---------------- */
const FEATURES = [
  { icon: Search, title: "Paper Retrieval", desc: "Semantic search across 5M+ papers from arXiv, IEEE, ACM, Springer." },
  { icon: FileText, title: "PDF Analysis", desc: "Multi-page parsing, chunking, citation extraction and OCR." },
  { icon: Sparkles, title: "Research Summarization", desc: "Section-aware summaries with citations and key findings." },
  { icon: Lightbulb, title: "Research Gap Detection", desc: "Surface unaddressed problems and novel research directions." },
  { icon: Database, title: "Dataset Recommendation", desc: "Curated datasets matched to your domain and task." },
  { icon: FlaskConical, title: "Experiment Recommendation", desc: "Suggested models, baselines, metrics and training strategies." },
  { icon: BookOpen, title: "Literature Survey", desc: "Auto-generate comparison tables across N papers." },
  { icon: FileSpreadsheet, title: "IEEE Report Generator", desc: "Format-perfect IEEE reports ready for submission." },
  { icon: Presentation, title: "PPT Generator", desc: "Themed presentation decks generated from your research." },
  { icon: Network, title: "Semantic Search", desc: "Embedding-powered, meaning-first paper search." },
  { icon: Layers, title: "Vector Search", desc: "FAISS / pgvector pipelines tuned for academic corpora." },
  { icon: WorkflowIcon, title: "RAG Pipeline", desc: "Retrieval-augmented generation over your private library." },
  { icon: Bot, title: "Multi-Agent AI", desc: "Specialized agents coordinated by a central planner." },
  { icon: GitBranch, title: "CrewAI", desc: "Crew orchestration for collaborative agent execution." },
  { icon: Cpu, title: "LangGraph Workflow", desc: "Stateful graph workflows powering every research step." },
];

function Features() {
  return (
    <section id="features" className="relative py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Capabilities"
          title="Everything your research needs"
          subtitle="15+ integrated capabilities — one cohesive AI research operating system."
        />
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.4, delay: (i % 3) * 0.08 }}
              whileHover={{ y: -4 }}
              className="group relative overflow-hidden rounded-2xl glass p-6 transition-all hover:border-[oklch(0.62_0.23_295_/_0.4)]"
            >
              <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100"
                style={{ background: "radial-gradient(400px circle at var(--x,50%) var(--y,0%), oklch(0.62 0.23 295 / 0.15), transparent 60%)" }}
              />
              <div className="relative">
                <div className="grid h-11 w-11 place-items-center rounded-xl gradient-primary-bg">
                  <f.icon className="h-5 w-5 text-primary-foreground" />
                </div>
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- WORKFLOW ---------------- */
const WORKFLOW = [
  { icon: Bot, name: "Coordinator Agent", desc: "Plans the workflow and routes tasks." },
  { icon: Search, name: "Paper Retrieval Agent", desc: "Discovers relevant papers across databases." },
  { icon: FileText, name: "PDF Analysis Agent", desc: "Parses, chunks and structures PDFs." },
  { icon: Sparkles, name: "Summary Agent", desc: "Produces section-aware summaries." },
  { icon: Lightbulb, name: "Research Gap Agent", desc: "Finds limitations and opportunities." },
  { icon: Database, name: "Dataset Agent", desc: "Recommends matching datasets." },
  { icon: FlaskConical, name: "Experiment Agent", desc: "Suggests models, baselines and metrics." },
  { icon: BookOpen, name: "Literature Survey Agent", desc: "Builds comparison tables." },
  { icon: FileSpreadsheet, name: "IEEE Report Agent", desc: "Generates IEEE-formatted reports." },
  { icon: Presentation, name: "Presentation Agent", desc: "Builds themed PPT decks." },
];

function Workflow() {
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="How it works"
          title="An orchestrated multi-agent pipeline"
          subtitle="Every request flows through specialized agents — coordinated, traceable, parallel."
        />
        <div className="relative mt-14">
          <div className="grid gap-5 lg:grid-cols-5">
            {WORKFLOW.map((a, i) => (
              <motion.div
                key={a.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.35, delay: i * 0.05 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="group relative rounded-2xl glass p-5"
              >
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg">
                    <a.icon className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <span className="text-xs text-muted-foreground">Step {i + 1}</span>
                </div>
                <h3 className="mt-3 text-sm font-semibold">{a.name}</h3>
                <p className="mt-1 text-xs text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
                  {a.desc}
                </p>
                <p className="mt-1 text-xs text-muted-foreground group-hover:hidden">{a.desc.slice(0, 40)}…</p>
              </motion.div>
            ))}
          </div>
          <div className="mt-8 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <span>User input</span>
            <ArrowRight className="h-4 w-4" />
            <span className="gradient-text font-medium">Final Research Package</span>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------------- AGENT SHOWCASE ---------------- */
function AgentShowcase() {
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Meet the Agents"
          title="10 specialized AI researchers"
          subtitle="Each agent owns a focused responsibility. Together, they ship complete research."
        />
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {WORKFLOW.map((a, i) => (
            <motion.div
              key={a.name}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className="rounded-2xl glass p-5"
            >
              <div className="flex items-start justify-between">
                <div className="grid h-12 w-12 place-items-center rounded-2xl gradient-primary-bg">
                  <a.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-[var(--success)]/15 px-2 py-0.5 text-[10px] text-[var(--success)]">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--success)]" />
                  Online
                </span>
              </div>
              <h3 className="mt-4 text-sm font-semibold">{a.name}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{a.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- COMPARISON ---------------- */
function Comparison() {
  const rows = [
    { label: "Time to literature survey", t: "2–4 weeks", r: "Under 10 minutes", icon: Clock },
    { label: "Paper discovery", t: "Manual keyword search", r: "Semantic + vector search", icon: Search },
    { label: "PDF analysis", t: "Read & highlight by hand", r: "Automated chunking + RAG", icon: FileText },
    { label: "Gap detection", t: "Subjective and slow", r: "AI-surfaced opportunities", icon: Lightbulb },
    { label: "IEEE report drafting", t: "Days of formatting", r: "One-click generation", icon: FileSpreadsheet },
    { label: "Presentation deck", t: "Hours in PowerPoint", r: "Themed deck in minutes", icon: Presentation },
    { label: "Accuracy", t: "Variable", r: "Cited, verifiable", icon: Target },
    { label: "Workflow", t: "Disconnected tools", r: "Single platform", icon: WorkflowIcon },
  ];
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Why ResearchX"
          title="ResearchX vs Traditional Research"
          subtitle="See how a multi-agent OS changes the math on time, quality and effort."
        />
        <div className="mt-14 overflow-hidden rounded-3xl glass-strong">
          <div className="grid grid-cols-3 gap-4 border-b border-border/60 bg-secondary/30 p-5 text-xs font-semibold uppercase tracking-wide">
            <span>Capability</span>
            <span className="text-muted-foreground">Traditional</span>
            <span className="gradient-text">ResearchX</span>
          </div>
          {rows.map((r) => (
            <div key={r.label} className="grid grid-cols-3 items-center gap-4 border-b border-border/40 p-5 last:border-0 text-sm">
              <div className="flex items-center gap-3">
                <r.icon className="h-4 w-4 text-[var(--electric)]" />
                <span className="font-medium">{r.label}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <X className="h-4 w-4 text-destructive/80" /> {r.t}
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-[var(--success)]" /> {r.r}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {[
            { icon: Zap, label: "10x faster", desc: "End-to-end research in hours, not weeks." },
            { icon: Shield, label: "Trustworthy", desc: "Every claim is cited and traceable." },
            { icon: Globe, label: "Always on", desc: "Agents run in parallel, 24/7." },
          ].map((p) => (
            <div key={p.label} className="rounded-2xl glass p-5">
              <p.icon className="h-5 w-5 text-[var(--electric)]" />
              <h4 className="mt-3 font-semibold">{p.label}</h4>
              <p className="mt-1 text-sm text-muted-foreground">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- TESTIMONIALS ---------------- */
function Testimonials() {
  const items = [
    { name: "Dr. Aarav Mehta", role: "PhD, ML — IIT Bombay", quote: "ResearchX collapsed a six-week literature review into an afternoon. The IEEE report agent alone is worth it." },
    { name: "Prof. Lena Schmidt", role: "Researcher — ETH Zürich", quote: "The gap detection agent surfaces directions we hadn't considered. It's like having a senior collaborator on tap." },
    { name: "Maya Okafor", role: "Master's student — MIT", quote: "From PDF upload to a polished presentation deck in under 20 minutes. I shipped my thesis defense with it." },
    { name: "Yuki Tanaka", role: "Research Engineer — DeepMind", quote: "The RAG pipeline over our private corpus is the cleanest implementation I've used." },
    { name: "Carlos Ríos", role: "Scientist — CERN", quote: "Multi-agent orchestration that actually works. The coordinator's plans are auditable end to end." },
    { name: "Priya Nair", role: "Postdoc — Stanford NLP", quote: "Dataset and experiment recommendations have been spot-on across three different sub-fields." },
  ];
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Testimonials"
          title="Researchers building with ResearchX"
          subtitle="From PhD students to research engineers at frontier labs."
        />
        <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {items.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: (i % 3) * 0.08 }}
              className="rounded-2xl glass p-6"
            >
              <Quote className="h-5 w-5 text-[var(--purple-glow)]" />
              <p className="mt-3 text-sm leading-relaxed">{t.quote}</p>
              <div className="mt-5 flex items-center gap-3 border-t border-border/60 pt-4">
                <div className="grid h-10 w-10 place-items-center rounded-full gradient-primary-bg text-sm font-semibold text-primary-foreground">
                  {t.name.split(" ").map((s) => s[0]).slice(0, 2).join("")}
                </div>
                <div>
                  <div className="text-sm font-medium">{t.name}</div>
                  <div className="text-xs text-muted-foreground">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- FAQ ---------------- */
function FAQ() {
  const faqs = [
    { q: "What sources does ResearchX search?", a: "arXiv, IEEE Xplore, ACM, Springer, Semantic Scholar and OpenReview — with semantic and vector retrieval." },
    { q: "Can I upload my own PDFs?", a: "Yes. Drag-and-drop any number of PDFs; we parse, chunk and embed them into a private RAG index." },
    { q: "How accurate are the summaries?", a: "Every claim is grounded in source citations you can inspect and verify in the document viewer." },
    { q: "Does it support IEEE formatting?", a: "Yes — the report agent generates IEEE-formatted PDFs ready for submission, including references and figures." },
    { q: "Is my research data private?", a: "Your library is private by default. We never train on user content. Enterprise plans support self-hosting." },
    { q: "Which AI models power ResearchX?", a: "A mix of frontier LLMs orchestrated through LangGraph and CrewAI, with domain-tuned embeddings for retrieval." },
  ];
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="FAQ"
          title="Questions, answered"
          subtitle="Everything you need to know before getting started."
        />
        <Accordion type="single" collapsible className="mt-10">
          {faqs.map((f) => (
            <AccordionItem key={f.q} value={f.q} className="border-border/60">
              <AccordionTrigger className="text-left text-base hover:no-underline">
                {f.q}
              </AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground">
                {f.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}

/* ---------------- CTA ---------------- */
function CTA() {
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl border border-border/60 p-12 text-center">
          <div className="absolute inset-0 gradient-primary-bg opacity-20" />
          <div className="absolute inset-0 grid-bg opacity-30" />
          <div className="relative">
            <h2 className="font-display text-4xl font-bold sm:text-5xl">
              Ship research at the <span className="gradient-text">speed of thought</span>
            </h2>
            <p className="mt-4 text-muted-foreground">
              Join 1,000+ researchers using ResearchX to discover, analyze and publish faster.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button asChild variant="hero" size="lg">
                <Link to="/register">Get Started Free <ArrowRight className="h-4 w-4" /></Link>
              </Button>
              <Button asChild variant="glass" size="lg">
                <Link to="/login">
  Login
</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------------- HELPERS ---------------- */
function SectionHeader({
  eyebrow, title, subtitle,
}: { eyebrow: string; title: string; subtitle?: string }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      <span className="inline-flex items-center gap-2 rounded-full glass px-3 py-1 text-xs uppercase tracking-wide text-[var(--electric)]">
        <ChevronDown className="h-3 w-3" /> {eyebrow}
      </span>
      <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-5xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-muted-foreground">{subtitle}</p>
      )}
    </div>
  );
}
