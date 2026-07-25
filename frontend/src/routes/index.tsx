import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Sparkles, HelpCircle, ArrowLeft } from "lucide-react";
import { Toaster, toast } from "sonner";

import { Onboarding } from "@/components/digitai/Onboarding";
import { InputMethodSelector } from "@/components/digitai/InputMethodSelector";
import { ImageUploader } from "@/components/digitai/ImageUploader";
import { CanvasBoard } from "@/components/digitai/CanvasBoard";
import { PredictionLoader } from "@/components/digitai/PredictionLoader";
import { PredictionResult } from "@/components/digitai/PredictionResult";
import { Footer } from "@/components/digitai/Footer";
import { Button } from "@/components/ui/button";
import { predictFromDrawing, predictFromImage, type PredictionResponse } from "@/lib/predict-api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DigitAI — Handwritten Number Recognition" },
      { name: "description", content: "Upload or draw a handwritten digit and let DigitAI predict it using machine learning." },
      { property: "og:title", content: "DigitAI — Handwritten Number Recognition" },
      { property: "og:description", content: "An elegant AI demo that recognizes handwritten digits 0–9." },
    ],
  }),
  component: Index,
});

type Mode = "select" | "upload" | "draw";
type Phase = "idle" | "loading" | "result";

const LAST_MODE_KEY = "digitai:last-mode";

function Index() {
  const [onboardOpen, setOnboardOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("select");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<PredictionResponse | null>(null);

  useEffect(() => {
    const seen = typeof window !== "undefined" && window.sessionStorage.getItem("digitai:onboarded");
    if (!seen) setOnboardOpen(true);
    const last = typeof window !== "undefined" && window.sessionStorage.getItem(LAST_MODE_KEY);
    if (last === "upload" || last === "draw") setMode(last);
  }, []);

  const closeOnboarding = () => {
    setOnboardOpen(false);
    try { window.sessionStorage.setItem("digitai:onboarded", "1"); } catch {}
  };

  const pickMode = (m: "upload" | "draw") => {
    setMode(m);
    try { window.sessionStorage.setItem(LAST_MODE_KEY, m); } catch {}
  };

  const runPrediction = async (fn: () => Promise<PredictionResponse>) => {
    setPhase("loading");
    setResult(null);
    try {
      const res = await fn();
      setResult(res);
      setPhase("result");
    } catch {
      setPhase("idle");
      toast.error("Something went wrong. Please try again.");
    }
  };

  const reset = () => {
    setPhase("idle");
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Toaster position="top-center" richColors />
      <Onboarding open={onboardOpen} onClose={closeOnboarding} />

      <header className="max-w-6xl w-full mx-auto px-6 pt-7 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-foreground text-background flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-semibold tracking-tight text-[17px]">DigitAI</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="rounded-xl text-muted-foreground hover:text-foreground"
          onClick={() => setOnboardOpen(true)}
        >
          <HelpCircle className="w-4 h-4 mr-1.5" />
          How the AI works
        </Button>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 pt-16 sm:pt-24">
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="text-center max-w-3xl mx-auto"
        >
          <div className="inline-flex items-center gap-1.5 text-xs font-medium text-primary bg-primary/10 px-3 py-1.5 rounded-full mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Powered by AI
          </div>
          <h1 className="text-[40px] sm:text-[56px] leading-[1.05] font-bold tracking-tight text-gradient-primary">
            AI Handwritten Digit Recognition
          </h1>
          <p className="mt-5 text-lg text-muted-foreground max-w-xl mx-auto">
            Upload or draw a handwritten number and let the AI predict which digit it is.
          </p>
        </motion.section>

        <section className="mt-14 sm:mt-20 pb-16">
          <AnimatePresence mode="wait">
            {phase === "loading" && (
              <motion.div key="loader" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <PredictionLoader />
              </motion.div>
            )}

            {phase === "result" && result && (
              <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <PredictionResult
                  result={result}
                  onAgain={reset}
                  onSwitch={() => {
                    reset();
                    setMode("select");
                  }}
                />
              </motion.div>
            )}

            {phase === "idle" && mode === "select" && (
              <motion.div key="select" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <InputMethodSelector onSelect={pickMode} />
              </motion.div>
            )}

            {phase === "idle" && mode === "upload" && (
              <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <ModeShell title="Upload an image" onBack={() => setMode("select")}>
                  <ImageUploader onAnalyze={(f) => runPrediction(() => predictFromImage(f))} />
                </ModeShell>
              </motion.div>
            )}

            {phase === "idle" && mode === "draw" && (
              <motion.div key="draw" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <ModeShell title="Draw a digit" onBack={() => setMode("select")}>
                  <CanvasBoard onAnalyze={(d) => runPrediction(() => predictFromDrawing(d))} />
                </ModeShell>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </main>

      <Footer />
    </div>
  );
}

function ModeShell({ title, onBack, children }: { title: string; onBack: () => void; children: React.ReactNode }) {
  return (
    <div>
      <div className="max-w-2xl mx-auto mb-5 flex items-center justify-between">
        <Button variant="ghost" size="sm" className="rounded-xl text-muted-foreground" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back
        </Button>
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div className="w-[68px]" />
      </div>
      {children}
    </div>
  );
}
