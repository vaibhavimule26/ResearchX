import { createFileRoute } from "@tanstack/react-router";
import { Bell, Globe, KeyRound, Palette, Shield, User } from "lucide-react";
import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/dashboard/settings")({
  head: () => ({ meta: [{ title: "Settings — ResearchX" }] }),
  component: SettingsPage,
});

function Section({ icon: Icon, title, desc, children }: any) {
  return (
    <div className="rounded-2xl glass p-5">
      <div className="flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-xl gradient-primary-bg">
          <Icon className="h-4 w-4 text-primary-foreground" />
        </div>
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p className="text-xs text-muted-foreground">{desc}</p>
        </div>
      </div>
      <div className="mt-5 space-y-4">{children}</div>
    </div>
  );
}

function Row({ label, hint, children }: any) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/40 bg-secondary/30 p-4">
      <div>
        <div className="text-sm font-medium">{label}</div>
        {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" subtitle="Manage your preferences & API access." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Section icon={User} title="Profile" desc="Your public account info.">
          <Row label="Display name"><Input defaultValue="Ada Lovelace" className="w-56" /></Row>
          <Row label="Email"><Input defaultValue="ada@researchx.ai" className="w-56" /></Row>
        </Section>

        <Section icon={Palette} title="Appearance" desc="Theme & visual preferences.">
          <Row label="Dark mode" hint="Optimized for late-night research."><Switch defaultChecked /></Row>
          <Row label="Reduce motion"><Switch /></Row>
        </Section>

        <Section icon={Bell} title="Notifications" desc="Stay updated on agent runs.">
          <Row label="Email digests"><Switch defaultChecked /></Row>
          <Row label="Agent completion alerts"><Switch defaultChecked /></Row>
          <Row label="Weekly research summary"><Switch /></Row>
        </Section>

        <Section icon={Globe} title="Language" desc="Interface language.">
          <Row label="Language">
            <select className="rounded-md border border-border/60 bg-secondary px-3 py-2 text-sm">
              <option>English (US)</option><option>English (UK)</option><option>Español</option><option>Deutsch</option>
            </select>
          </Row>
        </Section>

        <Section icon={KeyRound} title="API Keys" desc="Bring your own provider keys.">
          <Row label="OpenAI"><Input placeholder="sk-..." className="w-56" /></Row>
          <Row label="Anthropic"><Input placeholder="sk-ant-..." className="w-56" /></Row>
          <Row label="Cohere"><Input placeholder="..." className="w-56" /></Row>
        </Section>

        <Section icon={Shield} title="Security" desc="Account protection.">
          <Row label="Two-factor authentication"><Switch /></Row>
          <Row label="Active sessions" hint="3 active devices."><Button variant="glass" size="sm">Manage</Button></Row>
          <Row label="Delete account" hint="Permanent. Cannot be undone."><Button variant="destructive" size="sm">Delete</Button></Row>
        </Section>
      </div>
    </div>
  );
}
