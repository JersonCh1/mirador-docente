/**
 * Cliente HTTP de Mirador Docente.
 *
 * Funciones: createSession, listSessions, getSession, getSessionStatus.
 *
 * MODO MOCK: si VITE_API_BASE está vacío, o si un fetch falla, caemos al
 * `sample_session.json` para que la UI funcione standalone en desarrollo.
 */
import type {
  CreateSessionResponse,
  Session,
  SessionSummary,
  StatusResponse,
} from "../types";
import sampleSession from "../mocks/sample_session.json";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").trim();

/** El mock canónico, tipado contra el contrato. */
const MOCK: Session = sampleSession as unknown as Session;

/** ¿Estamos forzados a modo mock por configuración (sin API_BASE)? */
export function isMockMode(): boolean {
  return API_BASE.length === 0;
}

/** Filtros opcionales para listar sesiones. */
export interface SessionFilters {
  course?: string;
  teacher?: string;
}

function toSummary(s: Session): SessionSummary {
  const overall =
    s.analysis?.frameworks?.[0]?.overall_score ?? null;
  return {
    session_id: s.session_id,
    course: s.metadata.course,
    teacher: s.metadata.teacher,
    date: s.metadata.date,
    status: s.status,
    overall_score: overall,
  };
}

/** URL de la grabación de una sesión (puede no existir en demo). */
export function recordingUrl(sessionId: string): string {
  if (isMockMode()) return "";
  return `${API_BASE}/api/sessions/${sessionId}/recording`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`Petición fallida (${res.status}): ${path}`);
  }
  return (await res.json()) as T;
}

/** Crea una sesión a partir de un FormData (archivo o URL + metadatos). */
export async function createSession(
  formData: FormData,
): Promise<CreateSessionResponse> {
  if (isMockMode()) {
    return { session_id: MOCK.session_id, status: "uploaded" };
  }
  try {
    return await fetchJson<CreateSessionResponse>("/api/sessions", {
      method: "POST",
      body: formData,
    });
  } catch {
    // Fallback a mock si el backend no responde.
    return { session_id: MOCK.session_id, status: "uploaded" };
  }
}

/** Lista las sesiones de la biblioteca (con filtros opcionales). */
export async function listSessions(
  filters?: SessionFilters,
): Promise<SessionSummary[]> {
  if (isMockMode()) {
    return applyFilters([toSummary(MOCK)], filters);
  }
  try {
    const qs = new URLSearchParams();
    if (filters?.course) qs.set("course", filters.course);
    if (filters?.teacher) qs.set("teacher", filters.teacher);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return await fetchJson<SessionSummary[]>(`/api/sessions${suffix}`);
  } catch {
    return applyFilters([toSummary(MOCK)], filters);
  }
}

function applyFilters(
  list: SessionSummary[],
  filters?: SessionFilters,
): SessionSummary[] {
  let out = list;
  if (filters?.course) {
    const q = filters.course.toLowerCase();
    out = out.filter((s) => s.course.toLowerCase().includes(q));
  }
  if (filters?.teacher) {
    const q = filters.teacher.toLowerCase();
    out = out.filter((s) => s.teacher.toLowerCase().includes(q));
  }
  return out;
}

/** Obtiene el detalle completo de una sesión. */
export async function getSession(id: string): Promise<Session> {
  if (isMockMode()) {
    return MOCK;
  }
  try {
    return await fetchJson<Session>(`/api/sessions/${id}`);
  } catch {
    return MOCK;
  }
}

/** Estado/progreso del pipeline de una sesión (para polling). */
export async function getSessionStatus(id: string): Promise<StatusResponse> {
  if (isMockMode()) {
    return { status: MOCK.status, progress: MOCK.progress, error: null };
  }
  try {
    return await fetchJson<StatusResponse>(`/api/sessions/${id}/status`);
  } catch {
    return { status: "ready", progress: 100, error: null };
  }
}
