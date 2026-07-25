import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { Cpu } from "lucide-react";

const STAGES = [
  "Preparing image…",
  "Processing…",
  "Running AI model…",
  "Generating prediction…",
];

export function PredictionLoader() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStage((s) => (s + 1) % STAGES.length), 450);
    return () => clearInterval(id);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-md mx-auto bg-card rounded-3xl border border-border/70 shadow-[var(--shadow-elevated)] p-10 text-center"
      role="status"
      aria-live="polite"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
        className="w-16 h-16 mx-auto rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-6"
      >
        <Cpu className="w-8 h-8" />
      </motion.div>

      <motion.p
        key={stage}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-base font-medium text-foreground"
      >
        {STAGES[stage]}
      </motion.p>
      <p className="text-xs text-muted-foreground mt-1">Estimated 1–2 seconds</p>

      <div className="mt-6 h-1.5 rounded-full bg-secondary overflow-hidden">
        <motion.div
          className="h-full bg-primary rounded-full"
          initial={{ width: "10%" }}
          animate={{ width: ["10%", "70%", "95%"] }}
          transition={{ duration: 1.6, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );
}
