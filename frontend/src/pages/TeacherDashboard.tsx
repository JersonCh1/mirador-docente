/**
 * TeacherDashboard — LA REBANADA FUNCIONAL, la pieza estrella.
 *
 * Header (curso/docente/fecha + TimelineRibbon + Player), dos ScoreDial
 * (MINEDU y TALIS), TalkRatioBar + MetricCard, secciones por framework con sus
 * DimensionCard, fortalezas y mejoras, alineación a objetivos, y la evolución
 * del docente contra su propia línea base.
 *
 * Todos los TimestampChip hacen seek en el Player.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Gauge,
  MessageCircleQuestion,
  Timer,
  MessageSquareDashed,
  TrendingUp,
  ArrowUpRight,
  Lightbulb,
  CalendarDays,
  User,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { Session } from "../types";
import { getSession, recordingUrl } from "../api/client";
import { tokens } from "../theme/tokens";
import ScoreDial from "../components/ScoreDial";
import TalkRatioBar from "../components/TalkRatioBar";
import MetricCard from "../components/MetricCard";
import DimensionCard from "../components/DimensionCard";
import TimelineRibbon from "../components/TimelineRibbon";
import TimestampChip, { formatTime } from "../components/TimestampChip";
import Player, { type PlayerHandle } from "../components/Player";
import Card from "../components/Card";
import Badge from "../components/Badge";
import ChatAgent from "../components/ChatAgent";

export default function TeacherDashboard() {
  const { id = "" } = useParams();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const playerRef = useRef<PlayerHandle>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
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

  const seek = (seconds: number) => {
    playerRef.current?.seekTo(seconds);
    setCurrentTime(seconds);
    // Lleva la vista al reproductor para que se vea el efecto.
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Reúne todos los timestamps con evidencia para la cinta.
  const evidenceMarks = useMemo(() => {
    if (!session?.analysis) return [];
    const marks: number[] = [];
    for (const fw of session.analysis.frameworks) {
      for (const dim of fw.dimensions) {
        for (const ev of dim.evidence) marks.push(ev.timestamp);
      }
    }
    for (const st of session.analysis.strengths) {
      if (st.timestamp != null) marks.push(st.timestamp);
    }
    for (const im of session.analysis.improvements) {
      if (im.timestamp != null) marks.push(im.timestamp);
    }
    return marks;
  }, [session]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p className="text-inkSoft">Cargando la sesión…</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p className="text-inkSoft">No se encontró la sesión.</p>
        <Link to="/" className="text-evidence underline">
          Volver a la biblioteca
        </Link>
      </div>
    );
  }

  const { metadata, metrics, analysis } = session;
  const frameworks = analysis?.frameworks ?? [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-1">
        <h1 className="font-display text-3xl text-ink">{metadata.course}</h1>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-inkSoft">
          <span className="inline-flex items-center gap-1.5">
            <User className="h-4 w-4" aria-hidden="true" />
            {metadata.teacher}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays className="h-4 w-4" aria-hidden="true" />
            {metadata.date}
          </span>
          <span className="font-mono">
            Duración {formatTime(metadata.duration_seconds)}
          </span>
        </div>
      </div>

      {/* Reproductor + cinta */}
      <div className="mb-8 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Player
          ref={playerRef}
          recordingUrl={recordingUrl(session.session_id) || undefined}
          durationSeconds={metadata.duration_seconds}
          onTimeChange={setCurrentTime}
        />
        <Card className="flex flex-col justify-center">
          <h2 className="mb-3 text-sm font-semibold text-ink">
            Mapa de la clase
          </h2>
          <TimelineRibbon
            durationSeconds={metadata.duration_seconds}
            visualTimeline={metrics?.visual_timeline ?? []}
            evidenceMarks={evidenceMarks}
            onSeek={seek}
            currentTime={currentTime}
          />
        </Card>
      </div>

      {/* Dials por framework */}
      {frameworks.length > 0 && (
        <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2">
          {frameworks.slice(0, 2).map((fw) => (
            <Card
              key={fw.framework_id}
              className="flex flex-col items-center gap-2"
            >
              <ScoreDial
                score={fw.overall_score}
                label={fw.framework_name}
              />
            </Card>
          ))}
        </div>
      )}

      {/* Métricas duras */}
      {metrics && (
        <div className="mb-8 flex flex-col gap-4">
          <Card>
            <TalkRatioBar
              teacher={metrics.talk_ratio_teacher}
              students={metrics.talk_ratio_students}
            />
          </Card>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard
              label="Palabras / min"
              value={metrics.words_per_minute}
              detail="Ritmo del habla docente"
              icon={<Gauge className="h-3.5 w-3.5" />}
            />
            <MetricCard
              label="Preguntas"
              value={metrics.total_questions}
              detail={`${metrics.student_interventions} intervenciones de estudiantes`}
              icon={<MessageCircleQuestion className="h-3.5 w-3.5" />}
            />
            <MetricCard
              label="Silencios largos"
              value={metrics.long_silences.length}
              detail={
                metrics.long_silences.length > 0
                  ? metrics.long_silences
                      .map(
                        (s) =>
                          `${formatTime(s.start)}–${formatTime(s.end)}`,
                      )
                      .join(" · ")
                  : "Sin pausas extensas"
              }
              icon={<Timer className="h-3.5 w-3.5" />}
            />
            <MetricCard
              label="Muletillas"
              value={metrics.filler_words.count}
              detail={
                metrics.filler_words.top.length > 0
                  ? metrics.filler_words.top
                      .map((f) => `"${f.word}" ×${f.n}`)
                      .join(", ")
                  : "—"
              }
              icon={<MessageSquareDashed className="h-3.5 w-3.5" />}
            />
          </div>
        </div>
      )}

      {/* Dimensiones por framework */}
      {frameworks.map((fw) => (
        <section key={fw.framework_id} className="mb-10">
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <h2 className="font-display text-2xl text-ink">
              {fw.framework_name}
            </h2>
            {fw.overall_score !== null && (
              <span className="font-mono text-sm text-inkSoft">
                Global {fw.overall_score.toFixed(1)}/4
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {fw.dimensions.map((dim) => (
              <DimensionCard
                key={dim.dimension_id}
                dimension={dim}
                onSeek={seek}
              />
            ))}
          </div>
        </section>
      ))}

      {/* Fortalezas y mejoras */}
      <div className="mb-10 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <section>
          <h2 className="mb-4 font-display text-2xl text-ink">Fortalezas</h2>
          <div className="flex flex-col gap-4">
            {(analysis?.strengths ?? []).map((s, i) => (
              <Card key={i} className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-semibold text-ink">{s.title}</h3>
                  {s.timestamp != null && (
                    <TimestampChip seconds={s.timestamp} onSeek={seek} />
                  )}
                </div>
                <p className="text-sm text-inkSoft">{s.detail}</p>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 font-display text-2xl text-ink">
            Oportunidades de mejora
          </h2>
          <div className="flex flex-col gap-4">
            {(analysis?.improvements ?? []).map((im, i) => (
              <Card key={i} className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-semibold text-ink">{im.title}</h3>
                  {im.timestamp != null && (
                    <TimestampChip seconds={im.timestamp} onSeek={seek} />
                  )}
                </div>
                <p className="text-sm text-inkSoft">{im.detail}</p>
                <div className="mt-1 flex items-start gap-2 rounded-chip bg-paper px-3 py-2">
                  <Lightbulb
                    className="mt-0.5 h-4 w-4 shrink-0 text-good"
                    aria-hidden="true"
                  />
                  <p className="text-sm text-ink">
                    <span className="font-medium">Sugerencia: </span>
                    {im.suggestion}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </section>
      </div>

      {/* Alineación a objetivos */}
      {analysis?.objective_alignment && (
        <section className="mb-10">
          <h2 className="mb-4 font-display text-2xl text-ink">
            Alineación a objetivos
          </h2>
          <Card className="flex flex-col gap-4">
            <div>
              <div className="mb-1 flex items-baseline justify-between">
                <span className="text-sm font-medium text-ink">
                  Tiempo alineado a los objetivos
                </span>
                <span className="font-mono text-lg font-semibold text-good">
                  {Math.round(analysis.objective_alignment.aligned_pct * 100)}%
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-line">
                <div
                  className="h-full bg-good"
                  style={{
                    width: `${analysis.objective_alignment.aligned_pct * 100}%`,
                  }}
                />
              </div>
            </div>

            {metadata.objectives && metadata.objectives.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {metadata.objectives.map((o, i) => (
                  <Badge key={i} tone="ink">
                    {o}
                  </Badge>
                ))}
              </div>
            )}

            {analysis.objective_alignment.deviations.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-semibold text-ink">
                  Desvíos detectados
                </p>
                <ul className="flex flex-col gap-2">
                  {analysis.objective_alignment.deviations.map((d, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 border-l-2 border-evidence/30 pl-3"
                    >
                      <TimestampChip seconds={d.start} onSeek={seek} />
                      <span className="text-sm text-inkSoft">{d.note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        </section>
      )}

      {/* Evolución del docente */}
      <EvolutionSection
        currentScore={frameworks[0]?.overall_score ?? null}
        sessionDate={metadata.date}
      />

      {/* Chat con el agente */}
      <section className="mb-10">
        <div className="mb-4 flex items-center gap-2">
          <MessageCircleQuestion className="h-5 w-5 text-evidence" aria-hidden="true" />
          <h2 className="font-display text-2xl text-ink">
            Pregúntale al coach
          </h2>
        </div>
        <ChatAgent sessionId={session.session_id} />
      </section>
    </div>
  );
}

/**
 * Evolución del docente contra su PROPIA línea base (coaching, nunca ranking).
 * Solo hay 1 clase real; completamos con 2–3 puntos de ejemplo marcados.
 */
function EvolutionSection({
  currentScore,
  sessionDate,
}: {
  currentScore: number | null;
  sessionDate: string;
}) {
  const baseline = 2.6;
  const real = currentScore ?? 3.0;
  const data = [
    { name: "Sesión 1", score: 2.4, example: true },
    { name: "Sesión 2", score: 2.7, example: true },
    { name: "Sesión 3", score: 2.8, example: true },
    { name: "Esta clase", score: Number(real.toFixed(1)), example: false },
  ];

  return (
    <section className="mb-6">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-good" aria-hidden="true" />
        <h2 className="font-display text-2xl text-ink">
          Evolución del docente
        </h2>
      </div>
      <Card>
        <p className="mb-4 text-sm text-inkSoft">
          Comparación contra la propia línea base del docente. Es una lectura de
          coaching, no un ranking entre docentes.
        </p>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 8, right: 16, bottom: 8, left: -16 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={tokens.color.line} />
              <XAxis
                dataKey="name"
                tick={{ fill: tokens.color.inkSoft, fontSize: 12 }}
                stroke={tokens.color.line}
              />
              <YAxis
                domain={[0, 4]}
                ticks={[0, 1, 2, 3, 4]}
                tick={{ fill: tokens.color.inkSoft, fontSize: 12 }}
                stroke={tokens.color.line}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: 8,
                  border: `1px solid ${tokens.color.line}`,
                  fontSize: 12,
                }}
                formatter={(value: number, _name, item) => [
                  `${value}/4${item?.payload?.example ? " (sesión de ejemplo)" : ""}`,
                  "Puntaje global",
                ]}
              />
              <ReferenceLine
                y={baseline}
                stroke={tokens.color.inkSoft}
                strokeDasharray="4 4"
                label={{
                  value: "Línea base",
                  position: "insideTopRight",
                  fill: tokens.color.inkSoft,
                  fontSize: 11,
                }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke={tokens.color.good}
                strokeWidth={2.5}
                dot={{ r: 4, fill: tokens.color.good }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-3 inline-flex items-center gap-1 text-xs text-inkSoft">
          <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
          Las primeras tres sesiones son datos de ejemplo; &ldquo;Esta clase&rdquo;
          ({sessionDate}) es la lectura real.
        </p>
      </Card>
    </section>
  );
}
