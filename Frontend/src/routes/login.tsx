import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Github, Mail } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/lib/api";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Login — ResearchX" }, { name: "description", content: "Sign in to your ResearchX workspace." }] }),
  component: LoginPage,
});

function LoginPage() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
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
          <Button type="button" variant="glass"><Github className="h-4 w-4" /> GitHub</Button>
          <Button type="button" variant="glass"><Mail className="h-4 w-4" /> Google</Button>
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
        <Button type="submit" variant="hero" className="w-full" size="lg" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthLayout>
  );
}
