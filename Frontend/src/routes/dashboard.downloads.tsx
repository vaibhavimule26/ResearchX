import { createFileRoute } from "@tanstack/react-router";
import { Download, FileText, FileSpreadsheet, Presentation } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/downloads")({
  head: () => ({ meta: [{ title: "Downloads — ResearchX" }] }),
  component: DownloadsPage,
});

const FILES = [
  { name: "M-RAG-IEEE-v2.pdf", kind: "report", size: "1.4 MB", date: "Today" },
  { name: "M-RAG-slides.pptx", kind: "ppt", size: "3.8 MB", date: "Today" },
  { name: "literature-survey-rag.csv", kind: "report", size: "42 KB", date: "Yesterday" },
  { name: "attention-is-all-you-need.pdf", kind: "paper", size: "2.4 MB", date: "Yesterday" },
  { name: "rag-survey-2024.pdf", kind: "paper", size: "5.1 MB", date: "2d ago" },
  { name: "thesis-defense.pptx", kind: "ppt", size: "6.2 MB", date: "1w ago" },
];

const ICONS = { report: FileSpreadsheet, ppt: Presentation, paper: FileText };

function DownloadsPage() {
  return (
    <div>
      <PageHeader title="Downloads" subtitle="Everything you've exported." />
      <div className="rounded-2xl glass overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
              <th className="px-4 py-3 text-left font-medium">Size</th>
              <th className="px-4 py-3 text-left font-medium">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {FILES.map((f) => {
              const Icon = ICONS[f.kind as keyof typeof ICONS];
              return (
                <tr key={f.name} className="border-t border-border/40 hover:bg-accent/30">
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2 font-medium"><Icon className="h-4 w-4 text-[var(--electric)]" />{f.name}</span>
                  </td>
                  <td className="px-4 py-3 capitalize text-muted-foreground">{f.kind}</td>
                  <td className="px-4 py-3 text-muted-foreground">{f.size}</td>
                  <td className="px-4 py-3 text-muted-foreground">{f.date}</td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="sm"><Download className="h-3.5 w-3.5" /></Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
