import React, { createContext, useContext, useEffect, useState } from "react";
import { Moon, Sun, Laptop, Check } from "lucide-react";

export type Theme = "dark" | "light" | "system";

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: "dark" | "light";
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = "researchx-theme";

function getSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "dark";
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as Theme | null;
      if (saved && (saved === "dark" || saved === "light" || saved === "system")) {
        return saved;
      }
    } catch (e) {
      console.warn("Could not read theme from localStorage", e);
    }
    return "dark"; // Default theme
  });

  const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light">(() => {
    if (typeof window === "undefined") return "dark";
    if (theme === "system") return getSystemTheme();
    return theme;
  });

  // Apply theme to DOM and persist
  useEffect(() => {
    const root = document.documentElement;
    const currentResolved = theme === "system" ? getSystemTheme() : theme;
    setResolvedTheme(currentResolved);

    // Apply a temporary class for smooth transitions on manual theme change
    root.classList.add("theme-transition");
    const timeout = setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 300);

    if (currentResolved === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
    }

    root.setAttribute("data-theme", currentResolved);
    root.style.colorScheme = currentResolved;

    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      console.warn("Could not save theme to localStorage", e);
    }

    return () => clearTimeout(timeout);
  }, [theme]);

  // Listen for OS color scheme changes when theme === "system"
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = () => {
      if (theme === "system") {
        const newResolved = mediaQuery.matches ? "dark" : "light";
        setResolvedTheme(newResolved);
        const root = document.documentElement;
        if (newResolved === "dark") {
          root.classList.add("dark");
          root.classList.remove("light");
        } else {
          root.classList.add("light");
          root.classList.remove("dark");
        }
        root.setAttribute("data-theme", newResolved);
        root.style.colorScheme = newResolved;
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

/**
 * Compact, polished Theme Toggle button for the top navigation bar.
 */
export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-border/50 bg-secondary/30 text-muted-foreground hover:bg-secondary/70 hover:text-foreground transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary/40 shadow-xs"
        title={`Current theme: ${theme} (${resolvedTheme})`}
        aria-label="Toggle theme"
      >
        {resolvedTheme === "dark" ? (
          <Moon className="h-4 w-4 text-purple-400 transition-transform duration-200 rotate-0" />
        ) : (
          <Sun className="h-4 w-4 text-amber-500 transition-transform duration-200 rotate-0" />
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-36 rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70 border-b border-border/40 mb-1">
            Appearance
          </div>

          <button
            type="button"
            onClick={() => {
              setTheme("light");
              setOpen(false);
            }}
            className={`flex w-full items-center justify-between gap-2 rounded-xl px-2.5 py-1.5 text-xs font-medium transition-colors ${
              theme === "light"
                ? "bg-primary/15 text-primary font-semibold"
                : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
            }`}
          >
            <div className="flex items-center gap-2">
              <Sun className="h-3.5 w-3.5 text-amber-500" />
              <span>Light</span>
            </div>
            {theme === "light" && <Check className="h-3 w-3 text-primary" />}
          </button>

          <button
            type="button"
            onClick={() => {
              setTheme("dark");
              setOpen(false);
            }}
            className={`flex w-full items-center justify-between gap-2 rounded-xl px-2.5 py-1.5 text-xs font-medium transition-colors ${
              theme === "dark"
                ? "bg-primary/15 text-primary font-semibold"
                : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
            }`}
          >
            <div className="flex items-center gap-2">
              <Moon className="h-3.5 w-3.5 text-purple-400" />
              <span>Dark</span>
            </div>
            {theme === "dark" && <Check className="h-3 w-3 text-primary" />}
          </button>

          <button
            type="button"
            onClick={() => {
              setTheme("system");
              setOpen(false);
            }}
            className={`flex w-full items-center justify-between gap-2 rounded-xl px-2.5 py-1.5 text-xs font-medium transition-colors ${
              theme === "system"
                ? "bg-primary/15 text-primary font-semibold"
                : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
            }`}
          >
            <div className="flex items-center gap-2">
              <Laptop className="h-3.5 w-3.5 text-blue-400" />
              <span>System</span>
            </div>
            {theme === "system" && <Check className="h-3 w-3 text-primary" />}
          </button>
        </div>
      )}
    </div>
  );
}
