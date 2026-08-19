import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Award, BookOpen, FileText, Sparkles, Trophy, Zap } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { getCurrentUser } from "@/lib/api";

export const Route = createFileRoute("/dashboard/profile")({
  head: () => ({ meta: [{ title: "Profile — ResearchX" }] }),
  component: ProfilePage,
});

const STATS = [
  { l: "Sessions", v: "184" }, { l: "Papers analyzed", v: "612" },
  { l: "Reports generated", v: "21" }, { l: "PPTs", v: "14" },
];

const ACHIEVEMENTS = [
  { icon: Trophy, name: "First Report", desc: "Generated your first IEEE report." },
  { icon: Zap, name: "Speedrunner", desc: "Completed 5 sessions in one day." },
  { icon: BookOpen, name: "Bookworm", desc: "Analyzed 500+ papers." },
  { icon: Sparkles, name: "Innovator", desc: "Used all 10 agents in a project." },
];

function ProfilePage() {
  const [user, setUser] = useState({
    name: "",
    email: "",
  });

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) return;

    getCurrentUser(token)
      .then((data) => setUser(data))
      .catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader title="Profile" subtitle="Your research identity & achievements." />
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="rounded-2xl glass p-6 text-center">
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-full gradient-primary-bg font-display text-2xl font-bold text-primary-foreground">
            {user.name
              ? user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
              : "U"}
          </div>
          <h2 className="mt-3 font-display text-xl font-semibold">{user.name || "Loading..."}</h2>
          <p className="text-sm text-muted-foreground">{user.email || "Loading..."}</p>
          <p className="mt-2 text-xs text-muted-foreground">PhD candidate · Computational Linguistics</p>
          <div className="mt-5 grid grid-cols-2 gap-2">
            {STATS.map((s) => (
              <div key={s.l} className="rounded-xl border border-border/40 bg-secondary/30 p-3">
                <div className="font-display text-lg font-bold">{s.v}</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl glass p-5">
            <div className="flex items-center gap-2">
              <Award className="h-4 w-4 text-[var(--warning)]" />
              <h3 className="font-semibold">Achievements</h3>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {ACHIEVEMENTS.map((a) => (
                <div key={a.name} className="flex items-start gap-3 rounded-xl border border-border/40 bg-secondary/30 p-3">
                  <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl gradient-primary-bg">
                    <a.icon className="h-4 w-4 text-primary-foreground" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">{a.name}</div>
                    <div className="text-xs text-muted-foreground">{a.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl glass p-5">
            <h3 className="font-semibold">Recent Activity</h3>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li className="flex items-center gap-2"><FileText className="h-3.5 w-3.5 text-[var(--electric)]" /> Exported IEEE Report 'M-RAG v2' · 2h ago</li>
              <li className="flex items-center gap-2"><Sparkles className="h-3.5 w-3.5 text-[var(--purple-glow)]" /> Started session 'Agent Evaluation' · 6h ago</li>
              <li className="flex items-center gap-2"><BookOpen className="h-3.5 w-3.5 text-[var(--success)]" /> Bookmarked 4 papers · yesterday</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}