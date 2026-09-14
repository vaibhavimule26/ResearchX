import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  Bell,
  Globe,
  KeyRound,
  Palette,
  Shield,
  User,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Sparkles,
  Laptop,
  Check,
  Sun,
  Moon,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useTheme, type Theme } from "@/lib/theme-provider";

export const Route = createFileRoute("/dashboard/settings")({
  head: () => ({
    meta: [{ title: "Settings & Preferences — ResearchX" }],
  }),
  component: SettingsPage,
});

function SectionCard({
  icon: Icon,
  iconColor = "text-primary",
  iconBg = "bg-primary/10 border-primary/20",
  title,
  desc,
  children,
  badge,
}: {
  icon: any;
  iconColor?: string;
  iconBg?: string;
  title: string;
  desc: string;
  children: React.ReactNode;
  badge?: string;
}) {
  return (
    <div className="rounded-2xl border border-border/50 bg-card/80 p-6 backdrop-blur-xl shadow-sm transition-all hover:border-border/70">
      <div className="flex items-center justify-between border-b border-border/40 pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className={`grid h-9 w-9 place-items-center rounded-xl border ${iconBg} ${iconColor}`}>
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-foreground">
              {title}
            </h3>
            <p className="text-xs text-muted-foreground">{desc}</p>
          </div>
        </div>

        {badge && (
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-secondary/70 text-muted-foreground border border-border/40 uppercase">
            {badge}
          </span>
        )}
      </div>

      <div className="space-y-3.5">{children}</div>
    </div>
  );
}

function SettingsRow({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-border/40 bg-secondary/20 p-3.5 transition-colors hover:bg-secondary/35">
      <div className="min-w-0 flex-1 pr-2">
        <div className="text-xs font-semibold text-foreground">{label}</div>
        {hint && (
          <div className="text-[11px] text-muted-foreground/80 mt-0.5 leading-relaxed">
            {hint}
          </div>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function SettingsPage() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [savedFeedback, setSavedFeedback] = useState(false);

  const toggleKey = (provider: string) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleSave = () => {
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 2000);
  };

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Settings &amp; Preferences"
        subtitle="Manage your academic researcher profile, appearance, notifications, and LLM provider credentials."
        action={
          <Button
            variant="hero"
            size="sm"
            onClick={handleSave}
            className="h-8 text-xs gap-1.5 shadow-sm"
          >
            {savedFeedback ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span>Preferences Saved</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                <span>Save Preferences</span>
              </>
            )}
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2 items-start">
        {/* Profile Card */}
        <SectionCard
          icon={User}
          title="Researcher Profile"
          desc="Academic identification and publication credentials."
          badge="Account"
        >
          <SettingsRow label="Display Name" hint="Appears on generated IEEE reports.">
            <Input
              defaultValue="Dr. Alex Rivera"
              className="h-8 text-xs w-52 bg-secondary/40 border-border/60"
            />
          </SettingsRow>

          <SettingsRow label="Institutional Email" hint="Academic login handle.">
            <Input
              defaultValue="alex.rivera@researchx.ai"
              className="h-8 text-xs w-52 bg-secondary/40 border-border/60"
            />
          </SettingsRow>

          <SettingsRow label="University / Lab" hint="Affiliation for citations.">
            <Input
              defaultValue="Stanford AI Research Lab"
              className="h-8 text-xs w-52 bg-secondary/40 border-border/60"
            />
          </SettingsRow>
        </SectionCard>

        {/* Appearance Card */}
        <SectionCard
          icon={Palette}
          iconColor="text-purple-400"
          iconBg="bg-purple-500/10 border-purple-500/20"
          title="Appearance"
          desc="Choose your preferred ResearchX workspace theme."
          badge="Theme"
        >
          {/* Theme Selector Dropdown Row */}
          <SettingsRow
            label="Theme"
            hint="Select Dark, Light, or System-synchronized mode."
          >
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as Theme)}
              className="h-8 rounded-xl border border-border/60 bg-secondary/60 px-3 text-xs text-foreground outline-none cursor-pointer focus:ring-2 focus:ring-primary/40 font-medium transition-colors"
            >
              <option value="dark">☾ Dark</option>
              <option value="light">☀ Light</option>
              <option value="system">◐ System</option>
            </select>
          </SettingsRow>

          {/* Interactive Theme Previews */}
          <div className="space-y-2 pt-1">
            <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Theme Preview
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Dark Theme Preview Card */}
              <div
                onClick={() => setTheme("dark")}
                className={`group relative cursor-pointer rounded-xl border p-3 transition-all duration-200 ${
                  theme === "dark"
                    ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary/40"
                    : "border-border/60 bg-secondary/20 hover:border-border/90 hover:bg-secondary/40"
                }`}
              >
                {/* Mini Mockup Window */}
                <div className="overflow-hidden rounded-lg border border-border/50 bg-[#0B0F17] p-2 shadow-inner aspect-[16/10] flex flex-col justify-between">
                  <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-red-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-amber-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
                    </div>
                    <div className="h-1.5 w-10 rounded bg-white/20" />
                  </div>
                  <div className="flex gap-1.5 my-auto">
                    <div className="w-5 h-8 rounded bg-white/10 shrink-0" />
                    <div className="flex-1 space-y-1">
                      <div className="h-2 w-3/4 rounded bg-purple-500/60" />
                      <div className="h-1.5 w-full rounded bg-white/20" />
                      <div className="h-1.5 w-4/5 rounded bg-white/15" />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[8px] text-white/40 font-mono">
                    <span>Dark</span>
                    <span className="h-1.5 w-6 rounded bg-purple-400/40" />
                  </div>
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
                      <Moon className="h-3 w-3 text-purple-400" />
                      <span>Dark</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">Deep contrast, eye comfort</div>
                  </div>
                  {theme === "dark" && (
                    <div className="h-4 w-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                      <Check className="h-2.5 w-2.5" />
                    </div>
                  )}
                </div>
              </div>

              {/* Light Theme Preview Card */}
              <div
                onClick={() => setTheme("light")}
                className={`group relative cursor-pointer rounded-xl border p-3 transition-all duration-200 ${
                  theme === "light"
                    ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary/40"
                    : "border-border/60 bg-secondary/20 hover:border-border/90 hover:bg-secondary/40"
                }`}
              >
                {/* Mini Mockup Window */}
                <div className="overflow-hidden rounded-lg border border-slate-300 bg-[#FAFAFC] p-2 shadow-inner aspect-[16/10] flex flex-col justify-between">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-red-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-amber-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
                    </div>
                    <div className="h-1.5 w-10 rounded bg-slate-300" />
                  </div>
                  <div className="flex gap-1.5 my-auto">
                    <div className="w-5 h-8 rounded bg-slate-200 shrink-0" />
                    <div className="flex-1 space-y-1">
                      <div className="h-2 w-3/4 rounded bg-purple-600/70" />
                      <div className="h-1.5 w-full rounded bg-slate-700/60" />
                      <div className="h-1.5 w-4/5 rounded bg-slate-400/60" />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-200 text-[8px] text-slate-500 font-mono">
                    <span>Light</span>
                    <span className="h-1.5 w-6 rounded bg-purple-600/40" />
                  </div>
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
                      <Sun className="h-3 w-3 text-amber-500" />
                      <span>Light</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">Academic clarity, crisp text</div>
                  </div>
                  {theme === "light" && (
                    <div className="h-4 w-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                      <Check className="h-2.5 w-2.5" />
                    </div>
                  )}
                </div>
              </div>

              {/* System (Auto) Theme Preview Card */}
              <div
                onClick={() => setTheme("system")}
                className={`group relative cursor-pointer rounded-xl border p-3 transition-all duration-200 ${
                  theme === "system"
                    ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary/40"
                    : "border-border/60 bg-secondary/20 hover:border-border/90 hover:bg-secondary/40"
                }`}
              >
                {/* Mini Mockup Window (Split Dark/Light) */}
                <div className="overflow-hidden rounded-lg border border-border/50 bg-gradient-to-r from-[#0B0F17] 50% to-[#FAFAFC] 50% p-2 shadow-inner aspect-[16/10] flex flex-col justify-between">
                  <div className="flex items-center justify-between border-b border-border/40 pb-1.5">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-red-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-amber-400/80" />
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
                    </div>
                    <div className="h-1.5 w-10 rounded bg-muted-foreground/30" />
                  </div>
                  <div className="flex gap-1.5 my-auto">
                    <div className="w-5 h-8 rounded bg-muted/40 shrink-0" />
                    <div className="flex-1 space-y-1">
                      <div className="h-2 w-3/4 rounded bg-primary/80" />
                      <div className="h-1.5 w-full rounded bg-muted-foreground/40" />
                      <div className="h-1.5 w-4/5 rounded bg-muted-foreground/30" />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-border/40 text-[8px] text-muted-foreground font-mono">
                    <span>Auto</span>
                    <span className="text-[7px] uppercase font-bold text-primary">{resolvedTheme}</span>
                  </div>
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
                      <Laptop className="h-3.5 w-3.5 text-blue-400" />
                      <span>System</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">Follows OS ({resolvedTheme})</div>
                  </div>
                  {theme === "system" && (
                    <div className="h-4 w-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                      <Check className="h-2.5 w-2.5" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <SettingsRow
            label="High-Density Mode"
            hint="Compact margins for dense empirical comparison tables."
          >
            <Switch defaultChecked />
          </SettingsRow>

          <SettingsRow
            label="Reduce Micro-Animations"
            hint="Minimizes transition motions on lower-powered devices."
          >
            <Switch />
          </SettingsRow>
        </SectionCard>

        {/* Notifications Card */}
        <SectionCard
          icon={Bell}
          iconColor="text-blue-400"
          iconBg="bg-blue-500/10 border-blue-500/20"
          title="Research Notifications"
          desc="Alerts for multi-agent synthesis runs."
          badge="Alerts"
        >
          <SettingsRow
            label="Agent Completion Alerts"
            hint="Notify immediately when long-running reports finish."
          >
            <Switch defaultChecked />
          </SettingsRow>

          <SettingsRow
            label="Synthesis Error Alerts"
            hint="Alert if PDF parsing or embedding extraction encounters issues."
          >
            <Switch defaultChecked />
          </SettingsRow>

          <SettingsRow
            label="Weekly Research Digest"
            hint="Summary of analyzed papers, extracted gaps, and saved projects."
          >
            <Switch />
          </SettingsRow>
        </SectionCard>

        {/* Language & Standards Card */}
        <SectionCard
          icon={Globe}
          iconColor="text-emerald-400"
          iconBg="bg-emerald-500/10 border-emerald-500/20"
          title="Language &amp; Citation Standards"
          desc="Output localization and academic formatting."
          badge="Locale"
        >
          <SettingsRow
            label="Interface Language"
            hint="System workspace language."
          >
            <select className="h-8 rounded-xl border border-border/60 bg-secondary/60 px-3 text-xs text-foreground outline-none">
              <option>English (US) — Academic</option>
              <option>English (UK)</option>
              <option>Deutsch</option>
              <option>Français</option>
            </select>
          </SettingsRow>

          <SettingsRow
            label="Primary Citation Style"
            hint="Default standard applied across report bibliographies."
          >
            <select className="h-8 rounded-xl border border-border/60 bg-secondary/60 px-3 text-xs text-foreground outline-none">
              <option>IEEE Transactions [1]</option>
              <option>ACM Digital Library</option>
              <option>APA 7th Edition</option>
              <option>BibTeX Key Format</option>
            </select>
          </SettingsRow>
        </SectionCard>

        {/* API Keys Card (Masked Presentation) */}
        <SectionCard
          icon={KeyRound}
          iconColor="text-amber-400"
          iconBg="bg-amber-500/10 border-amber-500/20"
          title="API Keys &amp; LLM Providers"
          desc="Bring your own provider keys for dedicated inference."
          badge="Security"
        >
          <SettingsRow
            label="OpenAI API Key"
            hint="Used for GPT-4o synthesis and embedding fallback."
          >
            <div className="relative flex items-center">
              <Input
                type={showKeys.openai ? "text" : "password"}
                defaultValue="sk-proj-98234892348239482394"
                className="h-8 text-xs w-48 pr-8 font-mono bg-secondary/40 border-border/60"
                readOnly
              />
              <button
                type="button"
                onClick={() => toggleKey("openai")}
                className="absolute right-2 text-muted-foreground hover:text-foreground"
                title={showKeys.openai ? "Hide key" : "Show key"}
              >
                {showKeys.openai ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          </SettingsRow>

          <SettingsRow
            label="Google Gemini API Key"
            hint="Powers fast multi-modal document extraction."
          >
            <div className="relative flex items-center">
              <Input
                type={showKeys.gemini ? "text" : "password"}
                defaultValue="AIzaSyA8943289423894239842"
                className="h-8 text-xs w-48 pr-8 font-mono bg-secondary/40 border-border/60"
                readOnly
              />
              <button
                type="button"
                onClick={() => toggleKey("gemini")}
                className="absolute right-2 text-muted-foreground hover:text-foreground"
                title={showKeys.gemini ? "Hide key" : "Show key"}
              >
                {showKeys.gemini ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          </SettingsRow>

          <SettingsRow
            label="Anthropic Claude API Key"
            hint="For Claude 3.5 Sonnet long-context analysis."
          >
            <div className="relative flex items-center">
              <Input
                type={showKeys.anthropic ? "text" : "password"}
                defaultValue="sk-ant-api03-982489238492"
                className="h-8 text-xs w-48 pr-8 font-mono bg-secondary/40 border-border/60"
                readOnly
              />
              <button
                type="button"
                onClick={() => toggleKey("anthropic")}
                className="absolute right-2 text-muted-foreground hover:text-foreground"
                title={showKeys.anthropic ? "Hide key" : "Show key"}
              >
                {showKeys.anthropic ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          </SettingsRow>
        </SectionCard>

        {/* Security & Danger Zone Card */}
        <SectionCard
          icon={Shield}
          iconColor="text-rose-400"
          iconBg="bg-rose-500/10 border-rose-500/20"
          title="Account Security &amp; Data"
          desc="Authentication sessions and workspace lifecycle."
          badge="Protected"
        >
          <SettingsRow
            label="Two-Factor Authentication (2FA)"
            hint="Secure account with authenticator app TOTP."
          >
            <Switch defaultChecked />
          </SettingsRow>

          <SettingsRow
            label="Active Research Sessions"
            hint="Currently active on 2 desktop devices."
          >
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs border-border/60 hover:bg-secondary/60"
            >
              <Laptop className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
              Manage Sessions
            </Button>
          </SettingsRow>

          {/* Danger Zone */}
          <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 mt-4 space-y-3">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span className="text-xs font-bold uppercase tracking-wider">
                Danger Zone
              </span>
            </div>

            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Permanently delete your account, stored PDFs, vector embeddings, and generated IEEE reports. This action is irreversible.
            </p>

            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="h-8 text-xs"
            >
              Delete ResearchX Account
            </Button>
          </div>
        </SectionCard>
      </div>

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-md rounded-2xl border border-destructive/50 bg-card p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-destructive">
              <div className="rounded-xl bg-destructive/20 p-2">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground">
                  Confirm Account Deletion
                </h3>
                <p className="text-xs text-muted-foreground">
                  This action cannot be undone.
                </p>
              </div>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Please type <span className="font-mono text-destructive font-bold">DELETE</span> to confirm that you want to purge all your research data.
            </p>

            <Input
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE..."
              className="h-9 text-xs border-destructive/40 bg-secondary/30"
              autoFocus
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteConfirmText("");
                }}
                className="h-8 text-xs"
              >
                Cancel
              </Button>

              <Button
                variant="destructive"
                size="sm"
                disabled={deleteConfirmText !== "DELETE"}
                onClick={() => {
                  localStorage.clear();
                  window.location.href = "/login";
                }}
                className="h-8 text-xs"
              >
                Permanently Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SettingsPage;
