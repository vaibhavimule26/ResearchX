import { useState } from "react";
import { Bell, Command, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { searchDashboard } from "@/lib/api";

export function DashboardTopbar({
  title,
  userName,
}: {
  title?: string;
  userName?: string;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);

  const performSearch = async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    try {
      const response = await searchDashboard(query);
      setResults(response.results);
    } catch (error) {
      console.error("Search Error:", error);
    }
  };

  const handleSearch = async (
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter") {
      await performSearch();
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-3 min-w-0">
        {title && (
          <h1 className="truncate font-display text-lg font-semibold">
            {title}
          </h1>
        )}
      </div>

      <div className="relative flex-1 max-w-md">
        <div className="flex items-center gap-2">

  <div className="flex flex-1 items-center rounded-xl border border-border bg-secondary/50 px-3">

    <Search className="h-4 w-4 text-muted-foreground" />

    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      onKeyDown={handleSearch}
      placeholder="Search papers..."
      className="flex-1 bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
    />

  </div>

  <Button
    onClick={performSearch}
    variant="default"
  >
    Search
  </Button>

</div>

        {results.length > 0 && (
          <div className="absolute left-0 top-full mt-2 w-full rounded-xl border border-border bg-background shadow-xl z-50">

            {results.map((paper) => (
  <div
    key={paper.title + paper.uploaded_at}
    onClick={() => {
      window.location.href =
        `/dashboard/papers?paper=${encodeURIComponent(paper.title)}`;
    }}
    className="cursor-pointer border-b border-border px-4 py-3 hover:bg-accent"
  >
                <div className="font-medium">
                  {paper.title}
                </div>

                <div className="text-xs text-muted-foreground">
                  {paper.uploaded_at}
                </div>
              </div>
            ))}

          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>

        <div className="grid h-9 w-9 place-items-center rounded-full gradient-primary-bg text-sm font-semibold text-primary-foreground">
  {userName
    ? userName
        .split(" ")
        .map((name) => name[0])
        .join("")
        .toUpperCase()
    : "U"}
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
    <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight">
          {title}
        </h1>

        {subtitle && (
          <p className="mt-1 text-sm text-muted-foreground">
            {subtitle}
          </p>
        )}
      </div>

      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}