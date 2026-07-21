import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Search, Upload, FileSpreadsheet, Presentation, Sparkles, BookOpen,
  Paperclip, Bot, FileText, Lightbulb, HelpCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
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

const AGENT_ICON_MAP: Record<string, any> = {
  "Paper Retrieval": Search,
  "Summary": FileText,
  "Gap Analysis": Lightbulb,
};

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
  const [agents, setAgents] = useState<any[]>([]);
  const [recentResearch, setRecentResearch] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<any[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<number[]>([]);
  const [summary, setSummary] = useState("");

  const [sessionId, setSessionId] = useState("");
  const [agentResults, setAgentResults] = useState<Record<string, string>>({});

  const searchPapers = async () => {
    if (!prompt.trim()) {
      alert("Please enter a research topic.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/analysis/search-papers",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            topic: prompt,
          }),
        }
      );

      const data = await response.json();

      setPapers(data.papers || []);

      // Select all papers by default
      setSelectedPapers(
        (data.papers || []).map((_: any, index: number) => index)
      );

    } catch (error) {
      console.error(error);
      alert("Failed to search papers.");
    } finally {
      setLoading(false);
    }
  };

  const runResearch = async () => {
    if (!prompt.trim()) {
      alert("Please enter a research topic.");
      return;
    }

    const chosenPapers = selectedPapers.map((idx) => papers[idx]);

    try {
      setLoading(true);

      const response = await fetch("http://127.0.0.1:8000/analysis/workspace", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: prompt,
          papers: chosenPapers,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setSessionId(data.session_id);
        setAgents(data.agents || []);
        setAgentResults({});
        loadRecentResearch();
      } else {
        alert("Failed to start research.");
      }
    } catch (error) {
      console.error(error);
      alert("Error starting research workflow.");
    } finally {
      setLoading(false);
    }
  };

  const runAgent = async (agentName: string) => {
    const chosenPapers = selectedPapers.map((idx) => papers[idx]);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analysis/run-agent",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            topic: prompt,
            papers: chosenPapers,
            agent: agentName,
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        setAgentResults((prev) => ({
          ...prev,
          [agentName]: data.result,
        }));

        setAgents((prev) =>
          prev.map((a) =>
            a.agent === agentName
              ? {
                  ...a,
                  status: "Completed",
                  progress: 100,
                }
              : a
          )
        );
      }
    } catch (error) {
      console.error(error);
      alert("Failed to run agent.");
    }
  };

  const loadRecentResearch = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analysis/recent"
      );
      const data = await response.json();
      setRecentResearch(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadRecentResearch();
  }, []);

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
            <Button
              variant="hero"
              size="sm"
              onClick={searchPapers}
              disabled={loading}
            >
              {loading ? "Searching..." : "Search Papers"}
              <Search className="h-4 w-4" />
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
          <h3 className="font-semibold">
            Top Research Papers
          </h3>

          {papers.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No papers found. Search a topic to begin.
            </p>
          ) : (
            <div className="mt-4 space-y-4">
              {papers.map((paper, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-border/40 p-4"
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={selectedPapers.includes(index)}
                      onChange={() => {
                        if (selectedPapers.includes(index)) {
                          setSelectedPapers(
                            selectedPapers.filter(i => i !== index)
                          );
                        } else {
                          setSelectedPapers([
                            ...selectedPapers,
                            index,
                          ]);
                        }
                      }}
                    />

                    <div className="flex-1">
                      <h4 className="font-medium">
                        {paper.title}
                      </h4>

                      <p className="text-xs text-muted-foreground mt-1">
                        {paper.authors.join(", ")}
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Published: {paper.published}
                      </p>

                      <a
                        href={paper.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-500 text-sm"
                      >
                        View PDF
                      </a>
                    </div>
                  </div>
                </div>
              ))}

              <Button
                variant="hero"
                onClick={runResearch}
                disabled={loading || selectedPapers.length === 0}
              >
                {loading ? "Running..." : "Run AI Research"}
              </Button>
            </div>
          )}
        </div>

        <div className="mt-6 rounded-2xl glass p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Active session</h3>
            <span className={`rounded-full px-2 py-0.5 text-xs ${agents.length > 0 ? "bg-[var(--success)]/15 text-[var(--success)]" : "bg-muted text-muted-foreground"}`}>
              {agents.length > 0 ? "Running" : "Idle"}
            </span>
          </div>
          <div className="mt-4 space-y-3">
            {agents.length === 0 ? (
              <p className="text-sm text-muted-foreground italic text-center py-4">
                No active session running. Enter a topic above to dispatch research agents.
              </p>
            ) : (
              agents.map((a) => {
                const AgentIcon = AGENT_ICON_MAP[a.agent] || HelpCircle;
                const isIdle = a.status === "Pending";

                return (
                  <motion.div
                    key={a.agent}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="rounded-xl border border-border/40 bg-secondary/30 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`grid h-9 w-9 place-items-center rounded-xl ${isIdle ? "bg-muted" : "gradient-primary-bg"}`}>
                          <AgentIcon className={`h-4 w-4 ${isIdle ? "text-muted-foreground" : "text-primary-foreground"}`} />
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-medium">{a.agent}</div>
                          <div className={`truncate text-xs ${a.status === "Completed" ? "text-green-500" : "text-muted-foreground"}`}>
                            Status: {a.status}
                          </div>
                        </div>
                      </div>
                      <span className={`h-2 w-2 rounded-full ${isIdle ? "bg-muted-foreground" : "bg-[var(--success)] animate-pulse"}`} />
                    </div>

                    <Button
                      className="mt-3"
                      disabled={a.status === "Completed"}
                      onClick={() => runAgent(a.agent)}
                    >
                      {a.status === "Completed" ? "Completed" : "Run"}
                    </Button>

                    {agentResults[a.agent] && (
                      <div className="mt-4 rounded-lg border p-3 text-sm whitespace-pre-wrap">
                        {agentResults[a.agent]}
                      </div>
                    )}
                  </motion.div>
                );
              })
            )}
          </div>
        </div>

        {summary && (
          <div className="mt-6 rounded-2xl glass p-5">
            <h3 className="font-semibold mb-3">Summary</h3>

            <div className="whitespace-pre-wrap text-sm text-muted-foreground">
              {summary}
            </div>
          </div>
        )}
      </div>

      <aside className="space-y-4">
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Recent Research</h3>
          {recentResearch.length === 0 ? (
            <p className="mt-3 text-xs text-muted-foreground italic">No past sessions found.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {recentResearch.map((r: any, idx: number) => (
                <li key={r.session_id || idx} className="truncate hover:text-foreground cursor-pointer">
                  {r.topic}
                </li>
              ))}
            </ul>
          )}
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