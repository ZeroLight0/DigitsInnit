import { motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, ImageIcon, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface Props {
  onAnalyze: (file: File) => void;
}

const ACCEPTED = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

export function ImageUploader({ onAnalyze }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File | null) => {
    if (!f) return;
    if (!ACCEPTED.includes(f.type)) {
      toast.error("Unsupported file type. Use PNG, JPG, or WEBP.");
      return;
    }
    setFile(f);
    const url = URL.createObjectURL(f);
    setPreview(url);
  }, []);

  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const item = Array.from(e.clipboardData?.items || []).find((i) => i.type.startsWith("image/"));
      if (item) {
        const f = item.getAsFile();
        if (f) handleFile(f);
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [handleFile]);

  const formatBytes = (b: number) => {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / 1024 / 1024).toFixed(2)} MB`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="w-full max-w-2xl mx-auto"
    >
      {!preview ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFile(e.dataTransfer.files?.[0] || null);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
          className={`cursor-pointer rounded-3xl border-2 border-dashed transition-all p-12 sm:p-16 text-center bg-card ${
            dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/60 hover:bg-surface"
          }`}
        >
          <div className="w-16 h-16 mx-auto rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-5">
            <Upload className="w-8 h-8" strokeWidth={1.75} />
          </div>
          <h3 className="text-xl font-semibold">Drop your image here</h3>
          <p className="mt-2 text-muted-foreground text-[15px]">
            or click to browse · paste from clipboard supported
          </p>
          <p className="mt-4 text-xs text-muted-foreground">PNG, JPG, WEBP</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] || null)}
          />
        </div>
      ) : (
        <div className="rounded-3xl bg-card border border-border/70 shadow-[var(--shadow-soft)] p-5 sm:p-6">
          <div className="rounded-2xl overflow-hidden bg-surface border border-border/60 aspect-square max-h-[420px] flex items-center justify-center">
            <img src={preview} alt="Preview" className="max-w-full max-h-full object-contain" />
          </div>
          <div className="mt-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center text-muted-foreground shrink-0">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">{file?.name}</p>
              <p className="text-xs text-muted-foreground">{file && formatBytes(file.size)}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="rounded-xl"
              onClick={() => {
                setFile(null);
                setPreview(null);
              }}
            >
              <RefreshCw className="w-4 h-4 mr-1.5" />
              Replace
            </Button>
          </div>
          <Button
            size="lg"
            className="w-full mt-5 rounded-xl h-12 text-base"
            onClick={() => file && onAnalyze(file)}
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Analyze
          </Button>
        </div>
      )}
    </motion.div>
  );
}
