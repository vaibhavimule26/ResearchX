import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useState, useRef } from "react";
import {
  Search,
  Sparkles,
  Paperclip,
  FileText,
  Lightbulb,
  HelpCircle,
  Bot,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/dashboard/workspace")({
  head: () => ({ meta: [{ title: "AI Workspace — ResearchX" }] }),
  component: WorkspacePage,
});

const AGENT_ICON_MAP: Record<string, any> = {
  "Paper Retrieval": Search,
  Summary: FileText,
  "Gap Analysis": Lightbulb,
};

function WorkspacePage() {
  const [prompt, setPrompt] = useState("");
  const [agents, setAgents] = useState<any[]>([]);
  const [recentResearch, setRecentResearch] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<any[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<number[]>([]);
  const [summary, setSummary] = useState("");

  const [sessionId, setSessionId] = useState("");
  const [activeSessionId, setActiveSessionId] = useState("");
  const [agentResults, setAgentResults] = useState<Record<string, string>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);

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
        setActiveSessionId(data.session_id);
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

  const handleAttach = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload/pdf", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        alert("PDF uploaded successfully.");
      } else {
        alert("Upload failed.");
      }
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
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
      const response = await fetch("http://127.0.0.1:8000/analysis/recent");
      const data = await response.json();
      setRecentResearch(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadWorkspace = async (sessionId: string) => {
    try {
      setLoading(true);

      const response = await fetch(
        `http://127.0.0.1:8000/analysis/workspace/${sessionId}`
      );

      const data = await response.json();

      if (!data.success) {
        alert("Failed to restore workspace.");
        return;
      }

      setPrompt(data.topic);
      setPapers(data.papers || []);

      setSelectedPapers(
        (data.papers || []).map((_: any, index: number) => index)
      );

      setSessionId(data.session_id);
      setAgents(data.agents || []);
      setAgentResults(data.agent_results || {});
    } catch (err) {
      console.error(err);
      alert("Failed to restore workspace.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecentResearch();
  }, []);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <div className="mb-6">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">
            AI Workspace
          </div>
          <h1 className="mt-1 font-display text-3xl font-bold">
            What do you want to research today?
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Describe your topic. The coordinator will dispatch agents to handle
            the rest.
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
              <input
                type="file"
                accept=".pdf"
                ref={fileInputRef}
                className="hidden"
                onChange={handleFileChange}
              />

              <Button variant="glass" size="sm" onClick={handleAttach}>
                <Paperclip className="h-4 w-4" />
                Attach PDF
              </Button>
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

        <div className="mt-6 rounded-2xl glass p-5">
          <h3 className="font-semibold">Suggested research starters</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {[
              "Survey of multi-agent LLM orchestration patterns",
              "Compare RAG vs long-context for QA accuracy",
              "Gaps in evaluation of agentic frameworks",
              "Dataset recommendations for medical NER (2024)",
            ].map((s) => (
              <button
                key={s}
                onClick={() => setPrompt(s)}
                className="rounded-xl border border-border/40 bg-secondary/30 p-3 text-left text-sm hover:bg-accent"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 rounded-2xl glass p-5">
          <h3 className="font-semibold">Top Research Papers</h3>

          {papers.length === 0 ? (
            <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-border/40 py-12 text-center">
              <Search className="mb-4 h-10 w-10 text-muted-foreground" />

              <h4 className="text-lg font-semibold">
                No Research Papers Yet
              </h4>

              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Enter a research topic above and click
                <span className="font-medium"> Search Papers </span>
                to discover relevant research papers.
              </p>
            </div>
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
                        setSelectedPapers((prev) =>
                          prev.includes(index)
                            ? prev.filter((i) => i !== index)
                            : [...prev, index]
                        );
                      }}
                    />

                    <div className="flex-1">
                      <h4 className="font-medium">{paper.title}</h4>

                      <p className="text-xs text-muted-foreground mt-1">
                        {paper.authors?.join(", ") || "Unknown Authors"}
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Published: {paper.published || "N/A"}
                      </p>

                      {paper.pdf_url && (
                        <a
                          href={paper.pdf_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-500 text-sm"
                        >
                          View PDF
                        </a>
                      )}
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
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                agents.length > 0
                  ? "bg-[var(--success)]/15 text-[var(--success)]"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {agents.length > 0 ? "Running" : "Idle"}
            </span>
          </div>
          <div className="mt-4 space-y-3">
            {agents.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/40 py-12 text-center">
                <Bot className="mb-4 h-10 w-10 text-muted-foreground" />

                <h4 className="text-lg font-semibold">
                  No Active Research Session
                </h4>

                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Search research papers and click
                  <span className="font-medium"> Run AI Research </span>
                  to start your workspace session.
                </p>
              </div>
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
                        <div
                          className={`grid h-9 w-9 place-items-center rounded-xl ${
                            isIdle ? "bg-muted" : "gradient-primary-bg"
                          }`}
                        >
                          <AgentIcon
                            className={`h-4 w-4 ${
                              isIdle
                                ? "text-muted-foreground"
                                : "text-primary-foreground"
                            }`}
                          />
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-medium">{a.agent}</div>
                          <div
                            className={`truncate text-xs ${
                              a.status === "Completed"
                                ? "text-green-500"
                                : "text-muted-foreground"
                            }`}
                          >
                            Status: {a.status}
                          </div>
                        </div>
                      </div>
                      <span
                        className={`h-2 w-2 rounded-full ${
                          isIdle
                            ? "bg-muted-foreground"
                            : "bg-[var(--success)] animate-pulse"
                        }`}
                      />
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
            <p className="mt-3 text-xs text-muted-foreground italic">
              No past sessions found.
            </p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {recentResearch.map((r: any, idx: number) => (
                <li
                  key={r.session_id || idx}
                  onClick={() => loadWorkspace(r.session_id)}
                  className="truncate rounded-lg p-2 cursor-pointer transition-colors hover:bg-accent hover:text-foreground"
                >
                  {r.topic}
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </div>
  );
}