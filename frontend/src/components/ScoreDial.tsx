/**
 * ScoreDial — dial/gauge circular (SVG) que muestra overall_score sobre el
 * máximo (ej. "3.0/4"). Color según valor: good si >=3, ink si 2–3, warn si <2.
 */
import { scoreColor } from "../theme/tokens";

interface ScoreDialProps {
  score: number | null;
  maxScore?: number;
  label: string;
}

export default function ScoreDial({
  score,
  maxScore = 4,
  label,
}: ScoreDialProps) {
  const size = 132;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const value = score ?? 0;
  const fraction = maxScore > 0 ? Math.min(1, value / maxScore) : 0;
  const dash = circ * fraction;
  const color = scoreColor(score);
  const hasScore = score !== null && score !== undefined;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={`${label}: ${hasScore ? `${value} de ${maxScore}` : "no disponible"}`}
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="#E2E5EB"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-display text-3xl leading-none"
            style={{ color }}
          >
            {hasScore ? value.toFixed(1) : "—"}
          </span>
          <span className="mt-0.5 font-mono text-xs text-inkSoft">
            / {maxScore}
          </span>
        </div>
      </div>
      <span className="max-w-[14rem] text-center text-sm font-medium text-inkSoft">
        {label}
      </span>
    </div>
  );
}
