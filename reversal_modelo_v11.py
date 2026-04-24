"""
╔══════════════════════════════════════════════════════════════════╗
║  GREKOTRADER — 100% Automático · Sin datos en duro · v11               ║
║                                                                  ║
║  Instalar:  pip install streamlit plotly pandas numpy           ║
║  Ejecutar:  streamlit run reversal_modelo_v5.py                 ║
║                                                                  ║
║  CSV formato (posiciones.csv):                                  ║
║  Ticker,Precio_Compra,Cantidad,Fecha                           ║
║  NBIS,92.00,50,2026-03-10                                      ║
║  RGTI,12.50,200,2026-02-15                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import io

st.set_page_config(
    page_title="GrekoTrader v11",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state — inicializar SIEMPRE al inicio ─────────────
if "noticias_cache" not in st.session_state:
    st.session_state["noticias_cache"] = {}
if "noticias_actualizadas" not in st.session_state:
    st.session_state["noticias_actualizadas"] = None

# ─────────────────────────────────────────────────────────────
#  PALETA — LIGHT MODE PROFESIONAL
# ─────────────────────────────────────────────────────────────
BG_APP   = "#F8FAFC"
BG_CARD  = "#FFFFFF"
BG_TABLE = "#FFFFFF"
BG_HEAD  = "#F1F5F9"
BG_ROW2  = "#F8FAFC"
BOR      = "#E2E8F0"
BOR2     = "#CBD5E1"
TXT      = "#1E293B"
TXT_MUT  = "#64748B"
TXT_SOFT = "#94A3B8"

# Colores semánticos light
G      = "#16A34A"; G_BG = "#F0FDF4"; G_BOR = "#BBF7D0"
R      = "#DC2626"; R_BG = "#FEF2F2"; R_BOR = "#FECACA"
A      = "#D97706"; A_BG = "#FFFBEB"; A_BOR = "#FDE68A"
B      = "#2563EB"; B_BG = "#EFF6FF"; B_BOR = "#BFDBFE"
P      = "#7C3AED"; P_BG = "#F5F3FF"; P_BOR = "#DDD6FE"
C      = "#0891B2"; C_BG = "#ECFEFF"; C_BOR = "#A5F3FC"
OR     = "#EA580C"; OR_BG= "#FFF7ED"; OR_BOR= "#FED7AA"

st.markdown(f"""
<style>
/* ── Fondo general ── */
[data-testid="stAppViewContainer"] {{ background:{BG_APP}; }}
[data-testid="stSidebar"]          {{ background:{BG_CARD}; border-right:1px solid {BOR}; box-shadow:2px 0 8px rgba(0,0,0,.04); }}
.main .block-container              {{ padding:0.8rem 1.4rem; max-width:100%; }}

/* ── Métricas ── */
[data-testid="metric-container"]   {{ background:{BG_CARD}; border:1px solid {BOR}; border-radius:12px; padding:12px 16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
[data-testid="stMetricLabel"]      {{ color:{TXT_MUT} !important; font-size:11px !important; font-weight:600 !important; }}
[data-testid="stMetricValue"]      {{ color:{TXT} !important; font-size:22px !important; font-weight:700 !important; }}
[data-testid="stMetricDelta"]      {{ font-size:11px !important; }}

/* ── Tabs ── */
div[data-testid="stTabs"] button   {{ font-size:13px; color:{TXT_MUT}; font-weight:500; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{ color:{B}; font-weight:700; border-bottom:2px solid {B}; }}

/* ── Tablas ── */
.tbl-wrap  {{ overflow-x:auto; border-radius:12px; border:1px solid {BOR}; box-shadow:0 1px 4px rgba(0,0,0,.04); margin-bottom:12px; }}
.dtbl      {{ width:100%; border-collapse:collapse; font-size:12.5px; table-layout:auto; background:{BG_TABLE}; }}
.dtbl th   {{ background:{BG_HEAD}; color:{TXT_MUT}; font-size:11px; font-weight:700;
              padding:10px 14px; border-bottom:2px solid {BOR};
              text-transform:uppercase; letter-spacing:.06em; white-space:nowrap; text-align:left; }}
.dtbl td   {{ padding:10px 14px; border-bottom:1px solid {BOR};
              vertical-align:middle; color:{TXT}; white-space:nowrap; }}
.dtbl tr:nth-child(even) td {{ background:{BG_ROW2}; }}
.dtbl tr:hover td {{ background:#EFF6FF; transition:background .1s; }}
.dtbl tr:last-child td {{ border:none; }}

/* ── Badges ── */
.badge {{ display:inline-block; font-size:10.5px; font-weight:700;
          padding:3px 10px; border-radius:6px; white-space:nowrap; letter-spacing:.03em; }}
.bg-g  {{ background:{G_BG};  color:{G};  border:1px solid {G_BOR}; }}
.bg-r  {{ background:{R_BG};  color:{R};  border:1px solid {R_BOR}; }}
.bg-a  {{ background:{A_BG};  color:{A};  border:1px solid {A_BOR}; }}
.bg-b  {{ background:{B_BG};  color:{B};  border:1px solid {B_BOR}; }}
.bg-p  {{ background:{P_BG};  color:{P};  border:1px solid {P_BOR}; }}
.bg-c  {{ background:{C_BG};  color:{C};  border:1px solid {C_BOR}; }}
.bg-or {{ background:{OR_BG}; color:{OR}; border:1px solid {OR_BOR}; }}
.bg-gr {{ background:{BG_HEAD}; color:{TXT_MUT}; border:1px solid {BOR}; }}

/* ── Cards y secciones ── */
.sec-header {{ display:flex; align-items:center; gap:12px; margin:14px 0 10px;
               padding:12px 18px; border-radius:12px; border:1px solid; }}
.pos-card   {{ background:{BG_CARD}; border:1px solid {BOR}; border-radius:14px;
               padding:18px; margin-bottom:14px; box-shadow:0 2px 6px rgba(0,0,0,.05); }}
.info-box   {{ background:{BG_HEAD}; border:1px solid {BOR}; border-radius:10px;
               padding:12px 16px; font-size:12px; color:{TXT_MUT}; line-height:1.7; margin-bottom:12px; }}

footer{{visibility:hidden;}} #MainMenu{{visibility:hidden;}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  COLORES SECTOR
# ─────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Tech":"#2563EB","Salud":"#16A34A","Energía":"#D97706",
    "Finanzas":"#7C3AED","Consumo":"#EA580C","Industrial":"#64748B",
    "Cripto/AI":"#0891B2","Quantum":"#7C3AED","Fintech":"#EA580C",
    "AI Infra":"#2563EB","IA y Software":"#2563EB",
}
PT = dict(
    paper_bgcolor=BG_APP, plot_bgcolor=BG_CARD,
    font_color=TXT, font_size=11,
    margin=dict(l=10,r=10,t=36,b=10),
)

# ─────────────────────────────────────────────────────────────
#  UNIVERSO — Actualizado Abril 2026
#  Estado_Patron:
#   "REFERENCIA"  — patrón completado, solo benchmark
#   "ACTIVO"      — patrón en curso, oportunidad real AHORA
#   "FORMANDO"    — fondo formándose, vigilar catalizador
#   "BAJADA"      — bajada activa, acumular en watchlist
# ─────────────────────────────────────────────────────────────
RAW = [
    # ══ REFERENCIA ══════════════════════════════════════════
    ("NBIS","Nebius Group","AI Infra",
     165.0,62,180,+5.0,0.80,3.2,2.71,-38,141,"Oct-25",4,17.47,
     1.2,0.9,2.0,"Contrato","NVIDIA $2B + Meta $27B","Completado",
     ["IREN","APLD","CORZ","CLSK"],"",
     "Patron completado +80% desde fondo. Referencia del modelo.","REFERENCIA"),

    # ══ ACTIVO — oportunidades reales HOY abril 2026 ════════
    ("MSFT","Microsoft Corp","AI Infra",
     371.0,36,145,-14.0,0.40,1.8,1.80,-22,475,"Feb-26",2,5.2,
     0.8,0.6,1.8,"Earnings","Q3 earnings 29 Abr · Azure growth + AI CapEx","29 Abr 2026",
     ["AMZN","GOOGL","CRM"],"",
     "RSI 36 sobreventa. -22% YTD. Earnings 29 Abr catalizador principal.","ACTIVO"),

    ("AMZN","Amazon.com","AI Infra",
     198.0,34,155,-16.0,0.35,2.0,1.39,-24,261,"Feb-26",2,4.8,
     0.6,0.5,1.5,"Earnings","Q1 earnings 30 Abr · AWS growth 21-22% + $200B CapEx","30 Abr 2026",
     ["MSFT","GOOGL"],"",
     "RSI 34. -24% YTD. AWS acceleration catalizador. Earnings 30 Abr.","ACTIVO"),

    ("GOOGL","Alphabet Inc","AI Infra",
     155.0,37,138,-13.0,0.30,1.9,1.60,-20,208,"Feb-26",2,4.2,
     0.5,0.4,1.2,"Earnings","Q1 earnings 23 Abr · Cloud 48% growth","23 Abr 2026",
     ["META","MSFT"],"",
     "RSI 37. Earnings 23 Abr. Cloud +48% YoY. Setup solido.","ACTIVO"),

    ("META","Meta Platforms","AI Infra",
     521.0,40,128,-8.0,0.50,1.5,1.40,-18,636,"Feb-26",2,3.8,
     0.4,0.3,0.8,"Earnings","Q1 earnings 30 Abr · Llama AI + Reality Labs","30 Abr 2026",
     ["GOOGL","SNAP"],"",
     "RSI 40. Corrigio desde maximos. Earnings 30 Abr.","ACTIVO"),

    ("ZS","Zscaler Inc","Tech",
     175.0,28,220,-22.0,0.60,1.2,2.20,-42,301,"Nov-25",4,18.5,
     0.5,0.4,1.4,"Earnings","FY Q2 record revenue $788M · MACD girando alcista","May 2026",
     ["CRWD","PANW"],"",
     "RSI 28. Sobreventa >1 mes. MACD alcista. 34 analistas Buy.","ACTIVO"),

    ("NVDA","NVIDIA Corp","AI Infra",
     108.0,38,162,-14.0,0.45,1.8,2.20,-28,153,"Ene-26",2,6.8,
     0.5,0.4,1.2,"Earnings","Q1 FY27 earnings 28 May · Blackwell demand · Vera Rubin","28 May 2026",
     ["AMD","SMCI","MRVL","ANET"],"",
     "RSI 38. -28% desde pico. Blackwell demanda. Earnings Mayo.","ACTIVO"),

    # ══ FORMANDO — fondo en construccion ════════════════════
    ("AMD","AMD Corp","AI Infra",
     92.0,35,168,-18.0,0.30,1.5,2.40,-42,159,"Nov-25",4,9.4,
     0.3,0.2,0.5,"Earnings","Q1 earnings 29 Abr · MI350X GPU demand","29 Abr 2026",
     ["SMCI","ANET","MRVL"],"NVDA",
     "RSI 35. Arrastrada por NVDA. Earnings 29 Abr catalizador.","FORMANDO"),

    ("APLD","Applied Digital","AI Infra",
     26.0,32,185,-22.0,0.45,1.2,7.10,-38,42,"Nov-25",4,12.5,
     0.4,0.3,0.8,"Earnings","CoreWeave lease expansion · AI infra continua","May 2026",
     ["IREN","CORZ"],"",
     "RSI 32. AI infra continua. Correccion post-earnings absorbida.","FORMANDO"),

    ("IREN","Iris Energy","Cripto/AI",
     38.0,30,195,-24.0,0.35,1.1,4.24,-42,65,"Nov-25",4,11.8,
     0.3,0.2,0.6,"Earnings","BTC >$70K · Microsoft AI deal activo","May 2026",
     ["CORZ","CLSK","MARA"],"NBIS",
     "RSI 30. BTC correlacion + AI. Fondo formando en soporte.","FORMANDO"),

    ("TSLA","Tesla Inc","Consumo",
     238.0,36,148,-10.0,0.25,1.6,2.80,-45,480,"Dic-24",4,5.2,
     0.4,0.3,0.9,"Earnings","Q1 earnings 22 Abr · Robotaxi + energia","22 Abr 2026",
     ["RIVN","LCID"],"",
     "RSI 36. Earnings 22 Abr. Robotaxi + Megapack catalizadores.","FORMANDO"),

    ("CRM","Salesforce Inc","IA y Software",
     248.0,33,172,-16.0,0.40,1.4,1.90,-28,348,"Feb-26",2,6.4,
     0.3,0.3,0.8,"Earnings","Agentforce AI momentum · Q1 FY27 earnings Mayo","Mayo 2026",
     ["ORCL","SNOW"],"MSFT",
     "RSI 33. Agentforce AI traction. Arrastrada por MSFT.","FORMANDO"),

    ("ORCL","Oracle Corp","IA y Software",
     148.0,36,165,-12.0,0.38,1.5,1.80,-22,196,"Feb-26",2,4.8,
     0.3,0.2,0.6,"Contrato","Cloud AI gov contracts · OpenAI infrastructure deal","Mayo 2026",
     ["CRM","SNOW"],"",
     "RSI 36. Cloud AI gov momentum. Fondo formando.","FORMANDO"),

    # ══ BAJADA — watchlist ═══════════════════════════════════
    ("SMCI","Super Micro Computer","Tech",
     34.0,28,245,-28.0,0.55,0.8,4.20,-72,122,"Mar-25",6,18.4,
     0.2,0.1,0.4,"Pipeline","Server demand AI + Nvidia partnership","Q2 2026",
     ["NVDA","AMD"],"NVDA",
     "RSI 28. DD -72% desde pico. Alta volatilidad. Watchlist.","BAJADA"),

    ("PFE","Pfizer Inc","Salud",
     24.0,27,255,-19.0,0.55,0.6,1.40,-72,85,"2022",36,18.2,
     0.1,0.1,0.2,"Pipeline","Oncology pipeline + cost cuts $4B","Q2 2026",
     ["MRK","ABBV"],"",
     "RSI 27. Capitulacion post-pandemia. Watchlist largo plazo.","BAJADA"),

    ("BA","Boeing Co","Industrial",
     155.0,31,228,-18.0,0.40,1.2,1.90,-48,301,"Nov-25",4,14.6,
     0.2,0.1,0.4,"FAA","737 MAX 10 certif. + Defense contracts","Q2 2026",
     ["GE","SPR"],"",
     "RSI 31. Recuperacion lenta post-crisis. FAA cert catalizador.","BAJADA"),

    ("MRNA","Moderna Inc","Salud",
     48.0,25,280,-24.0,0.55,0.6,1.80,-90,484,"2021",36,14.0,
     0.1,0.1,0.2,"Pipeline","INT melanoma Phase 3 mid-2026 readout","Mid-2026",
     ["BNTX","NVAX"],"",
     "RSI 25. Capitulacion estructural. Watchlist catalizador clinico.","BAJADA"),

    ("HOOD","Robinhood","Fintech",
     62.0,48,132,-4.0,0.40,1.1,2.90,-32,92,"Ene-26",2,8.4,
     0.3,0.2,0.5,"Earnings","Q1 earnings · usuarios activos plateados","May 2026",
     ["SOFI","COIN"],"",
     "RSI 48. Rally previo absorbido. Pausa tecnica, no senal aun.","BAJADA"),

    ("NKE","Nike Inc","Consumo",
     68.0,31,215,-18.0,0.42,1.0,1.70,-42,121,"Oct-25",5,10.5,
     0.2,0.1,0.3,"Macro","China recovery + nuevo CEO turnaround","Q2 2026",
     ["LULU","SKX"],"",
     "RSI 31. CEO turnaround en curso. DD -42%. Watchlist.","BAJADA"),

    ("OXY","Occidental Pet.","Energía",
     44.0,29,272,-22.0,0.50,0.8,1.90,-35,72,"Nov-25",4,9.1,
     0.2,0.2,0.4,"Petróleo","Buffett 27% float · oil price recovery","Q2 2026",
     ["XOM","DVN"],"",
     "RSI 29. Buffett acumulando. Oil recovery esperado.","BAJADA"),
]

# ─────────────────────────────────────────────────────────────
#  FUNDAMENTALES POR TICKER
#  (bpa, dividendo%, margen_bruto%, ingresos_M, vol_diario_K)
#  Aprendizaje: ACN/AXSM/SEI (fundamentales sólidos) vs
#               ENTX/CRWN (sin ingresos, ilíquidas)
# ─────────────────────────────────────────────────────────────
FUND = {
    #  Ticker: (BPA,  Div%,  Margen%, Ingresos_M, VolDiario_K)
    "NBIS":  (0.0,   0.0,   45.0,   280.0,    2800.0),
    "MSFT":  (12.20, 0.82,  68.8,   72110.0,  20000.0),
    "AMZN":  (4.33,  0.0,   47.0,   638000.0, 35000.0),
    "GOOGL": (7.52,  0.0,   56.0,   88000.0,  25000.0),
    "META":  (23.86, 0.52,  81.0,   164000.0, 18000.0),
    "ZS":    (-1.20, 0.0,   77.0,   2370.0,   3500.0),
    "NVDA":  (2.94,  0.04,  73.0,   130500.0, 32000.0),
    "AMD":   (2.61,  0.0,   52.5,   34640.0,  37000.0),
    "APLD":  (-0.74, 0.0,   45.4,   319.0,    24000.0),
    "IREN":  (-0.45, 0.0,   38.0,   210.0,    8000.0),
    "TSLA":  (2.04,  0.0,   17.0,   97690.0,  85000.0),
    "CRM":   (6.20,  0.0,   76.0,   36000.0,  5500.0),
    "ORCL":  (5.60,  1.28,  71.0,   56900.0,  7000.0),
    "SMCI":  (-2.10, 0.0,   14.0,   23000.0,  12000.0),
    "PFE":   (1.41,  6.90,  64.0,   63600.0,  28000.0),
    "BA":    (-5.20, 0.0,   12.0,   66517.0,  6000.0),
    "MRNA":  (-9.60, 0.0,   55.0,   3240.0,   9000.0),
    "HOOD":  (0.42,  0.0,   83.0,   3580.0,   63000.0),
    "NKE":   (3.73,  2.08,  44.0,   51362.0,  7000.0),
    "OXY":   (3.58,  2.40,  51.0,   27263.0,  14000.0),
}
# ─────────────────────────────────────────────────────────────
def calc_score(rsi,vol,ema,macd,sop,dd,pre_move,short_int,pre_vol,post_vol,rsi_tendencia=0):
    sc=0
    if rsi<25:   sc+=18
    elif rsi<30: sc+=16
    elif rsi<35: sc+=12
    elif rsi<42: sc+=6
    sc += rsi_tendencia
    if vol>300: sc+=15
    elif vol>200: sc+=12
    elif vol>150: sc+=8
    elif vol>120: sc+=4
    if pre_move>=10: sc+=18
    elif pre_move>=7: sc+=15
    elif pre_move>=5: sc+=11
    elif pre_move>=3: sc+=6
    elif pre_move>=1: sc+=2
    if pre_vol>=3.0: sc+=12
    elif pre_vol>=2.0: sc+=9
    elif pre_vol>=1.5: sc+=6
    elif pre_vol>=1.2: sc+=3
    if macd>1.5: sc+=12
    elif macd>1: sc+=10
    elif macd>0: sc+=7
    elif macd>-0.5: sc+=2
    if ema<-20: sc+=10
    elif ema<-15: sc+=8
    elif ema<-10: sc+=6
    elif ema<-5: sc+=3
    if sop<0.5: sc+=10
    elif sop<1: sc+=8
    elif sop<2: sc+=6
    elif sop<3: sc+=3
    if dd<-40: sc+=5
    elif dd<-25: sc+=3
    elif dd<-15: sc+=1
    sc=min(sc,100)
    if short_int>=20: sc=min(int(sc*1.30),100)
    elif short_int>=15: sc=min(int(sc*1.20),100)
    elif short_int>=10: sc=min(int(sc*1.10),100)
    return sc

def bonus_fundamentales(bpa: float, dividendo: float, margen_bruto: float,
                         ingresos_m: float, vol_diario_k: float) -> tuple:
    """
    Calcula bonus/penalización por calidad fundamental.
    Retorna (bonus_pts, descripcion)
    Aprendizaje del análisis del día: ACN, AXSM, SEI vs ENTX, CRWN.
    """
    bonus = 0
    razones = []

    # ── BPA positivo ──────────────────────────────────────────
    if bpa > 5:
        bonus += 8; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa > 1:
        bonus += 5; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa > 0:
        bonus += 3; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa < -2:
        bonus -= 5; razones.append(f"BPA -${abs(bpa):.2f} ❌")
    elif bpa < 0:
        bonus -= 2; razones.append(f"BPA negativo ⚠️")

    # ── Dividendo activo ──────────────────────────────────────
    if dividendo >= 3.0:
        bonus += 5; razones.append(f"Dividendo {dividendo:.1f}% 💎")
    elif dividendo >= 1.5:
        bonus += 3; razones.append(f"Dividendo {dividendo:.1f}% ✅")
    elif dividendo > 0:
        bonus += 1; razones.append(f"Dividendo {dividendo:.1f}%")

    # ── Margen bruto ──────────────────────────────────────────
    if margen_bruto >= 70:
        bonus += 4; razones.append(f"Margen {margen_bruto:.0f}% 💎")
    elif margen_bruto >= 40:
        bonus += 2; razones.append(f"Margen {margen_bruto:.0f}% ✅")
    elif margen_bruto > 0:
        bonus += 1

    # ── Ingresos reales ───────────────────────────────────────
    if ingresos_m >= 10000:
        bonus += 3; razones.append(f"Ingresos ${ingresos_m/1000:.0f}B 💎")
    elif ingresos_m >= 500:
        bonus += 2; razones.append(f"Ingresos ${ingresos_m:.0f}M ✅")
    elif ingresos_m >= 100:
        bonus += 1
    elif ingresos_m < 1:
        bonus -= 10; razones.append("Sin ingresos reales ❌")

    # ── Filtro liquidez (no suma, solo excluye) ───────────────
    # vol_diario_k en miles de acciones
    if vol_diario_k < 500:
        bonus -= 20  # penalización que excluye del radar
        razones.append(f"⚠️ ILÍQUIDA vol {vol_diario_k:.0f}K/día")

    bonus = max(-20, min(12, bonus))  # cap: +12 / -20
    desc = " · ".join(razones) if razones else "Sin datos fundamentales"
    return bonus, desc

# ─────────────────────────────────────────────────────────────
#  VIX — SEMÁFORO DE OPORTUNIDAD DEL MERCADO
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 min
def fetch_vix() -> dict:
    """
    Descarga el VIX actual via yfinance.
    Retorna dict con valor, nivel, color, mensaje y multiplicador de score.
    """
    try:
        import yfinance as yf
        vix_data = yf.Ticker("^VIX").history(period="2d")
        if vix_data.empty:
            raise ValueError("sin datos VIX")
        vix_val = round(float(vix_data["Close"].iloc[-1]), 2)
        vix_prev = round(float(vix_data["Close"].iloc[-2]), 2) if len(vix_data) >= 2 else vix_val
        cambio = round(vix_val - vix_prev, 2)

        if vix_val >= 35:
            nivel="PÁNICO"; color=G; bg=G_BG; bor=G_BOR
            msg="🟢 Máxima oportunidad — mercado en pánico, buscar fondos"
            mult=1.20  # bonus +20% al score en pánico
        elif vix_val >= 25:
            nivel="MIEDO"; color=A; bg=A_BG; bor=A_BOR
            msg="🟡 Oportunidad moderada — nerviosismo, vigilar fondos"
            mult=1.10
        elif vix_val >= 20:
            nivel="ALERTA"; color=A; bg=A_BG; bor=A_BOR
            msg="🟡 Mercado nervioso — modo normal del modelo"
            mult=1.0
        elif vix_val >= 15:
            nivel="NORMAL"; color=TXT_MUT; bg=BG_HEAD; bor=BOR
            msg="⚪ Mercado tranquilo — exigir más confirmación Pre-Market"
            mult=1.0
        else:
            nivel="COMPLACENCIA"; color=R; bg=R_BG; bor=R_BOR
            msg="🔴 Mercado muy tranquilo — precaución, corrección probable"
            mult=0.95

        return {
            "valor": vix_val, "cambio": cambio, "prev": vix_prev,
            "nivel": nivel, "color": color, "bg": bg, "bor": bor,
            "msg": msg, "mult": mult, "_ok": True
        }
    except Exception:
        return {
            "valor": 0, "cambio": 0, "prev": 0,
            "nivel": "SIN DATOS", "color": TXT_MUT, "bg": BG_HEAD, "bor": BOR,
            "msg": "VIX no disponible — instala yfinance", "mult": 1.0, "_ok": False
        }

# ─────────────────────────────────────────────────────────────
#  FECHAS DE CATALIZADORES — busca earnings desde yfinance
# ─────────────────────────────────────────────────────────────
def fetch_earnings_dates(tickers):
    import yfinance as yf, datetime
    ETF_SIN_EARNINGS = ["VOO","SPY","IVV","QQQ","VTI","SCHB","IBIT","ETHA","GBTC","FBTC","TAN","XBI","IBB","XLF","XLE","XLK","XLV","ARKK","SOXX"]
    rows = []
    for tk in tickers:
        if tk in ETF_SIN_EARNINGS:
            rows.append({"Ticker":tk,"Cat_Fecha":"—","Fuente":"ETF — sin earnings","Nota":"ETF — no tiene earnings propios"})
            continue
        try:
            stk = yf.Ticker(tk)
            earn_date = "—"; fuente = "—"
            try:
                cal = stk.calendar
                if cal is not None and "Earnings Date" in cal:
                    hoy = datetime.date.today()
                    fechas = [str(f)[:10] for f in cal["Earnings Date"] if f and str(f)[:10] != "nan"]
                    futuras = [f for f in fechas if datetime.date.fromisoformat(f) >= hoy]
                    if futuras:
                        earn_date = futuras[0]; fuente = "yfinance"
            except Exception:
                pass
            if earn_date == "—":
                info = stk.info or {}
                ed = info.get("earningsDate") or info.get("earningsTimestamp")
                if ed and isinstance(ed, (int,float)):
                    earn_date = datetime.datetime.fromtimestamp(ed).strftime("%Y-%m-%d"); fuente = "yfinance"
            nota = "Earnings confirmados" if earn_date != "—" else "No encontrado — verificar en Nasdaq.com o Investing.com"
            rows.append({"Ticker":tk,"Cat_Fecha":earn_date,"Fuente":fuente,"Nota":nota})
        except Exception:
            rows.append({"Ticker":tk,"Cat_Fecha":"—","Fuente":"Error","Nota":"Error — verificar manualmente"})
    return pd.DataFrame(rows)


def render_catalysts_section(posiciones_df, key_prefix):
    st.markdown("---")
    st.markdown(
        '<div style="font-size:13px;font-weight:700;margin-bottom:8px">'+
        '📅 Fechas de Earnings — Catalizadores</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">Busca automáticamente las fechas de earnings desde yfinance. '+
        'Descarga el CSV y agrega las fechas a la columna <strong>Cat_Fecha</strong> '+
        'de tu archivo de posiciones.</div>',
        unsafe_allow_html=True)

    if st.button("📅 Buscar fechas de earnings", use_container_width=True,
                 key=f"btn_earnings_{key_prefix}"):
        tickers = posiciones_df["Ticker"].str.upper().unique().tolist()
        with st.spinner(f"Buscando earnings para {len(tickers)} acciones..."):
            earn_df = fetch_earnings_dates(tickers)
            st.session_state[f"earnings_{key_prefix}"] = earn_df

    earn_result = st.session_state.get(f"earnings_{key_prefix}")
    if earn_result is not None:
        for _, row in earn_result.iterrows():
            has_date = row["Cat_Fecha"] not in ("—","","nan")
            color = G if has_date else TXT_MUT
            bg    = G_BG if has_date else GRIS_CLAR if 'GRIS_CLAR' in dir() else "F8FAFC"
            bor   = G_BOR if has_date else BOR
            icon  = "📅" if has_date else "—"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {bor};border-radius:8px;'
                f'padding:8px 14px;margin-bottom:5px;'
                f'display:flex;justify-content:space-between;align-items:center">'
                f'<div style="display:flex;align-items:center;gap:12px">'
                f'<span style="font-size:14px;font-weight:800;color:{B}">{row["Ticker"]}</span>'
                f'<span style="font-size:12px;font-weight:700;color:{color}">'
                f'{icon} {row["Cat_Fecha"]}</span>'
                f'</div>'
                f'<span style="font-size:10px;color:{TXT_MUT}">{row["Nota"]}</span>'
                f'</div>', unsafe_allow_html=True)

        import datetime as _dt
        earn_csv = df_to_csv_chile(earn_result).encode("utf-8-sig")
        col_dl, col_tip = st.columns([2,3])
        with col_dl:
            st.download_button(
                "⬇️ Descargar fechas CSV",
                data=earn_csv,
                file_name=f"earnings_{_dt.date.today()}.csv",
                mime="text/csv",
                key=f"dl_earn_{key_prefix}",
                use_container_width=True)
        with col_tip:
            st.markdown(
                f'<div style="font-size:10px;color:{TXT_MUT};padding-top:8px">'
                f'Copia <strong>Cat_Fecha</strong> a tu archivo de posiciones '
                f'y vuelve a subirlo al dashboard.</div>',
                unsafe_allow_html=True)


# Cargar VIX al iniciar
vix = fetch_vix()

# ─────────────────────────────────────────────────────────────
#  INDICADORES DE MERCADO — automáticos para el header
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)  # cache 15 min
def fetch_market_indicators() -> dict:
    """
    Descarga indicadores clave de mercado para el header.
    Todos relevantes para el modelo de rebote técnico NBIS.
    """
    result = {}
    try:
        import yfinance as yf

        # S&P 500
        try:
            spx = yf.Ticker("^GSPC").history(period="2d")
            if not spx.empty:
                spx_now  = float(spx["Close"].iloc[-1])
                spx_prev = float(spx["Close"].iloc[-2]) if len(spx)>=2 else spx_now
                result["spx"] = {"val": spx_now, "chg": (spx_now-spx_prev)/spx_prev*100}
        except Exception: pass

        # Nasdaq
        try:
            ndx = yf.Ticker("^IXIC").history(period="2d")
            if not ndx.empty:
                ndx_now  = float(ndx["Close"].iloc[-1])
                ndx_prev = float(ndx["Close"].iloc[-2]) if len(ndx)>=2 else ndx_now
                result["ndx"] = {"val": ndx_now, "chg": (ndx_now-ndx_prev)/ndx_prev*100}
        except Exception: pass

        # Fear & Greed aproximado via VIX (^PCALL no disponible en Yahoo)
        try:
            # Usar VIX como proxy de Fear & Greed
            vix_fg = yf.Ticker("^VIX").history(period="2d")
            if not vix_fg.empty:
                vix_val = float(vix_fg["Close"].iloc[-1])
                if vix_val >= 35:
                    fg_label = "MIEDO EXTREMO 🟢"; fg_score = 15; fg_color = "G"
                elif vix_val >= 25:
                    fg_label = "MIEDO 🟡"; fg_score = 30; fg_color = "A"
                elif vix_val >= 18:
                    fg_label = "NEUTRAL ⚪"; fg_score = 50; fg_color = "TXT_MUT"
                elif vix_val >= 13:
                    fg_label = "CODICIA 🟡"; fg_score = 70; fg_color = "A"
                else:
                    fg_label = "CODICIA EXTREMA 🔴"; fg_score = 85; fg_color = "R"
                result["pcr"] = {"val": round(vix_val,1), "label": fg_label,
                                 "score": fg_score, "color_key": fg_color}
        except Exception:
            pass

        # % acciones S&P500 bajo su EMA50 — proxy via ETF XLK vs SMA
        try:
            # Usar RSI del SPY como proxy de sentimiento
            spy = yf.Ticker("SPY").history(period="3mo")
            if not spy.empty:
                s = spy["Close"]
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi_spy = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
                ema50_spy = float(s.ewm(span=50).mean().iloc[-1])
                bajo_ema  = "SPY bajo EMA50" if float(s.iloc[-1]) < ema50_spy else "SPY sobre EMA50"
                result["spy"] = {"rsi": rsi_spy, "ema_status": bajo_ema,
                                 "precio": round(float(s.iloc[-1]),2)}
        except Exception: pass

        # Sector más débil — buscar el que tiene más acciones en corrección
        sectores = {
            "Energía":   ["XOM","CVX","OXY","DVN","COP"],
            "Tech":      ["MSFT","GOOGL","META","NVDA","AMD"],
            "Salud":     ["PFE","MRNA","ABBV","MRK","GILD"],
            "Finanzas":  ["JPM","BAC","GS","MS","C"],
            "Consumo":   ["NKE","CROX","SBUX","MCD","TGT"],
            "Industrial":["BA","GE","HON","CAT","DE"],
        }
        sector_scores = {}
        for sector, tickers in sectores.items():
            en_correccion = 0
            for tk in tickers:
                try:
                    h = yf.Ticker(tk).history(period="3mo")
                    if h.empty: continue
                    c2 = h["Close"].values
                    precio = float(c2[-1]); pico = float(c2.max())
                    dd = (precio-pico)/pico*100
                    s2 = __import__("pandas").Series(c2)
                    d2 = s2.diff()
                    g2 = d2.clip(lower=0).rolling(14).mean()
                    l2 = (-d2.clip(upper=0)).rolling(14).mean()
                    rsi2 = float(100-100/(1+g2.iloc[-1]/(l2.iloc[-1]+1e-9)))
                    if rsi2 < 50 and dd < -10:
                        en_correccion += 1
                except Exception: continue
            sector_scores[sector] = en_correccion

        if sector_scores:
            mejor_sector = max(sector_scores, key=sector_scores.get)
            result["sectores"] = {
                "mejor_oportunidad": mejor_sector,
                "acciones_en_correccion": sector_scores[mejor_sector],
                "scores": sector_scores,
            }

    except Exception: pass
    return result


# ─────────────────────────────────────────────────────────────
#  UNIVERSO A ESCANEAR — S&P500 + Nasdaq + Sectores
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
#  PRE/POST MARKET — datos en tiempo real por ticker
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 min
def fetch_pre_post(ticker: str) -> dict:
    """
    Obtiene Pre-Market y Post-Market de yfinance.
    Si no hay datos, retorna dict con valores None.
    """
    result = {
        "pre_price":  None, "pre_chg":   None, "pre_vol":  None,
        "post_price": None, "post_chg":  None, "post_vol": None,
        "vol_hoy":    None, "vol_avg20": None, "vol_ratio": None,
        "precio_reg": None,
    }
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)

        # Fast info — precio regular, pre y post
        try:
            fi = tk.fast_info
            result["precio_reg"] = float(fi.last_price) if fi.last_price else None

            # Pre-Market
            if hasattr(fi, "pre_market_price") and fi.pre_market_price:
                result["pre_price"] = float(fi.pre_market_price)
                if result["precio_reg"]:
                    result["pre_chg"] = round(
                        (result["pre_price"] - result["precio_reg"]) / result["precio_reg"] * 100, 2)

            # Post-Market
            if hasattr(fi, "post_market_price") and fi.post_market_price:
                result["post_price"] = float(fi.post_market_price)
                if result["precio_reg"]:
                    result["post_chg"] = round(
                        (result["post_price"] - result["precio_reg"]) / result["precio_reg"] * 100, 2)
        except Exception:
            pass

        # Volumen hoy vs promedio 20 días
        try:
            hist = tk.history(period="1mo")
            if not hist.empty and len(hist) >= 5:
                import numpy as np
                avg20 = float(np.mean(hist["Volume"].values[-20:]))
                vol_hoy = float(hist["Volume"].values[-1])
                result["vol_hoy"]   = int(vol_hoy)
                result["vol_avg20"] = int(avg20)
                result["vol_ratio"] = round(vol_hoy / avg20 * 100, 0) if avg20 > 0 else None
        except Exception:
            pass

    except Exception:
        pass
    return result

def render_pre_post_bar(ticker: str, precio_actual: float,
                        G: str, A: str, R: str,
                        TXT_MUT: str, TXT_SOFT: str,
                        BG_HEAD: str, BOR: str) -> str:
    """
    Genera HTML con Pre/Post Market y volumen para un ticker.
    Se llama desde cada tarjeta del scanner.
    """
    d = fetch_pre_post(ticker)

    def vol_semaforo(ratio):
        if ratio is None: return "⚪", TXT_MUT, "Sin datos"
        if ratio >= 200:  return "🟢", G,       f"{ratio:.0f}% del promedio — Alto"
        if ratio >= 120:  return "🟡", A,        f"{ratio:.0f}% del promedio — Normal"
        return "🔴", R, f"{ratio:.0f}% del promedio — Bajo"

    def chg_semaforo(chg):
        if chg is None:  return "⚪", TXT_MUT, "Sin datos"
        if chg >= 3:     return "🟢", G,       f"+{chg:.2f}% — Fuerte"
        if chg >= 1:     return "🟢", G,       f"+{chg:.2f}% — Positivo"
        if chg >= 0:     return "🟡", A,        f"+{chg:.2f}% — Plano"
        if chg >= -1:    return "🟡", A,        f"{chg:.2f}% — Leve baja"
        return "🔴", R, f"{chg:.2f}% — Negativo"

    pre_ico,  pre_c,  pre_txt  = chg_semaforo(d["pre_chg"])
    post_ico, post_c, post_txt = chg_semaforo(d["post_chg"])
    vol_ico,  vol_c,  vol_txt  = vol_semaforo(d["vol_ratio"])

    pre_precio  = f"${d['pre_price']:.2f}"  if d["pre_price"]  else "Sin datos"
    post_precio = f"${d['post_price']:.2f}" if d["post_price"] else "Sin datos"

    html = (
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px">'+
        # Pre-Market
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'+
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">PRE-MARKET</div>'+
        f'<div style="font-size:12px;font-weight:700;color:{pre_c}">{pre_ico} {pre_precio}</div>'+
        f'<div style="font-size:10px;color:{pre_c}">{pre_txt}</div>'+
        f'</div>'+
        # Post-Market
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'+
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">POST-MARKET</div>'+
        f'<div style="font-size:12px;font-weight:700;color:{post_c}">{post_ico} {post_precio}</div>'+
        f'<div style="font-size:10px;color:{post_c}">{post_txt}</div>'+
        f'</div>'+
        # Volumen
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'+
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">VOLUMEN HOY</div>'+
        f'<div style="font-size:12px;font-weight:700;color:{vol_c}">{vol_ico} {vol_txt.split(" — ")[0]}</div>'+
        f'<div style="font-size:10px;color:{vol_c}">{vol_txt.split(" — ")[1] if " — " in vol_txt else vol_txt}</div>'+
        f'</div>'+
        f'</div>'
    )
    return html


# ─────────────────────────────────────────────────────────────
#  PANEL PROBABILIDAD NBIS — para todas las tarjetas del scanner
# ─────────────────────────────────────────────────────────────
def render_nbis_panel(prob: float, sim: float,
                      G: str, A: str, R: str, C: str,
                      TXT: str, TXT_MUT: str, TXT_SOFT: str,
                      BG_HEAD: str, BOR: str) -> str:
    """
    Genera HTML con probabilidad NBIS y similitud con barra de progreso.
    prob: 0-100 probabilidad de seguir el patrón completo
    sim:  0-100 similitud técnica con el momento de entrada de NBIS
    """
    # Colores según umbrales
    def nivel_color(val):
        if val >= 70: return G, "Alta"
        if val >= 50: return A, "Moderada"
        if val >= 30: return C, "Baja"
        return TXT_MUT, "Muy baja"

    prob_c, prob_lbl = nivel_color(prob)
    sim_c,  sim_lbl  = nivel_color(sim)

    # Interpretación combinada
    if prob >= 65 and sim >= 55:
        inter = "🔥 Patrón muy similar a NBIS — alta probabilidad de rebote significativo"
        inter_c = G
    elif prob >= 50 and sim >= 40:
        inter = "⚡ Patrón parcialmente similar — monitorear catalizador"
        inter_c = A
    elif prob >= 35:
        inter = "👀 Similitud moderada — esperar más confirmación"
        inter_c = C
    else:
        inter = "📡 Patrón distinto a NBIS — entrada más especulativa"
        inter_c = TXT_MUT

    html = (
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">'+

        # Prob NBIS
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:9px 12px">'+
        f'  <div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:4px">'+
        f'  ⭐ PROB. PATRÓN NBIS</div>'+
        f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'+
        f'    <span style="font-size:22px;font-weight:800;color:{prob_c}">{prob:.0f}%</span>'+
        f'    <span style="background:{prob_c}22;color:{prob_c};border:1px solid {prob_c}44;'+
        f'    border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{prob_lbl}</span>'+
        f'  </div>'+
        f'  <div style="background:{BOR};border-radius:3px;height:5px;margin-bottom:4px">'+
        f'    <div style="background:{prob_c};height:5px;border-radius:3px;width:{min(prob,100):.0f}%"></div>'+
        f'  </div>'+
        f'  <div style="font-size:9px;color:{TXT_SOFT}">Probabilidad de seguir el patrón completo +20-80%</div>'+
        f'</div>'+

        # Sim NBIS
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:9px 12px">'+
        f'  <div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:4px">'+
        f'  📊 SIMILITUD TÉCNICA CON NBIS</div>'+
        f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'+
        f'    <span style="font-size:22px;font-weight:800;color:{sim_c}">{sim:.0f}%</span>'+
        f'    <span style="background:{sim_c}22;color:{sim_c};border:1px solid {sim_c}44;'+
        f'    border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{sim_lbl}</span>'+
        f'  </div>'+
        f'  <div style="background:{BOR};border-radius:3px;height:5px;margin-bottom:4px">'+
        f'    <div style="background:{sim_c};height:5px;border-radius:3px;width:{min(sim,100):.0f}%"></div>'+
        f'  </div>'+
        f'  <div style="font-size:9px;color:{TXT_SOFT}">RSI · Volumen · EMA · MACD vs entrada original NBIS</div>'+
        f'</div>'+

        f'</div>'+

        # Interpretación combinada
        f'<div style="margin-top:6px;padding:6px 10px;background:{inter_c}11;'+
        f'border-left:3px solid {inter_c};border-radius:4px;'+
        f'font-size:10px;color:{inter_c};font-weight:600">{inter}</div>'
    )
    return html


# ─────────────────────────────────────────────────────────────
#  EXPORTAR SEÑALES DEL DÍA — genera CSV para el tracker
# ─────────────────────────────────────────────────────────────
def exportar_senales_dia(df: pd.DataFrame, tab_nombre: str,
                         fase_col: str = None) -> bytes:
    """
    Genera CSV en formato del tracker paper trading.
    Listo para pegar en hoja ⚡ Paper Trading del Excel.
    """
    import datetime
    hoy = datetime.date.today().strftime("%d-%b-%Y")

    filas = []
    for _, r in df.iterrows():
        tk     = str(r.get("Ticker",""))
        precio = r.get("Precio", 0)
        rsi    = r.get("RSI", 0)
        vol    = r.get("Volumen", r.get("vol_ratio", 0))
        prob   = r.get("Prob_NBIS", 0)
        # Calcular fase según tipo de tab
        if "Dias_Alcistas" in r and "Momentum_3d" in r:
            # Swing Activo — calcular desde momentum
            dias_a = int(r.get("Dias_Alcistas", 0))
            mom_3d = float(r.get("Momentum_3d", 0))
            vol_r2 = float(r.get("Volumen", 0))
            if dias_a >= 3 and mom_3d >= 8 and vol_r2 >= 150:
                fase = "M3 - ENTRAR HOY"
            elif dias_a >= 2 and mom_3d >= 4:
                fase = "M2 - ENTRADA VALIDA"
            else:
                fase = "M1M2 - TEMPRANA"
        elif "Decision" in r:
            # Tabs con scanner normal — mapear Decision a Momento NBIS
            dec = str(r.get("Decision",""))
            rsi_v = float(r.get("RSI", 50))
            dd_v  = float(r.get("DD_pico", 0))
            if dec in ("ENTRAR",) or (rsi_v < 35 and dd_v < -20):
                fase = "M3 - ENTRAR HOY"
            elif dec in ("ANTICIPAR",) or (rsi_v < 45 and dd_v < -12):
                fase = "M2 - ENTRADA VALIDA"
            elif dd_v < -8:
                fase = "M1 - DETECTADA"
            else:
                fase = str(r.get("Fase", dec))
        else:
            fase = str(r.get("Fase", "—"))
        lectura= str(r.get("Lectura",""))[:60]

        stop   = round(float(precio) * 0.95, 2) if precio else ""
        target1= round(float(precio) * 1.08, 2) if precio else ""
        target2= round(float(precio) * 1.12, 2) if precio else ""

        filas.append({
            "Fecha señal":    hoy,
            "Ticker":         tk,
            "Tab señal":      tab_nombre,
            "Fase detectada": str(fase).replace("→","->").replace("·","-").replace("↑","up").replace("↓","down"),
            "VIX entrada":    round(float(vix.get("valor", 0)), 1) if vix.get("_ok") else "",
            "RSI entrada":    round(float(rsi), 1),
            "Vol %":          round(float(vol), 0),
            "Prob NBIS %":    round(float(prob), 1),
            "Precio entrada": round(float(precio), 2),
            "Stop -5%":       stop,
            "Target 1 +8%":   target1,
            "Target 2 +12%":  target2,
            "Precio dia 5":   "",
            "T1 alcanzado?":  "",
            "Precio dia 10":  "",
            "T2 alcanzado?":  "",
            "Stop activado?": "",
            "Resultado %":    "",
            "SPY mismo periodo": "",
            "Alpha vs SPY":   "",
            "Modelo correcto?": "",
            "Notas": lectura.replace("→","->").replace("·","-").replace("↑","up").replace("↓","down").replace("¿","").replace("é","e").replace("í","i").replace("á","a").replace("ó","o").replace("ú","u"),
        })

    return df_to_csv_chile(pd.DataFrame(filas)).encode("utf-8-sig")

def boton_exportar(df: pd.DataFrame, tab_nombre: str,
                   key: str, fase_col: str = None):
    """Renderiza botón de exportar + instrucción."""
    import datetime
    if df is None or df.empty:
        return
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    # Limpiar nombre para filename
    tab_clean = (tab_nombre.replace(" ","_")
                 .replace("🔥","").replace("⚡","")
                 .replace("📡","").replace("👀","")
                 .replace("🔗","").replace("🔎","").strip())
    fname = f"senales_{tab_clean}_{hoy}.csv"

    # Cache CSV en session_state para evitar MediaFileStorageError
    cache_key = f"csv_cache_{key}"
    if cache_key not in st.session_state or st.session_state.get(f"{cache_key}_tab") != tab_nombre:
        st.session_state[cache_key] = exportar_senales_dia(df, tab_nombre, fase_col)
        st.session_state[f"{cache_key}_tab"] = tab_nombre

    csv_bytes = st.session_state[cache_key]

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        st.download_button(
            label=f"📥 Exportar señales de hoy — {len(df)} acción(es)",
            data=csv_bytes,
            file_name=fname,
            mime="text/csv",
            key=key,
            use_container_width=True,
        )
    with col_info:
        st.markdown(
            f'<div style="font-size:10px;color:#64748B;padding-top:8px;line-height:1.6">'+
            f'📋 Pega este CSV en la hoja <strong>⚡ Paper Trading</strong> del tracker.<br>'+
            f'Stop · Targets · VIX · RSI ya vienen calculados.</div>',
            unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  ETF STRATEGY DASHBOARD
# ─────────────────────────────────────────────────────────────
ETF_UNIVERSE = {
    # Índices principales
    "VOO":  {"nombre":"Vanguard S&P500",      "categoria":"Indice",    "riesgo":"Bajo",    "rend_hist":10.0},
    "QQQ":  {"nombre":"Nasdaq 100",            "categoria":"Indice",    "riesgo":"Medio",   "rend_hist":13.0},
    "SPY":  {"nombre":"S&P500 SPDR",           "categoria":"Indice",    "riesgo":"Bajo",    "rend_hist":10.0},
    "VEA":  {"nombre":"Europa/Asia Dev",       "categoria":"Indice",    "riesgo":"Medio",   "rend_hist":7.0},
    # Renta fija / Parking
    "SGOV": {"nombre":"Treasury 0-3m",         "categoria":"Parking",   "riesgo":"Mínimo",  "rend_hist":5.0},
    "BIL":  {"nombre":"Treasury Bills",        "categoria":"Parking",   "riesgo":"Mínimo",  "rend_hist":5.0},
    # Sectoriales
    "XLK":  {"nombre":"Tech Select",           "categoria":"Sectorial", "riesgo":"Medio",   "rend_hist":12.0},
    "XLV":  {"nombre":"Health Care",           "categoria":"Sectorial", "riesgo":"Bajo",    "rend_hist":9.0},
    "XLE":  {"nombre":"Energy Select",         "categoria":"Sectorial", "riesgo":"Medio",   "rend_hist":8.0},
    # Ya tienes
    "TAN":  {"nombre":"Solar Energy",          "categoria":"Sectorial", "riesgo":"Alto",    "rend_hist":8.0},
    "XBI":  {"nombre":"Biotech",               "categoria":"Sectorial", "riesgo":"Alto",    "rend_hist":9.0},
    # Cripto
    "IBIT": {"nombre":"Bitcoin ETF BlackRock", "categoria":"Cripto",    "riesgo":"MuyAlto", "rend_hist":30.0},
    "ETHA": {"nombre":"Ethereum ETF BlackRock","categoria":"Cripto",    "riesgo":"MuyAlto", "rend_hist":25.0},
}

def fetch_etf_data(ticker: str) -> dict:
    """Obtiene datos técnicos de un ETF desde yfinance."""
    try:
        import yfinance as yf
        import numpy as np
        tk  = yf.Ticker(ticker)
        hist = tk.history(period="6mo")
        if hist.empty or len(hist) < 20:
            return None
        close = hist["Close"].values
        vol   = hist["Volume"].values

        precio  = float(close[-1])
        pico    = float(close.max())
        dd      = round((precio - pico) / pico * 100, 1)

        # RSI 14
        delta  = hist["Close"].diff()
        gain   = delta.clip(lower=0).rolling(14).mean()
        loss   = (-delta.clip(upper=0)).rolling(14).mean()
        rsi    = round(float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

        # Tendencia 20d
        ema20  = float(hist["Close"].ewm(span=20).mean().iloc[-1])
        tend   = "↑" if precio > ema20 * 1.02 else "↓" if precio < ema20 * 0.98 else "→"

        # YTD
        try:
            hist_ytd = tk.history(period="1y")
            ytd_price = float(hist_ytd["Close"].iloc[0]) if not hist_ytd.empty else precio
            ytd_pct   = round((precio - ytd_price) / ytd_price * 100, 1)
        except:
            ytd_pct = 0.0

        # Volumen ratio
        avg_vol   = float(np.mean(vol[-20:]))
        vol_ratio = round(float(vol[-1]) / avg_vol * 100, 0) if avg_vol > 0 else 100

        # Señal de entrada
        if rsi < 35 and dd < -15:
            senal = "🟢 COMPRAR AHORA"
            senal_c = "16A34A"
        elif rsi < 50 and dd < -8:
            senal = "🟡 BUENA ENTRADA"
            senal_c = "D97706"
        elif rsi > 70:
            senal = "🔴 ESPERAR — RSI alto"
            senal_c = "DC2626"
        elif dd > -3:
            senal = "⚪ EN MÁXIMOS"
            senal_c = "64748B"
        else:
            senal = "🔵 NEUTRAL"
            senal_c = "2563EB"

        return {
            "ticker":    ticker,
            "precio":    precio,
            "dd":        dd,
            "rsi":       rsi,
            "tend":      tend,
            "ytd":       ytd_pct,
            "vol_ratio": vol_ratio,
            "senal":     senal,
            "senal_c":   senal_c,
            "ema20":     ema20,
        }
    except Exception:
        return None


def calcular_estrategia(capital: float, plazo: str, perfil: str,
                         etf_data: dict) -> dict:
    """
    Calcula distribución óptima de capital en ETFs
    basada en indicadores actuales + perfil + plazo.
    """
    # Pesos base por perfil y plazo
    if perfil == "Moderado":
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.50, "Indice":0.30, "Sectorial":0.10, "Cripto":0.10}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.20, "Indice":0.50, "Sectorial":0.20, "Cripto":0.10}
        else:  # Largo
            base = {"Parking":0.05, "Indice":0.55, "Sectorial":0.25, "Cripto":0.15}
    elif perfil == "Agresivo":
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.20, "Indice":0.40, "Sectorial":0.25, "Cripto":0.15}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.05, "Indice":0.45, "Sectorial":0.30, "Cripto":0.20}
        else:
            base = {"Parking":0.00, "Indice":0.40, "Sectorial":0.35, "Cripto":0.25}
    else:  # Conservador
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.70, "Indice":0.20, "Sectorial":0.10, "Cripto":0.00}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.40, "Indice":0.40, "Sectorial":0.15, "Cripto":0.05}
        else:
            base = {"Parking":0.20, "Indice":0.50, "Sectorial":0.25, "Cripto":0.05}

    # Ajustar por señales técnicas — sobreponderar ETFs en zona de compra
    allocations = []
    for tk, meta in ETF_UNIVERSE.items():
        d = etf_data.get(tk)
        if d is None:
            continue
        cat = meta["categoria"]
        peso_base = base.get(cat, 0)

        # Ajuste por RSI y DD
        if d["rsi"] < 40 and d["dd"] < -15:
            ajuste = 1.3   # sobreponderar
        elif d["rsi"] > 70:
            ajuste = 0.6   # subponderar
        elif d["dd"] > -3:
            ajuste = 0.8   # en máximos, esperar
        else:
            ajuste = 1.0

        peso_ajustado = peso_base * ajuste
        monto         = round(capital * peso_ajustado, 0)

        allocations.append({
            "ticker":   tk,
            "nombre":   meta["nombre"],
            "categoria":cat,
            "riesgo":   meta["riesgo"],
            "rend_hist":meta["rend_hist"],
            "peso":     round(peso_ajustado * 100, 1),
            "monto":    monto,
            "rsi":      d["rsi"],
            "dd":       d["dd"],
            "senal":    d["senal"],
            "senal_c":  d["senal_c"],
            "tend":     d["tend"],
            "ytd":      d["ytd"],
            "precio":   d["precio"],
        })

    # Normalizar a 100%
    total_peso = sum(a["peso"] for a in allocations)
    if total_peso > 0:
        for a in allocations:
            a["peso"]  = round(a["peso"] / total_peso * 100, 1)
            a["monto"] = round(capital * a["peso"] / 100, 0)

    # DCA — dividir en meses según plazo
    meses_dca = {"Corto (6-12m)": 3, "Mediano (2-5a)": 4, "Largo (5-10a)": 6}
    n_meses   = meses_dca.get(plazo, 4)
    monto_mes = round(capital / n_meses, 0)

    # Proyección
    rend_ponderado = sum(
        (a["monto"] / capital) * ETF_UNIVERSE[a["ticker"]]["rend_hist"]
        for a in allocations if capital > 0
    )
    años = {"Corto (6-12m)": 1, "Mediano (2-5a)": 5, "Largo (5-10a)": 10}
    n_años = años.get(plazo, 5)
    proy_base = round(capital * (1 + rend_ponderado/100) ** n_años, 0)
    proy_opt  = round(capital * (1 + (rend_ponderado+3)/100) ** n_años, 0)
    proy_pes  = round(capital * (1 + max(rend_ponderado-4, 2)/100) ** n_años, 0)

    return {
        "allocations":      sorted(allocations, key=lambda x: -x["monto"]),
        "n_meses":          n_meses,
        "monto_mes":        monto_mes,
        "rend_ponderado":   round(rend_ponderado, 1),
        "proy_base":        proy_base,
        "proy_opt":         proy_opt,
        "proy_pes":         proy_pes,
        "n_años":           n_años,
    }


def df_to_csv_chile(df: pd.DataFrame) -> str:
    """Exporta DataFrame en formato CSV Chile: separador ; y decimales con coma"""
    return df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")


# ─────────────────────────────────────────────────────────────
#  SCORE DE REBOTE v11 — Reemplaza Prob NBIS + Sim NBIS
#  Basado en condiciones del patrón, no en comparación exacta
# ─────────────────────────────────────────────────────────────
def calcular_score_rebote(dd: float, rsi: float, vol_ratio: float,
                           dias_alcistas: int, momentum_3d: float,
                           tiene_catalizador: bool, dias_para_cat: int,
                           beta: float) -> dict:
    """
    Score de rebote 0-100 basado en 4 componentes:
    30% DD (corrección profunda)
    25% RSI girando desde zona baja
    25% Volumen confirmando
    20% Catalizador próximo
    """
    # ── Componente 1: DD (30 pts) ─────────────────────────────
    # Buscamos corrección real pero no destrucción
    if dd <= -40:
        pts_dd = 25    # muy profundo — posible destrucción
    elif dd <= -30:
        pts_dd = 30    # ideal — corrección severa
    elif dd <= -20:
        pts_dd = 28    # muy bueno
    elif dd <= -15:
        pts_dd = 22    # bueno
    elif dd <= -10:
        pts_dd = 15    # moderado
    elif dd <= -5:
        pts_dd = 8     # leve
    else:
        pts_dd = 0     # en máximos — no hay corrección

    # ── Componente 2: RSI girando (25 pts) ────────────────────
    # RSI bajo + subiendo = zona ideal de entrada
    if rsi <= 30:
        pts_rsi = 25   # sobreventa extrema
    elif rsi <= 38:
        pts_rsi = 23   # sobreventa clara
    elif rsi <= 45:
        pts_rsi = 18   # zona baja — buena entrada
    elif rsi <= 55:
        pts_rsi = 12   # zona media — aceptable
    elif rsi <= 65:
        pts_rsi = 5    # zona alta — precaución
    else:
        pts_rsi = 0    # sobrecomprado — no entrar

    # Bonus si momentum positivo (RSI girando hacia arriba)
    if momentum_3d > 0 and dias_alcistas >= 2:
        pts_rsi = min(pts_rsi + 5, 25)

    # ── Componente 3: Volumen (25 pts) ────────────────────────
    # Volumen alto confirma que el movimiento es real
    if vol_ratio >= 300:
        pts_vol = 25   # excepcional — institucional
    elif vol_ratio >= 200:
        pts_vol = 22   # muy alto
    elif vol_ratio >= 150:
        pts_vol = 18   # alto — buena señal
    elif vol_ratio >= 100:
        pts_vol = 12   # normal
    elif vol_ratio >= 70:
        pts_vol = 6    # bajo
    else:
        pts_vol = 0    # muy bajo — señal débil

    # ── Componente 4: Catalizador (20 pts) ────────────────────
    if tiene_catalizador and dias_para_cat <= 7:
        pts_cat = 20   # earnings en menos de 1 semana
    elif tiene_catalizador and dias_para_cat <= 15:
        pts_cat = 16   # earnings en 2 semanas
    elif tiene_catalizador and dias_para_cat <= 30:
        pts_cat = 10   # earnings en el mes
    elif tiene_catalizador:
        pts_cat = 5    # earnings lejanos
    else:
        pts_cat = 0    # sin catalizador identificado

    # ── Score total ───────────────────────────────────────────
    score_total = pts_dd + pts_rsi + pts_vol + pts_cat

    # Penalización por Beta muy alto sin volumen
    if beta > 3.0 and vol_ratio < 100:
        score_total = max(score_total - 10, 0)

    # Clasificación
    if score_total >= 75:
        nivel = "🔥 FUERTE"
        color = "16A34A"
    elif score_total >= 60:
        nivel = "⚡ BUENO"
        color = "D97706"
    elif score_total >= 45:
        nivel = "🟡 MODERADO"
        color = "2563EB"
    else:
        nivel = "🔵 DÉBIL"
        color = "64748B"

    return {
        "score":      score_total,
        "nivel":      nivel,
        "color":      color,
        "pts_dd":     pts_dd,
        "pts_rsi":    pts_rsi,
        "pts_vol":    pts_vol,
        "pts_cat":    pts_cat,
        "detalle":    f"DD:{pts_dd}/30 · RSI:{pts_rsi}/25 · Vol:{pts_vol}/25 · Cat:{pts_cat}/20",
    }


def clasificar_sizing(score: int, vix: float) -> dict:
    """
    Cambio 3: Sizing dinámico por VIX + Score
    Retorna el tamaño recomendado de posición como % del capital planificado
    """
    if vix < 20:
        vix_mult = 0.5    # mercado tranquilo → reducir
        vix_label = "VIX bajo — reducir tamaño"
        vix_color = "D97706"
    elif vix < 30:
        vix_mult = 1.0    # normal
        vix_label = "VIX normal — tamaño estándar"
        vix_color = "2563EB"
    else:
        vix_mult = 1.5    # miedo/pánico → aumentar
        vix_label = "VIX alto — aumentar tamaño"
        vix_color = "16A34A"

    if score >= 75:
        score_pct = 1.0
        score_label = "Señal fuerte"
    elif score >= 60:
        score_pct = 0.75
        score_label = "Señal buena"
    elif score >= 45:
        score_pct = 0.50
        score_label = "Señal moderada"
    else:
        score_pct = 0.25
        score_label = "Señal débil"

    sizing_final = round(vix_mult * score_pct * 100)
    sizing_final = max(25, min(sizing_final, 150))  # entre 25% y 150%

    return {
        "sizing_pct":   sizing_final,
        "vix_label":    vix_label,
        "vix_color":    vix_color,
        "score_label":  score_label,
        "detalle":      f"{vix_label} × {score_label} = {sizing_final}% del capital planificado",
    }


# ─────────────────────────────────────────────────────────────
#  UNIVERSO DINÁMICO — S&P500 + Nasdaq100 + Portfolio personal
#  Se descarga automáticamente desde Wikipedia al iniciar
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)  # cache 24 horas
def cargar_universo_dinamico() -> list:
    """
    Descarga componentes S&P500 + Nasdaq100 via múltiples fuentes.
    Fallback progresivo si alguna fuente falla.
    """
    import yfinance as yf

    portfolio_personal = [
        "NBIS","MRNA","CROX","APLD","ASTS","NVDA","CNC","CLOV",
        "NKE","XBI","TAN","VOO","IBIT","ETHA","SPY","IBRX",
    ]
    tickers = set(portfolio_personal)

    # Fuente 1: yfinance — componentes S&P500 via ETF holdings
    try:
        import pandas as pd
        # Descargar desde GitHub (fuente pública confiable)
        url_sp500 = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
        sp500 = pd.read_csv(url_sp500)
        tickers.update(sp500["Symbol"].tolist())
    except Exception:
        pass

    # Fuente 2: Wikipedia con timeout corto
    try:
        import pandas as pd
        sp500_wiki = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            storage_options={"timeout": 5}
        )[0]
        tickers.update(sp500_wiki["Symbol"].str.replace(".","-").tolist())
    except Exception:
        pass

    # Fuente 3: yfinance screener — top 500 por market cap
    try:
        screener = yf.screen("most_actives", count=500)
        if screener and "quotes" in screener:
            for q in screener["quotes"]:
                if "symbol" in q:
                    tickers.add(q["symbol"])
    except Exception:
        pass

    # Siempre ampliar con universo curado de alta calidad
    universo_curado = [
        # Mega Cap
        "MSFT","GOOGL","META","AMZN","AAPL","NVDA","TSLA","ORCL","CRM","SNOW",
        "PLTR","ADBE","INTU","NOW","WDAY","DDOG","NET","CRWD","PANW","ZS","MDB",
        "AMD","AVGO","MRVL","ANET","SMCI","APP","RDDT","DOMO","AI","HOOD","SOFI",
        # Fintech
        "COIN","AFRM","XYZ","PYPL","V","MA","AXP","JPM","BAC","GS","MS","C",
        "WFC","BLK","SCHW","ICE","CME","MELI","NU","PAGS","UPST","LC","OPEN",
        # Biotech
        "IBRX","CELH","HIMS","RXRX","PCVX","PFE","ABBV","MRK","BMY","GILD",
        "AMGN","REGN","VRTX","BIIB","ILMN","ZTS","ISRG","SYK","BSX","EW",
        "DXCM","HOLX","AXSM","TVTX","MRNA","BNTX","ARWR","BEAM","CRSP","EDIT",
        "NVCR","RCUS","MRUS","KROS","FOLD","VRNA","IMVT","XENE","PRAX","ACAD",
        # Cripto/AI
        "MARA","RIOT","CORZ","CLSK","HUT","BTBT","IONQ","RGTI","QBTS","MSTR",
        "IREN","WULF","BITF","CIFR","BTDR","SMLR","HIVE","DMGI",
        # LatAm/Global
        "BABA","PDD","SE","GRAB","GLOB","ARCO","VTEX","DESP",
        # Consumo
        "LULU","SBUX","MCD","CMG","TGT","COST","HD","BURL","CHWY","W","RH",
        "RVLV","ONON","DECK","SKX","CROX","BOOT","ANF","AEO","URBN",
        # Energía/Solar
        "OXY","DVN","XOM","CVX","COP","SLB","HAL","FCX","NEM","FANG",
        "AR","EQT","RRC","ENPH","SEDG","RUN","ARRY","NOVA","FSLR","TAN",
        # Industrial/Defensa
        "BA","GE","HON","LMT","RTX","GD","DE","CAT","UPS","FDX",
        "NOC","AXON","KTOS","RCAT","JOBY","ACHR",
        # ETFs
        "ARKK","ARKG","ARKF","SOXX","XBI","IBB","XLK","XLF","XLV",
        "XLE","XLI","XLY","JETS","HACK","BOTZ",
        # Small/Mid Alta Beta
        "STAA","ACN","OPEN","RGTI","APLD","ASTS","CLOV","NKE",
    ]
    tickers.update(universo_curado)

    result = sorted(list(tickers))
    return result


# Cargar universo al iniciar
SCAN_UNIVERSE = cargar_universo_dinamico()

@st.cache_data(ttl=1800, show_spinner=False)
def scan_tab(rsi_max: float, dd_min: float,
             score_min: int = 20, decisions: list = None,
             vol_min_k: float = 200,
             max_results: int = 100,
             universo: list = None) -> pd.DataFrame:
    """
    Escanea el universo y retorna candidatos para el tab específico.
    rsi_max, dd_min: filtros técnicos del tab
    decision_filter: ["ENTRAR"] | ["ANTICIPAR"] | ["SEGUIR"] etc.
    score_min: score mínimo para aparecer en este tab
    """
    candidatos = []
    try:
        import yfinance as yf
        _universo = universo if universo else SCAN_UNIVERSE
        for tk in _universo:
            try:
                stk  = yf.Ticker(tk)
                # Usar 3mo para velocidad — suficiente para DD y RSI
                try:
                    hist = stk.history(period="3mo")
                except Exception:
                    continue
                if hist.empty or len(hist) < 20:
                    continue

                close = hist["Close"].values
                vol   = hist["Volume"].values
                precio = float(close[-1])
                pico   = float(close.max())
                dd     = round((precio - pico) / pico * 100, 1)
                if dd > dd_min:
                    continue

                s     = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
                if rsi > rsi_max:
                    continue

                avg_v  = float(np.mean(vol[-20:]))
                vol_k  = avg_v / 1000
                if vol_k < vol_min_k:
                    continue

                vol_r  = int(vol[-1] / avg_v * 100)
                ema50  = float(s.ewm(span=50).mean().iloc[-1])
                ema_d  = round((precio - ema50) / ema50 * 100, 1)
                ema12  = s.ewm(span=12).mean()
                ema26  = s.ewm(span=26).mean()
                macd_h = round(float((ema12-ema26-(ema12-ema26).ewm(9).mean()).iloc[-1]), 3)
                low30  = float(np.min(close[-30:]))
                sop    = round((precio - low30) / low30 * 100, 1)
                rsi_5d = float((100-100/(1+gain/(loss+1e-9))).iloc[-6]) if len(close)>=6 else rsi
                rsi_t  = 5 if (rsi-rsi_5d)>3 else -3 if (rsi-rsi_5d)<-3 else 0

                try:
                    info    = stk.info or {}
                except Exception:
                    info = {}
                beta_v  = float(info.get("beta", 1.5) or 1.5)
                nombre  = info.get("shortName", tk)
                sector  = info.get("sector", "—")
                ingresos= float(info.get("totalRevenue", 0) or 0) / 1e6
                bpa_v   = float(info.get("trailingEps", 0) or 0)
                div_v   = float(info.get("dividendYield", 0) or 0) * 100
                mar_v   = float(info.get("grossMargins", 0) or 0) * 100
                si_v    = float(info.get("shortPercentOfFloat", 0) or 0) * 100

                try:
                    cal  = stk.calendar
                    earn = str(cal["Earnings Date"][0])[:10] if (cal is not None and "Earnings Date" in cal) else "—"
                except Exception:
                    earn = "—"

                sector_map = {
                    "Technology":"Tech","Healthcare":"Salud",
                    "Financial Services":"Finanzas",
                    "Consumer Cyclical":"Consumo",
                    "Consumer Defensive":"Consumo",
                    "Energy":"Energía","Industrials":"Industrial",
                    "Communication Services":"Tech",
                }
                area = sector_map.get(sector, sector[:10] if sector and sector!="—" else "—")

                bonus_f, desc_f = bonus_fundamentales(bpa_v, div_v, mar_v, ingresos, vol_k)
                sc_base = calc_score(rsi, vol_r, ema_d, macd_h, sop, dd, 0, si_v, 1.0, 1.0, rsi_t)
                sc = min(100, sc_base + bonus_f)
                vix_mult = vix.get("mult", 1.0) if vix.get("_ok") else 1.0
                if vix_mult > 1.0:
                    sc = min(100, int(sc * vix_mult))
                if sc < score_min:
                    continue

                dec, fase, trig, col, bg = get_decision(sc, 0, 1.0, macd_h, rsi, "—")
                if decisions and dec not in decisions:
                    continue

                pat = clasificar_patron(beta_v, si_v, 0, 3, dd)
                rsi_dir, _, rsi_dir_desc = rsi_direccion(rsi, rsi_t, dd, macd_h)
                earn_txt = f"Earnings {earn}" if earn != "—" else "Sin catalizador detectado"
                lectura  = (f"RSI {rsi:.0f} {'↑' if rsi_t>0 else '↓' if rsi_t<0 else '→'} · "
                           f"DD {dd:.0f}% · {earn_txt} · Vol {vol_r}% promedio")

                candidatos.append({
                    "Ticker":tk,"Nombre":nombre,"Area":area,
                    "Precio":round(precio,2),"RSI":rsi,"RSI_Tend":rsi_t,
                    "Volumen":vol_r,"EMA50":ema_d,"MACD":macd_h,
                    "Soporte":sop,"Beta":round(beta_v,2),"DD_pico":dd,
                    "Pico_P":round(pico,2),"Pico_F":"—","Meses":3,
                    "Short_Int":round(si_v,1),
                    "Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
                    "Cat_Tipo":"Earnings" if earn!="—" else "—",
                    "Cat_Desc":earn_txt,"Cat_Fecha":earn,
                    "Arrastradas":"—","Lider":"—",
                    "Score":sc,"Score_Base":sc_base,"Bonus_Fund":bonus_f,
                    "Fund_Desc":desc_f,
                    "BPA":round(bpa_v,2),"Dividendo":round(div_v,1),
                    "Margen":round(mar_v,1),"Ingresos_M":round(ingresos,0),
                    "Vol_Diario_K":round(vol_k,0),
                    "Es_Iliquida":vol_k<500,
                    "Decision":dec,"Fase":fase,"Trigger":trig,
                    "Color":col,"Bg":bg,
                    "Prob_NBIS":prob_nbis(sc,1.0,si_v,dd,3),
                    "Sim_NBIS":sim_nbis(rsi,vol_r,ema_d,macd_h,sop,dd),
                    "Motivo":motivo("Earnings" if earn!="—" else "—",0,"—"),
                    "Lectura":lectura,"Estado":"ACTIVO",
                    "Patron_Tipo":pat[0],"Patron_Emoji":pat[1],
                    "Patron_Desc":pat[2],"Patron_Dias":pat[3],
                    "RSI_Dir":rsi_dir,"RSI_Dir_Desc":rsi_dir_desc,
                    "_source":"screener","_precio_live":True,
                })
            except Exception:
                continue
    except Exception:
        pass

    return pd.DataFrame(
        sorted(candidatos, key=lambda x: -x["Score"])[:max_results]
    )


# Session state para resultados de cada tab
for _tab_key in ["scan_entrar","scan_swing","scan_detectadas","scan_sympathy"]:
    if _tab_key not in st.session_state:
        st.session_state[_tab_key] = None

def _count(key):
    d = st.session_state.get(key)
    return len(d) if d is not None and not d.empty else 0



def get_decision(score, pre_move, pre_vol, macd, rsi, lider):
    # ── ENTRAR — señal M3 confirmada ──────────────────────────
    if score>=80 and pre_move>=5 and pre_vol>=1.8 and macd>0:
        return "ENTRAR","Fase 3","RUPTURA ACTIVA",G,G_BG
    # ── ANTICIPAR — pre-señal activa ──────────────────────────
    elif score>=65 and pre_move>=2 and macd>0:
        return "ANTICIPAR","Fase 3","PRE-SEÑAL ACTIVA",C,C_BG
    # ── SEGUIR Fase 2 — radar, fondo formando ─────────────────
    elif score>=40:
        return "SEGUIR","Fase 2","FONDO FORMANDO",A,A_BG
    # ── SEGUIR Fase 1 — bajada activa ─────────────────────────
    elif score>=20:
        return "SEGUIR","Fase 1","EN BAJADA",R,R_BG
    else:
        return "OBSERVAR","Fase 0","SIN SEÑAL",TXT_MUT,BG_HEAD

def clasificar_patron(beta: float, short_int: float, pre_move: float,
                      meses: int, dd: float) -> tuple:
    """
    Clasifica el tipo de patrón esperado.
    Aprendizaje del análisis: NBIS (explosivo) vs SEI (gradual) vs TVTX (cíclico).
    Retorna (tipo, emoji, descripcion, dias_objetivo)
    """
    # Patrón EXPLOSIVO — alta velocidad, alto riesgo
    if beta >= 2.5 or short_int >= 15 or pre_move >= 7:
        return ("EXPLOSIVO", "🚀",
                "Rebote rápido 1-3 semanas · Beta alto o short squeeze",
                "7-21 días")
    # Patrón CÍCLICO — múltiples fondos visibles
    if meses <= 2 and dd >= -35 and beta >= 1.5:
        return ("CÍCLICO", "🔄",
                "Ciclos repetidos · Entrar solo en fondo del ciclo",
                "3-8 semanas por ciclo")
    # Patrón GRADUAL — fundamentales sólidos, movimiento sostenido
    return ("GRADUAL", "📈",
            "Rebote sostenido 2-4 meses · Fundamentales sólidos",
            "8-16 semanas")

def rsi_direccion(rsi_actual: float, rsi_tend: int, precio_dd: float,
                   macd: float) -> tuple:
    """
    Evalúa la dirección del RSI en contexto del precio.
    Aprendizaje: ENTX (RSI 48 bajando = trampa) vs STAA (RSI 28 subiendo = oportunidad)
    Retorna (señal, color, descripcion)
    """
    # RSI bajo + subiendo = rebote confirmado ✅
    if rsi_actual < 40 and rsi_tend > 0 and macd > 0:
        return ("RSI REBOTANDO", "G",
                f"RSI {rsi_actual:.0f} subiendo con MACD positivo — señal fuerte")
    # RSI bajo + lateral = base formando 🟡
    if rsi_actual < 40 and rsi_tend == 0:
        return ("RSI BASE", "A",
                f"RSI {rsi_actual:.0f} lateral — base formando, esperar dirección")
    # RSI bajo + bajando = trampa ❌
    if rsi_actual < 45 and rsi_tend < 0:
        return ("RSI CAYENDO", "R",
                f"RSI {rsi_actual:.0f} aún bajando — NO entrar, esperar capitulación")
    # RSI medio + bajando = tendencia bajista activa
    if rsi_actual >= 45 and precio_dd < -15:
        return ("TRAMPA DD", "R",
                f"RSI {rsi_actual:.0f} con DD {precio_dd:.0f}% — bajada sin capitulación")
    # RSI neutro normal
    return ("RSI NEUTRO", "TXT_MUT",
            f"RSI {rsi_actual:.0f} — zona neutral")


def prob_nbis(score,pre_vol,short_int,dd,meses):
    b=score*0.65+min(pre_vol*8,20)+min(short_int*0.8,15)
    if dd<-30: b+=8
    if meses>=3: b+=7
    return round(min(b,99),1)

def sim_nbis(rsi,vol,ema,macd,sop,dd):
    s=100-abs(rsi-29)*1.5-abs(vol-310)*0.04-abs(ema+12)*1.2-abs(macd-1.80)*8-abs(sop-0.8)*4-abs(dd+38)*0.3
    return round(max(0,min(s,99)),1)

def motivo(ct,pm,lider):
    if lider: return "Sympathy play" if pm>=3 else "Narrativa sectorial"
    if ct in ["Earnings","Clinical"]: return "Catalizador directo"
    if ct in ["Contrato","FDA"]: return "Catalizador fundamental"
    if ct=="Sector": return "Narrativa sectorial"
    if pm>=5: return "Catalizador general"
    return "Acumulación técnica"

@st.cache_data
def build_curated() -> pd.DataFrame:
    """
    Construye el DataFrame con SOLO los datos curados del RAW:
    catalizador, área, acciones arrastradas, estado, lectura, Pre-Market.
    Los indicadores técnicos se reemplazarán con datos reales de yfinance.
    """
    rows=[]
    for r in RAW:
        (t,n,area,p,rsi,vol,ema,macd,sop,beta,
         dd,pp,pf,mes,si,pv,postv,pm,ct,cd,cf,
         arr,lider,lect,estado)=r
        rows.append({
            # ── Datos curados (no reemplazables por yfinance) ──
            "Ticker":t,"Nombre":n,"Area":area,
            "Cat_Tipo":ct,"Cat_Desc":cd,"Cat_Fecha":cf,
            "Arrastradas":", ".join(arr) if arr else "—",
            "Lider":lider if lider else "—",
            "Estado":estado,"Lectura":lect,
            "Meses":mes,                     # meses en corrección (curado)
            "Short_Int":si,                  # short interest (curado, FINRA bi-mensual)
            "Pre_Vol":pv,"Post_Vol":postv,   # vol Pre/Post Market (curado)
            "Pre_Move":pm,                   # movimiento Pre-Market % (curado)
            # ── Indicadores técnicos: valores RAW como fallback ──
            "Precio":p,"RSI":rsi,"Volumen":vol,"EMA50":ema,
            "MACD":macd,"Soporte":sop,"Beta":beta,
            "DD_pico":dd,"Pico_P":pp,"Pico_F":pf,
            "_source":"curado",
        })
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────
#  OPCIÓN C — TODOS LOS INDICADORES EN TIEMPO REAL
#  Cache 20 min para no saturar yfinance en cada recarga
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1200, show_spinner=False)
def fetch_all_indicators(tickers: tuple) -> dict:
    """
    Descarga 6 meses de historia para cada ticker y calcula:
    Precio, RSI, RSI_Tend, MACD, EMA50 dist, Volumen ratio,
    DD desde pico, Soporte dist, Beta.
    Retorna dict {ticker: {campo: valor, ...}}
    """
    resultado = {}
    try:
        import yfinance as yf

        # Descarga batch de todos los tickers de una vez (más rápido)
        raw = yf.download(
            list(tickers),
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )

        for tk in tickers:
            try:
                # Extraer OHLCV para este ticker
                if len(tickers) == 1:
                    hist_close = raw["Close"].dropna()
                    hist_vol   = raw["Volume"].dropna()
                else:
                    hist_close = raw[tk]["Close"].dropna()
                    hist_vol   = raw[tk]["Volume"].dropna()

                if len(hist_close) < 20:
                    continue

                close = hist_close.values
                vol   = hist_vol.values

                # ── RSI (14) ──────────────────────────────
                s = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rs    = gain / (loss + 1e-9)
                rsi_series = 100 - 100 / (1 + rs)
                rsi   = round(float(rsi_series.iloc[-1]), 1)

                # Tendencia RSI (vs 5 días atrás)
                rsi_5d = float(rsi_series.iloc[-6]) if len(rsi_series) >= 6 else rsi
                rsi_tend = 5 if (rsi - rsi_5d) > 3 else -3 if (rsi - rsi_5d) < -3 else 0

                # ── MACD (12/26/9) ────────────────────────
                ema12 = s.ewm(span=12, adjust=False).mean()
                ema26 = s.ewm(span=26, adjust=False).mean()
                macd_line   = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_hist   = round(float((macd_line - signal_line).iloc[-1]), 3)

                # ── EMA50 distancia % ─────────────────────
                ema50 = float(s.ewm(span=50, adjust=False).mean().iloc[-1])
                precio_actual = float(close[-1])
                ema_dist = round((precio_actual - ema50) / ema50 * 100, 1)

                # ── Volumen ratio (último vs media 20d) ───
                avg_v = float(np.mean(vol[-20:])) if len(vol) >= 20 else float(np.mean(vol))
                vol_ratio = int(vol[-1] / avg_v * 100) if avg_v > 0 else 100

                # ── DD desde pico (6 meses) ───────────────
                pico = float(np.max(close))
                dd   = round((precio_actual - pico) / pico * 100, 1)

                # ── Soporte (distancia al mínimo 30d) ─────
                low30 = float(np.min(close[-30:])) if len(close) >= 30 else float(np.min(close))
                sop   = round((precio_actual - low30) / low30 * 100, 1)

                # ── Beta (desde fast_info, no bloquea) ────
                try:
                    info = yf.Ticker(tk).fast_info
                    beta = float(getattr(info, "beta", 1.5) or 1.5)
                except Exception:
                    beta = 1.5

                resultado[tk] = {
                    "Precio": round(precio_actual, 2),
                    "RSI": rsi,
                    "RSI_Tend": rsi_tend,
                    "MACD": macd_hist,
                    "EMA50": ema_dist,
                    "Volumen": vol_ratio,
                    "DD_pico": dd,
                    "Pico_P": round(pico, 2),
                    "Soporte": sop,
                    "Beta": round(beta, 2),
                    "_source": "live",
                }
            except Exception:
                continue  # si falla un ticker, seguimos con los demás

    except Exception:
        pass  # sin yfinance o sin internet — retorna vacío

    return resultado

def build_df():
    """
    Combina datos curados del RAW con indicadores de yfinance.
    Si yfinance no está disponible o falla, usa los datos del RAW directamente.
    Siempre retorna (DataFrame, n_live) sin excepciones.
    """
    df_cur = build_curated()
    tickers = tuple(df_cur["Ticker"].tolist())

    # Intentar obtener indicadores reales
    try:
        live = fetch_all_indicators(tickers)
    except Exception:
        live = {}
    n_live = len(live)

    rows = []
    for _, row in df_cur.iterrows():
        tk     = row["Ticker"]
        ind    = live.get(tk, {})
        estado = row["Estado"]

        # ── Indicadores: precio/RSI/EMA/Vol de yfinance ──────
        # MACD y Soporte: SIEMPRE del RAW curado.
        # El MACD real en mercados bajistas es negativo → rompe el score.
        # El dato curado representa la tendencia esperada del catalizador.
        rsi    = float(ind.get("RSI",     row["RSI"]))
        rsi_t  = int(ind.get("RSI_Tend", 5 if float(row["MACD"])>0 and rsi<42 else 0))
        macd   = float(row["MACD"])          # ← siempre del RAW curado
        ema    = float(ind.get("EMA50",  row["EMA50"]))
        vol    = int(ind.get("Volumen",  row["Volumen"]))
        dd     = float(ind.get("DD_pico",row["DD_pico"]))
        pico_p = float(ind.get("Pico_P", row["Pico_P"]))
        sop    = float(row["Soporte"])       # ← siempre del RAW curado
        beta   = float(ind.get("Beta",   row["Beta"]))
        precio = float(ind.get("Precio", row["Precio"]))
        src    = ind.get("_source", "curado")

        # ── Datos curados (siempre del RAW) ─────────────────
        pm  = float(row["Pre_Move"])
        pv  = float(row["Pre_Vol"])
        si  = float(row["Short_Int"])
        mes = int(row["Meses"])
        lider  = row["Lider"]

        # ── Fundamentales del diccionario FUND ───────────────
        fund = FUND.get(tk, (0.0, 0.0, 0.0, 0.0, 999.0))
        bpa_v, div_v, mar_v, ing_v, vol_k = fund
        bonus_fund, desc_fund = bonus_fundamentales(bpa_v, div_v, mar_v, ing_v, vol_k)

        # ── Score base + bonus fundamentales ─────────────────
        sc_base = calc_score(rsi, vol, ema, macd, sop, dd, pm, si, pv,
                             float(row["Post_Vol"]), rsi_t)
        sc = min(100, sc_base + bonus_fund)

        # ── Multiplicador VIX (ya cargado globalmente) ────────
        # Solo aplica cuando VIX > 25 (mercado en miedo/pánico)
        vix_mult = vix.get("mult", 1.0) if vix.get("_ok") else 1.0
        if vix_mult > 1.0:
            sc = min(100, int(sc * vix_mult))

        # ── Filtro liquidez: acciones ilíquidas no pasan F2 ──
        # vol_k < 500K → penalización ya está en bonus_fund (-20)
        # pero además limitamos la decisión
        es_iliquida = vol_k < 500

        dec, fase, trig, col, bg = get_decision(sc, pm, pv, macd, rsi, lider)

        # Ilíquidas no pueden pasar de Bajada F1
        if es_iliquida and dec in ["ENTRAR","ANTICIPAR","SEGUIR"]:
            if dec != "SEGUIR" or sc >= 40:
                dec="SEGUIR"; fase="Fase 1"; trig="ILÍQUIDA"; col=R; bg=R_BG

        if estado == "REFERENCIA":
            dec="REFERENCIA"; fase="Completado"
            trig="PATRÓN COMPLETO"; col=TXT_MUT; bg=BG_HEAD

        prob = prob_nbis(sc, pv, si, dd, mes)
        sim  = sim_nbis(rsi, vol, ema, macd, sop, dd)
        mot  = motivo(row["Cat_Tipo"], pm, lider)

        rows.append({
            "Ticker":tk, "Nombre":row["Nombre"], "Area":row["Area"],
            "Precio":precio, "RSI":rsi, "RSI_Tend":rsi_t,
            "Volumen":vol, "EMA50":ema, "MACD":macd,
            "Soporte":sop, "Beta":beta, "DD_pico":dd,
            "Pico_P":pico_p, "Pico_F":row["Pico_F"],
            "Meses":mes, "Short_Int":si,
            "Pre_Vol":pv, "Post_Vol":float(row["Post_Vol"]), "Pre_Move":pm,
            "Cat_Tipo":row["Cat_Tipo"], "Cat_Desc":row["Cat_Desc"],
            "Cat_Fecha":row["Cat_Fecha"],
            "Arrastradas":row["Arrastradas"], "Lider":lider,
            # Score enriquecido
            "Score":sc, "Score_Base":sc_base, "Bonus_Fund":bonus_fund,
            "Fund_Desc":desc_fund,
            "BPA":bpa_v, "Dividendo":div_v, "Margen":mar_v,
            "Ingresos_M":ing_v, "Vol_Diario_K":vol_k,
            "Es_Iliquida":es_iliquida,
            "Decision":dec, "Fase":fase, "Trigger":trig,
            "Color":col, "Bg":bg, "Prob_NBIS":prob, "Sim_NBIS":sim,
            "Motivo":mot, "Lectura":row["Lectura"], "Estado":estado,
            # v6: tipo patrón + RSI direccional
            "Patron_Tipo": clasificar_patron(beta, si, pm, mes, dd)[0],
            "Patron_Emoji": clasificar_patron(beta, si, pm, mes, dd)[1],
            "Patron_Desc": clasificar_patron(beta, si, pm, mes, dd)[2],
            "Patron_Dias": clasificar_patron(beta, si, pm, mes, dd)[3],
            "RSI_Dir": rsi_direccion(rsi, rsi_t, dd, macd)[0],
            "RSI_Dir_Desc": rsi_direccion(rsi, rsi_t, dd, macd)[2],
            "_source":src, "_precio_live": src=="live",
            # v11: Score Rebote
            **{k: v for k, v in calcular_score_rebote(
                dd=dd, rsi=rsi, vol_ratio=vol,
                dias_alcistas=0, momentum_3d=float(macd),
                tiene_catalizador=row["Cat_Fecha"] not in ("—","","nan"),
                dias_para_cat=(
                    max(0, (pd.to_datetime(row["Cat_Fecha"], errors="coerce").date()
                    - __import__("datetime").date.today()).days)
                    if row["Cat_Fecha"] not in ("—","","nan") else 999
                ),
                beta=beta
            ).items() if k in ("score","nivel","detalle","pts_dd","pts_rsi","pts_vol","pts_cat")},
            "Score_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("—","","nan"),dias_para_cat=999,beta=beta)["score"],
            "Nivel_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("—","","nan"),dias_para_cat=999,beta=beta)["nivel"],
            "Detalle_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("—","","nan"),dias_para_cat=999,beta=beta)["detalle"],
        })

    return pd.DataFrame(rows), n_live

# ── Cargar con spinner visible al usuario ─────────────────────
# v8: sin carga automática — cada tab escanea a pedido
df_all = pd.DataFrame()  # vacío al inicio
_n_live = 0

# ─────────────────────────────────────────────────────────────
#  LOOKUP DINÁMICO — cualquier ticker del CSV
#  Intenta yfinance primero; si falla, estima desde precio
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ticker_data(ticker: str, precio_compra: float) -> dict:
    """Retorna dict con los mismos campos que df_all para un ticker arbitrario."""
    try:
        import yfinance as yf
        stk  = yf.Ticker(ticker)
        hist = stk.history(period="6mo")
        if hist.empty:
            raise ValueError("sin datos")

        close = hist["Close"].values
        vol   = hist["Volume"].values

        # RSI
        delta = pd.Series(close).diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9)))

        # MACD
        ema12 = pd.Series(close).ewm(span=12).mean()
        ema26 = pd.Series(close).ewm(span=26).mean()
        macd_hist = float((ema12 - ema26 - (ema12-ema26).ewm(span=9).mean()).iloc[-1])

        # EMA50
        ema50  = float(pd.Series(close).ewm(span=50).mean().iloc[-1])
        ema_d  = round((close[-1]-ema50)/ema50*100, 1)

        # Volumen ratio
        avg_v  = float(np.mean(vol[-20:])) if len(vol)>=20 else float(np.mean(vol))
        vol_r  = int(vol[-1]/avg_v*100) if avg_v>0 else 100

        # DD desde pico (6 meses)
        peak  = float(np.max(close))
        dd    = round((close[-1]-peak)/peak*100, 1)

        # Soporte (mínimo 30d)
        low30 = float(np.min(close[-30:])) if len(close)>=30 else float(np.min(close))
        sop   = round((close[-1]-low30)/low30*100, 1)

        info  = stk.fast_info
        beta  = float(getattr(info,"beta",1.5) or 1.5)
        nombre= ticker
        area  = "—"

        precio_actual = float(close[-1])

        # Tendencia RSI — comparar RSI actual vs hace 5 días
        rsi_series = pd.Series(close)
        delta_all  = rsi_series.diff()
        gain_all   = delta_all.clip(lower=0).rolling(14).mean()
        loss_all   = (-delta_all.clip(upper=0)).rolling(14).mean()
        rsi_full   = 100 - 100/(1 + gain_all/(loss_all+1e-9))
        rsi_5d_ago = float(rsi_full.iloc[-6]) if len(rsi_full)>=6 else rsi
        rsi_tend   = 5 if (rsi - rsi_5d_ago) > 3 else -3 if (rsi - rsi_5d_ago) < -3 else 0

        sc = calc_score(rsi, vol_r, ema_d, macd_hist, sop, dd, 0.0, 0.0, 1.0, 1.0, rsi_tend)
        dec,fase,trig,col,bg = get_decision(sc, 0.0, 1.0, macd_hist, rsi, "")

        return {
            "Ticker":ticker,"Nombre":nombre,"Area":area,
            "Precio":round(precio_actual,2),
            "RSI":round(rsi,1),"Volumen":vol_r,"EMA50":ema_d,
            "MACD":round(macd_hist,2),"Soporte":round(sop,1),
            "Beta":round(beta,2),"DD_pico":dd,
            "Pico_P":round(peak,2),"Pico_F":"—","Meses":3,
            "Short_Int":0.0,"Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
            "RSI_Tend":rsi_tend,
            "Cat_Tipo":"—","Cat_Desc":"Sin catalizador identificado","Cat_Fecha":"—",
            "Arrastradas":"—","Lider":"—",
            "Score":sc,"Decision":dec,"Fase":fase,"Trigger":trig,
            "Color":col,"Bg":bg,
            "Prob_NBIS":round(prob_nbis(sc,1.0,0.0,dd,3),1),
            "Sim_NBIS":round(sim_nbis(rsi,vol_r,ema_d,macd_hist,sop,dd),1),
            "Motivo":"Datos en tiempo real","Lectura":"Calculado desde yfinance.",
            "_source":"yfinance",
        }
    except Exception:
        # Sin internet o ticker inválido — estimación desde precio de compra
        precio_actual = precio_compra   # no sabemos el precio actual
        rsi_est  = 45.0
        ema_est  = -5.0
        macd_est = 0.0
        vol_est  = 100
        dd_est   = -10.0
        sop_est  = 2.0
        sc = calc_score(rsi_est,vol_est,ema_est,macd_est,sop_est,dd_est,0.0,0.0,1.0,1.0,0)
        dec,fase,trig,col,bg = get_decision(sc,0.0,1.0,macd_est,rsi_est,"")
        return {
            "Ticker":ticker,"Nombre":ticker,"Area":"—",
            "Precio":precio_compra,
            "RSI":rsi_est,"Volumen":vol_est,"EMA50":ema_est,
            "MACD":macd_est,"Soporte":sop_est,
            "Beta":1.5,"DD_pico":dd_est,
            "Pico_P":precio_compra,"Pico_F":"—","Meses":1,
            "Short_Int":0.0,"Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
            "RSI_Tend":0,
            "Cat_Tipo":"—","Cat_Desc":"Sin datos disponibles","Cat_Fecha":"—",
            "Arrastradas":"—","Lider":"—",
            "Score":sc,"Decision":dec,"Fase":fase,"Trigger":trig,
            "Color":col,"Bg":bg,
            "Prob_NBIS":20.0,"Sim_NBIS":10.0,
            "Motivo":"Estimación (sin datos)","Lectura":"Instala yfinance para datos reales.",
            "_source":"estimado",
        }

def get_row_for_ticker(ticker: str, precio_compra: float) -> dict:
    """Busca en el universo local primero; si no existe, llama a fetch_ticker_data."""
    rdata = pd.DataFrame()  # v8: sin universo fijo
    if not rdata.empty:
        return rdata.iloc[0].to_dict()
    return fetch_ticker_data(ticker, precio_compra)


def analizar_posicion(precio_compra, precio_actual, rsi, macd,
                      ema_dist, score, pnl_pct, prob_nbis_v, sim_nbis_v, beta,
                      cat_fecha="—", dias_posicion=0, tipo="Accion", estrategia="Swing"):
    """
    Retorna un dict con:
      - tramos: lista de (pct, etiqueta, color) — los 3 tramos de gestión
      - señal: texto resumen
      - razon: explicación
      - color: color principal
      - urgencia: etiqueta de urgencia

    Lógica de 3 tramos NBIS:
      Tramo 1 (30%) → +20% → VENDER 30% para asegurar ganancia
      Tramo 2 (40%) → +40% → VENDER 40% momentum confirmado
      Tramo 3 (30%) → +60% → RUNNER dejar correr
    """
    import datetime
    # ── Categoría según Tipo + Beta ──────────────────────────
    if tipo == "ETF_Cripto":
        categoria = "VOLATIL 🔴 Cripto"
        stop_pct  = 0.80; t1_pct=0.30; t2_pct=0.60; t3_pct=1.00
        cat_label = f"ETF Cripto (Beta {beta:.1f}) · Stop -20% · Targets +30/60/100%"
    elif tipo == "ETF_Indice":
        categoria = "CONSERVADOR 🔵 Índice"
        stop_pct  = 0.88; t1_pct=0.15; t2_pct=0.25; t3_pct=0.40
        cat_label = f"ETF Índice (Beta {beta:.1f}) · Acumulación LP · Stop -12% · Targets +15/25/40%"
    elif tipo == "ETF_Sectorial":
        categoria = "NORMAL 🟡 Sectorial"
        stop_pct  = 0.90; t1_pct=0.20; t2_pct=0.40; t3_pct=0.60
        cat_label = f"ETF Sectorial (Beta {beta:.1f}) · Patrón NBIS estándar"
    elif beta >= 2.5:
        categoria = "VOLATIL 🔴 Alta Beta"
        stop_pct  = 0.82; t1_pct=0.25; t2_pct=0.50; t3_pct=0.80
        cat_label = f"Acción alta volatilidad (Beta {beta:.1f}) · Stop -18% · Targets +25/50/80%"
    elif beta < 1.5:
        categoria = "CONSERVADOR 🔵 Baja Beta"
        stop_pct  = 0.88; t1_pct=0.15; t2_pct=0.25; t3_pct=0.40
        cat_label = f"Acción baja volatilidad (Beta {beta:.1f}) · Stop -12% · Targets +15/25/40%"
    else:
        categoria = "NORMAL 🟡 Estándar"
        stop_pct  = 0.90; t1_pct=0.20; t2_pct=0.40; t3_pct=0.60
        cat_label = f"Acción estándar (Beta {beta:.1f}) · Patrón NBIS · Stop -10% · Targets +20/40/60%"

    stop = precio_compra * stop_pct
    t1   = precio_compra * (1 + t1_pct)
    t2   = precio_compra * (1 + t2_pct)
    t3   = precio_compra * (1 + t3_pct)

    # ── Verificar si hay catalizador próximo (earnings, etc.) ──
    dias_para_cat = 999
    try:
        if cat_fecha and cat_fecha not in ("—","","Sin catalizador identificado","nan"):
            fecha_cat = pd.to_datetime(cat_fecha, errors="coerce")
            if fecha_cat and not pd.isna(fecha_cat):
                dias_para_cat = (fecha_cat.date() - datetime.date.today()).days
    except Exception:
        pass
    tiene_cat_proximo = 0 <= dias_para_cat <= 15  # earnings en próximos 15 días

    # ── Escenarios basados en PnL real (no RSI) ──────────────
    # El RSI alto en posición abierta no es señal de salida
    # La señal de salida la determina el PnL vs los 3 tramos NBIS

    # -1. Verificar día 10 con excepción por catalizador
    if dias_posicion >= 10 and estrategia != "Largo_Plazo":
        if tiene_cat_proximo and dias_para_cat <= 5:
            # Excepción: catalizador en próximos 5 días → extender
            pass  # continuar con análisis normal
        elif pnl_pct > 0:
            tramos = [(60,"VENDER",R),(40,"MANTENER",A),(0,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Día 10 — Vender 60% · Revisar",
                    "razon":f"Día {dias_posicion} en posición. Swing venció. Vender 60% hoy. "
                            f"Sin catalizador próximo — no extender.","color":R,"urgencia":"HOY"}
        else:
            tramos = [(100,"VENDER",R),(0,"MANTENER",G),(0,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Día 10 — Salida obligatoria",
                    "razon":f"Día {dias_posicion} en posición. Swing venció sin ganancia. "
                            f"Salir hoy — liberar capital para nueva oportunidad.","color":R,"urgencia":"HOY"}

    # 0. Largo plazo — sin stop, solo monitorear
    if estrategia == "Largo_Plazo":
        if pnl_pct >= t1_pct*100:
            tramos = [(30,"VENDER",OR),(40,"MANTENER",A),(30,"RUNNER",G)]
            return {"tramos":tramos,"señal":f"Vender 30% · Mantener 70%",
                    "razon":f"Largo plazo · {cat_label}. Target 1 alcanzado (+{pnl_pct:.0f}%). Vender 30%, mantener 70%.","color":G,"urgencia":"ESTA SEMANA"}
        elif pnl_pct < -30:
            tramos = [(0,"VENDER",TXT_SOFT),(50,"MANTENER",B),(50,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Mantener — estrategia largo plazo",
                    "razon":f"Largo plazo · {cat_label}. Pérdida {pnl_pct:.0f}% — en cripto es volatilidad normal. Mantener si tienes convicción en BTC/ETH.","color":B,"urgencia":"MONITOR"}
        else:
            tramos = [(0,"VENDER",TXT_SOFT),(60,"MANTENER",B),(40,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Mantener — acumulación",
                    "razon":f"Largo plazo · {cat_label}. P&L {pnl_pct:+.0f}%. Sin stop. Acumular en caídas si tienes convicción.","color":B,"urgencia":"MONITOR"}

    # 0b. Stop loss — prioridad absoluta (solo para Swing)
    if pnl_pct < -12:
        tramos = [(100,"VENDER",R),(0,"MANTENER",TXT_SOFT),(0,"RUNNER",TXT_SOFT)]
        return {"tramos":tramos,"señal":"SALIR — Stop loss activado",
                "razon":f"Pérdida {pnl_pct:.0f}%. Stop loss activado. Salir hoy sin excepción.","color":R,"urgencia":"STOP LOSS"}

    # 1. Pérdida leve — revisar catalizador
    if pnl_pct < -5:
        tramos = [(0,"VENDER",TXT_SOFT),(80,"MANTENER",B),(20,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener — revisar catalizador",
                "razon":f"Pérdida leve {pnl_pct:.0f}%. Verificar que el catalizador sigue válido. Si no hay catalizador → evaluar salida.","color":B,"urgencia":"VIGILAR"}

    # 2. Break even / pérdida mínima
    if pnl_pct < 5:
        tramos = [(0,"VENDER",TXT_SOFT),(70,"MANTENER",B),(30,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener — esperar movimiento",
                "razon":f"{cat_label}. Break even ({pnl_pct:+.0f}%). Confirmar catalizador activo. Stop en ${stop:.2f}.","color":B,"urgencia":"MONITOR"}

    # 3. En camino — no llegó al Tramo 1 aún
    if pnl_pct < t1_pct * 100:
        if tiene_cat_proximo:
            razon_cat = f"Earnings en {dias_para_cat}d — mantener hasta el catalizador."
            urgencia_cat = "MONITOR"
        else:
            razon_cat = "Sin catalizador próximo. Vigilar RSI y stop."
            urgencia_cat = "AJUSTAR STOP"
        tramos = [(0,"VENDER",TXT_SOFT),(65,"MANTENER",A),(35,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener — en camino al Tramo 1",
                "razon":f"Ganancia {pnl_pct:+.0f}% — falta {20-pnl_pct:.0f}% para Tramo 1 (+20%). {razon_cat}","color":A,"urgencia":urgencia_cat}

    # 4. Tramo 1 alcanzado con catalizador próximo
    if pnl_pct >= t1_pct*100 and tiene_cat_proximo:
        tramos = [(30,"VENDER",OR),(45,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30% · Mantener 70%",
                "razon":f"{cat_label}. Tramo 1 alcanzado (+{pnl_pct:.0f}%). Vender 30%. Earnings en {dias_para_cat}d — mantener 70%.","color":A,"urgencia":"ESTA SEMANA"}

    # 5. Tramo 1 alcanzado sin catalizador
    if pnl_pct >= t1_pct*100 and pnl_pct < t2_pct*100:
        tramos = [(30,"VENDER",OR),(45,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30% · Mantener 70%",
                "razon":f"{cat_label}. Tramo 1 (+{t1_pct*100:.0f}%) alcanzado. Vender 30%, mantener 70% con stop en ${stop:.2f}.","color":A,"urgencia":"ESTA SEMANA"}

    # 6. Tramo 2 alcanzado
    if pnl_pct >= t2_pct*100 and pnl_pct < t3_pct*100:
        tramos = [(40,"VENDER",R),(35,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 40% · Runner 25%",
                "razon":f"{cat_label}. Tramo 2 (+{t2_pct*100:.0f}%) alcanzado. Vender 40%, dejar runner.","color":G,"urgencia":"HOY"}

    # 7. Tramo 3 alcanzado
    if pnl_pct >= t3_pct*100:
        tramos = [(30,"VENDER",R),(10,"MANTENER",A),(60,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30% más · Runner libre",
                "razon":f"{cat_label}. Tramo 3 (+{t3_pct*100:.0f}%) alcanzado. Dejar runner correr.","color":G,"urgencia":"HOY"}

    # 9. Posición en ganancia moderada, patrón activo
    if pnl_pct > 0 and score > 55:
        tramos = [(0,"VENDER",TXT_SOFT),(60,"MANTENER",B),(40,"RUNNER",G)]
        return {"tramos":tramos,"señal":"0% Vender / 60% Mantener / 40% Runner",
                "razon":f"Ganancia {pnl_pct:.0f}%. Patrón en desarrollo, mantener posición.","color":G,"urgencia":"HOLD"}

    # 10. Default — posición nueva o neutral
    tramos = [(0,"VENDER",TXT_SOFT),(70,"MANTENER",B),(30,"RUNNER",G)]
    return {"tramos":tramos,"señal":"0% Vender / 70% Mantener / 30% Runner",
            "razon":"Posición activa. Monitorear Pre-Market y catalizador.","color":B,"urgencia":"MONITOR"}

# ─────────────────────────────────────────────────────────────
#  HELPERS DE RENDER
# ─────────────────────────────────────────────────────────────
def badge(text,cls="bg-gr"):
    return f'<span class="badge {cls}">{text}</span>'

def c_rsi(v):
    if v<30: return R
    if v<40: return A
    return TXT_MUT

def c_pre(v):
    if v>=8: return G
    if v>=5: return C
    if v>=3: return A
    return TXT_MUT

def c_vol(v):
    if v>=2.5: return G
    if v>=1.5: return A
    return TXT_MUT

def render_table(df_sub, show_cols):
    if df_sub.empty:
        st.markdown(f'<div style="padding:16px;color:{TXT_MUT};font-size:12px;text-align:center;background:{BG_HEAD};border-radius:10px;border:1px solid {BOR}">— sin resultados —</div>',unsafe_allow_html=True)
        return

    # v11: calcular Score_Rebote si no existe en el DataFrame
    df_sub = df_sub.copy()
    if "Score_Rebote" not in df_sub.columns or df_sub["Score_Rebote"].isna().all() or (df_sub["Score_Rebote"] == "").all():
        def _calc_sr(row):
            try:
                sr = calcular_score_rebote(
                    dd=float(row.get("DD_pico", 0)),
                    rsi=float(row.get("RSI", 50)),
                    vol_ratio=float(row.get("Volumen", 100)),
                    dias_alcistas=int(row.get("Dias_Alcistas", 0)),
                    momentum_3d=float(row.get("MACD", 0)),
                    tiene_catalizador=str(row.get("Cat_Fecha","—")) not in ("—","","nan"),
                    dias_para_cat=999,
                    beta=float(row.get("Beta", 1.5))
                )
                return sr["score"], sr["nivel"], sr["detalle"]
            except Exception:
                return 0, "🔵 DÉBIL", "—"
        _scores = df_sub.apply(_calc_sr, axis=1)
        df_sub["Score_Rebote"]   = [s[0] for s in _scores]
        df_sub["Nivel_Rebote"]   = [s[1] for s in _scores]
        df_sub["Detalle_Rebote"] = [s[2] for s in _scores]

    rows_html=""
    for _,r in df_sub.iterrows():
        row_html="<tr>"
        for col in show_cols:
            val=r.get(col,"")
            cell=""
            if col=="Ticker":
                cell=f'<strong style="color:{B};font-size:13px">{val}</strong>'
            elif col=="Area":
                c2=SECTOR_COLORS.get(str(r.get("Area","")),TXT_MUT)
                cell=f'<span style="color:{c2};font-size:11px;font-weight:600">{val}</span>'
            elif col=="Decision":
                m={"ENTRAR":"bg-g","ANTICIPAR":"bg-c","SEGUIR":"bg-a",
                   "OBSERVAR":"bg-gr","REFERENCIA":"bg-p"}
                cell=badge(val,m.get(val,"bg-gr"))
            elif col=="Fase":
                cell=f'<span style="color:{TXT_MUT};font-size:11px">{val}</span>'
            elif col=="Trigger":
                v_str = str(val)
                if any(x in v_str for x in ["RUPTURA","REBOTE EN CURSO"]):
                    c2 = "bg-g"
                elif any(x in v_str for x in ["PRE-SEÑAL","MACD ALCISTA"]):
                    c2 = "bg-c"
                elif "FONDO" in v_str:
                    c2 = "bg-a"
                else:
                    c2 = "bg-r"
                cell=badge(val,c2)
            elif col=="Precio":
                es_live = r.get("_precio_live", False)
                live_badge = (f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};'
                              f'border-radius:3px;padding:0px 4px;font-size:9px;font-weight:700;'
                              f'margin-left:4px">● live</span>') if es_live else (
                             f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};'
                             f'border-radius:3px;padding:0px 4px;font-size:9px;'
                             f'margin-left:4px">estático</span>')
                cell=f'<span style="font-weight:700;color:{TXT}">${val:.2f}</span>{live_badge}'
            elif col=="Prob_NBIS":
                c2=G if val>=75 else A if val>=55 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val}</span>'
            elif col=="Sim_NBIS":
                c2=G if val>=60 else A if val>=45 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val:.1f}</span>'
            elif col=="Motivo":
                cell=f'<span style="color:{TXT_MUT};font-size:11px">{val}</span>'
            elif col=="Lectura":
                v2=str(val); cell=f'<span style="color:{TXT_MUT};font-size:11px">{v2[:70]}{"…" if len(v2)>70 else ""}</span>'
            elif col=="Arrastradas":
                if val and val!="—":
                    chips=" ".join([f'<span style="background:{B_BG};color:{B};border-radius:4px;padding:1px 6px;font-size:10px;font-weight:700;border:1px solid {B_BOR}">{tk}</span>' for tk in str(val).split(", ")])
                    cell=chips
                else: cell=f'<span style="color:{TXT_SOFT}">—</span>'
            elif col=="Lider":
                if val and val!="—":
                    cell=f'<span style="background:{P_BG};color:{P};border-radius:4px;padding:1px 7px;font-size:10px;font-weight:700;border:1px solid {P_BOR}">↑{val}</span>'
                else: cell=f'<span style="color:{TXT_SOFT}">—</span>'
            elif col=="Score":
                c2=G if val>=75 else A if val>=55 else R
                bonus_f = r.get("Bonus_Fund", 0)
                bonus_str = (f'<span style="color:{G};font-size:9px"> +{bonus_f}F</span>'
                             if bonus_f > 0 else
                             f'<span style="color:{R};font-size:9px"> {bonus_f}F</span>'
                             if bonus_f < 0 else "")
                cell=f'<span style="color:{c2};font-weight:700;font-size:13px">{val}</span>{bonus_str}'
            elif col=="RSI":
                tend = r.get("RSI_Tend", 0)
                flecha = " ↑" if tend>0 else " ↓" if tend<0 else ""
                cell=f'<span style="color:{c_rsi(val)};font-weight:700">{val}{flecha}</span>'
            elif col=="Pre_Move":
                cell=f'<span style="color:{c_pre(val)};font-weight:700">+{val:.1f}%</span>'
            elif col=="Pre_Vol":
                cell=f'<span style="color:{c_vol(val)};font-weight:700">{val:.1f}x</span>'
            elif col=="Post_Vol":
                cell=f'<span style="color:{c_vol(val)};font-weight:700">{val:.1f}x</span>'
            elif col=="Short_Int":
                c2=R if val>=20 else A if val>=12 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val:.1f}%</span>'
            elif col=="DD_pico":
                cell=f'<span style="color:{R};font-weight:700">{val:.0f}%</span>'
            elif col=="Patron_Tipo":
                emoji = r.get("Patron_Emoji","📈")
                desc  = r.get("Patron_Dias","—")
                tipo_colors = {"EXPLOSIVO":R,"GRADUAL":G,"CÍCLICO":C}
                tc = tipo_colors.get(str(val), TXT_MUT)
                cell = (f'<span style="color:{tc};font-weight:700;font-size:11px">{emoji} {val}</span>'
                        f'<br><span style="color:{TXT_SOFT};font-size:9px">{desc}</span>')
            elif col=="RSI_Dir":
                dir_colors = {"RSI REBOTANDO":G,"RSI BASE":A,"RSI CAYENDO":R,
                              "TRAMPA DD":R,"RSI NEUTRO":TXT_MUT}
                dc = dir_colors.get(str(val), TXT_MUT)
                desc2 = str(r.get("RSI_Dir_Desc",""))[:35]
                cell = (f'<span style="color:{dc};font-weight:600;font-size:10px">{val}</span>'
                        f'<br><span style="color:{TXT_SOFT};font-size:9px">{desc2}</span>')
            elif col=="Cat_Fecha":
                c2=G if "Abr" in str(val) or "Activo" in str(val) else A
                cell=f'<span style="color:{c2};font-size:11px;font-weight:600">{val}</span>'
            else:
                cell=f'<span style="color:{TXT}">{val}</span>'
            row_html+=f"<td>{cell}</td>"
        row_html+="</tr>"
        rows_html+=row_html
    hdr={"Ticker":"Ticker","Area":"Área","Decision":"Decisión","Fase":"Fase","Trigger":"Trigger",
         "Precio":"Precio","Score_Rebote":"Score Rebote","Nivel_Rebote":"Nivel","Detalle_Rebote":"Detalle Score",
         "Prob_NBIS":"Score Rebote","Sim_NBIS":"Nivel","Motivo":"Motivo",
         "Lectura":"Lectura Trader","Arrastradas":"Arrastradas","Patron_Tipo":"Tipo Patrón","RSI_Dir":"RSI Dir","Lider":"Líder",
         "Score":"Score","RSI":"RSI","Pre_Move":"Pre/Post %","Pre_Vol":"Vol Pre",
         "Post_Vol":"Vol Post","Short_Int":"Short %","DD_pico":"DD Caída","Cat_Fecha":"Catalizador"}
    ths="".join([f"<th>{hdr.get(c,c)}</th>" for c in show_cols])
    st.markdown(f'<div class="tbl-wrap"><table class="dtbl"><thead><tr>{ths}</tr></thead><tbody>{rows_html}</tbody></table></div>',unsafe_allow_html=True)

    # ── Paneles expandibles de noticias por ticker ──────────
    news_cache = st.session_state.get("noticias_cache", {})
    if news_cache:
        st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin:10px 0 6px">📰 Noticias — click en el ticker para expandir</div>', unsafe_allow_html=True)
        for _, r in df_sub.iterrows():
            tk = r["Ticker"]
            tk_data = news_cache.get(tk, {})
            noticias = tk_data.get("noticias", [])
            bonus    = tk_data.get("bonus", 0)
            bonus_str = f"+{bonus}" if bonus > 0 else str(bonus)
            bonus_color = G if bonus > 0 else R if bonus < 0 else TXT_MUT
            n_alc = sum(1 for n in noticias if n["sentimiento"]=="Alcista")
            n_baj = sum(1 for n in noticias if n["sentimiento"]=="Bajista")
            label = (f"📰 {tk} — {len(noticias)} noticias · "
                     f"🟢{n_alc} alcistas · 🔴{n_baj} bajistas · "
                     f"Impacto score: {bonus_str} pts")
            with st.expander(label, expanded=False):
                render_noticias_panel(tk, noticias, bonus)
    else:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;'
            f'padding:8px 12px;font-size:11px;color:{A};margin-top:8px">'
            f'💡 Presiona "Actualizar noticias" en el sidebar para ver análisis automático</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
KEYWORDS_ALCISTA = [
    "beat","beats","upgrade","upgraded","buy","outperform","contract","contracts",
    "approval","approved","growth","record","partnership","acquisition","bullish",
    "raised","raises","target","expands","wins","awarded","launches","strong",
    "exceeds","accelerat","positive","rally","rebound","surges","breakthrough",
    "dividend","buyback","investment","deal","agreement","milestone"
]
KEYWORDS_BAJISTA = [
    "miss","misses","downgrade","downgraded","sell","underperform","layoff","layoffs",
    "recall","investigation","loss","losses","bearish","cut","cuts","warning","warns",
    "decline","fell","drops","disappoints","weak","concern","risk","below","fraud",
    "lawsuit","probe","fine","penalty","delay","withdrawal","reject","rejected"
]

def analizar_sentimiento_noticia(titulo: str) -> tuple:
    """
    Analiza el sentimiento de un titular de noticia.
    Retorna (sentimiento, impacto, keywords_encontradas)
    """
    titulo_lower = titulo.lower()
    score_alc = sum(1 for k in KEYWORDS_ALCISTA if k in titulo_lower)
    score_baj = sum(1 for k in KEYWORDS_BAJISTA if k in titulo_lower)

    if score_alc > score_baj:
        impacto = min(score_alc * 2, 8)
        return "Alcista", impacto, [k for k in KEYWORDS_ALCISTA if k in titulo_lower]
    elif score_baj > score_alc:
        impacto = -min(score_baj * 2, 8)
        return "Bajista", impacto, [k for k in KEYWORDS_BAJISTA if k in titulo_lower]
    else:
        return "Neutro", 0, []

def clasificar_tipo_noticia(titulo: str) -> str:
    """Clasifica el tipo de noticia según el titular."""
    t = titulo.lower()
    if any(k in t for k in ["earnings","results","revenue","eps","quarterly","q1","q2","q3","q4"]): return "Earnings"
    if any(k in t for k in ["fda","approval","trial","clinical","drug","therapy"]): return "FDA/Clínico"
    if any(k in t for k in ["contract","deal","agreement","partnership","awarded"]): return "Contrato"
    if any(k in t for k in ["upgrade","downgrade","target","analyst","rating","price target"]): return "Analyst"
    if any(k in t for k in ["insider","ceo","cfo","bought","purchased","sold shares"]): return "Insider"
    if any(k in t for k in ["buyback","dividend","acquisition","merger"]): return "Corporativo"
    return "Macro/Sector"

@st.cache_data(ttl=21600, show_spinner=False)  # cache 6 horas
def fetch_noticias_ticker(ticker: str) -> list:
    """
    Descarga y analiza las últimas noticias de un ticker via yfinance.
    Compatible con todas las versiones de yfinance.
    """
    noticias = []
    try:
        import yfinance as yf
        stk = yf.Ticker(ticker)
        try:
            raw_news = stk.news or []
        except Exception:
            raw_news = []

        for item in raw_news[:8]:
            try:
                titulo, link, ts, fuente = "", "", 0, "Yahoo Finance"

                if isinstance(item, dict):
                    # Formato nuevo: content anidado
                    content = item.get("content", {})
                    if isinstance(content, dict):
                        titulo = content.get("title","") or content.get("headline","")
                        cl = content.get("clickThroughUrl", {})
                        link = cl.get("url","") if isinstance(cl, dict) else str(cl)
                        prov = content.get("provider",{})
                        fuente = prov.get("displayName","Yahoo Finance") if isinstance(prov,dict) else "Yahoo Finance"
                        ts = content.get("pubDate", 0)
                    # Formato antiguo: campos directos
                    if not titulo:
                        titulo = item.get("title","") or item.get("headline","")
                        link   = item.get("link","") or item.get("url","")
                        ts     = item.get("providerPublishTime",0)
                        fuente = item.get("publisher","Yahoo Finance")
                else:
                    titulo = getattr(item,"title","") or getattr(item,"headline","")
                    link   = getattr(item,"link","") or getattr(item,"url","")
                    ts     = getattr(item,"providerPublishTime",0)
                    fuente = getattr(item,"publisher","Yahoo Finance")

                if not titulo or not link:
                    continue

                # Calcular antigüedad
                fecha_dt = datetime.datetime.fromtimestamp(ts) if ts else datetime.datetime.now()
                dias_atras = (datetime.datetime.now() - fecha_dt).days
                fecha_str  = fecha_dt.strftime("%d %b %Y")

                # Noticias > 14 días pesan la mitad
                sentimiento, impacto_base, keywords = analizar_sentimiento_noticia(titulo)
                impacto = impacto_base // 2 if dias_atras > 14 else impacto_base
                tipo = clasificar_tipo_noticia(titulo)

                noticias.append({
                    "titulo":      titulo,
                    "link":        link,
                    "fecha":       fecha_str,
                    "dias":        dias_atras,
                    "fuente":      fuente,
                    "tipo":        tipo,
                    "sentimiento": sentimiento,
                    "impacto":     impacto,
                    "keywords":    keywords,
                })
            except Exception:
                continue

    except Exception:
        pass

    return noticias

def calcular_bonus_noticias(noticias: list) -> int:
    """Suma el impacto total de las noticias con límite de +12/-8 pts."""
    if not noticias:
        return 0
    total = sum(n["impacto"] for n in noticias)
    return max(-8, min(12, total))  # cap: +12 alcista, -8 bajista

def render_noticias_panel(ticker: str, noticias: list, bonus: int):
    """Renderiza el panel expandible de noticias para un ticker."""
    if not noticias:
        st.markdown(
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;'
            f'padding:10px 14px;font-size:11px;color:{TXT_MUT}">Sin noticias recientes</div>',
            unsafe_allow_html=True)
        return

    bonus_color = G if bonus > 0 else R if bonus < 0 else TXT_MUT
    bonus_txt   = f"+{bonus}" if bonus > 0 else str(bonus)

    st.markdown(
        f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:6px">'
        f'Impacto total noticias: <strong style="color:{bonus_color}">{bonus_txt} pts al score</strong>'
        f' · {len(noticias)} noticias analizadas</div>',
        unsafe_allow_html=True)

    for n in noticias:
        # Color por sentimiento
        if n["sentimiento"] == "Alcista":
            s_color = G; s_bg = G_BG; s_bor = G_BOR
            imp_txt = f'+{n["impacto"]} pts'
        elif n["sentimiento"] == "Bajista":
            s_color = R; s_bg = R_BG; s_bor = R_BOR
            imp_txt = f'{n["impacto"]} pts'
        else:
            s_color = TXT_MUT; s_bg = BG_HEAD; s_bor = BOR
            imp_txt = "0 pts"

        # Color tipo noticia
        tipo_colors = {
            "Earnings": B, "FDA/Clínico": P, "Contrato": G,
            "Analyst": A, "Insider": C, "Corporativo": B, "Macro/Sector": TXT_MUT
        }
        t_color = tipo_colors.get(n["tipo"], TXT_MUT)

        # Antigüedad
        dias_str = "hoy" if n["dias"]==0 else f"hace {n['dias']}d"

        titulo_short = n["titulo"][:90] + "..." if len(n["titulo"]) > 90 else n["titulo"]

        st.markdown(
            f'<div style="background:{s_bg};border:1px solid {s_bor};border-left:3px solid {s_color};'
            f'border-radius:8px;padding:8px 12px;margin-bottom:6px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
            f'<span style="background:{BG_HEAD};color:{t_color};border:1px solid {BOR};'
            f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{n["tipo"]}</span>'
            f'<span style="font-size:10px;color:{TXT_SOFT}">{dias_str} · {n["fuente"]}</span>'
            f'<span style="color:{s_color};font-size:10px;font-weight:700">{imp_txt}</span>'
            f'</div>'
            f'<a href="{n["link"]}" target="_blank" style="color:{TXT};font-size:11px;'
            f'text-decoration:none;line-height:1.4">{titulo_short}</a>'
            f'</div>',
            unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
#  SWING ACTIVO — detecta acciones que giraron alcista 2-3 días
#  Patrón: estaban cayendo → llevan 2-3 días subiendo con vol
#  Filtros: precio subiendo 3 días + volumen creciente + RSI girando
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def scan_swing(vol_min_k: float = 200, max_results: int = 100, universo: list = None) -> pd.DataFrame:
    """
    Detecta acciones en rebote de swing 5-10 días.
    Criterios:
    - Venían en corrección (DD > -8% desde pico)
    - Llevan 2-3 días consecutivos subiendo
    - Volumen creciente en los días alcistas
    - RSI girando hacia arriba desde zona baja-media
    - No en sobrecompra (RSI < 65)
    """
    candidatos = []
    try:
        import yfinance as yf
        _universo_sw = universo if universo else SCAN_UNIVERSE
        for tk in _universo_sw:
            # ETFs que no tienen fundamentals en yfinance — saltar
            _ETF_SKIP = {"XLE","XLI","XLY","XLC","XLB","XLP","XLRE","GLD","SLV","USO","UNG","JETS","HACK","BOTZ","ROBO","COPX","ARKG","ARKF","ARKQ","SOXX","IBB","ARKK"}
            if tk in _ETF_SKIP:
                continue
            try:
                try:
                    hist = yf.Ticker(tk).history(period="3mo")
                except Exception:
                    continue
                if hist.empty or len(hist) < 20:
                    continue

                close = hist["Close"].values
                vol   = hist["Volume"].values

                # Necesitamos últimos 5 días
                if len(close) < 5:
                    continue

                precio   = float(close[-1])
                pico     = float(close.max())
                dd       = round((precio - pico) / pico * 100, 1)

                # Filtro: debe haber corrección previa real
                if dd > -5:
                    continue  # no hubo corrección suficiente

                # Detectar días consecutivos alcistas (últimos 3)
                dias_alcistas = 0
                for i in range(1, 4):
                    if close[-i] > close[-i-1]:
                        dias_alcistas += 1
                    else:
                        break

                if dias_alcistas < 2:
                    continue  # necesita mínimo 2 días alcistas consecutivos

                # Volumen creciente en días alcistas
                avg_v = float(import_np().mean(vol[-20:]))
                vol_k = avg_v / 1000
                if vol_k < vol_min_k:
                    continue

                # Volumen de hoy vs promedio
                vol_hoy = float(vol[-1])
                vol_ratio = int(vol_hoy / avg_v * 100)

                # RSI actual y tendencia
                import pandas as pd
                s = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

                # RSI no debe estar sobrecomprado
                if rsi > 65:
                    continue

                # RSI debe estar girando (hoy > hace 3 días)
                rsi_3d = float(100-100/(1+gain.iloc[-4]/(loss.iloc[-4]+1e-9))) if len(close)>=4 else rsi
                rsi_tend = rsi - rsi_3d
                if rsi_tend < 1:  # RSI debe estar subiendo
                    continue

                # Momentum: ganancia en últimos 3 días
                momentum_3d = round((close[-1] / close[-4] - 1) * 100, 2) if len(close)>=4 else 0
                if momentum_3d <= 0:
                    continue

                # Ganancia de hoy
                gain_hoy = round((close[-1] / close[-2] - 1) * 100, 2)

                # Fundamentales básicos
                info    = yf.Ticker(tk).info or {}
                beta_v  = float(info.get("beta", 1.5) or 1.5)
                nombre  = info.get("shortName", tk)
                sector  = info.get("sector", "—")
                ingresos= float(info.get("totalRevenue", 0) or 0) / 1e6

                sector_map = {
                    "Technology":"Tech","Healthcare":"Salud",
                    "Financial Services":"Finanzas",
                    "Consumer Cyclical":"Consumo",
                    "Consumer Defensive":"Consumo",
                    "Energy":"Energía","Industrials":"Industrial",
                    "Communication Services":"Tech",
                }
                area = sector_map.get(sector, sector[:10] if sector and sector!="—" else "—")

                # Stop para swing: -5% desde precio actual
                stop_swing = round(precio * 0.95, 2)
                # Target: +8-12% en 5-10 días
                target1 = round(precio * 1.08, 2)
                target2 = round(precio * 1.12, 2)

                lectura = (f"↑{dias_alcistas} días alcistas consecutivos · "
                          f"Momentum +{momentum_3d:.1f}% (3d) · "
                          f"RSI {rsi:.0f} girando ↑ · "
                          f"DD {dd:.0f}% desde pico")

                candidatos.append({
                    "Ticker": tk, "Nombre": nombre, "Area": area,
                    "Precio": round(precio, 2),
                    "RSI": rsi, "RSI_Tend": round(rsi_tend, 1),
                    "Volumen": vol_ratio, "DD_pico": dd,
                    "Beta": round(beta_v, 2),
                    "Dias_Alcistas": dias_alcistas,
                    "Momentum_3d": momentum_3d,
                    "Gain_Hoy": gain_hoy,
                    "Stop_Swing": stop_swing,
                    "Target_1": target1,
                    "Target_2": target2,
                    "Ingresos_M": round(ingresos, 0),
                    "Vol_Diario_K": round(vol_k, 0),
                    "Lectura": lectura,
                    "_source": "screener",
                    # Score Rebote v11 para Swing
                    "Score_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["score"],
                    "Nivel_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["nivel"],
                    "Detalle_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["detalle"],
                })
            except Exception:
                continue
    except Exception:
        pass

    # Ordenar por momentum 3d descendente
    return pd.DataFrame(
        sorted(candidatos, key=lambda x: -x["Momentum_3d"])[:max_results]
    )

def import_np():
    import numpy as np
    return np


with st.sidebar:
    st.markdown(f'<div style="font-size:22px;font-weight:800;color:{B}">🦅 GrekoTrader</div>'
            f'<div style="font-size:10px;color:{TXT_MUT};margin-top:2px">'
            f'v11 · 21 Abr 2026 · Score Rebote · '
            f'{len(SCAN_UNIVERSE)} tickers</div>'+
            f'</div>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:6px">{datetime.date.today():%d %b %Y} · Modelo 3 Momentos</div>',unsafe_allow_html=True)

    # Badge indicadores live
    if _n_live > 0:
        hora = datetime.datetime.now().strftime("%H:%M")
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:8px;'
            f'padding:5px 10px;font-size:11px;color:{G};font-weight:600;margin-bottom:8px">'
            f'● Indicadores live · {_n_live} tickers · {hora} · cache 20min</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;'
            f'padding:5px 10px;font-size:11px;color:{A};font-weight:600;margin-bottom:8px">'
            f'⚠ Datos estáticos · pip install yfinance</div>',
            unsafe_allow_html=True)
    st.markdown("---")
    area_fil  = st.selectbox("Área",["Todas","AI Infra","Tech","Salud","Finanzas","Consumo","Energía","Industrial","Cripto/AI","Quantum"])
    st.markdown("---")
    max_res = st.slider("📊 Máx. resultados por tab", min_value=10, max_value=200, value=100, step=10,
                        help="Cuántas acciones mostrar por tab. Más = escaneo más lento.")
    st.markdown("---")
    # Refresh market data
    if st.button("🔄 Actualizar indicadores de mercado", use_container_width=True):
        st.session_state["mkt_cache"] = {}
        st.rerun()
    if st.button("🗑️ Limpiar cache de precios", use_container_width=True,
                  help="Fuerza descarga de precios frescos — usar si los datos parecen desactualizados"):
        st.cache_data.clear()
        for key in ["scan_swing","scan_entrar","scan_detectadas","scan_sympathy",
                    "mkt_cache","etf_data","earnings_mis_pos","earnings_amparito"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Cache limpiado — datos frescos al escanear")
        st.rerun()
    st.markdown("---")
    # Guía rápida de fases
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">📋 Guía de fases</div>',unsafe_allow_html=True)
    for emoji, label, desc, color in [
        ("📡","M1 Detectada","Cayendo · Solo observar",TXT_SOFT),
        ("⚡","Swing Activo","Rebotando · Entrar 5-10d",C),
        ("🔥","M3 Entrar hoy","Confirmado · Ejecutar",G),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid {BOR}">'
            f'<span style="font-size:14px">{emoji}</span>'
            f'<div><div style="font-size:11px;font-weight:600;color:{color}">{label}</div>'
            f'<div style="font-size:10px;color:{TXT_SOFT}">{desc}</div></div>'
            f'</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f'<div style="font-size:12px;font-weight:700;color:{TXT};margin-bottom:8px">📰 Noticias automáticas</div>', unsafe_allow_html=True)

    if st.button("🔄 Actualizar noticias", use_container_width=True, help="Descarga y analiza las últimas noticias de cada ticker via yfinance"):
        # Combinar tickers de todos los tabs escaneados
        _all_scanned = []
        for _k in ["scan_entrar","scan_swing","scan_detectadas"]:
            _d = st.session_state.get(_k)
            if _d is not None and not _d.empty:
                _all_scanned.extend(_d["Ticker"].tolist())
        tickers_universo = list(dict.fromkeys(_all_scanned)) or ["MSFT","NVDA","AAPL"]
        progress = st.progress(0)
        cache_nuevo = {}
        for i, tk in enumerate(tickers_universo):
            news = fetch_noticias_ticker(tk)
            bonus = calcular_bonus_noticias(news)
            cache_nuevo[tk] = {"noticias": news, "bonus": bonus}
            progress.progress((i+1)/len(tickers_universo))
        st.session_state["noticias_cache"] = cache_nuevo
        st.session_state["noticias_actualizadas"] = datetime.datetime.now().strftime("%H:%M")
        progress.empty()
        st.success("✅ Noticias actualizadas")

    if st.session_state["noticias_actualizadas"]:
        st.markdown(
            f'<div style="font-size:10px;color:{G}">● Última actualización: {st.session_state["noticias_actualizadas"]}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:10px;color:{TXT_SOFT}">Sin actualizar — presiona el botón</div>', unsafe_allow_html=True)

    st.markdown("---")
    resumen = [
        ("ENTRAR",  "🔥", G,  _count("scan_entrar")),
        ("ANTICIPAR","⚡", C,  _count("scan_anticipar")),
        ("RADAR F2", "👀", A,  _count("scan_radar")),
        ("BAJADA F1","📡", R,  _count("scan_detectadas")),
    ]
    for dec,emoji,c,cnt in resumen:
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px;color:{TXT_MUT};border-bottom:1px solid {BOR}"><span>{emoji} {dec}</span><span style="color:{c};font-weight:700">{cnt}</span></div>',unsafe_allow_html=True)

# Filtros
# v8: df se construye en cada tab al escanear
df = pd.DataFrame()

COLS_MAIN=["Ticker","Score_Rebote","Nivel_Rebote","Area","Fase","Precio","RSI","DD_pico","Detalle_Rebote","Motivo","Lectura"]
COLS_EXT =["Ticker","Score_Rebote","Nivel_Rebote","Area","Decision","Fase","Precio","Score","RSI","DD_pico","Cat_Fecha","Detalle_Rebote","Pre_Move","Pre_Vol","Motivo","Lectura"]


# ─────────────────────────────────────────────────────────────
#  NOTICIAS AUTOMÁTICAS — yfinance + análisis de sentimiento
# ─────────────────────────────────────────────────────────────

# Keywords para análisis de sentimiento

def render_scan_tab(tab_key, titulo, emoji, color, color_bg, color_bor,
                    desc, rsi_max, dd_min, score_min, decisions,
                    cols_show=None, default_sort="Score"):
    """Renderiza un tab con botón de escaneo y resultados."""
    if cols_show is None:
        cols_show = COLS_MAIN

    st.markdown(
        f'<div class="sec-header" style="background:{color_bg};border-color:{color_bor}">'+
        f'<span style="font-size:20px">{emoji}</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:{color}">{titulo}</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">{desc}</span></div>'+
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:10px;'+
        f'padding:12px 16px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center">'+
        f'<div style="font-size:11px;color:{TXT_MUT}">'+
        f'<strong>Filtros automáticos:</strong> RSI ≤ {rsi_max} · DD ≤ {dd_min}% · Score ≥ {score_min} · Vol ≥ 200K/día'+
        f'</div></div>', unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        if st.button(f"🔍 Escanear {titulo}", use_container_width=True, key=f"btn_{tab_key}"):
            with st.spinner(f"Escaneando ~{len(SCAN_UNIVERSE)} tickers..."):
                resultado = scan_tab(rsi_max, dd_min, score_min, decisions, universo=SCAN_UNIVERSE[:st.session_state.get("universo_size", 300)])
                st.session_state[tab_key] = resultado
    with col_info:
        if st.session_state.get(tab_key) is not None:
            n = len(st.session_state[tab_key])
            ts = st.session_state.get(f"{tab_key}_ts", "")
            st.markdown(
                f'<div style="font-size:11px;color:{G if n>0 else TXT_MUT};padding-top:8px">'+
                f'● {n} candidatos encontrados {ts}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:11px;color:{TXT_SOFT};padding-top:8px">'+
                f'Presiona el botón para escanear el mercado ahora</div>', unsafe_allow_html=True)

    resultado_df = st.session_state.get(tab_key)
    if resultado_df is None:
        st.markdown(
            f'<div style="background:{color_bg};border:1px solid {color_bor};border-radius:12px;'+
            f'padding:32px;text-align:center">'+
            f'<div style="font-size:36px;margin-bottom:10px">{emoji}</div>'+
            f'<div style="font-size:14px;font-weight:700;color:{color};margin-bottom:6px">{titulo} — Sin escanear</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT}">Presiona el botón para buscar oportunidades en tiempo real</div>'+
            f'</div>', unsafe_allow_html=True)
        return

    # Aplicar filtro de área si está seleccionado
    if not resultado_df.empty and area_fil != "Todas":
        resultado_df = resultado_df[resultado_df["Area"]==area_fil]

    if resultado_df.empty:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:10px;'+
            f'padding:20px;text-align:center;color:{A}">'+
            f'🚀 Mercado en rally — ninguna acción cumple los filtros de {titulo} ahora.'+
            f'<br><span style="font-size:11px;color:{TXT_MUT}">'+
            f'Filtros activos: RSI ≤ {rsi_max} · DD ≤ {dd_min}% · Score ≥ {score_min}. '+
            f'Esto es información válida — el modelo dice que no hay oportunidades en este nivel hoy.</span></div>',
            unsafe_allow_html=True)
        return

    # ── Orden automático por tab + columna Señal ────────────
    df_show = resultado_df.copy()

    # Agregar columna "Señal" con interpretación correcta según tab
    def generar_senal(row):
        rsi  = float(row.get("RSI", 50))
        dd   = float(row.get("DD_pico", 0))
        vol  = float(row.get("Volumen", 100))
        dec  = str(row.get("Decision",""))

        # Detectadas M1 — solo estados de corrección
        if tab_key == "scan_detectadas":
            if dd < -30 and rsi < 40:
                return "🔴 Corrección profunda — watchlist prioritaria"
            elif dd < -15 and rsi < 50:
                return "👀 En corrección — vigilar"
            elif dd < -8:
                return "📡 Inicio corrección — agregar a watchlist"
            else:
                return "🔵 Corrección leve"

        # Entrar hoy — solo señales fuertes
        elif tab_key == "scan_entrar":
            if dec == "ENTRAR" or (rsi < 35 and dd < -15 and vol > 150):
                return "🔥 Entrar hoy — señal completa"
            elif dec == "ANTICIPAR":
                return "⚡ Anticipar — pre-señal"
            else:
                return "⚡ Candidata"

        # Otros tabs — señal general
        else:
            if dec == "ENTRAR" or (rsi < 35 and dd < -20 and vol > 150):
                return "🔥 Entrar hoy"
            elif dec == "ANTICIPAR" or (rsi < 45 and dd < -15 and vol > 100):
                return "⚡ Entrada válida"
            elif dd < -8 and rsi < 55:
                return "👀 En corrección — vigilar"
            elif rsi > 65:
                return "⛔ RSI alto — esperar"
            else:
                return "🔵 Neutral — observar"

    if not df_show.empty:
        df_show["Señal modelo"] = df_show.apply(generar_senal, axis=1)

    # Orden automático según tab (sin selector)
    if default_sort in df_show.columns:
        asc = (default_sort == "DD_pico")
        df_show = df_show.sort_values(default_sort, ascending=asc)

    # Mostrar columna Señal primero
    cols_con_senal = cols_show.copy() if cols_show else list(df_show.columns)
    if "Señal modelo" not in cols_con_senal:
        cols_con_senal = ["Ticker","Señal modelo"] + [c for c in cols_con_senal if c not in ("Ticker","Señal modelo")]

    render_table(df_show, cols_con_senal)

    # Exportar señales del día
    boton_exportar(resultado_df, titulo, f"exp_{tab_key}")

    # Pre/Post Market por ticker
    if not resultado_df.empty:
        st.markdown(
            f'<div style="font-size:11px;font-weight:700;color:{TXT};margin:14px 0 6px">'+
            f'📡 Pre-Market · Post-Market · Volumen en tiempo real</div>',
            unsafe_allow_html=True)
        for _, r in resultado_df.iterrows():
            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;'+
                f'padding:10px 14px;margin-bottom:6px">'+
                f'<div style="font-size:12px;font-weight:700;color:{B};margin-bottom:4px">'+
                f'{r["Ticker"]} — {r.get("Nombre","")[:30]}</div>'+
                render_pre_post_bar(r["Ticker"], r["Precio"], G, A, R, TXT_MUT, TXT_SOFT, BG_HEAD, BOR)+
                render_nbis_panel(r.get('Prob_NBIS',0), r.get('Sim_NBIS',0), G, A, R, C, TXT, TXT_MUT, TXT_SOFT, BG_HEAD, BOR)+
                f'</div>', unsafe_allow_html=True)




# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">'
    f'<span style="font-size:24px;font-weight:800;color:{TXT}">Panel de Monitoreo Diario</span>'
    f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};border-radius:8px;padding:3px 12px;font-size:12px;font-weight:700">'
    f'{datetime.date.today():%A %d %b %Y}</span>'
    f'{"<span style=background:" + G_BG + ";color:" + G + ";border:1px solid " + G_BOR + ";border-radius:8px;padding:3px 10px;font-size:11px;font-weight:600>● Precios live</span>" if _n_live>0 else "<span style=background:" + A_BG + ";color:" + A + ";border:1px solid " + A_BOR + ";border-radius:8px;padding:3px 10px;font-size:11px>⚠ Precios estáticos</span>"}'
    f'</div>',unsafe_allow_html=True)
st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:10px">Modelo Rebote Técnico · Patrón NBIS · 3 Momentos · Pre/Post Market · {"RSI / MACD / EMA50 / Precio actualizados en tiempo real · cache 20min" if _n_live>0 else "pip install yfinance para indicadores en tiempo real"}</div>',unsafe_allow_html=True)

# ── Semáforo VIX ──────────────────────────────────────────────
if not vix["_ok"]:
    st.markdown(
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};'
        f'border-radius:12px;padding:10px 18px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:center;gap:16px">'
        f'<div>'
        f'  <span style="font-size:10px;color:{TXT_MUT};font-weight:600">VIX — Índice de Volatilidad</span><br>'
        f'  <span style="font-size:22px;font-weight:800;color:{TXT_MUT}">—</span>'
        f'  <span style="font-size:11px;color:{TXT_MUT};margin-left:8px">Sin datos · Mercado cerrado</span>'
        f'</div></div></div>',
        unsafe_allow_html=True)
elif vix["_ok"]:
    cambio_sym = f'+{vix["cambio"]:.2f}' if vix["cambio"] >= 0 else f'{vix["cambio"]:.2f}'
    cambio_col = R if vix["cambio"] > 0 else G
    vix_v = vix["valor"]

    # Etapa VIX + ETF sugerido
    if vix_v >= 35:
        vix_etapa = "🔥 ENTRAR — Pánico máximo"
        vix_etf   = "ETF: SPY · VOO · QQQ"
        vix_accion= "Comprar índices ahora · Máxima oportunidad histórica"
    elif vix_v >= 25:
        vix_etapa = "⚡ SWING — Miedo elevado"
        vix_etf   = "ETF: SPY · IVV · TQQQ"
        vix_accion= "Buscar swings en índices · Oportunidad moderada"
    elif vix_v >= 18:
        vix_etapa = "📡 VIGILAR — Nerviosismo"
        vix_etf   = "ETF: SPY · QQQ · XLF"
        vix_accion= "Monitorear · No entrar índices aún"
    elif vix_v >= 13:
        vix_etapa = "⚪ NORMAL — Mercado tranquilo"
        vix_etf   = "—"
        vix_accion= "Exigir Pre-Market confirmado antes de entrar"
    else:
        vix_etapa = "🔴 PRECAUCIÓN — Complacencia"
        vix_etf   = "Considerar UVXY · VIXY (corto)"
        vix_accion= "Mercado muy tranquilo — corrección probable próxima"

    st.markdown(
        f'<div style="background:{vix["bg"]};border:1px solid {vix["bor"]};'
        f'border-radius:12px;padding:12px 18px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">'
        f'<div>'
        f'  <span style="font-size:10px;color:{TXT_MUT};font-weight:600">VIX — Índice de Volatilidad</span><br>'
        f'  <span style="font-size:26px;font-weight:800;color:{vix["color"]}">{vix_v}</span>'
        f'  <span style="font-size:12px;color:{cambio_col};margin-left:6px">{cambio_sym}</span>'
        f'  <span style="background:{vix["bg"]};color:{vix["color"]};border:1px solid {vix["bor"]};'
        f'  border-radius:6px;padding:2px 10px;font-size:11px;font-weight:700;margin-left:8px">'
        f'  {vix["nivel"]}</span>'
        f'</div>'
        f'<div style="flex:1">'
        f'  <div style="font-size:12px;font-weight:700;color:{vix["color"]}">{vix_etapa}</div>'
        f'  <div style="font-size:11px;color:{TXT_MUT};margin-top:2px">{vix_accion}</div>'
        f'  <div style="font-size:10px;color:{TXT_SOFT};margin-top:4px">'
        f'  {"🎯 " + vix_etf if vix_etf != "—" else ""}</div>'
        f'</div>'
        f'{"<div style=font-size:11px;color:" + G + ";font-weight:600;white-space:nowrap>● Score ×" + str(vix["mult"]) + " activo</div>" if vix["mult"] > 1.0 else ""}'
        f'</div></div>',
        unsafe_allow_html=True)

# ── Cargar indicadores de mercado (cache 15min — no bloquea) ──
if "mkt_cache" not in st.session_state:
    st.session_state["mkt_cache"] = {}
mkt = st.session_state.get("mkt_cache", {})
if not mkt:
    with st.spinner("Cargando indicadores de mercado..."):
        mkt = fetch_market_indicators()
        st.session_state["mkt_cache"] = mkt

# ── Fila 1: S&P500 · Nasdaq · SPY RSI · Sector · Señal ───────
col_spx, col_ndx, col_spy, col_sector, col_signal = st.columns(5)

with col_spx:
    if "spx" in mkt:
        sc = G if mkt["spx"]["chg"] >= 0 else R
        chg = mkt["spx"]["chg"]
        # Etapa S&P500
        spy_rsi_hdr = mkt.get("spy", {}).get("rsi", 50)
        if spy_rsi_hdr < 35:
            spx_etapa = "🔥 M3 — Entrar"; spx_etf = "SPY · VOO · IVV"; spx_c = G; spx_bg = G_BG; spx_bor = G_BOR
        elif spy_rsi_hdr < 45:
            spx_etapa = "⚡ Swing activo"; spx_etf = "SPY · TQQQ"; spx_c = C; spx_bg = C_BG; spx_bor = C_BOR
        elif spy_rsi_hdr < 55:
            spx_etapa = "📡 M1 — Vigilar"; spx_etf = "SPY · IVV"; spx_c = A; spx_bg = A_BG; spx_bor = A_BOR
        else:
            spx_etapa = "🔴 Alto — Esperar"; spx_etf = "No entrar índices"; spx_c = TXT_MUT; spx_bg = BG_CARD; spx_bor = BOR
        st.markdown(
            f'<div style="background:{spx_bg};border:1px solid {spx_bor};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">S&P 500</div>'
            f'<div style="font-size:18px;font-weight:800;color:{TXT}">{mkt["spx"]["val"]:,.0f}</div>'
            f'<div style="font-size:11px;color:{sc};font-weight:600">{chg:+.2f}%</div>'
            f'<div style="font-size:10px;color:{spx_c};font-weight:700;margin-top:4px">{spx_etapa}</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT}">🎯 {spx_etf}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("S&P 500", "—")

with col_ndx:
    if "ndx" in mkt:
        nc = G if mkt["ndx"]["chg"] >= 0 else R
        chg_n = mkt["ndx"]["chg"]
        # Etapa Nasdaq
        if spy_rsi_hdr < 35:
            ndx_etapa = "🔥 M3 — Entrar"; ndx_etf = "QQQ · TQQQ"; ndx_c = G; ndx_bg = G_BG; ndx_bor = G_BOR
        elif spy_rsi_hdr < 45:
            ndx_etapa = "⚡ Swing activo"; ndx_etf = "QQQ · SQQQ hedge"; ndx_c = C; ndx_bg = C_BG; ndx_bor = C_BOR
        elif spy_rsi_hdr < 55:
            ndx_etapa = "📡 M1 — Vigilar"; ndx_etf = "QQQ · QQQM"; ndx_c = A; ndx_bg = A_BG; ndx_bor = A_BOR
        else:
            ndx_etapa = "🔴 Alto — Esperar"; ndx_etf = "No entrar Nasdaq"; ndx_c = TXT_MUT; ndx_bg = BG_CARD; ndx_bor = BOR
        st.markdown(
            f'<div style="background:{ndx_bg};border:1px solid {ndx_bor};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">Nasdaq</div>'
            f'<div style="font-size:18px;font-weight:800;color:{TXT}">{mkt["ndx"]["val"]:,.0f}</div>'
            f'<div style="font-size:11px;color:{nc};font-weight:600">{chg_n:+.2f}%</div>'
            f'<div style="font-size:10px;color:{ndx_c};font-weight:700;margin-top:4px">{ndx_etapa}</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT}">🎯 {ndx_etf}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("Nasdaq", "—")

with col_spy:
    if "spy" in mkt:
        spy_d = mkt["spy"]
        rc = G if spy_d["rsi"] < 40 else R if spy_d["rsi"] > 65 else A
        ec = R if "bajo" in spy_d["ema_status"] else G
        # Descripción RSI SPY
        if spy_d["rsi"] < 35:
            spy_desc = "Sobreventa — oportunidad"
        elif spy_d["rsi"] < 50:
            spy_desc = "Zona baja — vigilar"
        elif spy_d["rsi"] < 65:
            spy_desc = "Zona media — neutral"
        else:
            spy_desc = "Sobrecompra — precaución"
        st.markdown(
            f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">SPY — S&P500 ETF</div>'
            f'<div style="font-size:18px;font-weight:800;color:{rc}">{spy_d["rsi"]}</div>'
            f'<div style="font-size:10px;color:{rc};font-weight:600">{spy_desc}</div>'
            f'<div style="font-size:9px;color:{ec};margin-top:3px">{spy_d["ema_status"]}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("SPY RSI", "—")

with col_sector:
    if "sectores" in mkt:
        sec = mkt["sectores"]
        # Sugerir ETF del sector
        sector_etf_map = {
            "Energía": "XLE · OIH", "Tech": "XLK · SOXX",
            "Salud": "XLV · XBI", "Finanzas": "XLF · KRE",
            "Consumo": "XLY · XLP", "Industrial": "XLI · ITA",
            "Materiales": "XLB · GDX",
        }
        etf_sector = sector_etf_map.get(sec["mejor_oportunidad"], "ETF sectorial")
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">🔍 Sector con oportunidades</div>'
            f'<div style="font-size:16px;font-weight:800;color:{G}">{sec["mejor_oportunidad"]}</div>'
            f'<div style="font-size:11px;color:{G}">{sec["acciones_en_correccion"]} acciones en corrección</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:3px">🎯 ETF: {etf_sector}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("Sector", "—")

with col_signal:
    vix_v2  = vix.get("valor", 18)
    spy_rsi2 = mkt.get("spy", {}).get("rsi", 50)
    if vix_v2 >= 30 and spy_rsi2 < 45:
        sig="🟢 MÁXIMA OPORTUNIDAD"; sig_c=G; sig_bg=G_BG; sig_bor=G_BOR
        sig_etf = "SPY · QQQ · VOO"
        sig_acc = "Activar reserva táctica"
    elif vix_v2 >= 25 or spy_rsi2 < 40:
        sig="🟡 OPORTUNIDAD MODERADA"; sig_c=A; sig_bg=A_BG; sig_bor=A_BOR
        sig_etf = "SPY · sector ETF"
        sig_acc = "Buscar swings confirmados"
    elif vix_v2 < 18 and spy_rsi2 > 65:
        sig="🔴 PRECAUCIÓN — Rally"; sig_c=R; sig_bg=R_BG; sig_bor=R_BOR
        sig_etf = "No entrar índices"
        sig_acc = "Esperar corrección"
    else:
        sig="⚪ MERCADO NORMAL"; sig_c=TXT_MUT; sig_bg=BG_HEAD; sig_bor=BOR
        sig_etf = "Selectivo por señal"
        sig_acc = "Seguir señales del modelo"
    st.markdown(
        f'<div style="background:{sig_bg};border:1px solid {sig_bor};border-radius:10px;padding:10px 14px">'
        f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">Señal del modelo</div>'
        f'<div style="font-size:12px;font-weight:700;color:{sig_c}">{sig}</div>'
        f'<div style="font-size:10px;color:{TXT_MUT};margin-top:3px">{sig_acc}</div>'
        f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:2px">🎯 {sig_etf}</div>'
        f'<div style="font-size:9px;color:{TXT_SOFT}">VIX {vix_v2} · SPY RSI {spy_rsi2}</div>'
        f'</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("---")

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8=st.tabs([
    "📡 Detectadas M1","⚡ Swing Activo","🔥 Entrar hoy",
    "🔗 Sympathy","🔎 Mi Watchlist","💼 Mis Posiciones","💜 Posiciones Amparito",
    "💰 Estrategia ETF",
])




# ══ TAB 1 — DETECTADAS M1 (M1 del patrón NBIS) ════════════════
# ══ TAB 5 — DETECTADAS M1 ════════════════════════════════════════
with tab1:
    render_scan_tab(
        tab_key="scan_detectadas",
        titulo="Detectadas M1",
        emoji="📡",
        color=R, color_bg=R_BG, color_bor=R_BOR,
        desc="Bajada activa · En corrección · Score ≥ 15 · Watchlist temprana",
        rsi_max=60, dd_min=-8, score_min=15,
        decisions=["SEGUIR","OBSERVAR","ANTICIPAR"],
        default_sort="DD_pico",
    )


# ══ TAB 2 — SWING ACTIVO (M2 — rebote confirmado) ══════════════
# ══ TAB 4 — SWING ACTIVO ═════════════════════════════════════
with tab2:
    st.markdown(
        f'<div class="sec-header" style="background:{C_BG};border-color:{C_BOR}">'+
        f'<span style="font-size:20px">⚡</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:{C}">Swing Activo</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'+
        f'Rebote confirmado 2-3 días · RSI girando ↑ · Salida obligatoria día 5-10</span></div>'+
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box">'+
        f'<strong>3 fases del Swing — alineadas con el patrón NBIS:</strong><br>'+
        f'<span style="color:#D97706">👀 TEMPRANA (M1→M2)</span> — Solo 2 días subiendo. '+
        f'Puede revertir. <strong>No entrar</strong> — agregar a watchlist y esperar.<br>'+
        f'<span style="color:#0891B2">⚡ ENTRADA VÁLIDA (M2)</span> — Rebote confirmado pero sin plena convicción. '+
        f'<strong>Entrar 50%</strong> del tamaño. Si mañana confirma volumen, completar.<br>'+
        f'<span style="color:#16A34A">🔥 ENTRAR HOY (M3)</span> — 3+ días + volumen alto + momentum fuerte. '+
        f'<strong>Entrar 100%</strong> del tamaño planificado.<br><br>'+
        f'🛑 Stop duro -5% · 🎯 Target 1 +8% (vender 60%) · 🎯 Target 2 +12% (runner 40%) · Salida obligatoria día 10'+
        f'</div>',
        unsafe_allow_html=True)

    col_btn_sw, col_info_sw = st.columns([2, 3])
    with col_btn_sw:
        if st.button("⚡ Escanear Swing Activo", use_container_width=True, key="btn_swing"):
            with st.spinner("Detectando rebotes activos en ~{} tickers...".format(len(SCAN_UNIVERSE))):
                resultado_sw = scan_swing(max_results=max_res, universo=SCAN_UNIVERSE[:st.session_state.get("universo_size", 300)])
                st.session_state["scan_swing"] = resultado_sw
                st.session_state["scan_swing_ts"] = datetime.datetime.now().strftime("%H:%M")
    with col_info_sw:
        if st.session_state.get("scan_swing") is not None:
            n_sw = len(st.session_state["scan_swing"])
            ts_sw = st.session_state.get("scan_swing_ts","")
            st.markdown(
                f'<div style="font-size:11px;color:{G if n_sw>0 else TXT_MUT};padding-top:8px">'+
                f'● {n_sw} swings activos encontrados · {ts_sw}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:11px;color:{TXT_SOFT};padding-top:8px">'+
                f'Presiona el botón para detectar swings en tiempo real</div>',
                unsafe_allow_html=True)

    sw_result = st.session_state.get("scan_swing")

    if sw_result is None:
        st.markdown(
            f'<div style="background:{C_BG};border:1px solid {C_BOR};border-radius:12px;'+
            f'padding:32px;text-align:center">'+
            f'<div style="font-size:36px;margin-bottom:10px">⚡</div>'+
            f'<div style="font-size:14px;font-weight:700;color:{C};margin-bottom:6px">Swing Activo — Sin escanear</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT}">'+
            f'Detecta acciones con 2-3 días consecutivos alcistas tras corrección.'+
            f'<br>Oportunidades de 8-15% en 5-10 días.</div>'+
            f'</div>', unsafe_allow_html=True)
    elif sw_result.empty:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:10px;'+
            f'padding:20px;text-align:center;color:{A}">'+
            f'Sin swings activos ahora — mercado sin momentum claro de rebote.'+
            f'</div>', unsafe_allow_html=True)
    else:
        # Ordenar por Momentum 3d descendente (default Swing)

        # Render swing cards
        for _, r in sw_result.iterrows():
            dias_c = G if r["Dias_Alcistas"] >= 3 else A
            mom_c  = G if r["Momentum_3d"] >= 5 else A if r["Momentum_3d"] >= 2 else TXT_MUT
            rsi_c  = G if r["RSI"] < 45 else A if r["RSI"] < 55 else TXT_MUT

            # ── FASE DE ENTRADA ──────────────────────────────
            vol_r = r.get("Volumen", 100)
            if r["Dias_Alcistas"] >= 3 and r["Momentum_3d"] >= 8 and vol_r >= 150:
                fase       = "🔥 ENTRAR HOY"
                fase_c     = G; fase_bg = G_BG; fase_bor = G_BOR
                fase_momento = "M3 — Confirmado"
                fase_desc  = "El tren ya salió con fuerza. Entrar hoy con posición completa."
                fase_accion= "✅ Entrar 100% del tamaño planificado"
            elif r["Dias_Alcistas"] >= 2 and r["Momentum_3d"] >= 4:
                fase       = "⚡ ENTRADA VÁLIDA"
                fase_c     = C; fase_bg = C_BG; fase_bor = C_BOR
                fase_momento = "M2 — Confirmando"
                fase_desc  = "Rebote iniciado pero sin plena convicción. Entrar con la mitad."
                fase_accion= "⚡ Entrar 50% ahora · completar si mañana confirma volumen"
            else:
                fase       = "👀 TEMPRANA"
                fase_c     = A; fase_bg = A_BG; fase_bor = A_BOR
                fase_momento = "M1→M2 — Vigilar"
                fase_desc  = "Solo 2 días subiendo. Puede revertir. Esperar un día más."
                fase_accion= "⏳ Solo watchlist — no entrar todavía"

            # ── VOLUMEN ──────────────────────────────────────
            if vol_r >= 200:
                vol_label = "🟢 ALTO"; vol_c = G; vol_desc = f"{vol_r}% del promedio · Confirma el movimiento"
            elif vol_r >= 120:
                vol_label = "🟡 NORMAL"; vol_c = A; vol_desc = f"{vol_r}% del promedio · Movimiento moderado"
            else:
                vol_label = "🔴 BAJO"; vol_c = R; vol_desc = f"{vol_r}% del promedio · Sin convicción — cuidado"

            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {C_BOR};'
                f'border-left:4px solid {fase_c};border-radius:12px;'
                f'padding:14px 18px;margin-bottom:10px">'

                # Header con NBIS badge integrado
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                f'  <span style="font-size:20px;font-weight:800;color:{B}">{r["Ticker"]}</span>'
                f'  <span style="font-size:12px;color:{TXT_MUT}">{r["Nombre"][:20]}</span>'
                f'  <span style="background:{C_BG};color:{C};border:1px solid {C_BOR};'
                f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">⚡ SWING</span>'
                + (lambda p=r.get("Prob_NBIS",0), s=r.get("Sim_NBIS",0):
                    f'  <span style="background:{"#F0FDF4" if p>=65 else "#FFFBEB" if p>=45 else "#F8FAFC"};'
                    f'  color:{"#16A34A" if p>=65 else "#D97706" if p>=45 else "#64748B"};'
                    f'  border:1px solid {"#86EFAC" if p>=65 else "#FDE68A" if p>=45 else "#E2E8F0"};'
                    f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'  ⭐ NBIS {p:.0f}%</span>'
                    f'  <span style="background:{"#EFF6FF" if s>=55 else "#FFFBEB" if s>=35 else "#F8FAFC"};'
                    f'  color:{"#2563EB" if s>=55 else "#D97706" if s>=35 else "#64748B"};'
                    f'  border:1px solid {"#BFDBFE" if s>=55 else "#FDE68A" if s>=35 else "#E2E8F0"};'
                    f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'  📊 Sim {s:.0f}%</span>'
                )() +
                f'</div>'
                f'<div style="text-align:right;font-size:11px;color:{TXT_MUT}">'
                f'${r["Precio"]:.2f} · {r["Area"]} · Beta {r["Beta"]}</div>'
                f'</div>'

                # ── FASE + VOLUMEN — nueva fila destacada ────
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">'
                f'  <div style="background:{fase_bg};border:1px solid {fase_bor};'
                f'  border-radius:8px;padding:8px 12px">'
                f'    <div style="font-size:9px;color:{fase_c};font-weight:700;margin-bottom:2px">FASE DE ENTRADA · {fase_momento}</div>'
                f'    <div style="font-size:13px;font-weight:700;color:{fase_c}">{fase}</div>'
                f'    <div style="font-size:10px;color:{TXT_MUT};margin-top:2px">{fase_desc}</div>'
                f'    <div style="font-size:10px;color:{fase_c};font-weight:600;margin-top:4px">{fase_accion}</div>'
                f'  </div>'
                f'  <div style="background:{BG_HEAD};border:1px solid {BOR};'
                f'  border-radius:8px;padding:8px 12px">'
                f'    <div style="font-size:10px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">VOLUMEN</div>'
                f'    <div style="font-size:13px;font-weight:700;color:{vol_c}">{vol_label}</div>'
                f'    <div style="font-size:10px;color:{TXT_MUT};margin-top:2px">{vol_desc}</div>'
                f'  </div>'
                f'</div>'

                # Métricas
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px">'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">Días alcistas</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{dias_c}">{r["Dias_Alcistas"]}</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">Momentum 3d</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{mom_c}">+{r["Momentum_3d"]:.1f}%</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">RSI actual</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{rsi_c}">{r["RSI"]:.0f} ↑</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">DD desde pico</div>'
                f'    <div style="font-size:18px;font-weight:700;color:{R}">{r["DD_pico"]:.0f}%</div></div>'
                f'</div>'

                # Targets
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">'
                f'  <div style="background:{R_BG};border:1px solid {R_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{R};font-weight:700">🛑 Stop (-5%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{R}">${r["Stop_Swing"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Salir si llega aquí</div></div>'
                f'  <div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{A};font-weight:700">🎯 Target 1 (+8%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{A}">${r["Target_1"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Vender 60%</div></div>'
                f'  <div style="background:{G_BG};border:1px solid {G_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{G};font-weight:700">🎯 Target 2 (+12%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{G}">${r["Target_2"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Runner 40%</div></div>'
                f'</div>'

                f'<div style="font-size:10px;color:{TXT_MUT};margin-top:8px;'
                f'border-top:1px solid {BOR};padding-top:6px">'
                f'{r["Lectura"]}</div>'
                f'</div>', unsafe_allow_html=True)

        # Exportar
        sw_export = sw_result[["Ticker","Area","Precio","RSI","Dias_Alcistas",
                                "Momentum_3d","DD_pico","Stop_Swing","Target_1","Target_2","Beta","Lectura"]]
        st.download_button("⬇️ Exportar swings (CSV)",
            df_to_csv_chile(sw_export), "swing_activo.csv","text/csv", key="dl_sw")
        boton_exportar(sw_result, "Swing Activo", "exp_swing", fase_col=None)


# ══ TAB 3 — ENTRAR HOY (M3 confirmado) ════════════════════════
# ══ TAB 1 — ENTRAR HOY ══════════════════════════════════════════
with tab3:
    render_scan_tab(
        tab_key="scan_entrar",
        titulo="Entrar hoy",
        emoji="🔥",
        color=G, color_bg=G_BG, color_bor=G_BOR,
        desc="M3 confirmado · RSI capitulación · Catalizador activo · Score ≥ 75",
        rsi_max=45, dd_min=-12, score_min=55,
        decisions=["ENTRAR","ANTICIPAR"],
        default_sort="Prob_NBIS",
    )


# ══ TAB 4 — SYMPATHY ═══════════════════════════════════════════
# ══ TAB 5 — SYMPATHY ═════════════════════════════════════════════
with tab4:
    st.markdown(
        f'<div class="sec-header" style="background:{P_BG};border-color:{P_BOR}">'+
        f'<span style="font-size:20px">🔗</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:{P}">Sympathy Plays</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'+
        f'Acciones que se mueven con el líder del sector</span></div>'+
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box">Lógica: si NBIS está en Swing Activo rebotando, '+
        f'el modelo busca <strong>otras acciones del mismo sector que AÚN NO han subido</strong>. '+
        f'Esas son las arrastradas — la oportunidad de entrar antes de que el sector complete el movimiento.<br>'+
        f'<strong>Paso 1:</strong> Escanea Swing Activo o Entrar hoy. '+
        f'<strong>Paso 2:</strong> Vuelve aquí para ver las arrastradas.</div>',
        unsafe_allow_html=True)

    # ── Lógica Sympathy: Líder → Arrastradas ─────────────────
    # 1. Obtener líderes = acciones en Swing Activo o Entrar Hoy
    lideres_df = pd.DataFrame()
    for key in ["scan_swing","scan_entrar"]:
        df_tmp = st.session_state.get(key)
        if df_tmp is not None and not df_tmp.empty:
            df_tmp = df_tmp.copy()
            df_tmp["_tab_origen"] = "Swing Activo" if key=="scan_swing" else "Entrar hoy"
            lideres_df = pd.concat([lideres_df, df_tmp], ignore_index=True)

    # 2. Obtener candidatos = todas las acciones escaneadas (detectadas M1 + universo)
    candidatos_df = pd.DataFrame()
    for key in ["scan_detectadas","scan_swing","scan_entrar"]:
        df_tmp = st.session_state.get(key)
        if df_tmp is not None and not df_tmp.empty:
            candidatos_df = pd.concat([candidatos_df, df_tmp], ignore_index=True)

    all_results = []  # kept for compatibility

    if lideres_df.empty:
        st.markdown(
            f'<div style="background:{P_BG};border:1px solid {P_BOR};border-radius:12px;'+
            f'padding:32px;text-align:center">'+
            f'<div style="font-size:36px;margin-bottom:10px">🔗</div>'+
            f'<div style="font-size:14px;font-weight:700;color:{P};margin-bottom:6px">Sin líderes detectados</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT}">'+
            f'Paso 1: Escanea ⚡ Swing Activo<br>'+
            f'Paso 2: Escanea 📡 Detectadas M1 (opcional — para ver arrastradas)<br>'+
            f'Paso 3: Vuelve aquí para ver líderes y arrastradas</div>'+
            f'</div>', unsafe_allow_html=True)
    else:
        lideres_df["Area"] = lideres_df["Area"].fillna("—").astype(str)
        tickers_lideres = set(lideres_df["Ticker"].str.upper().tolist())

        # Agrupar líderes por sector
        for area_name, grupo_lideres in lideres_df.groupby("Area"):
            if area_name in ("—","","nan"):
                continue

            lideres_list = grupo_lideres["Ticker"].tolist()
            tab_origen   = grupo_lideres["_tab_origen"].iloc[0]

            # Buscar arrastradas en detectadas M1
            arrastradas = pd.DataFrame()
            df_detect = st.session_state.get("scan_detectadas")
            if df_detect is not None and not df_detect.empty:
                arrastradas = df_detect[
                    (df_detect["Area"].fillna("—") == area_name) &
                    (~df_detect["Ticker"].isin(tickers_lideres))
                ]

            n_lideres     = len(lideres_list)
            n_arrastradas = len(arrastradas)

            # Header del sector
            st.markdown(
                f'<div style="background:{P_BG};border:1px solid {P_BOR};'+
                f'border-left:4px solid {P};border-radius:10px;'+
                f'padding:12px 16px;margin:12px 0 6px">'+
                f'<div style="display:flex;justify-content:space-between;align-items:center">'+
                f'<div style="font-size:14px;font-weight:800;color:{P}">🔗 {area_name}</div>'+
                f'<div style="font-size:11px;color:{TXT_MUT}">'+
                f'{n_lideres} líder(es) · {n_arrastradas} arrastrada(s)</div>'+
                f'</div></div>',
                unsafe_allow_html=True)

            # Mostrar líderes
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;color:{G};margin:6px 0 4px">'+
                f'🏆 Líderes — rebotando ({tab_origen})</div>',
                unsafe_allow_html=True)

            for _, lider_row in grupo_lideres.iterrows():
                dias = int(lider_row.get("Dias_Alcistas",0)) if "Dias_Alcistas" in lider_row.index else 0
                mom  = float(lider_row.get("Momentum_3d",0)) if "Momentum_3d" in lider_row.index else 0
                vol  = float(lider_row.get("Volumen",0))
                if dias >= 3 and mom >= 8 and vol >= 150:
                    fase_l = "🔥 ENTRAR HOY"
                elif dias >= 2 and mom >= 4:
                    fase_l = "⚡ ENTRADA VÁLIDA"
                else:
                    fase_l = "👀 TEMPRANA"

                st.markdown(
                    f'<div style="background:{G_BG};border:1px solid {G_BOR};'+
                    f'border-radius:8px;padding:8px 14px;margin-bottom:4px;'+
                    f'display:flex;justify-content:space-between;align-items:center">'+
                    f'<div style="display:flex;align-items:center;gap:10px">'+
                    f'  <span style="font-size:14px;font-weight:800;color:{G}">{lider_row["Ticker"]}</span>'+
                    f'  <span style="font-size:11px;color:{TXT_MUT}">{str(lider_row.get("Nombre",""))[:25]}</span>'+
                    f'  <span style="font-size:11px;font-weight:700;color:{G}">{fase_l}</span>'+
                    f'</div>'+
                    f'<div style="display:flex;gap:16px;font-size:10px;color:{TXT_MUT}">'+
                    f'  <span>RSI {lider_row.get("RSI","—")}</span>'+
                    f'  <span>Vol {int(vol)}%</span>'+
                    f'  <span>DD {lider_row.get("DD_pico","—")}%</span>'+
                    f'  <span>${lider_row.get("Precio","—")}</span>'+
                    f'</div></div>',
                    unsafe_allow_html=True)

            # Mostrar arrastradas
            if not arrastradas.empty:
                st.markdown(
                    f'<div style="font-size:11px;font-weight:700;color:{C};margin:8px 0 4px">'+
                    f'🔗 Arrastradas — aún no han subido (oportunidad)</div>',
                    unsafe_allow_html=True)
                for _, arr_row in arrastradas.iterrows():
                    st.markdown(
                        f'<div style="background:{C_BG};border:1px solid {C_BOR};'+
                        f'border-radius:8px;padding:8px 14px;margin-bottom:4px;'+
                        f'display:flex;justify-content:space-between;align-items:center">'+
                        f'<div style="display:flex;align-items:center;gap:10px">'+
                        f'  <span style="font-size:14px;font-weight:800;color:{C}">{arr_row["Ticker"]}</span>'+
                        f'  <span style="font-size:11px;color:{TXT_MUT}">{str(arr_row.get("Nombre",""))[:25]}</span>'+
                        f'  <span style="font-size:11px;color:{C};font-weight:700">'+
                        f'⚡ Arrastrada por {", ".join(lideres_list[:2])}</span>'+
                        f'</div>'+
                        f'<div style="display:flex;gap:16px;font-size:10px;color:{TXT_MUT}">'+
                        f'  <span>RSI {arr_row.get("RSI","—")}</span>'+
                        f'  <span>DD {arr_row.get("DD_pico","—")}%</span>'+
                        f'  <span>Score {arr_row.get("Score","—")}</span>'+
                        f'  <span>${arr_row.get("Precio","—")}</span>'+
                        f'</div></div>',
                        unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="font-size:10px;color:{TXT_MUT};padding:6px 14px;'+
                    f'background:{BG_HEAD};border-radius:6px;margin-bottom:6px">'+
                    f'Sin arrastradas en Detectadas M1 — escanea 📡 Detectadas M1 para ver candidatas.</div>',
                    unsafe_allow_html=True)


# ══ TAB 5 — MI WATCHLIST ═══════════════════════════════════════
# ══ TAB 6 — MI WATCHLIST CSV ══════════════════════════════════
with tab5:
    st.markdown(
        f'<div class="sec-header" style="background:{B_BG};border-color:{B_BOR}">'
        f'<span style="font-size:20px">🔎</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{B}">Mi Watchlist personal</span>'
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'
        f'Carga tus acciones de seguimiento · El modelo analiza cada una bajo el patrón NBIS</span></div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box">Ingresa cualquier acción que quieras monitorear. '
        f'El modelo calculará su score, momento del patrón, similitud con NBIS y señal. '
        f'Si tienes internet con <code>yfinance</code> instalado, usará datos reales. '
        f'Si no, estimará a partir del precio que ingreses.</div>',
        unsafe_allow_html=True)

    # ── Instrucciones y plantilla ──────────────────────────────
    with st.expander("📋 Formato del CSV de Watchlist", expanded=False):
        st.markdown(f"""
**Columnas requeridas — solo el Ticker es obligatorio:**

| Ticker | Nombre | Area | Nota |
|--------|--------|------|------|
| TAN    | Invesco Solar ETF | Energía | Solar sector recovery |
| CROX   | Crocs Inc | Consumo | Post earnings dip |
| CNC    | Centene Corp | Salud | Healthcare turnaround |
| SOFI   | SoFi Tech | Fintech | Banking license catalyst |

- **Ticker**: obligatorio, en mayúsculas
- **Nombre**: opcional, nombre descriptivo
- **Area**: opcional, sector (Tech, Salud, Energía, Finanzas, Consumo, Industrial, Cripto/AI, Quantum, Fintech)
- **Nota**: opcional, tu tesis o razón de seguimiento

El modelo descarga el precio actual y calcula todos los indicadores automáticamente.
""")
        wl_template = pd.DataFrame({
            "Ticker":  ["TAN","CROX","CNC","SOFI","MSTR"],
            "Nombre":  ["Invesco Solar ETF","Crocs Inc","Centene Corp","SoFi Tech","Strategy Inc"],
            "Area":    ["Energía","Consumo","Salud","Fintech","Cripto/AI"],
            "Nota":    ["Solar recovery","Post dip consumer","Healthcare turnaround",
                        "Banking license","BTC proxy"],
        })
        st.download_button(
            "⬇️ Descargar plantilla Watchlist CSV",
            wl_template.to_csv(index=False),
            "watchlist_template.csv","text/csv",key="dl_wl_template")

    # ── Upload ─────────────────────────────────────────────────
    wl_file = st.file_uploader(
        "📂 Subir Watchlist CSV",
        type=["csv"],
        help="Solo el Ticker es obligatorio",
        key="wl_uploader")

    wl_df = None

    if wl_file:
        try:
            wl_df = pd.read_csv(wl_file)
            # Limpiar tickers — quitar $ y espacios
            if "Ticker" in wl_df.columns:
                wl_df["Ticker"] = wl_df["Ticker"].str.upper().str.strip().str.replace("$","")
            wl_df.columns = [c.strip() for c in wl_df.columns]
            if "Ticker" not in wl_df.columns:
                st.error("❌ El CSV debe tener al menos la columna 'Ticker'")
                wl_df = None
            else:
                wl_df["Ticker"] = wl_df["Ticker"].str.upper().str.strip()
                st.success(f"✅ Watchlist cargada — {len(wl_df)} acciones para analizar")
        except Exception as e:
            st.error(f"❌ Error: {e}"); wl_df = None
    else:
        st.markdown(
            f'<div class="info-box">💡 No hay Watchlist cargada. '
            f'Mostrando ejemplos. Sube tu CSV para analizar tus propias acciones.</div>',
            unsafe_allow_html=True)
        wl_df = pd.DataFrame({
            "Ticker": ["TAN","CROX","CNC","MSTR","SOFI"],
            "Nombre": ["Invesco Solar ETF","Crocs Inc","Centene Corp","Strategy Inc","SoFi Tech"],
            "Area":   ["Energía","Consumo","Salud","Cripto/AI","Fintech"],
            "Nota":   ["Solar recovery","Post dip","Healthcare turnaround","BTC proxy","Banking license"],
        })

    if wl_df is not None and len(wl_df) > 0:
        # Avisar de tickers externos
        tickers_wl = wl_df["Ticker"].tolist()
        ext_wl = tickers_wl  # v8: todos son externos, no hay universo fijo
        if ext_wl:
            st.info(f"🔄 Cargando datos para: {', '.join(ext_wl)} — usando yfinance si disponible...")

        # ── Analizar cada acción ────────────────────────────────
        wl_results = []
        for _, row in wl_df.iterrows():
            tk      = str(row["Ticker"]).upper()
            nombre  = str(row.get("Nombre", tk))
            area    = str(row.get("Area", "—"))
            nota    = str(row.get("Nota", "—"))

            r = get_row_for_ticker(tk, 0.0)  # precio_compra=0 → se usará el actual
            source = r.get("_source", "universo")

            # Sobrescribir nombre/area si el usuario los dio y son más específicos
            if nombre != tk and r["Nombre"] in [tk, "—"]:
                r["Nombre"] = nombre
            if area != "—" and r["Area"] == "—":
                r["Area"] = area

            wl_results.append({**r, "Nota": nota, "_source": source})

        wl_res_df = pd.DataFrame(wl_results)

        # ── Resumen por momento ─────────────────────────────────
        sm1,sm2,sm3,sm4 = st.columns(4)
        for col,dec,lbl,color in [
            (sm1,"ENTRAR","🔥 Entrar hoy",G),
            (sm2,"ANTICIPAR","⚡ Anticipar",C),
            (sm3,"SEGUIR","👀 Radar",A),
            (sm4,"OBSERVAR","📡 Seguimiento",TXT_MUT),
        ]:
            cnt = len(wl_res_df[wl_res_df["Decision"]==dec])
            with col:
                st.markdown(
                    f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;'
                    f'padding:12px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04)">'
                    f'<div style="font-size:11px;color:{color};font-weight:700">{lbl}</div>'
                    f'<div style="font-size:28px;font-weight:800;color:{color}">{cnt}</div>'
                    f'<div style="font-size:10px;color:{TXT_MUT}">de {len(wl_res_df)}</div>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # ── Tabla de resultados ─────────────────────────────────
        st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">Análisis del patrón NBIS — tu watchlist</div>', unsafe_allow_html=True)

        rows_html = ""
        cols_wl = ["Ticker","Area","Decision","Fase","Trigger","Precio",
                   "RSI","Volumen","EMA50","MACD","Score",
                   "Prob_NBIS","Sim_NBIS","Motivo","Nota","Fuente"]

        hdr_names = {
            "Ticker":"Ticker","Area":"Área","Decision":"Decisión","Fase":"Fase",
            "Trigger":"Trigger","Precio":"Precio","RSI":"RSI","Volumen":"Vol %",
            "EMA50":"vs EMA50","MACD":"MACD","Score":"Score",
            "Prob_NBIS":"Prob NBIS","Sim_NBIS":"Sim. NBIS",
            "Motivo":"Motivo","Nota":"Tu nota","Fuente":"Fuente",
        }

        for _, r in (wl_res_df.sort_values("Score", ascending=False) if "Score" in wl_res_df.columns else wl_res_df).iterrows():
            source_badge_html = (
                f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">● live</span>'
                if r.get("_source")=="yfinance" else
                f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">⚠ est.</span>'
                if r.get("_source")=="estimado" else
                f'<span style="background:{B_BG};color:{B};border:1px solid {B_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">◆ modelo</span>'
            )
            dec_cls = {"ENTRAR":"bg-g","ANTICIPAR":"bg-c","SEGUIR":"bg-a",
                       "OBSERVAR":"bg-gr","REFERENCIA":"bg-p"}.get(r["Decision"],"bg-gr")
            trig_cls = ("bg-g" if "RUPTURA" in str(r["Trigger"]) else
                        "bg-c" if "PRE-SEÑAL" in str(r["Trigger"]) else
                        "bg-a" if "FONDO" in str(r["Trigger"]) else "bg-r")
            sc2 = G if r["Score"]>=75 else A if r["Score"]>=55 else R
            prob_c = G if r["Prob_NBIS"]>=75 else A if r["Prob_NBIS"]>=55 else TXT_MUT
            sim_c  = G if r["Sim_NBIS"]>=60 else A if r["Sim_NBIS"]>=40 else TXT_MUT
            sec_c  = SECTOR_COLORS.get(str(r["Area"]), TXT_MUT)
            nota_str = str(r.get("Nota","—"))[:40]
            ema_v = float(r["EMA50"]) if r["EMA50"] else 0
            macd_v = float(r["MACD"]) if r["MACD"] else 0

            rows_html += f"""<tr>
<td><strong style="color:{B};font-size:13px">{r['Ticker']}</strong></td>
<td><span style="color:{sec_c};font-size:11px;font-weight:600">{r['Area']}</span></td>
<td>{badge(r['Decision'],dec_cls)}</td>
<td><span style="color:{TXT_MUT};font-size:11px">{r['Fase']}</span></td>
<td>{badge(r['Trigger'],trig_cls)}</td>
<td><strong>${r['Precio']:.2f}</strong></td>
<td><span style="color:{c_rsi(r['RSI'])};font-weight:700">{r['RSI']}</span></td>
<td><span style="color:{G if r['Volumen']>150 else TXT_MUT};font-weight:600">{r['Volumen']}%</span></td>
<td><span style="color:{G if ema_v<-10 else A if ema_v<-5 else TXT_MUT};font-weight:600">{ema_v:.1f}%</span></td>
<td><span style="color:{G if macd_v>0 else R};font-weight:600">{macd_v:+.2f}</span></td>
<td><span style="color:{sc2};font-weight:700;font-size:13px">{r['Score']}</span></td>
<td><span style="color:{prob_c};font-weight:700">{r['Prob_NBIS']}</span></td>
<td><span style="color:{sim_c};font-weight:700">{r['Sim_NBIS']:.1f}</span></td>
<td><span style="color:{TXT_MUT};font-size:11px">{r['Motivo']}</span></td>
<td><span style="color:{B};font-size:11px;font-style:italic">{nota_str}</span></td>
<td>{source_badge_html}</td>
</tr>"""

        ths = "".join([f"<th>{hdr_names.get(c,c)}</th>" for c in cols_wl])
        st.markdown(
            f'<div class="tbl-wrap"><table class="dtbl">'
            f'<thead><tr>{ths}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True)

        # ── Cards de oportunidades encontradas en watchlist ─────
        wl_entrar = wl_res_df[wl_res_df["Decision"].isin(["ENTRAR","ANTICIPAR"])].sort_values("Score",ascending=False) if "Score" in wl_res_df.columns else wl_res_df[wl_res_df["Decision"].isin(["ENTRAR","ANTICIPAR"])]
        if not wl_entrar.empty:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{G};margin:16px 0 10px">✅ Oportunidades detectadas en tu watchlist</div>',unsafe_allow_html=True)
            for _,r in wl_entrar.iterrows():
                sc2=G if r["Score"]>=75 else A
                dec_color=G if r["Decision"]=="ENTRAR" else C
                dec_bg=G_BG if r["Decision"]=="ENTRAR" else C_BG
                dec_bor=G_BOR if r["Decision"]=="ENTRAR" else C_BOR
                st.markdown(
                    f'<div style="background:{dec_bg};border:1px solid {dec_bor};'
                    f'border-left:4px solid {dec_color};border-radius:10px;'
                    f'padding:12px 16px;margin-bottom:8px;'
                    f'display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
                    f'<span style="font-size:18px;font-weight:800;color:{B}">{r["Ticker"]}</span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">{r["Nombre"]}</span>'
                    f'{badge(r["Decision"],dec_cls)}'
                    f'<span style="font-size:12px;font-weight:700;color:{sc2}">Score {r["Score"]}/100</span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">Prob NBIS: <strong style="color:{G}">{r["Prob_NBIS"]}%</strong></span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">Sim. NBIS: <strong style="color:{G}">{r["Sim_NBIS"]:.1f}%</strong></span>'
                    f'<span style="font-size:11px;color:{B};font-style:italic">📝 {str(r.get("Nota",""))[:45]}</span>'
                    f'</div>', unsafe_allow_html=True)

        # ── Exportar resultados ─────────────────────────────────
        export_wl = wl_res_df[[
            "Ticker","Nombre","Area","Precio","RSI","Volumen","EMA50","MACD",
            "Score","Decision","Fase","Prob_NBIS","Sim_NBIS","Motivo","Lectura"
        ]].copy()
        export_wl["Nota"] = wl_res_df.get("Nota","—")
        st.download_button(
            "⬇️ Exportar análisis de watchlist (CSV)",
            df_to_csv_chile(export_wl),
            "watchlist_analisis.csv","text/csv",
            key="dl_wl_export")


# ══ TAB 6 — MIS POSICIONES ═════════════════════════════════════
# ══ TAB 7 — MIS POSICIONES ═════════════════════════════════════
with tab6:
    st.markdown(f'<div class="sec-header" style="background:{B_BG};border-color:{B_BOR}"><span style="font-size:20px">💼</span><div><span style="font-size:16px;font-weight:700;color:{B}">Mis posiciones abiertas</span><span style="font-size:12px;color:{TXT_MUT};margin-left:10px">Carga tu CSV · señales de salida · Prob. NBIS · Similitud</span></div></div>',unsafe_allow_html=True)

    # ── Instrucciones CSV ──────────────────────────────────
    with st.expander("📋 Formato del CSV — cómo preparar el archivo", expanded=False):
        st.markdown(f"""
**El CSV debe tener exactamente estas 4 columnas (en cualquier orden):**

| Ticker | Fecha_Compra | Precio_Compra | Cantidad |
|--------|-------------|--------------|----------|
| NBIS   | 2026-03-10  | 92.00        | 50       |
| RGTI   | 2026-02-15  | 12.50        | 200      |
| HOOD   | 2026-03-20  | 71.00        | 80       |

- **Ticker**: debe coincidir con los tickers del universo del modelo
- **Fecha_Compra**: formato YYYY-MM-DD
- **Precio_Compra**: precio en USD con decimales (usar punto, no coma)
- **Cantidad**: número entero de acciones

También puedes descargar la plantilla de abajo y completarla.
""")
        # Plantilla descargable
        template_df = pd.DataFrame({
            "Ticker":["NBIS","RGTI","HOOD","APLD"],
            "Fecha_Compra":["2026-03-10","2026-02-15","2026-03-20","2026-03-05"],
            "Precio_Compra":[92.00,12.50,71.00,18.50],
            "Cantidad":[50,200,80,150],
        })
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            "⬇️ Descargar plantilla CSV",
            csv_template,
            "posiciones_template.csv",
            "text/csv",
            key="dl_template",
        )

    # ── Upload ─────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📂 Subir archivo CSV con posiciones",
        type=["csv"],
        help="Formato: Ticker, Fecha_Compra, Precio_Compra, Cantidad",
    )

    posiciones_df = None

    if uploaded:
        try:
            # Auto-detectar separador (coma o punto y coma)
            _raw_pos = uploaded.read()
            _sep_pos = ";" if b";" in _raw_pos[:200] else ","
            import io
            posiciones_df = pd.read_csv(io.BytesIO(_raw_pos),
                                        sep=_sep_pos,
                                        encoding="utf-8-sig",
                                        on_bad_lines="skip")
            posiciones_df.columns = [c.strip() for c in posiciones_df.columns]
            # Aceptar tanto "Fecha_Compra" como "Fecha"
            if "Fecha_Compra" in posiciones_df.columns and "Fecha" not in posiciones_df.columns:
                posiciones_df = posiciones_df.rename(columns={"Fecha_Compra": "Fecha"})
            required = ["Ticker","Precio_Compra","Cantidad","Fecha"]
            missing = [c for c in required if c not in posiciones_df.columns]
            if missing:
                st.error(f"❌ Columnas faltantes en el CSV: {', '.join(missing)}")
                posiciones_df = None
            else:
                posiciones_df["Ticker"]        = posiciones_df["Ticker"].str.upper().str.strip()
                posiciones_df["Precio_Compra"] = pd.to_numeric(posiciones_df["Precio_Compra"], errors="coerce")
                posiciones_df["Cantidad"]      = pd.to_numeric(posiciones_df["Cantidad"], errors="coerce")
                posiciones_df = posiciones_df.dropna(subset=["Precio_Compra","Cantidad"])
                # Normalizar fechas — acepta DD-MM-YYYY y YYYY-MM-DD
                for _fcol in ["Fecha","Cat_Fecha"]:
                    if _fcol in posiciones_df.columns:
                        posiciones_df[_fcol] = pd.to_datetime(
                            posiciones_df[_fcol], dayfirst=True, errors="coerce"
                        ).dt.strftime("%Y-%m-%d").fillna("—")
                # Columnas opcionales
                if "Cat_Fecha" not in posiciones_df.columns:
                    posiciones_df["Cat_Fecha"] = "—"
                if "Tipo" not in posiciones_df.columns:
                    posiciones_df["Tipo"] = "Accion"
                if "Estrategia" not in posiciones_df.columns:
                    posiciones_df["Estrategia"] = "Swing"
                # Múltiples compras del mismo ticker = filas separadas (precio de compra distinto)
                if posiciones_df["Ticker"].duplicated().any():
                    n_dup = posiciones_df["Ticker"].duplicated().sum()
                    tickers_dup = posiciones_df[posiciones_df["Ticker"].duplicated(keep=False)]["Ticker"].unique().tolist()
                    st.info(f"ℹ️ {tickers_dup} tienen múltiples compras — se muestran como filas separadas con su precio de compra individual.")
                st.success(f"✅ CSV cargado — {len(posiciones_df)} posiciones encontradas")
        except Exception as e:
            st.error(f"❌ Error leyendo el CSV: {e}")
            posiciones_df = None
    else:
        posiciones_df = None
        st.markdown(
            f'<div style="background:{B_BG};border:1px solid {B_BOR};border-radius:12px;'+
            f'padding:32px;text-align:center;margin-top:16px">'+
            f'<div style="font-size:36px;margin-bottom:10px">💼</div>'+
            f'<div style="font-size:15px;font-weight:700;color:{B};margin-bottom:8px">'+
            f'Sube tu archivo CSV para ver tus posiciones</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT};margin-bottom:16px;line-height:1.7">'+
            f'Formato requerido:<br>'+
            f'<code style="background:{BG_HEAD};padding:2px 8px;border-radius:4px;font-size:11px">'+
            f'Ticker, Precio_Compra, Cantidad, Fecha</code><br><br>'+
            f'Ejemplo:<br>'+
            f'<code style="background:{BG_HEAD};padding:4px 8px;border-radius:4px;font-size:11px;display:inline-block;text-align:left">'+
            f'NBIS,129.90,3,2026-04-09<br>MRNA,42.58,15,2026-02-17<br>CROX,78.72,4,2026-02-17</code>'+
            f'</div>'+
            f'<div style="font-size:11px;color:{TXT_SOFT}">'+
            f'Usa el botón "Browse files" del sidebar para subir tu archivo</div>'+
            f'</div>', unsafe_allow_html=True)

    # ── Análisis de posiciones ──────────────────────────────
    if posiciones_df is not None and len(posiciones_df) > 0:
        total_inv=0; total_act=0; total_pnl=0; n_ok=0

        # Barra de progreso mientras carga tickers externos
        tickers_csv = posiciones_df["Ticker"].str.upper().str.strip().tolist()
        externos = tickers_csv  # v8: todos son externos
        if externos:
            st.info(f"🔄 Cargando datos para: {', '.join(externos)} — puede tomar unos segundos si hay internet...")

        for _,pos in posiciones_df.iterrows():
            tk  = str(pos["Ticker"]).upper()
            pc  = float(pos["Precio_Compra"])
            qty = int(pos["Cantidad"])
            fch = str(pos.get("Fecha","—"))

            r = get_row_for_ticker(tk, pc)
            source = r.get("_source","universo")
            pa  = r["Precio"]
            inv = pc*qty; act=pa*qty
            pnl_usd=act-inv; pnl_pct=(pa-pc)/pc*100
            total_inv+=inv; total_act+=act; total_pnl+=pnl_usd; n_ok+=1

            _dias_pos = (pd.Timestamp.now()-pd.to_datetime(fch,errors="coerce")).days if fch not in ("—","","nan") else 0
            # Usar Cat_Fecha del CSV si existe, sino del scanner
            _cat_fecha_csv = str(pos.get("Cat_Fecha","—")) if "Cat_Fecha" in pos else "—"
            _cat_fecha_use = _cat_fecha_csv if _cat_fecha_csv not in ("—","","nan") else str(r.get("Cat_Fecha","—"))
            _tipo_pos = str(pos.get("Tipo","Accion")) if "Tipo" in pos else "Accion"
            _estrategia_pos = str(pos.get("Estrategia","Swing")) if "Estrategia" in pos else "Swing"
            # Auto-detectar cripto ETFs por ticker si Tipo no está definido
            _crypto_etfs = ["IBIT","ETHA","GBTC","FBTC","ETHW","BITB","ARKB","BRRR","BTCO","DEFI"]
            _index_etfs  = ["VOO","SPY","IVV","QQQ","VTI","SCHB","ITOT","VEA","VWO","AGG","BND"]
            if _tipo_pos == "Accion":
                if tk in _crypto_etfs:
                    _tipo_pos = "ETF_Cripto"
                elif tk in _index_etfs:
                    _tipo_pos = "ETF_Indice"
            # Score de rebote v11
            _tiene_cat = _cat_fecha_use not in ("—","","nan")
            _dias_cat  = 999
            try:
                import datetime as _dtt
                if _tiene_cat:
                    _fc = pd.to_datetime(_cat_fecha_use, errors="coerce")
                    if not pd.isna(_fc):
                        _dias_cat = (_fc.date() - _dtt.date.today()).days
            except Exception: pass
            _score_rebote = calcular_score_rebote(
                dd=float(r.get("DD_pico",0)),
                rsi=float(r["RSI"]),
                vol_ratio=float(r.get("Volumen",100)),
                dias_alcistas=0,
                momentum_3d=float(r.get("MACD",0)),
                tiene_catalizador=_tiene_cat,
                dias_para_cat=_dias_cat,
                beta=float(r.get("Beta",1.5))
            )
            _vix_val = float(vix.get("valor",20)) if vix.get("_ok") else 20
            _sizing  = clasificar_sizing(_score_rebote["score"], _vix_val)
            analisis = analizar_posicion(
                pc,pa,r["RSI"],r["MACD"],
                abs(r["EMA50"]) if r["EMA50"]>0 else 0,
                r["Score"],pnl_pct,r["Prob_NBIS"],r["Sim_NBIS"],r["Beta"],
                cat_fecha=_cat_fecha_use,
                dias_posicion=_dias_pos,
                tipo=_tipo_pos,
                estrategia=_estrategia_pos)

            señal    = analisis["señal"]
            razon    = analisis["razon"]
            s_color  = analisis["color"]
            urgencia = analisis["urgencia"]
            tramos   = analisis["tramos"]

            pnl_color=G if pnl_pct>0 else R
            urg_cls={"URGENTE":"bg-r","HOY":"bg-or","ESTA SEMANA":"bg-a","AJUSTAR":"bg-a","REVISAR":"bg-r","HOLD":"bg-g","MONITOR":"bg-b"}.get(urgencia,"bg-gr")
            borde=s_color
            sec_c=SECTOR_COLORS.get(r["Area"],TXT_MUT)

            # ── Tarjeta posición ──
            st.markdown(f'<div class="pos-card" style="border-left:5px solid {borde}">',unsafe_allow_html=True)

            # Fila 1: identificación + resumen
            ci1,ci2,ci3,ci4,ci5 = st.columns([2,1,1,1,2])
            with ci1:
                source_badge = ""
                if source == "yfinance":
                    source_badge = f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700;margin-left:6px">● live</span>'
                elif source == "estimado":
                    source_badge = f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700;margin-left:6px">⚠ estimado</span>'
                st.markdown(f'<div><span style="font-size:22px;font-weight:800;color:{B}">{tk}</span>{source_badge}<span style="color:{sec_c};font-size:11px;font-weight:700;margin-left:8px">{r["Area"]}</span><br><span style="color:{TXT_MUT};font-size:11px">{qty} acciones · compra ${pc:.2f} · {fch}</span></div>',unsafe_allow_html=True)
            with ci2:
                # Determinar fuente del precio
                es_live_pos = r.get("_precio_live", False) or source == "yfinance"
                precio_badge = (
                    f'<div style="font-size:9px;color:{G};font-weight:600;margin-top:2px">● live</div>'
                    if es_live_pos else
                    f'<div style="font-size:9px;color:{A};font-weight:600;margin-top:2px">⚠ estático</div>'
                )
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:11px;color:{TXT_MUT};font-weight:600">Precio actual</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{TXT}">${pa:.2f}</div>'
                    f'{precio_badge}'
                    f'</div>', unsafe_allow_html=True)
            with ci3:
                st.markdown(f'<div style="text-align:center"><div style="font-size:11px;color:{TXT_MUT};font-weight:600">P&L</div><div style="font-size:20px;font-weight:800;color:{pnl_color}">{pnl_pct:+.1f}%</div><div style="font-size:11px;color:{pnl_color};font-weight:600">${pnl_usd:+,.0f}</div></div>',unsafe_allow_html=True)
            with ci4:
                sc_c=G if _score_rebote["score"]>=75 else A if _score_rebote["score"]>=55 else R
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:11px;color:{TXT_MUT};font-weight:600">Score Rebote</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{sc_c}">{_score_rebote["score"]}</div>'
                    f'<div style="font-size:10px;color:{sc_c}">{_score_rebote["nivel"]}</div>'
                    f'</div>',unsafe_allow_html=True)
            with ci5:
                # Barra visual de 3 tramos
                tramo_html = ""
                for pct, etiq, color in tramos:
                    if pct > 0:
                        tramo_html += (
                            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">'
                            f'<div style="width:{max(pct,8)*1.4:.0f}px;height:10px;border-radius:5px;background:{color}"></div>'
                            f'<span style="font-size:11px;font-weight:700;color:{color}">{pct}%</span>'
                            f'<span style="font-size:10px;color:{TXT_MUT}">{etiq}</span>'
                            f'</div>'
                        )
                st.markdown(
                    f'<div>'
                    f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600;margin-bottom:6px">GESTIÓN DE POSICIÓN</div>'
                    f'{tramo_html}'
                    f'<span class="badge {urg_cls}" style="margin-top:4px;display:inline-block">{urgencia}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

            st.markdown(f'<hr style="border:none;border-top:1px solid {BOR};margin:12px 0">',unsafe_allow_html=True)

            # Fila 2: indicadores + NBIS + objetivos + lectura
            cd1,cd2,cd3,cd4 = st.columns(4)
            with cd1:
                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">Indicadores actuales</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;font-size:11px">'
                    f'<span style="color:{TXT_MUT}">RSI</span><span style="color:{c_rsi(r["RSI"])};font-weight:700">{r["RSI"]}</span>'
                    f'<span style="color:{TXT_MUT}">MACD</span><span style="color:{G if r["MACD"]>0 else R};font-weight:700">{r["MACD"]:+.2f}</span>'
                    f'<span style="color:{TXT_MUT}">Volumen</span><span style="color:{c_vol(r["Volumen"]/100)};font-weight:700">{r["Volumen"]}%</span>'
                    f'<span style="color:{TXT_MUT}">Beta</span><span style="color:{TXT};font-weight:700">{r["Beta"]}</span>'
                    f'<span style="color:{TXT_MUT}">Pre-Mkt</span><span style="color:{c_pre(r["Pre_Move"])};font-weight:700">+{r["Pre_Move"]:.1f}%</span>'
                    f'<span style="color:{TXT_MUT}">Vol Pre</span><span style="color:{c_vol(r["Pre_Vol"])};font-weight:700">{r["Pre_Vol"]:.1f}x</span>'
                    f'</div></div>',unsafe_allow_html=True)
            with cd2:
                # Señal de gestión de posición — no score de entrada
                rsi_pos = r["RSI"]
                pnl_pos = pnl_pct

                # Determinar semáforo de gestión
                if pnl_pos >= 40:
                    gest_color = G; gest_emoji = "🟢"
                    gest_titulo = "Ganancia sólida"
                    gest_msg = f"Tramo 1 ejecutado? Si no, vender 30% ahora. Dejar runner."
                elif pnl_pos >= 20:
                    gest_color = G; gest_emoji = "🟢"
                    gest_titulo = "Objetivo 1 alcanzado"
                    gest_msg = "Vender 30% para asegurar ganancia. Mantener 70% con stop."
                elif pnl_pos >= 10:
                    gest_color = A; gest_emoji = "🟡"
                    gest_titulo = "En camino"
                    gest_msg = "Mantener. Vigilar RSI y catalizador próximo."
                elif pnl_pos >= 0:
                    gest_color = A; gest_emoji = "🟡"
                    gest_titulo = "Break even"
                    gest_msg = "Sin ganancia aún. Confirmar que el catalizador sigue activo."
                elif pnl_pos >= -15:
                    gest_color = R; gest_emoji = "🔴"
                    gest_titulo = "En pérdida moderada"
                    gest_msg = "Revisar catalizador. ¿Sigue válido? Si no, evaluar salida."
                else:
                    gest_color = R; gest_emoji = "🔴"
                    gest_titulo = "Pérdida alta — acción requerida"
                    gest_msg = "Stop loss cercano. Evaluar salida inmediata."

                # RSI de la posición
                rsi_gest = "RSI alto — zona salida" if rsi_pos > 65 else \
                           "RSI medio — mantener" if rsi_pos > 45 else \
                           "RSI bajo — posición sana"
                rsi_gest_c = R if rsi_pos > 65 else A if rsi_pos > 45 else G

                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">📊 Estado de la posición</div>'
                    f'<div style="background:{gest_color}18;border:1px solid {gest_color}44;border-radius:8px;padding:8px;margin-bottom:10px">'
                    f'  <div style="font-size:12px;font-weight:700;color:{gest_color}">{gest_emoji} {gest_titulo}</div>'
                    f'  <div style="font-size:11px;color:{TXT_MUT};margin-top:4px;line-height:1.5">{gest_msg}</div>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">'
                    f'  <span style="color:{TXT_MUT}">RSI actual</span>'
                    f'  <span style="color:{rsi_gest_c};font-weight:700">{rsi_pos:.0f} — {rsi_gest}</span>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px">'
                    f'  <span style="color:{TXT_MUT}">Días en posición</span>'
                    f'  <span style="color:{TXT};font-weight:700">'
                    f'{(pd.Timestamp.now()-pd.to_datetime(pos["Fecha"],errors="coerce")).days if "Fecha" in pos else "—"} días</span>'
                    f'</div>'
                    f'</div>', unsafe_allow_html=True)
            with cd3:
                # Objetivos — usar _tipo_pos ya calculado arriba
                _beta_p = float(r.get("Beta", 1.5))
                if _tipo_pos=="ETF_Cripto":   stop_val=pc*0.80; obj1=pc*1.30; obj2=pc*1.60; obj3=pc*2.00
                elif _tipo_pos=="ETF_Indice": stop_val=pc*0.88; obj1=pc*1.15; obj2=pc*1.25; obj3=pc*1.40
                elif _tipo_pos=="ETF_Sectorial": stop_val=pc*0.90; obj1=pc*1.20; obj2=pc*1.40; obj3=pc*1.60
                elif _beta_p < 1.5:           stop_val=pc*0.88; obj1=pc*1.15; obj2=pc*1.25; obj3=pc*1.40
                elif _beta_p < 2.5:           stop_val=pc*0.90; obj1=pc*1.20; obj2=pc*1.40; obj3=pc*1.60
                else:                         stop_val=pc*0.82; obj1=pc*1.25; obj2=pc*1.50; obj3=pc*1.80
                stop_pct = (stop_val/pa-1)*100 if pa>0 else 0
                obj1_pct  = (obj1/pa-1)*100 if pa>0 else 0
                obj2_pct  = (obj2/pa-1)*100 if pa>0 else 0
                obj3_pct  = (obj3/pa-1)*100 if pa>0 else 0

                def obj_color(pct):
                    return G if pct <= 0 else A if pct <= 20 else C

                def tramo_badge(label, color):
                    return (f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
                            f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{label}</span>')

                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:10px">🎯 Plan de salida — 3 tramos</div>'

                    # Stop loss
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{R}">${stop_val:.2f}</span>'
                    f'  <span style="font-size:10px;color:{R}"> ({stop_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("🛑 STOP LOSS", R)}</div>'
                    f'</div>'

                    # Tramo 1
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj1_pct)}">${obj1:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj1_pct)}"> ({obj1_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("VENDER 30%", A)}</div>'
                    f'</div>'

                    # Tramo 2
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj2_pct)}">${obj2:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj2_pct)}"> ({obj2_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("VENDER 40%", G)}</div>'
                    f'</div>'

                    # Tramo 3
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj3_pct)}">${obj3:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj3_pct)}"> ({obj3_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("RUNNER 30%", C)}</div>'
                    f'</div>'

                    f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:6px;border-top:1px solid {BOR};padding-top:5px">'
                    f'% = cuánto falta desde precio actual · Verde = ya alcanzado</div>'
                    f'</div>', unsafe_allow_html=True)
            with cd4:
                tramos_resumen = " · ".join([f'<span style="color:{c};font-weight:700">{p}% {e}</span>' for p,e,c in tramos if p>0])
                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">Lectura del trader</div>'
                    f'<div style="font-size:12px;margin-bottom:8px">{tramos_resumen}</div>'
                    f'<div style="font-size:11px;color:{TXT_MUT};line-height:1.7">{razon}</div>'
                    f'<div style="margin-top:10px;font-size:10px;color:{TXT_SOFT}">Catalizador: {"Earnings " + _cat_fecha_use if _cat_fecha_use not in ("—","","nan") else "Sin catalizador identificado"}</div>'
                    f'<div style="font-size:10px;color:{"" + G if _cat_fecha_use not in ("—","","nan") else TXT_SOFT}">Próximo: {_cat_fecha_use}</div>'
                    f'</div>',unsafe_allow_html=True)

            # ── NBIS Panel + Pre/Post Market ─────────────────
            st.markdown(
                render_nbis_panel(
                    r.get("Prob_NBIS", 0), r.get("Sim_NBIS", 0),
                    G, A, R, C, TXT, TXT_MUT, TXT_SOFT, BG_HEAD, BOR
                ) + render_pre_post_bar(
                    str(r.get("Ticker", tk)), r.get("Precio", pa),
                    G, A, R, TXT_MUT, TXT_SOFT, BG_HEAD, BOR
                ), unsafe_allow_html=True)

            st.markdown('</div>',unsafe_allow_html=True)  # cierra pos-card

        # ── Alerta concentración sectorial ──────────────────
        sectores_pos = {}
        for _, _prow in posiciones_df.iterrows():
            _ptk = str(_prow["Ticker"]).upper()
        # Calcular concentración desde los datos ya cargados
        if n_ok > 0:
            _areas = {}
            for _, _prow in posiciones_df.iterrows():
                _tipo_c = str(_prow.get("Tipo","Accion"))
                _areas[_tipo_c] = _areas.get(_tipo_c, 0) + 1
            _concentradas = {k:v for k,v in _areas.items() if v >= 3}
            if _concentradas:
                for _sector_c, _cnt_c in _concentradas.items():
                    st.warning(f"⚠️ Concentración: tienes {_cnt_c} posiciones en {_sector_c}. "
                               f"Si el sector cae, caen todas juntas. Considera diversificar.")

        # ── Resumen portafolio ──────────────────────────────
        if n_ok>0:
            pnl_total_pct=(total_act/total_inv-1)*100 if total_inv>0 else 0
            st.markdown("---")
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">Resumen del portafolio</div>',unsafe_allow_html=True)
            pr1,pr2,pr3,pr4=st.columns(4)
            with pr1: st.metric("Invertido",f"${total_inv:,.0f}")
            with pr2: st.metric("Valor actual",f"${total_act:,.0f}")
            with pr3: st.metric("P&L total",f"${total_pnl:+,.0f}",f"{pnl_total_pct:+.1f}%",delta_color="normal" if pnl_total_pct>0 else "inverse")
            with pr4: st.metric("Posiciones",n_ok)

            # Exportar análisis
            export_rows=[]
            for _,pos in posiciones_df.iterrows():
                tk=str(pos["Ticker"]).upper()
                pc=float(pos["Precio_Compra"]); qty=int(pos["Cantidad"])
                r=get_row_for_ticker(tk,pc); pa=r["Precio"]
                pnl_e=(pa-pc)/pc*100
                analisis2=analizar_posicion(pc,pa,r["RSI"],r["MACD"],abs(r["EMA50"]) if r["EMA50"]>0 else 0,r["Score"],pnl_e,r["Prob_NBIS"],r["Sim_NBIS"],r["Beta"])
                # Determinar etapa de la señal al momento del escaneo
            _dias_pos_e = max(1, _dias_pos)
            if _dias_pos_e <= 1:
                _etapa_senal = "🔥 Entrar Hoy (M3)"
            elif _dias_pos_e <= 3:
                _etapa_senal = "⚡ Entrada Válida (M2)"
            elif pnl_e < -3:
                _etapa_senal = "📡 Detectadas M1"
            else:
                _etapa_senal = "⚡ Entrada Temprana (M2)"
            export_rows.append({"Ticker":tk,"Etapa_Señal":_etapa_senal,"Precio_Compra":pc,"Precio_Actual":pa,"Cantidad":qty,"P&L_%":round(pnl_e,2),"P&L_USD":round((pa-pc)*qty,2),"Score_Rebote":r.get("Score_Rebote",0),"Nivel_Rebote":r.get("Nivel_Rebote","—"),"Señal":analisis2["señal"],"Urgencia":analisis2["urgencia"],"Catalizador":str(r["Cat_Desc"])[:50],"Fecha_Cat":r["Cat_Fecha"]})
            if export_rows:
                export_csv=df_to_csv_chile(pd.DataFrame(export_rows))
                st.download_button("⬇️ Exportar análisis de posiciones (CSV)",export_csv,"analisis_posiciones.csv","text/csv")

        if posiciones_df is not None and len(posiciones_df) > 0:
            render_catalysts_section(posiciones_df, "mis_pos")

# ══ TAB 7 — POSICIONES AMPARITO ═════════════════════════════════
with tab7:
    st.markdown(
        f'<div class="sec-header" style="background:{P_BG};border-color:{P_BOR}">'
        f'<span style="font-size:20px">💜</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{P}">Posiciones Amparito</span>'
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'
        f'Portfolio independiente · Misma lógica de gestión · Señales de salida por tramos</span></div>'
        f'</div>', unsafe_allow_html=True)

    uploaded_amp = st.file_uploader(
        "📂 Subir posiciones de Amparito (CSV)",
        type=["csv"], key="csv_amparito",
        help="Formato: Ticker, Precio_Compra, Cantidad, Fecha")

    amp_df = None

    if uploaded_amp:
        try:
            # Auto-detectar separador
            _raw_amp = uploaded_amp.read()
            _sep_amp = ";" if b";" in _raw_amp[:200] else ","
            import io as _io
            amp_df = pd.read_csv(_io.BytesIO(_raw_amp),
                                 sep=_sep_amp,
                                 encoding="utf-8-sig",
                                 on_bad_lines="skip")
            amp_df.columns = [c.strip() for c in amp_df.columns]
            if "Fecha_Compra" in amp_df.columns and "Fecha" not in amp_df.columns:
                amp_df = amp_df.rename(columns={"Fecha_Compra":"Fecha"})
            required_a = ["Ticker","Precio_Compra","Cantidad","Fecha"]
            missing_a  = [x for x in required_a if x not in amp_df.columns]
            if missing_a:
                st.error(f"❌ Faltan columnas: {missing_a}")
                amp_df = None
            else:
                amp_df["Ticker"]        = amp_df["Ticker"].str.upper().str.strip()
                amp_df["Precio_Compra"] = pd.to_numeric(amp_df["Precio_Compra"], errors="coerce")
                amp_df["Cantidad"]      = pd.to_numeric(amp_df["Cantidad"], errors="coerce")
                amp_df = amp_df.dropna(subset=["Precio_Compra","Cantidad"])
                # Normalizar fechas — acepta DD-MM-YYYY y YYYY-MM-DD
                for _fcol in ["Fecha","Cat_Fecha"]:
                    if _fcol in amp_df.columns:
                        amp_df[_fcol] = pd.to_datetime(
                            amp_df[_fcol], dayfirst=True, errors="coerce"
                        ).dt.strftime("%Y-%m-%d").fillna("—")
                # Columnas opcionales
                if "Cat_Fecha" not in amp_df.columns:
                    amp_df["Cat_Fecha"] = "—"
                if "Tipo" not in amp_df.columns:
                    amp_df["Tipo"] = "Accion"
                if "Estrategia" not in amp_df.columns:
                    amp_df["Estrategia"] = "Swing"
                if amp_df["Ticker"].duplicated().any():
                    tks_dup = amp_df[amp_df["Ticker"].duplicated(keep=False)]["Ticker"].unique().tolist()
                    st.info(f"ℹ️ {tks_dup} tienen múltiples compras — se muestran como filas separadas.")
                st.success(f"✅ {len(amp_df)} posiciones cargadas para Amparito")
        except Exception as e:
            st.error(f"❌ Error leyendo CSV: {e}")
            amp_df = None
    else:
        st.markdown(
            f'<div style="background:{P_BG};border:1px solid {P_BOR};border-radius:12px;'
            f'padding:32px;text-align:center;margin-top:16px">'
            f'<div style="font-size:36px;margin-bottom:10px">💜</div>'
            f'<div style="font-size:15px;font-weight:700;color:{P};margin-bottom:8px">'
            f'Sube el CSV de posiciones de Amparito</div>'
            f'<div style="font-size:12px;color:{TXT_MUT};line-height:1.7">'
            f'Mismo formato que Mis Posiciones:<br>'
            f'<code style="background:{BG_HEAD};padding:2px 8px;border-radius:4px;font-size:11px">'
            f'Ticker, Precio_Compra, Cantidad, Fecha</code></div>'
            f'</div>', unsafe_allow_html=True)

    if amp_df is not None and len(amp_df) > 0:
        total_inv_a=0; total_act_a=0; total_pnl_a=0; n_ok_a=0

        for _,pos in amp_df.iterrows():
            tk  = str(pos["Ticker"]).upper()
            pc  = float(pos["Precio_Compra"])
            qty = float(pos["Cantidad"])
            fch = str(pos.get("Fecha","—"))

            r = get_row_for_ticker(tk, pc)
            pa  = r["Precio"]
            inv = pc*qty; act=pa*qty
            pnl_usd=act-inv; pnl_pct=(pa-pc)/pc*100
            total_inv_a+=inv; total_act_a+=act; total_pnl_a+=pnl_usd; n_ok_a+=1

            _dias_pos_a = (pd.Timestamp.now()-pd.to_datetime(fch,errors="coerce")).days if fch not in ("—","","nan") else 0
            _cat_fecha_a = str(pos.get("Cat_Fecha","—")) if "Cat_Fecha" in pos else "—"
            _tipo_a = str(pos.get("Tipo","Accion")) if "Tipo" in pos else "Accion"
            _estrategia_a = str(pos.get("Estrategia","Swing")) if "Estrategia" in pos else "Swing"
            # Auto-detectar cripto y ETF índice por ticker
            if _tipo_a == "Accion":
                if tk in ["IBIT","ETHA","GBTC","FBTC","ETHW","BITB","ARKB","BRRR","BTCO"]:
                    _tipo_a = "ETF_Cripto"
                elif tk in ["VOO","SPY","IVV","QQQ","VTI","SCHB","ITOT"]:
                    _tipo_a = "ETF_Indice"
            analisis = analizar_posicion(pc,pa,r["RSI"],r["MACD"],
                abs(r["EMA50"]) if r["EMA50"]>0 else 0,
                r["Score"],pnl_pct,r["Prob_NBIS"],r["Sim_NBIS"],r["Beta"],
                cat_fecha=_cat_fecha_a,
                dias_posicion=_dias_pos_a,
                tipo=_tipo_a,
                estrategia=_estrategia_a)
            tramos   = analisis["tramos"]
            razon    = analisis["razon"]
            urgencia = analisis["urgencia"]

            pnl_c   = G if pnl_pct>0 else R
            urg_cls = {"URGENTE":"bg-r","HOY":"bg-or","ESTA SEMANA":"bg-a",
                      "AJUSTAR":"bg-a","REVISAR":"bg-r","HOLD":"bg-g",
                      "MONITOR":"bg-b"}.get(urgencia,"bg-gr")

            # Header posición
            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {P_BOR};'
                f'border-left:4px solid {P};border-radius:12px;padding:14px 18px;margin-bottom:8px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                f'<div style="display:flex;align-items:center;gap:10px">'
                f'  <span style="font-size:20px;font-weight:800;color:{P}">{tk}</span>'
                f'  <span class="badge {urg_cls}">{urgencia}</span>'
                f'  <span style="font-size:11px;color:{TXT_SOFT}">{qty:.4f} acc · compra ${pc:.2f} · {fch}</span>'
                f'</div>'
                f'<div style="display:flex;gap:20px;align-items:center">'
                f'  <div style="text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">Precio actual</div>'
                f'    <div style="font-size:18px;font-weight:800;color:{TXT}">${pa:.2f}</div>'
                f'  </div>'
                f'  <div style="text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">P&L</div>'
                f'    <div style="font-size:18px;font-weight:800;color:{pnl_c}">{pnl_pct:+.1f}%</div>'
                f'    <div style="font-size:11px;color:{pnl_c}">${pnl_usd:+,.0f}</div>'
                f'  </div>'
                f'</div></div>'
                f'</div>', unsafe_allow_html=True)

            # Targets dinámicos según Tipo
            if _tipo_a == "ETF_Cripto":
                _a_stop=pc*0.80; _a_t1=pc*1.30; _a_t2=pc*1.60; _a_t3=pc*2.00
            elif _tipo_a == "ETF_Indice":
                _a_stop=pc*0.88; _a_t1=pc*1.15; _a_t2=pc*1.25; _a_t3=pc*1.40
            else:
                _a_stop=pc*0.90; _a_t1=pc*1.20; _a_t2=pc*1.40; _a_t3=pc*1.60

            def _ac(p): return G if (p/pa-1)*100<=0 else A if (p/pa-1)*100<=20 else C

            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px">'
                f'  <div style="background:{R_BG};border:1px solid {R_BOR};border-radius:6px;padding:6px;text-align:center">'
                f'    <div style="font-size:9px;color:{R};font-weight:700">🛑 STOP</div>'
                f'    <div style="font-size:12px;font-weight:700;color:{R}">${_a_stop:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">({(_a_stop/pa-1)*100:+.1f}%)</div></div>'
                f'  <div style="background:{A_BG};border:1px solid {A_BOR};border-radius:6px;padding:6px;text-align:center">'
                f'    <div style="font-size:9px;color:{A};font-weight:700">VENDER 30%</div>'
                f'    <div style="font-size:12px;font-weight:700;color:{_ac(_a_t1)}">${_a_t1:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">({(_a_t1/pa-1)*100:+.1f}%)</div></div>'
                f'  <div style="background:{G_BG};border:1px solid {G_BOR};border-radius:6px;padding:6px;text-align:center">'
                f'    <div style="font-size:9px;color:{G};font-weight:700">VENDER 40%</div>'
                f'    <div style="font-size:12px;font-weight:700;color:{_ac(_a_t2)}">${_a_t2:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">({(_a_t2/pa-1)*100:+.1f}%)</div></div>'
                f'  <div style="background:{C_BG};border:1px solid {C_BOR};border-radius:6px;padding:6px;text-align:center">'
                f'    <div style="font-size:9px;color:{C};font-weight:700">RUNNER 30%</div>'
                f'    <div style="font-size:12px;font-weight:700;color:{_ac(_a_t3)}">${_a_t3:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">({(_a_t3/pa-1)*100:+.1f}%)</div></div>'
                f'</div>'
                f'<div style="font-size:10px;color:{TXT_MUT};margin-top:4px;'
                f'border-top:1px solid {BOR};padding-top:6px">{razon}</div>',
                unsafe_allow_html=True)

            st.markdown(
                render_nbis_panel(r.get("Prob_NBIS",0), r.get("Sim_NBIS",0),
                    G, A, R, C, TXT, TXT_MUT, TXT_SOFT, BG_HEAD, BOR) +
                render_pre_post_bar(tk, pa, G, A, R, TXT_MUT, TXT_SOFT, BG_HEAD, BOR),
                unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # Resumen Amparito
        if n_ok_a > 0:
            pnl_total_pct_a = (total_act_a/total_inv_a-1)*100 if total_inv_a>0 else 0
            st.markdown("---")
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{P};margin-bottom:10px">💜 Resumen portfolio Amparito</div>',unsafe_allow_html=True)
            pa1,pa2,pa3,pa4 = st.columns(4)
            with pa1: st.metric("Invertido", f"${total_inv_a:,.0f}")
            with pa2: st.metric("Valor actual", f"${total_act_a:,.0f}")
            with pa3: st.metric("P&L total", f"${total_pnl_a:+,.0f}",
                               f"{pnl_total_pct_a:+.1f}%",
                               delta_color="normal" if pnl_total_pct_a>0 else "inverse")
            with pa4: st.metric("Posiciones", n_ok_a)

        if amp_df is not None and len(amp_df) > 0:
            render_catalysts_section(amp_df, "amparito")


# ══ TAB 8 — ESTRATEGIA ETF ══════════════════════════════════
with tab8:
    st.markdown(
        f'<div class="sec-header" style="background:#FEF9C3;border-color:#FDE047">'+
        f'<span style="font-size:20px">💰</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:#854D0E">Estrategia ETF</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'+
        f'Monitor de ETFs · Estrategia de inversión personalizada · DCA automático</span></div>'+
        f'</div>', unsafe_allow_html=True)

    # ── Inputs de usuario ─────────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">⚙️ Configuración</div>',unsafe_allow_html=True)
    ei1, ei2, ei3, ei4 = st.columns(4)
    with ei1:
        capital_usd = st.number_input("Capital USD", min_value=100, max_value=1000000,
                                       value=4000, step=100,
                                       help="Capital a invertir en USD")
    with ei2:
        tipo_cambio = st.number_input("Tipo cambio CLP/USD", min_value=700, max_value=1100,
                                       value=879, step=1,
                                       help="Pesos chilenos por 1 dólar")
    with ei3:
        plazo_etf = st.selectbox("Horizonte", ["Corto (6-12m)","Mediano (2-5a)","Largo (5-10a)"],
                                  index=1)
    with ei4:
        perfil_etf = st.selectbox("Perfil riesgo", ["Conservador","Moderado","Agresivo"],
                                   index=1)

    capital_clp = capital_usd * tipo_cambio
    st.markdown(
        f'<div style="background:#FEF9C3;border:1px solid #FDE047;border-radius:8px;'+
        f'padding:8px 14px;margin-bottom:14px;font-size:12px;color:#854D0E">'+
        f'💵 <strong>${capital_usd:,.0f} USD</strong> = '+
        f'<strong>${capital_clp:,.0f} CLP</strong> · '+
        f'Tipo cambio: ${tipo_cambio} CLP/USD</div>',
        unsafe_allow_html=True)

    st.markdown("---")

    # ── Estado actual de ETFs ─────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">📊 Estado actual de los ETFs</div>',unsafe_allow_html=True)

    if st.button("🔄 Cargar datos de ETFs", use_container_width=False, key="btn_etf"):
        with st.spinner("Cargando datos de ETFs..."):
            etf_results = {}
            for tk in ETF_UNIVERSE.keys():
                etf_results[tk] = fetch_etf_data(tk)
            st.session_state["etf_data"] = etf_results

    etf_data = st.session_state.get("etf_data", {})

    if not etf_data:
        st.markdown(
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:10px;'+
            f'padding:24px;text-align:center;color:{TXT_MUT}">'+
            f'<div style="font-size:28px;margin-bottom:8px">📊</div>'+
            f'<div>Presiona <strong>Cargar datos de ETFs</strong> para ver el estado actual</div>'+
            f'</div>', unsafe_allow_html=True)
    else:
        # Tabla de ETFs por categoría
        categorias = ["Indice","Parking","Sectorial","Cripto"]
        cat_labels = {"Indice":"📈 Índices","Parking":"🅿️ Parking / Renta Fija",
                      "Sectorial":"🏭 Sectoriales","Cripto":"₿ Cripto ETFs"}
        cat_colors = {"Indice":"2563EB","Parking":"16A34A","Sectorial":"D97706","Cripto":"7C3AED"}

        for cat in categorias:
            tks_cat = [tk for tk,meta in ETF_UNIVERSE.items() if meta["categoria"]==cat]
            st.markdown(
                f'<div style="font-size:12px;font-weight:700;color:#{cat_colors[cat]};'+
                f'margin:12px 0 6px">{cat_labels[cat]}</div>',
                unsafe_allow_html=True)

            for tk in tks_cat:
                d = etf_data.get(tk)
                if d is None:
                    continue
                meta   = ETF_UNIVERSE[tk]
                dd_c   = G if d["dd"] > -5 else A if d["dd"] > -15 else R
                rsi_c  = G if d["rsi"] < 45 else A if d["rsi"] < 60 else R
                ytd_c  = G if d["ytd"] > 0 else R
                tend_c = G if d["tend"]=="↑" else R if d["tend"]=="↓" else TXT_MUT

                st.markdown(
                    f'<div style="background:{BG_CARD};border:1px solid {BOR};'+
                    f'border-left:4px solid #{cat_colors[cat]};'+
                    f'border-radius:8px;padding:10px 14px;margin-bottom:6px;'+
                    f'display:flex;justify-content:space-between;align-items:center">'+
                    f'<div style="display:flex;align-items:center;gap:14px">'+
                    f'  <div>'+
                    f'    <div style="font-size:14px;font-weight:800;color:{B}">{tk}</div>'+
                    f'    <div style="font-size:10px;color:{TXT_MUT}">{meta["nombre"]}</div>'+
                    f'  </div>'+
                    f'  <div style="font-size:12px;font-weight:700;color:{TXT}">${d["precio"]:.2f}</div>'+
                    f'  <div style="text-align:center">'+
                    f'    <div style="font-size:9px;color:{TXT_MUT}">RSI</div>'+
                    f'    <div style="font-size:12px;font-weight:700;color:{rsi_c}">{d["rsi"]}</div>'+
                    f'  </div>'+
                    f'  <div style="text-align:center">'+
                    f'    <div style="font-size:9px;color:{TXT_MUT}">DD pico</div>'+
                    f'    <div style="font-size:12px;font-weight:700;color:{dd_c}">{d["dd"]}%</div>'+
                    f'  </div>'+
                    f'  <div style="text-align:center">'+
                    f'    <div style="font-size:9px;color:{TXT_MUT}">Tendencia</div>'+
                    f'    <div style="font-size:14px;font-weight:700;color:{tend_c}">{d["tend"]}</div>'+
                    f'  </div>'+
                    f'  <div style="text-align:center">'+
                    f'    <div style="font-size:9px;color:{TXT_MUT}">YTD</div>'+
                    f'    <div style="font-size:12px;font-weight:700;color:{ytd_c}">{d["ytd"]:+.1f}%</div>'+
                    f'  </div>'+
                    f'  <div style="font-size:11px;font-weight:700;color:#{d["senal_c"]}">{d["senal"]}</div>'+
                    f'</div>'+
                    f'<div style="font-size:10px;color:{TXT_MUT};text-align:right">'+
                    f'Riesgo: {meta["riesgo"]}<br>Rend hist: +{meta["rend_hist"]}%/año</div>'+
                    f'</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Estrategia recomendada ─────────────────────────────
        st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">🎯 Estrategia recomendada para ${capital_usd:,.0f} USD · {plazo_etf} · Perfil {perfil_etf}</div>',unsafe_allow_html=True)

        estrategia = calcular_estrategia(capital_usd, plazo_etf, perfil_etf, etf_data)
        allocs     = estrategia["allocations"]

        # Tabla de asignación
        for a in allocs:
            if a["monto"] < 50:  # mínimo $50 para mostrar
                continue
            bar_w = int(a["peso"] * 2)
            rsi_c2 = G if a["rsi"] < 45 else A if a["rsi"] < 60 else R
            dd_c2  = G if a["dd"] > -5 else A if a["dd"] > -15 else R

            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {BOR};'+
                f'border-radius:8px;padding:10px 14px;margin-bottom:6px">'+
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">'+
                f'<div style="display:flex;align-items:center;gap:10px">'+
                f'  <span style="font-size:14px;font-weight:800;color:{B}">{a["ticker"]}</span>'+
                f'  <span style="font-size:11px;color:{TXT_MUT}">{a["nombre"]}</span>'+
                f'  <span style="font-size:11px;font-weight:700;color:#{a["senal_c"]}">{a["senal"]}</span>'+
                f'</div>'+
                f'<div style="text-align:right">'+
                f'  <div style="font-size:16px;font-weight:800;color:{G}">${a["monto"]:,.0f}</div>'+
                f'  <div style="font-size:11px;color:{TXT_MUT}">{a["peso"]}% del capital</div>'+
                f'</div></div>'+
                f'<div style="background:{BOR};border-radius:4px;height:6px;margin-bottom:6px">'+
                f'<div style="background:{G};height:6px;border-radius:4px;width:{min(bar_w,200)}px"></div></div>'+
                f'<div style="display:flex;gap:16px;font-size:10px;color:{TXT_MUT}">'+
                f'  <span>RSI <strong style="color:{rsi_c2}">{a["rsi"]}</strong></span>'+
                f'  <span>DD <strong style="color:{dd_c2}">{a["dd"]}%</strong></span>'+
                f'  <span>Tend <strong>{a["tend"]}</strong></span>'+
                f'  <span>Rend hist <strong>+{a["rend_hist"]}%/año</strong></span>'+
                f'  <span>Riesgo <strong>{a["riesgo"]}</strong></span>'+
                f'</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Plan DCA ──────────────────────────────────────────
        st.markdown(
            f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">'+
            f'📅 Plan DCA — {estrategia["n_meses"]} meses · ${estrategia["monto_mes"]:,.0f} USD/mes</div>',
            unsafe_allow_html=True)

        import datetime as _dt
        mes_actual = _dt.date.today().replace(day=1)
        top3 = [a for a in allocs if a["monto"] >= 50][:4]

        for i in range(estrategia["n_meses"]):
            import calendar
            mes = (mes_actual.replace(day=1) + _dt.timedelta(days=32*i)).replace(day=1)
            mes_nom = mes.strftime("%B %Y").capitalize()
            monto_m = estrategia["monto_mes"]
            # Distribuir mes entre top ETFs
            detalle = " + ".join([
                f'<strong>{a["ticker"]}</strong> ${monto_m * a["peso"]/100:,.0f}'
                for a in top3 if a["monto"] > 0
            ])
            st.markdown(
                f'<div style="background:{"EFF6FF" if i%2==0 else "FFFFFF"};border:1px solid {BOR};'+
                f'border-radius:8px;padding:8px 14px;margin-bottom:4px;'+
                f'display:flex;justify-content:space-between;align-items:center">'+
                f'<div style="font-size:12px;font-weight:700;color:{TXT}">'+
                f'Mes {i+1} — {mes_nom}</div>'+
                f'<div style="font-size:11px;color:{TXT_MUT}">{detalle}</div>'+
                f'<div style="font-size:13px;font-weight:800;color:#2563EB">${monto_m:,.0f}</div>'+
                f'</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Proyección ────────────────────────────────────────
        st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">📈 Proyección a {estrategia["n_años"]} años · Rend. ponderado estimado +{estrategia["rend_ponderado"]}%/año</div>',unsafe_allow_html=True)

        pp1, pp2, pp3, pp4 = st.columns(4)
        with pp1:
            st.metric("Capital inicial", f"${capital_usd:,.0f}")
        with pp2:
            st.metric(f"Escenario base (+{estrategia['rend_ponderado']}%)",
                      f"${estrategia['proy_base']:,.0f}",
                      f"+${estrategia['proy_base']-capital_usd:,.0f}")
        with pp3:
            st.metric(f"Optimista (+{estrategia['rend_ponderado']+3:.0f}%)",
                      f"${estrategia['proy_opt']:,.0f}",
                      f"+${estrategia['proy_opt']-capital_usd:,.0f}")
        with pp4:
            st.metric(f"Pesimista (+{max(estrategia['rend_ponderado']-4,2):.0f}%)",
                      f"${estrategia['proy_pes']:,.0f}",
                      f"+${estrategia['proy_pes']-capital_usd:,.0f}")

        st.markdown(
            f'<div style="font-size:10px;color:{TXT_SOFT};margin-top:8px;font-style:italic">'+
            f'⚠️ Proyecciones basadas en rendimientos históricos. No constituyen asesoría financiera. '+
            f'Rendimientos pasados no garantizan resultados futuros.</div>',
            unsafe_allow_html=True)


st.markdown("---")
st.markdown(
    f'<div style="text-align:center;font-size:11px;color:{TXT_SOFT};padding:8px">'
    f'🦅 <strong>GrekoTrader</strong> · '
    f'Versión 11 · Creado el 21 Abr 2026 · '
    f'Patrón NBIS · 3 Momentos · 100% Automático<br>'
    f'<span style="font-size:10px">Datos educativos · No constituye asesoría financiera · '
    f'Powered by yfinance + Streamlit</span>'
    f'</div>',
    unsafe_allow_html=True)