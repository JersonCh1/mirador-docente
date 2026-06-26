# HANDOFF — Guía para la próxima sesión de Claude Code

> **Objetivo de esta guía:** que la siguiente sesión deje Mirador Docente
> funcionando **tal como pide el prompt original** (`prompt_inicial`): subir clase →
> pipeline multimodal → análisis con **MINEDU + TALIS** anclado en evidencia con
> timestamps → **TeacherDashboard funcional** con retro completa. Todo validado
> **parte por parte**, no de un solo golpe.
>
> Lee esto entero ANTES de tocar código. El prompt original (la especificación
> congelada) es la fuente de verdad del producto; esta guía es el plan de ataque.

---

## 0. TL;DR del estado actual (qué es real y qué es fake)

La **rebanada vertical YA existe y corre end-to-end en modo fake**. La arquitectura
desacoplada del prompt (§2) está implementada: providers swappables, rúbricas como
datos, repo, pipeline por etapas, contrato Pydantic+TS, validador de citas por código.

| Pieza | Estado | Nota |
|---|---|---|
| Contrato JSON (`schemas.py` + `types.ts` + mock) | ✅ Real | Congelado, respétalo. |
| Pipeline por etapas (ingest→transcribe→metrics→**frames**→analyze→validate→persist) | ✅ Cableado | frames recién conectado (devuelve `[]`). |
| Métricas duras (talk ratio, WPM, preguntas, silencios, muletillas) | ✅ Real, determinista | CERO LLM. Testeadas. |
| Validador anti-alucinación (citas por código) | ✅ Real | Valida `evidence`; no toca strengths/improvements. |
| Rúbricas MINEDU + TALIS | ⚠️ Real como **datos**, pero **texto = paráfrasis** | Movidas a `backend/standards/*.json`, `verified:false`. |
| Descarga de grabación por URL (Drive/Meet) | ✅ Real | Solo descarga si transcriptor ≠ fake. |
| Transcripción real (audio→texto, diarización) | ⏸️ Requiere `ASSEMBLYAI_API_KEY` | Sin key → transcript **fake canónico**. |
| Análisis LLM real (Claude) | ⏸️ Requiere `ANTHROPIC_API_KEY` | Sin key → análisis **fake canónico** (mock). |
| **Frames / `visual_timeline` (multimodal visual)** | ❌ **No implementado** | Seam conectado; `sample_frames` devuelve `[]`. |
| StudentDashboard / InstitutionDashboard | ✅ Mock con UI real | Es lo que pide el MVP (§15). |

**La confusión típica:** sin keys, el sistema NO analiza la clase real — devuelve datos
de ejemplo precocinados (transcript y análisis de una clase de derivadas). "Multimodal"
hoy = solo audio→texto. No hay análisis de video/frames. No hay multi-agente: hay UN
`Analyzer` que llama al LLM una vez por marco.

**Por qué "no aparecía la retro" en local:** un provider quedó en modo real sin key →
la etapa revienta → sesión `failed` → no se guarda análisis. Solución inmediata: ambos
providers en `fake`, o poner las dos keys.

---

## 1. Lo que falta para cumplir el prompt (gap analysis priorizado)

En orden de impacto para la demo:

1. **[CRÍTICO] Keys reales + 1 pasada real verificada.** Sin esto nada es "de verdad".
   `ASSEMBLYAI_API_KEY` (free tier) + `ANTHROPIC_API_KEY` (ya se usa en este entorno).
2. **[ALTO] Verificar los estándares contra el documento oficial.** El prompt (§7.1) lo
   marca como **obligatorio**: reemplazar la paráfrasis del MBDD por texto oficial y
   poner `verified:true`. TALIS revisar igual.
3. **[ALTO] Afinar el prompt-rúbrica con la clase real** (§8, §16.4): requiere 2–3
   iteraciones para que las citas sean exactas y el validador no descarte evidencia.
4. **[MEDIO] Multi-agente / subagentes de análisis** (lo que pediste): paralelizar el
   análisis por marco y añadir un sub-análisis visual. Ver §5 de esta guía.
5. **[OPCIONAL] Frames reales** (`visual_timeline`): visión multimodal con Claude. §6.
6. **[OPCIONAL] Serie temporal de evolución** con 2–3 sesiones de ejemplo (§15).

---

## 2. Cómo correr y verificar (hazlo PRIMERO, antes de cambiar nada)

```powershell
# Backend (desde backend/)
.venv\Scripts\python.exe -m pytest -q                       # 14 tests deben pasar
.venv\Scripts\uvicorn app.main:app --reload --port 8000     # API en :8000

# Frontend (desde frontend/)
# crea frontend/.env.local con:  VITE_API_BASE=http://localhost:8000
npm install
npm run dev
```

**Smoke test de humo en modo fake (sin keys)** — confirma que la rebanada corre:
```powershell
# backend/.env  →  TRANSCRIPTION_PROVIDER=fake  y  LLM_PROVIDER=fake
curl -X POST http://localhost:8000/api/sessions -F "course=Cálculo I" -F "platform=meet" -F "objectives=Definir derivada"
# toma el session_id y:
curl http://localhost:8000/api/sessions/<id>          # debe llegar a status "ready" con analysis lleno
```
Si en fake ves la retro completa → la rebanada está sana y el problema siempre fue keys.

---

## 3. Secuencia recomendada (parte por parte, con verificación)

> Regla: **un paso, una verificación, un commit**. No avances al siguiente hasta que el
> actual esté verde. Trabaja en una rama (`git checkout -b real-pipeline`).

### Paso 1 — Activar providers reales y validar transcripción
- `backend/.env`: `TRANSCRIPTION_PROVIDER=assemblyai`, `ASSEMBLYAI_API_KEY=...`,
  `LLM_PROVIDER=claude`, `ANTHROPIC_API_KEY=...`.
- Sube/pega una grabación **corta (2–3 min, español, 2+ voces)** primero, no la clase
  de 1h (itera barato).
- **Verifica:** `GET /api/sessions/<id>` → `transcript.segments` con `speaker`
  teacher/student y timestamps reales. Si falla, lee `error` del status.
- Gotcha: el heurístico de diarización marca como `teacher` al speaker con más tiempo.
  Si sale al revés, revisa `assemblyai.py`.

### Paso 2 — Validar métricas duras sobre transcript real
- **Verifica:** `metrics` coherentes (talk_ratio suma ~1.0, WPM 100–180, preguntas > 0).
- Las métricas son funciones puras en `metrics/`; si algo se ve raro, testéalo aislado.

### Paso 3 — Validar análisis LLM + citas
- **Verifica:** `analysis.frameworks` (MINEDU y TALIS) con `evidence` cuyas `quote`
  existan **textualmente** en el transcript. Mira el `validation_report` (en
  `validator.py`, hoy solo se loguea internamente — considera exponerlo para debug).
- **Si el validador descarta muchas citas:** el modelo está parafraseando. Endurece el
  prompt (`analysis/prompt.py`): exige copiar carácter por carácter; baja temperatura.
- Itera el prompt 2–3 veces aquí. Es el paso que más pulido necesita (§16.4 del prompt).

### Paso 4 — Verificar los estándares (anti-alucinación de marco)
- Abre el **documento oficial del MBDD** (RM del MINEDU). Reemplaza `name`/`description`
  en `backend/standards/minedu_mbdd.json` por el texto oficial; llena `source` con la
  cita (RM, página) y pon `"verified": true`. Igual para TALIS si tienes la fuente.
- **Verifica:** `build_registry()` carga el JSON (el `source` aparece). Reinicia el
  server (el registry se cachea; o llama `reload_registry()`).
- ⚠️ El usuario pegó un link de Drive que **NO** es el MBDD (era una grabación). Hay que
  **conseguir el PDF oficial del MBDD** aparte. No inventes el texto.

### Paso 5 — Dashboard del docente end-to-end
- **Verifica en el front:** ScoreDial por marco, TalkRatioBar, DimensionCards con
  EvidenceList, TimestampChips clickeables que hacen seek en el reproductor, secciones
  Fortalezas/Mejoras, alineación a objetivos. Dimensiones `observable:false` atenuadas.

### Paso 6 — Pre-procesar la clase de demo y congelar (§17 del prompt)
- Procesa la clase real definitiva, déjala como `Session` `ready`, guarda un
  `sample_session.json` de respaldo. **Nunca** proceses en vivo frente al jurado.

---

## 4. Cómo usar AGENTES/SUBAGENTES en la próxima sesión (lo que pediste)

Hay **dos sentidos** de "agentes" — úsalos ambos:

### 4.1 Subagentes de Claude Code para CONSTRUIR y VERIFICAR (meta-nivel)
Paraleliza el trabajo de la sesión con la herramienta `Agent` / `Workflow`:
- **Agente A (transcripción):** activa AssemblyAI, prueba con audio corto, reporta el
  shape del transcript. (read-only + edita `assemblyai.py` si hace falta).
- **Agente B (métricas):** verifica cada métrica contra el transcript real, escribe tests.
- **Agente C (análisis+prompt):** itera `prompt.py` hasta que el validador acepte ≥90%
  de las citas; reporta `validation_report`.
- **Agente D (estándares):** toma el PDF del MBDD y produce el JSON oficial verificado.
- **Agente E (frontend):** verifica el render del dashboard con datos reales.

Lánzalos en paralelo cuando sean independientes; cada uno devuelve un reporte y tú
integras. Verifica **parte por parte** (es exactamente lo que el usuario pidió).

### 4.2 "Subagentes" de ANÁLISIS en runtime (dentro del producto)
Hoy `_build_analysis` (en `pipeline/runner.py`) ya llama al `Analyzer` **una vez por
marco** — eso es la semilla del patrón. Para hacerlo realmente multi-agente y mejor:

- **Paraleliza** las llamadas por marco (MINEDU, TALIS) — son independientes. Hoy es un
  `for` secuencial; conviértelo en llamadas concurrentes (asyncio/thread).
- **Añade un sub-agente "visual"** que analice los frames (§6) y aporte evidencia visual
  a `visual_timeline` y a dimensiones como "uso de recursos/apoyos visuales".
- **Añade un sub-agente "sintetizador"** que tome los análisis por marco + métricas +
  visual y genere `strengths`/`improvements` globales coherentes (hoy salen de la 1ª
  llamada, ver `_build_analysis`).
- **Mantén el validador por código como juez final** de toda evidencia (no lo reemplaces
  por un LLM: el prompt §9 es explícito en que la validación es código).

Patrón sugerido: `analyze (N marcos en paralelo) → analyze_visual → synthesize → validate`.
Cada sub-agente devuelve JSON tipado contra el contrato; el validador limpia citas.

> NO construyas el RAG / memoria del semestre / multiagente ADK completo (el prompt §15
> lo prohíbe en el MVP — es roadmap para slides).

---

## 5. Frames / `visual_timeline` (si hay tiempo — multimodal real)

Seam ya conectado: `pipeline/runner.py` etapa 3.5 llama `sample_frames(video_path)` y
mete el resultado en `metrics["visual_timeline"]`. Solo falta implementar la función en
`backend/app/media/frames.py`:

1. `ffprobe` → duración del video.
2. `ffmpeg -i video -vf "select='gt(scene,0.4)',showinfo"` (cambios de escena) o 1 frame
   cada N segundos a JPGs temporales.
3. Clasifica cada frame con **Claude multimodal** (visión, mensaje con imagen) en:
   `slides | whiteboard | screen_share | none`. Esto requiere extender `LLMProvider` con
   un método que acepte imágenes (hoy `complete(prompt)` es solo texto).
4. Colapsa frames consecutivos del mismo tipo en segmentos `{start, end, type}`.
5. **Honestidad:** si no clasificas con confianza, deja `[]` (no inventes segmentos). El
   contrato y la cinta del frontend aceptan `visual_timeline: []`.

---

## 6. Mapa de archivos (dónde está cada cosa)

```
backend/app/
  config.py            # Settings (env). Nuevo: STANDARDS_DIR + .standards_dir
  pipeline/runner.py   # orquestación 7 etapas (incl. descarga URL + frames)
  media/
    download.py        # NUEVO: descarga URL/Drive → disco (normaliza Drive)
    audio.py           # ffmpeg: extrae audio (degrada si no hay ffmpeg)
    frames.py          # seam visual_timeline (devuelve [] — implementar §5)
  providers/
    transcription/{base,assemblyai,fake}.py
    llm/{base,claude,fake}.py
    factory.py         # lee env → provider concreto
  rubrics/__init__.py  # registry: built-ins + JSON de standards/ (JSON manda)
  analysis/{prompt,analyzer,validator}.py
  metrics/{talk_ratio,questions,pace,runner}.py
  repository.py        # patrón repo (incl. update_recording_ref)
  api/sessions.py      # endpoints /api (lee file Y url en multipart)
backend/standards/     # ★ RUTA DE ESTÁNDARES (fuente de verdad editable)
  README.md            # cómo cargar el marco oficial
  minedu_mbdd.json     # MBDD (verified:false → reemplazar por oficial)
frontend/src/          # React+Vite+TS; types.ts espejo del contrato; mocks/
```

---

## 7. Checklist de "listo para demo" (del prompt §17–18)

- [ ] 1 clase real (español, audio limpio, 2+ voces) procesada y `ready`.
- [ ] `ASSEMBLYAI_API_KEY` y `ANTHROPIC_API_KEY` probadas desde el backend.
- [ ] Estándares MBDD verificados contra el documento oficial (`verified:true`).
- [ ] Validador acepta la mayoría de citas (prompt afinado 2–3 iteraciones).
- [ ] TeacherDashboard: evidencia clickeable hace seek en el reproductor.
- [ ] Serie temporal con 2–3 sesiones de ejemplo para que la tendencia se vea.
- [ ] Deploy Railway: `ffmpeg` presente y `$PORT` respetado; `/api/health` OK.
- [ ] `sample_session.json` de respaldo + código congelado 2h antes.

---

## 8. Gotchas conocidos

- **Sin keys = todo fake** (transcript y análisis precocinados). No es bug.
- **Drive privado** → la descarga falla con mensaje claro; el link debe ser "Cualquiera
  con el enlace". Link de sala de Meet en vivo NO sirve (usa la grabación en Drive).
- **El registry de rúbricas se cachea** (`_REGISTRY_CACHE`). Tras editar un JSON de
  `standards/`, reinicia el server o llama `reload_registry()`.
- **SQLite en Railway es efímero** — si reinicia, se pierde. Monta volumen si necesitas
  persistencia (o pre-procesa la demo y ten el JSON de respaldo).
- **Python global vs venv:** usa SIEMPRE `backend/.venv`. El Python global tiene una
  versión de FastAPI incompatible (falla al importar la app).
- **El validador solo valida `evidence`** de dimensiones; `strengths`/`improvements`
  pasan sin validar. Si quieres rigor total, extiéndelo a esas secciones.
