import { createFileRoute, Link } from "@tanstack/react-router";
import { LifeBuoy, BookOpen, MessageSquare, Mail, ArrowUpRight } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/dashboard/help")({
  head: () => ({ meta: [{ title: "Help — ResearchX" }] }),
  component: HelpPage,
});

const TOPICS = [
  { icon: BookOpen, title: "Getting Started", desc: "How to run your first research session.", to: "/docs" },
  { icon: LifeBuoy, title: "Troubleshooting", desc: "Common issues with agents and uploads.", to: "/docs" },
  { icon: MessageSquare, title: "Community", desc: "Discuss with other researchers.", to: "/about" },
  { icon: Mail, title: "Contact Support", desc: "Reach our team within 24h.", to: "/about" },
];

const FAQ = [
  { q: "How accurate are agent outputs?", a: "All outputs are grounded in retrieved sources with citations. We recommend reviewing before publication." },
  { q: "Can I bring my own API keys?", a: "Yes — set them in Settings → API Keys. We never log or share your keys." },
  { q: "What file formats are supported?", a: "PDF, DOCX and plain text. Scanned PDFs are processed via OCR." },
  { q: "How do I export reports?", a: "Open any report and click Download. We support PDF, DOCX and IEEE LaTeX." },
];

function HelpPage() {
  return (
    <div>
      <PageHeader title="Help & Support" subtitle="Search docs, FAQs and contact the team." />

      <div className="rounded-2xl glass p-5">
        <Input placeholder="Search documentation…" className="bg-secondary/60" />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {TOPICS.map((t) => (
          <Link key={t.title} to={t.to} className="group flex items-center justify-between rounded-2xl glass p-5 hover:border-[oklch(0.62_0.23_295_/_0.4)]">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl gradient-primary-bg">
                <t.icon className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h3 className="font-semibold">{t.title}</h3>
                <p className="text-xs text-muted-foreground">{t.desc}</p>
              </div>
            </div>
            <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          </Link>
        ))}
      </div>

      <div className="mt-6 rounded-2xl glass p-5">
        <h3 className="font-semibold">FAQ</h3>
        <div className="mt-4 space-y-3">
          {FAQ.map((f) => (
            <details key={f.q} className="group rounded-xl border border-border/40 bg-secondary/30 p-4">
              <summary className="cursor-pointer text-sm font-medium marker:hidden">{f.q}</summary>
              <p className="mt-2 text-sm text-muted-foreground">{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
