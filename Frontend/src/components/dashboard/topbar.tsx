import { useState, useRef, useEffect } from "react";
import {
  Bell,
  User,
  LogOut,
  CheckCircle2,
  Sparkles,
  Settings,
  Layers,
  Palette,
} from "lucide-react";
import { useNavigate, Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/lib/theme-provider";

export function DashboardTopbar({
  title,
  userName,
}: {
  title?: string;
  userName?: string;
}) {
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close menus on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        notifRef.current &&
        !notifRef.current.contains(event.target as Node)
      ) {
        setShowNotifications(false);
      }
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target as Node)
      ) {
        setShowMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initials = userName
    ? userName
        .split(" ")
        .map((name) => name[0])
        .join("")
        .toUpperCase()
    : "RX";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border/40 bg-background/85 px-4 backdrop-blur-2xl sm:px-6 transition-all">
      {/* Title & Page context */}
      <div className="flex items-center gap-3 min-w-0">
        {title ? (
          <h1 className="truncate font-display text-base sm:text-lg font-semibold tracking-tight text-foreground flex items-center gap-2">
            <span>{title}</span>
          </h1>
        ) : (
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="text-foreground font-semibold">Research Command Center</span>
          </div>
        )}
      </div>

      {/* Right Controls: Notifications & User Avatar */}
      <div className="flex items-center gap-2.5 ml-auto">
        {/* Notifications Popover */}
        <div className="relative" ref={notifRef}>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Notifications"
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative h-9 w-9 rounded-xl text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-primary ring-2 ring-background animate-pulse" />
          </Button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-border/80 bg-background/95 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150 overflow-hidden">
              <div className="flex items-center justify-between border-b border-border/40 px-4 py-3 bg-secondary/20">
                <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Research Notifications
                </span>
                <span className="text-[10px] text-primary font-mono font-semibold">
                  3 Updates
                </span>
              </div>

              <div className="divide-y divide-border/30 max-h-80 overflow-y-auto">
                <div className="flex items-start gap-3 px-4 py-3 hover:bg-secondary/40 transition-colors">
                  <div className="rounded-lg bg-emerald-500/10 p-1.5 text-emerald-400 shrink-0 mt-0.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground">
                      Research Paper Ingested
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Vector embeddings and chunking completed.
                    </p>
                    <span className="text-[10px] text-muted-foreground/60 font-mono">
                      Just now
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 px-4 py-3 hover:bg-secondary/40 transition-colors">
                  <div className="rounded-lg bg-blue-500/10 p-1.5 text-blue-400 shrink-0 mt-0.5">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground">
                      Literature Survey Ready
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Synthesis agent generated cross-paper comparison.
                    </p>
                    <span className="text-[10px] text-muted-foreground/60 font-mono">
                      10 mins ago
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 px-4 py-3 hover:bg-secondary/40 transition-colors">
                  <div className="rounded-lg bg-purple-500/10 p-1.5 text-purple-400 shrink-0 mt-0.5">
                    <Layers className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground">
                      IEEE Report Generated
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Ready for LaTeX or PDF export.
                    </p>
                    <span className="text-[10px] text-muted-foreground/60 font-mono">
                      Today
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Theme Toggle (Light / Dark / System) */}
        <ThemeToggle />

        {/* User Profile Avatar & Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="group relative flex h-9 w-9 items-center justify-center rounded-xl gradient-primary-bg text-xs font-bold text-primary-foreground shadow-sm transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary/40"
            title="User menu"
          >
            {initials}
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-background" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-border/80 bg-background/95 p-1.5 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-2 border-b border-border/40">
                <p className="text-xs font-semibold text-foreground truncate">
                  {userName || "Researcher"}
                </p>
                <p className="text-[10px] text-muted-foreground font-mono">
                  researcher@researchx.ai
                </p>
              </div>

              <div className="py-1 space-y-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    navigate({ to: "/dashboard/profile" });
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary/70 hover:text-foreground transition-colors"
                >
                  <User className="h-3.5 w-3.5" />
                  <span>Researcher Profile</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    navigate({ to: "/dashboard/settings" });
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary/70 hover:text-foreground transition-colors"
                >
                  <Palette className="h-3.5 w-3.5" />
                  <span>Theme &amp; Appearance</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    navigate({ to: "/dashboard/settings" });
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary/70 hover:text-foreground transition-colors"
                >
                  <Settings className="h-3.5 w-3.5" />
                  <span>Settings &amp; Keys</span>
                </button>
              </div>

              <div className="border-t border-border/40 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    localStorage.removeItem("token");
                    window.location.href = "/login";
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
          {title}
        </h1>

        {subtitle && (
          <p className="mt-1 text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-3xl">
            {subtitle}
          </p>
        )}
      </div>

      {action && <div className="shrink-0 flex items-center gap-2">{action}</div>}
    </div>
  );
}