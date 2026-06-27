/**
 * Tokens de diseño de Metrick — UN solo lugar.
 *
 * Dirección: instrumento analítico CÁLIDO, que se sienta como COACHING y
 * NO como vigilancia.
 *
 * REGLA DURA: el ámbar (`evidence`) es SOLO para anclas de evidencia /
 * timestamps. Nunca como color decorativo.
 */
export const tokens = {
  color: {
    paper: "#F7F8FA",
    ink: "#1B2A4A",
    inkSoft: "#41506E",
    evidence: "#E8843D", // ÁMBAR — SOLO evidencia/timestamps
    good: "#5C8A6B",
    warn: "#C2724B",
    line: "#E2E5EB",
    white: "#FFFFFF",
  },
  font: {
    display: "'Fraunces', serif",
    body: "'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  radius: { card: "14px", chip: "8px" },
} as const;

/** Colores sobrios por tipo de pista visual (para la TimelineRibbon). */
export const visualTypeColor: Record<string, string> = {
  slides: "#8FA3C4", // azul apagado
  whiteboard: "#A9B6A0", // verde-gris
  screen_share: "#C4A98F", // arena
  none: "#D6DAE2", // gris claro
};

export const visualTypeLabel: Record<string, string> = {
  slides: "Diapositivas",
  whiteboard: "Pizarra",
  screen_share: "Pantalla compartida",
  none: "Sin material visual",
};

/** Color de un score 1–4 según la convención de coaching. */
export function scoreColor(score: number | null): string {
  if (score === null || score === undefined) return tokens.color.inkSoft;
  if (score >= 3) return tokens.color.good;
  if (score >= 2) return tokens.color.ink;
  return tokens.color.warn;
}
