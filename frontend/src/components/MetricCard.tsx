/**
 * MetricCard — tarjeta genérica para una métrica dura.
 * label + valor grande mono + sub-detalle opcional.
 */
import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  icon?: ReactNode;
}

export default function MetricCard({
  label,
  value,
  detail,
  icon,
}: MetricCardProps) {
  return (
    <div className="card-mirador flex flex-col gap-1 p-4">
      <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-inkSoft">
        {icon}
        {label}
      </div>
      <div className="font-mono text-2xl font-semibold text-ink">{value}</div>
      {detail && <div className="text-xs text-inkSoft">{detail}</div>}
    </div>
  );
}
