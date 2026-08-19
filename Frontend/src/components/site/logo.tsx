import { Link } from "@tanstack/react-router";
import { Brain } from "lucide-react";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link to="/" className={`group flex items-center gap-2 ${className}`}>
      <div className="relative grid h-9 w-9 place-items-center rounded-xl gradient-primary-bg glow-primary">
        <Brain className="h-5 w-5 text-primary-foreground" />
        <span className="absolute inset-0 rounded-xl bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
      <span className="font-display text-lg font-bold tracking-tight">
        Research<span className="gradient-text">X</span>
      </span>
    </Link>
  );
}
