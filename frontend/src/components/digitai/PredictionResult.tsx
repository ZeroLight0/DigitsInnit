import { motion } from "motion/react";
import { CheckCircle2, RotateCcw, Shuffle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PredictionResponse } from "@/lib/predict-api";

interface Props {
  result: PredictionResponse;
  onAgain: () => void;
  onSwitch: () => void;
}

export function PredictionResult({ result, onAgain, onSwitch }: Props) {
  const { prediction, confidence } = result;
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - confidence / 100);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="w-full max-w-md mx-auto bg-card rounded-3xl border border-border/70 shadow-[var(--shadow-elevated)] p-8 sm:p-10 text-center"
    >
      <div className="inline-flex items-center gap-1.5 text-xs font-medium text-success bg-success/10 px-3 py-1.5 rounded-full mb-6">
        <CheckCircle2 className="w-3.5 h-3.5" />
        Prediction successful
      </div>

      <div className="relative w-[140px] h-[140px] mx-auto">
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r={radius} stroke="var(--color-secondary)" strokeWidth="10" fill="none" />
          <motion.circle
            cx="70"
            cy="70"
            r={radius}
            stroke="var(--color-primary)"
            strokeWidth="10"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 220, damping: 18 }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <span className="text-[68px] font-bold leading-none text-gradient-primary">
            {prediction}
          </span>
        </motion.div>
      </div>

      <p className="mt-6 text-xs uppercase tracking-wider text-muted-foreground font-medium">
        Prediction Confidence
      </p>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-2xl font-semibold mt-1"
      >
        {confidence.toFixed(2)}%
      </motion.p>

      <div className="mt-8 flex flex-col sm:flex-row gap-2.5">
        <Button size="lg" className="rounded-xl flex-1 h-11" onClick={onAgain}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Analyze Another
        </Button>
        <Button variant="outline" size="lg" className="rounded-xl flex-1 h-11" onClick={onSwitch}>
          <Shuffle className="w-4 h-4 mr-2" />
          Switch Method
        </Button>
      </div>
    </motion.div>
  );
}
