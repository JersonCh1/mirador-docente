/**
 * SessionListPage — biblioteca de clases.
 *
 * Cada Session = tarjeta (curso, docente, fecha, status, overall_score si
 * ready). Filtros por curso/docente. Click → TeacherDashboard. Estado vacío
 * como invitación.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Upload, Search, CalendarDays, User } from "lucide-react";
import { listSessions } from "../api/client";
import type { SessionSummary } from "../types";
import Badge from "../components/Badge";
import { scoreColor } from "../theme/tokens";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Subida",
  transcribing: "Transcribiendo",
  analyzing: "Analizando",
  validating: "Validando",
  ready: "Lista",
  failed: "Falló",
};

export default function SessionListPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [course, setCourse] = useState("");
  const [teacher, setTeacher] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    listSessions()
      .then((data) => {
        if (active) setSessions(data);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return sessions.filter((s) => {
      const okCourse = course
        ? s.course.toLowerCase().includes(course.toLowerCase())
        : true;
      const okTeacher = teacher
        ? s.teacher.toLowerCase().includes(teacher.toLowerCase())
        : true;
      return okCourse && okTeacher;
    });
  }, [sessions, course, teacher]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="font-display text-3xl text-ink">Biblioteca de clases</h1>
        <p className="text-inkSoft">
          Retroalimentación pedagógica anclada en evidencia, clase por clase.
        </p>
      </div>

      {/* Filtros */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <FilterInput
          icon={<Search className="h-4 w-4" />}
          placeholder="Filtrar por curso"
          value={course}
          onChange={setCourse}
        />
        <FilterInput
          icon={<User className="h-4 w-4" />}
          placeholder="Filtrar por docente"
          value={teacher}
          onChange={setTeacher}
        />
      </div>

      {loading ? (
        <p className="text-inkSoft">Cargando clases…</p>
      ) : filtered.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((s) => (
            <Link
              key={s.session_id}
              to={`/session/${s.session_id}`}
              className="card-mirador flex flex-col gap-3 p-5 transition-transform hover:-translate-y-0.5 hover:shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-display text-xl text-ink">{s.course}</h2>
                {s.status === "ready" && s.overall_score !== null ? (
                  <span
                    className="shrink-0 font-mono text-lg font-semibold"
                    style={{ color: scoreColor(s.overall_score) }}
                  >
                    {s.overall_score.toFixed(1)}
                    <span className="text-xs text-inkSoft">/4</span>
                  </span>
                ) : (
                  <Badge
                    tone={s.status === "failed" ? "warn" : "neutral"}
                  >
                    {STATUS_LABEL[s.status] ?? s.status}
                  </Badge>
                )}
              </div>
              <div className="flex flex-col gap-1 text-sm text-inkSoft">
                <span className="inline-flex items-center gap-1.5">
                  <User className="h-3.5 w-3.5" aria-hidden="true" />
                  {s.teacher}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />
                  {s.date}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function FilterInput({
  icon,
  placeholder,
  value,
  onChange,
}: {
  icon: React.ReactNode;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-1 items-center gap-2 rounded-chip border border-line bg-white px-3 py-2">
      <span className="text-inkSoft">{icon}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-inkSoft/70"
      />
    </label>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-card border border-dashed border-line bg-white px-6 py-16 text-center">
      <Upload className="h-10 w-10 text-inkSoft" aria-hidden="true" />
      <div>
        <p className="font-display text-xl text-ink">
          Sube una grabación para empezar
        </p>
        <p className="mt-1 text-sm text-inkSoft">
          Mirador transcribe la clase y te devuelve una lectura pedagógica con
          evidencia clickeable.
        </p>
      </div>
      <Link
        to="/upload"
        className="inline-flex items-center gap-1.5 rounded-chip bg-ink px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-inkSoft"
      >
        <Upload className="h-4 w-4" aria-hidden="true" />
        Procesar clase
      </Link>
    </div>
  );
}
