import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/site/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Reset password — ResearchX" }] }),
  component: ForgotPage,
});

function ForgotPage() {
  const [sent, setSent] = useState(false);
  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We'll email you a link to reset your password."
      footer={<>Remembered it? <Link to="/login" className="font-medium text-foreground hover:underline">Sign in</Link></>}
    >
      {sent ? (
        <div className="rounded-xl glass p-5 text-sm">
          Check your inbox — a reset link is on the way.
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            toast.success("Reset email sent");
            setSent(true);
          }}
        >
          <div className="space-y-2">
            <Label>Email</Label>
            <Input type="email" required placeholder="you@lab.edu" />
          </div>
          <Button type="submit" variant="hero" className="w-full" size="lg">
            Send reset link
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
