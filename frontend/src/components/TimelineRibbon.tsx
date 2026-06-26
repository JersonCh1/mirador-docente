/**
 * TimelineRibbon — LA FIRMA VISUAL.
 *
 * Cinta horizontal que representa toda la clase. Pinta segmentos por tipo
 * visual (slides / whiteboard / screen_share / none) con colores sobrios y
 * marca con puntos ÁMBAR los momentos con evidencia. Hover → tooltip con el
 * tipo y rango. Click en un punto de evidencia → onSeek.
 *
 * Si visual_timeline está vacío, muestra solo la barra base + puntos de
 * evidencia.
 */
import { useState } from "react";
import type { VisualSegment } from "../types";
import { formatTime } from "./TimestampChip";
import { visualTypeColor, visualTypeLabel } from "../theme/tokens";

interface TimelineRibbonProps {
  durationSeconds: number;
  visualTimeline: VisualSegment[];
  /** Segundos donde hay evidencia (puntos ámbar). */
  evidenceMarks: number[];
  onSeek?: (seconds: number) => void;
  /** Posición actual del reproductor (opcional) → cabezal. */
  currentTime?: number;
}

export default function TimelineRibbon({
  durationSeconds,
  visualTimeline,
  evidenceMarks,
  onSeek,
  currentTime,
}: TimelineRibbonProps) {
  const [hover, setHover] = useState<{ label: string; left: number } | null>(
    null,
  );

  const dur = durationSeconds > 0 ? durationSeconds : 1;
  const pct = (s: number) => `${Math.min(100, Math.max(0, (s / dur) * 100))}%`;

  // Marcas de evidencia únicas y ordenadas.
  const marks = Array.from(new Set(evidenceMarks)).sort((a, b) => a - b);

  return (
    <div className="w-full">
      <div className="relative">
        {/* Tooltip flotante */}
        {hover && (
          <div
            className="pointer-events-none absolute -top-9 z-10 -translate-x-1/2 whitespace-nowrap rounded-chip bg-ink px-2 py-1 text-xs text-white shadow-sm"
            style={{ left: `${hover.left}%` }}
          >
            {hover.label}
          </div>
        )}

        {/* Cinta base con segmentos de tipo visual */}
        <div className="relative h-7 w-full overflow-hidden rounded-chip border border-line bg-line/60">
          {visualTimeline.map((seg, i) => {
            const left = (seg.start / dur) * 100;
            const width = ((seg.end - seg.start) / dur) * 100;
            const center = left + width / 2;
            return (
              <div
                key={i}
                className="absolute top-0 h-full cursor-default"
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  backgroundColor: visualTypeColor[seg.type] ?? "#D6DAE2",
                }}
                onMouseEnter={() =>
                  setHover({
                    label: `${visualTypeLabel[seg.type] ?? seg.type} · ${formatTime(seg.start)}–${formatTime(seg.end)}`,
                    left: center,
                  })
                }
                onMouseLeave={() => setHover(null)}
              />
            );
          })}

          {/* Cabezal de reproducción */}
          {typeof currentTime === "number" && (
            <div
              className="absolute top-0 h-full w-0.5 bg-ink"
              style={{ left: pct(currentTime) }}
              aria-hidden="true"
            />
          )}
        </div>

        {/* Puntos de evidencia (ámbar), por encima de la cinta */}
        <div className="relative h-0">
          {marks.map((t, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onSeek?.(t)}
              onMouseEnter={() =>
                setHover({
                  label: `Evidencia · ${formatTime(t)}`,
                  left: (t / dur) * 100,
                })
              }
              onMouseLeave={() => setHover(null)}
              aria-label={`Evidencia en ${formatTime(t)}. Ir a ese momento.`}
              title={`Evidencia · ${formatTime(t)}`}
              className="absolute -top-[26px] -translate-x-1/2"
              style={{ left: pct(t) }}
            >
              <span className="block h-3 w-3 rounded-full border-2 border-white bg-evidence shadow-sm transition-transform hover:scale-125" />
            </button>
          ))}
        </div>
      </div>

      {/* Leyenda */}
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-inkSoft">
        {(["slides", "whiteboard", "screen_share", "none"] as const).map((t) => (
          <span key={t} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: visualTypeColor[t] }}
            />
            {visualTypeLabel[t]}
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-evidence" />
          Evidencia
        </span>
      </div>
    </div>
  );
}
