/**
 * TimestampChip — el ancla de evidencia.
 *
 * Chip monoespaciado, ámbar, con ícono ▸ y formato mm:ss ("▸ 23:14").
 * Clickeable y accesible (button con foco visible). Al activarse hace seek.
 */

/** Formatea segundos a "mm:ss" (o "h:mm:ss" si pasa de una hora). */
export function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  if (h > 0) return `${h}:${pad(m)}:${pad(s)}`;
  return `${pad(m)}:${pad(s)}`;
}

interface TimestampChipProps {
  seconds: number;
  onSeek?: (seconds: number) => void;
  className?: string;
}

export default function TimestampChip({
  seconds,
  onSeek,
  className = "",
}: TimestampChipProps) {
  return (
    <button
      type="button"
      onClick={() => onSeek?.(seconds)}
      title={`Ir a ${formatTime(seconds)} en la grabación`}
      aria-label={`Ir al minuto ${formatTime(seconds)} de la grabación`}
      className={`inline-flex items-center gap-1 rounded-chip border border-evidence/40 bg-evidence/10 px-2 py-0.5 font-mono text-xs font-medium text-evidence transition-colors hover:bg-evidence hover:text-white ${className}`}
    >
      <span aria-hidden="true">▸</span>
      {formatTime(seconds)}
    </button>
  );
}
