import { Link } from "@tanstack/react-router";
import { Github, Twitter, Linkedin, Mail } from "lucide-react";
import { Logo } from "./logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Footer() {
  return (
    <footer className="relative border-t border-border/60 bg-background/60">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-sm text-sm text-muted-foreground">
              The multi-agent AI operating system for modern research.
              From paper discovery to IEEE reports — fully automated.
            </p>
            <div className="mt-6 flex gap-2">
              <Button variant="glass" size="icon" aria-label="GitHub">
                <Github className="h-4 w-4" />
              </Button>
              <Button variant="glass" size="icon" aria-label="Twitter">
                <Twitter className="h-4 w-4" />
              </Button>
              <Button variant="glass" size="icon" aria-label="LinkedIn">
                <Linkedin className="h-4 w-4" />
              </Button>
              <Button variant="glass" size="icon" aria-label="Email">
                <Mail className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Product</h4>
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/features" className="hover:text-foreground">Features</Link></li>
              <li><Link to="/workspace-overview" className="hover:text-foreground">Workspace</Link></li>
              <li><Link to="/docs" className="hover:text-foreground">Documentation</Link></li>
              <li><Link to="/dashboard" className="hover:text-foreground">Dashboard</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Company</h4>
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/about" className="hover:text-foreground">About</Link></li>
              <li><a href="#" className="hover:text-foreground">Privacy</a></li>
              <li><a href="#" className="hover:text-foreground">Terms</a></li>
              <li><a href="#" className="hover:text-foreground">Support</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold">Newsletter</h4>
            <p className="mt-4 text-sm text-muted-foreground">
              Research updates, model releases, agent notes.
            </p>
            <form className="mt-4 flex gap-2" onSubmit={(e) => e.preventDefault()}>
              <Input placeholder="you@lab.edu" className="bg-card" />
              <Button variant="hero" type="submit">Subscribe</Button>
            </form>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border/60 pt-8 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} ResearchX Labs. All rights reserved.</p>
          <p>Built for researchers, by researchers.</p>
        </div>
      </div>
    </footer>
  );
}
