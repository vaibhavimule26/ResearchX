import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Send,
  Copy,
  RotateCcw,
  Sparkles,
  User,
  Bot,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import {
  getPapers,
  searchPaper,
  getSessions,
  getSearchHistory,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/chat")({
  head: () => ({
    meta: [{ title: "AI Chat — ResearchX" }],
  }),
  component: ChatPage,
});

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Paper = {
  filename: string;
  uploaded_at?: string;
};

type Session = {
  session_id: string;
  title: string;
  paper_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

type HistoryItem = {
  query?: string;
  answer?: string;
  paper_name?: string | null;
};

const SUGGESTED = [
  "Summarize this research paper",
  "What is the main methodology?",
  "List the key contributions",
];

// Complete Symbol & Metadata Stripper
function stripAllSymbols(raw: unknown): string {
  if (!raw) return "No response available.";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.data?.answer ||
      obj?.results?.summary?.output ||
      obj?.results?.gaps?.output ||
      obj?.results?.datasets?.output ||
      obj?.results?.experiments?.output ||
      obj?.output ||
      obj?.answer ||
      obj?.result ||
      "";

    if (!text && obj?.results && typeof obj.results === "object") {
      const first = Object.values(obj.results)[0] as any;
      if (first?.output) text = first.output;
    }
  } else if (typeof raw === "string") {
    const trimmed = raw.trim();
    try {
      const parsed = JSON.parse(trimmed.replace(/'/g, '"'));
      return stripAllSymbols(parsed);
    } catch {
      const match = trimmed.match(
        /['"]output['"]\s*:\s*['"]([\s\S]*?)['"]\s*(?:,\s*['"]|\})/
      );
      text = match && match[1] ? match[1] : trimmed;
    }
  } else {
    text = String(raw);
  }

  return text
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "")
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/^\s*[\*\-]\s+/gm, "• ")
    .replace(/`{1,3}(.*?)`{1,3}/g, "$1")
    .replace(/`+/g, "")
    .replace(/---+|___+/g, "")
    .replace(/\$\$(.*?)\$\$/g, "$1")
    .replace(/\$(.*?)\$/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);

  const [selectedPaper, setSelectedPaper] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState("");

  const [sessionId, setSessionId] = useState(() => `chat_${Date.now()}`);

  const loadSessions = async () => {
    try {
      const response = await getSessions();
      setSessions(response?.data?.sessions || []);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const papersResponse = await getPapers();
        const uploadedPapers: Paper[] = papersResponse?.data?.papers || [];

        setPapers(uploadedPapers);

        if (uploadedPapers.length > 0) {
          setSelectedPaper(uploadedPapers[0].filename);
        }

        await loadSessions();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load chat data"
        );
      }
    };

    loadInitialData();
  }, []);

  const openSession = async (session: Session) => {
    if (loading || loadingHistory) return;

    try {
      setLoadingHistory(true);
      setError("");
      setSessionId(session.session_id);

      if (session.paper_name) {
        setSelectedPaper(session.paper_name);
      }

      const response = await getSearchHistory(session.session_id);
      const history: HistoryItem[] = response?.data?.history || [];

      const loadedMessages: Message[] = [];

      history.forEach((item) => {
        if (item.query) {
          loadedMessages.push({
            role: "user",
            content: item.query,
          });
        }

        if (item.answer) {
          loadedMessages.push({
            role: "assistant",
            content: stripAllSymbols(item.answer),
          });
        }
      });

      setMessages(loadedMessages);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load chat history"
      );
    } finally {
      setLoadingHistory(false);
    }
  };

  const sendMessage = async (customQuery?: string) => {
    const query = (customQuery ?? input).trim();
    if (!query || loading) return;

    const userMessage: Message = {
      role: "user",
      content: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const response = await searchPaper(query, sessionId, selectedPaper || null);

      const cleanAnswer = stripAllSymbols(
        response?.data?.answer ?? response?.data ?? response
      );

      const assistantMessage: Message = {
        role: "assistant",
        content: cleanAnswer,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      await loadSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setInput("");
    setError("");
    setSessionId(`chat_${Date.now()}`);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="grid h-[calc(100vh-7rem)] gap-4 lg:grid-cols-[260px_1fr]">
      {/* Sidebar */}
      <aside className="hidden overflow-hidden rounded-2xl glass p-4 lg:flex lg:flex-col">
        <Button variant="hero" className="w-full" onClick={startNewChat}>
          <Sparkles className="h-4 w-4" />
          New chat
        </Button>

        <div className="mt-4 text-xs uppercase tracking-wider text-muted-foreground">
          Research Paper
        </div>

        <select
          value={selectedPaper}
          onChange={(e) => setSelectedPaper(e.target.value)}
          className="mt-2 w-full rounded-lg border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
        >
          {papers.length === 0 && <option value="">No papers uploaded</option>}
          {papers.map((paper, idx) => (
            <option key={`${paper.filename}-${idx}`} value={paper.filename}>
              {paper.filename}
            </option>
          ))}
        </select>

        <div className="mt-5 text-xs uppercase tracking-wider text-muted-foreground">
          History
        </div>

        <ul className="mt-2 flex-1 space-y-1 overflow-auto">
          {sessions.length === 0 ? (
            <li className="px-3 py-2 text-xs text-muted-foreground">
              No chat history yet
            </li>
          ) : (
            sessions.map((session) => (
              <li key={session.session_id}>
                <button
                  onClick={() => openSession(session)}
                  disabled={loadingHistory}
                  className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    session.session_id === sessionId
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                  title={session.title}
                >
                  {session.title || "New Chat"}
                </button>
              </li>
            ))
          )}
        </ul>
      </aside>

      {/* Main Chat Area */}
      <div className="flex min-h-0 flex-col rounded-2xl glass">
        <div className="flex-1 overflow-auto p-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {loadingHistory && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                Loading conversation...
              </div>
            )}

            {!loadingHistory && messages.length === 0 && (
              <div className="py-16 text-center">
                <Bot className="mx-auto h-10 w-10 text-[var(--electric)]" />
                <h2 className="mt-4 text-xl font-semibold">Ask ResearchX</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Select a research paper and ask any question.
                </p>
              </div>
            )}

            {!loadingHistory &&
              messages.map((message, index) => (
                <div key={index} className="flex gap-3">
                  <div
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-xl ${
                      message.role === "user"
                        ? "bg-secondary"
                        : "gradient-primary-bg"
                    }`}
                  >
                    {message.role === "user" ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4 text-primary-foreground" />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="text-xs text-muted-foreground">
                      {message.role === "user" ? "You" : "ResearchX"}
                    </div>

                    <div className="mt-2 whitespace-pre-line text-sm leading-relaxed text-foreground/90 font-normal">
                      {message.content}
                    </div>

                    {message.role === "assistant" && (
                      <div className="mt-3 flex gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(message.content)}
                        >
                          <Copy className="h-3.5 w-3.5" />
                          Copy
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const previousUserMsg = messages
                              .slice(0, index)
                              .reverse()
                              .find((m) => m.role === "user");
                            if (previousUserMsg) {
                              sendMessage(previousUserMsg.content);
                            }
                          }}
                          disabled={loading}
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Regenerate
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

            {loading && (
              <div className="flex gap-3">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl gradient-primary-bg">
                  <Bot className="h-4 w-4 text-primary-foreground" />
                </div>
                <div className="text-sm text-muted-foreground">
                  ResearchX is analyzing the paper...
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Input Bar */}
        <div className="border-t border-border/50 p-4">
          <div className="mx-auto max-w-3xl">
            <div className="mb-2 flex flex-wrap gap-1.5">
              {SUGGESTED.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  disabled={loading || loadingHistory}
                  className="rounded-full border border-border/60 bg-secondary/40 px-3 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            <div className="flex items-end gap-2 rounded-2xl border border-border/60 bg-secondary/40 p-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                rows={1}
                placeholder="Ask anything about your research…"
                className="min-h-10 resize-none border-0 bg-transparent focus-visible:ring-0"
              />

              <Button
                variant="hero"
                size="icon"
                onClick={() => sendMessage()}
                disabled={loading || loadingHistory || !input.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}