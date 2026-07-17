import { createFileRoute, Link } from "@tanstack/react-router";
import { Calendar, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/book-demo")({
  component: BookDemoPage,
});

function BookDemoPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <Calendar className="mx-auto h-16 w-16 text-primary mb-6" />

        <h1 className="text-5xl font-bold">
          Book a Demo
        </h1>

        <p className="mt-6 text-lg text-muted-foreground">
          Schedule a live walkthrough of ResearchX.
        </p>

        <Button
          className="mt-10"
          asChild
        >
          <a
            href="https://cal.com/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Book Now
          </a>
        </Button>

        <Button
          variant="outline"
          className="mt-4"
          asChild
        >
          <Link to="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back Home
          </Link>
        </Button>
      </div>
    </div>
  );
}