import {
  createFileRoute,
  Link,
  useNavigate,
} from "@tanstack/react-router";
import { useState } from "react";
import { Github, Mail } from "lucide-react";
import { toast } from "sonner";

import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setLoading(true);

    try {
      const response = await register(
        name,
        email,
        password
      );

      toast.success(
        response?.message ||
          "Account created successfully!"
      );

      nav({
        to: "/login",
      });
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Registration failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start researching with 10 AI agents."
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
      <form
        className="space-y-4"
        onSubmit={handleRegister}
      >
        <div className="grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="glass"
          >
            <Github className="h-4 w-4" />
            GitHub
          </Button>

          <Button
            type="button"
            variant="glass"
          >
            <Mail className="h-4 w-4" />
            Google
          </Button>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          OR
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="space-y-2">
          <Label>Full name</Label>

          <Input
            required
            placeholder="Ada Lovelace"
            value={name}
            onChange={(event) =>
              setName(event.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <Label>Email</Label>

          <Input
            type="email"
            required
            placeholder="you@lab.edu"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <Label>Password</Label>

          <Input
            type="password"
            required
            minLength={8}
            placeholder="At least 8 characters"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />
        </div>

        <Button
          type="submit"
          variant="hero"
          className="w-full"
          size="lg"
          disabled={loading}
        >
          {loading
            ? "Creating…"
            : "Create account"}
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          By signing up you agree to our Terms and
          Privacy Policy.
        </p>
      </form>
    </AuthLayout>
  );
}