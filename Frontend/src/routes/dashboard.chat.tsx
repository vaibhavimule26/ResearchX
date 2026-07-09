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

function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);

  const [selectedPaper, setSelectedPaper] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState("");

  const [sessionId, setSessionId] = useState(
    () => `chat_${Date.now()}`
  );

  const loadSessions = async () => {
    try {
      const response = await getSessions();

      setSessions(
        response?.data?.sessions || []
      );
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const papersResponse = await getPapers();

        const uploadedPapers =
          papersResponse?.data?.papers || [];

        setPapers(uploadedPapers);

        if (uploadedPapers.length > 0) {
          setSelectedPaper(
            uploadedPapers[0].filename
          );
        }

        await loadSessions();
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load chat data"
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

      const response = await getSearchHistory(
        session.session_id
      );

      const history: HistoryItem[] =
        response?.data?.history || [];

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
            content: item.answer,
          });
        }
      });

      setMessages(loadedMessages);

      const historyPaper = history.find(
        (item) => item.paper_name
      )?.paper_name;

      if (historyPaper) {
        setSelectedPaper(historyPaper);
      }
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load chat history"
      );
    } finally {
      setLoadingHistory(false);
    }
  };

  const sendMessage = async (
    customQuery?: string
  ) => {
    const query = (
      customQuery ?? input
    ).trim();

    if (!query || loading) return;

    const userMessage: Message = {
      role: "user",
      content: query,
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setInput("");
    setError("");
    setLoading(true);

    try {
      const response = await searchPaper(
        query,
        sessionId,
        selectedPaper || null
      );

      const answer =
        response?.data?.answer ||
        "No answer received.";

      const assistantMessage: Message = {
        role: "assistant",
        content: answer,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      await loadSessions();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Search failed"
      );
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

  return (
    <div className="grid h-[calc(100vh-7rem)] gap-4 lg:grid-cols-[260px_1fr]">
      <aside className="hidden overflow-hidden rounded-2xl glass p-4 lg:flex lg:flex-col">
        <Button
          variant="hero"
          className="w-full"
          onClick={startNewChat}
        >
          <Sparkles className="h-4 w-4" />
          New chat
        </Button>

        <div className="mt-4 text-xs uppercase tracking-wider text-muted-foreground">
          Research Paper
        </div>

        <select
          value={selectedPaper}
          onChange={(event) =>
            setSelectedPaper(event.target.value)
          }
          className="mt-2 w-full rounded-lg border border-border/60 bg-secondary/40 px-3 py-2 text-sm"
        >
          {papers.length === 0 && (
            <option value="">
              No papers uploaded
            </option>
          )}

          {papers.map((paper, index) => (
            <option
              key={`${paper.filename}-${index}`}
              value={paper.filename}
            >
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

        <div className="mt-3 border-t border-border/40 pt-3">
          <div className="text-xs text-muted-foreground">
            Current session
          </div>

          <div className="mt-1 truncate text-xs">
            {sessionId}
          </div>
        </div>
      </aside>

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

                <h2 className="mt-4 text-xl font-semibold">
                  Ask ResearchX
                </h2>

                <p className="mt-2 text-sm text-muted-foreground">
                  Select a research paper and ask a question.
                </p>
              </div>
            )}

            {!loadingHistory &&
              messages.map((message, index) => (
                <div
                  key={index}
                  className="flex gap-3"
                >
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
                      {message.role === "user"
                        ? "You"
                        : "ResearchX"}
                    </div>

                    <div className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </div>

                    {message.role === "assistant" && (
                      <div className="mt-3 flex gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                        >
                          <Copy className="h-3.5 w-3.5" />
                          Copy
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
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

        <div className="border-t border-border/50 p-4">
          <div className="mx-auto max-w-3xl">
            <div className="mb-2 flex flex-wrap gap-1.5">
              {SUGGESTED.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() =>
                    sendMessage(suggestion)
                  }
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
                onChange={(event) =>
                  setInput(event.target.value)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();
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
                disabled={
                  loading ||
                  loadingHistory ||
                  !input.trim()
                }
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