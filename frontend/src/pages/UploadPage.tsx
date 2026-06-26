/**
 * UploadPage — subir grabación o pegar URL.
 *
 * Campos opcionales: curso, docente, fecha, plataforma, objetivos (lista
 * editable). Botón "Procesar clase" → POST createSession → pantalla de
 * progreso con POLLING de getSessionStatus cada 2s hasta "ready", mostrando
 * ProgressStages. Estado vacío como invitación.
 */
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, X, Plus, Link2 } from "lucide-react";
import { createSession, getSessionStatus } from "../api/client";
import type { Platform, Status } from "../types";
import ProgressStages from "../components/ProgressStages";

const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "meet", label: "Google Meet" },
  { value: "zoom", label: "Zoom" },
  { value: "teams", label: "Microsoft Teams" },
  { value: "upload", label: "Archivo subido" },
];

export default function UploadPage() {
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [course, setCourse] = useState("");
  const [teacher, setTeacher] = useState("");
  const [date, setDate] = useState("");
  const [platform, setPlatform] = useState<Platform>("meet");
  const [objectives, setObjectives] = useState<string[]>([""]);
  const [dragging, setDragging] = useState(false);

  const [processing, setProcessing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("uploaded");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const fileInput = useRef<HTMLInputElement>(null);

  // Polling del estado mientras se procesa.
  useEffect(() => {
    if (!processing || !sessionId) return;
    let active = true;

    const poll = async () => {
      const s = await getSessionStatus(sessionId);
      if (!active) return;
      setStatus(s.status);
      setProgress(s.progress);
      if (s.status === "ready") {
        navigate(`/session/${sessionId}`);
      } else if (s.status === "failed") {
        setError(s.error ?? "El procesamiento falló.");
      }
    };

    void poll();
    const interval = setInterval(poll, 2000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [processing, sessionId, navigate]);

  const canSubmit = Boolean(file || url.trim());

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    const fd = new FormData();
    if (file) fd.append("file", file);
    if (url.trim()) fd.append("url", url.trim());
    if (course) fd.append("course", course);
    if (teacher) fd.append("teacher", teacher);
    if (date) fd.append("date", date);
    fd.append("platform", platform);
    objectives
      .map((o) => o.trim())
      .filter(Boolean)
      .forEach((o) => fd.append("objectives", o));

    setError(null);
    const res = await createSession(fd);
    setSessionId(res.session_id);
    setStatus(res.status);
    setProcessing(true);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  if (processing) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
        <h1 className="mb-2 font-display text-3xl text-ink">
          Procesando la clase
        </h1>
        <p className="mb-8 text-inkSoft">
          Estamos transcribiendo y leyendo la sesión. Esto se actualiza solo.
        </p>
        <div className="card-mirador p-6">
          <ProgressStages status={status} progress={progress} />
          {error && (
            <p className="mt-4 rounded-chip border border-warn/30 bg-warn/10 px-3 py-2 text-sm text-warn">
              {error}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="mb-2 font-display text-3xl text-ink">Procesar una clase</h1>
      <p className="mb-8 text-inkSoft">
        Sube una grabación o pega su enlace. Los demás campos son opcionales y
        ayudan a contextualizar la lectura.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`flex flex-col items-center gap-3 rounded-card border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragging ? "border-evidence bg-evidence/5" : "border-line bg-white"
          }`}
        >
          <UploadCloud className="h-9 w-9 text-inkSoft" aria-hidden="true" />
          {file ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink">{file.name}</span>
              <button
                type="button"
                onClick={() => setFile(null)}
                aria-label="Quitar archivo"
                className="text-inkSoft hover:text-warn"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <p className="text-sm text-ink">
                Arrastra el video o audio aquí
              </p>
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                className="rounded-chip border border-line px-3 py-1.5 text-sm font-medium text-ink hover:bg-paper"
              >
                Elegir archivo
              </button>
            </>
          )}
          <input
            ref={fileInput}
            type="file"
            accept="video/*,audio/*"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-inkSoft">
          <span className="h-px flex-1 bg-line" />
          o pega un enlace
          <span className="h-px flex-1 bg-line" />
        </div>

        <Field label="URL de la grabación">
          <div className="flex items-center gap-2 rounded-chip border border-line bg-white px-3 py-2">
            <Link2 className="h-4 w-4 text-inkSoft" aria-hidden="true" />
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://…"
              className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-inkSoft/70"
            />
          </div>
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Curso">
            <TextInput value={course} onChange={setCourse} placeholder="Cálculo I" />
          </Field>
          <Field label="Docente">
            <TextInput
              value={teacher}
              onChange={setTeacher}
              placeholder="Prof. Ramírez"
            />
          </Field>
          <Field label="Fecha">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-chip border border-line bg-white px-3 py-2 text-sm text-ink outline-none"
            />
          </Field>
          <Field label="Plataforma">
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
              className="w-full rounded-chip border border-line bg-white px-3 py-2 text-sm text-ink outline-none"
            >
              {PLATFORMS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        {/* Objetivos editables */}
        <Field label="Objetivos de la sesión">
          <div className="flex flex-col gap-2">
            {objectives.map((obj, i) => (
              <div key={i} className="flex items-center gap-2">
                <TextInput
                  value={obj}
                  onChange={(v) =>
                    setObjectives((prev) =>
                      prev.map((o, idx) => (idx === i ? v : o)),
                    )
                  }
                  placeholder={`Objetivo ${i + 1}`}
                />
                {objectives.length > 1 && (
                  <button
                    type="button"
                    onClick={() =>
                      setObjectives((prev) =>
                        prev.filter((_, idx) => idx !== i),
                      )
                    }
                    aria-label="Quitar objetivo"
                    className="text-inkSoft hover:text-warn"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => setObjectives((prev) => [...prev, ""])}
              className="inline-flex w-fit items-center gap-1 text-sm font-medium text-inkSoft hover:text-ink"
            >
              <Plus className="h-4 w-4" /> Agregar objetivo
            </button>
          </div>
        </Field>

        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex items-center justify-center gap-2 rounded-chip bg-ink px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-inkSoft disabled:cursor-not-allowed disabled:opacity-50"
        >
          <UploadCloud className="h-4 w-4" aria-hidden="true" />
          Procesar clase
        </button>
      </form>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
    </label>
  );
}

function TextInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-chip border border-line bg-white px-3 py-2 text-sm text-ink outline-none placeholder:text-inkSoft/70"
    />
  );
}
