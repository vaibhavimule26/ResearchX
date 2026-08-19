import { motion } from "framer-motion";

export function AnimatedBackground({ variant = "default" }: { variant?: "default" | "subtle" }) {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-30" />
      <div
        className="absolute -top-40 -left-32 h-[500px] w-[500px] rounded-full animate-blob"
        style={{
          background:
            "radial-gradient(circle, oklch(0.62 0.23 295 / 0.35), transparent 70%)",
        }}
      />
      <div
        className="absolute top-1/3 -right-40 h-[600px] w-[600px] rounded-full animate-blob"
        style={{
          background:
            "radial-gradient(circle, oklch(0.7 0.2 240 / 0.3), transparent 70%)",
          animationDelay: "4s",
        }}
      />
      {variant === "default" && (
        <div
          className="absolute bottom-0 left-1/3 h-[400px] w-[400px] rounded-full animate-blob"
          style={{
            background:
              "radial-gradient(circle, oklch(0.68 0.25 300 / 0.25), transparent 70%)",
            animationDelay: "8s",
          }}
        />
      )}
    </div>
  );
}

export function FloatingParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {Array.from({ length: 24 }).map((_, i) => {
        const size = 2 + (i % 4);
        const delay = (i * 0.4) % 6;
        const duration = 8 + (i % 6);
        return (
          <motion.span
            key={i}
            className="absolute rounded-full"
            style={{
              width: size,
              height: size,
              left: `${(i * 53) % 100}%`,
              top: `${(i * 37) % 100}%`,
              background:
                i % 2 === 0
                  ? "oklch(0.75 0.18 295 / 0.7)"
                  : "oklch(0.78 0.16 240 / 0.7)",
              boxShadow: "0 0 8px currentColor",
            }}
            animate={{ y: [0, -30, 0], opacity: [0.2, 0.9, 0.2] }}
            transition={{ duration, delay, repeat: Infinity, ease: "easeInOut" }}
          />
        );
      })}
    </div>
  );
}
