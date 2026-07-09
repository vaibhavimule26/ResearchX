import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Sparkles,
  FileText,
  Trash2,
  Loader2,
  MessageSquare,
  RefreshCcw,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/history")({
  head: () => ({
    meta: [{ title: "History — ResearchX" }],
  }),
  component: HistoryPage,
});

type Session = {
  session_id: string;
  title: string;
  paper_name: string | null;
  created_at: string | null;
  updated_at: string | null;
};

type HistoryMessage = {
  session_id: string;
  paper_name?: string | null;
  query: string;
  answer: string;
  created_at?: string | null;
};

const API_BASE_URL = "http://127.0.0.1:8000";

function HistoryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] =
    useState<string>("");

  const [history, setHistory] =
    useState<HistoryMessage[]>([]);

  const [loadingSessions, setLoadingSessions] =
    useState(true);

  const [loadingHistory, setLoadingHistory] =
    useState(false);

  const [deleting, setDeleting] =
    useState<string>("");

  const [error, setError] = useState("");

  const fetchSessions = async () => {
    setLoadingSessions(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/sessions`
      );

      if (!response.ok) {
        throw new Error(
          `Failed to load sessions: ${response.status}`
        );
      }

      const data = await response.json();

      const sessionList =
        data?.data?.sessions || [];

      setSessions(sessionList);

      if (sessionList.length === 0) {
        setSelectedSession("");
        setHistory([]);
        return;
      }

      const currentStillExists =
        sessionList.some(
          (session: Session) =>
            session.session_id === selectedSession
        );

      if (!currentStillExists) {
        const firstSessionId =
          sessionList[0].session_id;

        setSelectedSession(firstSessionId);

        await fetchHistory(firstSessionId);
      }
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load sessions"
      );
    } finally {
      setLoadingSessions(false);
    }
  };

  const fetchHistory = async (
    sessionId: string
  ) => {
    if (!sessionId) return;

    setLoadingHistory(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/search-history/${encodeURIComponent(
          sessionId
        )}`
      );

      if (!response.ok) {
        throw new Error(
          `Failed to load history: ${response.status}`
        );
      }

      const data = await response.json();

      setHistory(
        data?.data?.history || []
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load history"
      );

      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const openSession = async (
    sessionId: string
  ) => {
    setSelectedSession(sessionId);
    await fetchHistory(sessionId);
  };

  const deleteSession = async (
    sessionId: string
  ) => {
    const confirmed = window.confirm(
      "Delete this complete conversation history?"
    );

    if (!confirmed) return;

    setDeleting(sessionId);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/search-history/${encodeURIComponent(
          sessionId
        )}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Delete failed: ${response.status}`
        );
      }

      if (selectedSession === sessionId) {
        setSelectedSession("");
        setHistory([]);
      }

      await fetchSessions();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to delete session"
      );
    } finally {
      setDeleting("");
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div>
      <PageHeader
        title="History"
        subtitle="Your real ResearchX conversation history."
        action={
          <Button
            variant="glass"
            onClick={fetchSessions}
            disabled={loadingSessions}
          >
            <RefreshCcw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {error && (
        <div className="mb-4 rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <aside className="rounded-2xl glass p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--electric)]" />

            <h3 className="font-semibold">
              Sessions
            </h3>
          </div>

          {loadingSessions ? (
            <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading sessions...
            </div>
          ) : sessions.length === 0 ? (
            <div className="py-8 text-sm text-muted-foreground">
              No conversation history found.
            </div>
          ) : (
            <div className="mt-4 space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`rounded-xl border p-3 transition ${
                    selectedSession ===
                    session.session_id
                      ? "border-[var(--electric)] bg-[var(--electric)]/5"
                      : "border-border/40 bg-secondary/20"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() =>
                      openSession(
                        session.session_id
                      )
                    }
                    className="w-full text-left"
                  >
                    <div className="line-clamp-2 text-sm font-medium">
                      {session.title ||
                        "New Chat"}
                    </div>

                    {session.paper_name && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                        <FileText className="h-3 w-3" />

                        <span className="truncate">
                          {session.paper_name}
                        </span>
                      </div>
                    )}

                    <div className="mt-2 text-[11px] text-muted-foreground">
                      {session.updated_at ||
                        session.created_at ||
                        "No timestamp"}
                    </div>
                  </button>

                  <div className="mt-2 flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        deleteSession(
                          session.session_id
                        )
                      }
                      disabled={
                        deleting ===
                        session.session_id
                      }
                    >
                      {deleting ===
                      session.session_id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}

                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>

        <section className="rounded-2xl glass p-5">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-[var(--electric)]" />

            <h3 className="font-semibold">
              Conversation
            </h3>
          </div>

          {!selectedSession ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              Select a session to view its
              conversation.
            </div>
          ) : loadingHistory ? (
            <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading conversation...
            </div>
          ) : history.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              No messages found in this session.
            </div>
          ) : (
            <div className="mt-5 space-y-6">
              {history.map((message, index) => (
                <div
                  key={`${message.created_at}-${index}`}
                  className="space-y-3"
                >
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-md bg-[var(--electric)]/15 px-4 py-3">
                      <div className="text-xs font-medium text-[var(--electric)]">
                        You
                      </div>

                      <div className="mt-1 whitespace-pre-wrap text-sm">
                        {message.query}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-start">
                    <div className="max-w-[90%] rounded-2xl rounded-bl-md border border-border/40 bg-secondary/30 px-4 py-3">
                      <div className="text-xs font-medium">
                        ResearchX
                      </div>

                      <div className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                        {message.answer}
                      </div>

                      {message.created_at && (
                        <div className="mt-3 text-[10px] text-muted-foreground">
                          {message.created_at}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}