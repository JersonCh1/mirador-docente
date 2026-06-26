/**
 * EL CONTRATO JSON (CONGELADO) — frontend side.
 *
 * Espejo EXACTO de `backend/app/schemas.py`. Si cambia uno, cambia el otro.
 * Todos los timestamp / start / end están en SEGUNDOS desde el inicio de la
 * grabación. Los score van en escala 1–4 (maxScore = 4 en el MVP).
 */

export type Platform = "meet" | "zoom" | "teams" | "upload";

export type Status =
  | "uploaded"
  | "transcribing"
  | "analyzing"
  | "validating"
  | "ready"
  | "failed";

export type Speaker = "teacher" | "student";

export interface Metadata {
  course: string;
  teacher: string;
  date: string; // YYYY-MM-DD
  platform: Platform;
  duration_seconds: number;
  objectives?: string[] | null;
}

export interface Segment {
  speaker: Speaker;
  start: number;
  end: number;
  text: string;
}

export interface Transcript {
  segments: Segment[];
}

export interface Silence {
  start: number;
  end: number;
}

export interface FillerWord {
  word: string;
  n: number;
}

export interface FillerWords {
  count: number;
  top: FillerWord[];
}

export type VisualType = "slides" | "whiteboard" | "screen_share" | "none";

export interface VisualSegment {
  start: number;
  end: number;
  type: VisualType;
}

export interface Metrics {
  talk_ratio_teacher: number;
  talk_ratio_students: number;
  words_per_minute: number;
  total_questions: number;
  student_interventions: number;
  long_silences: Silence[];
  filler_words: FillerWords;
  visual_timeline: VisualSegment[];
}

export interface Evidence {
  timestamp: number;
  quote: string;
  comment?: string | null;
}

export interface Dimension {
  dimension_id: string;
  name: string;
  score: number | null;
  max_score: number;
  observable: boolean;
  summary: string;
  evidence: Evidence[];
}

export interface Framework {
  framework_id: string;
  framework_name: string;
  overall_score: number | null;
  dimensions: Dimension[];
}

export interface Strength {
  title: string;
  detail: string;
  timestamp?: number | null;
}

export interface Improvement {
  title: string;
  detail: string;
  timestamp?: number | null;
  suggestion: string;
}

export interface Deviation {
  start: number;
  end: number;
  note: string;
}

export interface ObjectiveAlignment {
  aligned_pct: number;
  deviations: Deviation[];
}

export interface Analysis {
  frameworks: Framework[];
  strengths: Strength[];
  improvements: Improvement[];
  objective_alignment?: ObjectiveAlignment | null;
}

export interface StudentRecommendation {
  title: string;
  detail: string;
}

export interface StudentFeedback {
  participation_level: "low" | "medium" | "high";
  interventions: number;
  speaking_seconds: number;
  recommendations: StudentRecommendation[];
  review_topics: string[];
}

export interface Session {
  session_id: string;
  status: Status;
  progress: number;
  error?: string | null;
  metadata: Metadata;
  transcript?: Transcript | null;
  metrics?: Metrics | null;
  analysis?: Analysis | null;
  student_feedback?: StudentFeedback | null;
  created_at: string;
}

export interface SessionSummary {
  session_id: string;
  course: string;
  teacher: string;
  date: string;
  status: Status;
  overall_score: number | null;
}

export interface StatusResponse {
  status: Status;
  progress: number;
  error?: string | null;
}

export interface CreateSessionResponse {
  session_id: string;
  status: Status;
}
