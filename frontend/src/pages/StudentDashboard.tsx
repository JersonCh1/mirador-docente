/**
 * StudentDashboard — vista de estudiante (MOCKEADO, UI real).
 *
 * Participación (participation_level, interventions, speaking_seconds),
 * recomendaciones y temas a repasar (review_topics). Datos del bloque
 * student_feedback del mock. Nota visible "Vista de demostración".
 */
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Hand,
  Clock,
  MessageCircle,
  Sparkles,
  BookOpen,
} from "lucide-react";
import type { Session } from "../types";
import { getSession } from "../api/client";
import { formatTime } from "../components/TimestampChip";
import Card from "../components/Card";
import Badge from "../components/Badge";
import MetricCard from "../components/MetricCard";

const LEVEL_LABEL: Record<string, string> = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
};

const LEVEL_TONE: Record<string, "warn" | "neutral" | "good"> = {
  low: "warn",
  medium: "neutral",
  high: "good",
};

export default function StudentDashboard() {
  const { id = "" } = useParams();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getSession(id)
      .then((s) => {
        if (active) setSession(s);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
        <p className="text-inkSoft">Cargando…</p>
      </div>
    );
  }

  const fb = session?.student_feedback;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <div className="mb-2 flex items-center gap-3">
        <h1 className="font-display text-3xl text-ink">Vista de estudiante</h1>
        <Badge tone="evidence">Vista de demostración</Badge>
      </div>
      <p className="mb-8 text-inkSoft">
        {session?.metadata.course} · {session?.metadata.teacher}
      </p>

      {!fb ? (
        <Card>
          <p className="text-inkSoft">
            Esta sesión no tiene retroalimentación de estudiante.
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-8">
          {/* Participación */}
          <section>
            <h2 className="mb-4 font-display text-2xl text-ink">
              Tu participación
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Card className="flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-inkSoft">
                  <Hand className="h-3.5 w-3.5" /> Nivel de participación
                </div>
                <Badge tone={LEVEL_TONE[fb.participation_level]}>
                  {LEVEL_LABEL[fb.participation_level] ??
                    fb.participation_level}
                </Badge>
              </Card>
              <MetricCard
                label="Intervenciones"
                value={fb.interventions}
                detail="Veces que participaste"
                icon={<MessageCircle className="h-3.5 w-3.5" />}
              />
              <MetricCard
                label="Tiempo hablando"
                value={formatTime(fb.speaking_seconds)}
                detail="Minutos:segundos"
                icon={<Clock className="h-3.5 w-3.5" />}
              />
            </div>
          </section>

          {/* Recomendaciones */}
          <section>
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-good" aria-hidden="true" />
              <h2 className="font-display text-2xl text-ink">
                Recomendaciones para ti
              </h2>
            </div>
            <div className="flex flex-col gap-4">
              {fb.recommendations.map((r, i) => (
                <Card key={i} className="flex flex-col gap-1">
                  <h3 className="font-semibold text-ink">{r.title}</h3>
                  <p className="text-sm text-inkSoft">{r.detail}</p>
                </Card>
              ))}
            </div>
          </section>

          {/* Temas a repasar */}
          <section>
            <div className="mb-4 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-ink" aria-hidden="true" />
              <h2 className="font-display text-2xl text-ink">
                Temas para repasar
              </h2>
            </div>
            <Card>
              <ul className="flex flex-col gap-2">
                {fb.review_topics.map((t, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 text-sm text-ink"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-evidence" />
                    {t}
                  </li>
                ))}
              </ul>
            </Card>
          </section>
        </div>
      )}

      <div className="mt-8">
        <Link
          to={`/session/${id}`}
          className="text-sm text-evidence underline"
        >
          Volver a la vista del docente
        </Link>
      </div>
    </div>
  );
}
