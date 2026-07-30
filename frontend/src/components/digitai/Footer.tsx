import { Github, BookOpen } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border/60 mt-16">
      <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-semibold tracking-tight">DigitAI</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Built to demonstrate handwritten digit recognition using machine learning.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="https://github.com/ZeroLight0/DigitsInnit"
            aria-label="GitHub"
            className="w-9 h-9 rounded-xl bg-surface border border-border/60 flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-border transition-colors"
          >
            <Github className="w-4 h-4" />
          </a>
          <a
            href="#"
            aria-label="Documentation"
            className="w-9 h-9 rounded-xl bg-surface border border-border/60 flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-border transition-colors"
          >
            <BookOpen className="w-4 h-4" />
          </a>
        </div>
      </div>
    </footer>
  );
}
