import { motion } from "motion/react";
import { ImageIcon, PencilLine, ArrowRight } from "lucide-react";

interface Props {
  onSelect: (mode: "upload" | "draw") => void;
}

export function InputMethodSelector({ onSelect }: Props) {
  const cards = [
    {
      id: "upload" as const,
      icon: ImageIcon,
      title: "Upload Image",
      description: "Upload a picture containing one handwritten digit.",
      cta: "Choose Image",
    },
    {
      id: "draw" as const,
      icon: PencilLine,
      title: "Draw Digit",
      description: "Draw a handwritten digit directly on the canvas.",
      cta: "Start Drawing",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5 w-full max-w-3xl mx-auto">
      {cards.map((c, i) => (
        <motion.button
          key={c.id}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.08, duration: 0.4, ease: "easeOut" }}
          whileHover={{ y: -4 }}
          whileTap={{ scale: 0.99 }}
          onClick={() => onSelect(c.id)}
          className="group text-left p-7 bg-card rounded-3xl border border-border/70 shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-elevated)] transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <div className="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-5 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
            <c.icon className="w-7 h-7" strokeWidth={1.75} />
          </div>
          <h3 className="text-xl font-semibold text-foreground">{c.title}</h3>
          <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">{c.description}</p>
          <div className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-primary">
            {c.cta}
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
          </div>
        </motion.button>
      ))}
    </div>
  );
}
