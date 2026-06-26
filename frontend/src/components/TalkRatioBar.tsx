/**
 * TalkRatioBar — barra horizontal apilada docente vs estudiantes (%).
 * Docente en ink, estudiantes en good. Con leyenda.
 */
import { tokens } from "../theme/tokens";

interface TalkRatioBarProps {
  teacher: number; // 0–1
  students: number; // 0–1
}

export default function TalkRatioBar({ teacher, students }: TalkRatioBarProps) {
  const t = Math.round(teacher * 100);
  const s = Math.round(students * 100);

  return (
    <div className="w-full">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-ink">
          Distribución de la palabra
        </h3>
      </div>
      <div
        className="flex h-6 w-full overflow-hidden rounded-chip border border-line"
        role="img"
        aria-label={`Docente ${t} por ciento, estudiantes ${s} por ciento`}
      >
        <div
          className="flex items-center justify-start pl-2"
          style={{ width: `${t}%`, backgroundColor: tokens.color.ink }}
        >
          <span className="text-xs font-medium text-white">{t}%</span>
        </div>
        <div
          className="flex items-center justify-end pr-2"
          style={{ width: `${s}%`, backgroundColor: tokens.color.good }}
        >
          <span className="text-xs font-medium text-white">{s}%</span>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-4 text-xs text-inkSoft">
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-sm"
            style={{ backgroundColor: tokens.color.ink }}
          />
          Docente
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-sm"
            style={{ backgroundColor: tokens.color.good }}
          />
          Estudiantes
        </span>
      </div>
    </div>
  );
}
