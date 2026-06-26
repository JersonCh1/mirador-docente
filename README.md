# Mirador Docente

Web app que toma la grabación de una clase virtual (Meet/Zoom/Teams o un archivo
subido), la analiza de forma multimodal (audio → texto con diarización, métricas
de habla y, opcionalmente, frames) y produce **retroalimentación pedagógica
accionable anclada en evidencia con timestamps**.

El feedback tiene tres lentes sobre el mismo análisis: **docente**, **estudiante**
e **institución**. En el MVP solo el **dashboard del docente** es funcional
end-to-end; alumno e institución se muestran con la UI real y datos de ejemplo.

La evaluación se ancla en dos marcos pedagógicos:
1. **MINEDU – Marco de Buen Desempeño Docente (MBDD)** (Perú).
2. **OECD / TALIS – tres dimensiones de calidad de la enseñanza** (internacional).

> **Regla de oro:** cada juicio cualitativo viene con (a) un timestamp y (b) la
> cita textual exacta de la transcripción que lo respalda. Si no hay evidencia
> citable, no se afirma. La validación de citas se hace **por código**
> (`analysis/validator.py`), no con otro LLM: cada cita debe existir
> literalmente en un segmento de la transcripción, o se descarta como
> alucinación.

---

## Arquitectura (desacoplada y swappable)

Cada pieza vive detrás de una interfaz para poder cambiarla sin reescribir el
resto. Cambiar de proveedor = cambiar una variable de entorno.

| Costura | Interfaz | Implementaciones |
|---|---|---|
| Transcripción + diarización | `TranscriptionProvider` | `fake` (default), `assemblyai` |
| Análisis cualitativo (LLM) | `LLMProvider` | `fake` (default), `claude` |
| Marcos pedagógicos | datos en `rubrics/` | `minedu_mbdd`, `oecd_talis` |
| Almacenamiento | `SessionRepository` | SQLite (→ Postgres sin tocar lógica) |
| Métricas duras | funciones puras en `metrics/` | cero LLM |

El **contrato JSON** (`backend/app/schemas.py` ↔ `frontend/src/types.ts`) es
sagrado: es el shape que viaja entre backend y frontend. El mock canónico
(`frontend/src/mocks/sample_session.json`) lo cumple y permite trabajar el
frontend sin backend.

```
mirador/
├── backend/   FastAPI · pipeline · proveedores · métricas · rúbricas · análisis
└── frontend/  React + Vite + TS + Tailwind + Recharts
```

---

## Cómo correrlo en local

### 1. Backend (corre SIN API keys gracias a los proveedores `fake`)

```powershell
cd backend
py -3.11 -m venv .venv          # o: python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API en `http://localhost:8000` · health en `/api/health` · docs en `/docs`.

Con los proveedores `fake` (default), subir cualquier archivo dispara el
pipeline completo y produce el contrato entero — útil para demostrar el flujo
sin gastar créditos ni depender del wifi del evento.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

- Si `VITE_API_BASE` está vacío (o el backend no responde), el frontend cae a
  **modo mock** y usa `sample_session.json` — la UI funciona standalone.
- Para conectar al backend real: copia `frontend/.env.example` a `.env` con
  `VITE_API_BASE=http://localhost:8000`.

---

## 🔑 Cómo cablear los proveedores REALES (las API keys)

Todo está detrás de interfaces, así que pasar de demo a real es **cambiar
variables de entorno, cero cambios de código**. En `backend/`:

```powershell
copy .env.example .env
```

Edita `backend/.env`:

```env
# Cambia "fake" por el proveedor real:
TRANSCRIPTION_PROVIDER=assemblyai
LLM_PROVIDER=claude

# Pega tus llaves:
ASSEMBLYAI_API_KEY=tu_key_de_assemblyai
ANTHROPIC_API_KEY=sk-ant-...

# Modelo (ya viene por default):
LLM_MODEL=claude-sonnet-4-6
LLM_TEMPERATURE=0.2
```

Reinicia uvicorn. Ahora:
- `AssemblyAIProvider` transcribe con diarización real (español, `speaker_labels`).
- `ClaudeProvider` hace el análisis pedagógico real y el `validator` verifica
  cada cita contra la transcripción real.

> Mientras una key falte, deja ese proveedor en `fake` y el otro en real
> (ej. `LLM_PROVIDER=claude` + `TRANSCRIPTION_PROVIDER=fake`): el sistema mezcla
> sin problema.

### Variables de entorno (referencia)

| Variable | Default | Para qué |
|---|---|---|
| `TRANSCRIPTION_PROVIDER` | `fake` | `fake` \| `assemblyai` |
| `LLM_PROVIDER` | `fake` | `fake` \| `claude` |
| `ASSEMBLYAI_API_KEY` | — | key de AssemblyAI |
| `ANTHROPIC_API_KEY` | — | key de Claude |
| `LLM_MODEL` | `claude-sonnet-4-6` | modelo de análisis |
| `LLM_TEMPERATURE` | `0.2` | baja para consistencia |
| `ACTIVE_FRAMEWORKS` | `minedu_mbdd,oecd_talis` | marcos activos |
| `SILENCE_THRESHOLD` | `8.0` | umbral de silencio largo (s) |
| `DATABASE_URL` | `sqlite:///./app.db` | base de datos |
| `CORS_ORIGINS` | `*` | orígenes permitidos |

---

## Alcance del MVP

**Funcional end-to-end:** subida → pipeline → transcripción → métricas duras →
análisis MINEDU + TALIS → validación de citas → **dashboard del docente con
evidencia clickeable** + lista de sesiones persistente.

**Mockeado (UI real, datos de ejemplo):** dashboard de estudiante e institución;
la serie de evolución del docente se completa con 2–3 sesiones de ejemplo.

**Roadmap (NO en el MVP, va en las slides):** vector DB / memoria del semestre,
captura en vivo (webhooks Zoom/Teams/Meet), LTI / SSO, capa institucional real,
muestreo de frames para la `visual_timeline`.

---

## Deploy (Railway)

- `backend/Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (usa el `$PORT` que inyecta Railway).
- `backend/nixpacks.toml` declara **ffmpeg** como paquete del sistema (suele ser
  el punto que rompe el deploy — verifícalo en runtime).
- Build del frontend (`npm run build`) → `frontend/dist`; `app/main.py` lo sirve
  como estáticos si existe (un solo servicio Railway). Alternativa: dos servicios
  con `VITE_API_BASE` apuntando al API.
- SQLite vive en el filesystem efímero de Railway: para la demo está bien, pero
  si el contenedor reinicia se pierde. Para persistir, monta un volumen para
  `app.db`.

## Seguridad para la demo

1. **Pre-procesa la clase de demo** y guárdala como `Session` ya `ready`; en
   vivo muestras la subida y cargas el resultado pre-calculado.
2. **Congela el código ~2 h antes** de presentar.
3. Ten un `sample_session.json` de respaldo por si la base se reinicia.
4. Prueba el deploy de Railway mucho antes del final (ffmpeg + `$PORT`).
