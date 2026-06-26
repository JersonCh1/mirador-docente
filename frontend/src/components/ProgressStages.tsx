/**
 * ProgressStages — avance del pipeline.
 *
 * Etapas: uploaded → transcribing → analyzing → validating → ready.
 * Resalta la etapa actual y muestra la barra de progress %.
 */
import { Check } from "lucide-react";
import type { Status } from "../types";

interface ProgressStagesProps {
  status: Status;
  progress: number;
}

const STAGES: { id: Status; label: string }[] = [
  { id: "uploaded", label: "Subida" },
  { id: "transcribing", label: "Transcribiendo" },
  { id: "analyzing", label: "Analizando" },
  { id: "validating", label: "Validando" },
  { id: "ready", label: "Lista" },
];

export default function ProgressStages({
  status,
  progress,
}: ProgressStagesProps) {
  const failed = status === "failed";
  const currentIndex = STAGES.findIndex((s) => s.id === status);
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;

  return (
    <div className="w-full">
      <ol className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-0">
        {STAGES.map((stage, i) => {
          const done = i < activeIndex || status === "ready";
          const active = i === activeIndex && status !== "ready";
          return (
            <li
              key={stage.id}
              className="flex items-center gap-3 sm:flex-1"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold transition-colors ${
                    done
                      ? "border-good bg-good text-white"
                      : active
                        ? "border-evidence bg-evidence text-white"
                        : "border-line bg-white text-inkSoft"
                  }`}
                  aria-hidden="true"
                >
                  {done ? <Check className="h-4 w-4" /> : i + 1}
                </span>
                <span
                  className={`text-sm ${active ? "font-semibold text-ink" : "text-inkSoft"}`}
                >
                  {stage.label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <span className="hidden h-px flex-1 bg-line sm:block" />
              )}
            </li>
          );
        })}
      </ol>

      <div className="mt-5">
        <div className="h-2 w-full overflow-hidden rounded-full bg-line">
          <div
            className={`h-full transition-all ${failed ? "bg-warn" : "bg-evidence"}`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
        <p className="mt-2 font-mono text-xs text-inkSoft">
          {failed ? "Falló el procesamiento" : `${Math.round(progress)}%`}
        </p>
      </div>
    </div>
  );
}
