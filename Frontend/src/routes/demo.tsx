import { createFileRoute, Link } from "@tanstack/react-router";
import { Play, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/demo")({
  component: DemoPage,
});

function DemoPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-4xl w-full text-center">
        <Play className="mx-auto h-16 w-16 text-primary mb-6" />

        <h1 className="text-5xl font-bold">
          Product Demo
        </h1>

        <p className="mt-6 text-lg text-muted-foreground">
          Demo video will be available soon.
        </p>

        <div className="mt-10 aspect-video w-full rounded-2xl border border-border bg-secondary flex items-center justify-center">
          <span className="text-muted-foreground">
            Demo Video Placeholder
          </span>
        </div>

        <Button asChild className="mt-10">
          <Link to="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back Home
          </Link>
        </Button>
      </div>
    </div>
  );
}