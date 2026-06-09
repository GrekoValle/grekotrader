# GrekoTrader v19.3 — Changelog
**Fecha:** 09-Jun-2026 | **Archivo:** reversal_modelo_v19_1.py

---

## 🐛 Bugs Corregidos

### Score MVALLE
- **Candidatos MVALLE mostraba tickets incorrectos** (AVAV/RDW/INFQ con WR 35%)
  - Causa: `_re_result` se calculaba DESPUÉS de que `_rec` lo usaba → siempre devolvía fallback 50 → `_rec = "✅ Entrar"` aunque WR fuera 35%
  - Fix: movido `calcular_riesgo_extension()` ANTES del bloque `_rec` en NBIS y Momentum
  - Impacto: Candidatos ahora solo muestra tickets con veredicto real ✅ ENTRAR o ⚡ PARCIAL

- **Botón 🔍 Análisis IA aparecía en tickets sin veredicto ENTRAR** (KTOS Score 13, LDOS Score 14)
  - Fix: botón solo visible cuando `_vered.startswith(("✅","⚡"))` — no por Score >= 12

- **`NameError: name 'os' is not defined`** en Tab Noticias IA
  - Fix: `os.path.join(...)` → `_os_nc.path.join(...)` usando alias correcto

- **`NameError: name '_reg_mercado' is not defined`** en botón N10
  - Fix: 4 referencias a `_reg_mercado.get(...)` → `st.session_state.get("mercado_data",{}).get("regimen","NEUTRO")`

### N10 / Probabilidad — JSON Parse Error (5 iteraciones resueltas)
- **Causa raíz:** `max_tokens=280/380` insuficiente cuando `web_search` activo consume ~400 tokens propios → JSON truncado antes del `}` final
- **Fix 1:** `max_tokens` subido a `800` en ambas funciones (`_llamar_n10_ia` y `_llamar_prob_entrada`)
- **Fix 2:** Sistema de parsing con 3 capas:
  1. `json.loads()` directo
  2. Reparación de JSON truncado (cierra llaves faltantes, elimina último campo incompleto)
  3. Extracción campo a campo con regex como último recurso
- **Fix 3:** System prompt simplificado sin comillas escapadas complejas que confundían al modelo

### Tab Noticias IA
- **`ValueError: Unknown format code 'f' for str`** — múltiples instancias
  - Fix: casting seguro `_pc_s = float(precio_entrada) if precio_entrada else 0.0` antes de f-strings
  - Reemplazado `:.2f` por `round()` integrado en todos los campos del prompt

---

## ✨ Nuevas Funcionalidades

### Regla RSI × DD (validada con 9 casos reales)
**Fundamento:** análisis de HPE/DELL/APTV (ganadores) vs BRZE/TEAM/PLTR (perdedores)

| Zona | Condición | Penalización | Patrón |
|------|-----------|-------------|--------|
| Sobreextensión | RSI > 73 + DD < -25% | -2pts | BRZE/TEAM/PLTR |
| Zona gris | RSI > 73 + DD -10% a -25% | -1pt | FCEL |
| Momentum genuino | RSI > 73 + DD > -10% | 0pts | HPE/DELL |
| Normal | RSI ≤ 73 | 0pts | APTV/RCAT/RUN |

Badge visible en cada card:
- `⚠️ RSI×DD: RSI 76 + DD -36% → sobreextensión rebote · -2pts`
- `✅ RSI×DD: RSI 76 + DD -4% → momentum genuino · sin penalización`

### Penalización Beta (validada con dataset completo)
**Fundamento:** ganadores promedio beta 0.94 vs perdedores promedio beta 2.28

| Beta | Penalización | Ejemplos |
|------|-------------|---------|
| ≥ 2.5 | -3pts ⚡ | PLTR, QUBT |
| ≥ 1.8 | -2pts ⚡ | BRZE, TEAM, FCEL |
| ≥ 1.4 | -1pt 🟡 | zona cautela |
| < 1.4 | 0pts ✅ | HPE, DELL, APTV |

- Nueva columna **Beta** en tabla Score MVALLE con color por nivel
- Badge informativo en cada card
- `beta` ahora extraído de `yfinance.info` y guardado en `_fund_sc`

### Separación visual entre tickets
- `margin-top: 16px` entre cada ticket en NBIS y Momentum
- Primer ticket sin margen (pegado al header de tabla)

---

## 🏗️ Arquitectura — Cambios Estructurales

### Tab Noticias IA — Arquitectura con Alertas
- **Eliminado:** Sección 2 Greko (65 posiciones paper → tokens innecesarios)
- **Nuevo flujo:**
  1. Scan técnico rápido yfinance (~10 seg, $0.00) para las 27 posiciones MVALLE+Amparito
  2. Detecta 6 tipos de alerta sin IA: caída >3% hoy, pérdida >7%, RSI >78, M1, >20 días, ganancia >20%
  3. Muestra resumen compacto de posiciones estables (sin IA)
  4. Solo posiciones alertadas tienen botón [🔍 Analizar] individual
  5. Botón maestro [🔍 Analizar las N alertas] en paralelo

**Costo real:**
- Días sin alertas: $0.00
- Días con alertas: ~$0.003 por posición analizada

### Modo Desarrollo (toggle 🛠️ Dev)
- Toggle en Tab Noticias IA que desactiva todas las llamadas IA
- Permite recargar el modelo sin consumir tokens durante desarrollo
- Caché en disco (`noticias_cache.json`) persiste 8h entre recargas

### Paralelismo
- **Noticias IA:** `ThreadPoolExecutor(max_workers=4)` → de 10 min a ~2 min para 27 posiciones
- **Botón 🔍 Análisis IA:** N10 + Probabilidad en paralelo con 2 workers → de ~60s a ~30s

### Botón Unificado
- **Antes:** 2 botones separados [N10 Análisis IA] + [🔮 ¿Probabilidad de éxito?]
- **Ahora:** 1 botón [🔍 Análisis IA · TICKER] ejecuta ambos en paralelo
- Aplica en NBIS y Momentum

---

## 📊 Validaciones del Modelo (sesión actual)

### Dataset cerrado analizado (18 posiciones)
| Fase | N | WR | Prom |
|------|---|----|------|
| M1 | 7 | 14% | -1.7% |
| M2 | 5 | 80% | +10.9% |
| M3 | 1 | 100% | +24.5% |
| Momentum | 5 | 60% | +7.8% |

### Lecciones implementadas
1. **Earn 3-15 días = catalizador más poderoso** (WR 100% en 8 casos)
2. **M1 deshabilitado confirma:** 14% WR en 7 casos cerrados
3. **Biotech clinical-stage sin catalizador** = señal inválida (KROS -11.1%)
4. **Beta alta amplifica pérdidas** más que ganancias en contexto adverso
5. **Segunda posición en M1 post-rally prohibida** (EL $88 → -11.5%)

---

## 🔧 Configuración

### secrets.toml — Corrección crítica
```toml
# ANTHROPIC_API_KEY debe ir FUERA de [gcp_service_account]
# Al inicio del archivo, antes de cualquier [sección]

ANTHROPIC_API_KEY = "sk-ant-api03-..."

[gcp_service_account]
# Solo credenciales de Google aquí

[anthropic]
api_key = "sk-ant-api03-..."  # fallback
```

### Modelos API
- `claude-sonnet-4-20250514` → **`claude-sonnet-4-6`** (corrige error 404)

---

## 📁 Archivos del repositorio

| Archivo | Descripción |
|---------|-------------|
| `reversal_modelo_v19_1.py` | Modelo principal Streamlit (18,672 líneas) |
| `calcular_Y_retroactivo.py` | Calcula Y_5D/Y_10D/Y_20D de posiciones históricas |
| `calcular_regresion.py` | Regresión logística cuando N≥80 posiciones |
| `CHANGELOG_v19_3.md` | Este archivo |

---

*GrekoTrader v19.3 · Patrón NBIS · 3 Momentos · Python/Streamlit*
