import { motion, AnimatePresence } from "motion/react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Sparkles, PencilLine, Upload, Cpu, CheckCircle2, ArrowRight } from "lucide-react";
import { useState } from "react";

interface OnboardingProps {
  open: boolean;
  onClose: () => void;
}

export function Onboarding({ open, onClose }: OnboardingProps) {
  const [step, setStep] = useState(0);

  const close = () => {
    setStep(0);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && close()}>
      <DialogContent className="sm:max-w-[560px] rounded-3xl border-border/60 shadow-[var(--shadow-elevated)] p-0 overflow-hidden">
        <AnimatePresence mode="wait">
          {step === 0 ? (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="p-8 sm:p-10"
            >
              <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 text-primary mb-6">
                <Sparkles className="w-7 h-7" />
              </div>
              <DialogHeader className="text-left space-y-3">
                <DialogTitle className="text-3xl font-semibold tracking-tight">
                  Welcome to DigitAI
                </DialogTitle>
                <DialogDescription className="text-base leading-relaxed text-muted-foreground">
                  DigitAI uses a neural network trained on thousands of handwritten samples
                  to recognize numbers from <span className="text-foreground font-medium">0 to 9</span>.
                  Draw a digit or upload an image — the model does the rest.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="mt-8 sm:justify-end">
                <Button size="lg" className="rounded-xl px-6" onClick={() => setStep(1)}>
                  Continue
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </DialogFooter>
            </motion.div>
          ) : (
            <motion.div
              key="how"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="p-8 sm:p-10"
            >
              <DialogHeader className="text-left space-y-2 mb-6">
                <DialogTitle className="text-3xl font-semibold tracking-tight">
                  How It Works
                </DialogTitle>
                <DialogDescription className="text-base text-muted-foreground">
                  A quick look at the pipeline behind every prediction.
                </DialogDescription>
              </DialogHeader>

              <div className="grid grid-cols-4 gap-2 mb-6">
                {[
                  { icon: PencilLine, label: "Draw or Upload" },
                  { icon: Upload, label: "Processing" },
                  { icon: Cpu, label: "AI Model" },
                  { icon: CheckCircle2, label: "Prediction" },
                ].map((s, i) => (
                  <motion.div
                    key={s.label}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 * i }}
                    className="flex flex-col items-center text-center"
                  >
                    <div className="w-11 h-11 rounded-xl bg-secondary flex items-center justify-center text-primary">
                      <s.icon className="w-5 h-5" />
                    </div>
                    <span className="mt-2 text-[11px] sm:text-xs font-medium text-muted-foreground">
                      {s.label}
                    </span>
                  </motion.div>
                ))}
              </div>

              <ul className="space-y-2 text-sm text-muted-foreground bg-surface rounded-2xl p-5 border border-border/60">
                <li>• Draw only <span className="text-foreground font-medium">one</span> digit.</li>
                <li>• Keep the digit centered.</li>
                <li>• Use a clear, high-contrast image.</li>
                <li>• Avoid extra markings or noise.</li>
              </ul>

              <DialogFooter className="mt-8 flex flex-row sm:justify-between gap-3">
                <Button variant="ghost" size="lg" className="rounded-xl" onClick={() => setStep(0)}>
                  Back
                </Button>
                <Button size="lg" className="rounded-xl px-6" onClick={close}>
                  Start Exploring
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </DialogFooter>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
