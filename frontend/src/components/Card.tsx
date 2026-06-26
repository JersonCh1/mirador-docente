import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  /** Atenúa la tarjeta (p. ej. dimensión no observable). */
  muted?: boolean;
}

/** Primitivo de tarjeta: fondo blanco, borde sutil, radio de tarjeta. */
export default function Card({ children, className = "", muted = false }: CardProps) {
  return (
    <div
      className={`card-mirador p-5 ${muted ? "opacity-55" : ""} ${className}`}
    >
      {children}
    </div>
  );
}
