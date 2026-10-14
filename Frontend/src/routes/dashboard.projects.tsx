import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import {
  FolderOpen,
  Star,
  MoreVertical,
  FileText,
  FileSpreadsheet,
  Presentation,
  Search,
  ArrowUpDown,
  Trash2,
  Edit3,
  Copy,
  Download,
  ExternalLink,
  Sparkles,
  Plus,
  RefreshCw,
  Loader2,
  ArrowRight,
  Clock,
  Layers,
  Activity,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  getProjects,
  toggleProjectFavorite,
  renameProject,
  duplicateProject,
  deleteProject,
  type ProjectItem,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/projects")({
  head: () => ({ meta: [{ title: "Saved Projects — ResearchX" }] }),
  component: ProjectsPage,
});

function ProjectsPage() {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<
    "updated" | "created" | "name_asc" | "name_desc" | "papers" | "favorites"
  >("updated");

  // Rename Dialog state
  const [renamingProject, setRenamingProject] = useState<ProjectItem | null>(null);
  const [renameInput, setRenameInput] = useState("");
  const [savingRename, setSavingRename] = useState(false);

  // Load Projects from backend
  const loadProjects = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await getProjects();
      if (res && res.success && Array.isArray(res.data)) {
        setProjects(res.data);
      } else {
        setProjects([]);
      }
    } catch (err: any) {
      console.error("Failed to load projects:", err);
      setError(err?.message || "Failed to load saved projects");
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Filter and Sort
  const filteredAndSortedProjects = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const result = projects.filter((p) => {
      if (!q) return true;
      const nameMatch = p.name?.toLowerCase().includes(q);
      const topicMatch = p.topic?.toLowerCase().includes(q);
      const agentMatch = p.agents_used?.some((a) => a.toLowerCase().includes(q));
      const activityMatch = p.last_activity?.toLowerCase().includes(q);
      return nameMatch || topicMatch || agentMatch || activityMatch;
    });

    return result.sort((a, b) => {
      if (sortBy === "favorites") {
        if (a.starred !== b.starred) {
          return a.starred ? -1 : 1;
        }
        return (
          new Date(b.updated_at || b.created_at || 0).getTime() -
          new Date(a.updated_at || a.created_at || 0).getTime()
        );
      }
      if (sortBy === "created") {
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
      if (sortBy === "name_asc") {
        return (a.name || "").localeCompare(b.name || "");
      }
      if (sortBy === "name_desc") {
        return (b.name || "").localeCompare(a.name || "");
      }
      if (sortBy === "papers") {
        return (b.papers_count || 0) - (a.papers_count || 0);
      }
      // Default: "updated"
      return (
        new Date(b.updated_at || b.created_at || 0).getTime() -
        new Date(a.updated_at || a.created_at || 0).getTime()
      );
    });
  }, [projects, searchQuery, sortBy]);

  // Open Project & Restore Workspace
  const handleOpenProject = (p: ProjectItem) => {
    try {
      localStorage.setItem("researchx-open-session", p.id);
    } catch (e) {
      console.warn("Could not save active session to localStorage", e);
    }
    navigate({
      to: "/dashboard/workspace",
      search: { session_id: p.id } as any,
    });
  };

  // Toggle Favorite
  const handleToggleFavorite = async (e: React.MouseEvent, p: ProjectItem) => {
    e.stopPropagation();
    const prevStarred = p.starred;
    setProjects((prev) =>
      prev.map((item) => (item.id === p.id ? { ...item, starred: !prevStarred } : item))
    );

    try {
      await toggleProjectFavorite(p.id);
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
      // Revert on error
      setProjects((prev) =>
        prev.map((item) => (item.id === p.id ? { ...item, starred: prevStarred } : item))
      );
    }
  };

  // Rename Project
  const handleStartRename = (p: ProjectItem) => {
    setRenamingProject(p);
    setRenameInput(p.name || "");
  };

  const handleSaveRename = async () => {
    if (!renamingProject || !renameInput.trim()) return;
    try {
      setSavingRename(true);
      const newName = renameInput.trim();
      await renameProject(renamingProject.id, newName);
      setProjects((prev) =>
        prev.map((p) => (p.id === renamingProject.id ? { ...p, name: newName } : p))
      );
      setRenamingProject(null);
    } catch (err) {
      console.error("Failed to rename project:", err);
      alert("Failed to rename project");
    } finally {
      setSavingRename(false);
    }
  };

  // Duplicate Project
  const handleDuplicate = async (p: ProjectItem) => {
    try {
      setLoading(true);
      await duplicateProject(p.id);
      await loadProjects();
    } catch (err) {
      console.error("Failed to duplicate project:", err);
      alert("Failed to duplicate project");
      setLoading(false);
    }
  };

  // Export Project (JSON download)
  const handleExport = (p: ProjectItem) => {
    try {
      const exportData = {
        project_name: p.name,
        research_topic: p.topic,
        session_id: p.id,
        created_at: p.created_at,
        updated_at: p.updated_at,
        last_activity: p.last_activity,
        metrics: {
          papers_count: p.papers_count,
          reports_count: p.reports_count,
          ppts_count: p.ppts_count,
        },
        agents_used: p.agents_used,
        status: p.status,
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const safeName = (p.name || "project").replace(/[^a-zA-Z0-9_\-]/g, "_");
      a.href = url;
      a.download = `${safeName}_export.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
      alert("Failed to export project data");
    }
  };

  // Delete Project
  const handleDelete = async (p: ProjectItem) => {
    if (!confirm(`Are you sure you want to delete "${p.name}"? This action cannot be undone.`)) {
      return;
    }
    // Optimistic deletion
    setProjects((prev) => prev.filter((item) => item.id !== p.id));
    try {
      await deleteProject(p.id);
    } catch (err) {
      console.error("Failed to delete project:", err);
      alert("Failed to delete project");
      await loadProjects();
    }
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Saved Projects"
        subtitle="Your real research workspaces, synthesized findings, and cross-agent literature collections."
        action={
          <Button
            variant="hero"
            size="sm"
            onClick={() => navigate({ to: "/dashboard/workspace" })}
            className="h-9 px-4 text-xs font-semibold gap-1.5 shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Research Project</span>
          </Button>
        }
      />

      {/* Search & Sort Controls Bar */}
      <div className="rounded-2xl border border-border/60 bg-card/80 p-4 backdrop-blur-sm shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/70" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by project name, research topic, or agent..."
              className="w-full rounded-xl border border-border/70 bg-background pl-10 pr-3.5 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Sort Selector */}
            <div className="flex items-center gap-1.5 rounded-xl border border-border/70 bg-background px-3 py-1.5 text-xs text-foreground">
              <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-transparent text-xs text-foreground focus:outline-none cursor-pointer"
              >
                <option value="updated">Recently Updated</option>
                <option value="created">Recently Created</option>
                <option value="name_asc">Name (A–Z)</option>
                <option value="name_desc">Name (Z–A)</option>
                <option value="papers">Most Papers</option>
                <option value="favorites">Favorites First</option>
              </select>
            </div>

            {/* Refresh Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={loadProjects}
              disabled={loading}
              className="h-8 w-8 p-0 border-border/70"
              title="Refresh projects"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-primary" : "text-muted-foreground"}`} />
            </Button>
          </div>
        </div>

        {/* Counter Info */}
        <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/30">
          <span>
            Showing <strong className="text-foreground">{filteredAndSortedProjects.length}</strong> of{" "}
            <strong className="text-foreground">{projects.length}</strong> saved research projects
          </span>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="text-primary hover:underline cursor-pointer"
            >
              Clear search filter
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading && projects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-3 rounded-2xl border border-border/40 bg-secondary/10">
          <Loader2 className="h-8 w-8 text-primary animate-spin" />
          <p className="text-sm font-medium text-foreground">Loading your saved research projects...</p>
          <p className="text-xs text-muted-foreground">Connecting to ResearchX database</p>
        </div>
      )}

      {/* Empty State: Zero Projects */}
      {!loading && projects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center space-y-4 rounded-2xl border border-dashed border-border/60 bg-secondary/10 p-8">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/10 border border-primary/25 text-primary">
            <FolderOpen className="h-7 w-7" />
          </div>
          <div className="space-y-1 max-w-md">
            <h3 className="text-base font-semibold text-foreground">No saved projects yet</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              You haven't saved any research projects yet. Search for academic papers or run an AI research workspace to begin.
            </p>
          </div>
          <Button
            variant="hero"
            size="sm"
            onClick={() => navigate({ to: "/dashboard/workspace" })}
            className="h-9 px-5 text-xs font-semibold gap-1.5 shadow-sm"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Start New Research Project</span>
          </Button>
        </div>
      )}

      {/* Empty State: Filter Returned No Match */}
      {!loading && projects.length > 0 && filteredAndSortedProjects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-14 text-center space-y-3 rounded-2xl border border-border/40 bg-secondary/10 p-6">
          <Search className="h-8 w-8 text-muted-foreground/60" />
          <h4 className="text-sm font-semibold text-foreground">No projects matched your search</h4>
          <p className="text-xs text-muted-foreground">
            No projects found matching "{searchQuery}". Try a different keyword or reset filters.
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSearchQuery("")}
            className="h-8 text-xs"
          >
            Clear Search
          </Button>
        </div>
      )}

      {/* Projects Grid: Two-Column Layout */}
      {!loading && filteredAndSortedProjects.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredAndSortedProjects.map((p) => (
            <div
              key={p.id}
              className="rounded-2xl border border-border/60 bg-card/85 p-5 backdrop-blur-xl shadow-md space-y-4 hover:border-primary/50 transition-all group flex flex-col justify-between"
            >
              <div className="space-y-3">
                {/* Header Row: Folder Icon, Project Name & Topic, Favorite Star & 3-dot Menu */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
                      <FolderOpen className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3
                        className="font-semibold text-sm text-foreground truncate cursor-pointer hover:text-primary transition-colors"
                        onClick={() => handleOpenProject(p)}
                        title={p.name}
                      >
                        {p.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="text-[11px] text-muted-foreground truncate" title={p.topic}>
                          Topic: <span className="text-foreground/90 font-medium">"{p.topic}"</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions: Favorite Star + 3-Dot Menu */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={(e) => handleToggleFavorite(e, p)}
                      className="p-1.5 rounded-lg hover:bg-secondary/60 transition-colors cursor-pointer"
                      title={p.starred ? "Remove from favorites" : "Add to favorites"}
                    >
                      <Star
                        className={`h-4 w-4 transition-all ${
                          p.starred
                            ? "fill-amber-400 text-amber-400 drop-shadow-sm scale-110"
                            : "text-muted-foreground/60 hover:text-amber-400"
                        }`}
                      />
                    </button>

                    {/* 3-Dot Dropdown Menu */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button
                          type="button"
                          className="p-1.5 rounded-lg hover:bg-secondary/60 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                          title="More options"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-44 text-xs">
                        <DropdownMenuItem onClick={() => handleOpenProject(p)} className="cursor-pointer gap-2">
                          <ExternalLink className="h-3.5 w-3.5 text-primary" />
                          <span>Open Project</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleStartRename(p)} className="cursor-pointer gap-2">
                          <Edit3 className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>Rename</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDuplicate(p)} className="cursor-pointer gap-2">
                          <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>Duplicate</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleExport(p)} className="cursor-pointer gap-2">
                          <Download className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>Export Data</span>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(p)}
                          className="cursor-pointer gap-2 text-destructive focus:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          <span>Delete</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>

                {/* Sub-Header: Last updated time and last activity */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground pt-1 border-t border-border/30">
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3 text-muted-foreground/70" />
                    <span>Updated {p.last_updated}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] font-medium text-foreground/80 truncate max-w-[200px]" title={p.last_activity}>
                    <Activity className="h-3 w-3 text-emerald-400 shrink-0" />
                    <span className="truncate">{p.last_activity}</span>
                  </div>
                </div>

                {/* Metric Boxes: Papers, Reports, PPT Count */}
                <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                  <div className="rounded-xl border border-border/40 bg-secondary/30 p-2.5 text-center">
                    <FileText className="mx-auto h-3.5 w-3.5 text-blue-400" />
                    <div className="mt-1 font-semibold text-foreground font-mono">{p.papers_count}</div>
                    <div className="text-[10px] text-muted-foreground">Papers</div>
                  </div>
                  <div className="rounded-xl border border-border/40 bg-secondary/30 p-2.5 text-center">
                    <FileSpreadsheet className="mx-auto h-3.5 w-3.5 text-purple-400" />
                    <div className="mt-1 font-semibold text-foreground font-mono">{p.reports_count}</div>
                    <div className="text-[10px] text-muted-foreground">Reports</div>
                  </div>
                  <div className="rounded-xl border border-border/40 bg-secondary/30 p-2.5 text-center">
                    <Presentation className="mx-auto h-3.5 w-3.5 text-amber-400" />
                    <div className="mt-1 font-semibold text-foreground font-mono">{p.ppts_count}</div>
                    <div className="text-[10px] text-muted-foreground">PPT Decks</div>
                  </div>
                </div>

                {/* Agents Used Chips */}
                {p.agents_used && p.agents_used.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] uppercase font-mono text-muted-foreground/70 block">
                      Agents Used ({p.agents_used.length})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {p.agents_used.map((ag) => (
                        <span
                          key={ag}
                          className="inline-flex items-center px-2 py-0.5 rounded-md bg-secondary/60 text-[10px] font-medium text-foreground/85 border border-border/40 capitalize"
                        >
                          {ag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Open Project Button */}
              <div className="pt-3 border-t border-border/30">
                <Button
                  variant="hero"
                  size="sm"
                  onClick={() => handleOpenProject(p)}
                  className="w-full justify-between h-9 text-xs font-semibold shadow-xs transition-all hover:scale-[1.01]"
                >
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Open Project</span>
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 opacity-80" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Rename Project Dialog Modal */}
      <Dialog open={Boolean(renamingProject)} onOpenChange={(open) => !open && setRenamingProject(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-sm font-semibold">Rename Research Project</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Enter a new descriptive name for this research workspace project.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input
              value={renameInput}
              onChange={(e) => setRenameInput(e.target.value)}
              placeholder="Project Name..."
              className="text-xs"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSaveRename();
                }
              }}
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRenamingProject(null)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              variant="hero"
              size="sm"
              onClick={handleSaveRename}
              disabled={savingRename || !renameInput.trim()}
              className="text-xs font-semibold"
            >
              {savingRename ? "Saving..." : "Save Name"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ProjectsPage;
