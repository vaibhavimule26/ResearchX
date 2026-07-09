import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  FileText,
  Bookmark,
  FileSpreadsheet,
  Presentation,
  Upload,
  Sparkles,
  Search,
  ArrowUpRight,
  Bot,
  Plus,
  TrendingUp,
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getCurrentUser, getPapers } from "@/lib/api";

export const Route = createFileRoute("/dashboard/")({
  head: () => ({ meta: [{ title: "Dashboard — ResearchX" }] }),
  component: DashboardHome,
});

const STATS = [
  { label: "Papers Indexed", value: "5,248,910", delta: "+12%", icon: FileText },
  { label: "Saved Projects", value: "37", delta: "+4", icon: Bookmark },
  { label: "Reports Generated", value: "21", delta: "+3", icon: FileSpreadsheet },
  { label: "Presentations", value: "14", delta: "+2", icon: Presentation },
  { label: "PDFs Uploaded", value: "126", delta: "+18", icon: Upload },
];

const ACTIVITY = [
  { name: "Mon", value: 12 }, { name: "Tue", value: 19 }, { name: "Wed", value: 14 },
  { name: "Thu", value: 28 }, { name: "Fri", value: 33 }, { name: "Sat", value: 22 }, { name: "Sun", value: 30 },
];
const RUNS = [
  { name: "W1", retrieval: 14, analysis: 9, reports: 3 },
  { name: "W2", retrieval: 22, analysis: 14, reports: 5 },
  { name: "W3", retrieval: 28, analysis: 18, reports: 7 },
  { name: "W4", retrieval: 41, analysis: 26, reports: 11 },
];

const RECENT = [
  { title: "Multimodal LLM survey", agent: "Literature Survey", time: "2h ago", status: "completed" },
  { title: "Vision transformers — gap analysis", agent: "Gap Detection", time: "5h ago", status: "completed" },
  { title: "Retrieval augmentation for biomedical QA", agent: "Paper Retrieval", time: "Yesterday", status: "completed" },
  { title: "Graph neural networks IEEE report", agent: "IEEE Report", time: "2d ago", status: "completed" },
];

const TASKS = [
  { title: "Review summary for ViT-22B paper", due: "Today" },
  { title: "Export literature survey: RAG systems", due: "Tomorrow" },
  { title: "Generate PPT for thesis defense", due: "Fri" },
];

const SUGGESTIONS = [
  "Explore long-context retrieval techniques (2024)",
  "Compare MoE architectures across major labs",
  "Investigate evaluation benchmarks for agentic systems",
];

function DashboardHome() {
  const navigate = useNavigate();

  const [user, setUser] = useState({
    name: "",
    email: "",
  });

  const [paperCount, setPaperCount] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate({ to: "/login" });
      return;
    }

    getCurrentUser(token)
      .then((data) => {
        setUser(data);
      })
      .catch((error) => {
        console.error(
          "Failed to load user:",
          error
        );
      });
  }, [navigate]);

  useEffect(() => {
    const loadPaperCount = async () => {
      try {
        const response = await getPapers();

        const papers =
          response?.data?.papers || [];

        setPaperCount(papers.length);
      } catch (error) {
        console.error(
          "Failed to load paper count:",
          error
        );
      }
    };

    loadPaperCount();
  }, []);

  return (

    <div>
      <PageHeader
  title={`Welcome back, ${user.name || "Researcher"}`}
  subtitle="Here's what your research OS has been up to."
  action={
    <div className="flex gap-2">
      <Button asChild variant="hero">
        <Link to="/dashboard/workspace">
          <Plus className="h-4 w-4" />
          New Research
        </Link>
      </Button>
    </div>
  }
/>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className="rounded-2xl glass p-5"
          >
            <div className="flex items-center justify-between">
              <s.icon className="h-5 w-5 text-[var(--electric)]" />
              <span className="inline-flex items-center gap-1 rounded-full bg-[var(--success)]/15 px-2 py-0.5 text-[10px] text-[var(--success)]">
                <TrendingUp className="h-3 w-3" />{s.delta}
              </span>
            </div>
            <div className="mt-4 font-display text-2xl font-bold">
  {s.label === "PDFs Uploaded"
    ? paperCount
    : s.value}
</div>
            <div className="text-xs text-muted-foreground">{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl glass p-5 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Research Activity</h3>
              <p className="text-xs text-muted-foreground">Past 7 days</p>
            </div>
          </div>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <AreaChart data={ACTIVITY}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.62 0.23 295)" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="oklch(0.62 0.23 295)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 0.05)" />
                <XAxis dataKey="name" stroke="oklch(0.7 0.02 270)" fontSize={12} />
                <YAxis stroke="oklch(0.7 0.02 270)" fontSize={12} />
                <Tooltip contentStyle={{ background: "oklch(0.17 0.018 270)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 12 }} />
                <Area type="monotone" dataKey="value" stroke="oklch(0.7 0.2 240)" fill="url(#g1)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Quick Actions</h3>
          <div className="mt-4 grid gap-2">
            {[
              { icon: Search, label: "Search papers", to: "/dashboard/papers" },
              { icon: Upload, label: "Upload PDF", to: "/dashboard/upload" },
              { icon: Sparkles, label: "AI Chat", to: "/dashboard/chat" },
              { icon: FileSpreadsheet, label: "IEEE Report", to: "/dashboard/report" },
              { icon: Presentation, label: "PPT Generator", to: "/dashboard/ppt" },
            ].map((a) => (
              <Link key={a.label} to={a.to} className="flex items-center justify-between rounded-xl border border-border/60 bg-secondary/40 px-4 py-3 text-sm hover:bg-accent">
                <span className="flex items-center gap-3"><a.icon className="h-4 w-4 text-[var(--electric)]" /> {a.label}</span>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl glass p-5 lg:col-span-2">
          <h3 className="font-semibold">Agent Runs (last 4 weeks)</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <BarChart data={RUNS}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(1 0 0 / 0.05)" />
                <XAxis dataKey="name" stroke="oklch(0.7 0.02 270)" fontSize={12} />
                <YAxis stroke="oklch(0.7 0.02 270)" fontSize={12} />
                <Tooltip contentStyle={{ background: "oklch(0.17 0.018 270)", border: "1px solid oklch(1 0 0 / 0.1)", borderRadius: 12 }} />
                <Bar dataKey="retrieval" fill="oklch(0.62 0.23 295)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="analysis" fill="oklch(0.7 0.2 240)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="reports" fill="oklch(0.78 0.16 75)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Research Progress</h3>
          <div className="mt-4 space-y-4">
            {[
              { name: "RAG benchmarks", pct: 84 },
              { name: "Vision-Language models", pct: 62 },
              { name: "Agentic eval framework", pct: 41 },
            ].map((p) => (
              <div key={p.name}>
                <div className="flex justify-between text-xs">
                  <span>{p.name}</span><span className="text-muted-foreground">{p.pct}%</span>
                </div>
                <Progress value={p.pct} className="mt-1.5" />
              </div>
            ))}
          </div>

          <h3 className="mt-6 font-semibold">Latest AI Suggestions</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {SUGGESTIONS.map((s) => (
              <li key={s} className="flex gap-2"><Bot className="h-4 w-4 shrink-0 text-[var(--purple-glow)]" />{s}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Recent Research</h3>
          <ul className="mt-4 space-y-3">
            {RECENT.map((r) => (
              <li key={r.title} className="flex items-center justify-between rounded-xl border border-border/40 bg-secondary/30 px-4 py-3 text-sm">
                <div className="min-w-0">
                  <div className="truncate font-medium">{r.title}</div>
                  <div className="text-xs text-muted-foreground">{r.agent}</div>
                </div>
                <span className="text-xs text-muted-foreground">{r.time}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">Upcoming Tasks</h3>
          <ul className="mt-4 space-y-3">
            {TASKS.map((t) => (
              <li key={t.title} className="flex items-center justify-between rounded-xl border border-border/40 bg-secondary/30 px-4 py-3 text-sm">
                <span>{t.title}</span>
                <span className="rounded-full bg-[var(--electric)]/15 px-2 py-0.5 text-xs text-[var(--electric)]">{t.due}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
