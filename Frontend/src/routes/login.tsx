import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Mail, Lock, Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { login } from "@/lib/api";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Login — ResearchX" },
      { name: "description", content: "Sign in to your ResearchX workspace." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Process incoming OAuth callback token or error (preserved for existing backend redirects)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const provider = params.get("provider");
    const error = params.get("error");

    if (error) {
      const decoded = decodeURIComponent(error);
      setErrorMessage(decoded);
      toast.error(decoded);
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }

    if (token) {
      localStorage.setItem("token", token);
      const providerLabel = provider
        ? provider.charAt(0).toUpperCase() + provider.slice(1)
        : "OAuth";
      toast.success(`${providerLabel} sign-in successful! Entering ResearchX...`);
      window.history.replaceState({}, document.title, window.location.pathname);
      nav({ to: "/dashboard" });
    }
  }, [nav]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setLoading(true);

    try {
      const response = await login(trimmedEmail, password);

      if (response && response.access_token) {
        localStorage.setItem("token", response.access_token);
        toast.success("Login Successful!");
        nav({ to: "/dashboard" });
      } else {
        const msg = response?.message || "Invalid email or password. Please try again.";
        setErrorMessage(msg);
        toast.error(msg);
      }
    } catch (error: any) {
      const msg =
        error?.message ||
        "Unable to connect to the backend server. Please verify the backend is running.";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in with your email and password to access your workspace."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-foreground hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        {errorMessage && (
          <Alert variant="destructive" className="py-2.5">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs font-medium">
              {errorMessage}
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="email" className="flex items-center gap-1.5 text-xs font-medium">
            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
            Email Address
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            autoFocus
            required
            placeholder="you@lab.edu"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (errorMessage) setErrorMessage(null);
            }}
            disabled={loading}
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="flex items-center gap-1.5 text-xs font-medium">
              <Lock className="h-3.5 w-3.5 text-muted-foreground" />
              Password
            </Label>
            <Link
              to="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errorMessage) setErrorMessage(null);
              }}
              disabled={loading}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none transition-colors"
              tabIndex={-1}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        <Button
          type="submit"
          variant="hero"
          className="w-full flex items-center justify-center gap-2 mt-2"
          size="lg"
          disabled={loading || !email.trim() || !password}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Signing in…</span>
            </>
          ) : (
            <span>Sign in</span>
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}

