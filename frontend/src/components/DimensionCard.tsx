/**
 * DimensionCard — tarjeta por dimensión.
 *
 * nombre + score 1–4 (como "3/4" + puntos) + resumen + EvidenceList con las
 * citas. Si observable=false: tarjeta ATENUADA, sin score, con la etiqueta
 * "No evaluable desde esta grabación".
 */
import type { Dimension } from "../types";
import Card from "./Card";
import Badge from "./Badge";
import EvidenceList from "./EvidenceList";
import { scoreColor } from "../theme/tokens";

interface DimensionCardProps {
  dimension: Dimension;
  onSeek?: (seconds: number) => void;
}

/** Puntos rellenos según el score (de max_score). */
function ScoreDots({ score, max }: { score: number; max: number }) {
  const color = scoreColor(score);
  return (
    <span
      className="inline-flex items-center gap-1"
      aria-hidden="true"
    >
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className="h-2.5 w-2.5 rounded-full"
          style={{
            backgroundColor: i < score ? color : "#E2E5EB",
          }}
        />
      ))}
    </span>
  );
}

export default function DimensionCard({
  dimension,
  onSeek,
}: DimensionCardProps) {
  const { observable, score, max_score, name, summary, evidence } = dimension;
  const color = scoreColor(score);

  return (
    <Card muted={!observable} className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-base font-semibold leading-snug text-ink">
          {name}
        </h4>
        {observable && score !== null ? (
          <span
            className="shrink-0 font-mono text-lg font-semibold"
            style={{ color }}
            aria-label={`Puntaje ${score} de ${max_score}`}
          >
            {score}/{max_score}
          </span>
        ) : (
          <Badge tone="neutral" className="shrink-0">
            No evaluable
          </Badge>
        )}
      </div>

      {observable && score !== null && (
        <ScoreDots score={score} max={max_score} />
      )}

      <p className="text-sm text-inkSoft">
        {observable
          ? summary
          : "No evaluable desde esta grabación."}
      </p>

      {observable && evidence.length > 0 && (
        <div className="mt-1">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-inkSoft">
            Evidencia
          </p>
          <EvidenceList evidence={evidence} onSeek={onSeek} />
        </div>
      )}
    </Card>
  );
}
