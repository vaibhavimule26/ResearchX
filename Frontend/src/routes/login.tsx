import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Github } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login, getOAuthLoginUrl } from "@/lib/api";

function GoogleIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
        fill="#EA4335"
      />
    </svg>
  );
}

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Login — ResearchX" }, { name: "description", content: "Sign in to your ResearchX workspace." }] }),
  component: LoginPage,
});

function LoginPage() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Process incoming OAuth callback token or error
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const provider = params.get("provider");
    const error = params.get("error");

    if (error) {
      toast.error(decodeURIComponent(error));
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }

    if (token) {
      localStorage.setItem("token", token);
      const providerLabel = provider ? provider.charAt(0).toUpperCase() + provider.slice(1) : "OAuth";
      toast.success(`${providerLabel} sign-in successful! Entering ResearchX...`);
      window.history.replaceState({}, document.title, window.location.pathname);
      nav({ to: "/dashboard" });
    }
  }, [nav]);

  const handleOAuthLogin = (provider: "github" | "google") => {
    setOauthLoading(provider);
    window.location.href = getOAuthLoginUrl(provider);
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue your research."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-foreground hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setLoading(true);

          try {
            const response = await login(email, password);

            if (response.access_token) {
              localStorage.setItem("token", response.access_token);
              toast.success("Login Successful!");
              nav({ to: "/dashboard" });
            } else {
              toast.error(response.message || "Login Failed");
            }
          } catch (error) {
            toast.error("Cannot connect to backend");
          } finally {
            setLoading(false);
          }
        }}
      >
        <div className="grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="glass"
            disabled={oauthLoading !== null}
            onClick={() => handleOAuthLogin("github")}
            className="w-full flex items-center justify-center gap-2 text-sm font-medium hover:border-border/80"
          >
            <Github className="h-4 w-4 shrink-0" />
            <span>{oauthLoading === "github" ? "Connecting…" : "GitHub"}</span>
          </Button>

          <Button
            type="button"
            variant="glass"
            disabled={oauthLoading !== null}
            onClick={() => handleOAuthLogin("google")}
            className="w-full flex items-center justify-center gap-2 text-sm font-medium hover:border-border/80"
          >
            <GoogleIcon className="h-4 w-4 shrink-0" />
            <span>{oauthLoading === "google" ? "Connecting…" : "Google"}</span>
          </Button>
        </div>


        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="h-px flex-1 bg-border" /> OR <div className="h-px flex-1 bg-border" />
        </div>

        <div className="space-y-2">
          <Label>Email</Label>
          <Input
            type="email"
            required
            placeholder="you@lab.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Password</Label>
            <Link to="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground">
              Forgot password?
            </Link>
          </div>
          <Input
            type="password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <Button type="submit" variant="hero" className="w-full" size="lg" disabled={loading || oauthLoading !== null}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthLayout>
  );
}

