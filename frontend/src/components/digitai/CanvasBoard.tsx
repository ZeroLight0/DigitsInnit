import { motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Undo2, Redo2, Eraser, Trash2, Sparkles, Pencil } from "lucide-react";
import { toast } from "sonner";

interface Props {
  onAnalyze: (dataUrl: string) => void;
}

type Stroke = {
  points: { x: number; y: number }[];
  size: number;
  erase: boolean;
};

export function CanvasBoard({ onAnalyze }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [redoStack, setRedoStack] = useState<Stroke[]>([]);
  const [brush, setBrush] = useState(18);
  const [erasing, setErasing] = useState(false);
  const drawing = useRef(false);
  const current = useRef<Stroke | null>(null);

  const redraw = useCallback(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const all = current.current ? [...strokes, current.current] : strokes;
    for (const s of all) {
      ctx.strokeStyle = s.erase ? "#ffffff" : "#0f172a";
      ctx.lineWidth = s.size;
      ctx.beginPath();
      s.points.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      });
      ctx.stroke();
    }
  }, [strokes]);

  // resize canvas to container
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const resize = () => {
      const parent = c.parentElement;
      if (!parent) return;
      const size = Math.min(parent.clientWidth, 520);
      const dpr = window.devicePixelRatio || 1;
      c.width = size * dpr;
      c.height = size * dpr;
      c.style.width = `${size}px`;
      c.style.height = `${size}px`;
      const ctx = c.getContext("2d");
      ctx?.scale(dpr, dpr);
      redraw();
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [redraw]);

  useEffect(() => {
    redraw();
  }, [redraw]);

  const getPos = (e: React.PointerEvent) => {
    const c = canvasRef.current!;
    const rect = c.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const startStroke = (e: React.PointerEvent) => {
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    drawing.current = true;
    current.current = { points: [getPos(e)], size: brush, erase: erasing };
    redraw();
  };
  const moveStroke = (e: React.PointerEvent) => {
    if (!drawing.current || !current.current) return;
    current.current.points.push(getPos(e));
    redraw();
  };
  const endStroke = () => {
    if (!drawing.current || !current.current) return;
    drawing.current = false;
    setStrokes((s) => [...s, current.current!]);
    setRedoStack([]);
    current.current = null;
  };

  const undo = () => {
    setStrokes((s) => {
      if (s.length === 0) return s;
      const next = s.slice(0, -1);
      setRedoStack((r) => [...r, s[s.length - 1]]);
      return next;
    });
  };
  const redo = () => {
    setRedoStack((r) => {
      if (r.length === 0) return r;
      const last = r[r.length - 1];
      setStrokes((s) => [...s, last]);
      return r.slice(0, -1);
    });
  };
  const clear = () => {
    setStrokes([]);
    setRedoStack([]);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if (e.key === "Delete") {
        clear();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const analyze = () => {
    if (strokes.length === 0) {
      toast.error("Draw a digit before analyzing.");
      return;
    }
    const c = canvasRef.current!;
    onAnalyze(c.toDataURL("image/png"));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className="bg-card rounded-3xl border border-border/70 shadow-[var(--shadow-soft)] p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <Button variant="outline" size="sm" className="rounded-xl" onClick={undo} aria-label="Undo">
            <Undo2 className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" className="rounded-xl" onClick={redo} aria-label="Redo">
            <Redo2 className="w-4 h-4" />
          </Button>
          <Button
            variant={erasing ? "default" : "outline"}
            size="sm"
            className="rounded-xl"
            onClick={() => setErasing((v) => !v)}
            aria-label="Toggle eraser"
          >
            {erasing ? <Eraser className="w-4 h-4" /> : <Pencil className="w-4 h-4" />}
          </Button>
          <Button variant="outline" size="sm" className="rounded-xl" onClick={clear} aria-label="Clear">
            <Trash2 className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3 ml-auto min-w-[160px] flex-1 max-w-[220px]">
            <span className="text-xs text-muted-foreground shrink-0">Brush</span>
            <Slider
              value={[brush]}
              min={4}
              max={48}
              step={1}
              onValueChange={(v) => setBrush(v[0])}
              aria-label="Brush size"
            />
          </div>
        </div>

        <div className="flex justify-center">
          <canvas
            ref={canvasRef}
            onPointerDown={startStroke}
            onPointerMove={moveStroke}
            onPointerUp={endStroke}
            onPointerLeave={endStroke}
            className="rounded-2xl border border-border bg-white touch-none cursor-crosshair"
            aria-label="Drawing canvas"
          />
        </div>

        <Button size="lg" className="w-full mt-5 rounded-xl h-12 text-base" onClick={analyze}>
          <Sparkles className="w-4 h-4 mr-2" />
          Analyze
        </Button>
      </div>
    </motion.div>
  );
}
