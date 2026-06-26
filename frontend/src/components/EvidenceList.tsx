/**
 * EvidenceList — lista de evidencias.
 *
 * Cada evidencia = TimestampChip + la quote (en cursiva/comillas, fuente body)
 * + comment si existe (inkSoft, más pequeño). Toda evidencia es clickeable y
 * hace seek.
 */
import type { Evidence } from "../types";
import TimestampChip from "./TimestampChip";

interface EvidenceListProps {
  evidence: Evidence[];
  onSeek?: (seconds: number) => void;
}

export default function EvidenceList({ evidence, onSeek }: EvidenceListProps) {
  if (evidence.length === 0) return null;

  return (
    <ul className="flex flex-col gap-3">
      {evidence.map((e, i) => (
        <li
          key={i}
          className="border-l-2 border-evidence/30 pl-3"
        >
          <div className="mb-1">
            <TimestampChip seconds={e.timestamp} onSeek={onSeek} />
          </div>
          <p className="font-body text-sm italic text-ink">
            &ldquo;{e.quote}&rdquo;
          </p>
          {e.comment && (
            <p className="mt-1 text-xs text-inkSoft">{e.comment}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
