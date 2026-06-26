# Estándares pedagógicos — fuente de verdad editable

Esta carpeta es **la ruta oficial de los estándares** que usa Mirador para
evaluar las clases. Aquí viven los marcos como **datos en JSON**, fuera del
código Python, para que se puedan corregir sin tocar la app.

**Ruta:** `backend/standards/`
**Se configura con:** la variable de entorno `STANDARDS_DIR` (si está vacía, se
usa esta carpeta por defecto).

## Cómo funciona

Al arrancar, el registro de marcos (`backend/app/rubrics/__init__.py`) carga:

1. Los marcos **built-in** del código (`minedu_mbdd`, `oecd_talis`) como fallback.
2. **Todos los `*.json` de esta carpeta**, que **sobrescriben** al built-in con el
   mismo `framework_id`.

Es decir: **lo que pongas aquí manda**. Para usar un marco editas su JSON, no el
código.

## Forma del archivo

```jsonc
{
  "framework_id": "minedu_mbdd",
  "framework_name": "Marco de Buen Desempeño Docente (MINEDU)",
  "source": "Cita oficial: RM N.º ..., MINEDU (Perú). Pega aquí la referencia exacta.",
  "verified": false,                    // pon true SOLO cuando el texto sea verbatim del documento oficial
  "dimensions": [
    {
      "dimension_id": "dominio_disciplinar",
      "name": "...",
      "description": "...",
      "look_for": "...",
      "observable_from_recording": true   // false = no evaluable desde una sola grabación
    }
  ]
}
```

## Importante (anti-alucinación)

El texto sembrado hoy en `minedu_mbdd.json` es una **paráfrasis no verificada**
(`"verified": false`). Para que el sistema pueda afirmar que sigue el MBDD
oficial:

1. Abre el documento oficial del MBDD (la RM del MINEDU).
2. Reemplaza `name` / `description` por el texto de los desempeños/competencias
   oficiales.
3. Rellena `source` con la cita exacta (RM, página) y pon `"verified": true`.

`observable_from_recording: false` se queda en las dimensiones que NO pueden
evidenciarse desde el video de una sola clase (p. ej. planificación previa); el
analizador las reporta como no evaluables en vez de inventar un puntaje.
