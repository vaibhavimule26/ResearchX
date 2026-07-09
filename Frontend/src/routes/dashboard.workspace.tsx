import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Search, Upload, FileSpreadsheet, Presentation, Sparkles, BookOpen,
  ArrowUp, Paperclip, Bot, FileText, Lightbulb, Database, FlaskConical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/dashboard/workspace")({
  head: () => ({ meta: [{ title: "AI Workspace — ResearchX" }] }),
  component: WorkspacePage,
});

const QUICK = [
  { icon: Search, label: "Search Papers" },
  { icon: Upload, label: "Upload PDF" },
  { icon: Sparkles, label: "Analyze Topic" },
  { icon: BookOpen, label: "Literature Survey" },
  { icon: FileSpreadsheet, label: "IEEE Report" },
  { icon: Presentation, label: "Generate PPT" },
];

const AGENTS = [
  { name: "Paper Retrieval", task: "Fetching 24 papers from arXiv", pct: 67, icon: Search },
  { name: "PDF Analysis", task: "Chunking 3 PDFs · pass 2/3", pct: 42, icon: FileText },
  { name: "Gap Detection", task: "Synthesizing cross-paper insights", pct: 18, icon: Lightbulb },
  { name: "Dataset Agent", task: "Idle — waiting on summary", pct: 0, icon: Database, idle: true },
];

const RECENT = [
  "Long-context attention mechanisms",
  "Sparse mixture of experts (MoE)",
  "Synthetic data for instruction tuning",
  "Retrieval over multimodal documents",
];

const SAVED = [
  { t: "Attention Is All You Need", a: "Vaswani et al." },
  { t: "LLaMA: Open and Efficient Foundation Models", a: "Touvron et al." },
  { t: "Toolformer", a: "Schick et al." },
];

const TIMELINE = [
  { time: "Now", text: "Coordinator agent dispatched 4 subtasks" },
  { time: "1m", text: "Paper Retrieval found 24 candidates" },
  { time: "3m", text: "PDF Analysis started on top-3 papers" },
  { time: "5m", text: "Summary agent queued" },
];

function WorkspacePage() {
  const [prompt, setPrompt] = useState("");
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <div className="mb-6">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">AI Workspace</div>
          <h1 className="mt-1 font-display text-3xl font-bold">What do you want to research today?</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Describe your topic. The coordinator will dispatch agents to handle the rest.
          </p>
        </div>

        <div className="rounded-3xl glass-strong p-4 sm:p-5">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your research topic… e.g. 'A literature survey on retrieval-augmented multimodal LLMs from 2023–2025, with experiment recommendations.'"
            rows={4}
            className="resize-none border-0 bg-transparent text-base focus-visible:ring-0"
          />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              <Button variant="glass" size="sm"><Paperclip className="h-4 w-4" /> Attach</Button>
              <Button variant="glass" size="sm"><Bot className="h-4 w-4" /> Choose agents</Button>
            </div>
            <Button variant="hero" size="sm">
              Run Research <ArrowUp className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {QUICK.map((q) => (
            <button
              key={q.label}
              className="group flex items-center gap-2 rounded-xl border border-border/60 bg-secondary/40 px-3 py-2.5 text-xs hover:bg-accent"
            >
              <q.icon className="h-4 w-4 text-[var(--electric)] transition-transform group-hover:scale-110" />
              <span className="truncate">{q.label}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 rounded-2xl glass p-5">
          <h3 className="font-semibold">Suggested research starters</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {[
              "Survey of multi-agent LLM orchestration patterns",
              "Compare RAG vs long-context for QA accuracy",
              "Gaps in evaluation of agentic frameworks",
              "Dataset recommendations for medical NER (2024)",
            ].map((s) => (
              <button key={s} className="rounded-xl border border-border/40 bg-secondary/30 p-3 text-left text-sm hover:bg-accent">
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 rounded-2xl glass p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Active session</h3>
            <span className="rounded-full bg-[var(--success)]/15 px-2 py-0.5 text-xs text-[var(--success)]">Running</span>
          </div>
          <div className="mt-4 space-y-3">
            {AGENTS.map((a) => (
              <motion.div
                key={a.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="rounded-xl border border-border/40 bg-secondary/30 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`grid h-9 w-9 place-items-center rounded-xl ${a.idle ? "bg-muted" : "gradient-primary-bg"}`}>
                      <a.icon className={`h-4 w-4 ${a.idle ? "text-muted-foreground" : "text-primary-foreground"}`} />
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{a.name}</div>
                      <div className="truncate text-xs text-muted-foreground">{a.task}</div>
                    </div>
                  </div>
                  <span className={`h-2 w-2 rounded-full ${a.idle ? "bg-muted-foreground" : "bg-[var(--success)] animate-pulse"}`} />
                </div>
                <Progress value={a.pct} className="mt-3" />
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <aside className="space-y-4">
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Recent Research</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {RECENT.map((r) => (
              <li key={r} className="truncate hover:text-foreground cursor-pointer">{r}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Saved Papers</h3>
          <ul className="mt-3 space-y-3 text-sm">
            {SAVED.map((p) => (
              <li key={p.t} className="rounded-xl border border-border/40 bg-secondary/30 p-3">
                <div className="truncate font-medium">{p.t}</div>
                <div className="text-xs text-muted-foreground">{p.a}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Activity Timeline</h3>
          <ul className="mt-4 space-y-3">
            {TIMELINE.map((t) => (
              <li key={t.text} className="flex gap-3 text-sm">
                <span className="text-xs text-muted-foreground w-10 shrink-0">{t.time}</span>
                <span className="text-muted-foreground">{t.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
