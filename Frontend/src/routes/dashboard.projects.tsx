import { createFileRoute } from "@tanstack/react-router";
import { FolderOpen, Star, Download, FileText, FileSpreadsheet, Presentation } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/projects")({
  head: () => ({ meta: [{ title: "Saved Projects — ResearchX" }] }),
  component: ProjectsPage,
});

const PROJECTS = [
  { name: "Multimodal RAG for Science", papers: 24, reports: 2, ppts: 1, updated: "2h ago", starred: true },
  { name: "MoE Architectures Survey", papers: 17, reports: 1, ppts: 1, updated: "Yesterday", starred: false },
  { name: "Agent Eval Benchmarks", papers: 12, reports: 0, ppts: 0, updated: "3d ago", starred: true },
  { name: "Biomedical NER", papers: 9, reports: 1, ppts: 0, updated: "1w ago", starred: false },
];

function ProjectsPage() {
  return (
    <div>
      <PageHeader title="Saved Projects" subtitle="Your research workspaces." />
      <div className="grid gap-4 md:grid-cols-2">
        {PROJECTS.map((p) => (
          <div key={p.name} className="rounded-2xl glass p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg">
                  <FolderOpen className="h-5 w-5 text-primary-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold">{p.name}</h3>
                  <p className="text-xs text-muted-foreground">Updated {p.updated}</p>
                </div>
              </div>
              <Star className={`h-4 w-4 ${p.starred ? "fill-[var(--warning)] text-[var(--warning)]" : "text-muted-foreground"}`} />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
              <div className="rounded-lg border border-border/40 bg-secondary/30 p-2 text-center">
                <FileText className="mx-auto h-3.5 w-3.5 text-[var(--electric)]" />
                <div className="mt-1 font-medium">{p.papers}</div>
                <div className="text-muted-foreground">papers</div>
              </div>
              <div className="rounded-lg border border-border/40 bg-secondary/30 p-2 text-center">
                <FileSpreadsheet className="mx-auto h-3.5 w-3.5 text-[var(--purple-glow)]" />
                <div className="mt-1 font-medium">{p.reports}</div>
                <div className="text-muted-foreground">reports</div>
              </div>
              <div className="rounded-lg border border-border/40 bg-secondary/30 p-2 text-center">
                <Presentation className="mx-auto h-3.5 w-3.5 text-[var(--warning)]" />
                <div className="mt-1 font-medium">{p.ppts}</div>
                <div className="text-muted-foreground">decks</div>
              </div>
            </div>
            <Button variant="glass" size="sm" className="mt-4 w-full">Open project</Button>
          </div>
        ))}
      </div>
    </div>
  );
}
