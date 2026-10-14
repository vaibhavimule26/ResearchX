import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import {
  Sparkles,
  FileText,
  Trash2,
  Loader2,
  RefreshCcw,
  Search,
  Upload,
  Database,
  FlaskConical,
  BookOpen,
  FileCheck,
  Presentation,
  ShieldCheck,
  LogIn,
  CheckCircle2,
  AlertCircle,
  Clock,
  Calendar,
  X,
  Layers,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getUserHistory,
  deleteUserActivity,
  clearUserHistory,
  UserActivityItem,
  UserHistoryGroup,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/history")({
  head: () => ({
    meta: [{ title: "History — ResearchX" }],
  }),
  component: HistoryPage,
});

const FILTER_TABS = [
  { id: "all", label: "All Activities" },
  { id: "summary", label: "Summaries" },
  { id: "gaps", label: "Gap Analysis" },
  { id: "datasets", label: "Datasets" },
  { id: "experiments", label: "Experiments" },
  { id: "literature", label: "Literature" },
  { id: "report", label: "IEEE Reports" },
  { id: "presentation", label: "Presentations" },
  { id: "plagiarism", label: "Plagiarism" },
  { id: "upload", label: "Uploads" },
  { id: "search", label: "Searches" },
];

function getActivityIcon(type: string) {
  const t = (type || "").toLowerCase();
  if (t.includes("summary")) return <FileText className="h-4 w-4 text-blue-400" />;
  if (t.includes("gap")) return <AlertCircle className="h-4 w-4 text-amber-400" />;
  if (t.includes("dataset")) return <Database className="h-4 w-4 text-emerald-400" />;
  if (t.includes("experiment")) return <FlaskConical className="h-4 w-4 text-purple-400" />;
  if (t.includes("literature")) return <BookOpen className="h-4 w-4 text-cyan-400" />;
  if (t.includes("report")) return <FileCheck className="h-4 w-4 text-rose-400" />;
  if (t.includes("presentation") || t.includes("ppt")) return <Presentation className="h-4 w-4 text-yellow-400" />;
  if (t.includes("plagiarism")) return <ShieldCheck className="h-4 w-4 text-emerald-400" />;
  if (t.includes("upload")) return <Upload className="h-4 w-4 text-sky-400" />;
  if (t.includes("search")) return <Search className="h-4 w-4 text-indigo-400" />;
  if (t.includes("auth") || t.includes("login")) return <LogIn className="h-4 w-4 text-emerald-400" />;
  if (t.includes("workspace")) return <Sparkles className="h-4 w-4 text-violet-400" />;
  return <Layers className="h-4 w-4 text-muted-foreground" />;
}

function getStatusBadge(status: string) {
  const s = (status || "").toLowerCase();
  if (s === "completed") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400">
        <CheckCircle2 className="h-3 w-3" />
        Completed
      </span>
    );
  }
  if (s === "failed") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[11px] font-medium text-rose-400">
        <X className="h-3 w-3" />
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-400">
      <Loader2 className="h-3 w-3 animate-spin" />
      {status || "In Progress"}
    </span>
  );
}

function HistoryPage() {
  const navigate = useNavigate();
  const [groupedHistory, setGroupedHistory] = useState<UserHistoryGroup[]>([]);
  const [totalActivities, setTotalActivities] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [deletingId, setDeletingId] = useState("");
  const [clearing, setClearing] = useState(false);

  const fetchHistory = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate({ to: "/login" });
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await getUserHistory(200, selectedFilter);
      if (res?.data) {
        setGroupedHistory(res.data.grouped || []);
        setTotalActivities(res.data.total || 0);
      } else {
        setGroupedHistory([]);
        setTotalActivities(0);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load activity history");
      setGroupedHistory([]);
      setTotalActivities(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [selectedFilter]);

  const handleDeleteItem = async (activityId: string) => {
    if (!window.confirm("Remove this activity from your history?")) return;
    setDeletingId(activityId);
    try {
      await deleteUserActivity(activityId);
      // Remove locally from state
      setGroupedHistory((prev) =>
        prev
          .map((group) => ({
            ...group,
            items: group.items.filter((item) => item.id !== activityId),
          }))
          .filter((group) => group.items.length > 0)
      );
      setTotalActivities((prev) => Math.max(0, prev - 1));
    } catch (err: any) {
      alert(err?.message || "Failed to delete activity item");
    } finally {
      setDeletingId("");
    }
  };

  const handleClearAll = async () => {
    if (
      !window.confirm(
        "Are you sure you want to clear your entire activity history? This action cannot be undone."
      )
    ) {
      return;
    }

    setClearing(true);
    try {
      await clearUserHistory();
      setGroupedHistory([]);
      setTotalActivities(0);
    } catch (err: any) {
      alert(err?.message || "Failed to clear history");
    } finally {
      setClearing(false);
    }
  };

  // Client-side search filtering
  const filteredGroups = useMemo(() => {
    if (!searchQuery.trim()) return groupedHistory;
    const q = searchQuery.toLowerCase().trim();

    return groupedHistory
      .map((group) => ({
        ...group,
        items: group.items.filter(
          (item) =>
            item.action_name?.toLowerCase().includes(q) ||
            item.topic?.toLowerCase().includes(q) ||
            item.paper_name?.toLowerCase().includes(q) ||
            item.agent?.toLowerCase().includes(q) ||
            item.details?.toLowerCase().includes(q)
        ),
      }))
      .filter((group) => group.items.length > 0);
  }, [groupedHistory, searchQuery]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="History"
        subtitle="Your personalized ResearchX activity history."
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="glass"
              size="sm"
              onClick={fetchHistory}
              disabled={loading}
              className="gap-2 text-xs"
            >
              <RefreshCcw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            {totalActivities > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearAll}
                disabled={clearing || loading}
                className="gap-2 border-destructive/30 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
              >
                {clearing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
                Clear History
              </Button>
            )}
          </div>
        }
      />

      {error && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-2xl glass p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by topic, paper, or agent..."
            className="pl-9 h-9 text-xs"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="text-xs text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{totalActivities}</span> activities
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {FILTER_TABS.map((tab) => {
          const isActive = selectedFilter === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-secondary/40 text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Activity Timeline View */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--electric)]" />
          <p className="mt-3 text-sm text-muted-foreground">Loading your activity history...</p>
        </div>
      ) : filteredGroups.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl glass p-12 text-center">
          <div className="grid h-16 w-16 place-items-center rounded-2xl bg-secondary/40 text-muted-foreground">
            {searchQuery ? <Search className="h-8 w-8" /> : <Clock className="h-8 w-8" />}
          </div>
          <h3 className="mt-4 font-display text-lg font-semibold">
            {searchQuery ? "No matching activities" : "No activity yet"}
          </h3>
          <p className="mt-1 max-w-sm text-xs text-muted-foreground">
            {searchQuery
              ? `No activities match "${searchQuery}". Try clearing your search query or switching filters.`
              : "Your ResearchX activities will appear here. Start by searching for research papers, uploading a PDF, or generating an AI summary."}
          </p>
          {searchQuery && (
            <Button
              variant="glass"
              size="sm"
              onClick={() => setSearchQuery("")}
              className="mt-4 text-xs"
            >
              Clear Search
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {filteredGroups.map((group) => (
            <div key={group.date} className="space-y-3">
              {/* Date Group Header */}
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-[var(--electric)]" />
                <h3 className="font-display text-sm font-semibold tracking-wide text-foreground">
                  {group.date}
                </h3>
                <span className="rounded-full bg-secondary/60 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                  {group.items.length} {group.items.length === 1 ? "activity" : "activities"}
                </span>
                <div className="flex-1 border-t border-border/40 ml-2" />
              </div>

              {/* Activity Cards List */}
              <div className="grid gap-2.5">
                {group.items.map((item) => {
                  const isDeleting = deletingId === item.id;
                  return (
                    <div
                      key={item.id}
                      className="group relative flex flex-col justify-between rounded-xl border border-border/40 bg-card/40 p-4 transition-all hover:border-border hover:bg-card/70 sm:flex-row sm:items-center"
                    >
                      <div className="flex items-start gap-3.5">
                        {/* Activity Icon */}
                        <div className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-border/50 bg-secondary/30">
                          {getActivityIcon(item.activity_type)}
                        </div>

                        {/* Activity Details */}
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-sm text-foreground">
                              {item.action_name}
                            </span>

                            {item.agent && (
                              <span className="rounded-md border border-border/40 bg-secondary/40 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                                {item.agent}
                              </span>
                            )}

                            {getStatusBadge(item.status)}
                          </div>

                          {/* Topic / Paper Name in quotes as requested */}
                          {(item.topic || item.paper_name) && (
                            <div className="text-xs text-muted-foreground">
                              {item.topic && (
                                <span className="italic font-medium text-foreground/90">
                                  "{item.topic}"
                                </span>
                              )}
                              {item.topic && item.paper_name && (
                                <span className="mx-1 text-muted-foreground/60">·</span>
                              )}
                              {item.paper_name && (
                                <span className="font-mono text-[11px] text-muted-foreground">
                                  "{item.paper_name}"
                                </span>
                              )}
                            </div>
                          )}

                          {/* Extra details note (e.g. "10 papers found") */}
                          {item.details && (
                            <div className="text-[11px] text-muted-foreground/80">
                              {item.details}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right side: Time and Delete action */}
                      <div className="mt-3 flex items-center justify-between gap-3 border-t border-border/20 pt-2 sm:mt-0 sm:border-t-0 sm:pt-0">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3 text-muted-foreground/60" />
                          <span>{item.formatted_time}</span>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleDeleteItem(item.id)}
                          disabled={isDeleting}
                          title="Delete activity"
                          className="opacity-60 transition hover:opacity-100 hover:text-destructive sm:opacity-0 sm:group-hover:opacity-100 p-1"
                        >
                          {isDeleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
