import type { ReactNode } from "react";

type Tone = "neutral" | "good" | "warn" | "ink" | "evidence";

interface BadgeProps {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}

const toneClasses: Record<Tone, string> = {
  neutral: "bg-paper text-inkSoft border-line",
  good: "bg-good/10 text-good border-good/30",
  warn: "bg-warn/10 text-warn border-warn/30",
  ink: "bg-ink/5 text-ink border-ink/20",
  evidence: "bg-evidence/10 text-evidence border-evidence/30",
};

/** Etiqueta pequeña reutilizable. */
export default function Badge({ children, tone = "neutral", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-chip border px-2 py-0.5 text-xs font-medium ${toneClasses[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
