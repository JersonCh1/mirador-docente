/**
 * InstitutionDashboard — vista institucional (MOCKEADO, UI real).
 *
 * Métricas agregadas por docente/departamento (datos de ejemplo coherentes) +
 * nota de cómo se traduce en evidencia para calidad institucional
 * (ISO 21001 / SUNEDU). Deja MUY claro que es agregado y NO punitivo.
 */
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { ShieldCheck, Info, Users } from "lucide-react";
import { tokens, scoreColor } from "../theme/tokens";
import Card from "../components/Card";
import Badge from "../components/Badge";
import MetricCard from "../components/MetricCard";

// Datos de ejemplo, coherentes pero inventados (vista de demostración).
const DEPARTMENTS = [
  { name: "Ciencias Básicas", score: 3.0, teachers: 12 },
  { name: "Ingeniería", score: 2.8, teachers: 18 },
  { name: "Humanidades", score: 3.2, teachers: 9 },
  { name: "Negocios", score: 2.6, teachers: 14 },
];

const TEACHERS = [
  { name: "Prof. Ramírez", course: "Cálculo I", score: 3.0, sessions: 4 },
  { name: "Prof. Salas", course: "Física I", score: 2.7, sessions: 3 },
  { name: "Prof. Núñez", course: "Álgebra", score: 3.3, sessions: 5 },
  { name: "Prof. Vega", course: "Química", score: 2.5, sessions: 2 },
];

export default function InstitutionDashboard() {
  const avg =
    DEPARTMENTS.reduce((a, d) => a + d.score, 0) / DEPARTMENTS.length;
  const totalTeachers = DEPARTMENTS.reduce((a, d) => a + d.teachers, 0);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-2 flex items-center gap-3">
        <h1 className="font-display text-3xl text-ink">Vista institucional</h1>
        <Badge tone="evidence">Vista de demostración con datos de ejemplo</Badge>
      </div>
      <p className="mb-8 max-w-3xl text-inkSoft">
        Lectura agregada de la calidad de la enseñanza. Sirve como evidencia
        para procesos de aseguramiento de la calidad; no es una herramienta
        punitiva ni de ranking individual.
      </p>

      {/* KPIs */}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Promedio institucional"
          value={`${avg.toFixed(1)}/4`}
          detail="Puntaje global agregado"
        />
        <MetricCard
          label="Docentes observados"
          value={totalTeachers}
          detail="Con al menos una sesión"
          icon={<Users className="h-3.5 w-3.5" />}
        />
        <MetricCard
          label="Departamentos"
          value={DEPARTMENTS.length}
          detail="Con cobertura activa"
        />
        <MetricCard
          label="Sesiones analizadas"
          value={142}
          detail="En el periodo actual"
        />
      </div>

      {/* Por departamento */}
      <section className="mb-8">
        <h2 className="mb-4 font-display text-2xl text-ink">
          Calidad por departamento
        </h2>
        <Card>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={DEPARTMENTS}
                margin={{ top: 8, right: 16, bottom: 8, left: -16 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={tokens.color.line}
                />
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
                  formatter={(value: number) => [`${value}/4`, "Puntaje global"]}
                />
                <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                  {DEPARTMENTS.map((d, i) => (
                    <Cell key={i} fill={scoreColor(d.score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </section>

      {/* Por docente */}
      <section className="mb-8">
        <h2 className="mb-4 font-display text-2xl text-ink">
          Resumen por docente
        </h2>
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-inkSoft">
              <tr>
                <th className="px-5 py-3 font-medium">Docente</th>
                <th className="px-5 py-3 font-medium">Curso</th>
                <th className="px-5 py-3 font-medium">Sesiones</th>
                <th className="px-5 py-3 font-medium">Puntaje global</th>
              </tr>
            </thead>
            <tbody>
              {TEACHERS.map((t, i) => (
                <tr key={i} className="border-b border-line last:border-0">
                  <td className="px-5 py-3 font-medium text-ink">{t.name}</td>
                  <td className="px-5 py-3 text-inkSoft">{t.course}</td>
                  <td className="px-5 py-3 font-mono text-inkSoft">
                    {t.sessions}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className="font-mono font-semibold"
                      style={{ color: scoreColor(t.score) }}
                    >
                      {t.score.toFixed(1)}/4
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      {/* Nota de calidad */}
      <section>
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-good" aria-hidden="true" />
            <h2 className="font-display text-xl text-ink">
              Evidencia para calidad institucional
            </h2>
          </div>
          <p className="text-sm text-inkSoft">
            Cada lectura se ancla en evidencia con timestamps verificables. Esa
            trazabilidad alimenta los sistemas de gestión de la calidad
            educativa (ISO 21001) y los procesos de licenciamiento y
            acreditación (SUNEDU), sustituyendo percepciones por evidencia
            concreta y revisable.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge tone="ink">ISO 21001</Badge>
            <Badge tone="ink">SUNEDU</Badge>
            <Badge tone="ink">Evidencia trazable</Badge>
          </div>
          <div className="mt-1 flex items-start gap-2 rounded-chip bg-paper px-3 py-2">
            <Info
              className="mt-0.5 h-4 w-4 shrink-0 text-inkSoft"
              aria-hidden="true"
            />
            <p className="text-xs text-inkSoft">
              El objetivo es el desarrollo profesional docente, no la sanción.
              Los datos se leen de forma agregada y formativa.
            </p>
          </div>
        </Card>
      </section>
    </div>
  );
}
