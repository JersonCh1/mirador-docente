/**
 * NavBar — barra superior.
 *
 * Muestra el nombre "Mirador" (display font) y, cuando estás dentro de una
 * sesión, el selector de los 3 lentes (Docente / Estudiante / Institución).
 */
import { Link, useLocation, useParams, useMatch } from "react-router-dom";
import { Mountain, Upload } from "lucide-react";

type Lens = "teacher" | "student";

export default function NavBar() {
  const location = useLocation();
  const params = useParams();
  const sessionMatch = useMatch("/session/:id/*");
  const sessionId = sessionMatch?.params.id ?? params.id;

  const onStudent = location.pathname.endsWith("/student");
  const lens: Lens = onStudent ? "student" : "teacher";

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <Mountain className="h-6 w-6 text-evidence" aria-hidden="true" />
          <span className="font-display text-2xl leading-none text-ink">
            Mirador
          </span>
          <span className="hidden text-sm text-inkSoft sm:inline">
            Docente
          </span>
        </Link>

        <nav className="flex items-center gap-2">
          {sessionId ? (
            <div
              className="flex items-center rounded-chip border border-line bg-white p-0.5"
              role="tablist"
              aria-label="Lentes de la sesión"
            >
              <LensTab
                to={`/session/${sessionId}`}
                active={lens === "teacher"}
                label="Docente"
              />
              <LensTab
                to={`/session/${sessionId}/student`}
                active={lens === "student"}
                label="Estudiante"
              />
              <LensTab
                to="/institution"
                active={false}
                label="Institución"
              />
            </div>
          ) : (
            <LensTab to="/institution" active={false} label="Institución" />
          )}

          <Link
            to="/upload"
            className="inline-flex items-center gap-1.5 rounded-chip bg-ink px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-inkSoft"
          >
            <Upload className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Procesar clase</span>
            <span className="sm:hidden">Subir</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}

function LensTab({
  to,
  active,
  label,
}: {
  to: string;
  active: boolean;
  label: string;
}) {
  return (
    <Link
      to={to}
      role="tab"
      aria-selected={active}
      className={`rounded-[6px] px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-ink text-white"
          : "text-inkSoft hover:bg-paper"
      }`}
    >
      {label}
    </Link>
  );
}
