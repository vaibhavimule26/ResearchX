import { Bell, Command, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function DashboardTopbar({ title }: { title?: string }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-3 min-w-0">
        {title && (
          <h1 className="truncate font-display text-lg font-semibold">{title}</h1>
        )}
      </div>
      <div className="hidden flex-1 max-w-md md:block">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-3 py-2 text-sm text-muted-foreground">
          <Search className="h-4 w-4" />
          <span className="flex-1">Search papers, agents, projects…</span>
          <kbd className="flex items-center gap-0.5 rounded bg-background px-1.5 py-0.5 text-[10px]">
            <Command className="h-3 w-3" /> K
          </kbd>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <div className="grid h-9 w-9 place-items-center rounded-full gradient-primary-bg text-sm font-semibold text-primary-foreground">
          AL
        </div>
      </div>
    </header>
  );
}

export function PageHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
