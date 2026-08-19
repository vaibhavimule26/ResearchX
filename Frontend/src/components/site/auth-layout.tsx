import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AnimatedBackground, FloatingParticles } from "@/components/site/animated-background";
import { Logo } from "@/components/site/logo";

export function AuthLayout({
  title, subtitle, children, footer,
}: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="relative grid min-h-screen lg:grid-cols-2">
      <AnimatedBackground />
      <FloatingParticles />

      <div className="relative hidden flex-col justify-between p-12 lg:flex">
        <Logo />
        <div>
          <h2 className="font-display text-4xl font-bold leading-tight">
            Your AI research <span className="gradient-text">team is waiting</span>
          </h2>
          <p className="mt-4 max-w-md text-muted-foreground">
            10 specialized agents. One coordinated platform. Ship research at the speed of thought.
          </p>
          <div className="mt-8 grid gap-3">
            {[
              "Semantic search across 5M+ papers",
              "Automated PDF analysis & summaries",
              "IEEE reports and presentations in minutes",
            ].map((t) => (
              <div key={t} className="rounded-xl glass p-4 text-sm">{t}</div>
            ))}
          </div>
        </div>
        <div className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} ResearchX Labs
        </div>
      </div>

      <div className="relative flex flex-col items-center justify-center p-6 sm:p-12">
        <div className="lg:hidden mb-8"><Logo /></div>
        <div className="w-full max-w-md rounded-3xl glass-strong p-8">
          <h1 className="font-display text-2xl font-bold">{title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-6">{children}</div>
          <div className="mt-6 border-t border-border/60 pt-6 text-sm text-muted-foreground">
            {footer}
          </div>
        </div>
        <Link to="/" className="mt-6 text-xs text-muted-foreground hover:text-foreground">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
