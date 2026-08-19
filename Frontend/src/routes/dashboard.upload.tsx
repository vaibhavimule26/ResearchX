import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
} from "lucide-react";

import { PageHeader } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import {
  getPapers,
  uploadPaper,
} from "@/lib/api";

export const Route = createFileRoute("/dashboard/upload")({
  head: () => ({
    meta: [
      {
        title: "Upload PDF — ResearchX",
      },
    ],
  }),
  component: UploadPage,
});

const STEPS = [
  { label: "Parsing", done: true },
  { label: "OCR", done: true },
  { label: "Chunking", done: true },
  { label: "Embedding", done: true },
  { label: "Indexing", done: true },
];

function UploadPage() {
  const [drag, setDrag] = useState(false);
  const [papers, setPapers] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPapers = async () => {
    try {
      setLoadingPapers(true);
      setError("");

      const response = await getPapers();

      setPapers(
        response?.data?.papers || []
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load papers"
      );
    } finally {
      setLoadingPapers(false);
    }
  };

  const uploadSelectedFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setMessage("");

      const response = await uploadPaper(file);

      setMessage(
        response?.message ||
          "PDF uploaded successfully"
      );

      await fetchPapers();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Upload failed"
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) return;

    await uploadSelectedFile(file);
  };

  const handleDrop = async (
    event: React.DragEvent<HTMLDivElement>
  ) => {
    event.preventDefault();
    setDrag(false);

    const file = event.dataTransfer.files?.[0];

    if (!file) return;

    await uploadSelectedFile(file);
  };

  useEffect(() => {
    fetchPapers();
  }, []);

  return (
    <div>
      <PageHeader
        title="Upload PDFs"
        subtitle="Drop research PDFs to parse, embed and analyze."
      />

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        className={`rounded-3xl border-2 border-dashed p-12 text-center transition-colors ${
          drag
            ? "border-[var(--electric)] bg-[var(--electric)]/5"
            : "border-border/60 bg-secondary/30"
        }`}
      >
        <UploadCloud className="mx-auto h-12 w-12 text-[var(--electric)]" />

        <h3 className="mt-4 font-display text-xl font-semibold">
          Drag & Drop your PDFs here
        </h3>

        <p className="mt-1 text-sm text-muted-foreground">
          or click to browse • up to 50 MB each
        </p>

        <Button
          variant="hero"
          className="mt-5"
          onClick={() =>
            fileInputRef.current?.click()
          }
          disabled={uploading}
        >
          {uploading
            ? "Uploading..."
            : "Browse Files"}
        </Button>

        <input
          type="file"
          accept=".pdf,application/pdf"
          ref={fileInputRef}
          onChange={handleUpload}
          hidden
        />
      </div>

      {message && (
        <div className="mt-4 rounded-xl border border-border/40 bg-secondary/30 p-3 text-sm">
          {message}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">
            Uploaded Files
          </h3>

          {loadingPapers ? (
            <p className="mt-4 text-sm text-muted-foreground">
              Loading papers...
            </p>
          ) : papers.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No papers uploaded yet.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {papers.map((paper, index) => (
                <li
                  key={`${paper.filename}-${paper.uploaded_at}-${index}`}
                  className="rounded-xl border border-border/40 bg-secondary/30 p-4"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-[var(--electric)]" />

                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {paper.filename}
                      </div>

                      <div className="text-xs text-muted-foreground">
                        Uploaded:{" "}
                        {paper.uploaded_at || "Unknown"}
                      </div>
                    </div>

                    <CheckCircle2 className="h-5 w-5 text-[var(--success)]" />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-2xl glass p-5">
          <h3 className="font-semibold">
            Analysis Pipeline
          </h3>

          <ul className="mt-4 space-y-3">
            {STEPS.map((step, index) => (
              <motion.li
                key={step.label}
                initial={{
                  opacity: 0,
                  x: -10,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                transition={{
                  delay: index * 0.06,
                }}
                className="flex items-center gap-3"
              >
                <span
                  className={`grid h-7 w-7 place-items-center rounded-full text-xs ${
                    step.done
                      ? "bg-[var(--success)] text-background"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {index + 1}
                </span>

                <span
                  className={`text-sm ${
                    step.done
                      ? "text-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  {step.label}
                </span>
              </motion.li>
            ))}
          </ul>

          <div className="mt-6 text-xs text-muted-foreground">
            Uploaded papers:{" "}
            <span className="text-foreground">
              {papers.length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}