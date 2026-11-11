import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { User, Mail, Lock, Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { register } from "@/lib/api";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      {
        title: "Create account — ResearchX",
      },
      {
        name: "description",
        content: "Create your ResearchX account.",
      },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const nav = useNavigate();

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();

    if (!trimmedName || !trimmedEmail || !password) {
      setErrorMessage("Please fill in all required fields.");
      return;
    }

    if (password.length < 8) {
      const msg = "Password must be at least 8 characters long.";
      setErrorMessage(msg);
      toast.error(msg);
      return;
    }

    if (password !== confirmPassword) {
      const msg = "Passwords do not match. Please verify your password.";
      setErrorMessage(msg);
      toast.error(msg);
      return;
    }

    setLoading(true);

    try {
      const response = await register(trimmedName, trimmedEmail, password);

      // Backend returns { "message": "User already exists" } if email is registered
      if (response?.message === "User already exists") {
        const msg = "An account with this email already exists. Please sign in instead.";
        setErrorMessage(msg);
        toast.error(msg);
        return;
      }

      if (response?.user_id || response?.message === "User Registered Successfully") {
        toast.success("Account created successfully! Please sign in with your credentials.");
        nav({ to: "/login" });
      } else {
        const msg = response?.message || "Registration failed. Please try again.";
        setErrorMessage(msg);
        toast.error(msg);
      }
    } catch (error: any) {
      const msg =
        error instanceof Error
          ? error.message
          : "Registration failed. Please try again.";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Sign up with your email to start researching with 10 AI agents."
      footer={
        <>
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-foreground hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={handleRegister}>
        {errorMessage && (
          <Alert variant="destructive" className="py-2.5">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs font-medium">
              {errorMessage}
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="name" className="flex items-center gap-1.5 text-xs font-medium">
            <User className="h-3.5 w-3.5 text-muted-foreground" />
            Full Name
          </Label>
          <Input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            autoFocus
            required
            placeholder="Ada Lovelace"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              if (errorMessage) setErrorMessage(null);
            }}
            disabled={loading}
          />
        </div>

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
            required
            placeholder="you@lab.edu"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (errorMessage) setErrorMessage(null);
            }}
            disabled={loading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="flex items-center gap-1.5 text-xs font-medium">
            <Lock className="h-3.5 w-3.5 text-muted-foreground" />
            Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={8}
              placeholder="At least 8 characters"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
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

        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className="flex items-center gap-1.5 text-xs font-medium">
            <Lock className="h-3.5 w-3.5 text-muted-foreground" />
            Confirm Password
          </Label>
          <div className="relative">
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={8}
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(event.target.value);
                if (errorMessage) setErrorMessage(null);
              }}
              disabled={loading}
              className="pr-10"
            />
          </div>
        </div>

        <Button
          type="submit"
          variant="hero"
          className="w-full flex items-center justify-center gap-2 mt-2"
          size="lg"
          disabled={loading || !name.trim() || !email.trim() || !password || !confirmPassword}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Creating account…</span>
            </>
          ) : (
            <span>Create account</span>
          )}
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          By signing up you agree to our Terms and Privacy Policy.
        </p>
      </form>
    </AuthLayout>
  );
}