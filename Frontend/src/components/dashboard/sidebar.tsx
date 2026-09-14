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

const GROUPS: { label: string; items: { to: string; label: string; icon: any; badge?: string }[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/dashboard/workspace", label: "AI Workspace", icon: Sparkles },
    ],
  },
  {
    label: "Research Workspace",
    items: [
      { to: "/dashboard/upload", label: "Upload PDF", icon: Upload },
      { to: "/dashboard/chat", label: "AI Chat", icon: MessageSquare },
      { to: "/dashboard/literature", label: "Literature Survey", icon: BookOpen },
      { to: "/dashboard/summary", label: "Research Summary", icon: FileText },
      { to: "/dashboard/gaps", label: "Research Gaps", icon: Lightbulb },
      { to: "/dashboard/datasets", label: "Datasets", icon: Database },
      { to: "/dashboard/experiments", label: "Experiments", icon: FlaskConical },
    ],
  },
  {
    label: "Generate",
    items: [
      { to: "/dashboard/report", label: "IEEE Report", icon: FileSpreadsheet },
      { to: "/dashboard/ppt", label: "PPT Generator", icon: Presentation },
    ],
  },
  {
    label: "Library",
    items: [
      { to: "/dashboard/history", label: "History", icon: History },
      { to: "/dashboard/projects", label: "Saved Projects", icon: Bookmark },
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
      className={`group/sb relative flex h-screen shrink-0 flex-col border-r border-sidebar-border/60 bg-sidebar backdrop-blur-xl transition-all duration-200 z-20 ${
        collapsed ? "w-[72px]" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-3.5 border-b border-border/30">
        {collapsed ? (
          <Link to="/dashboard" className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg glow-primary mx-auto transition-transform hover:scale-105">
            <Brain className="h-5 w-5 text-primary-foreground" />
          </Link>
        ) : (
          <Logo />
        )}
        <button
          onClick={onToggle}
          className="hidden rounded-lg p-1.5 text-muted-foreground hover:bg-secondary/60 hover:text-foreground transition-colors lg:block border border-transparent hover:border-border/40"
          aria-label="Toggle sidebar"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={`h-4 w-4 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`} />
        </button>
      </div>

      {/* Quick New Research CTA */}
      {!collapsed && (
        <div className="px-3 pt-3">
          <Link to="/dashboard/workspace">
            <Button
              variant="hero"
              className="w-full justify-start gap-2 h-9 text-xs font-medium shadow-sm transition-all hover:scale-[1.01]"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New AI Research</span>
            </Button>
          </Link>
        </div>
      )}

      {/* Grouped Navigation */}
      <nav className="scrollbar-thin mt-3 flex-1 overflow-y-auto px-2.5 pb-4 space-y-4">
        {GROUPS.map((g) => (
          <div key={g.label}>
            {!collapsed && (
              <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 select-none">
                {g.label}
              </div>
            )}
            <ul className="space-y-1">
              {g.items.map((item) => {
                const active = pathname === item.to || (item.to !== "/dashboard" && pathname.startsWith(item.to));
                return (
                  <li key={item.to} className="relative">
                    <Link
                      to={item.to}
                      className={`flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all ${
                        active
                          ? "bg-primary/15 text-primary-foreground border border-primary/30 shadow-sm"
                          : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                      }`}
                      title={collapsed ? item.label : undefined}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r-full gradient-primary-bg" />
                      )}
                      <item.icon
                        className={`h-4 w-4 shrink-0 transition-colors ${
                          active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                        }`}
                      />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                      {!collapsed && item.badge && (
                        <span className="ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-primary/20 text-primary border border-primary/30 uppercase tracking-tight">
                          {item.badge}
                        </span>
                      )}
                      {active && !collapsed && !item.badge && (
                        <span className="ml-auto h-1.5 w-1.5 rounded-full gradient-primary-bg glow-primary" />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer / Logout */}
      <div className="border-t border-border/30 p-2.5 bg-secondary/10">
        <Link
          to="/login"
          className="flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
          title={collapsed ? "Logout" : undefined}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </Link>
      </div>
    </aside>
  );
}

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  return { collapsed, toggle: () => setCollapsed((v) => !v) };
}
