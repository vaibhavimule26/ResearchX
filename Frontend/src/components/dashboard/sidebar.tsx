import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard, Sparkles, Search, Upload, MessageSquare, FileText,
  Lightbulb, Database, FlaskConical, BookOpen, FileSpreadsheet, Presentation,
  History, Bookmark, Download, User, Settings, HelpCircle, LogOut, ChevronLeft,
  Brain, Plus,
} from "lucide-react";
import { useState } from "react";
import { Logo } from "@/components/site/logo";
import { Button } from "@/components/ui/button";

const GROUPS: { label: string; items: { to: string; label: string; icon: any }[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/dashboard/workspace", label: "AI Workspace", icon: Sparkles },
    ],
  },
  {
    label: "Research",
    items: [
      { to: "/dashboard/papers", label: "Paper Search", icon: Search },
      { to: "/dashboard/upload", label: "Upload PDF", icon: Upload },
      { to: "/dashboard/chat", label: "AI Chat", icon: MessageSquare },
      { to: "/dashboard/summary", label: "Research Summary", icon: FileText },
      { to: "/dashboard/gaps", label: "Gap Analysis", icon: Lightbulb },
      { to: "/dashboard/datasets", label: "Datasets", icon: Database },
      { to: "/dashboard/experiments", label: "Experiments", icon: FlaskConical },
      { to: "/dashboard/literature", label: "Literature Survey", icon: BookOpen },
    ],
  },
  {
    label: "Outputs",
    items: [
      { to: "/dashboard/report", label: "IEEE Report", icon: FileSpreadsheet },
      { to: "/dashboard/ppt", label: "PPT Generator", icon: Presentation },
    ],
  },
  {
    label: "Library",
    items: [
      { to: "/dashboard/history", label: "History", icon: History },
      { to: "/dashboard/saved", label: "Saved Projects", icon: Bookmark },
      { to: "/dashboard/downloads", label: "Downloads", icon: Download },
    ],
  },
  {
    label: "Account",
    items: [
      { to: "/dashboard/profile", label: "Profile", icon: User },
      { to: "/dashboard/settings", label: "Settings", icon: Settings },
      { to: "/dashboard/help", label: "Help", icon: HelpCircle },
    ],
  },
];

export function DashboardSidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside
      className={`group/sb relative flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-all ${
        collapsed ? "w-[68px]" : "w-64"
      }`}
    >
      <div className="flex h-16 items-center justify-between px-3">
        {collapsed ? (
          <Link to="/" className="grid h-9 w-9 place-items-center rounded-xl gradient-primary-bg glow-primary mx-auto">
            <Brain className="h-5 w-5 text-primary-foreground" />
          </Link>
        ) : (
          <Logo />
        )}
        <button
          onClick={onToggle}
          className="hidden rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground lg:block"
          aria-label="Toggle sidebar"
        >
          <ChevronLeft className={`h-4 w-4 transition-transform ${collapsed ? "rotate-180" : ""}`} />
        </button>
      </div>

      {!collapsed && (
        <div className="px-3">
          <Link to="/dashboard/workspace">
            <Button variant="hero" className="w-full justify-start">
              <Plus className="h-4 w-4" /> New Research
            </Button>
          </Link>
        </div>
      )}

      <nav className="scrollbar-thin mt-4 flex-1 overflow-y-auto px-2 pb-4">
        {GROUPS.map((g) => (
          <div key={g.label} className="mb-4">
            {!collapsed && (
              <div className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {g.label}
              </div>
            )}
            <ul className="space-y-0.5">
              {g.items.map((item) => {
                const active = pathname === item.to;
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        active
                          ? "bg-accent text-foreground"
                          : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                      }`}
                      title={collapsed ? item.label : undefined}
                    >
                      <item.icon className={`h-4 w-4 shrink-0 ${active ? "text-[var(--electric)]" : ""}`} />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                      {active && !collapsed && (
                        <span className="ml-auto h-1.5 w-1.5 rounded-full gradient-primary-bg" />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <Link
          to="/login"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </Link>
      </div>
    </aside>
  );
}

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  return { collapsed, toggle: () => setCollapsed((v) => !v) };
}
