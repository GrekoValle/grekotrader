# GrekoTrader v19.3 — Changelog Final Sesión 2 (parte 2)
**Fecha:** 10-Jun-2026 | **Archivo:** reversal_modelo_v19_1.py (19,935 líneas)

> Continuación de `CHANGELOG_v19_3_sesion2.md`. Cubre los 3 últimos fixes
> de la sesión, posteriores al primer commit del día.

---

## 🐛 Bugs Corregidos (parte 2)

### 1. Backtest C-Score leía un Sheet vacío
- **Problema:** el botón "🔬 Backtest C-Score" arrojaba "no están los
  tickets en un Google Sheet definido"
- **Causa:** leía `GrekoTrader_Trades_Reales` (sheet sin uso real)
  en vez de `GrekoTrader_Posiciones_Greko` (donde viven las posiciones
  cerradas con `Fecha_Salida` + `Resultado_Pct`)
- **Fix:**
  - Ahora lee `GrekoTrader_Posiciones_Greko` como fuente principal
  - `GrekoTrader_Trades_Reales` como fuente adicional (si tiene datos, se concatena)
  - Acepta tanto `Fecha_Señal` como `Fecha_Entrada` como columna de fecha de entrada
  - Filtro confirmado: solo procesa filas donde **columna O (Fecha_Salida)** tiene dato — posiciones activas (vacías) se excluyen automáticamente
- **Nuevo:** selector de rango de fechas — "Todas" / "Últimos 30/60/90 días"
  (filtra por fecha de **salida**, default "Todas")

### 2. Botón "Analizar las N alertas con IA" → Error 429 (rate_limit)
- **Problema:** con 10 alertas, la API de Anthropic devolvía
  `Error code: 429 - rate_limit` y en logs aparecía
  `missing ScriptRunContext` repetidamente
- **Causa 1:** `ThreadPoolExecutor(max_workers=4)` → 4 llamadas
  simultáneas con `web_search` saturaban el rate limit
- **Causa 2:** `_prog.progress(...)` (barra de progreso de Streamlit)
  se llamaba DESDE los hilos secundarios, que no tienen
  `ScriptRunContext` → warning en cada actualización
- **Fix:**
  - `max_workers`: 4 → **2** (menos llamadas simultáneas)
  - Cliente Anthropic con `timeout=45.0`
  - **Retry automático con backoff** si la respuesta es 429:
    intento 1 falla → espera 3s → intento 2 falla → espera 6s →
    intento 3 → si falla, usa fallback (no crashea)
  - La barra de progreso ahora se actualiza desde el **hilo principal**
    (dentro del loop `as_completed`), no desde `_procesar_una`
    → elimina el warning `missing ScriptRunContext`

### 3. Selector duplicado "MVALLE" / "Mauri" en Tab Noticias IA
- **Problema:** el radio "Portfolio a analizar" mostraba
  `[MVALLE] [Greko] [Mauri] [Amparito]` — dos opciones
  apuntando al mismo Sheet (`GrekoTrader_Posiciones_Mauri`)
- **Fix:** eliminada la opción "MVALLE" duplicada → queda
  `[Mauri] [Greko] [Amparito]`

---

## 📁 Archivos para subir

| Archivo | Cambios |
|---------|---------|
| `reversal_modelo_v19_1.py` | 3 fixes descritos arriba (19,935 líneas) |
| `CHANGELOG_v19_3_sesion2_final.md` | Este archivo |
| `TAREAS_PENDIENTES_v19_3.md` | Plan de validación C-Score (no es código, referencia) |

---

## ✅ Commit sugerido

```bash
git add reversal_modelo_v19_1.py CHANGELOG_v19_3_sesion2_final.md TAREAS_PENDIENTES_v19_3.md
git commit -m "fix: backtest lee Posiciones_Greko + selector rango fechas; 429 rate_limit con retry+backoff (max_workers 4→2); elimina selector duplicado MVALLE/Mauri"
git push
```

---

*GrekoTrader v19.3 · Sesión 2 completa · Próximo hito: validar C-Score con el Backtest*
