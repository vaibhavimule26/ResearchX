import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Copy,
  RotateCcw,
  Sparkles,
  User,
  Bot,
  FileText,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Trash2,
  UploadCloud,
  Check,
  BookOpen,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import {
  getPapers,
  searchPaper,
  getSessions,
  getSearchHistory,
  deleteSearchHistory,
  ChatSource,
} from "@/lib/api";
import { AgentEvaluationCard } from "@/components/dashboard/agent-evaluation-card";


export const Route = createFileRoute("/dashboard/chat")({
  validateSearch: (search: Record<string, unknown>) => ({
    paper: (search.paper as string) || "",
  }),
  head: () => ({
    meta: [{ title: "AI Chat — ResearchX" }],
  }),
  component: ChatPage,
});

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
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

const SUGGESTED_PROMPTS = [
  "What is the main objective of this paper?",
  "Summarize the proposed methodology",
  "What are the key research gaps identified?",
  "What datasets and benchmarks were used?",
  "What are the main experimental results?",
  "What limitations or future directions are mentioned?",
];

// Clean text formatting utility preserving markdown and cleaning accidental meta-headers
function formatAssistantResponse(raw: unknown): string {
  if (!raw) return "I couldn't find this information in the uploaded paper.";

  let text = "";

  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, any>;
    text =
      obj?.data?.answer ||
      obj?.answer ||
      obj?.results?.summary?.output ||
      obj?.output ||
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
      return formatAssistantResponse(parsed);
    } catch {
      const match = trimmed.match(
        /['"]output['"]\s*:\s*['"]([\s\S]*?)['"]\s*(?:,\s*['"]|\})/
      );
      text = match && match[1] ? match[1] : trimmed;
    }
  } else {
    text = String(raw);
  }

  // Sanitize text: decode escape sequences and strip robotic preambles / inline evidence brackets
  let cleaned = text
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "")
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    // Clean bracketed or parenthetical inline evidence tags
    .replace(/【\s*Evidence\s*\d+\s*】/g, "")
    .replace(/\[\s*Evidence\s*\d+[^\]]*\]/gi, "")
    .replace(/\(\s*(?:see\s+)?Evidence\s*\d+[^)]*\)/gi, "")
    .replace(/\(\s*p\.\s*\d+,\s*Evidence\s*\d+[^)]*\)/gi, "")
    .replace(/\(\s*Page\s*\d+[^)]*\)/gi, "")
    // Clean robotic meta-headers like **[Topic] – evidence-based points**
    .replace(/^\s*#*\s*\*\*[^\n*]+[–\-—]\s*(?:evidence-based points|key points|evidence points)\*\*\s*\n*/gim, "")
    .replace(/^\s*#*\s*(?:Here are (?:some )?evidence-based points|Evidence-based points|ResearchX AI analysis|According to the (?:provided )?evidence|Based on the (?:provided )?(?:paper|evidence)[^:\n]*):\s*\n*/gim, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return cleaned || "I couldn't find this information in the uploaded paper.";
}

function ChatPage() {
  const searchParams = Route.useSearch();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);

  const [selectedPaper, setSelectedPaper] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<number, boolean>>({});

  const [sessionId, setSessionId] = useState(() => `chat_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const loadSessions = async () => {
    try {
      const response = await getSessions();
      setSessions(response?.data?.sessions || []);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  // Load uploaded papers and determine active paper
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const papersResponse = await getPapers();
        const uploadedPapers: Paper[] = papersResponse?.data?.papers || [];
        setPapers(uploadedPapers);

        // Precedence: 1. URL search param -> 2. localStorage -> 3. First uploaded paper
        const queryPaper = searchParams?.paper?.trim();
        let targetPaper = "";

        if (queryPaper && uploadedPapers.some((p) => p.filename === queryPaper)) {
          targetPaper = queryPaper;
        } else {
          const storedPaper = localStorage.getItem("researchx-active-paper") || "";
          if (storedPaper && uploadedPapers.some((p) => p.filename === storedPaper)) {
            targetPaper = storedPaper;
          } else if (uploadedPapers.length > 0) {
            targetPaper = uploadedPapers[0].filename;
          }
        }

        if (targetPaper) {
          setSelectedPaper(targetPaper);
          try {
            localStorage.setItem("researchx-active-paper", targetPaper);
          } catch (e) {
            // ignore
          }
        }

        await loadSessions();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load chat data"
        );
      }
    };

    loadInitialData();
  }, [searchParams?.paper]);

  // Document switching handler
  const handlePaperChange = (newPaper: string) => {
    if (newPaper === selectedPaper) return;
    setSelectedPaper(newPaper);
    try {
      localStorage.setItem("researchx-active-paper", newPaper);
    } catch (e) {
      // ignore
    }
    // Cleanly switch context & session
    setMessages([]);
    setError("");
    setInput("");
    setExpandedSources({});
    setSessionId(`chat_${Date.now()}`);
  };

  const openSession = async (session: Session) => {
    if (loading || loadingHistory) return;

    try {
      setLoadingHistory(true);
      setError("");
      setSessionId(session.session_id);

      if (session.paper_name && papers.some((p) => p.filename === session.paper_name)) {
        setSelectedPaper(session.paper_name);
        try {
          localStorage.setItem("researchx-active-paper", session.paper_name);
        } catch (e) {
          // ignore
        }
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
            content: formatAssistantResponse(item.answer),
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

  const handleDeleteSession = async (e: React.MouseEvent, sId: string) => {
    e.stopPropagation();
    try {
      await deleteSearchHistory(sId);
      if (sId === sessionId) {
        startNewChat();
      }
      await loadSessions();
    } catch (err) {
      console.error("Failed to delete session:", err);
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

      const rawAnswer = response?.data?.answer || response?.answer || response;
      const sources = response?.data?.sources || response?.sources || [];
      const cleanAnswer = formatAssistantResponse(rawAnswer);

      const assistantMessage: Message = {
        role: "assistant",
        content: cleanAnswer,
        sources: sources,
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
    setExpandedSources({});
    setSessionId(`chat_${Date.now()}`);
  };

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const toggleSources = (index: number) => {
    setExpandedSources((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="grid h-[calc(100vh-7.5rem)] gap-4 lg:grid-cols-[280px_1fr]">
      {/* Left Sidebar: Document Selector & Chat Sessions */}
      <aside className="hidden overflow-hidden rounded-2xl glass p-4 lg:flex lg:flex-col border border-border/50">
        <Button variant="hero" className="w-full gap-2 cursor-pointer shadow-md shadow-primary/10" onClick={startNewChat}>
          <Sparkles className="h-4 w-4" />
          New chat
        </Button>

        {/* Paper Selection in Sidebar */}
        <div className="mt-5">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
              Selected Paper
            </span>
            <span className="text-[10px] text-muted-foreground">
              {papers.length} {papers.length === 1 ? "paper" : "papers"}
            </span>
          </div>

          <div className="relative mt-2">
            <select
              value={selectedPaper}
              onChange={(e) => handlePaperChange(e.target.value)}
              className="w-full truncate rounded-xl border border-border/60 bg-secondary/50 px-3 py-2.5 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary appearance-none cursor-pointer pr-8"
            >
              {papers.length === 0 && <option value="">No papers uploaded</option>}
              {papers.map((paper, idx) => (
                <option key={`${paper.filename}-${idx}`} value={paper.filename}>
                  {paper.filename}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-3 h-4 w-4 text-muted-foreground" />
          </div>

          {selectedPaper ? (
            <div className="mt-2 flex items-center gap-1.5 px-1 text-[11px] text-emerald-500 font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Ready for Chat</span>
            </div>
          ) : (
            <div className="mt-2 px-1">
              <Link to="/dashboard/upload" className="text-[11px] text-primary hover:underline flex items-center gap-1">
                <UploadCloud className="h-3 w-3" />
                Upload PDF to start
              </Link>
            </div>
          )}
        </div>

        {/* Chat History List */}
        <div className="mt-6 flex items-center justify-between text-xs uppercase tracking-wider text-muted-foreground font-semibold">
          <span>Chat History</span>
          {messages.length > 0 && (
            <button
              onClick={startNewChat}
              className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
              title="Clear current view"
            >
              Clear
            </button>
          )}
        </div>

        <ul className="mt-2 flex-1 space-y-1 overflow-auto pr-1">
          {sessions.length === 0 ? (
            <li className="px-3 py-4 text-center text-xs text-muted-foreground">
              No chat history yet
            </li>
          ) : (
            sessions.map((session) => (
              <li key={session.session_id} className="group relative">
                <button
                  onClick={() => openSession(session)}
                  disabled={loadingHistory}
                  className={`w-full truncate rounded-xl px-3 py-2 text-left text-xs transition-colors pr-7 cursor-pointer ${
                    session.session_id === sessionId
                      ? "bg-accent text-foreground font-medium border border-border/60"
                      : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                  }`}
                  title={session.title}
                >
                  {session.title || "New Chat"}
                </button>
                <button
                  onClick={(e) => handleDeleteSession(e, session.session_id)}
                  className="absolute right-2 top-2.5 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity cursor-pointer p-0.5 rounded"
                  title="Delete chat session"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </li>
            ))
          )}
        </ul>
      </aside>

      {/* Main Chat Area */}
      <div className="flex min-h-0 flex-col rounded-2xl glass border border-border/50 overflow-hidden">
        {/* Top Active Document Header Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 bg-secondary/20 px-5 py-3.5">
          <div className="flex items-center gap-3 min-w-0">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary border border-primary/20">
              <FileText className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium flex items-center gap-2">
                <span>Chat with your research paper</span>
                {selectedPaper && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-500 border border-emerald-500/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Ready for Chat
                  </span>
                )}
              </div>
              <div className="text-sm font-semibold text-foreground truncate max-w-md sm:max-w-xl" title={selectedPaper || "No paper selected"}>
                {selectedPaper || "No research paper selected"}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Quick paper switcher for mobile/tablet */}
            <div className="lg:hidden">
              <select
                value={selectedPaper}
                onChange={(e) => handlePaperChange(e.target.value)}
                className="rounded-lg border border-border/60 bg-secondary px-2 py-1 text-xs"
              >
                {papers.map((p, i) => (
                  <option key={i} value={p.filename}>
                    {p.filename}
                  </option>
                ))}
              </select>
            </div>

            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-foreground cursor-pointer"
                onClick={startNewChat}
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Clear chat
              </Button>
            )}

            <Link to="/dashboard/upload">
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5 border-border/60 cursor-pointer">
                <UploadCloud className="h-3.5 w-3.5" />
                Upload PDF
              </Button>
            </Link>
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-auto p-5 md:p-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {loadingHistory && (
              <div className="py-12 text-center text-sm text-muted-foreground">
                Loading conversation history...
              </div>
            )}

            {/* Empty State: Prompt User to Chat */}
            {!loadingHistory && messages.length === 0 && (
              <div className="py-12 text-center">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-tr from-primary/20 via-primary/10 to-transparent border border-primary/20">
                  <Bot className="h-7 w-7 text-primary" />
                </div>
                <h2 className="mt-4 font-display text-xl font-semibold">
                  {selectedPaper ? "Ask ResearchX AI" : "No Research Paper Selected"}
                </h2>
                <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
                  {selectedPaper
                    ? `Ask any question grounded strictly in ${selectedPaper}. The AI retrieves evidence directly from the paper and cites source pages.`
                    : "Upload or select a PDF to start document-based chat with source-grounded citations."}
                </p>

                {selectedPaper ? (
                  <div className="mt-8 text-left">
                    <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-3 text-center">
                      Suggested Research Questions
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {SUGGESTED_PROMPTS.map((prompt) => (
                        <button
                          key={prompt}
                          onClick={() => sendMessage(prompt)}
                          disabled={loading}
                          className="flex items-start gap-2.5 rounded-xl border border-border/60 bg-secondary/30 p-3 text-left text-xs text-muted-foreground hover:border-primary/50 hover:bg-secondary/60 hover:text-foreground transition-all cursor-pointer group"
                        >
                          <Sparkles className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                          <span>{prompt}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="mt-6">
                    <Link to="/dashboard/upload">
                      <Button variant="hero" className="gap-2 cursor-pointer">
                        <UploadCloud className="h-4 w-4" />
                        Upload Research Paper
                      </Button>
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Conversation Messages */}
            {!loadingHistory &&
              messages.map((message, index) => (
                <div key={index} className="flex gap-3">
                  <div
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-xl ${
                      message.role === "user"
                        ? "bg-secondary text-foreground"
                        : "gradient-primary-bg text-primary-foreground shadow-md shadow-primary/20"
                    }`}
                  >
                    {message.role === "user" ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4 text-primary-foreground" />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-muted-foreground flex items-center gap-2">
                      <span>{message.role === "user" ? "You" : "ResearchX AI"}</span>
                      {message.role === "assistant" && selectedPaper && (
                        <span className="text-[10px] text-muted-foreground font-normal">
                          • Grounded in {selectedPaper}
                        </span>
                      )}
                    </div>

                    {/* Message Body */}
                    {message.role === "user" ? (
                      <div className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-foreground font-normal">
                        {message.content}
                      </div>
                    ) : (
                      <div className="mt-2 text-sm leading-relaxed text-foreground font-normal">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ children }) => (
                              <p className="mb-3 last:mb-0 leading-relaxed text-foreground/90">
                                {children}
                              </p>
                            ),
                            h1: ({ children }) => (
                              <h1 className="text-base font-bold text-foreground mt-4 mb-2 first:mt-0">
                                {children}
                              </h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="text-sm font-bold text-foreground mt-3.5 mb-1.5 first:mt-0">
                                {children}
                              </h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="text-sm font-semibold text-foreground mt-3 mb-1 first:mt-0">
                                {children}
                              </h3>
                            ),
                            h4: ({ children }) => (
                              <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mt-2.5 mb-1 first:mt-0">
                                {children}
                              </h4>
                            ),
                            ul: ({ children }) => (
                              <ul className="my-2.5 ml-4 list-disc space-y-1.5 text-foreground/90">
                                {children}
                              </ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="my-2.5 ml-4 list-decimal space-y-1.5 text-foreground/90">
                                {children}
                              </ol>
                            ),
                            li: ({ children }: any) => (
                              <li className="leading-relaxed pl-1 [&>p]:inline [&>p]:mb-0 [&>p]:leading-relaxed [&>p+p]:block [&>p+p]:mt-1">
                                {children}
                              </li>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold text-foreground">
                                {children}
                              </strong>
                            ),
                            em: ({ children }) => (
                              <em className="italic text-foreground/90">
                                {children}
                              </em>
                            ),
                            blockquote: ({ children }) => (
                              <blockquote className="my-2.5 border-l-2 border-primary/60 pl-3.5 italic text-muted-foreground bg-secondary/20 py-1.5 rounded-r-lg">
                                {children}
                              </blockquote>
                            ),
                            code: ({ className, children, ...props }: any) => {
                              const isInline = !className && typeof children === "string" && !children.includes("\n");
                              return isInline ? (
                                <code className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[12px] text-foreground font-medium border border-border/40" {...props}>
                                  {children}
                                </code>
                              ) : (
                                <div className="my-3 overflow-x-auto rounded-xl border border-border/50 bg-secondary/30 p-3 font-mono text-xs text-foreground">
                                  <pre className="overflow-x-auto">
                                    <code>{children}</code>
                                  </pre>
                                </div>
                              );
                            },
                            table: ({ children }) => (
                              <div className="my-3.5 w-full overflow-x-auto rounded-xl border border-border/60 bg-secondary/15">
                                <table className="w-full text-left text-xs border-collapse">
                                  {children}
                                </table>
                              </div>
                            ),
                            thead: ({ children }) => (
                              <thead className="border-b border-border/60 bg-secondary/40 text-[11px] font-semibold text-foreground uppercase tracking-wider">
                                {children}
                              </thead>
                            ),
                            tbody: ({ children }) => (
                              <tbody className="divide-y divide-border/40 font-normal text-foreground/90">
                                {children}
                              </tbody>
                            ),
                            tr: ({ children }) => (
                              <tr className="transition-colors hover:bg-secondary/25">
                                {children}
                              </tr>
                            ),
                            th: ({ children }) => (
                              <th className="px-3.5 py-2.5 font-semibold">
                                {children}
                              </th>
                            ),
                            td: ({ children }) => (
                              <td className="px-3.5 py-2.5 align-top">
                                {children}
                              </td>
                            ),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}

                    {/* Source References & Citations */}
                    {message.role === "assistant" && message.sources && message.sources.length > 0 && (
                      <div className="mt-3.5 rounded-xl border border-border/50 bg-secondary/20 p-3">
                        {/* Top Row: Sources chip summary + expand toggle */}
                        <div
                          onClick={() => toggleSources(index)}
                          className="flex flex-wrap items-center justify-between gap-2 cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="flex items-center gap-1.5 font-semibold text-foreground/90 mr-1">
                              <BookOpen className="h-3.5 w-3.5 text-primary" />
                              Sources ({message.sources.length}):
                            </span>
                            {message.sources.slice(0, 4).map((src, sIdx) => (
                              <span
                                key={sIdx}
                                className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-background/60 px-2 py-0.5 text-[10px] font-medium text-muted-foreground shadow-2xs"
                              >
                                <FileText className="h-2.5 w-2.5 text-primary" />
                                {src.page ? `Page ${src.page}` : `Evidence ${sIdx + 1}`}
                                {src.section && src.section !== "Paper Content" ? ` — ${src.section}` : ""}
                              </span>
                            ))}
                            {message.sources.length > 4 && (
                              <span className="text-[10px] text-muted-foreground">
                                +{message.sources.length - 4} more
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1 text-[11px] text-primary/90 font-medium ml-auto">
                            <span>{expandedSources[index] ? "Hide excerpts" : "View excerpts"}</span>
                            {expandedSources[index] ? (
                              <ChevronUp className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5" />
                            )}
                          </div>
                        </div>

                        <AnimatePresence>
                          {expandedSources[index] && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              className="mt-3 space-y-2 pt-2 border-t border-border/30 overflow-hidden"
                            >
                              {message.sources.map((src, sIdx) => (
                                <div
                                  key={sIdx}
                                  className="rounded-lg border border-border/40 bg-background/50 p-2.5 text-xs text-muted-foreground"
                                >
                                  <div className="flex items-center justify-between gap-2 font-medium text-foreground mb-1">
                                    <span className="flex items-center gap-1.5 text-primary">
                                      <CheckCircle2 className="h-3 w-3" />
                                      Evidence {sIdx + 1}
                                    </span>
                                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                      {src.page && (
                                        <span className="rounded bg-secondary px-1.5 py-0.5 font-medium text-foreground">
                                          Page {src.page}
                                        </span>
                                      )}
                                      {src.section && (
                                        <span className="rounded bg-secondary px-1.5 py-0.5">
                                          {src.section}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <p className="line-clamp-3 text-[11px] leading-relaxed italic text-muted-foreground/90">
                                    "{src.snippet}"
                                  </p>
                                </div>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}

                    {/* Actions: Copy & Regenerate */}
                    {message.role === "assistant" && (
                      <div className="mt-3 flex gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground cursor-pointer"
                          onClick={() => copyToClipboard(message.content, index)}
                        >
                          {copiedIndex === index ? (
                            <>
                              <Check className="h-3 w-3 text-emerald-500" />
                              <span className="text-emerald-500">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              Copy
                            </>
                          )}
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground cursor-pointer"
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
                          <RotateCcw className="h-3 w-3" />
                          Regenerate
                        </Button>
                      </div>
                    )}

                    {/* Scholarly Accuracy & Factuality Evaluation Card */}
                    {message.role === "assistant" && (
                      <AgentEvaluationCard
                        agentName="chat"
                        agentTitle="AI Chat / RAG Agent"
                        outputText={message.content}
                        paperName={selectedPaper}
                        query={index > 0 && messages[index - 1]?.role === "user" ? messages[index - 1].content : undefined}
                      />
                    )}
                  </div>
                </div>

              ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex gap-3">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl gradient-primary-bg shadow-md shadow-primary/20">
                  <Bot className="h-4 w-4 text-primary-foreground animate-pulse" />
                </div>
                <div className="flex items-center gap-2.5 rounded-2xl border border-border/50 bg-secondary/30 px-4 py-2.5 text-xs text-muted-foreground">
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                  </span>
                  <span className="font-medium text-foreground/80">ResearchX AI</span>
                  <span className="text-muted-foreground">•</span>
                  <span>Analyzing the relevant sections of your paper...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Chat Input Bar */}
        <div className="border-t border-border/50 bg-secondary/10 p-4">
          <div className="mx-auto max-w-3xl">
            {/* Suggested Question Chips when in conversation */}
            {messages.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-1.5 overflow-x-auto pb-1">
                {SUGGESTED_PROMPTS.slice(0, 3).map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage(suggestion)}
                    disabled={loading || loadingHistory}
                    className="rounded-full border border-border/60 bg-secondary/40 px-3 py-1 text-[11px] text-muted-foreground hover:border-primary/50 hover:text-foreground disabled:opacity-50 transition-colors cursor-pointer shrink-0"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-2xl border border-border/60 bg-secondary/40 p-2 focus-within:border-primary/60 focus-within:ring-1 focus-within:ring-primary/40 transition-all">
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
                placeholder={
                  selectedPaper
                    ? "Ask anything about this research paper..."
                    : "Upload or select a PDF to start document chat..."
                }
                className="min-h-10 resize-none border-0 bg-transparent focus-visible:ring-0 text-sm"
              />

              <Button
                variant="hero"
                size="icon"
                onClick={() => sendMessage()}
                disabled={loading || loadingHistory || !input.trim() || !selectedPaper}
                className="h-9 w-9 shrink-0 cursor-pointer shadow-md shadow-primary/20"
                title={!selectedPaper ? "Please select or upload a research paper first" : "Send message"}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            {!selectedPaper && papers.length > 0 && (
              <div className="mt-1 text-center text-[11px] text-muted-foreground">
                Please select a research paper above to enable chat.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
